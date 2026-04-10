"""
Shopify Scraper with Anti-Blocking Protection
Uses the public JSON API endpoint which never gets blocked.
"""
import logging
from typing import Optional, List, Dict
from .base import BaseScraper
from .scraper_utils import (
    product_delay,
    fingerprint_cache,
    BlockedError
)

logger = logging.getLogger(__name__)


class ShopifyScraper(BaseScraper):
    """
    Generic scraper for all Shopify-based stores.
    Uses the public /products.json endpoint which is designed for public access
    and very rarely gets blocked.
    """

    def __init__(self, brand_name: str, store_key: str, base_url: str):
        super().__init__()
        self.brand_name = brand_name
        self.store_key = store_key
        self.base_url = base_url.rstrip("/")
        # Shopify JSON API rarely needs proxy
        self.use_proxy = False
    
    async def scrape_products(self, max_pages: int = 5) -> List[dict]:
        """
        Scrape products using Shopify's public JSON API.
        This endpoint is designed for public consumption and doesn't get blocked.
        """
        products = []
        total_found = 0
        new_count = 0
        
        try:
            for page in range(1, max_pages + 1):
                # Shopify public JSON API endpoint
                url = f"{self.base_url}/products.json?limit=250&page={page}"
                logger.info(f"[{self.store_key}] Fetching page {page} via JSON API")
                
                try:
                    # Use protected fetch
                    data, raw_content = await self.fetch_with_protection(
                        url, 
                        json_response=True,
                        timeout=25
                    )
                    
                    page_products = data.get("products", [])
                    
                    if not page_products:
                        logger.info(f"[{self.store_key}] No more products on page {page}")
                        break
                    
                    total_found += len(page_products)
                    
                    for raw in page_products:
                        # Check fingerprint to skip unchanged products
                        product_id = str(raw.get("id", ""))
                        updated_at = raw.get("updated_at", "")
                        
                        # Always process but track if new/changed
                        is_new = self.should_process_product(product_id, updated_at)
                        
                        p = self.normalize_product(raw)
                        if p:
                            products.append(p)
                            if is_new:
                                new_count += 1
                    
                    # Random delay between pages
                    if page < max_pages:
                        await product_delay()
                        
                except BlockedError as e:
                    logger.error(f"[{self.store_key}] Blocked: {e}")
                    self.report_failure(str(e))
                    raise
                except Exception as e:
                    logger.error(f"[{self.store_key}] Page {page} error: {e}")
                    # Continue to next page on non-blocking errors
                    if page == 1:
                        # First page failure is critical
                        raise
                    break
            
            # Update fingerprints for processed products
            await fingerprint_cache.bulk_update(products)
            
            # Report success
            self.report_success(products_found=len(products), new_products=new_count)
            logger.info(f"[{self.store_key}] Total scraped: {len(products)} ({new_count} new/changed)")
            
        except Exception as e:
            self.report_failure(str(e))
            raise
        
        return products

    def normalize_product(self, raw: dict) -> Optional[dict]:
        """Convert Shopify product data to standard format."""
        title = raw.get("title", "").strip()
        if not title:
            return None

        variants = raw.get("variants", [])
        prices = []
        for v in variants:
            try:
                price = float(v.get("price", 0))
                if price > 0:
                    prices.append(price)
            except (ValueError, TypeError):
                continue

        if not prices:
            return None

        images = raw.get("images", [])
        image_url = images[0]["src"] if images else ""
        vendor = raw.get("vendor", "")
        handle = raw.get("handle", "")
        tags = raw.get("tags", [])
        product_type = (raw.get("product_type") or "").lower()
        product_id = str(raw.get("id", ""))
        updated_at = raw.get("updated_at", "")

        category = self._guess_category(title, product_type, tags)

        available_sizes = []
        for v in variants:
            if v.get("available"):
                size = v.get("option2") or v.get("option1") or v.get("title", "")
                if size and size != "Default Title":
                    available_sizes.append(size)

        compare_prices = []
        for v in variants:
            cp = v.get("compare_at_price")
            if cp:
                try:
                    compare_prices.append(float(cp))
                except (ValueError, TypeError):
                    pass

        # Check for limited edition indicators
        is_limited = self._check_limited_edition(title, tags)

        # Filter out shipping-related tags
        filtered_tags = self._filter_shipping_tags([str(t).lower() for t in tags[:15]])
        
        # Filter out shipping-related sizes
        filtered_sizes = self._filter_shipping_sizes(available_sizes[:20])

        return {
            "id": f"prod_{self.store_key}_{product_id}",
            "shopify_id": product_id,
            "name": title,
            "brand": vendor or self.brand_name,
            "category": category,
            "price": min(prices),
            "original_price": max(compare_prices) if compare_prices else min(prices),
            "image_url": image_url,
            "product_url": f"{self.base_url}/products/{handle}",
            "store": self.store_key,
            "in_stock": any(v.get("available") for v in variants),
            "available_sizes": filtered_sizes,
            "tags": filtered_tags[:10],
            "is_limited": is_limited,
            "updated_at": updated_at,
            "scraped_at": self.now_iso(),
        }

    def _guess_category(self, title: str, product_type: str, tags: list) -> str:
        """Guess product category from title, type, and tags."""
        combined = f"{title} {product_type} {' '.join(str(t) for t in tags)}".lower()

        shoes_kw = ["shoe", "sneaker", "boot", "slide", "sandal", "slipper", "foam", "dunk",
                     "jordan", "yeezy", "samba", "force", "footwear", "runner", "trainer",
                     "cloudnova", "gel-", "990", "550", "574", "af1", "air max"]
        clothes_kw = ["tee", "t-shirt", "tshirt", "shirt", "hoodie", "jacket", "pant", "trouser",
                      "short", "jogger", "cargo", "sweat", "dress", "top", "polo", "kurta",
                      "bottom", "denim", "jean", "corset", "co-ord", "coord", "vest", "tank"]
        accessories_kw = ["cap", "hat", "bag", "wallet", "watch", "chain", "ring", "sock",
                          "belt", "scarf", "mask", "keychain", "phone", "case", "accessory",
                          "sunglasses", "perfume", "sticker"]
        collectables_kw = ["bearbrick", "figure", "figurine", "toy", "lego", "funko", 
                           "collectible", "collectable", "medicom", "kaws"]

        if any(k in combined for k in shoes_kw):
            return "SHOES"
        if any(k in combined for k in collectables_kw):
            return "COLLECTABLES"
        if any(k in combined for k in accessories_kw):
            return "ACCESSORIES"
        if any(k in combined for k in clothes_kw):
            return "CLOTHES"
        return "CLOTHES"  # Default for streetwear brands
    
    def _check_limited_edition(self, title: str, tags: list) -> bool:
        """Check if product is limited edition."""
        combined = f"{title} {' '.join(str(t) for t in tags)}".lower()
        limited_kw = ["limited", "exclusive", "collab", "special edition", "only in india",
                      "numbered", "1 of", "drop", "rare", "sold out"]
        return any(k in combined for k in limited_kw)
    
    def _filter_shipping_tags(self, tags: list) -> list:
        """Remove shipping-related tags from product tags."""
        shipping_keywords = [
            'ship', 'shipping', 'delivery', 'dispatch', 'express', 'days',
            'instantship', 'dunkship', 'hyship', 'bearship', 'funkoship',
            'readyship', 'free-delivery', 'freeshipping', 'fast shipping',
            'lead time', 'ships in', 'dispatch in'
        ]
        filtered = []
        for tag in tags:
            tag_lower = tag.lower()
            if not any(kw in tag_lower for kw in shipping_keywords):
                filtered.append(tag)
        return filtered
    
    def _filter_shipping_sizes(self, sizes: list) -> list:
        """Remove shipping-related strings from sizes array."""
        shipping_keywords = [
            'ship', 'shipping', 'delivery', 'dispatch', 'days', 'week',
            'lead time', 'ships in', 'dispatch in', 'express', 'standard',
            'free', 'business'
        ]
        filtered = []
        for size in sizes:
            size_lower = str(size).lower()
            if not any(kw in size_lower for kw in shipping_keywords):
                filtered.append(size)
        return filtered


# For backwards compatibility
HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
