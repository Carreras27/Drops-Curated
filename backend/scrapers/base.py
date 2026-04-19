"""
Base Scraper with Anti-Blocking Protection
Includes human-like behavior patterns for bot detection evasion.
"""
import httpx
import logging
import asyncio
import time
import random
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
    detect_blocked_response,
    human,
    HumanBehavior,
    persona_manager,
    aether_brain,
    aether_human,
    AetherHuman,
    PersonaManager,
    AetherBrain,
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

    async def scrape_with_playwright(
        self, 
        url: str, 
        selectors: Dict[str, str] = None,
        wait_for_product: bool = True,
        scroll: bool = True
    ) -> tuple:
        """
        Scrape a page using Playwright with human-like behavior.
        Returns (html_content, extracted_data).
        
        Args:
            url: Page URL to scrape
            selectors: Dict of CSS selectors to extract {name: selector}
            wait_for_product: Wait for product image to be visible
            scroll: Simulate human scrolling
        """
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
        import random
        
        stealth = Stealth(
            navigator_webdriver=True,
            navigator_plugins=True,
            navigator_permissions=True,
            webgl_vendor=True,
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            
            context = await browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                extra_http_headers=human.get_human_headers()
            )
            
            # Apply stealth mode
            await stealth.apply_stealth_async(context)
            
            page = await context.new_page()
            
            # Block heavy resources
            await page.route("**/*.{woff,woff2,ttf,otf}", lambda r: r.abort())
            await page.route("**/analytics**", lambda r: r.abort())
            await page.route("**/gtm.js**", lambda r: r.abort())
            
            try:
                # Navigate with human-like timing
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                
                # Wait for product to be visible (mimics human looking at product)
                if wait_for_product:
                    await human.wait_for_product_visible(page)
                
                # Random mouse movements
                await human.random_mouse_movement(page)
                
                # Scroll like a human browsing
                if scroll:
                    await human.scroll_like_human(page, scroll_count=random.randint(2, 4))
                
                # Get page content
                html = await page.content()
                
                # Extract data if selectors provided
                extracted = {}
                if selectors:
                    for key, selector in selectors.items():
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                extracted[key] = await element.inner_text()
                        except Exception:
                            extracted[key] = None
                
                return html, extracted
                
            finally:
                await browser.close()



