import re
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .base import BaseScraper

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

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            for page_path in pages:
                url = f"{self.base_url}{page_path}"
                logger.info(f"[CultureCircle] Fetching: {url}")
                try:
                    await page.goto(url, timeout=30000, wait_until="networkidle")
                    await page.wait_for_timeout(2000)
                    html = await page.content()
                    page_products = self._parse_rendered_html(html)
                    for prod in page_products:
                        key = prod["name"]
                        if key not in seen:
                            seen.add(key)
                            products.append(prod)
                    logger.info(f"[CultureCircle] {page_path}: {len(page_products)} products")
                except Exception as e:
                    logger.error(f"[CultureCircle] {page_path} error: {e}")
                    continue

            await browser.close()

        logger.info(f"[CultureCircle] Total scraped: {len(products)}")
        return products

    def _parse_rendered_html(self, html_content: str) -> list[dict]:
        products = []
        soup = BeautifulSoup(html_content, "lxml")

        # Product cards are <a> tags linking to /products/all/{slug}
        product_links = soup.find_all("a", href=re.compile(r"/products/all/"))

        for link in product_links:
            try:
                href = link.get("href", "")
                product_url = href if href.startswith("http") else f"{self.base_url}{href}"

                # Find image
                img_tag = link.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("srcset", "").split(" ")[0] or ""

                # Extract texts
                texts = [t.strip() for t in link.stripped_strings if t.strip()]
                skip_words = {"Bookmark", "CULTURED BDAY SALE", "HOT PICK", "NEW", "INR", "Scroll Right"}

                name = ""
                prices = []
                for t in texts:
                    if t in skip_words:
                        continue
                    clean = t.replace(",", "").replace(" ", "")
                    if clean.isdigit() and len(clean) >= 3:
                        prices.append(int(clean))
                    elif not name and len(t) > 3:
                        name = t

                if not name or not prices:
                    continue

                sale_price = prices[0]
                original_price = prices[1] if len(prices) > 1 else sale_price

                products.append({
                    "name": name,
                    "brand": self._extract_brand(name),
                    "category": self._guess_category(name),
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
            "Converse", "Vans", "Yeezy", "Saucony", "Salomon",
            "Crocs", "Hoka", "Birkenstock", "Dior", "Balenciaga", "Off-White",
            "Ami", "Coach", "Creed", "Casio",
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        if "air jordan" in name_lower or "jordan" in name_lower:
            return "Jordan"
        if "air force" in name_lower or "dunk" in name_lower:
            return "Nike"
        if "samba" in name_lower or "adizero" in name_lower or "handball" in name_lower:
            return "Adidas"
        if "cloud" in name_lower:
            return "On Running"
        return name.split()[0] if name else "Unknown"

    def _guess_category(self, name: str) -> str:
        name_lower = name.lower()
        if any(k in name_lower for k in ["dunk", "jordan", "yeezy", "shoe", "sneaker", "boot", "slide",
                                           "samba", "force", "cloud", "adizero", "balance", "spezial"]):
            return "SHOES"
        if any(k in name_lower for k in ["tee", "shirt", "hoodie", "jacket", "pant", "short", "dress", "polo"]):
            return "CLOTHES"
        if any(k in name_lower for k in ["bag", "cap", "hat", "watch", "chain", "ring", "perfume", "edp"]):
            return "ACCESSORIES"
        return "SHOES"
