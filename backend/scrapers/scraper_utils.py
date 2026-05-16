"""
Scraper Protection Utilities
Comprehensive anti-blocking measures for all scrapers.
Includes human-like behavior patterns to avoid bot detection.
"""
import os
import random
import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============ USER AGENT ROTATION ============

USER_AGENTS = [
    # Desktop - Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Desktop - Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Desktop - Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Mobile - iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    # Mobile - iPhone Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    # Mobile - Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    # Mobile - Android Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
]

def get_random_user_agent() -> str:
    """Get a random user agent from the pool."""
    return random.choice(USER_AGENTS)


# ============ HUMAN-LIKE BEHAVIOR PATTERNS ============

class HumanBehavior:
    """
    Simulates human-like browsing patterns to avoid bot detection.
    Includes random delays, mouse movements, and element waiting.
    """
    
    @staticmethod
    async def think_delay(min_sec: float = 1.5, max_sec: float = 3.0) -> float:
        """Simulate human 'thinking' time when viewing a product."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
        return delay
    
    @staticmethod
    async def reading_delay(text_length: int = 100) -> float:
        """Simulate time spent reading text (avg 200 words/min)."""
        # Approx 5 chars per word, 200 words/min = 1000 chars/min
        min_read_time = max(0.5, text_length / 2000)  # Min 0.5s
        max_read_time = min(5.0, text_length / 500)   # Max 5s
        delay = random.uniform(min_read_time, max_read_time)
        await asyncio.sleep(delay)
        return delay
    
    @staticmethod
    async def scroll_like_human(page, scroll_count: int = 3):
        """Scroll down page in human-like increments."""
        for i in range(scroll_count):
            # Random scroll distance (200-600 pixels)
            scroll_distance = random.randint(200, 600)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            # Pause between scrolls like a human would
            await asyncio.sleep(random.uniform(0.5, 1.5))
    
    @staticmethod
    async def wait_for_product_visible(page, timeout: int = 10000):
        """
        Wait for product content to be visible before scraping.
        Mimics a human looking at the product before checking price.
        """
        # Common product image selectors
        image_selectors = [
            "img[alt*='sneaker' i]",
            "img[alt*='shoe' i]",
            "img[alt*='product' i]",
            ".product-image img",
            "[data-testid='product-image']",
            ".product-gallery img",
            ".pdp-image img",
        ]
        
        for selector in image_selectors:
            try:
                await page.wait_for_selector(selector, state="visible", timeout=timeout // len(image_selectors))
                # Human-like pause after seeing the product
                await HumanBehavior.think_delay(1.5, 3.0)
                return True
            except Exception:
                continue
        
        # Fallback: just wait a bit
        await asyncio.sleep(random.uniform(2.0, 4.0))
        return False
    
    @staticmethod
    async def random_mouse_movement(page):
        """Simulate random mouse movements on the page."""
        try:
            viewport = page.viewport_size
            if viewport:
                # Move to random positions
                for _ in range(random.randint(2, 4)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass
    
    @staticmethod
    def get_human_headers() -> dict:
        """Get headers that mimic a real browser."""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }


# Global instance for easy access
human = HumanBehavior()


# ============ RANDOM DELAYS ============

async def random_delay(min_sec: float = 1.5, max_sec: float = 4.0) -> float:
    """Apply random delay between requests. Returns actual delay used."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)
    return delay

async def brand_delay() -> float:
    """Delay between brand scrapes (8-25 seconds)."""
    return await random_delay(8.0, 25.0)

async def product_delay() -> float:
    """Delay between product/page requests (1.5-4 seconds)."""
    return await random_delay(1.5, 4.0)

async def stagger_delay() -> float:
    """Delay between brands — wider gaps to appear more natural (30-90 seconds)."""
    return await random_delay(30.0, 90.0)

async def retry_delay(attempt: int) -> float:
    """Exponential backoff delay (30-60 seconds base, doubles each attempt)."""
    base_delay = random.uniform(30.0, 60.0)
    actual_delay = base_delay * (2 ** attempt)
    await asyncio.sleep(actual_delay)
    return actual_delay


