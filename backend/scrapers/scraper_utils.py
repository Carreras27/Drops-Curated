"""
Scraper Protection Utilities
Comprehensive anti-blocking measures for all scrapers.
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
    """Delay for staggering scrapers (15-35 seconds)."""
    return await random_delay(15.0, 35.0)

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
        """Generate a fingerprint hash for a product."""
        data = f"{product_id}|{updated_at or ''}|{price or ''}"
        return hashlib.md5(data.encode()).hexdigest()
    
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
        
        if self._db:
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
        
        # Captcha detection
        captcha_indicators = [
            'captcha', 'recaptcha', 'hcaptcha', 'cloudflare',
            'please verify you are human', 'bot detection',
            'access denied', 'blocked', 'suspicious activity'
        ]
        for indicator in captcha_indicators:
            if indicator in content_lower:
                return BlockedError(f"Captcha/Block detected: {indicator}", is_captcha=True)
        
        # Empty product list when we expect products
        if '"products":[]' in content or '"products": []' in content:
            # This could be legitimate (no products) or a soft block
            # We'll flag it as potential block for retry logic
            pass
    
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
