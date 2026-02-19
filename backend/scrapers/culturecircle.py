import httpx
import re
import logging
from bs4 import BeautifulSoup
from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)

CATEGORY_PAGES = [
    "/category/sneakers",
    "/category/new arrivals",
    "/category/apparels",
]


class CultureCircleScraper(BaseScraper):
    brand_name = "Culture Circle"
    store_key = "CULTURE_CIRCLE"
    base_url = "https://www.culture-circle.com"

    async def scrape_products(self, max_pages: int = 3) -> list[dict]:
        products = []
        seen = set()
        pages = CATEGORY_PAGES[:max_pages]

        async with httpx.AsyncClient(headers=HEADERS, timeout=25, follow_redirects=True) as client:
            for page_path in pages:
                url = f"{self.base_url}{page_path}"
                logger.info(f"[CultureCircle] Fetching: {url}")
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    page_products = self._parse_page(resp.text)
                    for p in page_products:
                        key = p["name"]
                        if key not in seen:
                            seen.add(key)
                            products.append(p)
                    logger.info(f"[CultureCircle] {page_path}: {len(page_products)} products")
                except Exception as e:
                    logger.error(f"[CultureCircle] {page_path} error: {e}")
                    continue

        logger.info(f"[CultureCircle] Total scraped: {len(products)}")
        return products

    def _parse_page(self, html_content: str) -> list[dict]:
        products = []
        soup = BeautifulSoup(html_content, "lxml")

        # Culture Circle products are in <a> tags linking to /products/all/{slug}
        product_links = soup.find_all("a", href=re.compile(r"/products/all/"))

        for link in product_links:
            try:
                href = link.get("href", "")
                product_url = href if href.startswith("http") else f"{self.base_url}{href}"

                # Find the product image
                img_tag = link.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("srcset", "").split(" ")[0] or ""

                # Get all text content to extract name and price
                texts = [t.strip() for t in link.stripped_strings if t.strip()]

                # Filter out bookmark/badge text
                skip_words = {"Bookmark", "CULTURED BDAY SALE", "HOT PICK", "NEW", "INR"}
                meaningful_texts = [t for t in texts if t not in skip_words]

                if not meaningful_texts:
                    continue

                # Product name is usually the first meaningful text or the longest one
                name = ""
                prices = []
                for t in meaningful_texts:
                    # Check if it's a price (contains digits and comma)
                    clean = t.replace(",", "").replace(" ", "")
                    if clean.isdigit() and len(clean) >= 3:
                        prices.append(int(clean))
                    elif not name and len(t) > 3:
                        name = t

                if not name:
                    continue

                # First price is sale price, second is original
                sale_price = prices[0] if prices else 0
                original_price = prices[1] if len(prices) > 1 else sale_price

                if sale_price <= 0:
                    continue

                brand = self._extract_brand(name)
                category = self._guess_category(name)

                products.append({
                    "name": name,
                    "brand": brand,
                    "category": category,
                    "price": float(sale_price),
                    "original_price": float(original_price),
                    "image_url": image_url,
                    "product_url": product_url,
                    "store": self.store_key,
                    "in_stock": True,
                    "available_sizes": [],
                    "tags": ["sneakers", "streetwear"],
                    "scraped_at": self.now_iso(),
                })
            except Exception as e:
                logger.error(f"[CultureCircle] Product parse error: {e}")
                continue

        return products

    def _extract_brand(self, name: str) -> str:
        known = [
            "Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Yeezy", "Saucony", "Salomon", "On Running",
            "Crocs", "Hoka", "Birkenstock", "Dior", "Balenciaga", "Off-White",
            "Cloudmonster", "Cloudtilt", "Cloud", "Ami", "Coach", "Creed",
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        # Extract first word before common patterns
        if "air jordan" in name_lower or "jordan" in name_lower:
            return "Jordan"
        if "air force" in name_lower or "dunk" in name_lower:
            return "Nike"
        if "samba" in name_lower or "adizero" in name_lower or "handball" in name_lower:
            return "Adidas"
        return name.split()[0] if name else "Unknown"

    def _guess_category(self, name: str) -> str:
        name_lower = name.lower()
        if any(k in name_lower for k in ["dunk", "jordan", "yeezy", "shoe", "sneaker", "boot", "slide", "foam",
                                           "samba", "force", "cloud", "adizero", "balance", "spezial"]):
            return "SHOES"
        if any(k in name_lower for k in ["tee", "shirt", "hoodie", "jacket", "pant", "short", "dress", "polo"]):
            return "CLOTHES"
        if any(k in name_lower for k in ["bag", "cap", "hat", "watch", "chain", "ring", "perfume", "edp"]):
            return "ACCESSORIES"
        return "SHOES"
