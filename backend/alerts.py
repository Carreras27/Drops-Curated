"""
Real-time alert system for Drops Curated.
Detects price drops and new products, sends WhatsApp alerts via Meta Cloud API.
Implements the Preference Funnel for cost-efficient, targeted notifications.
"""
import logging
from datetime import datetime, timezone
from whatsapp import send_price_drop_alert, send_new_drop_alert, whatsapp_client, IS_CONFIGURED

logger = logging.getLogger(__name__)

SANDBOX_MODE = not IS_CONFIGURED

# Daily digest queue (in production, use Redis)
daily_digest_queue = {}  # {phone: [alerts]}


def _matches_keywords(product_name: str, product_desc: str, keywords: list) -> bool:
    """Check if product matches any of the user's keywords."""
    if not keywords:
        return True  # No keywords = match all
    
    search_text = f"{product_name} {product_desc}".lower()
    for kw in keywords:
        if kw.lower() in search_text:
            return True
    return False


def _matches_price_range(price: float, price_range: dict) -> bool:
    """Check if product price falls within user's budget range."""
    if not price_range:
        return True
    
    min_price = price_range.get('min')
    max_price = price_range.get('max')
    
    if min_price is not None and price < min_price:
        return False
    if max_price is not None and price > max_price:
        return False
    return True


def _matches_category(product_category: str, pref_categories: list) -> bool:
    """Check if product category matches user preferences."""
    if not pref_categories:
        return True  # No filter = all categories
    
    # Normalize category names
    category_map = {
        'CLOTHES': 'garments',
        'SHOES': 'sneakers',
        'ACCESSORIES': 'accessories',
        'garments': 'garments',
        'sneakers': 'sneakers',
        'accessories': 'accessories',
    }
    
    normalized = category_map.get(product_category, product_category.lower())
    return normalized in [c.lower() for c in pref_categories]


def _matches_sizes(product_sizes: list, pref_sizes: list) -> bool:
    """Check if product has any of the user's preferred sizes."""
    if not pref_sizes:
        return True  # No size filter = all sizes
    if not product_sizes:
        return True  # If product has no size info, include it
    
    # Normalize sizes for comparison
    product_sizes_lower = [s.lower().strip() for s in product_sizes]
    pref_sizes_lower = [s.lower().strip() for s in pref_sizes]
    
    return any(ps in product_sizes_lower for ps in pref_sizes_lower)


def _meets_drop_threshold(drop_percent: float, threshold: int) -> bool:
    """Check if price drop meets the user's minimum threshold."""
    return drop_percent >= threshold


async def detect_changes(db, scraped_products: list[dict], store_key: str) -> dict:
    """Compare scraped data against DB to find price drops and new products."""
    new_products = []
    price_drops = []
    restocks = []

    for item in scraped_products:
        existing = await db.products.find_one(
            {"name": item["name"], "store": item["store"]},
            {"_id": 0, "id": 1, "name": 1, "attributes": 1}
        )

        if not existing:
            new_products.append(item)
            continue

        # Check for price drop
        product_id = existing["id"]
        old_price_doc = await db.prices.find_one(
            {"productId": product_id, "store": item["store"]},
            {"_id": 0, "currentPrice": 1, "inStock": 1}
        )

        if old_price_doc:
            old_price = old_price_doc.get("currentPrice", 0)
            old_in_stock = old_price_doc.get("inStock", True)
            new_price = item["price"]
            new_in_stock = item.get("in_stock", True)
            
            # Price drop detection
            if old_price > 0 and new_price > 0 and new_price < old_price:
                drop_pct = round(((old_price - new_price) / old_price) * 100, 1)
                price_drops.append({
                    **item,
                    "old_price": old_price,
                    "new_price": new_price,
                    "drop_percent": drop_pct,
                    "available_sizes": existing.get("attributes", {}).get("sizes", []),
                })
            
            # Restock detection (was out of stock, now in stock)
            if not old_in_stock and new_in_stock:
                restocks.append({
                    **item,
                    "available_sizes": existing.get("attributes", {}).get("sizes", []),
                })

    return {"new_products": new_products, "price_drops": price_drops, "restocks": restocks}


