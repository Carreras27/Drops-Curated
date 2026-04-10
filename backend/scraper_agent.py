"""
LLM-Powered Self-Healing Scraper Agent

The brain of the scraper system that automatically diagnoses and fixes failures.
Uses Gemini to analyze errors, pick strategies, and even rewrite selectors.

Flow:
    Scraper fails → Agent receives error context → Diagnoses with Gemini →
    Tries strategies one by one (60s gap) → Logs everything to DB →
    Learns from success/failure → 3 hours exhausted? → WhatsApp admin

Collections:
    - scraper_agent_logs: Every attempt and result
    - scraper_strategies: Winning strategies with confidence scores
"""

import asyncio
import logging
import os
import re
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FixStrategy(Enum):
    """Available fix strategies in priority order."""
    SWITCH_TO_JSON_API = "switch_to_json_api"
    ROTATE_PROXY = "rotate_proxy"
    SWITCH_USER_AGENT = "switch_user_agent"
    ADD_LONGER_DELAYS = "add_longer_delays"
    USE_PLAYWRIGHT = "use_playwright"
    TRY_DIFFERENT_URL = "try_different_url"
    FETCH_SITEMAP = "fetch_sitemap"
    WAIT_AND_RETRY = "wait_and_retry"
    REWRITE_SELECTORS = "rewrite_selectors"
    TRY_MOBILE_VERSION = "try_mobile_version"


@dataclass
class ErrorContext:
    """Full context for a scraper error."""
    brand_key: str
    brand_name: str
    scraper_name: str
    error_message: str
    error_type: str
    http_status: Optional[int] = None
    response_snippet: str = ""
    url: str = ""
    last_3_errors: List[str] = field(default_factory=list)
    response_time_ms: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompt."""
        errors_str = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(self.last_3_errors)) if self.last_3_errors else "  None"
        return f"""
SCRAPER ERROR CONTEXT
=====================
Brand: {self.brand_name} ({self.brand_key})
Scraper: {self.scraper_name}
Timestamp: {self.timestamp}
URL: {self.url}

Error Type: {self.error_type}
Error Message: {self.error_message}
HTTP Status Code: {self.http_status or 'N/A'}
Response Time: {self.response_time_ms}ms (if >10000ms, likely being throttled)

Last 3 Errors for this brand:
{errors_str}

Response Body Snippet (first 1000 chars):
{self.response_snippet[:1000] if self.response_snippet else 'N/A'}
"""


@dataclass
class AgentAttempt:
    """Record of a single healing attempt."""
    brand_key: str
    strategy: str
    success: bool
    message: str
    products_scraped: int = 0
    response_time_ms: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gemini_diagnosis: str = ""
    error_context: Optional[Dict] = None


@dataclass
class BrandStrategy:
    """Stored winning strategy for a brand with confidence score."""
    brand_key: str
    brand_name: str
    strategy: str
    confidence_score: float = 50.0  # Start at 50, range 0-100
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    custom_selectors: Optional[Dict] = None  # For rewritten selectors
    custom_url_pattern: Optional[str] = None


class ScraperAgent:
    """
    The intelligent brain of the scraper system.
    Diagnoses errors, tries fixes, learns over time.
    """
    
    STRATEGY_GAP_SECONDS = 60  # Gap between strategy attempts
    EXHAUSTION_HOURS = 3  # Hours before sending WhatsApp alert
    SLOW_RESPONSE_THRESHOLD_MS = 10000  # 10 seconds = early warning
    
    def __init__(self, db=None):
        self._db = db
        self._llm = None
        self._llm_model = "gemini/gemini-2.0-flash"
        self._healing_start_times: Dict[str, datetime] = {}  # Track when healing started per brand
        self._recent_response_times: Dict[str, List[int]] = {}  # Track response times per brand
        
    async def init(self, db):
        """Initialize the agent with database and LLM."""
        self._db = db
        
        # Initialize LLM
        try:
            from emergentintegrations.llm.chat import LlmChat
            self._llm = LlmChat(
                api_key=os.getenv("EMERGENT_LLM_KEY"),
                session_id="scraper_agent",
                system_message="""You are an expert web scraping diagnostic agent. Your job is to:
1. Analyze scraper errors and diagnose the root cause
2. Pick the best fix strategy from available options
3. When websites change structure, analyze HTML and suggest new CSS selectors or JSON paths
4. Learn from past successes and failures

