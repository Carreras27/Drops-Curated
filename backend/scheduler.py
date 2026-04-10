"""
Background scheduler for auto-scraping all brands every 15 minutes.
Detects changes (price drops, new products) and triggers WhatsApp alerts.
Also handles daily digest notifications at 8 PM IST.
Includes AI classification for new products.
Includes health checks and dead-man's switch.

ANTI-BLOCKING FEATURES:
- Staggered brand scraping (15-35s random gaps)
- Fingerprint caching to skip unchanged products
- Health tracking per brand
- Automatic retry with exponential backoff
"""
import asyncio
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scrapers import SCRAPERS, SHOPIFY_BRANDS
from scrapers.scraper_utils import (
    stagger_delay, 
    brand_delay, 
    fingerprint_cache, 
    health_tracker,
    BlockedError
)
from alerts import detect_changes, send_alerts
from classifier import classify_product, clean_product_title
from duplicate_detector import filter_duplicates, merge_duplicate_prices, duplicate_stats
from scraper_agent import scraper_agent, ErrorContext, init_scraper_agent

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

    # Initialize health tracker with all brands
    all_brands = SHOPIFY_BRANDS + [
        {"key": "veg_non_veg", "name": "VegNonVeg"},
        {"key": "culture_circle", "name": "Culture Circle"},
        {"key": "hiyest", "name": "Hiyest"},
    ]
    health_tracker.init(db, all_brands)
    
    # Load fingerprint cache from database
    asyncio.create_task(_init_fingerprint_cache(db))
    
    # Initialize LLM-powered self-healing scraper agent
    asyncio.create_task(init_scraper_agent(db))

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
    logger.info("[Scheduler] Started — scraping every 15 minutes with staggered brand delays")


async def _init_fingerprint_cache(db):
    """Initialize fingerprint cache from database."""
    try:
        await fingerprint_cache.load_from_db(db)
    except Exception as e:
        logger.error(f"[Scheduler] Failed to load fingerprint cache: {e}")


async def _get_last_errors(brand_key: str, limit: int = 3) -> List[str]:
    """Get last N error messages for a brand from agent logs."""
    global _db
    if not _db:
        return []
    
    try:
        logs = await _db.scraper_agent_logs.find(
            {"brand_key": brand_key, "success": False},
            {"_id": 0, "message": 1}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return [log.get("message", "Unknown error") for log in logs]
    except:
        return []


async def scrape_all_brands():
    """
    Scrape all brands with STAGGERED execution.
    Each brand is scraped with random delays to avoid detection.
    """
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

    logger.info("[Scheduler] === Auto-scrape cycle starting (staggered) ===")

    # Randomize brand order to appear more natural
    brand_keys = list(SCRAPERS.keys())
    random.shuffle(brand_keys)
    
    for i, key in enumerate(brand_keys):
        scraper_factory = SCRAPERS[key]
        
        # Add stagger delay between brands (15-35 seconds)
        if i > 0:
            delay = await stagger_delay()
            logger.info(f"[Scheduler] Waiting {delay:.1f}s before next brand...")
        
        try:
            scraper = scraper_factory()
            logger.info(f"[Scheduler] [{i+1}/{len(brand_keys)}] Scraping {scraper.brand_name}...")

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

            logger.info(f"[Scheduler] {scraper.brand_name}: {len(scraped)} products ({len(duplicates)} duplicates), {new_count} new, {drops_count} price drops")

        except BlockedError as e:
            logger.error(f"[Scheduler] BLOCKED scraping {key}: {e}")
            
            # Get last 3 errors for context
            last_errors = await _get_last_errors(key, 3)
            
            # Trigger LLM Self-Healing Agent
            scraper = scraper_factory()
            error_context = ErrorContext(
                brand_key=key,
                brand_name=scraper.brand_name,
                scraper_name=type(scraper).__name__,
                error_type="BlockedError",
                error_message=str(e),
                http_status=getattr(e, 'status_code', None),
                url=scraper.base_url,
                last_3_errors=last_errors,
                response_snippet=getattr(e, 'response_snippet', '')
            )
            
            healing_result = await scraper_agent.handle_scraper_failure(scraper_factory, error_context)
            
            if healing_result.get("success"):
                logger.info(f"[Scheduler] Agent healed {key} with strategy: {healing_result.get('strategy')}")
                _run_results[key] = {
                    "status": "healed",
                    "scraped": healing_result.get("products", 0),
                    "strategy": healing_result.get("strategy"),
                    "strategies_tried": healing_result.get("strategies_tried", 0)
                }
                brands_succeeded += 1
            else:
                _run_results[key] = {
                    "status": "blocked", 
                    "error": str(e), 
                    "agent_attempted": True,
                    "exhausted": healing_result.get("exhausted", False)
                }
                brands_failed += 1
            
        except Exception as e:
            logger.error(f"[Scheduler] Error scraping {key}: {e}")
            
            # Get last 3 errors for context
            last_errors = await _get_last_errors(key, 3)
            
            # Trigger LLM Self-Healing Agent
            scraper = scraper_factory()
            error_context = ErrorContext(
                brand_key=key,
                brand_name=scraper.brand_name,
                scraper_name=type(scraper).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                url=scraper.base_url,
                last_3_errors=last_errors
            )
            
            healing_result = await scraper_agent.handle_scraper_failure(scraper_factory, error_context)
            
            if healing_result.get("success"):
                logger.info(f"[Scheduler] Agent healed {key} with strategy: {healing_result.get('strategy')}")
                _run_results[key] = {
                    "status": "healed",
                    "scraped": healing_result.get("products", 0),
                    "strategy": healing_result.get("strategy"),
                    "strategies_tried": healing_result.get("strategies_tried", 0)
                }
                brands_succeeded += 1
            else:
                _run_results[key] = {
                    "status": "error", 
                    "error": str(e), 
                    "agent_attempted": True,
                    "exhausted": healing_result.get("exhausted", False)
                }
                brands_failed += 1

    # Update success tracking
    if brands_succeeded > 0:
        _last_success = datetime.now(timezone.utc).isoformat()
        _consecutive_failures = 0
    else:
        _consecutive_failures += 1
    
    # Log blocked brands
    blocked = health_tracker.get_blocked_brands()
    if blocked:
        logger.warning(f"[Scheduler] Currently blocked brands: {blocked}")
    
    logger.info(f"[Scheduler] === Cycle complete: {brands_succeeded}/{len(brand_keys)} succeeded, {total_new} new, {total_drops} drops, {total_alerts} alerts ===")
    _is_running = False


async def _store_products(db, scraped_products: list[dict], brand_key: str) -> dict:
    """Store scraped products in the database with AI classification for new products."""
    added = 0
    updated = 0
    classified = 0

    for item in scraped_products:
        slug = item["name"].lower().replace(" ", "-").replace("'", "")[:80]
        
        # Use product ID from scraper if available, otherwise generate
        product_id = item.get("id") or f"prod_{item['store']}_{hash(item['name']) % 100000}"

        existing = await db.products.find_one({"name": item["name"], "store": item["store"]})

        if existing:
            await db.products.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "imageUrl": item["image_url"], 
                    "isActive": True, 
                    "updatedAt": item["scraped_at"],
                    "isLimited": item.get("is_limited", False),
                }}
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
                "isLimited": item.get("is_limited", False),
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

    return {"added": added, "updated": updated, "classified": classified}