# ============ PROXY ROTATION ============

class ProxyManager:
    """Manage residential proxy rotation."""
    
    def __init__(self):
        # Load proxy credentials from environment
        self.brightdata_host = os.getenv('BRIGHTDATA_HOST', '')
        self.brightdata_port = os.getenv('BRIGHTDATA_PORT', '22225')
        self.brightdata_user = os.getenv('BRIGHTDATA_USER', '')
        self.brightdata_pass = os.getenv('BRIGHTDATA_PASS', '')
        
        self.smartproxy_host = os.getenv('SMARTPROXY_HOST', '')
        self.smartproxy_port = os.getenv('SMARTPROXY_PORT', '10001')
        self.smartproxy_user = os.getenv('SMARTPROXY_USER', '')
        self.smartproxy_pass = os.getenv('SMARTPROXY_PASS', '')
        
        self._current_proxy = None
        self._proxy_failures = {}
        
    def get_proxy(self) -> Optional[str]:
        """Get a rotated proxy URL. Returns None if no proxy configured."""
        # Try Brightdata first
        if self.brightdata_host and self.brightdata_user:
            # Add session ID for rotation
            session_id = random.randint(100000, 999999)
            proxy_url = f"http://{self.brightdata_user}-session-{session_id}:{self.brightdata_pass}@{self.brightdata_host}:{self.brightdata_port}"
            self._current_proxy = ('brightdata', proxy_url)
            return proxy_url
        
        # Try Smartproxy
        if self.smartproxy_host and self.smartproxy_user:
            session_id = random.randint(100000, 999999)
            proxy_url = f"http://{self.smartproxy_user}-session-{session_id}:{self.smartproxy_pass}@{self.smartproxy_host}:{self.smartproxy_port}"
            self._current_proxy = ('smartproxy', proxy_url)
            return proxy_url
        
        # No proxy configured
        return None
    
    def get_fresh_proxy(self) -> Optional[str]:
        """Force rotation to a new proxy."""
        return self.get_proxy()
    
    def report_failure(self, proxy_url: str):
        """Report a proxy failure for monitoring."""
        if proxy_url:
            self._proxy_failures[proxy_url] = self._proxy_failures.get(proxy_url, 0) + 1
            logger.warning(f"Proxy failure reported. Total failures: {sum(self._proxy_failures.values())}")
    
    @property
    def is_configured(self) -> bool:
        """Check if any proxy is configured."""
        return bool(self.brightdata_host or self.smartproxy_host)


# Global proxy manager instance
proxy_manager = ProxyManager()


# ============ FINGERPRINT CACHING ============

