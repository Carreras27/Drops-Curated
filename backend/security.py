"""
Comprehensive Security Module for Drops Curated

Implements:
1. Rate Limiting (slowapi)
2. Input Sanitization & Validation
3. Security Headers
4. CORS Lockdown
5. MongoDB Injection Prevention
6. WhatsApp Webhook Verification
7. Admin IP Allowlisting & Brute Force Protection
8. DDoS Protection
9. Sensitive Data Sanitization
10. Dependency Security Check
11. Intrusion Detection & Logging
12. Secrets Rotation Reminder
"""

import os
import re
import hmac
import hashlib
import logging
import bleach
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Callable
from functools import wraps
from collections import defaultdict

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============

# Allowed frontend origins (lock down CORS)
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "https://drops-curated.preview.emergentagent.com"),
    "https://dropscurated.com",
    "https://www.dropscurated.com",
    "http://localhost:3000",  # Development only
]

# Admin IP allowlist (add your IPs here)
ADMIN_IP_ALLOWLIST = os.getenv("ADMIN_IP_ALLOWLIST", "").split(",") if os.getenv("ADMIN_IP_ALLOWLIST") else []

# Max request body size (10KB)
MAX_BODY_SIZE = 10 * 1024  # 10KB

# Rate limit thresholds
RATE_LIMIT_BLOCK_THRESHOLD = 10  # Block after 10 rate limit hits per hour
DDOS_THRESHOLD = 200  # Requests per minute before challenge
DDOS_BLOCK_MINUTES = 10

# Sensitive field patterns to strip from responses
SENSITIVE_PATTERNS = ['token', 'secret', 'password', 'key', 'hash', 'salt', 'credential']

# MongoDB injection patterns
MONGO_INJECTION_PATTERNS = [
    r'\$',  # $ operators
    r'\..*\.',  # Nested dots
    r'__',  # Double underscore
]

# ============ RATE LIMITER SETUP ============

