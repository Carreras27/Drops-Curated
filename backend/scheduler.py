"""
Background scheduler for auto-scraping all brands every 15 minutes.
Detects changes (price drops, new products) and triggers WhatsApp alerts.
"""
import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scrapers import SCRAPERS
from alerts import detect_changes, send_alerts

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_db = None
_is_running = False
_last_run = None
_run_results = {}


def init_scheduler(db):
    """Initialize the scheduler with database reference."""
    global _db
    _db = db

    scheduler.add_job(
        scrape_all_brands,
        'interval',
        minutes=15,
        id='auto_scrape',
        max_instances=1,
        replace_existing=True,
        next_run_time=None,  # Don't run immediately on startup
    )
    scheduler.start()
    logger.info("[Scheduler] Started — scraping every 15 minutes")


async def scrape_all_brands():
    """Scrape all brands, detect changes, send alerts."""
    global _is_running, _last_run, _run_results
    if _is_running:
        logger.warning("[Scheduler] Scrape already running, skipping")
        return
    _is_running = True
    _last_run = datetime.now(timezone.utc).isoformat()
    _run_results = {}
    total_new = 0
    total_drops = 0
    total_alerts = 0

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

            # Store products (same logic as the API endpoint)
            stored = await _store_products(_db, scraped, key)

            # Send alerts if there are changes
            alert_result = {"sent": 0}
            if new_count > 0 or drops_count > 0:
                alert_result = await send_alerts(_db, changes, scraper.store_key)

            _run_results[key] = {
                "status": "ok",
                "scraped": len(scraped),
                "new": new_count,
                "price_drops": drops_count,
                "alerts_sent": alert_result["sent"],
            }
            total_new += new_count
            total_drops += drops_count
            total_alerts += alert_result["sent"]

            logger.info(f"[Scheduler] {scraper.brand_name}: {len(scraped)} products, {new_count} new, {drops_count} price drops, {alert_result['sent']} alerts")

        except Exception as e:
            logger.error(f"[Scheduler] Error scraping {key}: {e}")
            _run_results[key] = {"status": "error", "error": str(e)}

    logger.info(f"[Scheduler] === Cycle complete: {total_new} new, {total_drops} drops, {total_alerts} alerts sent ===")
    _is_running = False


async def _store_products(db, scraped_products: list[dict], brand_key: str) -> dict:
    """Store scraped products in the database."""
    added = 0
    updated = 0

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
            await db.products.insert_one({
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
            })
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
        "next_run": str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else None,
        "interval_minutes": 15,
    }
