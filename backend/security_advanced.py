"""
Advanced Security Layers for Drops Curated

Implements:
- Cloudflare Turnstile CAPTCHA verification
- API Key validation for direct API access
- Pagination/scraping detection
- Admin 2FA (CAPTCHA + OTP + IP allowlist)
"""

import os
import re
import secrets
import hashlib
import hmac
import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from collections import defaultdict
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# ============ CLOUDFLARE TURNSTILE ============

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile_token(token: str, remote_ip: Optional[str] = None) -> Dict:
    """
    Verify Cloudflare Turnstile CAPTCHA token.
    Returns validation response or raises HTTPException.
    """
    if not TURNSTILE_SECRET:
        logger.warning("[Turnstile] Secret not configured - skipping verification")
        return {"success": True, "skipped": True}
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token required"
        )
    
    payload = {
        "secret": TURNSTILE_SECRET,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            result = response.json()
            
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.warning(f"[Turnstile] Validation failed: {error_codes}")
                
                if "timeout-or-duplicate" in error_codes:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="CAPTCHA expired. Please try again."
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CAPTCHA verification failed"
                )
            
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"[Turnstile] HTTP error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CAPTCHA service unavailable"
        )


# ============ API KEY VALIDATION ============

# Generate a secure API key for the frontend
FRONTEND_API_KEY = os.getenv("FRONTEND_API_KEY", "")
VALID_API_KEYS = set()

if FRONTEND_API_KEY:
    VALID_API_KEYS.add(FRONTEND_API_KEY)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"dc_{secrets.token_urlsafe(32)}"


def validate_api_key(request: Request) -> bool:
    """
    Validate API key from request headers.
    Prevents direct API access without the frontend.
    """
    # Skip validation if no keys configured (development mode)
    if not VALID_API_KEYS:
        return True
    
    api_key = request.headers.get("X-API-Key", "")
    
    if not api_key:
        return False
    
    return api_key in VALID_API_KEYS


def require_api_key(request: Request):
    """
    Dependency that requires valid API key.
    Use on public endpoints to prevent direct API access.
    """
    if not validate_api_key(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )


# ============ PAGINATION/SCRAPING DETECTION ============

class ScrapingDetector:
    """
    Detect potential data scraping attempts by monitoring
    pagination patterns and request volumes.
    """
    
    def __init__(self):
        self.request_history: Dict[str, List[Dict]] = defaultdict(list)
        self.blocked_scrapers: Dict[str, datetime] = {}
        
        # Thresholds
        self.MAX_PAGES_PER_MINUTE = 20
        self.MAX_TOTAL_PAGES = 100  # Max pages in single session
        self.SEQUENTIAL_PAGE_THRESHOLD = 10  # Suspicious if requesting 10+ sequential pages
        self.BLOCK_DURATION_HOURS = 24
    
    def record_request(self, ip: str, page: int, endpoint: str):
        """Record a paginated request."""
        now = datetime.now(timezone.utc)
        
        # Clean old entries (older than 10 minutes)
        cutoff = now - timedelta(minutes=10)
        self.request_history[ip] = [
            r for r in self.request_history[ip] 
            if datetime.fromisoformat(r["time"]) > cutoff
        ]
        
        # Add new request
        self.request_history[ip].append({
            "page": page,
            "endpoint": endpoint,
            "time": now.isoformat()
        })
    
    def is_scraping(self, ip: str, page: int, endpoint: str) -> Dict:
        """
        Check if request pattern indicates scraping.
        Returns dict with is_scraping bool and reason.
        """
        # Check if already blocked
        if ip in self.blocked_scrapers:
            if datetime.now(timezone.utc) < self.blocked_scrapers[ip]:
                return {
                    "is_scraping": True,
                    "reason": "IP blocked for scraping",
                    "blocked_until": self.blocked_scrapers[ip].isoformat()
                }
            else:
                del self.blocked_scrapers[ip]
        
        # Record this request
        self.record_request(ip, page, endpoint)
        
        history = self.request_history[ip]
        
        # Check 1: Too many pages per minute
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_requests = [
            r for r in history 
            if datetime.fromisoformat(r["time"]) > one_minute_ago
        ]
        
        if len(recent_requests) > self.MAX_PAGES_PER_MINUTE:
            self._block_ip(ip, "Too many pages per minute")
            return {
                "is_scraping": True,
                "reason": f"Rate exceeded: {len(recent_requests)} pages/minute"
            }
        
        # Check 2: Sequential page access pattern
        pages = sorted([r["page"] for r in recent_requests])
        sequential_count = 1
        for i in range(1, len(pages)):
            if pages[i] == pages[i-1] + 1:
                sequential_count += 1
            else:
                sequential_count = 1
            
            if sequential_count >= self.SEQUENTIAL_PAGE_THRESHOLD:
                self._block_ip(ip, "Sequential page scraping")
                return {
                    "is_scraping": True,
                    "reason": "Sequential page access detected"
                }
        
        # Check 3: Total page count
        unique_pages = len(set(pages))
        if unique_pages > self.MAX_TOTAL_PAGES:
            self._block_ip(ip, "Exceeded total page limit")
            return {
                "is_scraping": True,
                "reason": "Too many unique pages accessed"
            }
        
        return {"is_scraping": False}
    
    def _block_ip(self, ip: str, reason: str):
        """Block an IP for scraping."""
        self.blocked_scrapers[ip] = datetime.now(timezone.utc) + timedelta(hours=self.BLOCK_DURATION_HOURS)
        logger.warning(f"[ScrapingDetector] Blocked {ip}: {reason}")
    
    def get_stats(self) -> Dict:
        """Get scraping detection stats."""
        return {
            "active_sessions": len(self.request_history),
            "blocked_ips": len(self.blocked_scrapers),
            "blocked_list": list(self.blocked_scrapers.keys())
        }


