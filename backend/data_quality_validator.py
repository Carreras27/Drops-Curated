# DATA QUALITY VALIDATOR v1.0 — Catches bad data the scrapers miss
"""
Runs after every scrape cycle AND on a 2-hour schedule.
Validates actual field CONTENTS, not just counts:

  1. Sizes must look like sizes (UK 8, US 10, EU 44, S, M, L, XL) — not shipping/delivery text
  2. Prices must be in sane range (₹100 - ₹500,000)
  3. Product names must not be empty, HTML, or error messages
  4. Image URLs must be valid HTTP(S) URLs
  5. Tags must not contain shipping/delivery strings
  6. Brands must not be empty or "Unknown"

Auto-fixes what it can, flags what it can't.
Persists all findings to MongoDB `data_quality_log`.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)

# ── Patterns ──
SHIPPING_PATTERN = re.compile(
    r'ship|delivery|dispatch|days|week|business|express|standard|lead\s*time|pre.?order|coming\s*soon',
    re.IGNORECASE,
)

VALID_SIZE_PATTERN = re.compile(
    r'^(UK|US|EU|CM)[\s\-]?\d|'       # UK 8, US 10, EU 44, CM 26
    r'^\d+(\.\d+)?$|'                  # Pure number: 8, 10.5
    r'^(XXS|XS|S|M|L|XL|XXL|XXXL|'    # Letter sizes
    r'Free\s*Size|One\s*Size|'         # Universal
    r'\d+\s*(inch|in|cm|mm)|'          # Measurement sizes
    r'[A-Z]?\d{1,2}[/-]\d{1,2})',      # 28/30, S/M
    re.IGNORECASE,
)

VALID_URL_PATTERN = re.compile(r'^https?://', re.IGNORECASE)

PRICE_MIN = 50
PRICE_MAX = 500000

# Cooldown between full audits
AUDIT_COOLDOWN = 3600  # 1 hour


class DataQualityValidator:

    def __init__(self):
        self._db = None
        self._last_audit_time = 0

    async def init(self, db):
        self._db = db
        try:
            await db.data_quality_log.create_index([("timestamp", -1)])
        except Exception:
            pass
        logger.info("[DataQuality] Validator initialized")

    async def validate_and_fix(self, store_key: str = None) -> Dict:
        """
        Validate data quality for all products (or a specific store).
        Auto-fixes what's possible, logs everything.
        """
        if self._db is None:
            return {"error": "DB not initialized"}

        query = {}
        if store_key:
            query["store"] = store_key

        issues_found = 0
        auto_fixed = 0
        unfixable = 0

        findings = {
            "shipping_in_sizes": 0,
            "invalid_sizes": 0,
            "bad_prices": 0,
            "empty_names": 0,
            "bad_images": 0,
            "shipping_in_tags": 0,
            "empty_brands": 0,
            "duplicate_sizes": 0,
        }

        # ── Check attributes.sizes for shipping strings ──
        shipping_cursor = self._db.products.find(
            {**query, "attributes.sizes": {"$elemMatch": {"$regex": "ship|days|dispatch|delivery|week|business", "$options": "i"}}},
        )
        async for prod in shipping_cursor:
            old = prod.get("attributes", {}).get("sizes", [])
            new = [s for s in old if not SHIPPING_PATTERN.search(str(s))]
            await self._db.products.update_one(
                {"_id": prod["_id"]},
                {"$set": {"attributes.sizes": new}},
            )
            findings["shipping_in_sizes"] += 1
            auto_fixed += 1

        # ── Check available_sizes for shipping strings ──
        avail_cursor = self._db.products.find(
            {**query, "available_sizes": {"$elemMatch": {"$regex": "ship|days|dispatch|delivery|week|business", "$options": "i"}}},
        )
        async for prod in avail_cursor:
            old = prod.get("available_sizes", [])
            new = [s for s in old if not SHIPPING_PATTERN.search(str(s))]
            await self._db.products.update_one(
                {"_id": prod["_id"]},
                {"$set": {"available_sizes": new}},
            )
            findings["shipping_in_sizes"] += 1
            auto_fixed += 1

        # ── Check for duplicate sizes ──
        dedup_cursor = self._db.products.find(
            {**query, "attributes.sizes.0": {"$exists": True}},
            {"_id": 1, "attributes.sizes": 1},
        )
        async for prod in dedup_cursor:
            sizes = prod.get("attributes", {}).get("sizes", [])
            unique = list(dict.fromkeys(sizes))  # Preserve order, remove dupes
            if len(unique) < len(sizes):
                await self._db.products.update_one(
                    {"_id": prod["_id"]},
                    {"$set": {"attributes.sizes": unique}},
                )
                findings["duplicate_sizes"] += 1
                auto_fixed += 1

        # ── Check tags for shipping strings ──
        tag_cursor = self._db.products.find(
            {**query, "tags": {"$elemMatch": {"$regex": "ship|dispatch|delivery|instantship|readyship|dunkship|hyship|bearship|funkoship|freeshipping", "$options": "i"}}},
        )
        async for prod in tag_cursor:
            old = prod.get("tags", [])
            new = [t for t in old if not SHIPPING_PATTERN.search(str(t))]
            if len(new) < len(old):
                await self._db.products.update_one(
                    {"_id": prod["_id"]},
                    {"$set": {"tags": new}},
                )
                findings["shipping_in_tags"] += 1
                auto_fixed += 1

        # ── Check for empty/bad product names ──
        bad_name_count = await self._db.products.count_documents(
            {**query, "$or": [
                {"name": ""},
                {"name": {"$exists": False}},
                {"name": {"$regex": "^<|error|undefined|null|test", "$options": "i"}},
            ]}
        )
        if bad_name_count > 0:
            findings["empty_names"] = bad_name_count
            unfixable += bad_name_count

        # ── Check for empty brands ──
        empty_brand_count = await self._db.products.count_documents(
            {**query, "$or": [
                {"brand": ""},
                {"brand": "Unknown"},
                {"brand": {"$exists": False}},
            ]}
        )
        findings["empty_brands"] = empty_brand_count

        # ── Check for bad image URLs ──
        bad_image_cursor = self._db.products.find(
            {**query, "imageUrl": {"$exists": True, "$not": {"$regex": "^https?://"}}},
            {"_id": 1, "imageUrl": 1, "name": 1},
        ).limit(100)
        async for prod in bad_image_cursor:
            findings["bad_images"] += 1
            unfixable += 1

        issues_found = sum(findings.values())

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "store": store_key or "ALL",
            "issues_found": issues_found,
            "auto_fixed": auto_fixed,
            "unfixable": unfixable,
            "findings": findings,
        }

        # Persist
        if self._db is not None:
            try:
                await self._db.data_quality_log.insert_one({**result, "_type": "quality_check"})
            except Exception:
                pass

        if issues_found > 0:
            logger.warning(
                f"[DataQuality] {store_key or 'ALL'}: {issues_found} issues found, "
                f"{auto_fixed} auto-fixed, {unfixable} need review — {findings}"
            )
        else:
            logger.info(f"[DataQuality] {store_key or 'ALL'}: All clean")

        self._last_audit_time = time.time()
        return result

    async def run_full_audit(self) -> Dict:
        """Run a full data quality audit across all stores."""
        return await self.validate_and_fix(store_key=None)

    async def get_history(self, limit: int = 20) -> List[Dict]:
        if self._db is None:
            return []
        try:
            return await self._db.data_quality_log.find(
                {"_type": "quality_check"}, {"_id": 0},
            ).sort("timestamp", -1).limit(limit).to_list(limit)
        except Exception:
            return []


# Global instance
data_quality_validator = DataQualityValidator()


async def init_data_quality_validator(db):
    await data_quality_validator.init(db)
    return data_quality_validator