class FingerprintCache:
    """Cache product fingerprints to avoid reprocessing unchanged products."""
    
    def __init__(self, db=None):
        self._cache: Dict[str, str] = {}
        self._db = db
        self._loaded = False
    
    async def load_from_db(self, db):
        """Load fingerprints from database."""
        self._db = db
        try:
            fingerprints = await db.product_fingerprints.find({}, {'_id': 0}).to_list(100000)
            for fp in fingerprints:
                self._cache[fp['product_id']] = fp['fingerprint']
            self._loaded = True
            logger.info(f"[FingerprintCache] Loaded {len(self._cache)} fingerprints from DB")
        except Exception as e:
            logger.error(f"[FingerprintCache] Failed to load: {e}")
    
    def generate_fingerprint(self, product_id: str, updated_at: str = None, price: float = None) -> str:
        """Generate a fingerprint hash for a product.
        SHA-256 is overkill for a dedup cache key (no security context), but
        it silences security scanners and costs nothing measurable here."""
        data = f"{product_id}|{updated_at or ''}|{price or ''}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def has_changed(self, product_id: str, updated_at: str = None, price: float = None) -> bool:
        """Check if product has changed since last scrape."""
        new_fingerprint = self.generate_fingerprint(product_id, updated_at, price)
        old_fingerprint = self._cache.get(product_id)
        
        if old_fingerprint == new_fingerprint:
            return False  # No change
        
        return True  # Changed or new
    
    async def update(self, product_id: str, updated_at: str = None, price: float = None):
        """Update fingerprint for a product."""
        fingerprint = self.generate_fingerprint(product_id, updated_at, price)
        self._cache[product_id] = fingerprint
        
        if self._db is not None:
            try:
                await self._db.product_fingerprints.update_one(
                    {'product_id': product_id},
                    {'$set': {'product_id': product_id, 'fingerprint': fingerprint, 'updated_at': datetime.now(timezone.utc).isoformat()}},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"[FingerprintCache] Failed to save fingerprint: {e}")
    
    async def bulk_update(self, products: List[Dict]):
        """Bulk update fingerprints for multiple products."""
        if self._db is None or not products:
            return
        
        from pymongo import UpdateOne
        operations = []
        for p in products:
            product_id = p.get('id', p.get('product_id', ''))
            updated_at = p.get('updated_at', p.get('scraped_at', ''))
            price = p.get('price', 0)
            
            fingerprint = self.generate_fingerprint(product_id, updated_at, price)
            self._cache[product_id] = fingerprint
            
            operations.append(
                UpdateOne(
                    {'product_id': product_id},
                    {'$set': {'product_id': product_id, 'fingerprint': fingerprint, 'updated_at': datetime.now(timezone.utc).isoformat()}},
                    upsert=True
                )
            )
        
        try:
            if operations:
                await self._db.product_fingerprints.bulk_write(operations, ordered=False)
        except Exception as e:
            logger.error(f"[FingerprintCache] Bulk update failed: {e}")


# Global fingerprint cache
fingerprint_cache = FingerprintCache()


# ============ BLOCKED ERROR DETECTION ============

