"""
Real-time alert system for Drops Curated.
Detects price drops and new products, sends WhatsApp alerts via Meta Cloud API.
"""
import os
import logging
from datetime import datetime, timezone
from whatsapp import send_price_drop_alert, send_new_drop_alert, whatsapp_client, IS_CONFIGURED

logger = logging.getLogger(__name__)

SANDBOX_MODE = not IS_CONFIGURED


async def detect_changes(db, scraped_products: list[dict], store_key: str) -> dict:
    """Compare scraped data against DB to find price drops and new products."""
    new_products = []
    price_drops = []

    for item in scraped_products:
        existing = await db.products.find_one(
            {"name": item["name"], "store": item["store"]},
            {"_id": 0, "id": 1, "name": 1}
        )

        if not existing:
            new_products.append(item)
            continue

        # Check for price drop
        product_id = existing["id"]
        old_price_doc = await db.prices.find_one(
            {"productId": product_id, "store": item["store"]},
            {"_id": 0, "currentPrice": 1}
        )

        if old_price_doc:
            old_price = old_price_doc.get("currentPrice", 0)
            new_price = item["price"]
            if old_price > 0 and new_price > 0 and new_price < old_price:
                drop_pct = round(((old_price - new_price) / old_price) * 100, 1)
                price_drops.append({
                    **item,
                    "old_price": old_price,
                    "new_price": new_price,
                    "drop_percent": drop_pct,
                })

    return {"new_products": new_products, "price_drops": price_drops}


async def send_alerts(db, changes: dict, store_key: str):
    """Send WhatsApp alerts to subscribers who want notifications for this brand."""
    from whatsapp import send_price_drop_alert, send_new_drop_alert
    
    new_products = changes.get("new_products", [])
    price_drops = changes.get("price_drops", [])

    if not new_products and not price_drops:
        return {"sent": 0}

    # Find subscribers who want alerts for this brand/store
    subscribers = await db.subscribers.find(
        {"isActive": True, "isPaid": True},
        {"_id": 0}
    ).to_list(1000)

    sent_count = 0

    for sub in subscribers:
        phone = sub.get("phone", "")
        prefs = sub.get("preferences", {})
        pref_brands = prefs.get("brands", [])  # Empty = all brands
        pref_types = prefs.get("alert_types", ["price_drop", "new_release"])
        pref_categories = prefs.get("categories", [])  # sneakers, garments
        pref_sizes = prefs.get("sizes", [])

        # Check if this subscriber cares about this brand
        if pref_brands and store_key not in pref_brands:
            continue

        alerts_sent = 0

        # Price drop alerts with product images
        if "price_drop" in pref_types and price_drops:
            for drop in price_drops[:3]:  # Max 3 price drops per subscriber
                # Check category preference
                if pref_categories and drop.get('category') not in pref_categories:
                    continue
                    
                success, _ = send_price_drop_alert(
                    phone=phone,
                    product_name=drop['name'],
                    new_price=f"{drop['new_price']:,.0f}",
                    old_price=f"{drop['old_price']:,.0f}",
                    image_url=drop.get('imageUrl'),
                    product_url=drop.get('product_url')
                )
                if success:
                    sent_count += 1
                    alerts_sent += 1
                
                if alerts_sent >= 3:
                    break

        # New product alerts with product images
        if "new_release" in pref_types and new_products and alerts_sent < 3:
            for prod in new_products[:3]:
                # Check category preference
                if pref_categories and prod.get('category') not in pref_categories:
                    continue
                    
                success, _ = send_new_drop_alert(
                    phone=phone,
                    product_name=prod['name'],
                    price=f"{prod['price']:,.0f}",
                    brand=prod.get('brand', ''),
                    image_url=prod.get('imageUrl'),
                    product_url=prod.get('product_url')
                )
                if success:
                    sent_count += 1
                    alerts_sent += 1
                
                if alerts_sent >= 3:
                    break

        # Log alert activity
        if alerts_sent > 0:
            await db.alert_log.insert_one({
                "phone": phone,
                "store": store_key,
                "message": msg[:200],
                "sent": success,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            })

    logger.info(f"[Alerts] Sent {sent_count} WhatsApp messages for {store_key}")
    return {"sent": sent_count}


async def _send_whatsapp(phone: str, message: str, alert_type: str = "general", alert_data: dict = None) -> bool:
    """Send a WhatsApp message via Meta Cloud API."""
    if SANDBOX_MODE:
        logger.info(f"[Sandbox] WhatsApp to +91{phone}: {message[:80]}...")
        return True

    try:
        success, result = whatsapp_client.send_text_message(phone, message)
        if success:
            logger.info(f"[WhatsApp] Sent to {phone}. Message ID: {result}")
            return True
        else:
            logger.warning(f"[WhatsApp] Failed to send to {phone}: {result}")
            return False
    except Exception as e:
        logger.error(f"[WhatsApp] Failed to send to {phone}: {e}")
        return False
