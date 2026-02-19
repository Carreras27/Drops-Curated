import httpx
import logging
from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)


class CrepDogCrewScraper(BaseScraper):
    brand_name = "Crep Dog Crew"
    store_key = "CREPDOG_CREW"
    base_url = "https://crepdogcrew.com"

    async def scrape_products(self, max_pages: int = 3) -> list[dict]:
        products = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}/products.json?limit=250&page={page}"
                logger.info(f"[CrepDogCrew] Fetching page {page}: {url}")
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
                    logger.info(f"[CrepDogCrew] Page {page}: {len(page_products)} products")
                except Exception as e:
                    logger.error(f"[CrepDogCrew] Page {page} error: {e}")
                    break
        logger.info(f"[CrepDogCrew] Total scraped: {len(products)}")
        return products

    def normalize_product(self, raw: dict) -> dict | None:
        title = raw.get("title", "").strip()
        if not title:
            return None

        variants = raw.get("variants", [])
        prices = [float(v["price"]) for v in variants if v.get("price")]
        if not prices:
            return None

        images = raw.get("images", [])
        image_url = images[0]["src"] if images else ""
        vendor = raw.get("vendor", "")
        handle = raw.get("handle", "")
        tags = raw.get("tags", [])

        # Determine category from product_type and tags
        product_type = (raw.get("product_type") or "").lower()
        category = "SHOES"
        if any(k in product_type for k in ["apparel", "cloth", "tee", "hoodie", "jacket", "shirt", "pant"]):
            category = "CLOTHES"
        elif any(k in product_type for k in ["accessori", "bag", "cap", "hat", "watch"]):
            category = "ACCESSORIES"
        elif any(t.lower() in ["apparel", "tshirt", "hoodie", "jacket"] for t in tags):
            category = "CLOTHES"

        available_sizes = []
        for v in variants:
            if v.get("available"):
                size = v.get("option2") or v.get("option1") or v.get("title", "")
                if size:
                    available_sizes.append(size)

        return {
            "name": title,
            "brand": vendor or self._extract_brand(title),
            "category": category,
            "price": min(prices),
            "original_price": max(prices) if len(prices) > 1 else min(prices),
            "image_url": image_url,
            "product_url": f"{self.base_url}/products/{handle}",
            "store": self.store_key,
            "in_stock": any(v.get("available") for v in variants),
            "available_sizes": available_sizes,
            "tags": [t.lower() for t in tags[:10]],
            "scraped_at": self.now_iso(),
        }

    def _extract_brand(self, name: str) -> str:
        known = ["Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics", "Converse", "Vans", "Yeezy"]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        return name.split()[0] if name else "Unknown"
