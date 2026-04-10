"""
Mids and Lows Scraper - Shopify Store
Premium sneaker and streetwear retailer
"""
import json
import httpx
import logging
from typing import Optional, List
from .base import BaseScraper
from .scraper_utils import product_delay, fingerprint_cache, get_random_user_agent

logger = logging.getLogger(__name__)


class MidsAndLowsScraper(BaseScraper):
    """
    Scraper for Mids and Lows - Shopify-based store.
    Uses the public /products.json endpoint.
    """
    brand_name = "Mids and Lows"
    store_key = "MIDS_AND_LOWS"
    base_url = "https://www.midsandlows.com"
    use_proxy = False  # Shopify JSON API rarely needs proxy

    async def scrape_products(self, max_pages: int = 5) -> List[dict]:
        """Scrape products using Shopify's public JSON API."""
        products = []
        total_found = 0
        new_count = 0

        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
                for page in range(1, max_pages + 1):
                    url = f"{self.base_url}/products.json?limit=250&page={page}"
                    logger.info(f"[{self.store_key}] Fetching page {page} via JSON API")

                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()

                        page_products = data.get("products", [])
                        if not page_products:
                            logger.info(f"[{self.store_key}] No more products on page {page}")
                            break

                        total_found += len(page_products)

                        for raw in page_products:
                            product_id = str(raw.get("id", ""))
                            updated_at = raw.get("updated_at", "")
                            is_new = self.should_process_product(product_id, updated_at)

                            p = self.normalize_product(raw)
                            if p:
                                products.append(p)
                                if is_new:
                                    new_count += 1

                        if page < max_pages:
                            await product_delay()

                    except Exception as e:
                        logger.error(f"[{self.store_key}] Page {page} error: {e}")
                        if page == 1:
                            raise
                        break

            await fingerprint_cache.bulk_update(products)
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

        # Filter shipping-related tags and sizes
        filtered_tags = self._filter_shipping_tags([str(t).lower() for t in tags[:15]])
        filtered_sizes = self._filter_shipping_sizes(available_sizes[:20])

        is_limited = self._check_limited_edition(title, tags)

        return {
            "id": f"prod_{self.store_key}_{product_id}",
            "shopify_id": product_id,
            "name": title,
            "brand": vendor or self._extract_brand(title),
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

        # Check watches first (Mids and Lows sells Casio/G-Shock)
        watch_kw = ["watch", "casio", "g-shock", "gshock", "g shock", "timepiece", "digital watch",
                    "analog", "mtp-", "mrw-", "ae-", "la-", "dw-", "ga-", "gw-", "gwg-"]
        if any(k in combined for k in watch_kw):
            return "ACCESSORIES"

        shoes_kw = ["shoe", "sneaker", "boot", "slide", "sandal", "slipper", "foam", "dunk",
                    "jordan", "yeezy", "samba", "force", "footwear", "runner", "trainer",
                    "gel-", "990", "550", "574", "af1", "air max"]
        clothes_kw = ["tee", "t-shirt", "tshirt", "shirt", "hoodie", "jacket", "pant", "trouser",
                      "short", "jogger", "cargo", "sweat", "dress", "top", "polo",
                      "bottom", "denim", "jean", "vest", "tank"]
        accessories_kw = ["cap", "hat", "bag", "wallet", "chain", "ring", "sock",
                         "belt", "scarf", "mask", "keychain", "phone", "case", "accessory",
                         "sunglasses", "perfume", "sticker", "beanie"]

        if any(k in combined for k in shoes_kw):
            return "SHOES"
        if any(k in combined for k in accessories_kw):
            return "ACCESSORIES"
        if any(k in combined for k in clothes_kw):
            return "CLOTHES"
        return "ACCESSORIES"  # Default for watch-heavy stores

    def _check_limited_edition(self, title: str, tags: list) -> bool:
        """Check if product is limited edition."""
        combined = f"{title} {' '.join(str(t) for t in tags)}".lower()
        limited_kw = ["limited", "exclusive", "collab", "special edition",
                      "numbered", "1 of", "drop", "rare"]
        return any(k in combined for k in limited_kw)

    def _extract_brand(self, name: str) -> str:
        """Extract brand from product name."""
        known = [
            "Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Yeezy", "Casio", "G-Shock", "Crocs", "Hoka",
            "On Running", "Saucony", "Salomon", "Birkenstock"
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        return name.split()[0] if name else "Mids and Lows"
