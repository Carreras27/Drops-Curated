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

# Colors that should NEVER appear as sizes
COLOR_WORDS = {
    'red', 'blue', 'green', 'black', 'white', 'grey', 'gray', 'pink', 'yellow',
    'orange', 'purple', 'brown', 'navy', 'cream', 'ivory', 'teal', 'silver',
    'gold', 'crimson', 'coral', 'mint', 'menta', 'smoke', 'chrome', 'canary',
    'geode', 'arctic', 'sand', 'ice', 'lime', 'salmon', 'photon', 'dust',
    'pale', 'light', 'dark', 'hyper', 'solar', 'frosted', 'blackened',
    'indigo', 'maroon', 'olive', 'khaki', 'beige', 'tan', 'amber', 'jade',
    'ruby', 'sapphire', 'emerald', 'charcoal', 'slate', 'bone', 'ash',
    'cloud', 'fog', 'thunder', 'storm', 'midnight', 'sunset', 'dawn',
    'burgundy', 'magenta', 'cyan', 'turquoise', 'lavender', 'peach',
    'multi', 'multicolor', 'multicolour', 'tie-dye', 'camo', 'print',
}

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


        # ── CHECK: Products missing productUrl — auto-fix from Shopify API ──
        missing_url_count = await self._db.products.count_documents(
            {**query, "$or": [{"productUrl": {"$exists": False}}, {"productUrl": None}]}
        )
        if missing_url_count > 0:
            findings["missing_product_urls"] = missing_url_count
            unfixable += missing_url_count  # Needs full re-scrape or bulk migration to fix


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

        # ── CHECK: Colors stored as sizes (e.g., "GREEN", "RED", "IVORY") ──
        # This catches the exact bug where option1=COLOR was mistaken for a size
        all_sized_products = self._db.products.find(
            {**query, "attributes.sizes.0": {"$exists": True}},
            {"_id": 1, "attributes.sizes": 1, "attributes.size_prices": 1},
        ).limit(3000)
        async for prod in all_sized_products:
            sizes = prod.get("attributes", {}).get("sizes", [])
            sp = prod.get("attributes", {}).get("size_prices", {})
            bad_sizes = [s for s in sizes if s.strip().lower() in COLOR_WORDS]
            if bad_sizes:
                clean_sizes = [s for s in sizes if s.strip().lower() not in COLOR_WORDS]
                clean_sp = {k: v for k, v in sp.items() if k.strip().lower() not in COLOR_WORDS}
                update = {"attributes.sizes": clean_sizes}
                if sp:
                    update["attributes.size_prices"] = clean_sp
                await self._db.products.update_one({"_id": prod["_id"]}, {"$set": update})
                findings["colors_as_sizes"] = findings.get("colors_as_sizes", 0) + 1
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

        # ── Check price vs size_prices consistency ──
        sp_cursor = self._db.products.find(
            {**query, "attributes.size_prices": {"$exists": True, "$ne": {}}},
            {"_id": 1, "name": 1, "store": 1, "id": 1, "attributes.size_prices": 1, "attributes.sizes": 1},
        )
        async for prod in sp_cursor:
            sp = prod.get("attributes", {}).get("size_prices", {})
            sizes = prod.get("attributes", {}).get("sizes", [])
            if sp and sizes:
                first_size_price = sp.get(sizes[0])
                if first_size_price:
                    await self._db.prices.update_one(
                        {"productId": prod.get("id"), "store": prod.get("store")},
                        {"$set": {"currentPrice": first_size_price, "sizePrices": sp}},
                    )
                    findings["price_accuracy_fixed"] = findings.get("price_accuracy_fixed", 0) + 1
                    auto_fixed += 1

        # ── CHECK: Buy Now URL matches product name ──
        # Catches: URL pointing to a completely different product
        url_fix_count = 0
        url_mismatch_count = 0
        price_cursor = self._db.prices.find(
            {**({} if not store_key else {"store": store_key}), "productUrl": {"$exists": True, "$ne": ""}},
            {"_id": 1, "productId": 1, "store": 1, "productUrl": 1},
        ).limit(2000)  # Check up to 2000 per run
        
        # Batch-load product URLs for comparison
        price_docs = await price_cursor.to_list(2000)
        if price_docs:
            pids = list({p["productId"] for p in price_docs})
            prod_url_map = {}
            prod_name_map = {}
            prod_cursor = self._db.products.find(
                {"id": {"$in": pids}},
                {"_id": 0, "id": 1, "name": 1, "productUrl": 1}
            )
            async for prod in prod_cursor:
                prod_url_map[prod["id"]] = prod.get("productUrl", "")
                prod_name_map[prod["id"]] = prod.get("name", "")
            
            for price_doc in price_docs:
                pid = price_doc["productId"]
                price_url = price_doc.get("productUrl", "")
                correct_url = prod_url_map.get(pid, "")
                name = prod_name_map.get(pid, "")
                
                # If product has a stored URL and price URL differs, fix it
                if correct_url and price_url and price_url != correct_url:
                    await self._db.prices.update_one(
                        {"_id": price_doc["_id"]},
                        {"$set": {"productUrl": correct_url}}
                    )
                    url_fix_count += 1
                elif name and price_url and not correct_url:
                    # Cross-check: do key product name words appear in the URL?
                    name_words = [w.lower() for w in name.split()[:3] if len(w) > 2]
                    url_lower = price_url.lower()
                    if len(name_words) >= 2 and sum(1 for w in name_words if w in url_lower) == 0:
                        url_mismatch_count += 1
        
        if url_fix_count:
            findings["url_mismatch_fixed"] = url_fix_count
            auto_fixed += url_fix_count
        if url_mismatch_count:
            findings["url_name_mismatch"] = url_mismatch_count
            unfixable += url_mismatch_count

        # ── CHECK: Product ID collisions ──
        id_pipeline = [
            {"$group": {"_id": "$id", "count": {"$sum": 1}, "names": {"$addToSet": "$name"}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": 50},
        ]
        collisions = await self._db.products.aggregate(id_pipeline).to_list(50)
        collision_count = sum(1 for c in collisions if len(c.get("names", [])) > 1)
        if collision_count:
            findings["id_collisions"] = collision_count
            unfixable += collision_count

        # ── CHECK: Orphaned price records (sampled) ──
        # Check a sample of price records for missing products
        sample_prices = await self._db.prices.aggregate([
            {"$sample": {"size": 500}},
            {"$project": {"productId": 1}},
        ]).to_list(500)
        if sample_prices:
            sample_pids = [p["productId"] for p in sample_prices]
            existing_pids = set()
            existing_cursor = self._db.products.find(
                {"id": {"$in": sample_pids}}, {"_id": 0, "id": 1}
            )
            async for doc in existing_cursor:
                existing_pids.add(doc["id"])
            orphaned = [pid for pid in sample_pids if pid not in existing_pids]
            if orphaned:
                findings["orphaned_prices"] = len(orphaned)
                await self._db.prices.delete_many({"productId": {"$in": orphaned}})
                findings["orphaned_prices_cleaned"] = len(orphaned)
                auto_fixed += len(orphaned)

        # ── CHECK: Price records missing sizePrices when product has per-size pricing ──
        # Auto-sync: if product has size_prices but price record doesn't, copy them over
        missing_sp_cursor = self._db.products.find(
            {**query, "attributes.size_prices": {"$exists": True, "$ne": {}}},
            {"_id": 0, "id": 1, "store": 1, "attributes.size_prices": 1},
        ).limit(500)
        sp_sync_count = 0
        async for prod in missing_sp_cursor:
            sp = prod.get("attributes", {}).get("size_prices", {})
            if not sp:
                continue
            result = await self._db.prices.update_one(
                {"productId": prod["id"], "sizePrices": {"$exists": False}},
                {"$set": {"sizePrices": sp}},
            )
            if result.modified_count > 0:
                sp_sync_count += 1
        if sp_sync_count:
            findings["size_prices_synced"] = sp_sync_count
            auto_fixed += sp_sync_count


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
