"""
Foot Locker India Scraper
Uses Playwright for JavaScript-rendered content with anti-bot protection.
Site is powered by Nykaa Fashion platform.
"""
import re
import logging
from typing import List, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)

# Category pages to scrape
CATEGORY_PAGES = [
    "/men/c/7927",          # Men's shoes
    "/women/c/7928",        # Women's shoes
    "/jordan-picks/c/68782", # Jordan
    "/designers/nike/c/11784",  # Nike
    "/designers/adidas/c/76783", # Adidas (corrected from all-adidas)
]


class FootLockerIndiaScraper(BaseScraper):
    """
    Scraper for Foot Locker India.
    Uses Playwright to handle JavaScript rendering and anti-bot measures.
    """
    brand_name = "Foot Locker India"
    store_key = "FOOTLOCKER_INDIA"
    base_url = "https://www.footlocker.co.in"

    async def scrape_products(self, max_pages: int = 3) -> List[dict]:
        """Scrape products using Playwright browser automation."""
        products = []
        seen_ids = set()
        pages_to_scrape = CATEGORY_PAGES[:max_pages + 2]

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-IN",
            )
            page = await context.new_page()

            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico}", lambda route: route.abort())
            await page.route("**/analytics**", lambda route: route.abort())
            await page.route("**/tracking**", lambda route: route.abort())

            for page_path in pages_to_scrape:
                url = f"{self.base_url}{page_path}"
                logger.info(f"[{self.store_key}] Fetching: {url}")

                try:
                    await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(3000)

                    # Scroll to load more products
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await page.wait_for_timeout(1000)

                    html = await page.content()
                    page_products = self._parse_page(html)

                    for prod in page_products:
                        pid = prod.get("id") or prod.get("name", "")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            products.append(prod)

                    logger.info(f"[{self.store_key}] {page_path}: {len(page_products)} products")

                except Exception as e:
                    logger.error(f"[{self.store_key}] {page_path} error: {e}")
                    continue

            await browser.close()

        self.report_success(products_found=len(products), new_products=len(products))
        logger.info(f"[{self.store_key}] Total scraped: {len(products)}")
        return products

    def _parse_page(self, html_content: str) -> List[dict]:
        """Parse rendered HTML to extract product data."""
        products = []
        soup = BeautifulSoup(html_content, "lxml")

        # Find product cards - Nykaa uses various selectors
        # Look for product links with product data
        product_cards = soup.find_all("a", href=re.compile(r"/p/\d+"))

        for card in product_cards:
            try:
                href = card.get("href", "")
                product_url = href if href.startswith("http") else f"{self.base_url}{href}"

                # Extract product ID from URL
                pid_match = re.search(r"/p/(\d+)", href)
                pid = pid_match.group(1) if pid_match else ""

                # Find product name
                name_elem = card.find(["h3", "h4", "p", "span"], class_=re.compile(r"name|title|product", re.I))
                name = name_elem.get_text(strip=True) if name_elem else ""

                # Try alternate name extraction
                if not name:
                    texts = [t.strip() for t in card.stripped_strings]
                    for t in texts:
                        if len(t) > 10 and not t.startswith("₹") and not t.isdigit():
                            name = t
                            break

                if not name:
                    continue

                # Find image
                img_tag = card.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""
                    # Get higher resolution
                    image_url = re.sub(r"tr=w-\d+", "tr=w-500", image_url)

                # Find price
                price = 0
                original_price = 0
                price_texts = card.find_all(string=re.compile(r"₹\s*[\d,]+"))
                for pt in price_texts:
                    try:
                        p_val = float(re.sub(r"[₹,\s]", "", pt))
                        if p_val > 0:
                            if price == 0:
                                price = p_val
                            else:
                                original_price = p_val
                    except (ValueError, TypeError):
                        continue

                if price <= 0:
                    # Try finding price in nested elements
                    price_elem = card.find(class_=re.compile(r"price|cost|amount", re.I))
                    if price_elem:
                        try:
                            price = float(re.sub(r"[₹,\s]", "", price_elem.get_text()))
                        except (ValueError, TypeError):
                            continue

                if price <= 0:
                    continue

                if original_price == 0:
                    original_price = price

                # Determine brand and category
                brand = self._extract_brand(name)
                category = self._guess_category(name, product_url)

                products.append({
                    "id": f"prod_{self.store_key}_{pid}" if pid else f"prod_{self.store_key}_{hash(name)}",
                    "name": name,
                    "brand": brand,
                    "category": category,
                    "price": price,
                    "original_price": original_price,
                    "image_url": image_url,
                    "product_url": product_url,
                    "store": self.store_key,
                    "in_stock": True,
                    "available_sizes": [],
                    "tags": self._filter_shipping_tags(["footlocker", "india", brand.lower()]),
                    "scraped_at": self.now_iso(),
                })

            except Exception as e:
                logger.error(f"[{self.store_key}] Card parse error: {e}")
                continue

        return products

    def _extract_brand(self, name: str) -> str:
        """Extract brand from product name."""
        known = [
            "Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Yeezy", "Skechers", "Crocs", "Hoka", "Fila",
            "New Era", "Under Armour", "Champion", "Birkenstock"
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        # Check for Air Jordan
        if "air jordan" in name_lower or "jordan" in name_lower:
            return "Jordan"
        if "air force" in name_lower or "dunk" in name_lower or "air max" in name_lower:
            return "Nike"
        return name.split()[0] if name else "Foot Locker"

    def _guess_category(self, name: str, url: str = "") -> str:
        """Guess product category."""
        combined = f"{name} {url}".lower()

        if any(k in combined for k in ["shoe", "sneaker", "boot", "slide", "sandal", "runner",
                                        "jordan", "dunk", "force", "max", "yeezy", "/men/", "/women/"]):
            return "SHOES"
        if any(k in combined for k in ["tee", "shirt", "hoodie", "jacket", "pant", "short"]):
            return "CLOTHES"
        if any(k in combined for k in ["cap", "hat", "bag", "sock", "accessory"]):
            return "ACCESSORIES"
        return "SHOES"  # Default for Foot Locker
