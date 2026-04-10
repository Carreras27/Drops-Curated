"""
LLM-Powered Self-Healing Scraper System

Flow:
    Scraper fails
         ↓
    Error captured with full context
         ↓
    LLM Agent (Gemini Flash) analyses error
         ↓
    Agent picks fix strategy from available options
         ↓
    Retry with new strategy
         ↓
    Success? → Continue & learn from success
    Fail?   → Try next strategy
         ↓
    All strategies exhausted?
         → Alert admin via email every 5 minutes
"""

import asyncio
import logging
import smtplib
import os
import json
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FixStrategy(Enum):
    """Available fix strategies for scraper issues."""
    INCREASE_TIMEOUT = "increase_timeout"
    ROTATE_USER_AGENT = "rotate_user_agent"
    USE_PROXY = "use_proxy"
    ADD_DELAY = "add_delay"
    TRY_JSON_API = "try_json_api"
    USE_PLAYWRIGHT = "use_playwright"
    REDUCE_CONCURRENCY = "reduce_concurrency"
    CLEAR_COOKIES = "clear_cookies"
    TRY_MOBILE_UA = "try_mobile_ua"
    RETRY_LATER = "retry_later"


@dataclass
class ScraperError:
    """Captured scraper error with full context."""
    brand_key: str
    brand_name: str
    error_type: str
    error_message: str
    status_code: Optional[int] = None
    url: str = ""
    response_snippet: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    strategies_tried: List[str] = field(default_factory=list)
    
    def to_context_string(self) -> str:
        """Generate context string for LLM analysis."""
        return f"""
SCRAPER ERROR REPORT
====================
Brand: {self.brand_name} ({self.brand_key})
Timestamp: {self.timestamp}
URL: {self.url}
Error Type: {self.error_type}
Error Message: {self.error_message}
HTTP Status Code: {self.status_code or 'N/A'}
Retry Count: {self.retry_count}
Strategies Already Tried: {', '.join(self.strategies_tried) or 'None'}

Response Snippet (first 500 chars):
{self.response_snippet[:500] if self.response_snippet else 'N/A'}
"""


@dataclass
class HealingResult:
    """Result of a healing attempt."""
    success: bool
    strategy_used: FixStrategy
    message: str
    products_scraped: int = 0
    should_alert: bool = False


