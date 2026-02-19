import httpx
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


class BaseScraper:
    brand_name: str = ""
    store_key: str = ""
    base_url: str = ""

    async def scrape_products(self, max_pages: int = 3) -> list[dict]:
        raise NotImplementedError

    def normalize_product(self, raw: dict) -> dict:
        raise NotImplementedError

    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
