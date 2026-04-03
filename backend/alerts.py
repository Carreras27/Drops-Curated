"""
Real-time alert system for Drops Curated.
Detects price drops and new products, sends WhatsApp alerts via Twilio.
"""
import os
import logging
from datetime import datetime, timezone
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)

TWILIO_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+919700771000')  # Drops Curated WhatsApp

SANDBOX_MODE = not TWILIO_SID or TWILIO_SID.startswith('AC_test')


def get_twilio_client():
    if SANDBOX_MODE:
        return None
    return TwilioClient(TWILIO_SID, TWILIO_TOKEN)


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

        # Check if this subscriber cares about this brand
        if pref_brands and store_key not in pref_brands:
            continue

        messages = []

        # Price drop alerts
        if "price_drop" in pref_types and price_drops:
            for drop in price_drops[:5]:  # Max 5 drops per alert
                msg = (
                    f"Price Drop Alert!\n\n"
                    f"{drop['name']}\n"
                    f"Was: Rs.{drop['old_price']:,.0f}\n"
                    f"Now: Rs.{drop['new_price']:,.0f} (-{drop['drop_percent']}%)\n\n"
                    f"Buy: {drop.get('product_url', '')}"
                )
                messages.append(msg)

        # New product alerts
        if "new_release" in pref_types and new_products:
            # Batch new products into one message
            if len(new_products) <= 3:
                for prod in new_products:
                    msg = (
                        f"New Drop!\n\n"
                        f"{prod['name']}\n"
                        f"Rs.{prod['price']:,.0f}\n"
                        f"From: {prod['store'].replace('_', ' ').title()}\n\n"
                        f"Shop: {prod.get('product_url', '')}"
                    )
                    messages.append(msg)
            else:
                msg = (
                    f"New Collection Alert!\n\n"
                    f"{len(new_products)} new products just dropped on "
                    f"{new_products[0]['store'].replace('_', ' ').title()}!\n\n"
                    f"Browse: https://dropscurated.com/browse"
                )
                messages.append(msg)

        # Send messages
        for msg in messages[:3]:  # Max 3 messages per subscriber per cycle
            success = await _send_whatsapp(phone, msg)
            if success:
                sent_count += 1

            # Log alert
            await db.alert_log.insert_one({
                "phone": phone,
                "store": store_key,
                "message": msg[:200],
                "sent": success,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            })

    logger.info(f"[Alerts] Sent {sent_count} WhatsApp messages for {store_key}")
    return {"sent": sent_count}


async def _send_whatsapp(phone: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio."""
    if SANDBOX_MODE:
        logger.info(f"[Sandbox] WhatsApp to +91{phone}: {message[:80]}...")
        return True

    try:
        client = get_twilio_client()
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=message,
            to=f"whatsapp:+91{phone}",
        )
        return True
    except Exception as e:
        logger.error(f"[Twilio] Failed to send to {phone}: {e}")
        return False