class BlockedError(Exception):
    """Exception raised when scraper detects it's being blocked."""
    
    def __init__(self, message: str, status_code: int = None, is_captcha: bool = False, is_rate_limit: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.is_captcha = is_captcha
        self.is_rate_limit = is_rate_limit


def detect_blocked_response(response, content: str = None) -> Optional[BlockedError]:
    """
    Detect if a response indicates we're being blocked.
    Returns BlockedError if blocked, None otherwise.
    """
    status = response.status_code if hasattr(response, 'status_code') else None
    
    # HTTP 403 Forbidden
    if status == 403:
        return BlockedError("Access forbidden (403)", status_code=403)
    
    # HTTP 429 Too Many Requests
    if status == 429:
        return BlockedError("Rate limited (429)", status_code=429, is_rate_limit=True)
    
    # HTTP 503 Service Unavailable (often used for blocking)
    if status == 503:
        return BlockedError("Service unavailable (503)", status_code=503)
    
    # Check content for captcha/blocking indicators
    if content:
        content_lower = content.lower()
        
        # If the response is valid JSON with products, it's definitely not blocked
        if '"products":[' in content or '"products": [' in content:
            return None
        
        # Captcha detection — only check non-JSON responses
        captcha_indicators = [
            'captcha', 'recaptcha', 'hcaptcha',
            'please verify you are human', 'bot detection',
            'access denied', 'suspicious activity',
            'challenge-platform', 'cf-browser-verification',
        ]
        for indicator in captcha_indicators:
            if indicator in content_lower:
                return BlockedError(f"Captcha/Block detected: {indicator}", is_captcha=True)
        
        # Cloudflare challenge page (not just the word "cloudflare" in any context)
        if 'cloudflare' in content_lower and ('challenge' in content_lower or 'ray id' in content_lower):
            return BlockedError("Cloudflare challenge detected", is_captcha=True)
    
    return None


# ============ SCRAPER HEALTH TRACKING ============

@dataclass
class ScraperHealth:
    """Health status for a single scraper."""
    brand_key: str
    brand_name: str
    last_success: Optional[str] = None
    last_attempt: Optional[str] = None
    last_error: Optional[str] = None
    products_found: int = 0
    new_products: int = 0
    retry_count: int = 0
    is_blocked: bool = False
    consecutive_failures: int = 0
    total_runs: int = 0
    total_successes: int = 0


class HealthTracker:
    """Track health status for all scrapers."""
    
    def __init__(self):
        self._health: Dict[str, ScraperHealth] = {}
        self._db = None
    
    def init(self, db, brands: List[Dict]):
        """Initialize health tracking for all brands."""
        self._db = db
        for brand in brands:
            key = brand.get('key', brand.get('store_key', '').lower())
            name = brand.get('name', brand.get('brand_name', key))
            self._health[key] = ScraperHealth(brand_key=key, brand_name=name)
    
    def record_success(self, brand_key: str, products_found: int = 0, new_products: int = 0):
        """Record a successful scrape."""
        if brand_key not in self._health:
            self._health[brand_key] = ScraperHealth(brand_key=brand_key, brand_name=brand_key)
        
        health = self._health[brand_key]
        health.last_success = datetime.now(timezone.utc).isoformat()
        health.last_attempt = health.last_success
        health.products_found = products_found
        health.new_products = new_products
        health.is_blocked = False
        health.consecutive_failures = 0
        health.retry_count = 0
        health.total_runs += 1
        health.total_successes += 1
        health.last_error = None
    
    def record_failure(self, brand_key: str, error: str, is_blocked: bool = False, retry_count: int = 0):
        """Record a failed scrape."""
        if brand_key not in self._health:
            self._health[brand_key] = ScraperHealth(brand_key=brand_key, brand_name=brand_key)
        
        health = self._health[brand_key]
        health.last_attempt = datetime.now(timezone.utc).isoformat()
        health.last_error = error
        health.is_blocked = is_blocked
        health.retry_count = retry_count
        health.consecutive_failures += 1
        health.total_runs += 1
    
    def get_health(self, brand_key: str) -> Optional[ScraperHealth]:
        """Get health status for a brand."""
        return self._health.get(brand_key)
    
    def get_all_health(self) -> Dict[str, ScraperHealth]:
        """Get health status for all brands."""
        return self._health
    
    def get_blocked_brands(self) -> List[str]:
        """Get list of currently blocked brands."""
        return [k for k, v in self._health.items() if v.is_blocked]
    
    def get_dashboard_data(self) -> List[Dict]:
        """Get health data formatted for dashboard."""
        return [
            {
                'brand_key': h.brand_key,
                'brand_name': h.brand_name,
                'last_success': h.last_success,
                'last_attempt': h.last_attempt,
                'products_found': h.products_found,
                'new_products': h.new_products,
                'retry_count': h.retry_count,
                'is_blocked': h.is_blocked,
                'consecutive_failures': h.consecutive_failures,
                'success_rate': round(h.total_successes / h.total_runs * 100, 1) if h.total_runs > 0 else 0,
                'last_error': h.last_error
            }
            for h in self._health.values()
        ]


# Global health tracker
health_tracker = HealthTracker()


# ============ REQUEST HEADERS BUILDER ============

def build_headers(referer: str = None, is_json: bool = False) -> Dict[str, str]:
    """Build randomized request headers."""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': random.choice([
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9',
            'en-IN,en;q=0.9,hi;q=0.8',
            'en;q=0.9'
        ]),
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    
    if is_json:
        headers['Accept'] = 'application/json, text/plain, */*'
    else:
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
    
    if referer:
        headers['Referer'] = referer
    
    # Add some randomization to appear more human
    if random.random() > 0.5:
        headers['DNT'] = '1'
    
    if random.random() > 0.7:
        headers['Upgrade-Insecure-Requests'] = '1'
    
    return headers


# ============ AETHER SWARM v1.0 - Multi-Persona System ============