class ScraperHealer:
    """
    LLM-powered self-healing system for scrapers.
    Uses Gemini Flash to analyze errors and pick fix strategies.
    """
    
    def __init__(self, db=None):
        self._db = db
        self._last_alert_time: Dict[str, datetime] = {}
        self._error_history: Dict[str, List[ScraperError]] = {}
        self._success_history: Dict[str, Dict[str, int]] = {}  # Track which strategies work
        
        # Email config
        self._smtp_email = os.getenv("SMTP_EMAIL", "")
        self._smtp_password = os.getenv("SMTP_PASSWORD", "")
        self._admin_emails = os.getenv("ADMIN_ALERT_EMAILS", "dropscurated@gmail.com").split(",")
        
        # Alert interval (5 minutes)
        self._alert_interval = timedelta(minutes=5)
    
    async def init_llm(self):
        """Initialize LLM client."""
        try:
            from emergentintegrations.llm.chat import LlmChat
            self._llm = LlmChat(
                api_key=os.getenv("EMERGENT_LLM_KEY"),
                session_id="scraper_healer",
                system_message="You are a web scraping expert. Analyze errors and suggest fix strategies."
            )
            self._llm_model = "gemini/gemini-2.0-flash"
            logger.info("[Healer] LLM initialized successfully")
            return True
        except Exception as e:
            logger.error(f"[Healer] Failed to initialize LLM: {e}")
            self._llm = None
            return False
    
    async def analyze_and_fix(
        self, 
        scraper_factory: Callable, 
        error: ScraperError,
        max_strategies: int = 5
    ) -> HealingResult:
        """
        Main healing flow:
        1. Analyze error with LLM
        2. Pick strategy
        3. Apply strategy and retry
        4. Repeat or alert
        """
        strategies_to_try = await self._get_fix_strategies(error)
        
        for i, strategy in enumerate(strategies_to_try[:max_strategies]):
            if strategy.value in error.strategies_tried:
                continue
            
            logger.info(f"[Healer] Trying strategy {i+1}/{len(strategies_to_try)}: {strategy.value}")
            error.strategies_tried.append(strategy.value)
            
            try:
                # Apply strategy and retry
                result = await self._apply_strategy_and_retry(scraper_factory, strategy, error)
                
                if result.success:
                    # Record successful strategy for future reference
                    self._record_success(error.brand_key, strategy)
                    logger.info(f"[Healer] SUCCESS with strategy: {strategy.value}")
                    return result
                else:
                    logger.warning(f"[Healer] Strategy {strategy.value} failed: {result.message}")
                    
            except Exception as e:
                logger.error(f"[Healer] Strategy {strategy.value} threw exception: {e}")
                error.retry_count += 1
        
        # All strategies exhausted
        logger.error(f"[Healer] All strategies exhausted for {error.brand_name}")
        await self._send_alert(error)
        
        return HealingResult(
            success=False,
            strategy_used=FixStrategy.RETRY_LATER,
            message=f"All {len(error.strategies_tried)} strategies exhausted",
            should_alert=True
        )
    
    async def _get_fix_strategies(self, error: ScraperError) -> List[FixStrategy]:
        """
        Use LLM to analyze error and suggest fix strategies.
        Falls back to rule-based logic if LLM unavailable.
        """
        # Check if we have successful strategy history for this brand
        brand_history = self._success_history.get(error.brand_key, {})
        if brand_history:
            # Sort by success count, try most successful first
            sorted_strategies = sorted(brand_history.items(), key=lambda x: x[1], reverse=True)
            priority_strategies = [FixStrategy(s) for s, _ in sorted_strategies if s not in error.strategies_tried]
            if priority_strategies:
                logger.info(f"[Healer] Using historical success data: {[s.value for s in priority_strategies[:3]]}")
        else:
            priority_strategies = []
        
        # Try LLM analysis
        if self._llm:
            try:
                llm_strategies = await self._llm_analyze(error)
                if llm_strategies:
                    return priority_strategies + [s for s in llm_strategies if s not in priority_strategies]
            except Exception as e:
                logger.warning(f"[Healer] LLM analysis failed, using rule-based: {e}")
        
        # Fallback to rule-based strategy selection
        return priority_strategies + self._rule_based_strategies(error)
    
    async def _llm_analyze(self, error: ScraperError) -> List[FixStrategy]:
        """Use Gemini Flash to analyze error and suggest strategies."""
        
        strategy_descriptions = "\n".join([
            f"- {s.value}: {self._get_strategy_description(s)}"
            for s in FixStrategy
        ])
        
        prompt = f"""You are a web scraping expert. Analyze this scraper error and suggest the best fix strategies.

{error.to_context_string()}

AVAILABLE STRATEGIES:
{strategy_descriptions}

Based on the error, return a JSON array of strategy names in order of most likely to succeed.
Only return the JSON array, no other text.
Example: ["use_proxy", "rotate_user_agent", "add_delay"]

Consider:
- HTTP 403/429 usually means blocking - try proxy or delay
- Timeout errors - increase timeout or reduce concurrency  
- Captcha/Cloudflare - need proxy or Playwright
- Connection errors - try retry_later first
- JSON parse errors - website structure may have changed
"""

        try:
            response = await self._llm.chat(prompt, model=self._llm_model)
            # Parse JSON array from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                strategies_raw = json.loads(json_match.group())
            else:
                strategies_raw = json.loads(response_text)
            
            strategies = []
            for s in strategies_raw:
                try:
                    strategies.append(FixStrategy(s))
                except ValueError:
                    continue
            
            logger.info(f"[Healer] LLM suggested: {[s.value for s in strategies]}")
            return strategies
            
        except Exception as e:
            logger.error(f"[Healer] LLM parse error: {e}")
            return []
    
    def _rule_based_strategies(self, error: ScraperError) -> List[FixStrategy]:
        """Fallback rule-based strategy selection."""
        strategies = []
        
        # Analyze error patterns
        msg = error.error_message.lower()
        status = error.status_code
        
        # HTTP 403 Forbidden
        if status == 403 or "403" in msg or "forbidden" in msg:
            strategies = [
                FixStrategy.USE_PROXY,
                FixStrategy.ROTATE_USER_AGENT,
                FixStrategy.TRY_MOBILE_UA,
                FixStrategy.ADD_DELAY,
                FixStrategy.USE_PLAYWRIGHT
            ]
        
        # HTTP 429 Rate Limited
        elif status == 429 or "429" in msg or "rate limit" in msg:
            strategies = [
                FixStrategy.ADD_DELAY,
                FixStrategy.USE_PROXY,
                FixStrategy.REDUCE_CONCURRENCY,
                FixStrategy.RETRY_LATER
            ]
        
        # Timeout
        elif "timeout" in msg or "timed out" in msg:
            strategies = [
                FixStrategy.INCREASE_TIMEOUT,
                FixStrategy.USE_PROXY,
                FixStrategy.ADD_DELAY,
                FixStrategy.RETRY_LATER
            ]
        
        # Captcha/Cloudflare
        elif "captcha" in msg or "cloudflare" in msg or "challenge" in msg:
            strategies = [
                FixStrategy.USE_PLAYWRIGHT,
                FixStrategy.USE_PROXY,
                FixStrategy.TRY_MOBILE_UA,
                FixStrategy.RETRY_LATER
            ]
        
        # Connection error
        elif "connection" in msg or "reset" in msg:
            strategies = [
                FixStrategy.RETRY_LATER,
                FixStrategy.USE_PROXY,
                FixStrategy.INCREASE_TIMEOUT
            ]
        
        # JSON/Parse error
        elif "json" in msg or "parse" in msg or "decode" in msg:
            strategies = [
                FixStrategy.TRY_JSON_API,
                FixStrategy.USE_PLAYWRIGHT,
                FixStrategy.CLEAR_COOKIES
            ]
        
        # Default
        else:
            strategies = [
                FixStrategy.ROTATE_USER_AGENT,
                FixStrategy.ADD_DELAY,
                FixStrategy.USE_PROXY,
                FixStrategy.RETRY_LATER
            ]
        
        return strategies
    
    async def _apply_strategy_and_retry(
        self, 
        scraper_factory: Callable,
        strategy: FixStrategy,
        error: ScraperError
    ) -> HealingResult:
        """Apply a fix strategy and retry the scrape."""
        
        from scrapers.scraper_utils import (
            get_random_user_agent,
            proxy_manager,
            random_delay,
            USER_AGENTS
        )
        
        scraper = scraper_factory()
        
        # Apply strategy modifications
        if strategy == FixStrategy.INCREASE_TIMEOUT:
            # Most scrapers use 30s default, increase to 60s
            scraper.timeout = 60
            
        elif strategy == FixStrategy.ROTATE_USER_AGENT:
            # Force new UA on next request
            pass  # UA rotation happens in fetch_with_protection
            
        elif strategy == FixStrategy.USE_PROXY:
            scraper.use_proxy = True
            if not proxy_manager.is_configured:
                return HealingResult(
                    success=False,
                    strategy_used=strategy,
                    message="Proxy not configured"
                )
                
        elif strategy == FixStrategy.ADD_DELAY:
            # Add significant delay before retry
            await random_delay(15, 30)
            
        elif strategy == FixStrategy.TRY_JSON_API:
            # For Shopify stores, switch to JSON API
            if hasattr(scraper, 'base_url') and 'shopify' in scraper.base_url.lower():
                scraper.use_json_api = True
                
        elif strategy == FixStrategy.USE_PLAYWRIGHT:
            # Mark for Playwright rendering
            scraper.use_playwright = True
            
        elif strategy == FixStrategy.REDUCE_CONCURRENCY:
            # Scrape fewer pages
            scraper.max_pages = 2
            
        elif strategy == FixStrategy.CLEAR_COOKIES:
            # HTTP client handles cookies per-request
            pass
            
        elif strategy == FixStrategy.TRY_MOBILE_UA:
            # Use mobile UA (some sites less aggressive on mobile)
            mobile_uas = [ua for ua in USER_AGENTS if 'iPhone' in ua or 'Android' in ua]
            if mobile_uas:
                scraper.forced_ua = mobile_uas[0]
                
        elif strategy == FixStrategy.RETRY_LATER:
            # Wait 2-5 minutes then retry
            await random_delay(120, 300)
        
        # Retry the scrape
        try:
            products = await scraper.scrape_products(max_pages=3)
            
            return HealingResult(
                success=len(products) > 0,
                strategy_used=strategy,
                message=f"Scraped {len(products)} products" if products else "No products found",
                products_scraped=len(products)
            )
            
        except Exception as e:
            return HealingResult(
                success=False,
                strategy_used=strategy,
                message=str(e)
            )
    
    def _record_success(self, brand_key: str, strategy: FixStrategy):
        """Record successful strategy for future reference."""
        if brand_key not in self._success_history:
            self._success_history[brand_key] = {}
        
        current = self._success_history[brand_key].get(strategy.value, 0)
        self._success_history[brand_key][strategy.value] = current + 1
    
    def _get_strategy_description(self, strategy: FixStrategy) -> str:
        """Get human-readable description of strategy."""
        descriptions = {
            FixStrategy.INCREASE_TIMEOUT: "Increase request timeout from 30s to 60s",
            FixStrategy.ROTATE_USER_AGENT: "Switch to a different browser user agent",
            FixStrategy.USE_PROXY: "Route request through residential proxy",
            FixStrategy.ADD_DELAY: "Add 15-30 second delay before retry",
            FixStrategy.TRY_JSON_API: "Switch to Shopify JSON API endpoint",
            FixStrategy.USE_PLAYWRIGHT: "Use headless browser instead of HTTP",
            FixStrategy.REDUCE_CONCURRENCY: "Scrape fewer pages to reduce load",
            FixStrategy.CLEAR_COOKIES: "Clear cookies and start fresh session",
            FixStrategy.TRY_MOBILE_UA: "Use mobile device user agent",
            FixStrategy.RETRY_LATER: "Wait 2-5 minutes then retry",
        }
        return descriptions.get(strategy, "Unknown strategy")
    
    async def _send_alert(self, error: ScraperError):
        """Send email alert to admin (rate limited to every 5 mins per brand)."""
        brand_key = error.brand_key
        now = datetime.now(timezone.utc)
        
        # Check rate limit
        last_alert = self._last_alert_time.get(brand_key)
        if last_alert and (now - last_alert) < self._alert_interval:
            logger.info(f"[Healer] Skipping alert for {brand_key} - rate limited")
            return
        
        self._last_alert_time[brand_key] = now
        
        if not self._smtp_email or not self._smtp_password:
            logger.warning("[Healer] SMTP not configured - cannot send alert")
            return
        
        subject = f"[URGENT] Scraper Alert: {error.brand_name} - All Strategies Exhausted"
        
        body = f"""
SCRAPER SELF-HEALING FAILED
============================

The LLM-powered self-healing system has exhausted all available strategies for {error.brand_name}.

{error.to_context_string()}

STRATEGIES ATTEMPTED:
{chr(10).join(f'  - {s}' for s in error.strategies_tried)}

ACTION REQUIRED:
1. Check if the website structure has changed
2. Verify proxy service is active (if configured)
3. Consider adding new scraping strategy
4. Manual intervention may be needed

---
Drops Curated Self-Healing System
This alert will repeat every 5 minutes until resolved.
"""
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self._smtp_email
            msg['To'] = ", ".join(self._admin_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self._smtp_email, self._smtp_password)
                server.sendmail(self._smtp_email, self._admin_emails, msg.as_string())
            
            logger.info(f"[Healer] Alert email sent for {error.brand_name}")
            
        except Exception as e:
            logger.error(f"[Healer] Failed to send alert email: {e}")
    
    def get_healing_stats(self) -> Dict:
        """Get statistics about healing attempts."""
        return {
            "success_history": self._success_history,
            "last_alerts": {k: v.isoformat() for k, v in self._last_alert_time.items()},
            "total_brands_tracked": len(self._success_history),
        }


# Global healer instance
scraper_healer = ScraperHealer()


async def init_healer(db):
    """Initialize the global healer instance."""
    scraper_healer._db = db
    await scraper_healer.init_llm()
    return scraper_healer
