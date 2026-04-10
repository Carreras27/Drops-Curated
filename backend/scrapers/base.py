"""
Base Scraper with Anti-Blocking Protection
"""
import httpx
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

from .scraper_utils import (
    get_random_user_agent,
    random_delay,
    product_delay,
    retry_delay,
    proxy_manager,
    fingerprint_cache,
    health_tracker,
    build_headers,
    BlockedError,
    detect_blocked_response
)

logger = logging.getLogger(__name__)

# Default headers (will be randomized per request)
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Legacy HEADERS export for backwards compatibility with existing scrapers
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


class BaseScraper:
    """Base scraper class with built-in anti-blocking protection."""
    
    brand_name: str = ""
    store_key: str = ""
    base_url: str = ""
    max_retries: int = 3
    use_proxy: bool = True
    
    def __init__(self):
        self._retry_count = 0
        self._is_blocked = False
    
    async def scrape_products(self, max_pages: int = 3) -> List[dict]:
        """Override in subclass. Should return list of normalized products."""
        raise NotImplementedError
    
    def normalize_product(self, raw: dict) -> Optional[dict]:
        """Override in subclass. Should convert raw data to standard format."""
        raise NotImplementedError
    
    def now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    async def fetch_with_protection(
        self, 
        url: str, 
        method: str = 'GET',
        headers: Dict = None,
        json_response: bool = False,
        timeout: int = 30
    ) -> tuple[Any, str]:
        """
        Fetch URL with anti-blocking protection.
        Returns (response_data, raw_content)
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Build randomized headers
                request_headers = build_headers(
                    referer=self.base_url,
                    is_json=json_response
                )
                if headers:
                    request_headers.update(headers)
                
                # Get proxy if configured and enabled
                proxy = proxy_manager.get_proxy() if self.use_proxy else None
                
                # Create client with proxy
                client_kwargs = {
                    'headers': request_headers,
                    'timeout': timeout,
                    'follow_redirects': True
                }
                if proxy:
                    client_kwargs['proxies'] = {'http://': proxy, 'https://': proxy}
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    # Add random delay before request
                    await product_delay()
                    
                    response = await client.get(url)
                    content = response.text
                    
                    # Check if blocked
                    blocked_error = detect_blocked_response(response, content)
                    if blocked_error:
                        raise blocked_error
                    
                    # Success
                    response.raise_for_status()
                    self._retry_count = 0
                    self._is_blocked = False
                    
                    if json_response:
                        return response.json(), content
                    return response, content
                    
            except BlockedError as e:
                self._is_blocked = True
                last_error = str(e)
                logger.warning(f"[{self.store_key}] Blocked on attempt {attempt + 1}: {e}")
                
                # Report proxy failure
                if proxy:
                    proxy_manager.report_failure(proxy)
                
                # Exponential backoff retry
                if attempt < self.max_retries - 1:
                    delay = await retry_delay(attempt)
                    logger.info(f"[{self.store_key}] Retrying in {delay:.1f}s with new proxy...")
                    self._retry_count = attempt + 1
                else:
                    # All retries exhausted - notify admin
                    await self._notify_block_alert()
                    raise
                    
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                logger.error(f"[{self.store_key}] HTTP error on attempt {attempt + 1}: {e}")
                
                if e.response.status_code in [403, 429, 503]:
                    # Treat as potential block
                    if attempt < self.max_retries - 1:
                        delay = await retry_delay(attempt)
                        logger.info(f"[{self.store_key}] Retrying in {delay:.1f}s...")
                        self._retry_count = attempt + 1
                    else:
                        self._is_blocked = True
                        await self._notify_block_alert()
                        raise BlockedError(f"HTTP {e.response.status_code} after {self.max_retries} retries")
                else:
                    raise
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{self.store_key}] Error on attempt {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = await retry_delay(attempt)
                    logger.info(f"[{self.store_key}] Retrying in {delay:.1f}s...")
                    self._retry_count = attempt + 1
                else:
                    raise
        
        raise Exception(f"Failed after {self.max_retries} attempts: {last_error}")
    
    async def _notify_block_alert(self):
        """Send WhatsApp alert to admin about blocked scraper."""
        try:
            # Import here to avoid circular imports
            from whatsapp import send_admin_alert
            message = f"🚨 SCRAPER BLOCKED\n\nBrand: {self.brand_name}\nStore: {self.store_key}\nRetries: {self._retry_count}\n\nPlease check the scraper health dashboard."
            await send_admin_alert(message)
        except Exception as e:
            logger.error(f"[{self.store_key}] Failed to send block alert: {e}")
    
    def should_process_product(self, product_id: str, updated_at: str = None, price: float = None) -> bool:
        """Check if product should be processed based on fingerprint cache."""
        return fingerprint_cache.has_changed(product_id, updated_at, price)
    
    async def mark_product_processed(self, product_id: str, updated_at: str = None, price: float = None):
        """Update fingerprint cache after processing product."""
        await fingerprint_cache.update(product_id, updated_at, price)
    
    def report_success(self, products_found: int = 0, new_products: int = 0):
        """Report successful scrape to health tracker."""
        health_tracker.record_success(
            self.store_key.lower(),
            products_found=products_found,
            new_products=new_products
        )
    
    def report_failure(self, error: str):
        """Report failed scrape to health tracker."""
        health_tracker.record_failure(
            self.store_key.lower(),
            error=error,
            is_blocked=self._is_blocked,
            retry_count=self._retry_count
        )
    
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
            tag_lower = str(tag).lower()
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