def get_client_ip(request: Request) -> str:
    """Get real client IP, handling proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

limiter = Limiter(key_func=get_client_ip)

# Rate limit configurations
RATE_LIMITS = {
    "subscribe": "3/hour",
    "search": "30/minute",
    "login": "5/15minutes",
    "default": "60/minute",
}

# ============ IN-MEMORY SECURITY TRACKING ============

class SecurityTracker:
    """Track security events in memory for quick access."""
    
    def __init__(self):
        self.failed_logins: Dict[str, List[datetime]] = defaultdict(list)
        self.rate_limit_hits: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        self.connection_counts: Dict[str, int] = defaultdict(int)
        self._db = None
    
    def init_db(self, db):
        """Initialize database reference."""
        self._db = db
    
    def record_failed_login(self, ip: str, endpoint: str):
        """Record a failed login attempt."""
        now = datetime.now(timezone.utc)
        self.failed_logins[ip].append(now)
        
        # Clean old entries (older than 15 minutes for login tracking)
        cutoff = now - timedelta(minutes=15)
        self.failed_logins[ip] = [t for t in self.failed_logins[ip] if t > cutoff]
        
        # Check if should block
        if len(self.failed_logins[ip]) >= 5:
            self.block_ip(ip, hours=1, reason="brute_force_login")
    
    def record_rate_limit_hit(self, ip: str, endpoint: str):
        """Record a rate limit hit."""
        now = datetime.now(timezone.utc)
        self.rate_limit_hits[ip].append(now)
        
        # Clean old entries (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.rate_limit_hits[ip] = [t for t in self.rate_limit_hits[ip] if t > cutoff]
        
        # Check if should block (10+ hits in an hour)
        if len(self.rate_limit_hits[ip]) >= RATE_LIMIT_BLOCK_THRESHOLD:
            self.block_ip(ip, hours=1, reason="excessive_rate_limits")
    
    def block_ip(self, ip: str, hours: int = 1, reason: str = "unknown"):
        """Block an IP address."""
        self.blocked_ips[ip] = datetime.now(timezone.utc) + timedelta(hours=hours)
        logger.warning(f"[Security] Blocked IP {ip} for {hours}h - Reason: {reason}")
        
        # Log to database asynchronously
        if self._db:
            import asyncio
            asyncio.create_task(self._log_security_event(
                event_type="ip_blocked",
                ip=ip,
                details={"reason": reason, "duration_hours": hours}
            ))
    
    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked."""
        if ip in self.blocked_ips:
            if datetime.now(timezone.utc) < self.blocked_ips[ip]:
                return True
            else:
                # Block expired
                del self.blocked_ips[ip]
        return False
    
    def get_block_remaining(self, ip: str) -> int:
        """Get seconds remaining on a block."""
        if ip in self.blocked_ips:
            remaining = (self.blocked_ips[ip] - datetime.now(timezone.utc)).total_seconds()
            return max(0, int(remaining))
        return 0
    
    def increment_connection(self, ip: str) -> int:
        """Increment connection count for an IP."""
        self.connection_counts[ip] += 1
        return self.connection_counts[ip]
    
    def decrement_connection(self, ip: str):
        """Decrement connection count for an IP."""
        if ip in self.connection_counts:
            self.connection_counts[ip] = max(0, self.connection_counts[ip] - 1)
    
    async def _log_security_event(self, event_type: str, ip: str, details: Dict = None):
        """Log security event to database."""
        if not self._db:
            return
        
        try:
            await self._db.security_logs.insert_one({
                "event_type": event_type,
                "ip": ip,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"[Security] Failed to log event: {e}")
    
    async def log_auth_failure(self, ip: str, endpoint: str, reason: str):
        """Log authentication failure."""
        await self._log_security_event(
            event_type="auth_failure",
            ip=ip,
            details={"endpoint": endpoint, "reason": reason}
        )
    
    async def log_rate_limit(self, ip: str, endpoint: str):
        """Log rate limit hit."""
        await self._log_security_event(
            event_type="rate_limit",
            ip=ip,
            details={"endpoint": endpoint}
        )


# Global security tracker
security_tracker = SecurityTracker()


# ============ INPUT SANITIZATION ============

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string input - strip HTML, JS, and dangerous chars."""
    if not isinstance(value, str):
        return str(value)[:max_length]
    
    # Strip HTML tags
    cleaned = bleach.clean(value, tags=[], strip=True)
    
    # Remove potential JS
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)
    
    # Remove MongoDB injection attempts
    cleaned = re.sub(r'\$', '', cleaned)
    
    # Trim and limit length
    return cleaned.strip()[:max_length]


def sanitize_search_query(query: str) -> str:
    """Sanitize search query - more aggressive cleaning."""
    if not query:
        return ""
    
    # Remove all special characters except spaces and alphanumeric
    cleaned = re.sub(r'[^\w\s\-]', '', query, flags=re.UNICODE)
    
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()[:200]


def validate_phone_number(phone: str) -> bool:
    """Validate Indian phone number - must be 10 digits starting with 6-9."""
    if not phone:
        return False
    
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Must be exactly 10 digits starting with 6-9
    if len(digits) != 10:
        return False
    
    if digits[0] not in '6789':
        return False
    
    return True


def validate_object_id(id_string: str) -> bool:
    """Validate MongoDB ObjectId format."""
    if not id_string:
        return False
    
    # ObjectId is 24 hex characters
    return bool(re.match(r'^[a-fA-F0-9]{24}$', str(id_string)))


def check_mongo_injection(data: Any, path: str = "") -> List[str]:
    """Check for MongoDB injection patterns in data."""
    issues = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            # Check key for injection
            if any(re.search(pattern, key) for pattern in MONGO_INJECTION_PATTERNS):
                issues.append(f"Suspicious key at {path}.{key}")
            
            # Recursively check value
            issues.extend(check_mongo_injection(value, f"{path}.{key}"))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            issues.extend(check_mongo_injection(item, f"{path}[{i}]"))
    
    elif isinstance(data, str):
        if data.startswith('$'):
            issues.append(f"Operator injection at {path}: {data[:50]}")
    
    return issues


def sanitize_request_body(body: Dict) -> Dict:
    """Sanitize entire request body."""
    sanitized = {}
    
    for key, value in body.items():
        # Sanitize key
        clean_key = sanitize_string(key, max_length=100)
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[clean_key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[clean_key] = sanitize_request_body(value)
        elif isinstance(value, list):
            sanitized[clean_key] = [
                sanitize_request_body(v) if isinstance(v, dict) 
                else sanitize_string(v) if isinstance(v, str) 
                else v
                for v in value
            ]
        else:
            sanitized[clean_key] = value
    
    return sanitized


# ============ RESPONSE SANITIZATION ============

def mask_phone_number(phone: str) -> str:
    """Mask phone number - show only last 4 digits."""
    if not phone:
        return ""
    
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 4:
        return digits
    
    return "x" * (len(digits) - 4) + digits[-4:]


def sanitize_response(data: Any) -> Any:
    """Sanitize response data - remove sensitive fields and mask data."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Skip internal MongoDB fields (except 'id')
            if key.startswith('_') and key != '_id':
                continue
            
            # Convert _id to id
            if key == '_id':
                sanitized['id'] = str(value)
                continue
            
            # Skip sensitive fields
            if any(pattern in key.lower() for pattern in SENSITIVE_PATTERNS):
                continue
            
            # Mask phone numbers
            if 'phone' in key.lower() and isinstance(value, str):
                sanitized[key] = mask_phone_number(value)
                continue
            
            # Recursively sanitize
            sanitized[key] = sanitize_response(value)
        
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_response(item) for item in data]
    
    return data