class PersonaManager:
    """
    Multi-persona rotation system that deploys different browser identities
    per scrape run. Each persona is a complete browser fingerprint — user agent,
    viewport, locale, timezone, platform — designed to confuse bot-fingerprinting.
    """

    PERSONAS = [
        {
            "name": "mumbai_chrome_desktop",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "Win32",
            "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        },
        {
            "name": "delhi_firefox_desktop",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "viewport": {"width": 1536, "height": 864},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "Win32",
            "sec_ch_ua": None,
        },
        {
            "name": "bangalore_mac_safari",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "viewport": {"width": 1440, "height": 900},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "MacIntel",
            "sec_ch_ua": None,
        },
        {
            "name": "pune_iphone_safari",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            "viewport": {"width": 390, "height": 844},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "iPhone",
            "sec_ch_ua": None,
        },
        {
            "name": "hyderabad_android_chrome",
            "user_agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
            "viewport": {"width": 412, "height": 915},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "Linux armv81",
            "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        },
        {
            "name": "kolkata_edge_desktop",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "Win32",
            "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        },
        {
            "name": "chennai_mac_chrome",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 1680, "height": 1050},
            "locale": "en-IN",
            "timezone": "Asia/Kolkata",
            "platform": "MacIntel",
            "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        },
    ]

    def __init__(self):
        self._used_personas: List[str] = []
        self._brand_wins: Dict[str, str] = {}  # brand_key -> persona_name that worked

    def get_persona(self, brand_key: str = None) -> Dict:
        """
        Get a persona for scraping. Prioritises the last winning persona
        for the given brand, then rotates through unused ones.
        """
        # If we know a winner for this brand, try it first
        if brand_key and brand_key in self._brand_wins:
            winner_name = self._brand_wins[brand_key]
            for p in self.PERSONAS:
                if p["name"] == winner_name:
                    return p.copy()

        # Pick a random persona not recently used
        unused = [p for p in self.PERSONAS if p["name"] not in self._used_personas]
        if not unused:
            self._used_personas.clear()
            unused = self.PERSONAS

        persona = random.choice(unused)
        self._used_personas.append(persona["name"])

        # Keep rotation window small
        if len(self._used_personas) > 4:
            self._used_personas.pop(0)

        return persona.copy()

    def record_win(self, brand_key: str, persona_name: str):
        """Record which persona succeeded for a brand."""
        self._brand_wins[brand_key] = persona_name

    def get_headers_for_persona(self, persona: Dict) -> Dict[str, str]:
        """Build HTTP headers matching a persona's browser fingerprint."""
        headers = {
            "User-Agent": persona["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        if persona.get("sec_ch_ua"):
            headers["sec-ch-ua"] = persona["sec_ch_ua"]
            headers["sec-ch-ua-mobile"] = "?1" if "Mobile" in persona["user_agent"] else "?0"
            headers["sec-ch-ua-platform"] = f'"{persona.get("platform", "Windows")}"'
        return headers


# Global persona manager
persona_manager = PersonaManager()


class AetherBrain:
    """
    Self-learning component that tracks per-brand scraping patterns:
    - Which personas succeed/fail
    - Optimal request timing per brand
    - Selector health per store
    Persists knowledge to MongoDB collection `aether_learning`.
    """

    def __init__(self):
        self._db = None
        self._memory: Dict[str, Dict] = {}  # in-memory cache

    async def init(self, db):
        """Load learned data from MongoDB."""
        self._db = db
        try:
            docs = await db.aether_learning.find({}, {"_id": 0}).to_list(500)
            for doc in docs:
                self._memory[doc["brand_key"]] = doc
            logger.info(f"[AetherBrain] Loaded learning data for {len(self._memory)} brands")
        except Exception as e:
            logger.warning(f"[AetherBrain] Could not load learning data: {e}")

    async def record_attempt(self, brand_key: str, persona_name: str, success: bool, products: int = 0, response_ms: int = 0):
        """Record a scrape attempt for future learning."""
        if brand_key not in self._memory:
            self._memory[brand_key] = {
                "brand_key": brand_key,
                "persona_scores": {},
                "total_attempts": 0,
                "total_successes": 0,
                "avg_response_ms": 0,
                "best_persona": None,
                "last_updated": None,
            }

        mem = self._memory[brand_key]
        mem["total_attempts"] = mem.get("total_attempts", 0) + 1

        scores = mem.get("persona_scores", {})
        if persona_name not in scores:
            scores[persona_name] = {"wins": 0, "losses": 0, "score": 50}

        ps = scores[persona_name]
        if success:
            ps["wins"] += 1
            ps["score"] = min(100, ps["score"] + 5)
            mem["total_successes"] = mem.get("total_successes", 0) + 1
        else:
            ps["losses"] += 1
            ps["score"] = max(0, ps["score"] - 10)

        mem["persona_scores"] = scores

        # Track best persona
        best = max(scores.items(), key=lambda x: x[1]["score"])
        mem["best_persona"] = best[0]

        # Update avg response time
        if response_ms > 0:
            prev_avg = mem.get("avg_response_ms", 0)
            total = mem.get("total_attempts", 1)
            mem["avg_response_ms"] = int(((prev_avg * (total - 1)) + response_ms) / total)

        mem["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Persist to DB
        if self._db is not None:
            try:
                await self._db.aether_learning.update_one(
                    {"brand_key": brand_key},
                    {"$set": mem},
                    upsert=True,
                )
            except Exception as e:
                logger.warning(f"[AetherBrain] DB persist failed for {brand_key}: {e}")

    def get_best_persona(self, brand_key: str) -> Optional[str]:
        """Return the persona name with the highest score for a brand."""
        mem = self._memory.get(brand_key)
        if not mem:
            return None
        return mem.get("best_persona")

    def get_brand_stats(self, brand_key: str) -> Dict:
        """Get learning stats for a brand."""
        return self._memory.get(brand_key, {})

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get learning stats for all brands."""
        return self._memory.copy()


# Global brain
aether_brain = AetherBrain()


class AetherHuman(HumanBehavior):
    """
    Extended human mimicry with extreme anti-detection behaviours:
    - Irregular scroll patterns
    - Fake idle periods (simulating tab switches)
    - Mouse jitter and hover simulation
    - Reading-speed-aware waits
    """

    @staticmethod
    async def erratic_scroll(page, min_scrolls: int = 2, max_scrolls: int = 6):
        """Scroll in an unpredictable human pattern — sometimes up, sometimes down."""
        scrolls = random.randint(min_scrolls, max_scrolls)
        for _ in range(scrolls):
            direction = random.choice([1, 1, 1, -1])  # 75% down, 25% up
            distance = random.randint(150, 700) * direction
            await page.evaluate(f"window.scrollBy(0, {distance})")
            await asyncio.sleep(random.uniform(0.3, 1.8))

    @staticmethod
    async def fake_idle(min_sec: float = 2.0, max_sec: float = 6.0):
        """Simulate user switching tabs / being idle."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    @staticmethod
    async def mouse_jitter(page, moves: int = 5):
        """Small, nervous mouse movements like a real user scanning the page."""
        try:
            vp = page.viewport_size
            if not vp:
                return
            cx, cy = vp["width"] // 2, vp["height"] // 2
            for _ in range(moves):
                dx = random.randint(-60, 60)
                dy = random.randint(-40, 40)
                await page.mouse.move(cx + dx, cy + dy)
                await asyncio.sleep(random.uniform(0.05, 0.2))
        except Exception:
            pass

    @staticmethod
    async def hover_random_elements(page, selector: str = "a, button, img", max_hovers: int = 3):
        """Hover over random interactive elements like a browsing human."""
        try:
            elements = await page.query_selector_all(selector)
            if not elements:
                return
            targets = random.sample(elements, min(max_hovers, len(elements)))
            for el in targets:
                try:
                    await el.hover(timeout=2000)
                    await asyncio.sleep(random.uniform(0.3, 1.0))
                except Exception:
                    continue
        except Exception:
            pass

    @staticmethod
    async def full_human_session(page):
        """Run a complete human-like browsing session on the current page."""
        await AetherHuman.fake_idle(1.0, 3.0)
        await AetherHuman.mouse_jitter(page, moves=random.randint(3, 6))
        await AetherHuman.erratic_scroll(page, 2, 5)
        await AetherHuman.hover_random_elements(page)
        await AetherHuman.fake_idle(0.5, 2.0)


# Global aether human
aether_human = AetherHuman()