Always respond with valid JSON. Be concise and technical."""
            )
            logger.info("[ScraperAgent] LLM initialized successfully")
        except Exception as e:
            logger.error(f"[ScraperAgent] Failed to initialize LLM: {e}")
            self._llm = None
        
        # Ensure indexes
        await self._ensure_indexes()
        
    async def _ensure_indexes(self):
        """Create database indexes for performance."""
        try:
            await self._db.scraper_agent_logs.create_index([("brand_key", 1), ("timestamp", -1)])
            await self._db.scraper_agent_logs.create_index([("timestamp", -1)])
            await self._db.scraper_strategies.create_index([("brand_key", 1)], unique=True)
        except Exception as e:
            logger.warning(f"[ScraperAgent] Index creation warning: {e}")
    
    async def handle_scraper_failure(
        self,
        scraper_factory: Callable,
        error_context: ErrorContext
    ) -> Dict:
        """
        Main entry point: Handle a scraper failure with full self-healing.
        
        Returns dict with success status and details.
        """
        brand_key = error_context.brand_key
        logger.info(f"[ScraperAgent] Handling failure for {brand_key}")
        
        # Track when healing started for this brand
        if brand_key not in self._healing_start_times:
            self._healing_start_times[brand_key] = datetime.now(timezone.utc)
        
        # Log the initial error
        await self._log_attempt(AgentAttempt(
            brand_key=brand_key,
            strategy="initial_failure",
            success=False,
            message=error_context.error_message,
            error_context=asdict(error_context)
        ))
        
        # Get strategies ordered by confidence for this brand
        strategies = await self._get_ordered_strategies(brand_key)
        
        # Diagnose with Gemini
        diagnosis = await self._diagnose_with_gemini(error_context, strategies)
        
        # Try each strategy
        for i, strategy in enumerate(strategies):
            logger.info(f"[ScraperAgent] [{brand_key}] Trying strategy {i+1}/{len(strategies)}: {strategy.value}")
            
            # Check if we've exceeded 3 hour window
            if await self._check_exhaustion(brand_key):
                await self._send_whatsapp_alert(error_context)
                return {"success": False, "exhausted": True, "strategies_tried": i + 1}
            
            # Apply strategy and retry
            result = await self._apply_strategy_and_retry(
                scraper_factory, 
                strategy, 
                error_context,
                diagnosis
            )
            
            # Log the attempt
            await self._log_attempt(AgentAttempt(
                brand_key=brand_key,
                strategy=strategy.value,
                success=result["success"],
                message=result.get("message", ""),
                products_scraped=result.get("products", 0),
                response_time_ms=result.get("response_time_ms"),
                gemini_diagnosis=diagnosis
            ))
            
            if result["success"]:
                # Update confidence scores
                await self._record_success(brand_key, strategy)
                
                # Clear healing start time
                if brand_key in self._healing_start_times:
                    del self._healing_start_times[brand_key]
                
                logger.info(f"[ScraperAgent] [{brand_key}] SUCCESS with strategy: {strategy.value}")
                return {
                    "success": True,
                    "strategy": strategy.value,
                    "products": result.get("products", 0),
                    "strategies_tried": i + 1
                }
            else:
                # Record failure for this strategy
                await self._record_failure(brand_key, strategy)
            
            # Wait between strategies
            if i < len(strategies) - 1:
                logger.info(f"[ScraperAgent] [{brand_key}] Waiting {self.STRATEGY_GAP_SECONDS}s before next strategy...")
                await asyncio.sleep(self.STRATEGY_GAP_SECONDS)
        
        # All strategies exhausted within 3 hours - will alert on next failure or timeout
        logger.warning(f"[ScraperAgent] [{brand_key}] All immediate strategies exhausted")
        return {"success": False, "exhausted": False, "strategies_tried": len(strategies)}
    
    async def _diagnose_with_gemini(self, error_context: ErrorContext, strategies: List[FixStrategy]) -> str:
        """Use Gemini to diagnose the error and recommend strategy order."""
        if not self._llm:
            return "LLM not available - using default strategy order"
        
        strategy_list = "\n".join(f"- {s.value}" for s in strategies)
        
        prompt = f"""{error_context.to_prompt_context()}