# ============ SECURITY HEADERS MIDDLEWARE ============

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://*.emergentagent.com https://*.razorpay.com; "
            "frame-ancestors 'none';"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Force HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


# ============ REQUEST VALIDATION MIDDLEWARE ============

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize all incoming requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = get_client_ip(request)
        
        # Check if IP is blocked
        if security_tracker.is_blocked(ip):
            remaining = security_tracker.get_block_remaining(ip)
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"IP temporarily blocked. Try again in {remaining} seconds.",
                    "retry_after": remaining
                }
            )
        
        # Check concurrent connections (DDoS protection)
        conn_count = security_tracker.increment_connection(ip)
        if conn_count > 100:
            security_tracker.decrement_connection(ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many concurrent connections"}
            )
        
        try:
            # Check request body size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large. Maximum {MAX_BODY_SIZE} bytes."}
                )
            
            response = await call_next(request)
            return response
            
        finally:
            security_tracker.decrement_connection(ip)


# ============ CORS MIDDLEWARE ============

def validate_cors_origin(origin: str) -> bool:
    """Validate if origin is allowed."""
    if not origin:
        return False
    
    # Check exact match
    if origin in ALLOWED_ORIGINS:
        return True
    
    # Check wildcard patterns (e.g., *.emergentagent.com)
    for allowed in ALLOWED_ORIGINS:
        if allowed.startswith("*"):
            pattern = allowed.replace("*", ".*")
            if re.match(pattern, origin):
                return True
    
    return False


class CORSLockdownMiddleware(BaseHTTPMiddleware):
    """Strict CORS validation."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight
        if request.method == "OPTIONS":
            if origin and validate_cors_origin(origin):
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Authorization, Content-Type",
                        "Access-Control-Max-Age": "86400",
                    }
                )
            return Response(status_code=403)
        
        response = await call_next(request)
        
        # Add CORS headers for allowed origins
        if origin and validate_cors_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


# ============ WHATSAPP WEBHOOK VERIFICATION ============

def verify_whatsapp_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify Meta webhook signature."""
    if not signature or not app_secret:
        return False
    
    # Signature format: sha256=<hash>
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = signature[7:]  # Remove "sha256=" prefix
    
    # Calculate HMAC
    computed = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed, expected_signature)


# ============ ADMIN PROTECTION ============

def check_admin_ip(request: Request) -> bool:
    """Check if request IP is in admin allowlist."""
    if not ADMIN_IP_ALLOWLIST or ADMIN_IP_ALLOWLIST == ['']:
        # No allowlist configured - allow all (for development)
        return True
    
    ip = get_client_ip(request)
    return ip in ADMIN_IP_ALLOWLIST


async def admin_brute_force_check(ip: str, success: bool, db=None):
    """Check and handle admin login brute force attempts."""
    if success:
        # Clear failed attempts on success
        security_tracker.failed_logins[ip] = []
        return True
    
    security_tracker.record_failed_login(ip, "/api/admin/login")
    
    # Log to database
    if db:
        await security_tracker.log_auth_failure(ip, "/api/admin/login", "invalid_credentials")
    
    # Check if account should be locked
    attempts = len(security_tracker.failed_logins[ip])
    if attempts >= 5:
        # Send WhatsApp alert
        try:
            from whatsapp import send_admin_alert
            await send_admin_alert(
                f"⚠️ SECURITY ALERT\n\n"
                f"Admin login blocked after {attempts} failed attempts\n"
                f"IP: {ip}\n"
                f"Blocked for 1 hour"
            )
        except:
            pass
        
        return False
    
    return True


# ============ DEPENDENCY SECURITY CHECK ============