# Global scraping detector
scraping_detector = ScrapingDetector()


def check_scraping(request: Request, page: int = 1, endpoint: str = ""):
    """
    Dependency that checks for scraping attempts.
    Use on paginated endpoints.
    """
    from security import get_client_ip
    ip = get_client_ip(request)
    
    result = scraping_detector.is_scraping(ip, page, endpoint or request.url.path)
    
    if result["is_scraping"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result["reason"]
        )


# ============ ADMIN 2FA (CAPTCHA + OTP + IP) ============

class Admin2FA:
    """
    Multi-factor authentication for admin access:
    1. Turnstile CAPTCHA (bot protection)
    2. TOTP/OTP verification (proves identity)
    3. IP allowlist (network restriction)
    """
    
    def __init__(self):
        self.pending_2fa: Dict[str, Dict] = {}  # email -> {otp, expires, captcha_verified}
        self.otp_attempts: Dict[str, int] = defaultdict(int)
        
    def generate_otp(self) -> str:
        """Generate 6-digit OTP."""
        return f"{secrets.randbelow(1000000):06d}"
    
    async def initiate_2fa(
        self, 
        email: str, 
        turnstile_token: str,
        remote_ip: str
    ) -> Dict:
        """
        Step 1: Verify CAPTCHA and send OTP.
        """
        # Verify Turnstile CAPTCHA
        await verify_turnstile_token(turnstile_token, remote_ip)
        
        # Generate OTP
        otp = self.generate_otp()
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        self.pending_2fa[email] = {
            "otp": otp,
            "expires": expires,
            "captcha_verified": True,
            "ip": remote_ip
        }
        
        # In production, send OTP via WhatsApp/Email
        # For now, return it (remove in production!)
        logger.info(f"[Admin2FA] OTP for {email}: {otp}")
        
        return {
            "message": "OTP sent to your registered device",
            "expires_in": 600,  # 10 minutes
            # Remove this in production:
            "_debug_otp": otp if os.getenv("DEBUG") else None
        }
    
    def verify_otp(
        self, 
        email: str, 
        otp: str, 
        remote_ip: str,
        ip_allowlist: List[str]
    ) -> Dict:
        """
        Step 2: Verify OTP and IP allowlist.
        """
        # Check attempt count
        if self.otp_attempts[email] >= 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many failed attempts. Account locked."
            )
        
        pending = self.pending_2fa.get(email)
        
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending 2FA. Start login again."
            )
        
        # Check expiration
        if datetime.now(timezone.utc) > pending["expires"]:
            del self.pending_2fa[email]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Start login again."
            )
        
        # Verify OTP
        if not hmac.compare_digest(pending["otp"], otp):
            self.otp_attempts[email] += 1
            remaining = 5 - self.otp_attempts[email]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )
        
        # Verify IP allowlist (if configured)
        if ip_allowlist and ip_allowlist != ['']:
            if remote_ip not in ip_allowlist:
                logger.warning(f"[Admin2FA] IP {remote_ip} not in allowlist for {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied from this IP address"
                )
        
        # Success - clear pending 2FA
        del self.pending_2fa[email]
        self.otp_attempts[email] = 0
        
        return {"verified": True}
    
    def clear_expired(self):
        """Clean up expired pending 2FA entries."""
        now = datetime.now(timezone.utc)
        expired = [
            email for email, data in self.pending_2fa.items()
            if now > data["expires"]
        ]
        for email in expired:
            del self.pending_2fa[email]


# Global Admin 2FA instance
admin_2fa = Admin2FA()


# ============ COMBINED SECURITY CHECK ============

async def full_security_check(
    request: Request,
    turnstile_token: Optional[str] = None,
    require_captcha: bool = True,
    check_api_key: bool = True,
    check_scraping: bool = False,
    page: int = 1
) -> Dict:
    """
    Combined security check that can be used as a dependency.
    
    Layers:
    1. API Key validation (if enabled)
    2. Turnstile CAPTCHA (if required)
    3. Scraping detection (if enabled)
    """
    from security import get_client_ip
    ip = get_client_ip(request)
    
    result = {
        "ip": ip,
        "api_key_valid": True,
        "captcha_valid": True,
        "scraping_check": True
    }
    
    # Layer 1: API Key
    if check_api_key:
        if not validate_api_key(request):
            result["api_key_valid"] = False
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
    
    # Layer 2: Turnstile CAPTCHA
    if require_captcha and turnstile_token:
        captcha_result = await verify_turnstile_token(turnstile_token, ip)
        result["captcha_result"] = captcha_result
    
    # Layer 3: Scraping detection
    if check_scraping:
        scrape_result = scraping_detector.is_scraping(ip, page, request.url.path)
        if scrape_result["is_scraping"]:
            result["scraping_check"] = False
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=scrape_result["reason"]
            )
    
    return result