AVAILABLE STRATEGIES (in current confidence order):
{strategy_list}

TASKS:
1. Diagnose the root cause of this scraper failure
2. Should we try rewriting CSS selectors? If the response snippet shows a different HTML structure than expected, say "REWRITE_NEEDED"
3. What's your recommended strategy to try first?

Respond with JSON:
{{"diagnosis": "brief technical diagnosis", "rewrite_needed": true/false, "recommended_strategy": "strategy_name", "reason": "why this strategy"}}
"""
        
        try:
            response = await self._llm.chat(prompt, model=self._llm_model)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                diagnosis = data.get("diagnosis", "Unknown")
                
                # If rewrite needed, trigger selector analysis
                if data.get("rewrite_needed"):
                    logger.info(f"[ScraperAgent] Gemini suggests rewriting selectors for {error_context.brand_key}")
                
                return diagnosis
            return response_text[:500]
        except Exception as e:
            logger.error(f"[ScraperAgent] Gemini diagnosis failed: {e}")
            return f"Diagnosis failed: {e}"
    
    async def _get_ordered_strategies(self, brand_key: str) -> List[FixStrategy]:
        """Get strategies ordered by confidence score for this brand."""
        # Get stored strategy data
        stored = await self._db.scraper_strategies.find_one(
            {"brand_key": brand_key},
            {"_id": 0}
        )
        
        # Default order
        default_order = list(FixStrategy)
        
        if not stored:
            return default_order
        
        # If we have a winning strategy with high confidence, put it first
        winning_strategy = stored.get("strategy")
        confidence = stored.get("confidence_score", 50)
        
        if winning_strategy and confidence > 60:
            try:
                winning = FixStrategy(winning_strategy)
                # Put winning strategy first
                ordered = [winning] + [s for s in default_order if s != winning]
                return ordered
            except ValueError:
                pass
        
        return default_order
    
    async def _apply_strategy_and_retry(
        self,
        scraper_factory: Callable,
        strategy: FixStrategy,
        error_context: ErrorContext,
        diagnosis: str
    ) -> Dict:
        """Apply a fix strategy and retry the scrape."""
        
        from scrapers.scraper_utils import (
            get_random_user_agent,
            proxy_manager,
            random_delay,
            USER_AGENTS
        )
        import time
        
        scraper = scraper_factory()
        start_time = time.time()
        
        try:
            # Apply strategy modifications
            if strategy == FixStrategy.SWITCH_TO_JSON_API:
                # For Shopify stores, switch to JSON API
                if hasattr(scraper, 'use_json_api'):
                    scraper.use_json_api = True
                else:
                    return {"success": False, "message": "Not a Shopify store"}
                    
            elif strategy == FixStrategy.ROTATE_PROXY:
                scraper.use_proxy = True
                if not proxy_manager.is_configured:
                    return {"success": False, "message": "No proxy configured"}
                    
            elif strategy == FixStrategy.SWITCH_USER_AGENT:
                # Force rotation happens in fetch_with_protection
                pass
                
            elif strategy == FixStrategy.ADD_LONGER_DELAYS:
                # Add significant delay
                await random_delay(10, 20)
                if hasattr(scraper, 'delay_multiplier'):
                    scraper.delay_multiplier = 3
                    
            elif strategy == FixStrategy.USE_PLAYWRIGHT:
                scraper.use_playwright = True
                
            elif strategy == FixStrategy.TRY_DIFFERENT_URL:
                # Check if we have a custom URL stored
                stored = await self._db.scraper_strategies.find_one(
                    {"brand_key": error_context.brand_key},
                    {"_id": 0, "custom_url_pattern": 1}
                )
                if stored and stored.get("custom_url_pattern"):
                    scraper.base_url = stored["custom_url_pattern"]
                else:
                    # Try common alternatives
                    base = scraper.base_url
                    alternatives = [
                        base.replace("www.", ""),
                        base.replace("://", "://www."),
                        base + "/collections/all",
                        base + "/shop"
                    ]
                    scraper.alternative_urls = alternatives
                    
            elif strategy == FixStrategy.FETCH_SITEMAP:
                # Try to get product URLs from sitemap
                sitemap_urls = await self._fetch_sitemap_urls(scraper.base_url)
                if sitemap_urls:
                    scraper.sitemap_urls = sitemap_urls
                else:
                    return {"success": False, "message": "No sitemap found"}
                    
            elif strategy == FixStrategy.WAIT_AND_RETRY:
                # Wait 30 minutes
                logger.info(f"[ScraperAgent] Waiting 30 minutes before retry...")
                await asyncio.sleep(30 * 60)
                
            elif strategy == FixStrategy.REWRITE_SELECTORS:
                # Use Gemini to analyze and rewrite selectors
                new_selectors = await self._rewrite_selectors_with_gemini(scraper, error_context)
                if new_selectors:
                    scraper.custom_selectors = new_selectors
                    await self._store_custom_selectors(error_context.brand_key, new_selectors)
                else:
                    return {"success": False, "message": "Could not determine new selectors"}
                    
            elif strategy == FixStrategy.TRY_MOBILE_VERSION:
                mobile_uas = [ua for ua in USER_AGENTS if 'iPhone' in ua or 'Android' in ua]
                if mobile_uas:
                    scraper.forced_ua = mobile_uas[0]
            
            # Retry the scrape
            products = await scraper.scrape_products(max_pages=3)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if products and len(products) > 0:
                return {
                    "success": True,
                    "message": f"Scraped {len(products)} products",
                    "products": len(products),
                    "response_time_ms": elapsed_ms
                }
            else:
                return {
                    "success": False,
                    "message": "No products found",
                    "response_time_ms": elapsed_ms
                }
                
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "message": str(e),
                "response_time_ms": elapsed_ms
            }
    
    async def _fetch_sitemap_urls(self, base_url: str) -> List[str]:
        """Try to fetch product URLs from sitemap."""
        sitemap_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap_products_1.xml",
            "/sitemap-products.xml"
        ]
        
        product_urls = []
        
        async with httpx.AsyncClient(timeout=30) as client:
            for path in sitemap_paths:
                try:
                    resp = await client.get(f"{base_url}{path}")
                    if resp.status_code == 200:
                        # Extract product URLs
                        content = resp.text
                        urls = re.findall(r'<loc>([^<]+/products/[^<]+)</loc>', content)
                        product_urls.extend(urls[:100])  # Limit to 100
                        if product_urls:
                            break
                except:
                    continue
        
        return product_urls
    
    async def _rewrite_selectors_with_gemini(self, scraper, error_context: ErrorContext) -> Optional[Dict]:
        """Use Gemini to analyze HTML and suggest new selectors."""
        if not self._llm or not error_context.response_snippet:
            return None
        
        prompt = f"""Analyze this HTML from {error_context.brand_name}'s website and identify where the product data is located.

