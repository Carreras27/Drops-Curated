"""
Background scheduler for auto-scraping all brands every 15 minutes.
Detects changes (price drops, new products) and triggers WhatsApp alerts.
Also handles daily digest notifications at 8 PM IST.
Includes AI classification for new products.
Includes health checks and dead-man's switch.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scrapers import SCRAPERS
from alerts import detect_changes, send_alerts
from classifier import classify_product, clean_product_title
from duplicate_detector import filter_duplicates, merge_duplicate_prices, duplicate_stats

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_db = None
_is_running = False
_last_run = None
_last_success = None
_run_results = {}
_consecutive_failures = 0
_health_status = {
    'status': 'unknown',
    'last_check': None,
    'scraper_healthy': True,
    'db_healthy': True,
    'alerts_healthy': True
}


def init_scheduler(db):
    """Initialize the scheduler with database reference."""
    global _db
    _db = db

    # Auto-scrape job every 15 minutes
    scheduler.add_job(
        scrape_all_brands,
        'interval',
        minutes=15,
        id='auto_scrape',
        max_instances=1,
        replace_existing=True,
    )
    
    # Daily digest job at 8 PM IST (14:30 UTC)
    scheduler.add_job(
        send_daily_digest_notifications,
        'cron',
        hour=14,
        minute=30,
        id='daily_digest',
        max_instances=1,
        replace_existing=True,
    )
    
    # Health check every 5 minutes
    scheduler.add_job(
        run_health_check,
        'interval',
        minutes=5,
        id='health_check',
        max_instances=1,
        replace_existing=True,
    )
    
    # Dead-man's switch - check if scraper is stuck
    scheduler.add_job(
        check_dead_mans_switch,
        'interval',
        minutes=30,
        id='dead_mans_switch',
        max_instances=1,
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("[Scheduler] Started — scraping every 15 minutes, health check every 5 minutes")


async def scrape_all_brands():
    """Scrape all brands, detect changes, send alerts."""
    global _is_running, _last_run, _last_success, _run_results, _consecutive_failures
    if _is_running:
        logger.warning("[Scheduler] Scrape already running, skipping")
        return
    _is_running = True
    _last_run = datetime.now(timezone.utc).isoformat()
    _run_results = {}
    total_new = 0
    total_drops = 0
    total_alerts = 0
    total_duplicates = 0
    brands_succeeded = 0
    brands_failed = 0

    logger.info("[Scheduler] === Auto-scrape cycle starting ===")

    for key, scraper_factory in SCRAPERS.items():
        try:
            scraper = scraper_factory()
            logger.info(f"[Scheduler] Scraping {scraper.brand_name}...")

            scraped = await scraper.scrape_products(max_pages=5)
            if not scraped:
                _run_results[key] = {"status": "empty", "scraped": 0}
                continue

            # Detect changes BEFORE storing
            changes = await detect_changes(_db, scraped, scraper.store_key)
            new_count = len(changes["new_products"])
            drops_count = len(changes["price_drops"])

            # Filter duplicates before storing
            unique_products, duplicates = await filter_duplicates(_db, scraped)
            total_duplicates += len(duplicates)
            
            # Store products (only unique ones)
            if unique_products:
                await _store_products(_db, unique_products, key)

            # Send alerts if there are changes
            alert_result = {"sent": 0}
            if new_count > 0 or drops_count > 0:
                alert_result = await send_alerts(_db, changes, scraper.store_key)

            _run_results[key] = {
                "status": "ok",
                "scraped": len(scraped),
                "unique": len(unique_products),
                "duplicates": len(duplicates),
                "new": new_count,
                "price_drops": drops_count,
                "alerts_sent": alert_result["sent"],
            }
            total_new += new_count
            total_drops += drops_count
            total_alerts += alert_result["sent"]
            brands_succeeded += 1

            logger.info(f"[Scheduler] {scraper.brand_name}: {len(scraped)} products ({len(duplicates)} duplicates), {new_count} new, {drops_count} price drops, {alert_result['sent']} alerts")

        except Exception as e:
            logger.error(f"[Scheduler] Error scraping {key}: {e}")
            _run_results[key] = {"status": "error", "error": str(e)}
            brands_failed += 1

    # Update success tracking
    if brands_succeeded > 0:
        _last_success = datetime.now(timezone.utc).isoformat()
        _consecutive_failures = 0
    else:
        _consecutive_failures += 1
    
    logger.info(f"[Scheduler] === Cycle complete: {total_new} new, {total_drops} drops, {total_duplicates} duplicates filtered, {total_alerts} alerts sent ===")
    _is_running = False


async def _store_products(db, scraped_products: list[dict], brand_key: str) -> dict:
    """Store scraped products in the database with AI classification for new products."""
    added = 0
    updated = 0
    classified = 0

    for item in scraped_products:
        slug = item["name"].lower().replace(" ", "-").replace("'", "")[:80]
        product_id = f"prod_{item['store']}_{hash(item['name']) % 100000}"

        existing = await db.products.find_one({"name": item["name"], "store": item["store"]})

        if existing:
            await db.products.update_one(
                {"_id": existing["_id"]},
                {"$set": {"imageUrl": item["image_url"], "isActive": True, "updatedAt": item["scraped_at"]}}
            )
            product_id = existing["id"]
            updated += 1
        else:
            # Build base product data
            product_data = {
                "id": product_id,
                "name": item["name"],
                "slug": slug,
                "brand": item["brand"],
                "category": item["category"],
                "description": f'{item["brand"]} {item["category"].lower()} from {item["store"].replace("_", " ").title()}',
                "imageUrl": item["image_url"],
                "additionalImages": [],
                "attributes": {"sizes": item.get("available_sizes", [])},
                "tags": item.get("tags", []) + [item["brand"].lower(), item["category"].lower()],
                "store": item["store"],
                "isActive": True,
                "isTrending": False,
                "createdAt": item["scraped_at"],
            }
            
            # AI Classification for new products
            try:
                classification = await classify_product(product_data)
                product_data.update({
                    "normalizedTitle": classification.get("normalizedTitle"),
                    "aiGender": classification.get("aiGender"),
                    "aiCategory": classification.get("aiCategory"),
                    "aiSubcategory": classification.get("aiSubcategory"),
                    "aiBrand": classification.get("aiBrand"),
                    "aiConfidence": classification.get("aiConfidence"),
                    "classifiedAt": classification.get("classifiedAt"),
                })
                classified += 1
                logger.debug(f"[Classifier] Classified: {item['name']} -> {classification.get('aiCategory')}/{classification.get('aiSubcategory')}")
            except Exception as e:
                # If classification fails, just use cleaned title
                product_data["normalizedTitle"] = clean_product_title(item["name"])
                logger.warning(f"[Classifier] Failed to classify {item['name']}: {e}")
            
            await db.products.insert_one(product_data)
            added += 1

        await db.prices.update_one(
            {"productId": product_id, "store": item["store"]},
            {"$set": {
                "id": f"price_{product_id}_{item['store']}",
                "productId": product_id,
                "store": item["store"],
                "productUrl": item.get("product_url", ""),
                "currentPrice": item["price"],
                "originalPrice": item.get("original_price", item["price"]),
                "inStock": item.get("in_stock", True),
                "lastScrapedAt": item["scraped_at"],
                "createdAt": item["scraped_at"],
            }},
            upsert=True,
        )

    # Update brand record
    scraper_factory = SCRAPERS.get(brand_key)
    if scraper_factory:
        s = scraper_factory()
        await db.brands.update_one(
            {"key": brand_key},
            {"$set": {
                "key": brand_key,
                "name": s.brand_name,
                "storeKey": s.store_key,
                "websiteUrl": s.base_url,
                "isActive": True,
                "lastScrapedAt": datetime.now(timezone.utc).isoformat(),
                "productCount": await db.products.count_documents({"store": s.store_key}),
            }},
            upsert=True,
        )

    return {"added": added, "updated": updated}


def get_scheduler_status():
    """Get current scheduler status."""
    return {
        "is_running": _is_running,
        "last_run": _last_run,
        "results": _run_results,
        "next_scrape": str(scheduler.get_job('auto_scrape').next_run_time) if scheduler.get_job('auto_scrape') else None,
        "next_digest": str(scheduler.get_job('daily_digest').next_run_time) if scheduler.get_job('daily_digest') else None,
        "interval_minutes": 15,
        "digest_time": "8:00 PM IST",
    }


async def send_daily_digest_notifications():
    """Send daily digest WhatsApp messages to all subscribers with queued alerts."""
    global _db
    
    from whatsapp import whatsapp_client, IS_CONFIGURED
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    logger.info(f"[Daily Digest] Starting digest send for {today}")
    
    digests = await _db.daily_digest.find({'date': today, 'sent': {'$ne': True}}).to_list(1000)
    
    sent_count = 0
    
    for digest in digests:
        phone = digest.get('phone', '')
        alerts = digest.get('alerts', [])
        
        if not alerts:
            continue
        
        # Group alerts by type
        new_drops = [a for a in alerts if a.get('type') == 'new_release']
        price_drops = [a for a in alerts if a.get('type') == 'price_drop']
        restocks = [a for a in alerts if a.get('type') == 'restock']
        
        # Build digest message
        message = "🌙 *Your Daily Drops Digest*\n\n"
        message += f"_{today}_\n\n"
        
        if new_drops:
            message += f"🆕 *{len(new_drops)} New Arrivals*\n"
            for nd in new_drops[:3]:
                data = nd.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]} - ₹{data.get('price', 0):,.0f}\n"
            if len(new_drops) > 3:
                message += f"  _...and {len(new_drops) - 3} more_\n"
            message += "\n"
        
        if price_drops:
            message += f"💰 *{len(price_drops)} Price Drops*\n"
            for pd in price_drops[:3]:
                data = pd.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]} - ₹{data.get('new_price', 0):,.0f} (was ₹{data.get('old_price', 0):,.0f})\n"
            if len(price_drops) > 3:
                message += f"  _...and {len(price_drops) - 3} more_\n"
            message += "\n"
        
        if restocks:
            message += f"📦 *{len(restocks)} Back in Stock*\n"
            for rs in restocks[:3]:
                data = rs.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]}\n"
            message += "\n"
        
        message += "👉 Browse all drops on Drops Curated!"
        
        # Send the digest
        if IS_CONFIGURED:
            success, result = whatsapp_client.send_text_message(phone, message)
        else:
            success = True  # Sandbox mode
            logger.info(f"[Sandbox] Daily digest to {phone}: {len(alerts)} alerts")
        
        if success:
            sent_count += 1
            await _db.daily_digest.update_one(
                {'_id': digest['_id']},
                {'$set': {'sent': True, 'sentAt': datetime.now(timezone.utc).isoformat()}}
            )
    
    logger.info(f"[Daily Digest] Completed: {sent_count} digests sent")



# ============ HEALTH CHECKS ============

async def run_health_check():
    """Run periodic health checks on all systems"""
    global _health_status, _db
    
    now = datetime.now(timezone.utc)
    _health_status['last_check'] = now.isoformat()
    
    # Check database connectivity
    try:
        await _db.products.find_one({})
        _health_status['db_healthy'] = True
    except Exception as e:
        _health_status['db_healthy'] = False
        logger.error(f"[HealthCheck] Database unhealthy: {e}")
    
    # Check if scraper has run recently
    if _last_success:
        last_success_time = datetime.fromisoformat(_last_success)
        time_since_success = now - last_success_time
        _health_status['scraper_healthy'] = time_since_success < timedelta(hours=1)
    else:
        _health_status['scraper_healthy'] = _last_run is None  # OK if never run yet
    
    # Overall status
    if _health_status['db_healthy'] and _health_status['scraper_healthy']:
        _health_status['status'] = 'healthy'
    elif not _health_status['db_healthy']:
        _health_status['status'] = 'critical'
    else:
        _health_status['status'] = 'degraded'
    
    logger.debug(f"[HealthCheck] Status: {_health_status['status']}")


async def check_dead_mans_switch():
    """
    Dead-man's switch: If scraper hasn't succeeded in 1 hour, trigger alert.
    This prevents silent failures where the scraper stops working.
    """
    global _last_success, _consecutive_failures, _db
    
    if not _last_success:
        return  # Never run yet, skip
    
    now = datetime.now(timezone.utc)
    last_success_time = datetime.fromisoformat(_last_success)
    time_since_success = now - last_success_time
    
    # If no successful scrape in 1 hour, something is wrong
    if time_since_success > timedelta(hours=1):
        logger.warning(f"[DeadMansSwitch] No successful scrape in {time_since_success}. Consecutive failures: {_consecutive_failures}")
        
        # Log the issue
        await _db.system_alerts.insert_one({
            'type': 'dead_mans_switch',
            'message': f'Scraper has not succeeded in {time_since_success}',
            'consecutive_failures': _consecutive_failures,
            'last_success': _last_success,
            'created_at': now.isoformat()
        })
        
        # If 3+ consecutive failures, mark as critical
        if _consecutive_failures >= 3:
            _health_status['status'] = 'critical'
            _health_status['scraper_healthy'] = False


def get_health_status():
    """Get current health status"""
    return {
        **_health_status,
        'last_run': _last_run,
        'last_success': _last_success,
        'consecutive_failures': _consecutive_failures,
        'is_running': _is_running
    }
