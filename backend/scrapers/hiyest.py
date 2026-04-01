import httpx
import logging
from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)


class HiyestScraper(BaseScraper):
    brand_name = "Hiyest"
    store_key = "HIYEST"
    base_url = "https://hiyest.com"
    api_url = "https://hiyest.com/wp-json/wc/store/v1/products"

    async def scrape_products(self, max_pages: int = 5) -> list[dict]:
        products = []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                url = f"{self.api_url}?per_page=100&page={page}"
                logger.info(f"[Hiyest] Fetching page {page}")
                try:
                    resp = await client.get(url)
                    if resp.status_code == 404:
                        break
                    resp.raise_for_status()
                    data = resp.json()
                    if not data:
                        break
                    for raw in data:
                        p = self.normalize_product(raw)
                        if p:
                            products.append(p)
                except Exception as e:
                    logger.error(f"[Hiyest] Page {page} error: {e}")
                    break
        logger.info(f"[Hiyest] Total scraped: {len(products)}")
        return products

    def normalize_product(self, raw: dict) -> dict | None:
        name = raw.get("name", "").strip()
        if not name:
            return None

        prices = raw.get("prices", {})
        price_raw = prices.get("price", "0")
        regular_raw = prices.get("regular_price", price_raw)
        try:
            # WC Store API returns prices in minor units (paise)
            divisor = 10 ** int(prices.get("currency_minor_unit", 2))
            price = int(price_raw) / divisor
            original_price = int(regular_raw) / divisor
        except (ValueError, TypeError):
            return None

        if price <= 0:
            return None

        images = raw.get("images", [])
        image_url = images[0].get("src", "") if images else ""
        permalink = raw.get("permalink", "")

        return {
            "name": name,
            "brand": "Hiyest",
            "category": "CLOTHES",
            "price": price,
            "original_price": original_price,
            "image_url": image_url,
            "product_url": permalink,
            "store": self.store_key,
            "in_stock": raw.get("is_purchasable", True),
            "available_sizes": [],
            "tags": ["streetwear", "hiyest"],
            "scraped_at": self.now_iso(),
        }