HTML SNIPPET:
{error_context.response_snippet[:3000]}

The scraper is looking for:
- Product name
- Price
- Image URL
- Product URL
- Brand name

Provide CSS selectors or JSON paths to extract this data. Respond with JSON:
{{
    "product_container": "CSS selector for product cards",
    "name_selector": "CSS selector for product name",
    "price_selector": "CSS selector for price",
    "image_selector": "CSS selector for image",
    "url_selector": "CSS selector for product link",
    "is_json_api": true/false,
    "json_products_path": "path.to.products if JSON",
    "confidence": 0-100
}}
"""
        
        try:
            response = await self._llm.chat(prompt, model=self._llm_model)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                selectors = json.loads(json_match.group())
                if selectors.get("confidence", 0) >= 60:
                    return selectors
        except Exception as e:
            logger.error(f"[ScraperAgent] Selector rewrite failed: {e}")
        
        return None
    
    async def _store_custom_selectors(self, brand_key: str, selectors: Dict):
        """Store custom selectors for a brand."""
        await self._db.scraper_strategies.update_one(
            {"brand_key": brand_key},
            {"$set": {"custom_selectors": selectors, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    
    async def _log_attempt(self, attempt: AgentAttempt):
        """Log an attempt to the database."""
        try:
            await self._db.scraper_agent_logs.insert_one(asdict(attempt))
        except Exception as e:
            logger.error(f"[ScraperAgent] Failed to log attempt: {e}")
    
    async def _record_success(self, brand_key: str, strategy: FixStrategy):
        """Record a successful strategy and increase confidence."""
        now = datetime.now(timezone.utc).isoformat()
        
        await self._db.scraper_strategies.update_one(
            {"brand_key": brand_key},
            {
                "$set": {
                    "strategy": strategy.value,
                    "last_success": now,
                    "updated_at": now
                },
                "$inc": {
                    "success_count": 1,
                    "confidence_score": 5  # Increase by 5 on success
                },
                "$setOnInsert": {
                    "brand_key": brand_key,
                    "failure_count": 0
                }
            },
            upsert=True
        )
        
        # Cap confidence at 100
        await self._db.scraper_strategies.update_one(
            {"brand_key": brand_key, "confidence_score": {"$gt": 100}},
            {"$set": {"confidence_score": 100}}
        )
        
        logger.info(f"[ScraperAgent] Recorded success for {brand_key} with {strategy.value}")
    
    async def _record_failure(self, brand_key: str, strategy: FixStrategy):
        """Record a failed strategy and decrease confidence."""
        now = datetime.now(timezone.utc).isoformat()
        
        # Get current strategy
        current = await self._db.scraper_strategies.find_one(
            {"brand_key": brand_key},
            {"_id": 0, "strategy": 1}
        )
        
        # Only decrease confidence if this was the stored winning strategy
        update = {
            "$set": {"last_failure": now, "updated_at": now},
            "$inc": {"failure_count": 1}
        }
        
        if current and current.get("strategy") == strategy.value:
            update["$inc"]["confidence_score"] = -10  # Decrease by 10 on failure
        
        await self._db.scraper_strategies.update_one(
            {"brand_key": brand_key},
            update,
            upsert=True
        )
        
        # Floor confidence at 0
        await self._db.scraper_strategies.update_one(
            {"brand_key": brand_key, "confidence_score": {"$lt": 0}},
            {"$set": {"confidence_score": 0}}
        )
    
    async def _check_exhaustion(self, brand_key: str) -> bool:
        """Check if we've exceeded the 3 hour healing window."""
        start_time = self._healing_start_times.get(brand_key)
        if not start_time:
            return False
        
        elapsed = datetime.now(timezone.utc) - start_time
        return elapsed > timedelta(hours=self.EXHAUSTION_HOURS)
    
    async def _send_whatsapp_alert(self, error_context: ErrorContext):
        """Send WhatsApp alert to admin after 3 hours of trying."""
        brand_key = error_context.brand_key
        
        # Get all strategies tried
        attempts = await self._db.scraper_agent_logs.find(
            {"brand_key": brand_key},
            {"_id": 0, "strategy": 1, "success": 1, "message": 1}
        ).sort("timestamp", -1).limit(20).to_list(20)
        
        strategies_tried = [a["strategy"] for a in attempts if a["strategy"] != "initial_failure"]
        
        message = f"""🚨 SCRAPER AGENT ALERT

Brand: {error_context.brand_name}
Status: FAILED after 3 hours of self-healing

Strategies tried:
{chr(10).join(f'• {s}' for s in set(strategies_tried))}

Last error: {error_context.error_message[:200]}

Manual intervention required."""
        
        try:
            from whatsapp import send_admin_alert
            await send_admin_alert(message)
            logger.info(f"[ScraperAgent] WhatsApp alert sent for {brand_key}")
        except Exception as e:
            logger.error(f"[ScraperAgent] Failed to send WhatsApp alert: {e}")
        
        # Also send email
        await self._send_email_alert(error_context, strategies_tried)
        
        # Clear the start time
        if brand_key in self._healing_start_times:
            del self._healing_start_times[brand_key]
    
    async def _send_email_alert(self, error_context: ErrorContext, strategies_tried: List[str]):
        """Send email alert to admin."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_email = os.getenv("SMTP_EMAIL", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not smtp_email or not smtp_password:
            return
        
        subject = f"[URGENT] Scraper Agent Failed: {error_context.brand_name}"
        body = f"""