def get_scheduler_status():
    """Get current scheduler status."""
    return {
        "is_running": _is_running,
        "last_run": _last_run,
        "last_success": _last_success,
        "results": _run_results,
        "next_scrape": str(scheduler.get_job('auto_scrape').next_run_time) if scheduler.get_job('auto_scrape') else None,
        "next_digest": str(scheduler.get_job('daily_digest').next_run_time) if scheduler.get_job('daily_digest') else None,
        "interval_minutes": 15,
        "digest_time": "8:00 PM IST",
        "consecutive_failures": _consecutive_failures,
        "blocked_brands": health_tracker.get_blocked_brands(),
    }


def get_scraper_health():
    """Get health status for all scrapers."""
    return health_tracker.get_dashboard_data()


async def send_daily_digest_notifications():
    """Send daily digest WhatsApp messages to all subscribers with queued alerts."""
    global _db
    
    from whatsapp import whatsapp_client, IS_CONFIGURED
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    if not IS_CONFIGURED:
        logger.warning("[Digest] WhatsApp not configured, skipping digest")
        return {"sent": 0, "error": "WhatsApp not configured"}
    
    try:
        # Find subscribers who haven't received digest today
        subscribers = await _db.subscribers.find({
            "isActive": True,
            "lastDigestSent": {"$ne": today}
        }, {"_id": 0}).to_list(1000)
        
        if not subscribers:
            logger.info("[Digest] No pending digests to send")
            return {"sent": 0}
        
        logger.info(f"[Digest] Sending digest to {len(subscribers)} subscribers")
        
        sent = 0
        for sub in subscribers:
            phone = sub.get("phone")
            if not phone:
                continue
            
            # Get new products from last 24 hours matching preferences
            prefs = sub.get("preferences", {})
            brand_prefs = prefs.get("brands", [])
            
            query = {
                "createdAt": {"$gte": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
            }
            if brand_prefs:
                query["brand"] = {"$in": brand_prefs}
            
            new_products = await _db.products.find(query, {"_id": 0}).limit(10).to_list(10)
            
            if not new_products:
                continue
            
            # Build digest message
            message = f"🛍️ *Daily Drops Digest*\n\n"
            message += f"*{len(new_products)} new drops* in the last 24 hours:\n\n"
            
            for p in new_products[:5]:
                price = p.get("lowestPrice") or p.get("price", 0)
                price_str = f"₹{price:,.0f}" if price else "Price TBD"
                message += f"• {p.get('brand', 'Brand')} - {p.get('name', 'Product')[:40]}\n  {price_str}\n\n"
            
            if len(new_products) > 5:
                message += f"... and {len(new_products) - 5} more!\n\n"
            
            message += "Visit dropscurated.com to see all drops"
            
            try:
                await whatsapp_client.send_message(phone, message)
                await _db.subscribers.update_one(
                    {"phone": phone},
                    {"$set": {"lastDigestSent": today}}
                )
                sent += 1
            except Exception as e:
                logger.error(f"[Digest] Failed to send to {phone}: {e}")
        
        logger.info(f"[Digest] Sent {sent} digest messages")
        return {"sent": sent}
        
    except Exception as e:
        logger.error(f"[Digest] Error: {e}")
        return {"sent": 0, "error": str(e)}


async def run_health_check():
    """Run health check on all system components."""
    global _health_status, _db
    
    now = datetime.now(timezone.utc).isoformat()
    _health_status['last_check'] = now
    
    # Check database
    try:
        await _db.products.count_documents({})
        _health_status['db_healthy'] = True
    except Exception as e:
        logger.error(f"[HealthCheck] Database unhealthy: {e}")
        _health_status['db_healthy'] = False
    
    # Check scraper (based on last success)
    if _last_success:
        try:
            last_success_time = datetime.fromisoformat(_last_success.replace('Z', '+00:00'))
            age_minutes = (datetime.now(timezone.utc) - last_success_time).total_seconds() / 60
            _health_status['scraper_healthy'] = age_minutes < 60  # Healthy if success in last hour
        except:
            _health_status['scraper_healthy'] = False
    else:
        _health_status['scraper_healthy'] = True  # Assume healthy on first run
    
    # Check alerts
    from whatsapp import IS_CONFIGURED
    _health_status['alerts_healthy'] = IS_CONFIGURED
    
    # Overall status
    if _health_status['db_healthy'] and _health_status['scraper_healthy']:
        _health_status['status'] = 'healthy'
    elif _health_status['db_healthy']:
        _health_status['status'] = 'degraded'
    else:
        _health_status['status'] = 'unhealthy'
    
    # Check for blocked brands
    blocked = health_tracker.get_blocked_brands()
    if blocked:
        _health_status['status'] = 'degraded'
        _health_status['blocked_brands'] = blocked
    
    logger.debug(f"[HealthCheck] Status: {_health_status['status']}")


async def check_dead_mans_switch():
    """Check if scraper has been stuck for too long and alert."""
    global _consecutive_failures, _last_success
    
    # If no successful scrape in 2 hours, alert
    if _last_success:
        try:
            last_success_time = datetime.fromisoformat(_last_success.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - last_success_time).total_seconds() / 3600
            
            if age_hours > 2:
                logger.warning(f"[DeadMansSwitch] No successful scrape in {age_hours:.1f} hours!")
                
                # Send alert
                try:
                    from whatsapp import send_admin_alert
                    await send_admin_alert(
                        f"⚠️ SCRAPER ALERT\n\n"
                        f"No successful scrape in {age_hours:.1f} hours.\n"
                        f"Consecutive failures: {_consecutive_failures}\n"
                        f"Blocked brands: {health_tracker.get_blocked_brands()}"
                    )
                except Exception as e:
                    logger.error(f"[DeadMansSwitch] Failed to send alert: {e}")
        except Exception as e:
            logger.error(f"[DeadMansSwitch] Error: {e}")
    
    # If too many consecutive failures, alert
    if _consecutive_failures >= 3:
        logger.warning(f"[DeadMansSwitch] {_consecutive_failures} consecutive scrape failures!")


def get_health_status():
    """Get current health status."""
    return _health_status


# Manual scrape trigger for admin
async def manual_scrape(brand_key: str = None):
    """Manually trigger a scrape for one or all brands."""
    global _db
    
    if brand_key:
        if brand_key not in SCRAPERS:
            return {"error": f"Unknown brand: {brand_key}"}
        
        try:
            scraper = SCRAPERS[brand_key]()
            products = await scraper.scrape_products(max_pages=5)
            
            if products:
                unique, dupes = await filter_duplicates(_db, products)
                await _store_products(_db, unique, brand_key)
                return {
                    "brand": brand_key,
                    "scraped": len(products),
                    "unique": len(unique),
                    "duplicates": len(dupes)
                }
            return {"brand": brand_key, "scraped": 0}
        except Exception as e:
            return {"brand": brand_key, "error": str(e)}
    else:
        # Scrape all brands
        await scrape_all_brands()
        return get_scheduler_status()