async def send_alerts(db, changes: dict, store_key: str):
    """
    Send WhatsApp alerts to subscribers who want notifications for this brand.
    Implements the full Preference Funnel:
    - Brand selection
    - Trigger-based filtering
    - Category/Size specificity
    - Price range filtering
    - Keyword matching
    - Drop threshold
    - Daily digest vs instant
    """
    new_products = changes.get("new_products", [])
    price_drops = changes.get("price_drops", [])
    restocks = changes.get("restocks", [])

    if not new_products and not price_drops and not restocks:
        return {"sent": 0, "queued_for_digest": 0}

    # Find active paid subscribers
    subscribers = await db.subscribers.find(
        {"isActive": True, "isPaid": True},
        {"_id": 0}
    ).to_list(1000)

    sent_count = 0
    queued_count = 0

    for sub in subscribers:
        phone = sub.get("phone", "")
        prefs = sub.get("preferences", {})
        
        # === A. Brand Selection ===
        pref_brands = prefs.get("brands", [])  # Empty = all brands
        if pref_brands and store_key not in pref_brands:
            continue  # Skip if subscriber doesn't follow this brand
        
        # === B. Trigger Types ===
        pref_types = prefs.get("alert_types", ["price_drop", "new_release"])
        
        # === C. Specificity Filters ===
        pref_categories = prefs.get("categories", [])
        pref_sizes = prefs.get("sizes", [])
        
        # === Additional Filters ===
        price_range = prefs.get("price_range", {})
        keywords = prefs.get("keywords", [])
        drop_threshold = prefs.get("drop_threshold", 10)  # Default 10%
        alert_frequency = prefs.get("alert_frequency", "daily")
        
        alerts_to_send = []

        # Price drop alerts
        if "price_drop" in pref_types:
            for drop in price_drops:
                # Check category
                if not _matches_category(drop.get('category', ''), pref_categories):
                    continue
                
                # Check sizes
                if not _matches_sizes(drop.get('available_sizes', []), pref_sizes):
                    continue
                
                # Check price range
                if not _matches_price_range(drop['new_price'], price_range):
                    continue
                
                # Check keywords
                if not _matches_keywords(drop['name'], drop.get('description', ''), keywords):
                    continue
                
                # Check drop threshold
                if not _meets_drop_threshold(drop['drop_percent'], drop_threshold):
                    continue
                
                alerts_to_send.append({
                    'type': 'price_drop',
                    'data': drop,
                })

        # New product alerts
        if "new_release" in pref_types:
            for prod in new_products:
                # Check category
                if not _matches_category(prod.get('category', ''), pref_categories):
                    continue
                
                # Check sizes
                if not _matches_sizes(prod.get('available_sizes', []), pref_sizes):
                    continue
                
                # Check price range
                if not _matches_price_range(prod['price'], price_range):
                    continue
                
                # Check keywords
                if not _matches_keywords(prod['name'], prod.get('description', ''), keywords):
                    continue
                
                alerts_to_send.append({
                    'type': 'new_release',
                    'data': prod,
                })

        # Restock alerts
        if "restock" in pref_types:
            for restock in restocks:
                # Check category
                if not _matches_category(restock.get('category', ''), pref_categories):
                    continue
                
                # Check sizes
                if not _matches_sizes(restock.get('available_sizes', []), pref_sizes):
                    continue
                
                # Check price range
                if not _matches_price_range(restock['price'], price_range):
                    continue
                
                # Check keywords
                if not _matches_keywords(restock['name'], restock.get('description', ''), keywords):
                    continue
                
                alerts_to_send.append({
                    'type': 'restock',
                    'data': restock,
                })

        # === D. Notification Frequency ===
        if alert_frequency == "daily":
            # Queue for daily digest (8 PM)
            if phone not in daily_digest_queue:
                daily_digest_queue[phone] = []
            daily_digest_queue[phone].extend(alerts_to_send[:5])  # Max 5 per cycle
            queued_count += len(alerts_to_send[:5])
            
            # Store digest in DB for persistence
            if alerts_to_send:
                await db.daily_digest.update_one(
                    {'phone': phone, 'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')},
                    {
                        '$push': {'alerts': {'$each': alerts_to_send[:5]}},
                        '$set': {'updatedAt': datetime.now(timezone.utc).isoformat()}
                    },
                    upsert=True
                )
        else:
            # Instant alerts - send immediately (max 3 per subscriber per scrape cycle)
            for alert in alerts_to_send[:3]:
                success = False
                if alert['type'] == 'price_drop':
                    drop = alert['data']
                    success, _ = send_price_drop_alert(
                        phone=phone,
                        product_name=drop['name'],
                        new_price=f"{drop['new_price']:,.0f}",
                        old_price=f"{drop['old_price']:,.0f}",
                        image_url=drop.get('image_url'),
                        product_url=drop.get('product_url')
                    )
                elif alert['type'] == 'new_release':
                    prod = alert['data']
                    success, _ = send_new_drop_alert(
                        phone=phone,
                        product_name=prod['name'],
                        price=f"{prod['price']:,.0f}",
                        brand=prod.get('brand', ''),
                        image_url=prod.get('image_url'),
                        product_url=prod.get('product_url')
                    )
                elif alert['type'] == 'restock':
                    restock = alert['data']
                    success, _ = send_new_drop_alert(
                        phone=phone,
                        product_name=f"[BACK IN STOCK] {restock['name']}",
                        price=f"{restock['price']:,.0f}",
                        brand=restock.get('brand', ''),
                        image_url=restock.get('image_url'),
                        product_url=restock.get('product_url')
                    )
                
                if success:
                    sent_count += 1

        # Log alert activity
        if alerts_to_send:
            await db.alert_log.insert_one({
                "phone": phone,
                "store": store_key,
                "alert_count": len(alerts_to_send),
                "frequency": alert_frequency,
                "sent": alert_frequency == "instant",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            })

    logger.info(f"[Alerts] {store_key}: Sent {sent_count} instant, queued {queued_count} for digest")
    return {"sent": sent_count, "queued_for_digest": queued_count}


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
