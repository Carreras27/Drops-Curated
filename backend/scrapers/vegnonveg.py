import httpx
import re
import json
import html as html_lib
import logging
from bs4 import BeautifulSoup
from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)

COLLECTION_PAGES = [
    "/new-in",
    "/footwear",
    "/footwear?page=2",
    "/footwear?page=3",
    "/apparel",
]


class VegNonVegScraper(BaseScraper):
    brand_name = "Veg Non Veg"
    store_key = "VEG_NON_VEG"
    base_url = "https://www.vegnonveg.com"

    async def scrape_products(self, max_pages: int = 3) -> list[dict]:
        products = []
        seen_ids = set()
        pages_to_scrape = COLLECTION_PAGES[:max_pages + 2]

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            for page_path in pages_to_scrape:
                url = f"{self.base_url}{page_path}"
                logger.info(f"[VegNonVeg] Fetching: {url}")
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    page_products = self._parse_page(resp.text)
                    for p in page_products:
                        pid = p.get("external_id")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            products.append(p)
                    logger.info(f"[VegNonVeg] {page_path}: {len(page_products)} products")
                except Exception as e:
                    logger.error(f"[VegNonVeg] {page_path} error: {e}")
                    continue

        logger.info(f"[VegNonVeg] Total scraped: {len(products)}")
        return products

    def _parse_page(self, html_content: str) -> list[dict]:
        products = []
        soup = BeautifulSoup(html_content, "lxml")

        # Find all product cards with data-product attribute
        cards = soup.find_all(attrs={"data-product": True})
        for card in cards:
            try:
                data_str = card.get("data-product", "")
                data = json.loads(html_lib.unescape(data_str))

                pid = str(data.get("id", ""))
                name = data.get("name", "").strip()
                price_raw = data.get("price", 0)
                price = float(str(price_raw).replace(",", ""))

                if not name or price <= 0:
                    continue

                # Find image
                img_tag = card.find("img", class_="lazy")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("data-src") or img_tag.get("src") or ""
                    # Use higher res version
                    image_url = image_url.replace("51X60", "680X800")

                # Find product link
                link_tag = card.find_parent("a") or card.find("a")
                product_url = ""
                if link_tag:
                    href = link_tag.get("href", "")
                    product_url = href if href.startswith("http") else f"{self.base_url}{href}"

                # Determine category
                categories = data.get("category", [])
                category = "SHOES"
                cat_str = " ".join(categories).lower() if categories else ""
                if "apparel" in cat_str or "cloth" in cat_str:
                    category = "CLOTHES"
                elif "accessor" in cat_str:
                    category = "ACCESSORIES"

                brand = self._extract_brand(name)

                products.append({
                    "external_id": pid,
                    "name": name,
                    "brand": brand,
                    "category": category,
                    "price": price,
                    "original_price": price,
                    "image_url": image_url,
                    "product_url": product_url,
                    "store": self.store_key,
                    "in_stock": True,
                    "available_sizes": [],
                    "tags": [c.lower() for c in categories],
                    "scraped_at": self.now_iso(),
                })
            except Exception as e:
                logger.error(f"[VegNonVeg] Card parse error: {e}")
                continue

        return products

    def _extract_brand(self, name: str) -> str:
        known = [
            "Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Yeezy", "Saucony", "ASICS", "Salomon", "On Running",
            "Pharrell", "Crocs", "Hoka", "Birkenstock",
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        return name.split()[0] if name else "Unknown"
