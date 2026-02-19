import httpx
import re
import json
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

        # Culture Circle is a Next.js app - product data is in RSC payloads or __NEXT_DATA__
        # Try finding __NEXT_DATA__ JSON
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html_content, re.S)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                products = self._extract_from_next_data(data)
                if products:
                    return products
            except Exception as e:
                logger.error(f"[CultureCircle] __NEXT_DATA__ parse error: {e}")

        # Try RSC payload (React Server Components)
        rsc_products = self._extract_from_rsc(html_content)
        if rsc_products:
            return rsc_products

        # Fallback: parse structured data / JSON-LD
        soup = BeautifulSoup(html_content, "lxml")
        ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in ld_scripts:
            try:
                ld = json.loads(script.string)
                if ld.get("@type") == "ItemList":
                    for item in ld.get("itemListElement", []):
                        p = self._normalize_ld_item(item)
                        if p:
                            products.append(p)
            except Exception:
                continue

        # Fallback: extract product info from HTML structure
        if not products:
            products = self._extract_from_html(soup)

        return products

    def _extract_from_rsc(self, html_content: str) -> list[dict]:
        """Extract product data from React Server Component payloads embedded in script tags"""
        products = []
        # RSC data often contains product objects as JSON
        # Look for patterns like product names, prices, and images in the script data
        price_pattern = re.findall(
            r'"name"\s*:\s*"([^"]+)"[^}]*?"price"\s*:\s*(\d+(?:\.\d+)?)',
            html_content
        )
        image_pattern = re.findall(
            r'"(?:image|imageUrl|src)"\s*:\s*"(https://cdn\.culture-circle\.com[^"]+)"',
            html_content
        )
        slug_pattern = re.findall(
            r'"(?:slug|handle|path)"\s*:\s*"([^"]+)"',
            html_content
        )

        for i, (name, price) in enumerate(price_pattern):
            if float(price) < 100:  # Skip non-price numbers
                continue
            image = image_pattern[i] if i < len(image_pattern) else ""
            slug = slug_pattern[i] if i < len(slug_pattern) else name.lower().replace(" ", "-")

            products.append({
                "name": name,
                "brand": self._extract_brand(name),
                "category": self._guess_category(name),
                "price": float(price),
                "original_price": float(price),
                "image_url": image,
                "product_url": f"{self.base_url}/product/{slug}",
                "store": self.store_key,
                "in_stock": True,
                "available_sizes": [],
                "tags": ["sneakers", "streetwear"],
                "scraped_at": self.now_iso(),
            })

        return products

    def _extract_from_next_data(self, data: dict) -> list[dict]:
        products = []
        # Traverse the nested structure to find product arrays
        self._find_products_recursive(data, products)
        return products

    def _find_products_recursive(self, obj, results: list, depth: int = 0):
        if depth > 10:
            return
        if isinstance(obj, dict):
            # Check if this looks like a product
            if "name" in obj and ("price" in obj or "sellingPrice" in obj or "mrp" in obj):
                p = self._normalize_next_product(obj)
                if p:
                    results.append(p)
            else:
                for v in obj.values():
                    self._find_products_recursive(v, results, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self._find_products_recursive(item, results, depth + 1)

    def _normalize_next_product(self, raw: dict) -> dict | None:
        name = raw.get("name") or raw.get("title", "")
        price = raw.get("price") or raw.get("sellingPrice") or raw.get("mrp", 0)
        if not name or not price:
            return None
        image = raw.get("image") or raw.get("imageUrl") or raw.get("thumbnail", "")
        if isinstance(image, list) and image:
            image = image[0]
        if isinstance(image, dict):
            image = image.get("src") or image.get("url", "")

        slug = raw.get("slug") or raw.get("handle") or name.lower().replace(" ", "-")

        return {
            "name": name,
            "brand": raw.get("brand", self._extract_brand(name)),
            "category": self._guess_category(name),
            "price": float(price),
            "original_price": float(raw.get("mrp", price)),
            "image_url": image,
            "product_url": f"{self.base_url}/product/{slug}",
            "store": self.store_key,
            "in_stock": raw.get("inStock", True),
            "available_sizes": raw.get("sizes", []),
            "tags": raw.get("tags", ["sneakers", "streetwear"]),
            "scraped_at": self.now_iso(),
        }

    def _normalize_ld_item(self, item: dict) -> dict | None:
        product = item.get("item", item)
        name = product.get("name", "")
        if not name:
            return None
        offers = product.get("offers", {})
        price = offers.get("price", 0) if isinstance(offers, dict) else 0
        image = product.get("image", "")
        url = product.get("url", "")
        return {
            "name": name,
            "brand": self._extract_brand(name),
            "category": self._guess_category(name),
            "price": float(price) if price else 0,
            "original_price": float(price) if price else 0,
            "image_url": image,
            "product_url": url if url.startswith("http") else f"{self.base_url}{url}",
            "store": self.store_key,
            "in_stock": True,
            "available_sizes": [],
            "tags": ["sneakers", "streetwear"],
            "scraped_at": self.now_iso(),
        }

    def _extract_from_html(self, soup) -> list[dict]:
        """Fallback: extract from HTML product cards"""
        products = []
        # Look for common product card patterns
        for link in soup.find_all("a", href=re.compile(r"/product/")):
            name_tag = link.find(["h2", "h3", "p", "span"])
            img_tag = link.find("img")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            if len(name) < 3:
                continue
            image = ""
            if img_tag:
                image = img_tag.get("src") or img_tag.get("data-src", "")
            href = link.get("href", "")
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            products.append({
                "name": name,
                "brand": self._extract_brand(name),
                "category": self._guess_category(name),
                "price": 0,
                "original_price": 0,
                "image_url": image,
                "product_url": url,
                "store": self.store_key,
                "in_stock": True,
                "available_sizes": [],
                "tags": ["sneakers", "streetwear"],
                "scraped_at": self.now_iso(),
            })
        return products

    def _extract_brand(self, name: str) -> str:
        known = [
            "Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics",
            "Converse", "Vans", "Yeezy", "Saucony", "Salomon", "On Running",
            "Crocs", "Hoka", "Birkenstock", "Dior", "Balenciaga", "Off-White",
        ]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        return name.split()[0] if name else "Unknown"

    def _guess_category(self, name: str) -> str:
        name_lower = name.lower()
        if any(k in name_lower for k in ["dunk", "jordan", "yeezy", "shoe", "sneaker", "boot", "slide", "foam"]):
            return "SHOES"
        if any(k in name_lower for k in ["tee", "shirt", "hoodie", "jacket", "pant", "short", "dress"]):
            return "CLOTHES"
        if any(k in name_lower for k in ["bag", "cap", "hat", "watch", "chain", "ring"]):
            return "ACCESSORIES"
        return "SHOES"
