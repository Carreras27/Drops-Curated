"""
Alert freshness guard.

Rule: NEVER send a price-related alert (price_drop, new_drop, restock,
cross_store_save, daily_digest) if the underlying price data is older than
MAX_ALERT_AGE_HOURS. Stale data has caused real user-facing incidents where
alerts cite prices that no longer reflect the live store (see EVEMEN ₹3,486 →
₹1,800 incident, Apr 2026).

This module is intentionally a single small helper imported by both
`alerts.py` (instant alert path) and `server.py::send_daily_digests`
(digest path). Keeping it centralised means the cap is a *system-wide*
invariant, not a case-by-case decision.

Bonus: stale alerts are logged to `stale_alerts_log` so the admin can
spot brands whose scraper is silently stuck without looking at raw
scraper-health dashboards.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Configurable cap so ops can tune without a redeploy. Default: 10 hours.
MAX_ALERT_AGE_HOURS = int(os.environ.get("MAX_ALERT_AGE_HOURS", "10"))


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp. Returns None if unparseable."""
    if not ts:
        return None
    try:
        # Handle trailing Z
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _hours_since(ts: Optional[datetime]) -> Optional[float]:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - ts
    return delta.total_seconds() / 3600.0


async def is_price_fresh(db, product_id: str, store: str) -> tuple[bool, Optional[float]]:
    """
    True if the price record for (product_id, store) is within MAX_ALERT_AGE_HOURS.
    Returns (is_fresh, age_in_hours). age_in_hours is None when no price record
    is found (which we treat as stale — do not alert on ghost products).
    """
    if not product_id or not store:
        return False, None
    price_doc = await db.prices.find_one(
        {"productId": product_id, "store": store},
        {"_id": 0, "lastScrapedAt": 1},
    )
    if not price_doc:
        return False, None
    age = _hours_since(_parse_iso(price_doc.get("lastScrapedAt")))
    if age is None:
        return False, None
    return age <= MAX_ALERT_AGE_HOURS, age


async def is_brand_fresh(db, store_key: str) -> tuple[bool, Optional[float]]:
    """
    Fallback freshness check for cases where we have a store key but no specific
    product (e.g. brand-level alerts, new-drop announcements).
    """
    if not store_key:
        return False, None
    brand = await db.brands.find_one(
        {"$or": [{"storeKey": store_key}, {"store_key": store_key}]},
        {"_id": 0, "lastScrapedAt": 1},
    )
    if not brand:
        return False, None
    age = _hours_since(_parse_iso(brand.get("lastScrapedAt")))
    if age is None:
        return False, None
    return age <= MAX_ALERT_AGE_HOURS, age


async def log_stale_skip(db, *, alert_type: str, reason: str,
                        product_id: Optional[str] = None,
                        store: Optional[str] = None,
                        age_hours: Optional[float] = None,
                        phone: Optional[str] = None,
                        email: Optional[str] = None,
                        extra: Optional[dict] = None) -> None:
    """Record a skipped alert so the admin panel can surface the problem."""
    try:
        doc = {
            "alertType": alert_type,
            "reason": reason,
            "productId": product_id,
            "store": store,
            "ageHours": round(age_hours, 2) if age_hours is not None else None,
            "maxAllowedHours": MAX_ALERT_AGE_HOURS,
            "phone": phone,
            "email": email,
            "extra": extra or {},
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        await db.stale_alerts_log.insert_one(doc)
        logger.warning(
            f"[Freshness] Skipped {alert_type} — {reason} "
            f"(product={product_id} store={store} age={doc['ageHours']}h cap={MAX_ALERT_AGE_HOURS}h)"
        )
    except Exception as e:
        # Never let logging break the alert path
        logger.error(f"[Freshness] Failed to log stale skip: {e}")
