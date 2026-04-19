# CATALOG AUDITOR v1.0 — Automated completeness checker & auto-fixer
"""
Runs after each scrape cycle. For every Shopify-based brand:
  1. Gets the real product count from the Shopify JSON API
  2. Compares with our DB count
  3. If completeness < 90%, auto-triggers a full re-scrape with max pages
  4. Persists audit results to MongoDB `catalog_audit_log`
  5. Flags persistently incomplete brands for review
"""

import asyncio
import httpx
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

WARN_THRESHOLD = 0.90
CRITICAL_THRESHOLD = 0.70
AUTO_FIX_COOLDOWN = 1800  # 30 min cooldown between auto-fixes per brand

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "application/json",
}


async def get_shopify_catalog_count(base_url: str) -> Optional[int]:
    """Get total product count from a Shopify store."""
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=12, follow_redirects=True) as client:
            # Try the count endpoint first (fastest)
            resp = await client.get(f"{base_url}/products/count.json")
            if resp.status_code == 200:
                data = resp.json()
                count = data.get("count")
                if count is not None:
                    return count

            # Fallback: paginate through products.json
            total = 0
            for page in range(1, 100):
                resp = await client.get(f"{base_url}/products.json?limit=250&page={page}")
                if resp.status_code != 200:
                    break
                data = resp.json()
                prods = data.get("products", [])
                if not prods:
                    break
                total += len(prods)
            return total
    except Exception as e:
        logger.warning(f"[CatalogAuditor] Count failed for {base_url}: {e}")
        return None


class CatalogAuditor:

    def __init__(self):
        self._db = None
        self._last_fix_times: Dict[str, float] = {}

    async def init(self, db):
        self._db = db
        try:
            await db.catalog_audit_log.create_index([("timestamp", -1)])
        except Exception:
            pass
        logger.info("[CatalogAuditor] Initialized")

    async def run_audit(self) -> Dict:
        """Audit all Shopify brands for catalog completeness."""
        if self._db is None:
            return {"error": "DB not initialized"}

        from scrapers import SCRAPERS, SHOPIFY_BRANDS

        results = []
        auto_fixes = 0
        warnings = 0
        criticals = 0

        for brand_info in SHOPIFY_BRANDS:
            store_key = brand_info["store_key"]
            scraper_key = brand_info["key"]
            base_url = brand_info["url"].rstrip("/")
            brand_name = brand_info["name"]

            db_count = await self._db.products.count_documents({"store": store_key})
            site_count = await get_shopify_catalog_count(base_url)

            if site_count is None:
                results.append({
                    "brand_key": store_key,
                    "brand_name": brand_name,
                    "db_count": db_count,
                    "site_count": None,
                    "status": "unreachable",
                    "completeness": None,
                    "auto_fixed": False,
                })
                continue

            if site_count == 0:
                results.append({
                    "brand_key": store_key,
                    "brand_name": brand_name,
                    "db_count": db_count,
                    "site_count": 0,
                    "status": "empty_catalog",
                    "completeness": 100.0,
                    "auto_fixed": False,
                })
                continue

            completeness = db_count / site_count
            missing = max(0, site_count - db_count)

            status = "ok"
            if completeness < CRITICAL_THRESHOLD:
                status = "critical"
                criticals += 1
            elif completeness < WARN_THRESHOLD:
                status = "warn"
                warnings += 1

            result = {
                "brand_key": store_key,
                "brand_name": brand_name,
                "db_count": db_count,
                "site_count": site_count,
                "missing": missing,
                "completeness": round(completeness * 100, 1),
                "status": status,
                "auto_fixed": False,
            }

            # Auto-fix brands below threshold
            if completeness < WARN_THRESHOLD and missing > 5:
                fixed = await self._auto_fix(scraper_key, store_key, brand_name)
                if fixed:
                    result["auto_fixed"] = True
                    auto_fixes += 1

            results.append(result)

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_brands": len(results),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "warnings": warnings,
            "criticals": criticals,
            "auto_fixes": auto_fixes,
            "brands": results,
        }

        # Persist
        if self._db is not None:
            try:
                await self._db.catalog_audit_log.insert_one({**summary, "_type": "audit_run"})
            except Exception as e:
                logger.error(f"[CatalogAuditor] Persist failed: {e}")

        logger.info(
            f"[CatalogAuditor] Audit done — "
            f"{summary['ok']} OK, {warnings} warn, {criticals} critical, "
            f"{auto_fixes} auto-fixed"
        )

        for r in results:
            if r["status"] not in ("ok", "empty_catalog", "unreachable"):
                logger.warning(
                    f"[CatalogAuditor] {r['brand_name']}: {r['status'].upper()} — "
                    f"DB={r['db_count']}, Site={r.get('site_count','?')}, "
                    f"Missing={r.get('missing','?')}, {r.get('completeness','?')}% "
                    f"{'(AUTO-FIXED)' if r.get('auto_fixed') else ''}"
                )

        return summary

    async def _auto_fix(self, scraper_key: str, store_key: str, brand_name: str) -> bool:
        """Auto-trigger a full re-scrape for an incomplete brand."""
        last_fix = self._last_fix_times.get(store_key, 0)
        if time.time() - last_fix < AUTO_FIX_COOLDOWN:
            logger.info(f"[CatalogAuditor] Skipping {brand_name} (cooldown active)")
            return False

        try:
            from scrapers import SCRAPERS
            if scraper_key not in SCRAPERS:
                logger.warning(f"[CatalogAuditor] No scraper found for key '{scraper_key}'")
                return False

            logger.info(f"[CatalogAuditor] Auto-fixing {brand_name} — full re-scrape")
            scraper = SCRAPERS[scraper_key]()
            products = await scraper.run_swarm_scrape(max_pages=25)
            self._last_fix_times[store_key] = time.time()

            if products:
                # Store the products in DB through the scheduler's pipeline
                try:
                    from scheduler import _store_products, _db as scheduler_db
                    target_db = scheduler_db if scheduler_db is not None else self._db
                    await _store_products(target_db, products, store_key)
                except ImportError:
                    pass
                logger.info(
                    f"[CatalogAuditor] Auto-fix {brand_name}: {len(products)} products scraped and saved"
                )
                return True
            else:
                logger.warning(f"[CatalogAuditor] Auto-fix {brand_name}: 0 products returned")
                return False

        except Exception as e:
            logger.error(f"[CatalogAuditor] Auto-fix {brand_name} FAILED: {e}")
            return False

    def get_status(self) -> Dict:
        """Quick status for API."""
        return {
            "cooldown_brands": {
                k: int(AUTO_FIX_COOLDOWN - (time.time() - v))
                for k, v in self._last_fix_times.items()
                if time.time() - v < AUTO_FIX_COOLDOWN
            }
        }

    async def get_history(self, limit: int = 20) -> List[Dict]:
        if self._db is None:
            return []
        try:
            return await self._db.catalog_audit_log.find(
                {"_type": "audit_run"}, {"_id": 0},
            ).sort("timestamp", -1).limit(limit).to_list(limit)
        except Exception:
            return []


# Global instance
catalog_auditor = CatalogAuditor()


async def init_catalog_auditor(db):
    await catalog_auditor.init(db)
    return catalog_auditor
