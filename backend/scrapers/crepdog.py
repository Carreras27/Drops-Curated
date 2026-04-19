# AETHER SWARM v1.0 - Lethal self-learning multi-bot mode
import httpx
import logging
from .base import AetherBaseScraper, HEADERS
from .scraper_utils import persona_manager

logger = logging.getLogger(__name__)


class CrepDogCrewScraper(AetherBaseScraper):
    brand_name = "Crep Dog Crew"
    store_key = "CREPDOG_CREW"
    base_url = "https://crepdogcrew.com"

    async def scrape_products(self, max_pages: int = 20) -> list[dict]:
        """Scrape ALL products from Crepdog Crew via Shopify JSON API.
        Shopify limits to 250/page. With 3500+ products, we need ~14 pages.
        The JSON API is public and free — no reason to limit pages."""
        products = []
        catalog_complete = False

        # Get persona-aware headers
        persona = self._current_persona or persona_manager.get_persona(self.store_key.lower())
        headers = persona_manager.get_headers_for_persona(persona)
        headers['Accept'] = 'application/json'

        async with httpx.AsyncClient(headers=headers, timeout=25, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}/products.json?limit=250&page={page}"
                logger.info(f"[CrepDogCrew] Fetching page {page}/{max_pages}")
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    page_products = data.get("products", [])
                    if not page_products:
                        catalog_complete = True
                        logger.info(f"[CrepDogCrew] Catalog complete at page {page} (no more products)")
                        break
                    for raw in page_products:
                        p = self.normalize_product(raw)
                        if p:
                            products.append(p)
                    logger.info(f"[CrepDogCrew] Page {page}: {len(page_products)} products (running total: {len(products)})")
                except Exception as e:
                    logger.error(f"[CrepDogCrew] Page {page} error: {e}")
                    break

        if not catalog_complete and len(products) >= max_pages * 250:
            logger.warning(f"[CrepDogCrew] Hit page limit ({max_pages}) — catalog may be incomplete. Got {len(products)} products.")

        logger.info(f"[CrepDogCrew] Total scraped: {len(products)} | Catalog complete: {catalog_complete}")
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

        product_id = str(raw.get("id", ""))
        if not product_id:
            return None

        # Build size_prices map
        size_prices = {}
        available_prices = []
        available_sizes = []
        for v in variants:
            opt1 = v.get("option1", "")
            opt2 = v.get("option2", "")
            vtitle = v.get("title", "")
            
            size = ""
            if opt1 and opt1 != "Default Title":
                size = opt1
            elif opt2 and opt2 != "Default Title":
                size = opt2
            elif vtitle and vtitle != "Default Title":
                size = vtitle.split(" / ")[0] if " / " in vtitle else vtitle
            
            try:
                vprice = float(v.get("price", 0))
            except (ValueError, TypeError):
                vprice = 0
            
            if v.get("available") and size:
                available_sizes.append(size)
                if vprice > 0:
                    size_prices[size] = vprice
                    available_prices.append(vprice)

        # Filter out shipping-related tags and sizes
        filtered_tags = self._filter_shipping_tags([t.lower() for t in tags[:15]])
        filtered_sizes = self._filter_shipping_sizes(available_sizes)

        display_price = available_prices[0] if available_prices else min(prices)
        compare_prices = [float(v.get("compare_at_price", 0) or 0) for v in variants if v.get("compare_at_price")]

        return {
            "id": f"prod_{self.store_key}_{product_id}",
            "shopify_id": product_id,
            "name": title,
            "brand": vendor or self._extract_brand(title),
            "category": category,
            "price": display_price,
            "lowest_price": min(available_prices) if available_prices else min(prices),
            "highest_price": max(available_prices) if available_prices else max(prices),
            "original_price": max(compare_prices) if compare_prices else display_price,
            "image_url": image_url,
            "product_url": f"{self.base_url}/products/{handle}",
            "store": self.store_key,
            "in_stock": any(v.get("available") for v in variants),
            "available_sizes": filtered_sizes,
            "size_prices": size_prices,
            "tags": filtered_tags[:10],
            "scraped_at": self.now_iso(),
        }

    def _extract_brand(self, name: str) -> str:
        known = ["Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok", "Asics", "Converse", "Vans", "Yeezy"]
        name_lower = name.lower()
        for b in known:
            if b.lower() in name_lower:
                return b
        return name.split()[0] if name else "Unknown"
    
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