async def check_dependency_security():
    """Check installed packages for known CVEs."""
    import subprocess
    import sys
    
    try:
        # Run safety check using the same Python interpreter
        result = subprocess.run(
            [sys.executable, "-m", "safety", "check", "--json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            # Parse vulnerabilities
            import json
            try:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", [])
                
                if vulnerabilities:
                    vuln_list = "\n".join([
                        f"- {v.get('package_name', 'unknown')}: {v.get('vulnerability_id', 'CVE')}"
                        for v in vulnerabilities[:5]
                    ])
                    
                    logger.warning(f"[Security] Found {len(vulnerabilities)} vulnerable packages:\n{vuln_list}")
                    
                    # Alert admin
                    try:
                        from whatsapp import send_admin_alert
                        import asyncio
                        asyncio.create_task(send_admin_alert(
                            f"⚠️ DEPENDENCY ALERT\n\n"
                            f"Found {len(vulnerabilities)} vulnerable packages:\n{vuln_list}"
                        ))
                    except:
                        pass
                    
                    return vulnerabilities
            except json.JSONDecodeError:
                pass
        
        logger.info("[Security] Dependency check passed - no known vulnerabilities")
        return []
        
    except Exception as e:
        logger.warning(f"[Security] Dependency check failed: {e}")
        return []


# ============ SECRETS ROTATION CHECK ============

async def check_secrets_rotation(db):
    """Check if secrets need rotation (>90 days)."""
    try:
        config = await db.system_config.find_one({"key": "jwt_secret_rotated"})
        
        if not config:
            # No record - create one
            await db.system_config.insert_one({
                "key": "jwt_secret_rotated",
                "value": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc)
            })
            return True
        
        last_rotated = datetime.fromisoformat(config["value"].replace("Z", "+00:00"))
        days_since = (datetime.now(timezone.utc) - last_rotated).days
        
        if days_since > 90:
            logger.warning(f"[Security] JWT secret was last rotated {days_since} days ago - needs rotation!")
            
            try:
                from whatsapp import send_admin_alert
                await send_admin_alert(
                    f"⚠️ SECRET ROTATION REMINDER\n\n"
                    f"JWT secret was last rotated {days_since} days ago.\n"
                    f"Please rotate secrets for security."
                )
            except:
                pass
            
            return False
        
        logger.info(f"[Security] JWT secret last rotated {days_since} days ago")
        return True
        
    except Exception as e:
        logger.error(f"[Security] Secrets rotation check failed: {e}")
        return True


# ============ SECURITY LOG TTL INDEX ============

async def setup_security_indexes(db):
    """Set up security log indexes including TTL."""
    try:
        # TTL index - auto-delete after 30 days
        await db.security_logs.create_index(
            "created_at",
            expireAfterSeconds=30 * 24 * 60 * 60  # 30 days
        )
        
        # Query indexes
        await db.security_logs.create_index([("event_type", 1), ("timestamp", -1)])
        await db.security_logs.create_index([("ip", 1), ("timestamp", -1)])
        
        logger.info("[Security] Security log indexes created")
    except Exception as e:
        logger.warning(f"[Security] Index creation warning: {e}")


# ============ RATE LIMIT HANDLER ============

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded."""
    ip = get_client_ip(request)
    endpoint = request.url.path
    
    # Record the hit
    security_tracker.record_rate_limit_hit(ip, endpoint)
    
    # Log to database
    if security_tracker._db:
        await security_tracker.log_rate_limit(ip, endpoint)
    
    # Calculate retry time
    retry_after = 60  # Default 1 minute
    if "hour" in str(exc.detail):
        retry_after = 3600
    elif "15minutes" in str(exc.detail):
        retry_after = 900
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
            "retry_after": retry_after
        },
        headers={"Retry-After": str(retry_after)}
    )


# ============ INITIALIZATION ============

async def init_security(app, db):
    """Initialize all security features."""
    security_tracker.init_db(db)
    
    # Set up indexes
    await setup_security_indexes(db)
    
    # Check dependency security
    await check_dependency_security()
    
    # Check secrets rotation
    await check_secrets_rotation(db)
    
    logger.info("[Security] Security module initialized")


# ============ DECORATORS ============

def require_admin_ip(func):
    """Decorator to require admin IP for endpoint."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not check_admin_ip(request):
            raise HTTPException(
                status_code=403,
                detail="Access denied - IP not in allowlist"
            )
        return await func(request, *args, **kwargs)
    return wrapper


def sanitize_input(func):
    """Decorator to sanitize request body."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find request body in kwargs
        for key in ['body', 'data', 'payload']:
            if key in kwargs and isinstance(kwargs[key], dict):
                kwargs[key] = sanitize_request_body(kwargs[key])
        return await func(*args, **kwargs)
    return wrapper
