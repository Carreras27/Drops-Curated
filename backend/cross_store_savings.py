"""
Cross-Store Savings Scanner

Nightly job that finds products which are available cheaper at another store
(via the token-overlap + type-bucket matcher in server.py), stores the current
savings feed, and queues alerts to subscribers whose preferences match.

Collection schema: `cross_store_savings`
  {
    id: str,                # productId (source product)
    productId: str,
    name: str,
    brand: str,
    imageUrl: str,
    sourceStore: str,
    sourcePrice: float,
    cheapestStore: str,
    cheapestPrice: float,
    cheapestProductUrl: str,
    cheapestMatchedName: str,
    savingsAmount: float,
    savingsPct: float,
    category: str,
    sizes: list,
    updatedAt: ISO8601 str,
  }
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from freshness import _parse_iso, _hours_since, MAX_ALERT_AGE_HOURS, log_stale_skip

logger = logging.getLogger(__name__)

# Savings thresholds — must beat BOTH to be considered "meaningful"
MIN_SAVINGS_AMOUNT = 500.0    # INR
MIN_SAVINGS_PCT = 10.0        # percent


def _is_price_record_fresh(price_doc: dict) -> tuple[bool, Optional[float]]:
    """Check a price record against MAX_ALERT_AGE_HOURS."""
    if not price_doc:
        return False, None
    age = _hours_since(_parse_iso(price_doc.get('lastScrapedAt')))
    if age is None:
        return False, None
    return age <= MAX_ALERT_AGE_HOURS, age


class CrossStoreSavingsScanner:
    def __init__(self):
        self.db = None
        self.last_run = None
        self.last_result = {}

    async def init(self, db):
        self.db = db

    async def run_scan(self, _find_cross_store_prices) -> dict:
        """Scan all active products; upsert current savings; queue alerts for NEW savings.

        `_find_cross_store_prices` is injected from server.py to avoid a circular import.
        """
        if self.db is None:
            return {'error': 'DB not initialized'}

        started = datetime.now(timezone.utc)
        logger.info("[CrossStoreSavings] === Scan starting ===")

        scanned = 0
        savings_found = 0
        new_savings = 0
        removed = 0
        stale_skipped = 0

        # Build a snapshot of currently-known savings so we can diff at the end
        prev_ids = set()
        try:
            async for doc in self.db.cross_store_savings.find({}, {'_id': 0, 'id': 1}):
                prev_ids.add(doc['id'])
        except Exception:
            pass

        seen_ids = set()

        # Iterate all active products with a direct price
        cursor = self.db.products.find(
            {'isActive': True},
            {'_id': 0}
        )

        async for product in cursor:
            scanned += 1
            pid = product.get('id')
            if not pid:
                continue

            # Source (direct) price
            src_price_doc = await self.db.prices.find_one(
                {'productId': pid, 'store': product.get('store')},
                {'_id': 0}
            )
            if not src_price_doc:
                continue
            src_price = src_price_doc.get('currentPrice') or 0
            if src_price <= 0:
                continue

            # Freshness gate — skip if source price data is stale.
            # Prevents "phantom savings" from brands whose scraper has gone silent.
            fresh, age = _is_price_record_fresh(src_price_doc)
            if not fresh:
                stale_skipped += 1
                continue

            # Find cross-store matches (reuse server.py matcher)
            try:
                cross = await _find_cross_store_prices(product, [src_price_doc])
            except Exception as e:
                logger.debug(f"[CrossStoreSavings] Match error for {pid}: {e}")
                continue
            if not cross:
                continue

            # Freshness gate — drop any cross-store candidate whose price is
            # stale. Otherwise we'd be comparing fresh data against outdated
            # competitor data and emit a wrong saving.
            in_stock_cross = [
                c for c in cross
                if c.get('inStock', True)
                and (c.get('currentPrice') or 0) > 0
                and _is_price_record_fresh(c)[0]
            ]
            if not in_stock_cross:
                continue
            cheapest = min(in_stock_cross, key=lambda c: c['currentPrice'])

            savings_amount = round(src_price - cheapest['currentPrice'], 2)
            if savings_amount <= 0:
                continue
            savings_pct = round((savings_amount / src_price) * 100, 1)

            if savings_amount < MIN_SAVINGS_AMOUNT or savings_pct < MIN_SAVINGS_PCT:
                continue

            savings_found += 1
            seen_ids.add(pid)

            record = {
                'id': pid,
                'productId': pid,
                'name': product.get('name'),
                'brand': product.get('brand'),
                'imageUrl': product.get('imageUrl'),
                'sourceStore': product.get('store'),
                'sourcePrice': src_price,
                'cheapestStore': cheapest.get('store'),
                'cheapestPrice': cheapest['currentPrice'],
                'cheapestProductUrl': cheapest.get('productUrl'),
                'cheapestMatchedName': cheapest.get('matchedFrom'),
                'savingsAmount': savings_amount,
                'savingsPct': savings_pct,
                'category': product.get('aiCategory') or product.get('category'),
                'subcategory': product.get('aiSubcategory'),
                'gender': product.get('aiGender'),
                'sizes': (product.get('attributes') or {}).get('sizes', []),
                'updatedAt': datetime.now(timezone.utc).isoformat(),
            }

            await self.db.cross_store_savings.update_one(
                {'id': pid},
                {'$set': record},
                upsert=True,
            )

            # Detect NEW savings (not present in previous snapshot) → queue alerts
            if pid not in prev_ids:
                new_savings += 1
                try:
                    await self._queue_cross_store_alerts(record)
                except Exception as e:
                    logger.error(f"[CrossStoreSavings] Alert queue failed for {pid}: {e}")

        # Clean up stale savings: (a) no longer cheaper, (b) source data went stale
        stale_ids = prev_ids - seen_ids
        if stale_ids:
            try:
                res = await self.db.cross_store_savings.delete_many({'id': {'$in': list(stale_ids)}})
                removed = res.deleted_count
            except Exception:
                pass

        self.last_run = datetime.now(timezone.utc).isoformat()
        self.last_result = {
            'scanned': scanned,
            'stale_skipped': stale_skipped,
            'savings_found': savings_found,
            'new_savings': new_savings,
            'removed': removed,
            'max_alert_age_hours': MAX_ALERT_AGE_HOURS,
            'duration_s': round((datetime.now(timezone.utc) - started).total_seconds(), 1),
        }
        logger.info(f"[CrossStoreSavings] === Scan complete: {self.last_result} ===")
        return self.last_result

    async def _queue_cross_store_alerts(self, record: dict):
        """Queue cross-store savings alerts to subscribers whose preferences match.

        Uses the same daily_digest collection the existing alert pipeline uses,
        so existing digest sender picks it up automatically.
        """
        # Reuse existing filter helpers from alerts.py
        from alerts import (
            _matches_keywords,
            _matches_price_range,
            _matches_category,
            _matches_gender,
            _matches_sizes,
        )

        subscribers = await self.db.subscribers.find(
            {'isActive': True, 'isPaid': True},
            {'_id': 0}
        ).to_list(2000)

        queued = 0
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        alert_payload = {
            'type': 'cross_store_save',
            'data': {
                'productId': record['productId'],
                'name': record['name'],
                'brand': record['brand'],
                'image_url': record.get('imageUrl'),
                'cheapestStore': record['cheapestStore'],
                'cheapestPrice': record['cheapestPrice'],
                'sourcePrice': record['sourcePrice'],
                'savingsAmount': record['savingsAmount'],
                'savingsPct': record['savingsPct'],
                'cheapestProductUrl': record.get('cheapestProductUrl'),
                'category': record.get('category', ''),
                'sizes': record.get('sizes', []),
            }
        }

        for sub in subscribers:
            phone = sub.get('phone')
            if not phone:
                continue
            prefs = sub.get('preferences', {}) or {}

            # Brand filter
            pref_brands = prefs.get('brands') or []
            if pref_brands and record['sourceStore'] not in pref_brands and record['cheapestStore'] not in pref_brands:
                continue

            # Opt-in: only users with cross_store_save in alert_types (defaults ON if unset)
            pref_types = prefs.get('alert_types', ['price_drop', 'new_release', 'cross_store_save'])
            if 'cross_store_save' not in pref_types and 'price_drop' not in pref_types:
                continue

            # Specificity filters
            if not _matches_gender({'name': record['name'], 'tags': [], 'attributes': {}}, prefs.get('gender', 'all')):
                continue
            if not _matches_category(record.get('category', ''), prefs.get('categories', [])):
                continue
            if not _matches_sizes(record.get('sizes', []), prefs.get('sizes', [])):
                continue
            if not _matches_price_range(record['cheapestPrice'], prefs.get('price_range', {})):
                continue
            if not _matches_keywords(record['name'], '', prefs.get('keywords', [])):
                continue

            # Drop threshold (reuse price_drop threshold for cross_store_save; default 10%)
            threshold = prefs.get('drop_threshold', 10)
            if record['savingsPct'] < threshold:
                continue

            # Queue into daily digest
            await self.db.daily_digest.update_one(
                {'phone': phone, 'date': today},
                {
                    '$push': {'alerts': alert_payload},
                    '$set': {'updatedAt': datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
            queued += 1

        if queued:
            logger.info(f"[CrossStoreSavings] Queued cross-store alert for {record['name'][:40]}... to {queued} subscribers")

    def get_status(self) -> dict:
        return {
            'last_run': self.last_run,
            'last_result': self.last_result,
            'thresholds': {
                'min_savings_amount': MIN_SAVINGS_AMOUNT,
                'min_savings_pct': MIN_SAVINGS_PCT,
            },
        }


cross_store_savings_scanner = CrossStoreSavingsScanner()


async def init_cross_store_savings_scanner(db):
    await cross_store_savings_scanner.init(db)
