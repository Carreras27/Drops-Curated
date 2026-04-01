import httpx
import logging
from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)


class ShopifyScraper(BaseScraper):
    """Generic scraper for all Shopify-based stores"""

    def __init__(self, brand_name: str, store_key: str, base_url: str):
        self.brand_name = brand_name
        self.store_key = store_key
        self.base_url = base_url.rstrip("/")

    async def scrape_products(self, max_pages: int = 5) -> list[dict]:
        products = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}/products.json?limit=250&page={page}"
                logger.info(f"[{self.store_key}] Fetching page {page}")
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    page_products = data.get("products", [])
                    if not page_products:
                        break
                    for raw in page_products:
                        p = self.normalize_product(raw)
                        if p:
                            products.append(p)
                except Exception as e:
                    logger.error(f"[{self.store_key}] Page {page} error: {e}")
                    break
        logger.info(f"[{self.store_key}] Total scraped: {len(products)}")
        return products

    def normalize_product(self, raw: dict) -> dict | None:
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

        return {
            "name": title,
            "brand": vendor or self.brand_name,
            "category": category,
            "price": min(prices),
            "original_price": max(compare_prices) if compare_prices else min(prices),
            "image_url": image_url,
            "product_url": f"{self.base_url}/products/{handle}",
            "store": self.store_key,
            "in_stock": any(v.get("available") for v in variants),
            "available_sizes": available_sizes[:20],
            "tags": [str(t).lower() for t in tags[:10]],
            "scraped_at": self.now_iso(),
        }

    def _guess_category(self, title: str, product_type: str, tags: list) -> str:
        combined = f"{title} {product_type} {' '.join(str(t) for t in tags)}".lower()

        shoes_kw = ["shoe", "sneaker", "boot", "slide", "sandal", "slipper", "foam", "dunk",
                     "jordan", "yeezy", "samba", "force", "footwear", "runner", "trainer"]
        clothes_kw = ["tee", "t-shirt", "tshirt", "shirt", "hoodie", "jacket", "pant", "trouser",
                      "short", "jogger", "cargo", "sweat", "dress", "top", "polo", "kurta",
                      "bottom", "denim", "jean", "corset", "co-ord", "coord", "vest", "tank"]
        accessories_kw = ["cap", "hat", "bag", "wallet", "watch", "chain", "ring", "sock",
                          "belt", "scarf", "mask", "keychain", "phone", "case", "accessory",
                          "sunglasses", "perfume", "sticker"]

        if any(k in combined for k in shoes_kw):
            return "SHOES"
        if any(k in combined for k in clothes_kw):
            return "CLOTHES"
        if any(k in combined for k in accessories_kw):
            return "ACCESSORIES"
        return "CLOTHES"  # Default for streetwear brands