class AetherBaseScraper(BaseScraper):
    """
    AETHER SWARM v1.0 — Lethal self-learning multi-bot scraper base.

    Extends BaseScraper with:
    - Multi-persona rotation via PersonaManager
    - Self-learning via AetherBrain (per-brand persona scoring)
    - Extreme human mimicry via AetherHuman
    - Swarm retry: on failure, automatically rotates persona and retries

    Subclasses still implement scrape_products() and normalize_product()
    exactly as before. The swarm layer wraps around them transparently.
    """

    swarm_max_retries: int = 3  # How many persona rotations before giving up

    def __init__(self):
        super().__init__()
        self._current_persona: Optional[Dict] = None
        self._swarm_attempt: int = 0

    # ------------------------------------------------------------------
    # Public entry point — call this instead of scrape_products() directly
    # ------------------------------------------------------------------
    async def run_swarm_scrape(self, max_pages: int = 20) -> List[dict]:
        """
        Run the scrape through the Aether Swarm pipeline:
        1. Pick best persona (or rotate on retry)
        2. Apply persona headers/fingerprint
        3. Call the subclass scrape_products()
        4. Record result in AetherBrain
        5. On failure → rotate persona → retry up to swarm_max_retries
        """
        last_error = None

        for attempt in range(self.swarm_max_retries):
            self._swarm_attempt = attempt

            # Pick persona — prioritise brain's best pick, then rotate
            best_name = aether_brain.get_best_persona(self.store_key.lower())
            if attempt == 0 and best_name:
                # Use the learned best persona on first try
                persona = persona_manager.get_persona(self.store_key.lower())
                for p in PersonaManager.PERSONAS:
                    if p["name"] == best_name:
                        persona = p.copy()
                        break
            else:
                persona = persona_manager.get_persona(self.store_key.lower())

            self._current_persona = persona
            persona_name = persona["name"]

            logger.info(
                f"[AetherSwarm] [{self.store_key}] Attempt {attempt + 1}/{self.swarm_max_retries} "
                f"with persona '{persona_name}'"
            )

            start = time.time()
            try:
                products = await self.scrape_products(max_pages=max_pages)
                elapsed_ms = int((time.time() - start) * 1000)

                if products:
                    # Record success
                    await aether_brain.record_attempt(
                        self.store_key.lower(), persona_name,
                        success=True, products=len(products), response_ms=elapsed_ms,
                    )
                    persona_manager.record_win(self.store_key.lower(), persona_name)

                    logger.info(
                        f"[AetherSwarm] [{self.store_key}] SUCCESS — {len(products)} products "
                        f"via '{persona_name}' in {elapsed_ms}ms"
                    )
                    return products
                else:
                    raise Exception("No products returned")

            except Exception as e:
                elapsed_ms = int((time.time() - start) * 1000)
                last_error = e

                await aether_brain.record_attempt(
                    self.store_key.lower(), persona_name,
                    success=False, response_ms=elapsed_ms,
                )

                logger.warning(
                    f"[AetherSwarm] [{self.store_key}] Persona '{persona_name}' failed: {e}"
                )

                # Backoff before next persona
                if attempt < self.swarm_max_retries - 1:
                    backoff = random.uniform(5, 15) * (attempt + 1)
                    logger.info(f"[AetherSwarm] [{self.store_key}] Backing off {backoff:.1f}s before next persona")
                    await asyncio.sleep(backoff)

        # All personas exhausted — fall through to caller / scraper agent
        logger.error(
            f"[AetherSwarm] [{self.store_key}] All {self.swarm_max_retries} personas exhausted"
        )
        raise last_error or Exception("Swarm scrape failed after all persona rotations")

    # ------------------------------------------------------------------
    # Override fetch_with_protection to inject current persona headers
    # ------------------------------------------------------------------
    async def fetch_with_protection(
        self,
        url: str,
        method: str = "GET",
        headers: Dict = None,
        json_response: bool = False,
        timeout: int = 30,
    ) -> tuple:
        """Fetch with persona-aware headers injected automatically."""
        persona_headers = {}
        if self._current_persona:
            persona_headers = persona_manager.get_headers_for_persona(self._current_persona)

        merged = {**persona_headers, **(headers or {})}
        return await super().fetch_with_protection(
            url, method=method, headers=merged,
            json_response=json_response, timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Override Playwright scrape to use persona + extreme human mimicry
    # ------------------------------------------------------------------
    async def scrape_with_playwright(
        self,
        url: str,
        selectors: Dict[str, str] = None,
        wait_for_product: bool = True,
        scroll: bool = True,
    ) -> tuple:
        """
        Playwright scrape with persona fingerprint and AetherHuman session.
        """
        from playwright.async_api import async_playwright

        persona = self._current_persona or persona_manager.get_persona(self.store_key.lower())

        try:
            from playwright_stealth import Stealth
            stealth = Stealth(
                navigator_webdriver=True,
                navigator_plugins=True,
                navigator_permissions=True,
                webgl_vendor=True,
            )
        except ImportError:
            stealth = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await browser.new_context(
                user_agent=persona["user_agent"],
                viewport=persona["viewport"],
                locale=persona.get("locale", "en-IN"),
                timezone_id=persona.get("timezone", "Asia/Kolkata"),
                extra_http_headers=persona_manager.get_headers_for_persona(persona),
            )

            if stealth:
                await stealth.apply_stealth_async(context)

            page = await context.new_page()

            # Block heavy resources
            await page.route("**/*.{woff,woff2,ttf,otf}", lambda r: r.abort())
            await page.route("**/analytics**", lambda r: r.abort())
            await page.route("**/gtm.js**", lambda r: r.abort())

            try:
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")

                if wait_for_product:
                    await aether_human.wait_for_product_visible(page)

                # Full human session — jitter, hover, erratic scroll
                await aether_human.full_human_session(page)

                html = await page.content()

                extracted = {}
                if selectors:
                    for key, selector in selectors.items():
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                extracted[key] = await element.inner_text()
                        except Exception:
                            extracted[key] = None

                return html, extracted

            finally:
                await browser.close()