SCRAPER AGENT EXHAUSTED ALL STRATEGIES
======================================

Brand: {error_context.brand_name} ({error_context.brand_key})
URL: {error_context.url}
Time spent healing: 3+ hours

Error: {error_context.error_message}
HTTP Status: {error_context.http_status or 'N/A'}

Strategies Attempted:
{chr(10).join(f'  • {s}' for s in set(strategies_tried))}

Response Snippet:
{error_context.response_snippet[:500]}

---
This is an automated alert from the Drops Curated Scraper Agent.
Manual intervention is required.
"""
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = smtp_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, [smtp_email], msg.as_string())
        except Exception as e:
            logger.error(f"[ScraperAgent] Email alert failed: {e}")
    
    # ============ PROACTIVE MONITORING ============
    
    def record_response_time(self, brand_key: str, response_time_ms: int):
        """Record response time for proactive monitoring."""
        if brand_key not in self._recent_response_times:
            self._recent_response_times[brand_key] = []
        
        times = self._recent_response_times[brand_key]
        times.append(response_time_ms)
        
        # Keep last 10 measurements
        if len(times) > 10:
            times.pop(0)
    
    def check_response_degradation(self, brand_key: str) -> Optional[Dict]:
        """
        Check if response times are degrading (early warning of blocking).
        Returns warning info if degradation detected.
        """
        times = self._recent_response_times.get(brand_key, [])
        
        if len(times) < 3:
            return None
        
        # Calculate average of first 3 and last 3
        early_avg = sum(times[:3]) / 3
        recent_avg = sum(times[-3:]) / 3
        
        # Check if recent is significantly slower
        if recent_avg > self.SLOW_RESPONSE_THRESHOLD_MS:
            return {
                "brand_key": brand_key,
                "warning": "Response time exceeds 10s threshold",
                "early_avg_ms": int(early_avg),
                "recent_avg_ms": int(recent_avg),
                "recommendation": "Consider proactive strategy switch"
            }
        
        # Check if response time has doubled
        if early_avg > 0 and recent_avg > early_avg * 2:
            return {
                "brand_key": brand_key,
                "warning": "Response time has doubled",
                "early_avg_ms": int(early_avg),
                "recent_avg_ms": int(recent_avg),
                "recommendation": "Early warning - impending blocking likely"
            }
        
        return None
    
    async def proactive_check_all_brands(self) -> List[Dict]:
        """Check all brands for response time degradation."""
        warnings = []
        for brand_key in self._recent_response_times:
            warning = self.check_response_degradation(brand_key)
            if warning:
                warnings.append(warning)
                # Log the warning
                await self._log_attempt(AgentAttempt(
                    brand_key=brand_key,
                    strategy="proactive_warning",
                    success=False,
                    message=warning["warning"],
                    response_time_ms=warning["recent_avg_ms"]
                ))
        return warnings
    
    # ============ API DATA METHODS ============
    
    async def get_agent_logs(self, limit: int = 100, brand_key: str = None) -> List[Dict]:
        """Get agent logs for the API endpoint."""
        query = {}
        if brand_key:
            query["brand_key"] = brand_key
        
        logs = await self._db.scraper_agent_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return logs
    
    async def get_brand_strategies(self) -> List[Dict]:
        """Get all brand strategies with confidence scores."""
        strategies = await self._db.scraper_strategies.find(
            {},
            {"_id": 0}
        ).sort("confidence_score", -1).to_list(100)
        
        return strategies
    
    async def get_agent_summary(self) -> Dict:
        """Get summary stats for the agent."""
        total_attempts = await self._db.scraper_agent_logs.count_documents({})
        successful_heals = await self._db.scraper_agent_logs.count_documents({"success": True, "strategy": {"$ne": "initial_failure"}})
        
        # Get top strategies
        pipeline = [
            {"$match": {"success": True, "strategy": {"$ne": "initial_failure"}}},
            {"$group": {"_id": "$strategy", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_strategies = await self._db.scraper_agent_logs.aggregate(pipeline).to_list(5)
        
        # Get recent activity
        recent = await self._db.scraper_agent_logs.find(
            {},
            {"_id": 0, "brand_key": 1, "strategy": 1, "success": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Get brands currently being healed
        healing_brands = list(self._healing_start_times.keys())
        
        return {
            "total_attempts": total_attempts,
            "successful_heals": successful_heals,
            "success_rate": round(successful_heals / max(total_attempts, 1) * 100, 1),
            "top_strategies": [{"strategy": s["_id"], "successes": s["count"]} for s in top_strategies],
            "recent_activity": recent,
            "brands_currently_healing": healing_brands,
            "llm_enabled": self._llm is not None
        }


# Global agent instance
scraper_agent = ScraperAgent()


async def init_scraper_agent(db):
    """Initialize the global agent instance."""
    await scraper_agent.init(db)
    return scraper_agent
