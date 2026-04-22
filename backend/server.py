from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import time
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from enum import Enum
import base64
import openai

# Security imports
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from security import (
    limiter,
    get_client_ip,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    CORSLockdownMiddleware,
    security_tracker,
    init_security,
    rate_limit_exceeded_handler,
    sanitize_string,
    sanitize_search_query,
    validate_phone_number,
    validate_object_id,
    check_mongo_injection,
    sanitize_request_body,
    sanitize_response,
    verify_whatsapp_signature,
    check_admin_ip,
    admin_brute_force_check,
    RATE_LIMITS,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'indiashop-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 30  # 30 days

# OpenAI Configuration (using Emergent LLM Key)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-emergent-541365a2cCb29A3C46')
openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Drops Curated API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Add rate limiter to app
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ============ ENUMS ============
class Category(str, Enum):
    SHOES = "SHOES"
    CLOTHES = "CLOTHES"
    COSMETICS = "COSMETICS"
    ACCESSORIES = "ACCESSORIES"

class Store(str, Enum):
    AMAZON_IN = "AMAZON_IN"
    FLIPKART = "FLIPKART"
    MYNTRA = "MYNTRA"
    AJIO = "AJIO"
    NYKAA = "NYKAA"
    VEG_NON_VEG = "VEG_NON_VEG"
    SUPER_KICKS = "SUPER_KICKS"
    CULTURE_CIRCLE = "CULTURE_CIRCLE"

# ============ MODELS ============
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    createdAt: str

# Contact Form Model
class ContactForm(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    category: str = 'general'
    message: str
    turnstile_token: Optional[str] = None

# ============ AUTH HELPERS ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ============ SUBSCRIPTION PLAN CATALOG ============
# Central source of truth for all subscription plans. Used by /api/plans, payment order
# creation, and payment verification. Amounts are in paise (INR * 100).
PLAN_CATALOG = {
    'monthly': {
        'code': 'monthly',
        'tier': 'regular',
        'label': 'Regular',
        'billing_period': 'monthly',
        'duration_days': 30,
        'amount_paise': 39900,          # ₹399 / month
        'display_price': '₹399',
        'display_period': '/month',
        'brand_limit': 5,               # max brands subscriber can follow
        'savings_pct': 0,
        'benefits': [
            'WhatsApp alerts within 10 seconds',
            'Price drop notifications',
            'New collection drops',
            'Follow up to 5 brands',
            'Digital membership card',
        ],
    },
    'vip_monthly': {
        'code': 'vip_monthly',
        'tier': 'vip',
        'label': 'VIP',
        'billing_period': 'monthly',
        'duration_days': 30,
        'amount_paise': 299900,          # ₹2,999 / month
        'display_price': '₹2,999',
        'display_period': '/month',
        'brand_limit': 0,                # 0 = unlimited
        'savings_pct': 0,
        'benefits': [
            'Alerts for ALL 24+ premium brands (unlimited)',
            'Everything in Regular',
            'Cross-store savings feed (find cheaper elsewhere)',
            'Early-access alerts — 15 min before non-VIP',
            'Exclusive raffle entries & drop priority',
            'Priority WhatsApp concierge support',
            'Premium Apple / Google Wallet membership card',
        ],
    },
    'vip_6mo': {
        'code': 'vip_6mo',
        'tier': 'vip',
        'label': 'VIP',
        'billing_period': 'semiannual',
        'duration_days': 180,
        'amount_paise': 1619500,         # ₹2,999 × 6 × 0.90 = ₹16,195
        'display_price': '₹16,195',
        'display_period': '/6 months',
        'brand_limit': 0,
        'savings_pct': 10,
        'benefits': [
            'Everything in VIP Monthly',
            'Save 10% — 6-month commitment',
        ],
    },
    'vip_yearly': {
        'code': 'vip_yearly',
        'tier': 'vip',
        'label': 'VIP',
        'billing_period': 'yearly',
        'duration_days': 365,
        'amount_paise': 2879000,         # ₹2,999 × 12 × 0.80 = ₹28,790
        'display_price': '₹28,790',
        'display_period': '/year',
        'brand_limit': 0,
        'savings_pct': 20,
        'benefits': [
            'Everything in VIP Monthly',
            'Save 20% — best value',
            'Priority early-access to exclusive drops',
        ],
    },
}


def get_plan(plan_code: str) -> dict:
    """Return a plan dict for a given plan code, falling back to 'monthly'."""
    return PLAN_CATALOG.get(plan_code) or PLAN_CATALOG['monthly']


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({'id': payload['user_id']}, {'_id': 0, 'password_hash': 0})
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')

# ============ AUTH ENDPOINTS ============
@api_router.post('/auth/signup')
async def signup(user_data: UserSignup):
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    
    user_id = f"user_{datetime.now(timezone.utc).timestamp()}"
    user_doc = {
        'id': user_id,
        'email': user_data.email,
        'password_hash': hash_password(user_data.password),
        'name': user_data.name,
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email)
    return {'token': token, 'user': User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})}

@api_router.post('/auth/login')
@limiter.limit("5/15minutes")
async def login(request: Request, login_data: UserLogin):
    ip = get_client_ip(request)
    
    user = await db.users.find_one({'email': login_data.email})
    if not user or not verify_password(login_data.password, user['password_hash']):
        # Record failed attempt
        security_tracker.record_failed_login(ip, "/api/auth/login")
        await security_tracker.log_auth_failure(ip, "/api/auth/login", "invalid_credentials")
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    token = create_jwt_token(user['id'], user['email'])
    return {'token': token, 'user': User(**{k: v for k, v in user.items() if k not in ['password_hash', '_id']})}

@api_router.get('/auth/me', response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)

# ============ CONTACT FORM ============
@api_router.post('/contact')
@limiter.limit("5/minute")
async def submit_contact_form(request: Request, form: ContactForm):
    """
    Handle contact form submission.
    Stores in database and sends email notification.
    Email address is kept on backend only (discreet).
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from security_advanced import verify_turnstile_token
    from security import get_client_ip
    
    # Verify Turnstile CAPTCHA first
    if form.turnstile_token:
        ip = get_client_ip(request)
        await verify_turnstile_token(form.turnstile_token, ip)
    
    # Target email (kept discreet - not exposed to frontend)
    TARGET_EMAIL = "dropscurated@gmail.com"
    
    try:
        # Store in database for record keeping
        contact_doc = {
            'id': f"contact_{datetime.now(timezone.utc).timestamp()}",
            'name': form.name,
            'email': form.email,
            'phone': form.phone,
            'subject': form.subject or 'No Subject',
            'category': form.category,
            'message': form.message,
            'status': 'new',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.contact_submissions.insert_one(contact_doc)
        
        # Prepare email content
        category_labels = {
            'general': 'General Inquiry',
            'support': 'Support / Help',
            'billing': 'Billing / Subscription',
            'partnership': 'Partnership / Business',
            'feedback': 'Feedback / Suggestion',
            'bug': 'Bug Report',
            'other': 'Other'
        }
        
        email_subject = f"[Drops Curated] {category_labels.get(form.category, 'Contact')} - {form.subject or form.name}"
        
        email_body = f"""
New Contact Form Submission
============================

From: {form.name}
Email: {form.email}
Phone: {form.phone or 'Not provided'}
Category: {category_labels.get(form.category, form.category)}
Subject: {form.subject or 'Not provided'}

Message:
---------
{form.message}

============================
Submitted at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        # Try to send email via SMTP (Gmail)
        # Note: For Gmail, you need App Password if 2FA is enabled
        SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
        SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
        
        if SMTP_EMAIL and SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg['From'] = SMTP_EMAIL
                msg['To'] = TARGET_EMAIL
                msg['Subject'] = email_subject
                msg['Reply-To'] = form.email  # Allow easy reply to customer
                
                msg.attach(MIMEText(email_body, 'plain'))
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(SMTP_EMAIL, SMTP_PASSWORD)
                    server.send_message(msg)
                
                # Update status to sent
                await db.contact_submissions.update_one(
                    {'id': contact_doc['id']},
                    {'$set': {'status': 'email_sent'}}
                )
                
                logger.info(f"Contact form email sent: {form.email} -> {TARGET_EMAIL}")
                
            except Exception as email_error:
                logger.warning(f"Failed to send email (stored in DB): {email_error}")
                # Email failed but submission is stored
                await db.contact_submissions.update_one(
                    {'id': contact_doc['id']},
                    {'$set': {'status': 'email_failed', 'email_error': str(email_error)}}
                )
        else:
            # No SMTP configured - just store in database
            logger.info(f"Contact form stored (no SMTP): {form.email}")
            await db.contact_submissions.update_one(
                {'id': contact_doc['id']},
                {'$set': {'status': 'stored_no_smtp'}}
            )
        
        return {
            'success': True,
            'message': 'Thank you! Your message has been received. We\'ll get back to you soon.'
        }
        
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail='Failed to submit contact form')


# ============ HEALTH CHECK ============
@api_router.get('/health')
async def health_check():
    """Public health check endpoint"""
    from scheduler import get_health_status
    
    health = get_health_status()
    
    return {
        'status': health.get('status', 'unknown'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'scraper': {
            'healthy': health.get('scraper_healthy', False),
            'last_run': health.get('last_run'),
            'is_running': health.get('is_running', False)
        },
        'database': {
            'healthy': health.get('db_healthy', True)
        }
    }

# ============ PUBLIC STATS (Fix #10 - Social Proof) ============
@api_router.get('/stats/public')
async def get_public_stats():
    """Get public statistics for social proof on landing page.
    Note: total_products counts only isActive products — must match /scrape/status and
    what a user can actually browse on the site. Do NOT change without also updating
    the scrape status endpoint, or the landing page will show mismatched numbers.
    """
    active_members = await db.subscribers.count_documents({'isActive': True, 'isPaid': True})
    total_products = await db.products.count_documents({'isActive': True})
    total_brands = await db.brands.count_documents({'isActive': {'$ne': False}})
    alerts_sent = await db.alert_log.count_documents({})
    
    return {
        'activeMembers': active_members,
        'productsTracked': total_products,
        'brandsMonitored': total_brands,
        'alertsSent': alerts_sent
    }

# ============ SEARCH SUGGESTIONS (Dynamic Autocomplete) ============
@api_router.get('/search/suggestions')
@limiter.limit("30/minute")
async def get_search_suggestions(
    request: Request,
    q: str = Query(..., min_length=1, description='Search query'),
    limit: int = Query(10, ge=1, le=20)
):
    """
    Get search suggestions for autocomplete.
    Returns matching brands, categories, and product names.
    """
    # Sanitize search query
    search_term = sanitize_search_query(q)
    
    if len(search_term) < 1:
        return {'suggestions': []}
    
    if len(search_term) < 1:
        return {'suggestions': []}
    
    suggestions = []
    
    # 1. Search matching brands (highest priority)
    brand_pipeline = [
        {'$match': {'brand': {'$regex': search_term, '$options': 'i'}}},
        {'$group': {'_id': '$brand', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    brands = await db.products.aggregate(brand_pipeline).to_list(5)
    for b in brands:
        suggestions.append({
            'type': 'brand',
            'value': b['_id'],
            'label': b['_id'],
            'count': b['count'],
            'icon': 'store'
        })
    
    # 2. Search matching stores
    store_pipeline = [
        {'$match': {'store': {'$regex': search_term, '$options': 'i'}}},
        {'$group': {'_id': '$store', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 3}
    ]
    stores = await db.products.aggregate(store_pipeline).to_list(3)
    for s in stores:
        store_name = s['_id'].replace('_', ' ').title()
        suggestions.append({
            'type': 'store',
            'value': s['_id'],
            'label': store_name,
            'count': s['count'],
            'icon': 'building'
        })
    
    # 3. Search matching categories/subcategories
    if len(search_term) >= 2:
        category_pipeline = [
            {'$match': {'aiSubcategory': {'$regex': search_term, '$options': 'i'}}},
            {'$group': {'_id': '$aiSubcategory', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 3}
        ]
        categories = await db.products.aggregate(category_pipeline).to_list(3)
        for c in categories:
            if c['_id']:
                suggestions.append({
                    'type': 'category',
                    'value': c['_id'],
                    'label': c['_id'],
                    'count': c['count'],
                    'icon': 'tag'
                })
    
    # 4. Search matching product names (show top products)
    if len(search_term) >= 2:
        product_query = {'name': {'$regex': search_term, '$options': 'i'}}
        products = await db.products.find(
            product_query, 
            {'_id': 0, 'id': 1, 'name': 1, 'brand': 1, 'price': 1, 'imageUrl': 1}
        ).limit(5).to_list(5)
        
        for p in products:
            suggestions.append({
                'type': 'product',
                'value': p['id'],
                'label': p['name'][:60] + ('...' if len(p['name']) > 60 else ''),
                'brand': p.get('brand', ''),
                'price': p.get('price'),
                'image': p.get('imageUrl'),
                'icon': 'package'
            })
    
    # Remove duplicates and limit
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        key = f"{s['type']}:{s['value']}"
        if key not in seen:
            seen.add(key)
            unique_suggestions.append(s)
        if len(unique_suggestions) >= limit:
            break
    
    return {
        'query': q,
        'suggestions': unique_suggestions
    }

# ============ SEARCH & PRODUCTS ============
@api_router.get('/search')
@limiter.limit("30/minute")
async def search_products(
    request: Request,
    q: str = Query(''),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    store: Optional[str] = None,
    sort: str = Query('date', description='Sort by: date, price_low, price_high, shuffle'),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    import random as rnd
    from security_advanced import scraping_detector
    from security import get_client_ip
    
    # Check for scraping attempts
    ip = get_client_ip(request)
    scrape_check = scraping_detector.is_scraping(ip, page, "/api/search")
    if scrape_check["is_scraping"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=scrape_check["reason"]
        )
    
    query = {}
    # Sanitize search query
    search_term = sanitize_search_query(q)
    
    # Store filter - filter by store/brand key (e.g., CREPDOG_CREW)
    if store:
        query['store'] = {'$regex': f'^{store}$', '$options': 'i'}
    # Search query - searches name, description, brand, tags, store
    elif search_term:
        # Make search flexible: spaces match hyphens and vice versa
        # "li ning" matches "Li-Ning", "ink ivory" matches "INK IVORY"
        import re as _re
        flexible_term = _re.sub(r'[\s\-]+', r'[\\s\\-]+', search_term)
        
        # For very short search terms (<=3 chars like "On", "NIL"), ONLY search brand field
        # This prevents false positives like "Monk On Fire Hoodie" where "on" is just a preposition
        if len(search_term) <= 3:
            # STRICT BRAND-ONLY MATCH for short terms
            query['brand'] = {'$regex': f'^{flexible_term}$', '$options': 'i'}
        elif len(search_term) <= 5:
            # For medium terms (4-5 chars), use word boundary matching on brand and name
            word_regex = f'\\b{flexible_term}\\b'
            query['$or'] = [
                {'brand': {'$regex': f'^{flexible_term}$', '$options': 'i'}},
                {'brand': {'$regex': word_regex, '$options': 'i'}},
                {'name': {'$regex': word_regex, '$options': 'i'}},
                {'store': {'$regex': word_regex, '$options': 'i'}},
            ]
        else:
            # For longer search terms, use standard partial matching
            query['$or'] = [
                {'name': {'$regex': flexible_term, '$options': 'i'}},
                {'description': {'$regex': flexible_term, '$options': 'i'}},
                {'brand': {'$regex': flexible_term, '$options': 'i'}},
                {'tags': {'$regex': flexible_term, '$options': 'i'}},
                {'store': {'$regex': flexible_term, '$options': 'i'}},
            ]
    
    # Brand filter - exact match on brand field
    if brand:
        query['brand'] = {'$regex': f'^{brand}$', '$options': 'i'}

    if category:
        query['category'] = category
    
    # Calculate skip value
    skip_val = skip if skip > 0 else (page - 1) * limit
    
    # Get total count first
    total = await db.products.count_documents(query)
    
    # Determine sort order
    if sort == 'shuffle':
        # For shuffle, get more products and randomize
        products = await db.products.find(query, {'_id': 0}).limit(min(limit * 3, 200)).to_list(min(limit * 3, 200))
        rnd.shuffle(products)
        products = products[:limit]
    elif sort == 'price_low':
        products = await db.products.find(query, {'_id': 0}).sort('price', 1).skip(skip_val).limit(limit).to_list(limit)
    elif sort == 'price_high':
        products = await db.products.find(query, {'_id': 0}).sort('price', -1).skip(skip_val).limit(limit).to_list(limit)
    else:
        # Default: sort by createdAt (newest first) with random seed for variety
        products = await db.products.find(query, {'_id': 0}).sort('createdAt', -1).skip(skip_val).limit(limit).to_list(limit)
    
    # Enrich products with price data
    for product in products:
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(100)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['highestPrice'] = max(p['currentPrice'] for p in prices)
            product['priceCount'] = len(prices)
        else:
            product['lowestPrice'] = product.get('price', 0)
            product['highestPrice'] = product.get('price', 0)
            product['priceCount'] = 1
    
    return {
        'products': products,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    }

@api_router.get('/brand-search')
async def brand_search(
    store: str = Query(..., description='Brand/Store key to search within'),
    q: str = Query('', description='Search query within the brand'),
    sort: str = Query('date', description='Sort by: date, price_low, price_high'),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Search products within a specific brand/store"""
    import random as rnd
    
    # Always filter by store
    query = {'store': {'$regex': f'^{store}$', '$options': 'i'}}
    
    # Add search within the brand's products
    search_term = q.strip()
    if search_term:
        # Search within product name, description, and tags for this brand
        search_conditions = [
            {'name': {'$regex': search_term, '$options': 'i'}},
            {'description': {'$regex': search_term, '$options': 'i'}},
            {'tags': {'$regex': search_term, '$options': 'i'}},
        ]
        query['$and'] = [
            {'store': {'$regex': f'^{store}$', '$options': 'i'}},
            {'$or': search_conditions}
        ]
        # Remove the duplicate store key
        del query['store']
    
    # Calculate skip value
    skip_val = skip if skip > 0 else (page - 1) * limit
    
    # Get total count
    total = await db.products.count_documents(query)
    
    # Fetch products with sorting
    if sort == 'price_low':
        products = await db.products.find(query, {'_id': 0}).sort('price', 1).skip(skip_val).limit(limit).to_list(limit)
    elif sort == 'price_high':
        products = await db.products.find(query, {'_id': 0}).sort('price', -1).skip(skip_val).limit(limit).to_list(limit)
    else:
        products = await db.products.find(query, {'_id': 0}).sort('createdAt', -1).skip(skip_val).limit(limit).to_list(limit)
    
    # Enrich products with price data
    for product in products:
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(100)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['highestPrice'] = max(p['currentPrice'] for p in prices)
            product['priceCount'] = len(prices)
        else:
            product['lowestPrice'] = product.get('price', 0)
            product['highestPrice'] = product.get('price', 0)
            product['priceCount'] = 1
    
    return {
        'products': products,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
        'query': search_term,
        'store': store
    }

# Batch price lookup for wishlist
class ProductIdsRequest(BaseModel):
    ids: List[str]

@api_router.post('/products/prices')
async def get_product_prices(request: Request, data: ProductIdsRequest):
    """
    Get current prices for multiple products by ID.
    Used by wishlist portfolio to show live prices.
    """
    if not data.ids or len(data.ids) == 0:
        return {'prices': {}}
    
    # Limit to 50 products max
    product_ids = data.ids[:50]
    
    prices = {}
    for product_id in product_ids:
        # Get latest price from prices collection
        price_doc = await db.prices.find_one(
            {'productId': product_id},
            {'_id': 0, 'currentPrice': 1},
            sort=[('lastScrapedAt', -1)]
        )
        
        if price_doc:
            prices[product_id] = price_doc['currentPrice']
        else:
            # Fallback to product's price field
            product = await db.products.find_one(
                {'id': product_id},
                {'_id': 0, 'price': 1, 'lowestPrice': 1}
            )
            if product:
                prices[product_id] = product.get('lowestPrice') or product.get('price', 0)
    
    return {'prices': prices}

# NOTE: This route MUST come BEFORE /products/{product_id} to avoid route conflicts
@api_router.get('/products/classified')
async def get_classified_products(
    gender: Optional[str] = Query(None, description='Filter by aiGender'),
    category: Optional[str] = Query(None, description='Filter by aiCategory'),
    subcategory: Optional[str] = Query(None, description='Filter by aiSubcategory'),
    brand: Optional[str] = Query(None, description='Filter by aiBrand'),
    min_confidence: float = Query(0.0, description='Minimum AI confidence'),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Get products filtered by AI classification fields"""
    query = {'aiGender': {'$exists': True}}
    
    if gender:
        query['aiGender'] = gender
    if category:
        query['aiCategory'] = category
    if subcategory:
        query['aiSubcategory'] = {'$regex': subcategory, '$options': 'i'}
    if brand:
        query['aiBrand'] = {'$regex': brand, '$options': 'i'}
    if min_confidence > 0:
        query['aiConfidence'] = {'$gte': min_confidence}
    
    total = await db.products.count_documents(query)
    products = await db.products.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    
    return {
        'products': products,
        'total': total,
        'filters': {
            'gender': gender,
            'category': category,
            'subcategory': subcategory,
            'brand': brand,
            'min_confidence': min_confidence
        }
    }

@api_router.get('/products/{product_id}')
async def get_product(product_id: str):
    product = await db.products.find_one({'id': product_id}, {'_id': 0})
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    # Get direct prices for this product
    prices = await db.prices.find({'productId': product_id}, {'_id': 0}).sort('currentPrice', 1).to_list(100)
    
    # Cross-store matching: find the same product at other stores
    # Build a flexible regex from the product name — extract key terms
    cross_prices = await _find_cross_store_prices(product, prices)
    if cross_prices:
        prices = prices + cross_prices
        # Sort all prices by currentPrice
        prices.sort(key=lambda p: p.get('currentPrice', float('inf')))
    
    return {'product': product, 'prices': prices}


# Token sets used by cross-store product matching
_CS_TYPE_WORDS = {
    'slide', 'slides', 'mules', 'pregame', 'sneaker', 'sneakers',
    'shoe', 'shoes', 'boot', 'boots', 'sandal', 'sandals', 'slipper',
    'hoodie', 'hoody', 'sweatshirt', 'sweater', 'pullover', 'crewneck',
    'tee', 'tshirt', 't-shirt', 'shirt', 'top', 'jersey',
    'jacket', 'coat', 'parka', 'vest', 'bomber', 'windbreaker',
    'pants', 'trouser', 'trousers', 'pant', 'shorts', 'jean', 'jeans',
    'cap', 'hat', 'beanie', 'bag', 'backpack', 'tote', 'sling',
    'sock', 'socks', 'belt', 'wallet',
    'men', 'women', 'mens', 'womens', 'unisex', 'male', 'female',
    'low', 'mid', 'high', 'retro', 'og', 'se', 'premium', 'essential', 'essentials',
    'clothes', 'clothing', 'apparel',
}

# Fit / cut descriptors that may differ across retailer listings
_CS_FIT_WORDS = {
    'boxy', 'oversized', 'regular', 'slim', 'relaxed', 'cropped', 'crop',
    'loose', 'straight', 'skinny', 'tapered', 'baggy', 'fitted', 'fit',
    'wide', 'long', 'short', 'tall', 'mini', 'midi', 'maxi',
    'patched', 'distressed', 'washed', 'raw', 'faded', 'bleached',
}

_CS_COLOR_WORDS = {
    'black', 'white', 'red', 'blue', 'green', 'grey', 'gray', 'pink', 'yellow',
    'orange', 'purple', 'brown', 'navy', 'cream', 'ivory', 'teal', 'silver',
    'gold', 'crimson', 'coral', 'mint', 'menta', 'smoke', 'chrome', 'canary',
    'geode', 'arctic', 'sand', 'ice', 'lime', 'salmon', 'photon', 'dust',
    'pale', 'light', 'dark', 'hyper', 'solar', 'frosted', 'blackened', 'beige',
    'olive', 'khaki', 'maroon', 'burgundy', 'charcoal', 'stone', 'rust',
    'turquoise', 'aqua', 'lilac', 'lavender', 'magenta', 'tan', 'camo',
    'indigo', 'platinum', 'bronze', 'copper', 'emerald', 'ruby', 'sapphire',
    'mocha', 'taupe', 'fuchsia', 'peach', 'wheat', 'rose', 'apricot',
}

_CS_STOPWORDS = {
    'the', 'a', 'an', 'of', 'and', 'for', 'with', 'in', 'on', 'by', 'to',
    'from', 'at', 'as', 'is',
}

# Broad product-type buckets used to ensure a Tee doesn't match a Cap, etc.
_CS_TYPE_BUCKETS = {
    'footwear': {'sneaker', 'sneakers', 'shoe', 'shoes', 'boot', 'boots', 'sandal', 'sandals',
                 'slide', 'slides', 'mule', 'mules', 'slipper', 'slippers', 'trainer', 'trainers',
                 'runner', 'runners', 'clog', 'clogs', 'loafer', 'loafers'},
    'top': {'tee', 'tshirt', 't-shirt', 'shirt', 'top', 'jersey', 'polo', 'tank', 'singlet',
            'blouse'},
    'outerwear': {'hoodie', 'hoody', 'sweatshirt', 'sweater', 'pullover', 'crewneck',
                  'jacket', 'coat', 'parka', 'vest', 'bomber', 'windbreaker', 'cardigan',
                  'zipup', 'zip-up'},
    'bottom': {'pants', 'pant', 'trouser', 'trousers', 'shorts', 'short', 'jean', 'jeans',
               'skirt', 'legging', 'leggings', 'joggers', 'jogger', 'sweatpant', 'sweatpants',
               'cargo', 'cargos', 'chino', 'chinos'},
    'dress': {'dress', 'gown', 'robe', 'kaftan', 'kurta', 'saree'},
    'headwear': {'cap', 'hat', 'beanie', 'bucket', 'visor'},
    'bag': {'bag', 'backpack', 'tote', 'sling', 'duffel', 'crossbody', 'pouch'},
    'accessory': {'sock', 'socks', 'belt', 'wallet', 'scarf', 'gloves', 'glasses',
                  'sunglasses', 'bracelet', 'necklace', 'ring', 'keychain'},
    'homeware': {'quilt', 'blanket', 'throw', 'pillow', 'duvet', 'rug', 'mat', 'towel'},
    'collectible': {'card', 'cards', 'figure', 'figurine', 'poster', 'sticker', 'plush',
                    'model', 'booster', 'deck', 'pack'},
}

def _cs_detect_bucket(tokens: list) -> str:
    """Return the broad product-type bucket for a list of name tokens, or '' if undetected."""
    for bucket, words in _CS_TYPE_BUCKETS.items():
        for t in tokens:
            if t in words:
                return bucket
    return ''


def _cs_tokenize(name: str, brand: str) -> tuple:
    """Return (distinctive_tokens, colors_found, type_bucket) for a product name.
    Distinctive tokens exclude brand words, type words, fit words, colors, stopwords and pure size tokens.
    """
    import re
    if not name:
        return set(), set(), ''
    # Normalize punctuation to spaces but preserve alphanumerics (so "Cloud X 4" stays)
    cleaned = re.sub(r'[^a-zA-Z0-9]+', ' ', name).lower()
    tokens = [t for t in cleaned.split() if t]
    brand_tokens = set()
    if brand:
        brand_tokens = set(re.sub(r'[^a-zA-Z0-9]+', ' ', brand).lower().split())
    size_pattern = re.compile(r'^(xx?x?s|xx?x?l|xxs|xxxl|2xl|3xl|4xl|s|m|l|uk|us|eu)$')
    # All words from any product-type bucket are product-category descriptors and
    # should NOT be treated as distinctive identifiers.
    all_bucket_words: set = set()
    for bucket_words in _CS_TYPE_BUCKETS.values():
        all_bucket_words.update(bucket_words)
    distinctive = set()
    colors = set()
    for t in tokens:
        if t in _CS_COLOR_WORDS:
            colors.add(t)
            continue
        if t in brand_tokens:
            continue
        if t in _CS_TYPE_WORDS or t in _CS_FIT_WORDS or t in _CS_STOPWORDS:
            continue
        if t in all_bucket_words:
            continue
        if size_pattern.match(t):
            continue
        # Keep single-character digits (model numbers like "Ja 1", "Cloud X 4"),
        # but drop other single-character noise.
        if len(t) < 2 and not t.isdigit():
            continue
        distinctive.add(t)
    bucket = _cs_detect_bucket(tokens)
    return distinctive, colors, bucket


async def _find_cross_store_prices(product: dict, existing_prices: list) -> list:
    """Find the same product at other stores using token-overlap fuzzy matching."""
    import re

    name = product.get('name', '')
    brand = product.get('brand', '')
    store = product.get('store', '')

    if not name or not brand:
        return []

    src_tokens, src_colors, src_bucket = _cs_tokenize(name, brand)
    if len(src_tokens) < 1:
        return []

    existing_stores = {p.get('store') for p in existing_prices}
    existing_stores.add(store)

    # Query by same brand + at least one distinctive token present (keeps candidate set small)
    # Build an $or across distinctive tokens — each as a case-insensitive regex.
    token_regexes = [
        {'name': {'$regex': rf'(^|[^a-zA-Z0-9]){re.escape(tok)}([^a-zA-Z0-9]|$)', '$options': 'i'}}
        for tok in list(src_tokens)[:8]
    ]
    if not token_regexes:
        return []

    query_filter = {
        'brand': {'$regex': f'^{re.escape(brand)}$', '$options': 'i'},
        'store': {'$nin': list(existing_stores)},
        'isActive': True,
        '$or': token_regexes,
    }

    try:
        candidates = await db.products.find(
            query_filter,
            {'_id': 0, 'id': 1, 'name': 1, 'store': 1}
        ).limit(50).to_list(50)
    except Exception:
        return []

    if not candidates:
        return []

    # Score candidates by token overlap + color agreement + type-bucket agreement
    scored = []
    for cand in candidates:
        cand_tokens, cand_colors, cand_bucket = _cs_tokenize(cand.get('name', ''), brand)
        if not cand_tokens:
            continue
        shared = src_tokens & cand_tokens
        if not shared:
            continue
        # Type-bucket guard: when both sides have a detectable product-type bucket,
        # they MUST match. Prevents a "Tee" matching a "Cap" just because both
        # share the distinctive name words ("arcana", "jacquard").
        if src_bucket and cand_bucket and src_bucket != cand_bucket:
            continue
        # Jaccard over distinctive tokens
        union = src_tokens | cand_tokens
        jaccard = len(shared) / max(1, len(union))
        # Color compatibility: if both have colors, require at least one overlap
        if src_colors and cand_colors and not (src_colors & cand_colors):
            continue
        scored.append((len(shared), jaccard, cand))

    if not scored:
        return []

    # Require bulletproof match (false positives erode trust more than false negatives):
    #   (a) shared >= 4 distinctive tokens (very strong signal), OR
    #   (b) shared >= 2 AND one side's distinctive tokens fully contained in the other's,
    #       AND the larger side has at most 1 extra distinctive token beyond the shared set.
    # This prevents family-name overlaps like "Crocs Classic Clog Squid Game" vs
    # "Crocs Classic Clog" — the shorter name is a base model that shares a family,
    # not a cross-listing of the same SKU.
    strong = []
    for n, j, c in scored:
        cand_tokens, _, _ = _cs_tokenize(c.get('name', ''), brand)
        if n >= 4:
            strong.append(c)
            continue
        if n >= 2:
            if src_tokens.issubset(cand_tokens) and len(cand_tokens - src_tokens) <= 1:
                strong.append(c)
                continue
            if cand_tokens.issubset(src_tokens) and len(src_tokens - cand_tokens) <= 1:
                strong.append(c)
                continue
    if not strong:
        return []

    # Dedupe by store: keep the candidate with highest score per store
    by_store = {}
    for n, j, c in scored:
        if c not in strong:
            continue
        key = c.get('store')
        prev = by_store.get(key)
        if not prev or (n, j) > (prev[0], prev[1]):
            by_store[key] = (n, j, c)

    cross_prices = []
    for n, j, match in by_store.values():
        match_prices = await db.prices.find(
            {'productId': match['id']},
            {'_id': 0}
        ).to_list(5)
        for mp in match_prices:
            mp['matchedFrom'] = match['name']
            mp['matchedProductId'] = match['id']
            cross_prices.append(mp)

    return cross_prices

@api_router.get('/drops/curated')
async def get_curated_drops():
    """Get products organized by sections: Limited Edition, Trending, New Drops"""
    import re
    
    # Limited Edition keywords to detect
    limited_keywords = [
        r'limited\s*(edition)?',
        r'only\s*\d+\s*(pairs?|pieces?|units?|left)',
        r'exclusive',
        r'rare',
        r'\d+\s*(pairs?|pieces?)\s*(only|left|remaining|available)',
        r'sold\s*out\s*soon',
        r'last\s*(few|chance)',
        r'dropping\s*\d+',
        r'limited\s*stock',
        r'limited\s*release',
        r'special\s*edition',
        r'numbered\s*edition',
        r'collab(oration)?',
    ]
    limited_pattern = re.compile('|'.join(limited_keywords), re.IGNORECASE)
    
    # Function to extract stock number from text
    def extract_stock_number(text):
        if not text:
            return None
        matches = re.findall(r'(\d+)\s*(pairs?|pieces?|units?|left|only|remaining|available|dropping)', text, re.IGNORECASE)
        if matches:
            num = int(matches[0][0])
            if num <= 500:  # Only consider reasonable limited quantities
                return num
        return None
    
    # Get all active products
    all_products = await db.products.find({'isActive': True}, {'_id': 0}).to_list(500)
    
    limited_edition = []
    trending = []
    new_drops = []
    
    for product in all_products:
        # Enrich with price data
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(10)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['highestPrice'] = max(p['currentPrice'] for p in prices)
        else:
            product['lowestPrice'] = 0
            product['highestPrice'] = 0
        
        # Check for limited edition
        search_text = f"{product.get('name', '')} {product.get('description', '')} {' '.join(product.get('tags', []))}"
        if limited_pattern.search(search_text):
            stock_num = extract_stock_number(search_text)
            product['stockLimit'] = stock_num
            product['isLimited'] = True
            limited_edition.append(product)
        
        # Check trending
        if product.get('isTrending'):
            trending.append(product)
        
        # New drops (last 7 days)
        created = product.get('createdAt', '')
        if created:
            try:
                from datetime import datetime, timezone, timedelta
                created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) - created_date < timedelta(days=7):
                    new_drops.append(product)
            except Exception:
                pass
    
    # Sort sections with shuffle for variety
    import random as rnd
    
    # Limited edition - sort by stock limit but shuffle items with same/similar stock
    limited_edition = sorted(limited_edition, key=lambda x: x.get('stockLimit') or 999)[:20]
    rnd.shuffle(limited_edition)
    limited_edition = limited_edition[:12]
    
    # Trending - shuffle for variety
    trending = sorted(trending, key=lambda x: x.get('createdAt', ''), reverse=True)[:20]
    rnd.shuffle(trending)
    trending = trending[:12]
    
    # New drops - sort by date first, then shuffle top items
    new_drops = sorted(new_drops, key=lambda x: x.get('createdAt', ''), reverse=True)[:20]
    rnd.shuffle(new_drops)
    new_drops = new_drops[:12]
    
    # Get last scrape time
    last_scrape = await db.brands.find_one({}, {'_id': 0, 'lastScrapedAt': 1}, sort=[('lastScrapedAt', -1)])
    last_scrape_time = last_scrape.get('lastScrapedAt') if last_scrape else None
    
    return {
        'limited_edition': limited_edition,
        'trending': trending,
        'new_drops': new_drops,
        'counts': {
            'limited': len(limited_edition),
            'trending': len(trending),
            'new': len(new_drops)
        },
        'last_scraped_at': last_scrape_time,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

# ============ CELEBRITY STYLE ============
# Celebrity data with their known style preferences (brands, keywords)
CELEBRITY_DATA = [
    {
        'id': 'travis_scott',
        'name': 'Travis Scott',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/a29d41d9ff81e1f2d4f07469db2f62afb16331f34142846baa62f306fdcf8f7a.png',
        'style_keywords': ['jordan', 'nike', 'dunk', 'air jordan', 'travis'],
        'brands': ['Nike Air Jordan', 'AIR JORDAN', 'Nike Dunk', 'NIKE'],
        'category': 'Hip-Hop Icon'
    },
    {
        'id': 'ranveer_singh',
        'name': 'Ranveer Singh',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/329253afcfdfbc27373e820e4d2d0527991dbcd73df453ee3c5ff36929928da3.png',
        'style_keywords': ['gucci', 'balenciaga', 'oversized', 'bold', 'colorful', 'huemn'],
        'brands': ['Urban Monkey®', 'House of Koala', 'HUEMN', 'Huemn'],
        'category': 'Bollywood Style King'
    },
    {
        'id': 'kanye_west',
        'name': 'Kanye West',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/c773912009908ed5a2411d876b8535b02aaef22d6437ea1aa2b34652b64974db.png',
        'style_keywords': ['yeezy', 'adidas', 'foam', 'boost', 'minimal'],
        'brands': ['ADIDAS', 'Adidas Yeezy', 'NEW BALANCE'],
        'category': 'Yeezy Pioneer'
    },
    {
        'id': 'asap_rocky',
        'name': 'A$AP Rocky',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/594ce23741ea35525fead63f03b410404c6097eba6cd37c9b8adaad17b6b619d.png',
        'style_keywords': ['vans', 'adidas', 'new balance', 'retro', 'vintage'],
        'brands': ['VANS', 'ADIDAS', 'NEW BALANCE'],
        'category': 'Fashion Forward'
    },
    {
        'id': 'billie_eilish',
        'name': 'Billie Eilish',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/16746c29104da6b37a09138a355586f9a8d1ef69252ba343952e2940f5a5e743.png',
        'style_keywords': ['oversized', 'nike', 'jordan', 'baggy', 'streetwear'],
        'brands': ['Nike Air Jordan', 'AIR JORDAN', 'NIKE', 'Urban Monkey®'],
        'category': 'Gen Z Icon'
    },
    {
        'id': 'pharrell_williams',
        'name': 'Pharrell Williams',
        'image': 'https://static.prod-images.emergentagent.com/jobs/921b3e03-5859-468d-bad4-ffdaf98d9621/images/27cdb86b980977d815ceed47019ca8669f295195638d12b29b337073a6a141cf.png',
        'style_keywords': ['adidas', 'human race', 'nmd', 'colorful', 'bold'],
        'brands': ['ADIDAS', 'NEW BALANCE', 'HOKA'],
        'category': 'Music & Fashion'
    },
    {
        'id': 'virgil_abloh',
        'name': 'Virgil Abloh',
        'image': 'https://ui-avatars.com/api/?name=Virgil+Abloh&background=001f3f&color=c9a961&size=400&bold=true',
        'style_keywords': ['off-white', 'nike', 'jordan', 'dunk', 'air force'],
        'brands': ['Nike Air Jordan', 'AIR JORDAN', 'Nike Dunk', 'NIKE'],
        'category': 'Design Legend'
    },
    {
        'id': 'rihanna',
        'name': 'Rihanna',
        'image': 'https://ui-avatars.com/api/?name=Rihanna&background=001f3f&color=c9a961&size=400&bold=true',
        'style_keywords': ['puma', 'jordan', 'nike', 'fenty', 'bold'],
        'brands': ['Nike Air Jordan', 'NIKE', 'AIR JORDAN'],
        'category': 'Fashion Mogul'
    }
]

async def match_celebrity_products(db, celebrity: dict, limit: int = 6) -> list:
    """Find products that match a celebrity's style"""
    import random as rnd
    
    # Build query for celebrity's preferred brands and keywords
    brand_queries = [{'brand': {'$regex': brand, '$options': 'i'}} for brand in celebrity['brands']]
    keyword_queries = []
    for keyword in celebrity['style_keywords']:
        keyword_queries.extend([
            {'name': {'$regex': keyword, '$options': 'i'}},
            {'tags': {'$regex': keyword, '$options': 'i'}}
        ])
    
    # Combine queries
    all_queries = brand_queries + keyword_queries
    if not all_queries:
        return []
    
    query = {'$or': all_queries}
    
    # Get matching products
    products = await db.products.find(query, {'_id': 0}).limit(50).to_list(50)
    
    # Shuffle and limit
    rnd.shuffle(products)
    selected = products[:limit]
    
    # Enrich with price data
    for product in selected:
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(10)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['highestPrice'] = max(p['currentPrice'] for p in prices)
        else:
            product['lowestPrice'] = product.get('price', 0)
            product['highestPrice'] = product.get('price', 0)
    
    return selected

@api_router.get('/celebrity/styles')
async def get_celebrity_styles():
    """Get celebrity style picks - products matching celebrity preferences"""
    import random as rnd
    
    celebrity_picks = []
    
    # Shuffle celebrities for variety
    shuffled_celebs = CELEBRITY_DATA.copy()
    rnd.shuffle(shuffled_celebs)
    
    for celeb in shuffled_celebs[:6]:  # Show 6 celebrities max
        products = await match_celebrity_products(db, celeb, limit=4)
        if products:  # Only include if products found
            celebrity_picks.append({
                'celebrity': {
                    'id': celeb['id'],
                    'name': celeb['name'],
                    'image': celeb['image'],
                    'category': celeb['category']
                },
                'products': products,
                'product_count': len(products)
            })
    
    return {
        'celebrity_picks': celebrity_picks,
        'total_celebrities': len(celebrity_picks),
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

@api_router.get('/trending')
async def get_trending_products(limit: int = Query(20, ge=1, le=50)):
    products = await db.products.find(
        {'isTrending': True},
        {'_id': 0}
    ).sort('createdAt', -1).limit(limit).to_list(limit)
    
    return {'products': products}

# ============ WATCHLIST ============
@api_router.post('/watchlist')
async def add_to_watchlist(
    product_id: str,
    target_price: Optional[float] = None,
    current_user: dict = Depends(get_current_user)
):
    watchlist_doc = {
        'id': f"watch_{datetime.now(timezone.utc).timestamp()}",
        'userId': current_user['id'],
        'productId': product_id,
        'targetPrice': target_price,
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    
    await db.watchlists.insert_one(watchlist_doc)
    return {'message': 'Added to watchlist'}

@api_router.get('/watchlist')
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    watchlists = await db.watchlists.find(
        {'userId': current_user['id']},
        {'_id': 0}
    ).to_list(1000)
    
    return {'watchlist': watchlists}

# ============ BRANDS ============
@api_router.get('/brands')
async def get_brands():
    import random as rnd
    brands = await db.brands.find(
        {'isActive': True},
        {'_id': 0}
    ).to_list(100)
    
    # Shuffle brands so all get equal visibility
    rnd.shuffle(brands)
    
    return {'brands': brands}

# ============ SUBSCRIPTIONS & PAYMENTS ============
import random
import string
import os

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
SANDBOX_MODE = RAZORPAY_KEY_ID.startswith('rzp_test')

# In-memory OTP store (use Redis in production)
otp_store: dict = {}

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

class CreateOrderRequest(BaseModel):
    phone: str
    name: str
    email: EmailStr
    address: str
    dob: str  # Date of Birth for birthday offers
    plan: str = "monthly"

class ConsentData(BaseModel):
    whatsapp_opt_in: bool = True
    timestamp: str = ""
    agreed_to_terms: bool = True

class VerifyPaymentRequest(BaseModel):
    phone: str
    order_id: str
    payment_id: str = ""
    signature: str = ""
    consent: Optional[ConsentData] = None

class OTPRequestWithCaptcha(BaseModel):
    phone: str
    turnstile_token: Optional[str] = None


@api_router.get('/plans')
async def list_plans():
    """Public catalog of subscription plans (for pricing UI)."""
    # Expose ordered list so frontend can render in tier order
    ordered = ['monthly', 'vip_monthly', 'vip_6mo', 'vip_yearly']
    return {
        'plans': [
            {
                'code': PLAN_CATALOG[c]['code'],
                'tier': PLAN_CATALOG[c]['tier'],
                'label': PLAN_CATALOG[c]['label'],
                'billing_period': PLAN_CATALOG[c]['billing_period'],
                'duration_days': PLAN_CATALOG[c]['duration_days'],
                'amount_paise': PLAN_CATALOG[c]['amount_paise'],
                'display_price': PLAN_CATALOG[c]['display_price'],
                'display_period': PLAN_CATALOG[c]['display_period'],
                'brand_limit': PLAN_CATALOG[c]['brand_limit'],
                'savings_pct': PLAN_CATALOG[c]['savings_pct'],
                'benefits': PLAN_CATALOG[c]['benefits'],
            }
            for c in ordered if c in PLAN_CATALOG
        ]
    }


@api_router.get('/subscribers/{phone}/status')
async def subscriber_status(phone: str):
    """Lightweight subscriber status lookup — used by the upgrade banner to decide
    whether to show 'Upgrade to VIP' for an existing regular subscriber.
    Returns only non-PII flags.
    """
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')
    sub = await db.subscribers.find_one(
        {'phone': phone},
        {'_id': 0, 'isPaid': 1, 'plan': 1, 'tier': 1, 'expiresAt': 1, 'membershipId': 1}
    )
    if not sub:
        return {'found': False}
    return {
        'found': True,
        'isPaid': sub.get('isPaid', False),
        'plan': sub.get('plan'),
        'tier': sub.get('tier') or ('vip' if sub.get('plan', '').startswith('vip_') else 'regular'),
        'expiresAt': sub.get('expiresAt'),
        'membershipId': sub.get('membershipId'),
    }


# ============ MEMBER ACCOUNT PAGE ============
# Same lightweight OTP auth as Subscribe flow — no JWT needed since the account
# page is low-stakes (preference management). Phone + verified OTP = session.

class AccountOTPVerify(BaseModel):
    phone: str
    otp: str


@api_router.post('/account/login')
@limiter.limit("10/hour")
async def account_login(request: Request, data: AccountOTPVerify):
    """Verify OTP for account page login. Returns subscriber snapshot. OTP
    must have been requested via /api/otp/send first."""
    phone = data.phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')
    stored = otp_store.get(phone)
    if not stored:
        raise HTTPException(status_code=400, detail='No OTP requested for this number')
    if stored.get('otp') != data.otp:
        raise HTTPException(status_code=400, detail='Invalid OTP')
    # OTP freshness check using created_at (default 10 min window)
    try:
        created = datetime.fromisoformat(stored.get('created_at', '').replace('Z', '+00:00'))
        if (datetime.now(timezone.utc) - created).total_seconds() > 600:
            raise HTTPException(status_code=400, detail='OTP expired — request a new one')
    except (ValueError, AttributeError):
        pass  # if created_at is missing / malformed, don't block login
    # Mark verified so other endpoints (like /preferences, /telegram/link-code)
    # accept this phone's requests
    stored['verified'] = True
    sub = await db.subscribers.find_one({'phone': phone}, {'_id': 0})
    if not sub:
        raise HTTPException(status_code=404, detail='No membership found for this phone. Subscribe first.')
    return {
        'ok': True,
        'subscriber': _serialize_subscriber(sub),
    }


@api_router.get('/account/{phone}')
async def account_get(phone: str):
    """Fetch full account snapshot for the account page. Requires prior OTP
    verification (phone must be in verified otp_store — same trust model as
    payment/preferences endpoints)."""
    phone = phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=401, detail='OTP verification required')
    sub = await db.subscribers.find_one({'phone': phone}, {'_id': 0})
    if not sub:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    return {'subscriber': _serialize_subscriber(sub)}


class UpdateChannelsRequest(BaseModel):
    phone: str
    channels: list[str]  # subset of ['email','whatsapp','telegram']


@api_router.post('/account/channels')
async def account_update_channels(data: UpdateChannelsRequest):
    """Update the subscriber's notification channels. Email is always kept on
    regardless of input (UI enforces this too — defense in depth)."""
    phone = data.phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=401, detail='OTP verification required')

    wanted = set(c.strip().lower() for c in (data.channels or []))
    wanted.add('email')  # email always on
    wanted &= {'email', 'whatsapp', 'telegram'}
    channel_str = ','.join(sorted(wanted)) if wanted != {'email'} else 'email'

    res = await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'notificationChannel': channel_str,
            'preferences.notification_channel': channel_str,
            'updatedAt': datetime.now(timezone.utc).isoformat(),
        }}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    return {'ok': True, 'notificationChannel': channel_str}


class PauseRequest(BaseModel):
    phone: str
    days: int  # 0 to resume, positive = pause for N days


@api_router.post('/account/pause')
async def account_pause(data: PauseRequest):
    """Pause alerts for a number of days (vacation mode). days=0 resumes."""
    phone = data.phone.strip()
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=401, detail='OTP verification required')
    if data.days < 0 or data.days > 365:
        raise HTTPException(status_code=400, detail='days must be 0-365')

    if data.days == 0:
        update = {'$unset': {'alertsPausedUntil': ''}, '$set': {'updatedAt': datetime.now(timezone.utc).isoformat()}}
    else:
        until = datetime.now(timezone.utc) + timedelta(days=data.days)
        update = {'$set': {
            'alertsPausedUntil': until.isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
        }}

    res = await db.subscribers.update_one({'phone': phone}, update)
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    return {'ok': True, 'paused_days': data.days}


class AccountPhoneRequest(BaseModel):
    phone: str


@api_router.post('/account/telegram-disconnect')
async def account_telegram_disconnect(payload: AccountPhoneRequest):
    """Remove the saved telegram_chat_id so future alerts skip Telegram."""
    phone = payload.phone.strip()
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=401, detail='OTP verification required')
    await db.subscribers.update_one(
        {'phone': phone},
        {'$unset': {'telegramChatId': '', 'telegramUsername': ''}}
    )
    return {'ok': True}


def _serialize_subscriber(sub: dict) -> dict:
    """Non-PII-safe projection for the account page — strips consent logs and
    internal fields."""
    prefs = sub.get('preferences') or {}
    return {
        'phone': sub.get('phone'),
        'name': sub.get('name'),
        'email': sub.get('email'),
        'membershipId': sub.get('membershipId'),
        'plan': sub.get('plan'),
        'tier': sub.get('tier') or ('vip' if (sub.get('plan') or '').startswith('vip_') else 'regular'),
        'expiresAt': sub.get('expiresAt'),
        'paidAt': sub.get('paidAt'),
        'isPaid': sub.get('isPaid', False),
        'notificationChannel': sub.get('notificationChannel', 'email'),
        'telegramLinked': bool(sub.get('telegramChatId')),
        'telegramUsername': sub.get('telegramUsername'),
        'alertsPausedUntil': sub.get('alertsPausedUntil'),
        'preferences': {
            'brands': prefs.get('brands', []),
            'alert_types': prefs.get('alert_types', []),
            'gender': prefs.get('gender', 'all'),
            'categories': prefs.get('categories', []),
            'sizes': prefs.get('sizes', []),
            'price_range': prefs.get('price_range', {}),
            'keywords': prefs.get('keywords', []),
            'drop_threshold': prefs.get('drop_threshold', 10),
            'alert_frequency': prefs.get('alert_frequency', 'instant'),
        },
    }


@api_router.post('/otp/send')
@limiter.limit("5/15minutes")
async def send_otp_endpoint(request: Request, data: OTPRequestWithCaptcha):
    """Send OTP via WhatsApp using Meta Cloud API"""
    from whatsapp import send_otp as whatsapp_send_otp, IS_CONFIGURED
    from security_advanced import verify_turnstile_token
    from security import get_client_ip
    
    # Verify Turnstile CAPTCHA first
    if data.turnstile_token:
        ip = get_client_ip(request)
        await verify_turnstile_token(data.turnstile_token, ip)
    
    phone = data.phone.strip()
    if len(phone) != 10 or phone[0] not in '6789':
        raise HTTPException(status_code=400, detail='Invalid Indian mobile number')

    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[phone] = {
        'otp': otp,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'verified': False,
    }

    # Send OTP via Meta WhatsApp Cloud API
    success, result = whatsapp_send_otp(phone, otp)
    
    if success:
        logger.info(f"OTP sent to {phone} via WhatsApp. Message ID: {result}")
    else:
        logger.warning(f"WhatsApp send failed: {result}. OTP for {phone}: {otp}")

    # Return OTP in sandbox mode or if WhatsApp fails (for testing)
    return {
        'message': 'OTP sent to WhatsApp',
        'sandbox_otp': otp if (SANDBOX_MODE or not success) else None,
        'sent_via': 'whatsapp' if success else 'sandbox',
    }

@api_router.post('/otp/verify')
async def verify_otp(data: OTPVerify):
    """Verify OTP"""
    phone = data.phone.strip()
    stored = otp_store.get(phone)

    if not stored:
        raise HTTPException(status_code=400, detail='OTP expired. Request a new one.')
    if stored['otp'] != data.otp:
        raise HTTPException(status_code=400, detail='Invalid OTP')

    otp_store[phone]['verified'] = True

    # Create or get subscriber
    existing = await db.subscribers.find_one({'phone': phone})
    if not existing:
        await db.subscribers.insert_one({
            'id': f"sub_{int(datetime.now(timezone.utc).timestamp())}",
            'phone': phone,
            'isActive': False,
            'isPaid': False,
            'createdAt': datetime.now(timezone.utc).isoformat(),
        })

    return {'message': 'OTP verified', 'verified': True}

@api_router.post('/payment/create-order')
@limiter.limit("3/hour")
async def create_payment_order(request: Request, data: CreateOrderRequest):
    """Create a Razorpay order for subscription"""
    # Validate phone number
    phone = data.phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number. Must be 10 digits starting with 6-9.')
    
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=400, detail='Phone not verified. Complete OTP first.')

    plan = get_plan(data.plan)
    amount = plan['amount_paise']

    if SANDBOX_MODE:
        # Sandbox: simulate order
        order_id = f"order_sandbox_{int(datetime.now(timezone.utc).timestamp())}"
        order_data = {
            'id': order_id,
            'amount': amount,
            'currency': 'INR',
            'status': 'created',
        }
    else:
        import razorpay
        rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order_data = rz_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {'phone': phone, 'plan': plan['code']},
        })

    # Store order
    await db.orders.insert_one({
        'orderId': order_data['id'],
        'phone': phone,
        'name': data.name,
        'email': data.email,
        'address': data.address,
        'dob': data.dob,
        'amount': amount,
        'status': 'created',
        'plan': plan['code'],
        'tier': plan['tier'],
        'createdAt': datetime.now(timezone.utc).isoformat(),
    })

    return {
        'order_id': order_data['id'],
        'amount': amount,
        'currency': 'INR',
        'key_id': RAZORPAY_KEY_ID,
        'sandbox': SANDBOX_MODE,
        'plan': {
            'code': plan['code'],
            'label': plan['label'],
            'tier': plan['tier'],
            'display_price': plan['display_price'],
            'display_period': plan['display_period'],
        },
    }

@api_router.post('/payment/verify')
async def verify_payment(data: VerifyPaymentRequest, request: Request):
    """Verify payment and activate membership"""
    from whatsapp import send_welcome_message, IS_CONFIGURED as WHATSAPP_CONFIGURED
    
    phone = data.phone.strip()

    # Find the order
    order = await db.orders.find_one({'orderId': data.order_id, 'phone': phone})
    if not order:
        raise HTTPException(status_code=400, detail='Order not found')

    if SANDBOX_MODE:
        # Auto-approve in sandbox
        is_valid = True
    else:
        import razorpay
        import hmac
        import hashlib
        rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        try:
            rz_client.utility.verify_payment_signature({
                'razorpay_order_id': data.order_id,
                'razorpay_payment_id': data.payment_id,
                'razorpay_signature': data.signature,
            })
            is_valid = True
        except Exception:
            is_valid = False

    if not is_valid:
        raise HTTPException(status_code=400, detail='Payment verification failed')

    # Activate membership — duration and tier derived from plan catalog
    now = datetime.now(timezone.utc)
    plan = get_plan(order.get('plan', 'monthly'))

    # If subscriber already has an active subscription, stack the new duration on top
    # (handles upgrades and renewals — remaining time is preserved, not lost)
    existing_sub = await db.subscribers.find_one({'phone': phone}, {'_id': 0, 'expiresAt': 1, 'isPaid': 1})
    base_time = now
    if existing_sub and existing_sub.get('isPaid') and existing_sub.get('expiresAt'):
        try:
            current_expiry = datetime.fromisoformat(existing_sub['expiresAt'].replace('Z', '+00:00'))
            if current_expiry > now:
                base_time = current_expiry
        except Exception:
            pass
    expires = base_time + timedelta(days=plan['duration_days'])
    membership_id = f"DC-{now.strftime('%Y%m')}-{random.randint(10000, 99999)}"

    await db.orders.update_one(
        {'orderId': data.order_id},
        {'$set': {'status': 'paid', 'paymentId': data.payment_id, 'paidAt': now.isoformat()}}
    )

    # Get client IP for consent logging
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('x-forwarded-for', '')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()

    # Build consent log for Meta compliance
    consent_log = None
    if data.consent:
        consent_log = {
            'whatsapp_opt_in': data.consent.whatsapp_opt_in,
            'timestamp': data.consent.timestamp or now.isoformat(),
            'ip_address': client_ip,
            'agreed_to_terms': data.consent.agreed_to_terms,
            'user_agent': request.headers.get('user-agent', 'unknown'),
        }

    await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'name': order.get('name', ''),
            'email': order.get('email', ''),
            'address': order.get('address', ''),
            'dob': order.get('dob', ''),
            'isActive': True,
            'isPaid': True,
            'membershipId': membership_id,
            'plan': plan['code'],
            'tier': plan['tier'],
            'brandLimit': plan['brand_limit'],
            'paidAt': now.isoformat(),
            'expiresAt': expires.isoformat(),
            'updatedAt': now.isoformat(),
            # Meta compliance: consent log
            'consent': consent_log,
        }},
        upsert=True,
    )

    # Send Welcome Message via WhatsApp (Meta compliance: proof of opt-in)
    user_name = order.get('name', '').split()[0] if order.get('name') else 'there'
    welcome_sent = False
    if WHATSAPP_CONFIGURED or SANDBOX_MODE:
        try:
            success, _ = send_welcome_message(
                phone=phone,
                name=user_name,
                membership_id=membership_id
            )
            welcome_sent = success
            logger.info(f"[Welcome] Sent to {phone}: {success}")
        except Exception as e:
            logger.error(f"[Welcome] Failed for {phone}: {e}")

    return {
        'success': True,
        'membership_id': membership_id,
        'expires_at': expires.isoformat(),
        'name': order.get('name', ''),
        'message': 'Welcome to Drops Curated!',
        'welcome_message_sent': welcome_sent,
    }

@api_router.get('/membership/{phone}')
async def get_membership(phone: str):
    """Get membership details"""
    sub = await db.subscribers.find_one({'phone': phone, 'isPaid': True}, {'_id': 0})
    if not sub:
        raise HTTPException(status_code=404, detail='No active membership found')
    return {
        'membership_id': sub.get('membershipId', ''),
        'name': sub.get('name', ''),
        'email': sub.get('email', ''),
        'address': sub.get('address', ''),
        'dob': sub.get('dob', ''),
        'phone': sub.get('phone', ''),
        'plan': sub.get('plan', 'monthly'),
        'expires_at': sub.get('expiresAt', ''),
        'is_active': sub.get('isActive', False),
    }

@api_router.get('/subscribers/count')
async def subscriber_count():
    count = await db.subscribers.count_documents({'isActive': True})
    return {'count': count}

# ============ USER PREFERENCES ============
class PriceRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None

class UpdatePreferences(BaseModel):
    phone: str
    # Brand selection
    brands: list[str] = []  # Empty = all brands
    brand_limit: int = 10  # 5, 10, or 0 (unlimited)
    # Trigger types
    alert_types: list[str] = ["price_drop", "new_release"]  # price_drop, new_release, restock
    # Specificity filters
    categories: list[str] = []  # Empty = all categories (garments, sneakers, accessories)
    sizes: list[str] = []  # Empty = all sizes
    # Budget filter
    price_range: Optional[PriceRange] = None
    # Keyword matching
    keywords: list[str] = []  # Empty = match all products
    # Price drop threshold (only alert if discount >= threshold)
    drop_threshold: int = 10  # Default 10%
    # Notification frequency
    alert_frequency: str = "daily"  # instant or daily (daily = digest at 8 PM)
    # Gender preference
    gender: str = "all"  # all, men, women, unisex
    # Notification channel: where alerts are delivered
    # 'email' (default — rich HTML, no chat interruption),
    # 'whatsapp' (instant but can interrupt), 'both'.
    notification_channel: str = "email"
    # Optional Telegram username for when channel includes telegram later
    telegram_username: Optional[str] = None

@api_router.post('/preferences')
async def update_preferences(data: UpdatePreferences):
    phone = data.phone.strip()
    
    # Build the complete preferences object
    preferences = {
        # Brand selection
        'brands': data.brands,
        'brand_limit': data.brand_limit,
        # Trigger types
        'alert_types': data.alert_types,
        # Specificity
        'gender': data.gender,
        'categories': data.categories,
        'sizes': data.sizes,
        # Budget range
        'price_range': {
            'min': data.price_range.min if data.price_range else None,
            'max': data.price_range.max if data.price_range else None,
        },
        # Keyword matching
        'keywords': data.keywords,
        # Price drop threshold
        'drop_threshold': data.drop_threshold,
        # Notification frequency
        'alert_frequency': data.alert_frequency,
        # Notification channel
        'notification_channel': data.notification_channel,
        'telegram_username': data.telegram_username,
    }
    
    # Mirror channel at top level of subscriber doc too — so the alert pipeline
    # can read it with a single projection (it lives on both for backward compat).
    result = await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'preferences': preferences,
            'notificationChannel': data.notification_channel,
            'updatedAt': datetime.now(timezone.utc).isoformat(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    logger.info(f"[Preferences] Updated for {phone}: {len(data.brands)} brands, {data.alert_types}, {data.alert_frequency}, via={data.notification_channel}")
    return {'message': 'Preferences updated', 'preferences': preferences}

@api_router.get('/preferences/{phone}')
async def get_preferences(phone: str):
    sub = await db.subscribers.find_one({'phone': phone}, {'_id': 0, 'preferences': 1, 'phone': 1})
    if not sub:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    # Return full preference funnel with defaults
    default_prefs = {
        'brands': [],
        'brand_limit': 10,
        'alert_types': ['price_drop', 'new_release'],
        'gender': 'all',
        'categories': [],
        'sizes': [],
        'price_range': {'min': None, 'max': None},
        'keywords': [],
        'drop_threshold': 10,
        'alert_frequency': 'daily',
    }
    prefs = {**default_prefs, **sub.get('preferences', {})}
    return {'phone': phone, 'preferences': prefs}


class SimulatePreferencesRequest(BaseModel):
    """Request model for preference simulation"""
    brands: list[str] = []
    brand_limit: int = 10
    alert_types: list[str] = ["price_drop", "new_release"]
    gender: str = "all"  # all, men, women, unisex
    categories: list[str] = []
    sizes: list[str] = []
    price_range: Optional[PriceRange] = None
    keywords: list[str] = []
    drop_threshold: int = 10


@api_router.post('/preferences/simulate')
async def simulate_preferences(data: SimulatePreferencesRequest):
    """
    Test My Preferences - Simulate what alerts user would receive
    based on their current preference funnel settings.
    Returns sample products matching the criteria.
    """
    import random as rnd
    
    # Build query based on preferences
    query = {'isActive': True}
    
    # Brand filter
    if data.brands:
        query['store'] = {'$in': data.brands}
    
    # Gender filter
    if data.gender and data.gender != 'all':
        # Map gender to common product tags/attributes
        gender_keywords = {
            'men': ['men', 'male', "men's", 'mens', 'man'],
            'women': ['women', 'female', "women's", 'womens', 'woman', 'ladies'],
            'unisex': ['unisex', 'gender neutral', 'all gender'],
        }
        keywords = gender_keywords.get(data.gender, [])
        if keywords:
            query['$or'] = [
                {'tags': {'$regex': '|'.join(keywords), '$options': 'i'}},
                {'name': {'$regex': '|'.join(keywords), '$options': 'i'}},
                {'attributes.gender': {'$regex': '|'.join(keywords), '$options': 'i'}},
            ]
    
    # Category filter (map frontend categories to DB categories)
    category_map = {
        'garments': 'CLOTHES',
        'sneakers': 'SHOES',
        'accessories': 'ACCESSORIES',
    }
    if data.categories:
        db_categories = [category_map.get(c, c.upper()) for c in data.categories]
        query['category'] = {'$in': db_categories}
    
    # Price range filter
    if data.price_range:
        price_query = {}
        if data.price_range.min is not None:
            price_query['$gte'] = data.price_range.min
        if data.price_range.max is not None:
            price_query['$lte'] = data.price_range.max
        if price_query:
            query['price'] = price_query
    
    # Keyword filter
    if data.keywords:
        keyword_patterns = [{'name': {'$regex': kw, '$options': 'i'}} for kw in data.keywords]
        keyword_patterns.extend([{'tags': {'$regex': kw, '$options': 'i'}} for kw in data.keywords])
        query['$or'] = keyword_patterns
    
    # Get matching products
    all_products = await db.products.find(query, {'_id': 0}).limit(500).to_list(500)
    
    # Filter by sizes if specified
    if data.sizes:
        size_filtered = []
        for product in all_products:
            product_sizes = product.get('attributes', {}).get('sizes', [])
            if not product_sizes:  # No size info = include it
                size_filtered.append(product)
            elif any(s.upper() in [ps.upper() for ps in product_sizes] for s in data.sizes):
                size_filtered.append(product)
        all_products = size_filtered
    
    # Simulate different alert types
    new_drops_sample = []
    price_drops_sample = []
    # restocks_sample would require historical out-of-stock data
    
    # Enrich with price data and categorize
    for product in all_products[:100]:  # Process max 100
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(10)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['originalPrice'] = prices[0].get('originalPrice', product['lowestPrice'])
            
            # Check for price drop
            if product['originalPrice'] > product['lowestPrice']:
                drop_pct = ((product['originalPrice'] - product['lowestPrice']) / product['originalPrice']) * 100
                if drop_pct >= data.drop_threshold:
                    product['dropPercent'] = round(drop_pct, 1)
                    price_drops_sample.append(product)
        else:
            product['lowestPrice'] = product.get('price', 0)
            product['originalPrice'] = product.get('price', 0)
        
        # New drops (products created in last 7 days)
        created = product.get('createdAt', '')
        if created:
            try:
                created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) - created_date < timedelta(days=7):
                    new_drops_sample.append(product)
            except Exception:
                pass
    
    # Shuffle and limit samples
    rnd.shuffle(new_drops_sample)
    rnd.shuffle(price_drops_sample)
    
    # Build simulation results
    results = {
        'total_matching_products': len(all_products),
        'new_drops': {
            'count': len(new_drops_sample),
            'sample': new_drops_sample[:3] if 'new_release' in data.alert_types else [],
            'enabled': 'new_release' in data.alert_types,
        },
        'price_drops': {
            'count': len(price_drops_sample),
            'sample': price_drops_sample[:3] if 'price_drop' in data.alert_types else [],
            'enabled': 'price_drop' in data.alert_types,
            'threshold': data.drop_threshold,
        },
        'restocks': {
            'count': 0,  # Can't simulate restocks without historical data
            'sample': [],
            'enabled': 'restock' in data.alert_types,
            'note': 'Restock alerts trigger when sold-out items return to stock',
        },
        'filters_applied': {
            'brands': len(data.brands) if data.brands else 'All brands',
            'gender': data.gender.capitalize() if data.gender != 'all' else 'All collections',
            'categories': data.categories if data.categories else 'All categories',
            'sizes': data.sizes if data.sizes else 'All sizes',
            'price_range': f"₹{data.price_range.min or 0} - ₹{data.price_range.max or '∞'}" if data.price_range and (data.price_range.min or data.price_range.max) else 'No limit',
            'keywords': data.keywords if data.keywords else 'None',
        },
        'estimated_daily_alerts': _estimate_daily_alerts(
            len(all_products),
            len(data.brands) if data.brands else 23,
            data.alert_types,
            data.gender,
            data.categories,
            data.sizes,
        ),
        'sample_daily_digest': _generate_sample_digest(
            new_drops_sample[:3] if 'new_release' in data.alert_types else [],
            price_drops_sample[:3] if 'price_drop' in data.alert_types else [],
        ),
    }
    
    return results


def _estimate_daily_alerts(total_products: int, brand_count: int, alert_types: list, gender: str, categories: list, sizes: list) -> dict:
    """Estimate how many alerts user might receive per day"""
    # Base estimate: ~2-5% of products have activity per day
    base_activity_rate = 0.03
    
    # Adjust by filters
    gender_factor = 0.4 if gender != 'all' else 1.0  # Gender filter reduces by ~60%
    category_factor = 0.33 if categories else 1.0  # Each category ~1/3 of products
    size_factor = 0.15 if sizes else 1.0  # Each size ~15% of products
    brand_factor = brand_count / 23  # Proportion of brands followed
    
    estimated_activity = total_products * base_activity_rate * gender_factor * category_factor * size_factor * brand_factor
    
    # Split by alert types
    new_drops_estimate = estimated_activity * 0.6 if 'new_release' in alert_types else 0
    price_drops_estimate = estimated_activity * 0.3 if 'price_drop' in alert_types else 0
    restocks_estimate = estimated_activity * 0.1 if 'restock' in alert_types else 0
    
    total = round(new_drops_estimate + price_drops_estimate + restocks_estimate, 1)
    
    return {
        'total': max(1, total),
        'breakdown': {
            'new_drops': round(new_drops_estimate, 1),
            'price_drops': round(price_drops_estimate, 1),
            'restocks': round(restocks_estimate, 1),
        },
        'frequency_impact': 'Low' if total < 3 else 'Medium' if total < 10 else 'High',
    }


def _generate_sample_digest(new_drops: list, price_drops: list) -> str:
    """Generate a sample daily digest message"""
    message = "🌙 *Your Daily Drops Digest*\n\n"
    message += "_Sample Preview_\n\n"
    
    if new_drops:
        message += f"🆕 *{len(new_drops)} New Arrivals*\n"
        for prod in new_drops[:2]:
            name = prod.get('name', 'Product')[:35]
            price = prod.get('lowestPrice', 0)
            message += f"  • {name}... - ₹{price:,.0f}\n"
        message += "\n"
    
    if price_drops:
        message += f"💰 *{len(price_drops)} Price Drops*\n"
        for prod in price_drops[:2]:
            name = prod.get('name', 'Product')[:35]
            new_price = prod.get('lowestPrice', 0)
            drop_pct = prod.get('dropPercent', 0)
            message += f"  • {name}... - ₹{new_price:,.0f} ({drop_pct}% off)\n"
        message += "\n"
    
    if not new_drops and not price_drops:
        message += "_No matching products found with current filters._\n"
        message += "Try adjusting your preferences for more results.\n"
    
    message += "\n👉 Browse all drops on Drops Curated!"
    
    return message


# ============ WALLET PASS GENERATION ============
import json
import hashlib
import zipfile
import io

# Apple Wallet Configuration (requires Apple Developer certificates)
APPLE_PASS_TYPE_ID = os.getenv('APPLE_PASS_TYPE_ID', '')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID', '')
APPLE_CERT_PATH = os.getenv('APPLE_CERT_PATH', '')
APPLE_KEY_PATH = os.getenv('APPLE_KEY_PATH', '')
APPLE_WWDR_PATH = os.getenv('APPLE_WWDR_PATH', '')

# Google Wallet Configuration
GOOGLE_WALLET_ISSUER_ID = os.getenv('GOOGLE_WALLET_ISSUER_ID', '')
GOOGLE_WALLET_SERVICE_ACCOUNT = os.getenv('GOOGLE_WALLET_SERVICE_ACCOUNT_JSON', '')

class WalletPassRequest(BaseModel):
    phone: str
    name: str
    membership_id: str
    expires_at: str

@api_router.post('/wallet/apple')
async def generate_apple_wallet_pass(data: WalletPassRequest):
    """Generate Apple Wallet .pkpass file for membership card"""
    
    # Check if Apple Wallet is configured
    if not APPLE_PASS_TYPE_ID or not APPLE_TEAM_ID:
        # Return helpful message about configuration
        return {
            'configured': False,
            'message': 'Apple Wallet integration requires Apple Developer certificates. Contact support to enable this feature.',
            'requirements': [
                'Apple Developer Account ($99/year)',
                'Pass Type ID certificate',
                'WWDR certificate'
            ]
        }
    
    try:
        # Generate pass.json structure
        pass_data = {
            "formatVersion": 1,
            "passTypeIdentifier": APPLE_PASS_TYPE_ID,
            "serialNumber": data.membership_id,
            "teamIdentifier": APPLE_TEAM_ID,
            "organizationName": "Drops Curated",
            "description": "VIP Membership Card",
            "logoText": "Drops Curated",
            "foregroundColor": "rgb(212, 175, 55)",
            "backgroundColor": "rgb(0, 31, 63)",
            "labelColor": "rgb(255, 255, 255)",
            "storeCard": {
                "headerFields": [
                    {
                        "key": "member",
                        "label": "MEMBER",
                        "value": data.name
                    }
                ],
                "primaryFields": [
                    {
                        "key": "membership",
                        "label": "VIP MEMBERSHIP",
                        "value": "Active"
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "id",
                        "label": "MEMBER ID",
                        "value": data.membership_id
                    },
                    {
                        "key": "phone",
                        "label": "PHONE",
                        "value": f"+91 {data.phone}"
                    }
                ],
                "auxiliaryFields": [
                    {
                        "key": "expires",
                        "label": "VALID UNTIL",
                        "value": data.expires_at[:10]
                    }
                ],
                "backFields": [
                    {
                        "key": "terms",
                        "label": "MEMBERSHIP BENEFITS",
                        "value": "• Instant WhatsApp alerts (<10 seconds)\\n• Price drop notifications\\n• New collection drops\\n• Access to all 14 premium Indian streetwear brands\\n\\nSupport: hello@dropscurated.com"
                    }
                ]
            },
            "barcode": {
                "message": data.membership_id,
                "format": "PKBarcodeFormatQR",
                "messageEncoding": "iso-8859-1"
            }
        }
        
        # In production with certificates, generate actual .pkpass file
        # For now, store pass data and return placeholder
        await db.wallet_passes.update_one(
            {'membership_id': data.membership_id, 'type': 'apple'},
            {'$set': {
                'pass_data': pass_data,
                'phone': data.phone,
                'name': data.name,
                'createdAt': datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        return {
            'configured': False,
            'message': 'Apple Wallet pass data saved! Full .pkpass generation requires Apple Developer certificates.',
            'pass_preview': {
                'member': data.name,
                'id': data.membership_id,
                'expires': data.expires_at[:10]
            }
        }
        
    except Exception as e:
        logging.error(f"Apple Wallet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post('/wallet/google')
async def generate_google_wallet_pass(data: WalletPassRequest):
    """Generate Google Wallet pass for membership card"""
    
    # Check if Google Wallet is configured
    if not GOOGLE_WALLET_ISSUER_ID:
        return {
            'configured': False,
            'message': 'Google Wallet integration requires Google Cloud setup. Contact support to enable this feature.',
            'requirements': [
                'Google Cloud Account',
                'Google Wallet API enabled',
                'Service Account with Wallet permissions'
            ]
        }
    
    try:
        # Google Wallet pass object structure
        pass_object = {
            "id": f"{GOOGLE_WALLET_ISSUER_ID}.{data.membership_id}",
            "classId": f"{GOOGLE_WALLET_ISSUER_ID}.drops_curated_vip",
            "state": "ACTIVE",
            "heroImage": {
                "sourceUri": {
                    "uri": "https://dropscurated.com/card-hero.png"
                }
            },
            "textModulesData": [
                {
                    "header": "Member Name",
                    "body": data.name
                },
                {
                    "header": "Phone",
                    "body": f"+91 {data.phone}"
                }
            ],
            "linksModuleData": {
                "uris": [
                    {
                        "uri": "https://dropscurated.com",
                        "description": "Visit Drops Curated"
                    }
                ]
            },
            "barcode": {
                "type": "QR_CODE",
                "value": data.membership_id,
                "alternateText": data.membership_id
            },
            "validTimeInterval": {
                "end": {
                    "date": data.expires_at
                }
            }
        }
        
        # Store pass data
        await db.wallet_passes.update_one(
            {'membership_id': data.membership_id, 'type': 'google'},
            {'$set': {
                'pass_object': pass_object,
                'phone': data.phone,
                'name': data.name,
                'createdAt': datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        return {
            'configured': False,
            'message': 'Google Wallet pass data saved! Full integration requires Google Cloud credentials.',
            'pass_preview': {
                'member': data.name,
                'id': data.membership_id,
                'expires': data.expires_at[:10]
            }
        }
        
    except Exception as e:
        logging.error(f"Google Wallet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ RAFFLE & ENTRY MANAGEMENT SYSTEM ============
import secrets
from collections import defaultdict

# Rate limiting for bot protection
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5  # max entries per minute per IP

class RaffleStatus(str, Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSED = "closed"
    DRAWING = "drawing"
    COMPLETED = "completed"

class CreateRaffleRequest(BaseModel):
    product_id: str
    product_name: str
    product_image: str
    brand: str
    retail_price: float
    total_pairs: int
    entry_start: str  # ISO datetime
    entry_end: str    # ISO datetime
    draw_time: str    # ISO datetime
    sizes_available: list[str]
    entry_requirements: list[str] = ["VIP membership required"]

class RaffleEntryRequest(BaseModel):
    raffle_id: str
    phone: str
    name: str
    selected_size: str
    shipping_address: Optional[str] = None
    captcha_token: Optional[str] = None  # For bot protection

class DrawWinnersRequest(BaseModel):
    raffle_id: str
    admin_key: str = ""

def check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded rate limit"""
    current_time = time.time()
    # Clean old entries
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if current_time - t < RATE_LIMIT_WINDOW]
    
    if len(rate_limit_store[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    rate_limit_store[ip].append(current_time)
    return True

def generate_entry_id() -> str:
    """Generate secure random entry ID"""
    return f"ENTRY-{secrets.token_hex(8).upper()}"

def generate_fingerprint(request: Request, phone: str) -> str:
    """Generate device fingerprint for bot detection"""
    user_agent = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    ip = request.client.host if request.client else "unknown"
    
    fingerprint_data = f"{ip}:{user_agent}:{accept_lang}:{phone}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

@api_router.post('/raffles/create')
async def create_raffle(data: CreateRaffleRequest):
    """Create a new raffle for a limited drop (Admin only)"""
    raffle_id = f"RAFFLE-{secrets.token_hex(6).upper()}"
    
    raffle = {
        'id': raffle_id,
        'product_id': data.product_id,
        'product_name': data.product_name,
        'product_image': data.product_image,
        'brand': data.brand,
        'retail_price': data.retail_price,
        'total_pairs': data.total_pairs,
        'sizes_available': data.sizes_available,
        'entry_start': data.entry_start,
        'entry_end': data.entry_end,
        'draw_time': data.draw_time,
        'entry_requirements': data.entry_requirements,
        'status': RaffleStatus.UPCOMING,
        'total_entries': 0,
        'winners': [],
        'createdAt': datetime.now(timezone.utc).isoformat(),
    }
    
    await db.raffles.insert_one(raffle)
    
    return {'success': True, 'raffle_id': raffle_id, 'message': 'Raffle created successfully'}

@api_router.get('/raffles')
async def get_raffles(status: Optional[str] = None):
    """Get all raffles, optionally filtered by status"""
    query = {}
    if status:
        query['status'] = status
    
    raffles = await db.raffles.find(query, {'_id': 0}).sort('entry_start', -1).to_list(50)
    
    # Update status based on current time
    now = datetime.now(timezone.utc)
    for raffle in raffles:
        entry_start = datetime.fromisoformat(raffle['entry_start'].replace('Z', '+00:00'))
        entry_end = datetime.fromisoformat(raffle['entry_end'].replace('Z', '+00:00'))
        
        if raffle['status'] == RaffleStatus.UPCOMING and now >= entry_start:
            raffle['status'] = RaffleStatus.OPEN
        elif raffle['status'] == RaffleStatus.OPEN and now >= entry_end:
            raffle['status'] = RaffleStatus.CLOSED
    
    return {'raffles': raffles}

@api_router.get('/raffles/{raffle_id}')
async def get_raffle(raffle_id: str):
    """Get raffle details with entry count"""
    raffle = await db.raffles.find_one({'id': raffle_id}, {'_id': 0})
    if not raffle:
        raise HTTPException(status_code=404, detail='Raffle not found')
    
    # Get entry count by size
    pipeline = [
        {'$match': {'raffle_id': raffle_id}},
        {'$group': {'_id': '$selected_size', 'count': {'$sum': 1}}}
    ]
    size_entries = await db.raffle_entries.aggregate(pipeline).to_list(100)
    raffle['entries_by_size'] = {item['_id']: item['count'] for item in size_entries}
    
    return {'raffle': raffle}

@api_router.post('/raffles/enter')
async def enter_raffle(data: RaffleEntryRequest, request: Request):
    """Enter a raffle with bot protection"""
    
    # Rate limiting check
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail='Too many requests. Please wait before trying again.')
    
    # Get raffle
    raffle = await db.raffles.find_one({'id': data.raffle_id})
    if not raffle:
        raise HTTPException(status_code=404, detail='Raffle not found')
    
    # Check raffle status
    now = datetime.now(timezone.utc)
    entry_start = datetime.fromisoformat(raffle['entry_start'].replace('Z', '+00:00'))
    entry_end = datetime.fromisoformat(raffle['entry_end'].replace('Z', '+00:00'))
    
    if now < entry_start:
        raise HTTPException(status_code=400, detail='Raffle has not started yet')
    if now > entry_end:
        raise HTTPException(status_code=400, detail='Raffle entry period has ended')
    
    # Check if size is available
    if data.selected_size not in raffle['sizes_available']:
        raise HTTPException(status_code=400, detail='Selected size is not available')
    
    # Verify user is a VIP subscriber
    subscriber = await db.subscribers.find_one({'phone': data.phone, 'isActive': True})
    if not subscriber:
        raise HTTPException(status_code=403, detail='VIP membership required to enter raffles')
    
    # Generate device fingerprint for bot detection
    fingerprint = generate_fingerprint(request, data.phone)
    
    # Check for duplicate entry (same phone + same raffle)
    existing_entry = await db.raffle_entries.find_one({
        'raffle_id': data.raffle_id,
        'phone': data.phone
    })
    if existing_entry:
        raise HTTPException(status_code=400, detail='You have already entered this raffle')
    
    # Check for suspicious activity (same fingerprint, different phones)
    fingerprint_entries = await db.raffle_entries.count_documents({
        'raffle_id': data.raffle_id,
        'fingerprint': fingerprint
    })
    if fingerprint_entries >= 2:
        raise HTTPException(status_code=403, detail='Suspicious activity detected. Entry blocked.')
    
    # Create entry
    entry_id = generate_entry_id()
    entry = {
        'id': entry_id,
        'raffle_id': data.raffle_id,
        'phone': data.phone,
        'name': data.name,
        'selected_size': data.selected_size,
        'shipping_address': data.shipping_address,
        'fingerprint': fingerprint,
        'ip_address': client_ip,
        'user_agent': request.headers.get("user-agent", ""),
        'status': 'entered',  # entered, winner, not_selected
        'entered_at': datetime.now(timezone.utc).isoformat(),
    }
    
    await db.raffle_entries.insert_one(entry)
    
    # Update raffle entry count
    await db.raffles.update_one(
        {'id': data.raffle_id},
        {'$inc': {'total_entries': 1}}
    )
    
    return {
        'success': True,
        'entry_id': entry_id,
        'message': f'You have been entered into the raffle for {raffle["product_name"]}',
        'selected_size': data.selected_size,
        'draw_time': raffle['draw_time'],
        'total_entries': raffle['total_entries'] + 1
    }

@api_router.get('/raffles/my-entries/{phone}')
async def get_my_entries(phone: str):
    """Get all raffle entries for a user"""
    entries = await db.raffle_entries.find(
        {'phone': phone},
        {'_id': 0, 'fingerprint': 0, 'ip_address': 0, 'user_agent': 0}
    ).sort('entered_at', -1).to_list(50)
    
    # Enrich with raffle details
    for entry in entries:
        raffle = await db.raffles.find_one({'id': entry['raffle_id']}, {'_id': 0})
        if raffle:
            entry['raffle'] = {
                'product_name': raffle['product_name'],
                'product_image': raffle['product_image'],
                'brand': raffle['brand'],
                'draw_time': raffle['draw_time'],
                'status': raffle['status'],
                'total_entries': raffle['total_entries']
            }
    
    return {'entries': entries}

@api_router.post('/raffles/draw')
async def draw_winners(data: DrawWinnersRequest):
    """Draw random winners for a raffle (Admin only)"""
    
    raffle = await db.raffles.find_one({'id': data.raffle_id})
    if not raffle:
        raise HTTPException(status_code=404, detail='Raffle not found')
    
    if raffle['status'] == RaffleStatus.COMPLETED:
        raise HTTPException(status_code=400, detail='Winners have already been drawn')
    
    # Update status to drawing
    await db.raffles.update_one(
        {'id': data.raffle_id},
        {'$set': {'status': RaffleStatus.DRAWING}}
    )
    
    # Get all entries grouped by size
    entries = await db.raffle_entries.find({'raffle_id': data.raffle_id}).to_list(10000)
    
    if not entries:
        raise HTTPException(status_code=400, detail='No entries to draw from')
    
    # Group entries by size
    entries_by_size = defaultdict(list)
    for entry in entries:
        entries_by_size[entry['selected_size']].append(entry)
    
    # Calculate pairs per size (distribute evenly for simplicity)
    total_pairs = raffle['total_pairs']
    sizes = raffle['sizes_available']
    pairs_per_size = max(1, total_pairs // len(sizes))
    
    winners = []
    
    # Secure random selection using secrets module
    for size, size_entries in entries_by_size.items():
        # Shuffle using secure random
        shuffled = size_entries.copy()
        for i in range(len(shuffled) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        
        # Select winners for this size
        size_winners = shuffled[:pairs_per_size]
        
        for winner in size_winners:
            winners.append({
                'entry_id': winner['id'],
                'phone': winner['phone'],
                'name': winner['name'],
                'size': size,
            })
            
            # Update entry status
            await db.raffle_entries.update_one(
                {'id': winner['id']},
                {'$set': {'status': 'winner', 'won_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # Mark non-winners
    winner_ids = [w['entry_id'] for w in winners]
    await db.raffle_entries.update_many(
        {'raffle_id': data.raffle_id, 'id': {'$nin': winner_ids}},
        {'$set': {'status': 'not_selected'}}
    )
    
    # Update raffle with winners
    await db.raffles.update_one(
        {'id': data.raffle_id},
        {'$set': {
            'status': RaffleStatus.COMPLETED,
            'winners': winners,
            'drawn_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        'success': True,
        'total_entries': len(entries),
        'winners_selected': len(winners),
        'winners': winners,
        'message': f'Drew {len(winners)} winners from {len(entries)} entries'
    }

@api_router.get('/raffles/check-entry/{raffle_id}/{phone}')
async def check_entry_status(raffle_id: str, phone: str):
    """Check if user has entered and their status"""
    entry = await db.raffle_entries.find_one(
        {'raffle_id': raffle_id, 'phone': phone},
        {'_id': 0, 'fingerprint': 0, 'ip_address': 0, 'user_agent': 0}
    )
    
    if not entry:
        return {'entered': False}
    
    return {
        'entered': True,
        'entry_id': entry['id'],
        'status': entry['status'],
        'selected_size': entry['selected_size'],
        'entered_at': entry['entered_at'],
        'is_winner': entry['status'] == 'winner'
    }

# ============ SCHEDULER STATUS ============
from scheduler import get_scheduler_status, scrape_all_brands as run_full_scrape, get_scraper_health, get_health_status
from scraper_agent import scraper_agent

@api_router.get('/scheduler/status')
async def scheduler_status():
    return get_scheduler_status()

@api_router.post('/scheduler/trigger')
async def trigger_scrape():
    """Manually trigger a full scrape cycle"""
    import asyncio
    asyncio.create_task(run_full_scrape())
    return {'message': 'Scrape cycle triggered', 'status': 'running'}

@api_router.get('/admin/scraper-health')
async def scraper_health_dashboard():
    """
    Get detailed health status for all scrapers.
    Shows success rates, blocked brands, last errors, and healing stats.
    """
    scraper_health = get_scraper_health()
    system_health = get_health_status()
    
    # Get agent summary
    agent_summary = await scraper_agent.get_agent_summary()
    
    # Calculate summary stats
    total_brands = len(scraper_health)
    healthy_brands = sum(1 for s in scraper_health if not s.get('is_blocked') and s.get('consecutive_failures', 0) == 0)
    blocked_brands = sum(1 for s in scraper_health if s.get('is_blocked'))
    degraded_brands = sum(1 for s in scraper_health if s.get('consecutive_failures', 0) > 0 and not s.get('is_blocked'))
    
    avg_success_rate = sum(s.get('success_rate', 0) for s in scraper_health) / max(total_brands, 1)
    
    return {
        'summary': {
            'total_brands': total_brands,
            'healthy': healthy_brands,
            'blocked': blocked_brands,
            'degraded': degraded_brands,
            'average_success_rate': round(avg_success_rate, 1),
            'system_status': system_health.get('status', 'unknown'),
        },
        'scrapers': scraper_health,
        'system_health': system_health,
        'agent': agent_summary,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@api_router.get('/admin/agent-logs')
async def get_agent_logs(limit: int = 100, brand_key: str = None):
    """
    Get detailed logs of everything the agent tried.
    Shows what worked, what failed, and current winning strategies.
    """
    logs = await scraper_agent.get_agent_logs(limit=limit, brand_key=brand_key)
    strategies = await scraper_agent.get_brand_strategies()
    summary = await scraper_agent.get_agent_summary()
    
    # Check for response time warnings
    warnings = await scraper_agent.proactive_check_all_brands()
    
    return {
        'logs': logs,
        'brand_strategies': strategies,
        'summary': summary,
        'proactive_warnings': warnings,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

# ============ AETHER MASTER STATUS ============
@api_router.get('/admin/aether-status')
async def get_aether_status():
    """Get the full Aether Master health report — current + history."""
    from aether_master import aether_master
    status = aether_master.get_status()
    history = await aether_master.get_history(limit=20)
    recent_incidents = await aether_master.get_incidents(limit=30)
    return {
        'current': status,
        'history': history,
        'recent_incidents': recent_incidents,
    }

@api_router.post('/admin/aether-run')
async def trigger_aether_cycle():
    """Manually trigger an Aether Master health cycle."""
    from aether_master import aether_master
    report = await aether_master.run_cycle()
    return aether_master.get_status()

@api_router.get('/admin/catalog-audit')
async def get_catalog_audit():
    """Get latest catalog completeness audit results."""
    from catalog_auditor import catalog_auditor
    history = await catalog_auditor.get_history(limit=10)
    return {
        'status': catalog_auditor.get_status(),
        'history': history,
    }

@api_router.post('/admin/catalog-audit/run')
async def trigger_catalog_audit():
    """Manually trigger a catalog completeness audit."""
    from catalog_auditor import catalog_auditor
    result = await catalog_auditor.run_audit()
    return result

@api_router.get('/admin/data-quality')
async def get_data_quality():
    """Get data quality check history."""
    from data_quality_validator import data_quality_validator
    history = await data_quality_validator.get_history(limit=10)
    return {'history': history}

@api_router.post('/admin/data-quality/run')
async def trigger_data_quality_check():
    """Manually trigger a data quality validation."""
    from data_quality_validator import data_quality_validator
    result = await data_quality_validator.run_full_audit()
    return result



# ============ AI PRODUCT CLASSIFICATION ============
from classifier import (
    classify_product, 
    classify_products_batch, 
    run_batch_classification,
    clean_product_title,
    update_product_classification,
    get_classification_stats,
    classify_new_products_batch
)

# Track ongoing classification jobs
classification_jobs = {}

@api_router.get('/classification/status')
async def classification_status():
    """Get classification statistics"""
    # Count products by classification status
    total = await db.products.count_documents({})
    classified = await db.products.count_documents({'aiGender': {'$exists': True}})
    unclassified = total - classified
    
    # Get breakdown by AI category
    pipeline = [
        {'$match': {'aiCategory': {'$exists': True}}},
        {'$group': {'_id': '$aiCategory', 'count': {'$sum': 1}}}
    ]
    category_breakdown = await db.products.aggregate(pipeline).to_list(100)
    
    # Get breakdown by AI gender
    gender_pipeline = [
        {'$match': {'aiGender': {'$exists': True}}},
        {'$group': {'_id': '$aiGender', 'count': {'$sum': 1}}}
    ]
    gender_breakdown = await db.products.aggregate(gender_pipeline).to_list(100)
    
    # Get ongoing job status
    active_jobs = {k: v for k, v in classification_jobs.items() if v.get('status') == 'running'}
    
    return {
        'total_products': total,
        'classified': classified,
        'unclassified': unclassified,
        'percentage': round((classified / total * 100) if total > 0 else 0, 2),
        'by_category': {item['_id']: item['count'] for item in category_breakdown},
        'by_gender': {item['_id']: item['count'] for item in gender_breakdown},
        'active_jobs': len(active_jobs),
        'jobs': active_jobs
    }

@api_router.post('/classification/run')
async def trigger_classification(
    limit: int = Query(100, description='Max products to classify'),
    skip_classified: bool = Query(True, description='Skip already classified products'),
    batch_size: int = Query(15, description='Products per API call (max 20)')
):
    """
    Trigger BATCH classification of products using Gemini Flash.
    
    Uses efficient batch API approach:
    - Sends multiple products per API call (batch_size)
    - Much faster than 1-by-1 processing
    - Bulk writes to MongoDB
    
    Args:
        limit: Max products to classify
        skip_classified: Skip products that already have AI tags
        batch_size: Products per Gemini API call (default 15, max 20)
    """
    import asyncio
    import uuid
    
    # Validate batch_size
    batch_size = min(20, max(1, batch_size))
    
    job_id = str(uuid.uuid4())[:8]
    classification_jobs[job_id] = {
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'limit': limit,
        'skip_classified': skip_classified,
        'batch_size': batch_size,
        'method': 'gemini-2.5-flash-batch'
    }
    
    async def run_job():
        try:
            stats = await run_batch_classification(
                db, 
                limit=limit, 
                skip_classified=skip_classified,
                batch_size=batch_size
            )
            classification_jobs[job_id].update({
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                **stats
            })
        except Exception as e:
            classification_jobs[job_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
    
    asyncio.create_task(run_job())
    
    return {
        'message': f'Batch classification job started with Gemini Flash',
        'job_id': job_id,
        'limit': limit,
        'skip_classified': skip_classified,
        'batch_size': batch_size,
        'method': 'gemini-2.5-flash-batch'
    }

@api_router.get('/classification/job/{job_id}')
async def get_classification_job(job_id: str):
    """Get status of a specific classification job"""
    if job_id not in classification_jobs:
        raise HTTPException(status_code=404, detail='Job not found')
    return classification_jobs[job_id]

@api_router.post('/classification/single/{product_id}')
async def classify_single_product(product_id: str):
    """Classify a single product by ID"""
    product = await db.products.find_one({'id': product_id}, {'_id': 0})
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    classified = await classify_product(product)
    await update_product_classification(db, product_id, classified)
    
    return {
        'product_id': product_id,
        'classification': {
            'normalizedTitle': classified.get('normalizedTitle'),
            'aiGender': classified.get('aiGender'),
            'aiCategory': classified.get('aiCategory'),
            'aiSubcategory': classified.get('aiSubcategory'),
            'aiBrand': classified.get('aiBrand'),
            'aiConfidence': classified.get('aiConfidence')
        }
    }


@api_router.post('/classification/high-demand')
async def classify_high_demand_products(
    limit: int = Query(500, description='Max products to classify'),
    batch_size: int = Query(20, description='Products per API call')
):
    """
    Classify HIGH DEMAND products first:
    - Sneakers/Shoes (Nike, Jordan, Yeezy, ON, etc.)
    - Limited editions
    - Popular streetwear brands
    """
    import asyncio
    import uuid
    
    batch_size = min(20, max(1, batch_size))
    job_id = str(uuid.uuid4())[:8]
    
    # High demand query - prioritize shoes and popular brands
    high_demand_query = {
        'aiGender': {'$exists': False},
        '$or': [
            # Shoes/Sneakers keywords
            {'name': {'$regex': 'dunk|jordan|yeezy|air max|air force|cloudnova|gel-|990|550|574|slide|foam', '$options': 'i'}},
            # Popular brands
            {'name': {'$regex': 'nike|adidas|new balance|amiri|off-white|supreme|stussy|palace', '$options': 'i'}},
            {'brand': {'$regex': 'nike|jordan|on|amiri|yeezy', '$options': 'i'}},
            # Limited editions
            {'name': {'$regex': 'limited|exclusive|only.*india|collab', '$options': 'i'}},
            {'isLimited': True}
        ]
    }
    
    classification_jobs[job_id] = {
        'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(),
        'limit': limit,
        'batch_size': batch_size,
        'method': 'gemini-2.5-flash-batch',
        'priority': 'high-demand'
    }
    
    async def run_high_demand_job():
        try:
            from classifier import classify_products_batch, update_products_bulk
            
            # Get high-demand unclassified products
            products = await db.products.find(
                high_demand_query, 
                {'_id': 0}
            ).limit(limit).to_list(limit)
            
            if not products:
                classification_jobs[job_id].update({
                    'status': 'completed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'total': 0,
                    'message': 'No high-demand products to classify'
                })
                return
            
            # Classify
            classified = await classify_products_batch(products, batch_size=batch_size)
            result = await update_products_bulk(db, classified)
            
            classification_jobs[job_id].update({
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'total': len(products),
                'classified': result.get('updated', 0),
                'errors': result.get('errors', 0)
            })
        except Exception as e:
            classification_jobs[job_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
    
    asyncio.create_task(run_high_demand_job())
    
    return {
        'message': 'High-demand classification job started',
        'job_id': job_id,
        'priority': 'high-demand (sneakers, popular brands, limited editions)',
        'limit': limit,
        'batch_size': batch_size
    }


# ============ ALERT LOG ============
@api_router.get('/alerts/recent')
async def recent_alerts():
    alerts = await db.alert_log.find({}, {'_id': 0}).sort('createdAt', -1).limit(50).to_list(50)
    return {'alerts': alerts, 'count': len(alerts)}


@api_router.get('/savings/active')
async def get_active_savings(
    limit: int = Query(50, ge=1, le=200),
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_savings_pct: float = Query(0, ge=0, le=100),
):
    """Live cross-store savings feed: products that are cheaper at another store right now.

    Updated nightly by the cross-store savings scanner. Sorted by savings % desc.
    """
    query: dict = {}
    if brand:
        query['brand'] = {'$regex': f'^{brand}$', '$options': 'i'}
    if category:
        query['category'] = {'$regex': f'^{category}$', '$options': 'i'}
    if min_savings_pct > 0:
        query['savingsPct'] = {'$gte': min_savings_pct}

    total = await db.cross_store_savings.count_documents(query)
    savings = await db.cross_store_savings.find(query, {'_id': 0}) \
        .sort('savingsPct', -1) \
        .limit(limit) \
        .to_list(limit)

    return {
        'savings': savings,
        'count': len(savings),
        'total': total,
    }


@api_router.post('/admin/savings/run-scan')
async def run_savings_scan_now():
    """Admin-only: manually trigger the cross-store savings scan (instead of waiting for nightly cron)."""
    from cross_store_savings import cross_store_savings_scanner
    result = await cross_store_savings_scanner.run_scan(_find_cross_store_prices)
    return {'ok': True, 'result': result}


@api_router.get('/admin/savings/status')
async def savings_scanner_status():
    """Admin-only: last-run status of the cross-store savings scanner."""
    from cross_store_savings import cross_store_savings_scanner
    return cross_store_savings_scanner.get_status()


# ============ CLOSED BETA PROGRAM ============
# Free 30-day access for the first 100 signups. After cap, signup is blocked
# gracefully (UI shows a "Beta full — join waitlist" state).
BETA_MAX_SPOTS = 100
BETA_DURATION_DAYS = 30


class BetaSignupRequest(BaseModel):
    phone: str
    name: str
    email: str


class BetaFeedbackRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    category: str  # 'bug' | 'idea' | 'love' | 'other'
    page: Optional[str] = None  # which page they were on
    message: str
    rating: Optional[int] = None  # 1-5 optional CSAT


@api_router.get('/beta/status')
async def beta_status():
    """Public counter so the landing banner and /beta page show live spot availability."""
    taken = await db.subscribers.count_documents({'isBeta': True})
    spots_left = max(0, BETA_MAX_SPOTS - taken)
    return {
        'total': BETA_MAX_SPOTS,
        'taken': taken,
        'spots_left': spots_left,
        'is_open': spots_left > 0,
    }


@api_router.post('/beta/signup')
@limiter.limit("3/hour")
async def beta_signup(request: Request, data: BetaSignupRequest):
    """Closed beta signup. Requires verified OTP, bypasses payment, activates
    30-day free membership, flags subscriber as beta for analytics."""
    phone = data.phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')

    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=400, detail='Phone not verified. Complete OTP first.')

    # Cap enforcement — but if this phone is already a beta user, allow "resume"
    existing = await db.subscribers.find_one({'phone': phone}, {'_id': 0, 'isBeta': 1, 'isPaid': 1})
    if not (existing and existing.get('isBeta')):
        taken = await db.subscribers.count_documents({'isBeta': True})
        if taken >= BETA_MAX_SPOTS:
            raise HTTPException(status_code=403, detail='Beta is full. Please check back soon.')
        if existing and existing.get('isPaid'):
            raise HTTPException(status_code=400, detail='You already have a paid membership.')

    # Activate beta — give regular-tier feature set for 30 days
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=BETA_DURATION_DAYS)
    membership_id = f"DC-BETA-{now.strftime('%Y%m')}-{random.randint(100, 999)}"

    await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'name': data.name.strip(),
            'email': data.email.strip(),
            'isActive': True,
            'isPaid': True,             # unlocks full product surface
            'isBeta': True,             # analytics flag
            'membershipId': membership_id,
            'plan': 'beta_30d',
            'tier': 'regular',
            'brandLimit': 0,            # unlimited for beta (VIP-level)
            'paidAt': now.isoformat(),
            'expiresAt': expires.isoformat(),
            'betaJoinedAt': now.isoformat(),
            'betaExpiresAt': expires.isoformat(),
            'notificationChannel': 'email',  # email default per product choice
            'updatedAt': now.isoformat(),
        }},
        upsert=True,
    )
    logger.info(f"[Beta] New signup {phone} ({data.email})")

    # Send welcome email (non-blocking — best effort)
    try:
        from email_alerts import _send_email, _tpl_new_drop, _shell
        welcome_inner = f"""
<div class="hero">
  <p class="kicker">Welcome to the Beta · {_esc_safe(data.name.split()[0])}</p>
  <h1>You're in. All 25+ brands unlocked for 30 days.</h1>
  <p>You're one of the first {BETA_MAX_SPOTS} members shaping Drops Curated. Over the next 30 days, you'll get instant alerts across email, WhatsApp and Telegram for every drop, price cut, and cross-store save we spot. Zero payment, zero catches.</p>
  <p>As a beta member, your feedback shapes the product. Hit any bug or have an idea? Drop us a line — it goes straight to the founding team.</p>
  <div style="margin:28px 0">
    <a href="{APP_URL_SAFE}/beta/feedback" class="btn" style="background:#001F3F;color:#FAF8F5">Share feedback →</a>
  </div>
  <p>— The Drops Curated team</p>
</div>
"""
        html = _shell(welcome_inner, preheader='You are in · 30 days free access')
        _send_email(data.email.strip(), 'Welcome to the Drops Curated beta', html, tags=['beta_welcome'])
    except Exception as e:
        logger.warning(f"[Beta] Welcome email failed for {phone}: {e}")

    return {
        'success': True,
        'membership_id': membership_id,
        'expires_at': expires.isoformat(),
        'duration_days': BETA_DURATION_DAYS,
    }


@api_router.post('/beta/feedback')
@limiter.limit("30/hour")
async def beta_feedback(request: Request, data: BetaFeedbackRequest):
    """Collect in-app feedback from beta testers. No auth required — we want
    zero friction. Phone/email optional."""
    if not data.message or len(data.message.strip()) < 5:
        raise HTTPException(status_code=400, detail='Message too short — please add more detail')
    if data.category not in ('bug', 'idea', 'love', 'other'):
        raise HTTPException(status_code=400, detail='Invalid category')

    ip = (request.headers.get('x-forwarded-for') or
          (request.client.host if request.client else '')).split(',')[0].strip()
    ua = request.headers.get('user-agent', '')[:300]

    doc = {
        'id': f"fb_{secrets.token_urlsafe(8)}",
        'phone': (data.phone or '').strip() or None,
        'email': (data.email or '').strip() or None,
        'category': data.category,
        'page': (data.page or '')[:150],
        'message': data.message.strip()[:4000],
        'rating': data.rating if data.rating and 1 <= data.rating <= 5 else None,
        'ip': ip,
        'ua': ua,
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'status': 'new',  # new | triaged | fixed | wontfix
    }
    await db.beta_feedback.insert_one(doc)
    logger.info(f"[BetaFeedback] {data.category}: {data.message[:80]}")

    # Ping admin via email (best effort)
    try:
        from email_alerts import _send_email
        admin_email = os.environ.get('BETA_ADMIN_EMAIL', 'Dropscurated@gmail.com')
        body_html = f"""<html><body style="font-family:system-ui,sans-serif;background:#F3F1ED;padding:24px">
<h2 style="font-family:Georgia,serif;color:#001F3F">New beta feedback · {data.category.upper()}</h2>
<p><b>From:</b> {data.phone or '—'} · {data.email or '—'}</p>
<p><b>Page:</b> {data.page or '—'}</p>
<p><b>Rating:</b> {data.rating if data.rating else '—'}/5</p>
<div style="background:#FAF8F5;border-left:3px solid #D4AF37;padding:14px;margin:16px 0;color:#001F3F;white-space:pre-wrap">{_esc_safe(data.message[:1500])}</div>
<p style="color:#888;font-size:12px">IP {ip} · {ua[:80]}</p>
</body></html>"""
        _send_email(admin_email, f"[Beta] {data.category}: {data.message[:60]}",
                    body_html, tags=['beta_feedback', data.category])
    except Exception as e:
        logger.warning(f"[BetaFeedback] Admin email failed: {e}")

    return {'ok': True, 'id': doc['id']}


@api_router.get('/admin/beta/feedback')
async def admin_beta_feedback(status: Optional[str] = None, limit: int = 100):
    """Admin: list beta feedback, newest first. Optional status filter."""
    q: dict = {}
    if status:
        q['status'] = status
    items = await db.beta_feedback.find(q, {'_id': 0}).sort('createdAt', -1).limit(limit).to_list(limit)
    # Summary counts
    by_category = {}
    async for row in db.beta_feedback.aggregate([
        {'$group': {'_id': '$category', 'n': {'$sum': 1}}}
    ]):
        by_category[row['_id']] = row['n']
    return {
        'items': items,
        'count': len(items),
        'by_category': by_category,
    }


@api_router.get('/admin/beta/testers')
async def admin_beta_testers():
    """Admin: cohort snapshot — channel mix + engagement proxy (alerts received)."""
    pipeline = [
        {'$match': {'isBeta': True}},
        {'$project': {'_id': 0, 'phone': 1, 'email': 1, 'name': 1, 'notificationChannel': 1,
                      'betaJoinedAt': 1, 'betaExpiresAt': 1, 'telegramChatId': 1,
                      'preferences.brands': 1}}
    ]
    testers = await db.subscribers.aggregate(pipeline).to_list(200)
    # Channel mix
    mix = {'email_only': 0, 'email_whatsapp': 0, 'email_telegram': 0,
           'email_whatsapp_telegram': 0}
    for t in testers:
        ch = t.get('notificationChannel', 'email') or 'email'
        if ch == 'both':
            ch = 'email,whatsapp'
        parts = set(s.strip() for s in ch.split(','))
        if parts == {'email'}:
            mix['email_only'] += 1
        elif parts == {'email', 'whatsapp'}:
            mix['email_whatsapp'] += 1
        elif parts == {'email', 'telegram'}:
            mix['email_telegram'] += 1
        elif parts == {'email', 'whatsapp', 'telegram'}:
            mix['email_whatsapp_telegram'] += 1
    return {
        'count': len(testers),
        'testers': testers,
        'channel_mix': mix,
    }


def _esc_safe(s: str) -> str:
    import html
    return html.escape(str(s or ''), quote=False)


APP_URL_SAFE = os.environ.get('APP_URL', 'https://drops-curated.preview.emergentagent.com').rstrip('/')


# ============ TELEGRAM BOT ============
class TelegramLinkRequest(BaseModel):
    phone: str


@api_router.post('/telegram/link-code')
async def telegram_generate_link_code(payload: TelegramLinkRequest):
    """Member clicks 'Connect Telegram' → we mint a one-time code and return the
    deep-link they should open in Telegram. The bot's /start handler consumes
    the code and links their chat_id."""
    import telegram_alerts
    phone = payload.phone.strip()
    if not validate_phone_number(phone):
        raise HTTPException(status_code=400, detail='Invalid phone number')
    sub = await db.subscribers.find_one({'phone': phone}, {'_id': 0, 'isPaid': 1})
    if not sub:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    code = telegram_alerts.create_link_code(phone)
    link = telegram_alerts.deep_link_for(code)
    return {'code': code, 'deep_link': link, 'expires_in_s': 600}


@api_router.post('/telegram/webhook')
async def telegram_webhook(request: Request):
    """Receive updates from Telegram. Do not rate-limit — Telegram retries
    aggressively and we already validate shape."""
    import telegram_alerts
    try:
        update = await request.json()
    except Exception:
        return {'ok': False, 'error': 'invalid-json'}
    return await telegram_alerts.handle_webhook_update(db, update)


@api_router.get('/admin/telegram/status')
async def telegram_status():
    """Admin: status of the Telegram bot (webhook info, token configured)."""
    import telegram_alerts
    info = await telegram_alerts.get_webhook_info()
    return {
        'configured': telegram_alerts.IS_CONFIGURED,
        'bot_username': telegram_alerts.TELEGRAM_BOT_USERNAME,
        'webhook_info': info,
    }


class TelegramSetWebhookRequest(BaseModel):
    webhook_url: Optional[str] = None  # if None, derives from BACKEND_PUBLIC_URL / preview fallback


@api_router.post('/admin/telegram/set-webhook')
async def telegram_set_webhook(payload: Optional[TelegramSetWebhookRequest] = None):
    """Admin: register our webhook URL with Telegram.
    Accepts an optional `webhook_url` so the admin UI can re-point the bot at
    the deployed production URL after going live. Falls back to
    BACKEND_PUBLIC_URL env var, then the preview URL."""
    import telegram_alerts
    custom = (payload and payload.webhook_url and payload.webhook_url.strip()) or None
    if custom:
        webhook_url = custom.rstrip('/')
        if not webhook_url.endswith('/api/telegram/webhook'):
            webhook_url = f"{webhook_url.rstrip('/')}/api/telegram/webhook"
    else:
        backend_url = os.environ.get('BACKEND_PUBLIC_URL') or 'https://drops-curated.preview.emergentagent.com'
        webhook_url = f"{backend_url.rstrip('/')}/api/telegram/webhook"
    ok, msg = await telegram_alerts.set_webhook(webhook_url)
    return {'ok': ok, 'webhook_url': webhook_url, 'result': str(msg)}


# ============ FRESHNESS / STALE-DATA GUARD ============
@api_router.get('/admin/freshness/status')
async def admin_freshness_status():
    """Admin: per-brand freshness report + recent stale-skip events.
    Surfaces brands whose scraper is silently stuck so ops can intervene
    before users receive wrong-price alerts."""
    from freshness import MAX_ALERT_AGE_HOURS, _parse_iso, _hours_since

    now = datetime.now(timezone.utc)
    brands = await db.brands.find({'isActive': True}, {'_id': 0}).to_list(200)
    rows = []
    for b in brands:
        last = _parse_iso(b.get('lastScrapedAt'))
        age = _hours_since(last) if last else None
        rows.append({
            'key': b.get('key'),
            'name': b.get('name'),
            'storeKey': b.get('storeKey') or b.get('store_key'),
            'lastScrapedAt': b.get('lastScrapedAt'),
            'ageHours': round(age, 2) if age is not None else None,
            'isFresh': bool(last and age is not None and age <= MAX_ALERT_AGE_HOURS),
            'productCount': b.get('productCount', 0),
        })
    rows.sort(key=lambda r: (r['isFresh'], -(r['ageHours'] or 9999)))

    # Recent stale-skip events (last 7 days for trend view, last 48h for list)
    cutoff_48h = (now - timedelta(hours=48)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()

    recent = await db.stale_alerts_log.find(
        {'createdAt': {'$gte': cutoff_48h}},
        {'_id': 0},
    ).sort('createdAt', -1).limit(100).to_list(100)

    # Aggregate skips by reason category so the admin sees immediately whether
    # the system is dropping alerts because of (a) stale scrapes or (b) brands
    # bouncing prices back mid-digest. Both deserve attention but for
    # different reasons.
    weekly_skips = await db.stale_alerts_log.find(
        {'createdAt': {'$gte': cutoff_7d}},
        {'_id': 0, 'alertType': 1, 'reason': 1, 'store': 1, 'extra': 1, 'createdAt': 1},
    ).to_list(5000)

    buckets = {'stale_age': 0, 'bounced': 0, 'empty_scrape': 0, 'other': 0}
    bounced_by_store = {}
    for s in weekly_skips:
        at = s.get('alertType') or ''
        rsn = (s.get('reason') or '').lower()
        if 'bounced' in at or 'bounced' in rsn:
            buckets['bounced'] += 1
            st = s.get('store') or 'unknown'
            bounced_by_store[st] = bounced_by_store.get(st, 0) + 1
        elif 'batch' in at or 'empty' in rsn:
            buckets['empty_scrape'] += 1
        elif 'digest' in at or 'age' in rsn:
            buckets['stale_age'] += 1
        else:
            buckets['other'] += 1

    # Top 5 brands causing bounced alerts — these are your "flagged" brands.
    top_bounced_stores = sorted(
        bounced_by_store.items(), key=lambda x: -x[1]
    )[:5]

    stale_brands = [r for r in rows if not r['isFresh']]
    return {
        'max_alert_age_hours': MAX_ALERT_AGE_HOURS,
        'total_brands': len(rows),
        'fresh_brands': len(rows) - len(stale_brands),
        'stale_brands_count': len(stale_brands),
        'brands': rows,
        'recent_stale_skips': recent,
        'weekly_skip_buckets': buckets,
        'weekly_skip_total': sum(buckets.values()),
        'top_bounced_stores': [{'store': s, 'count': n} for s, n in top_bounced_stores],
        'generatedAt': now.isoformat(),
    }


@api_router.post('/admin/freshness/rescrape/{brand_key}')
async def admin_freshness_force_rescrape(brand_key: str):
    """Admin: trigger an immediate re-scrape of a single brand. Used by the
    Freshness dashboard 'Rescrape now' button to unstick silent failures."""
    if brand_key not in SCRAPERS:
        raise HTTPException(status_code=404, detail=f"Unknown brand key: {brand_key}")
    try:
        scraper = SCRAPERS[brand_key]()
        scraped = await scraper.run_swarm_scrape(max_pages=20)
        if not scraped:
            return {
                'ok': False,
                'brand_key': brand_key,
                'error': 'Scrape returned zero products — scraper may be broken or blocked',
            }
        result = await _store_scraped_products(scraped, brand_key)
        return {
            'ok': True,
            'brand_key': brand_key,
            'products_scraped': len(scraped),
            **result,
        }
    except Exception as e:
        logger.exception(f"[Freshness] Force rescrape failed for {brand_key}: {e}")
        return {'ok': False, 'brand_key': brand_key, 'error': str(e)}


# ============ EMAIL (BREVO) ADMIN ============
class EmailTestRequest(BaseModel):
    to: str
    kind: str = 'test'  # test | price_drop | new_drop | cross_save | digest


@api_router.get('/admin/email/status')
async def email_service_status():
    """Expose whether Brevo is configured + sender identity (no secrets)."""
    from email_alerts import IS_CONFIGURED as EMAIL_ON, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME, BREVO_REPLY_TO
    return {
        'configured': EMAIL_ON,
        'sender_email': BREVO_SENDER_EMAIL,
        'sender_name': BREVO_SENDER_NAME,
        'reply_to': BREVO_REPLY_TO,
    }


@api_router.post('/admin/email/test')
async def admin_send_test_email(payload: EmailTestRequest):
    """Admin-only: send a sample email to verify Brevo setup / DKIM / inbox placement.
    Pulls a REAL product + image URL from the DB (no fake image URLs) so image
    rendering can be verified end-to-end.
    """
    from email_alerts import (
        send_test_email, send_price_drop_alert as p_drop,
        send_new_drop_alert as new_drop,
        send_cross_store_save_alert as cross_save,
        send_daily_digest_email as digest,
    )
    kind = (payload.kind or 'test').lower()
    to = payload.to.strip()
    if '@' not in to:
        raise HTTPException(status_code=400, detail='Invalid email')

    # Pull a real product with a valid imageUrl so tests actually render an image
    app_url = os.environ.get('APP_URL', 'https://dropscurated.com')
    demo_prod = await db.products.find_one(
        {'isActive': True, 'imageUrl': {'$exists': True, '$ne': None, '$regex': '^https?://'}},
        {'_id': 0, 'id': 1, 'name': 1, 'brand': 1, 'store': 1, 'imageUrl': 1, 'productUrl': 1}
    ) or {}
    # Fallback demo data
    demo_name = demo_prod.get('name', 'Arcana Jacquard Patched Boxy Tee')
    demo_brand = demo_prod.get('brand', 'Almost Gods')
    demo_img = demo_prod.get('imageUrl', '')
    demo_url = demo_prod.get('productUrl') or f'{app_url}/products/{demo_prod.get("id", "")}'

    if kind == 'price_drop':
        ok, info = p_drop(to, demo_name, 9500, 12117,
                          brand=demo_brand, image_url=demo_img,
                          product_url=demo_url, savings_pct=22)
    elif kind == 'new_drop':
        ok, info = new_drop(to, demo_name, 4299, brand=demo_brand,
                            image_url=demo_img, product_url=demo_url)
    elif kind == 'cross_save':
        ok, info = cross_save(to, demo_name, demo_brand,
                              9500, 12117, 'SUPERKICKS',
                              demo_url, demo_img, 2617, 22)
    elif kind == 'digest':
        # Grab two real products for a rich demo digest
        demo_prods = await db.products.find(
            {'isActive': True, 'imageUrl': {'$regex': '^https?://'}},
            {'_id': 0, 'id': 1, 'name': 1, 'brand': 1, 'imageUrl': 1, 'productUrl': 1}
        ).limit(2).to_list(2)
        alerts_demo = []
        if len(demo_prods) > 0:
            p = demo_prods[0]
            alerts_demo.append({'type': 'new_release', 'data': {
                'name': p['name'], 'brand': p.get('brand', ''), 'price': 4299,
                'image_url': p.get('imageUrl', ''),
                'product_url': p.get('productUrl') or f'{app_url}/products/{p["id"]}'
            }})
        if len(demo_prods) > 1:
            p = demo_prods[1]
            alerts_demo.append({'type': 'price_drop', 'data': {
                'name': p['name'], 'brand': p.get('brand', ''),
                'new_price': 9500, 'old_price': 12117,
                'image_url': p.get('imageUrl', ''),
                'product_url': p.get('productUrl') or f'{app_url}/products/{p["id"]}'
            }})
        ok, info = digest(to, datetime.now(timezone.utc).strftime('%Y-%m-%d'), alerts_demo)
    else:
        ok, info = send_test_email(to)
    return {'ok': ok, 'info': str(info), 'kind': kind, 'recipient': to, 'image_used': demo_img}

@api_router.get('/alerts/digest/{phone}')
async def get_daily_digest(phone: str):
    """Get pending daily digest for a subscriber"""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    digest = await db.daily_digest.find_one(
        {'phone': phone, 'date': today},
        {'_id': 0}
    )
    if not digest:
        return {'phone': phone, 'date': today, 'alerts': [], 'count': 0}
    return {
        'phone': phone,
        'date': today,
        'alerts': digest.get('alerts', []),
        'count': len(digest.get('alerts', []))
    }

@api_router.post('/alerts/send-digests')
async def send_daily_digests():
    """
    Send daily digest messages to all subscribers with queued alerts.
    Routes to each subscriber's chosen notificationChannel (email | whatsapp |
    telegram | combinations). Called by the scheduler at 8 PM IST.

    Freshness invariant: any alert whose underlying product's price data is
    older than MAX_ALERT_AGE_HOURS is silently dropped from the digest to
    prevent stale-price incidents (see EVEMEN ₹3,486 → ₹1,800 on Apr 21).
    """
    from whatsapp import whatsapp_client, IS_CONFIGURED
    from email_alerts import send_daily_digest_email
    from telegram_alerts import send_daily_digest as tg_send_daily_digest
    from freshness import is_price_fresh, log_stale_skip, MAX_ALERT_AGE_HOURS

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    digests = await db.daily_digest.find({'date': today, 'sent': {'$ne': True}}).to_list(1000)

    sent_count = 0
    failed_count = 0
    stale_dropped = 0

    for digest in digests:
        phone = digest.get('phone', '')
        raw_alerts = digest.get('alerts', [])

        if not raw_alerts:
            continue

        # Freshness + live-verification filter.
        # freshness: drop alerts whose price data is older than cap (already).
        # live verify: for price_drop alerts, re-fetch the current stored price
        # right NOW — if the price has bounced back to or above the original,
        # the brand has already reverted and the alert is a lie-by-delivery.
        # Same for cross_store_save: re-check the cheapest store still wins.
        alerts = []
        for a in raw_alerts:
            data = a.get('data') or {}
            atype = a.get('type', 'unknown')
            # Figure out the productId + store to check. Different alert types
            # stash them under different keys — we try the common ones.
            pid = data.get('productId') or data.get('id')
            store = data.get('store') or data.get('sourceStore') or data.get('cheapestStore')
            if pid and store:
                fresh, age = await is_price_fresh(db, pid, store)
                if not fresh:
                    stale_dropped += 1
                    await log_stale_skip(
                        db,
                        alert_type=f"digest/{atype}",
                        reason=f"age {age}h > cap {MAX_ALERT_AGE_HOURS}h",
                        product_id=pid,
                        store=store,
                        age_hours=age,
                        phone=phone,
                        extra={'name': data.get('name')},
                    )
                    continue

                # Live-verification: for price-drop alerts, re-check the
                # current stored price is still at-or-below what we alerted.
                # If the brand bounced the price back UP before digest time,
                # the alert becomes a lie-by-delivery — drop it silently.
                if atype == 'price_drop' and pid and store:
                    live = await db.prices.find_one(
                        {'productId': pid, 'store': store},
                        {'_id': 0, 'currentPrice': 1},
                    )
                    live_price = (live or {}).get('currentPrice') or 0
                    alerted_new = data.get('new_price') or data.get('price') or 0
                    alerted_old = data.get('old_price') or 0
                    # Tolerate ≤1% drift (rounding). If live price is >1% above
                    # the price we alerted, the drop is no longer valid.
                    if alerted_new > 0 and live_price > alerted_new * 1.01:
                        stale_dropped += 1
                        await log_stale_skip(
                            db,
                            alert_type=f"digest/{atype}/bounced",
                            reason=f"live price ₹{live_price} > alerted new ₹{alerted_new}; brand reverted before delivery",
                            product_id=pid,
                            store=store,
                            phone=phone,
                            extra={
                                'name': data.get('name'),
                                'alerted_new': alerted_new,
                                'alerted_old': alerted_old,
                                'live_price': live_price,
                            },
                        )
                        continue

                # Historical-MSRP sanity: if old_price == new_price OR gap <1%,
                # the "SAVE X%" claim is meaningless. Strip the historical
                # old_price so the email template only shows the current price.
                if atype == 'price_drop':
                    op = data.get('old_price') or 0
                    np = data.get('new_price') or 0
                    if op and np and op <= np * 1.01:
                        data['old_price'] = None
                        data['drop_percent'] = None
            alerts.append(a)

        if not alerts:
            # All alerts were stale — mark digest sent so we don't spam tomorrow
            await db.daily_digest.update_one(
                {'_id': digest['_id']},
                {'$set': {'sent': True, 'stale_filtered': True, 'sentAt': datetime.now(timezone.utc).isoformat()}}
            )
            continue

        # Look up subscriber to get channel preference + email + chat_id
        sub = await db.subscribers.find_one(
            {'phone': phone},
            {'_id': 0, 'email': 1, 'notificationChannel': 1, 'preferences': 1, 'telegramChatId': 1}
        ) or {}
        channel_raw = (sub.get('notificationChannel') or (sub.get('preferences') or {}).get('notification_channel') or 'email').lower()
        if channel_raw == 'both':
            channel_raw = 'email,whatsapp'
        channel_set = set(s.strip() for s in channel_raw.split(',') if s.strip())
        send_email = 'email' in channel_set
        send_wa = 'whatsapp' in channel_set
        send_telegram = 'telegram' in channel_set
        sub_email = sub.get('email', '')
        telegram_chat_id = sub.get('telegramChatId')

        # Build plain-text message (WhatsApp)
        new_drops = [a for a in alerts if a.get('type') == 'new_release']
        price_drops = [a for a in alerts if a.get('type') == 'price_drop']
        restocks = [a for a in alerts if a.get('type') == 'restock']
        cross_saves = [a for a in alerts if a.get('type') == 'cross_store_save']

        message = "🌙 *Your Daily Drops Digest*\n\n"
        message += f"_{today}_\n\n"
        if new_drops:
            message += f"🆕 *{len(new_drops)} New Arrivals*\n"
            for nd in new_drops[:3]:
                data = nd.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]} - ₹{data.get('price', 0):,.0f}\n"
            if len(new_drops) > 3:
                message += f"  _...and {len(new_drops) - 3} more_\n"
            message += "\n"
        if price_drops:
            message += f"💰 *{len(price_drops)} Price Drops*\n"
            for pd in price_drops[:3]:
                data = pd.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]} - ₹{data.get('new_price', 0):,.0f} (was ₹{data.get('old_price', 0):,.0f})\n"
            if len(price_drops) > 3:
                message += f"  _...and {len(price_drops) - 3} more_\n"
            message += "\n"
        if restocks:
            message += f"📦 *{len(restocks)} Back in Stock*\n"
            for rs in restocks[:3]:
                data = rs.get('data', {})
                message += f"  • {data.get('name', 'Product')[:40]}\n"
            message += "\n"
        if cross_saves:
            message += f"🔀 *{len(cross_saves)} Cheaper Elsewhere*\n"
            for cs in cross_saves[:3]:
                data = cs.get('data', {})
                name = (data.get('name') or 'Product')[:40]
                cheapest_store = (data.get('cheapestStore') or '').replace('_', ' ').title()
                cheapest_price = data.get('cheapestPrice', 0)
                source_price = data.get('sourcePrice', 0)
                saving_pct = data.get('savingsPct', 0)
                message += f"  • {name} — ₹{cheapest_price:,.0f} at {cheapest_store} (was ₹{source_price:,.0f}, save {saving_pct}%)\n"
            if len(cross_saves) > 3:
                message += f"  _...and {len(cross_saves) - 3} more_\n"
            message += "\n"
        message += "👉 Browse all drops on Drops Curated!"

        wa_ok = False
        email_ok = False
        tg_ok = False

        # WhatsApp
        if send_wa:
            if IS_CONFIGURED:
                wa_ok, _ = whatsapp_client.send_text_message(phone, message)
            else:
                wa_ok = True
                logger.info(f"[Sandbox] WA digest to {phone}: {len(alerts)} alerts")

        # Email (rich HTML)
        if send_email and sub_email:
            email_ok, _ = send_daily_digest_email(sub_email, today, alerts)

        # Telegram (rich formatted)
        if send_telegram and telegram_chat_id:
            tg_ok, _ = await tg_send_daily_digest(telegram_chat_id, today, alerts)

        success = wa_ok or email_ok or tg_ok or (not send_wa and not send_email and not send_telegram)
        if success:
            sent_count += 1
            await db.daily_digest.update_one(
                {'_id': digest['_id']},
                {'$set': {
                    'sent': True,
                    'sentAt': datetime.now(timezone.utc).isoformat(),
                    'channels': {'whatsapp': wa_ok, 'email': email_ok, 'telegram': tg_ok},
                }}
            )
        else:
            failed_count += 1

    logger.info(f"[Daily Digest] Sent {sent_count} digests, {failed_count} failed")
    return {
        'sent': sent_count,
        'failed': failed_count,
        'date': today
    }


# ============ WHATSAPP WEBHOOK (Meta Compliance) ============
@api_router.post('/whatsapp/webhook')
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages (STOP/UNSUBSCRIBE requests)
    
    This endpoint processes opt-out requests to maintain Meta Quality Rating.
    Verifies Meta webhook signature for security.
    """
    from whatsapp import handle_stop_request, IS_CONFIGURED
    
    # Verify Meta webhook signature
    app_secret = os.getenv('WHATSAPP_APP_SECRET', '')
    signature = request.headers.get('X-Hub-Signature-256', '')
    
    if app_secret:  # Only verify if secret is configured
        body_bytes = await request.body()
        if not verify_whatsapp_signature(body_bytes, signature, app_secret):
            logger.warning(f"[WhatsApp Webhook] Invalid signature from {get_client_ip(request)}")
            raise HTTPException(status_code=401, detail='Invalid webhook signature')
        body = await request.json()
    else:
        # Development mode - skip verification but log warning
        logger.warning("[WhatsApp Webhook] WHATSAPP_APP_SECRET not set - signature verification disabled")
        body = await request.json()
    
    try:
        logger.info(f"[WhatsApp Webhook] Received: {body}")
        
        # Parse the webhook payload (Meta format)
        entry = body.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        for msg in messages:
            msg_type = msg.get('type', '')
            phone = msg.get('from', '')  # Phone number in E.164 format without +
            
            # Normalize phone (remove 91 prefix for Indian numbers)
            if phone.startswith('91') and len(phone) == 12:
                phone = phone[2:]
            
            if msg_type == 'text':
                text = msg.get('text', {}).get('body', '').strip().upper()
                
                # Check for opt-out keywords
                if text in ['STOP', 'UNSUBSCRIBE', 'CANCEL', 'QUIT', 'END']:
                    logger.info(f"[Opt-Out] Processing STOP request from {phone}")
                    
                    # Update subscriber status
                    result = await db.subscribers.update_one(
                        {'phone': phone},
                        {'$set': {
                            'isActive': False,
                            'optedOutAt': datetime.now(timezone.utc).isoformat(),
                            'optOutMethod': 'whatsapp_reply',
                            'optOutKeyword': text,
                        }}
                    )
                    
                    # Log the opt-out
                    await db.opt_out_log.insert_one({
                        'phone': phone,
                        'keyword': text,
                        'source': 'whatsapp_webhook',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                    })
                    
                    # Send confirmation message
                    if IS_CONFIGURED:
                        handle_stop_request(phone)
                    else:
                        logger.info(f"[Sandbox] Opt-out confirmation to {phone}")
                    
                    logger.info(f"[Opt-Out] Completed for {phone}, matched: {result.matched_count}")
        
        return {'status': 'ok'}
        
    except Exception as e:
        logger.error(f"[WhatsApp Webhook] Error: {e}")
        return {'status': 'error', 'message': str(e)}


@api_router.get('/whatsapp/webhook')
async def whatsapp_webhook_verify(request: Request):
    """
    Verify webhook for Meta WhatsApp Business API
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    """
    mode = request.query_params.get('hub.mode', '')
    token = request.query_params.get('hub.verify_token', '')
    challenge = request.query_params.get('hub.challenge', '')
    
    # Set your verify token in environment variable
    verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'drops_curated_webhook_2024')
    
    if mode == 'subscribe' and token == verify_token:
        logger.info("[WhatsApp Webhook] Verification successful")
        return int(challenge)
    else:
        logger.warning(f"[WhatsApp Webhook] Verification failed - mode: {mode}, token: {token}")
        raise HTTPException(status_code=403, detail='Verification failed')


@api_router.post('/unsubscribe')
async def manual_unsubscribe(phone: str = Query(...)):
    """
    Manual unsubscribe endpoint (alternative to WhatsApp reply)
    
    Can be called from a web page or API.
    """
    from whatsapp import handle_stop_request, IS_CONFIGURED
    
    phone = phone.strip()
    if len(phone) == 12 and phone.startswith('91'):
        phone = phone[2:]
    
    # Find subscriber
    sub = await db.subscribers.find_one({'phone': phone})
    if not sub:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    if not sub.get('isActive', False):
        return {'message': 'Already unsubscribed', 'phone': phone}
    
    # Update subscriber status
    await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'isActive': False,
            'optedOutAt': datetime.now(timezone.utc).isoformat(),
            'optOutMethod': 'manual_api',
        }}
    )
    
    # Log the opt-out
    await db.opt_out_log.insert_one({
        'phone': phone,
        'keyword': 'MANUAL',
        'source': 'api_endpoint',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })
    
    # Send confirmation message
    if IS_CONFIGURED:
        handle_stop_request(phone)
    else:
        logger.info(f"[Sandbox] Manual opt-out confirmation to {phone}")
    
    return {'message': 'Successfully unsubscribed', 'phone': phone}


# ============ PARTNER INQUIRIES ============
class PartnerInquiry(BaseModel):
    brand: str
    contact: str
    email: str
    message: str = ""

@api_router.post('/partner-inquiry')
async def partner_inquiry(data: PartnerInquiry):
    doc = {
        'brand': data.brand,
        'contact': data.contact,
        'email': data.email,
        'message': data.message,
        'status': 'new',
        'createdAt': datetime.now(timezone.utc).isoformat(),
    }
    await db.partner_inquiries.insert_one(doc)
    return {'message': 'Inquiry received', 'status': 'created'}

# ============ REAL-TIME SCRAPING ============
from scrapers import SCRAPERS


_SHIPPING_KEYWORDS = ['ship', 'shipping', 'delivery', 'dispatch', 'days', 'week', 'lead time', 'express', 'standard', 'business']

def _filter_shipping_from_sizes(sizes: list) -> list:
    """Remove shipping-related strings from size arrays before storing."""
    return [s for s in sizes if not any(kw in str(s).lower() for kw in _SHIPPING_KEYWORDS)]


async def _store_scraped_products(scraped_products: list[dict], brand_key: str) -> dict:
    """Store scraped products and prices in MongoDB"""
    products_added = 0
    products_updated = 0
    prices_added = 0

    for item in scraped_products:
        # Use the scraper-provided ID if available, otherwise generate one
        product_id = item.get("id") or f"prod_{item['store']}_{abs(hash(item['name'])) % 1000000}"
        product_url = item.get("product_url", "")

        existing = await db.products.find_one({"name": item["name"], "store": item["store"]})

        if existing:
            # Update existing product
            size_prices_clean = {k: v for k, v in item.get("size_prices", {}).items() if k not in ('', 'Default Title')}
            update_fields = {
                "imageUrl": item["image_url"],
                "isActive": True,
                "updatedAt": item["scraped_at"],
                "attributes.sizes": _filter_shipping_from_sizes(item.get("available_sizes", [])),
            }
            if product_url:
                update_fields["productUrl"] = product_url
            if size_prices_clean:
                update_fields["attributes.size_prices"] = size_prices_clean
            
            old_product_id = existing.get("id")
            
            # Update product ID if scraper provides a better one
            if item.get("id") and old_product_id != item["id"]:
                update_fields["id"] = item["id"]
                product_id = item["id"]
                # Migrate old price records to the new ID
                await db.prices.update_many(
                    {"productId": old_product_id, "store": item["store"]},
                    {"$set": {"productId": item["id"]}}
                )
            else:
                product_id = old_product_id
            
            await db.products.update_one(
                {"_id": existing["_id"]},
                {"$set": update_fields}
            )
            products_updated += 1
        else:
            product_doc = {
                "id": product_id,
                "name": item["name"],
                "brand": item["brand"],
                "category": item["category"],
                "description": f'{item["brand"]} {item["category"].lower()} from {item["store"].replace("_", " ").title()}',
                "imageUrl": item["image_url"],
                "productUrl": item.get("product_url", ""),
                "additionalImages": [],
                "attributes": {
                    "sizes": _filter_shipping_from_sizes(item.get("available_sizes", [])),
                    "size_prices": {k: v for k, v in item.get("size_prices", {}).items() if k not in ('', 'Default Title')},
                },
                "tags": item.get("tags", []) + [item["brand"].lower(), item["category"].lower()],
                "store": item["store"],
                "isActive": True,
                "isTrending": False,
                "createdAt": item["scraped_at"],
            }
            await db.products.insert_one(product_doc)
            products_added += 1

        # Upsert price record
        price_data = {
            "id": f"price_{product_id}_{item['store']}",
            "productId": product_id,
            "store": item["store"],
            "productUrl": item.get("product_url", ""),
            "currentPrice": item["price"],
            "lowestPrice": item.get("lowest_price", item["price"]),
            "highestPrice": item.get("highest_price", item["price"]),
            "originalPrice": item.get("original_price", item["price"]),
            "inStock": item.get("in_stock", True),
            "lastScrapedAt": item["scraped_at"],
            "createdAt": item["scraped_at"],
        }
        size_prices = item.get("size_prices", {})
        if size_prices:
            price_data["sizePrices"] = size_prices
        
        await db.prices.update_one(
            {"productId": product_id, "store": item["store"]},
            {"$set": price_data},
            upsert=True,
        )
        prices_added += 1

    # Update brand record
    scraper_cls = SCRAPERS.get(brand_key)
    if scraper_cls:
        s = scraper_cls()
        await db.brands.update_one(
            {"key": brand_key},
            {"$set": {
                "key": brand_key,
                "name": s.brand_name,
                "storeKey": s.store_key,
                "websiteUrl": s.base_url,
                "isActive": True,
                "lastScrapedAt": datetime.now(timezone.utc).isoformat(),
                "productCount": await db.products.count_documents({"store": s.store_key}),
            }},
            upsert=True,
        )

    return {"products_added": products_added, "products_updated": products_updated, "prices_added": prices_added}


@api_router.post("/scrape/{brand_key}")
async def scrape_brand(brand_key: str):
    """Scrape products from a specific brand"""
    if brand_key not in SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Unknown brand: {brand_key}. Available: {list(SCRAPERS.keys())}")

    scraper = SCRAPERS[brand_key]()
    logger.info(f"Starting scrape for {scraper.brand_name}")

    scraped = await scraper.run_swarm_scrape(max_pages=20)
    if not scraped:
        return {"success": False, "message": f"No products found for {scraper.brand_name}", "scraped": 0}

    result = await _store_scraped_products(scraped, brand_key)

    return {
        "success": True,
        "brand": scraper.brand_name,
        "scraped": len(scraped),
        **result,
        "message": f"Scraped {len(scraped)} products from {scraper.brand_name}",
    }


@api_router.post("/scrape/all")
async def scrape_all_brands():
    """Scrape all available brands"""
    results = {}
    for key, scraper_cls in SCRAPERS.items():
        scraper = scraper_cls()
        logger.info(f"Scraping {scraper.brand_name}...")
        try:
            scraped = await scraper.run_swarm_scrape(max_pages=20)
            result = await _store_scraped_products(scraped, key)
            results[key] = {"success": True, "scraped": len(scraped), **result}
        except Exception as e:
            logger.error(f"Scrape error for {key}: {e}")
            results[key] = {"success": False, "error": str(e)}

    total = sum(r.get("scraped", 0) for r in results.values())
    return {"success": True, "total_scraped": total, "results": results}


@api_router.get("/scrape/status")
async def scrape_status():
    """Get scraping status for all brands"""
    import random as rnd
    brands = await db.brands.find({}, {"_id": 0}).to_list(100)
    
    # Shuffle brands so all stores get equal visibility
    rnd.shuffle(brands)
    
    total_products = await db.products.count_documents({"isActive": True})
    total_prices = await db.prices.count_documents({})

    return {
        "brands": brands,
        "total_products": total_products,
        "total_prices": total_prices,
        "available_scrapers": list(SCRAPERS.keys()),
    }

# ============ VISUAL SEARCH ============
@api_router.post('/visual-search')
async def visual_search(
    image: UploadFile = File(...),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    AI-Powered Visual Search using OpenAI Vision
    Analyzes uploaded image and finds similar products
    """
    
    # Validate image
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File must be an image')
    
    # Read and encode image
    contents = await image.read()
    base64_image = base64.b64encode(contents).decode('utf-8')
    
    try:
        # Use OpenAI Vision to analyze the image
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this product image and provide:
1. Product type (shoes/clothes/cosmetics/accessories)
2. Brand (if visible)
3. Color
4. Style/design keywords
5. Gender target (men/women/unisex)

Format: type|brand|color|style|gender
Example: shoes|Nike|black|sneakers athletic sporty|men"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=200
        )
        
        # Parse AI response
        ai_analysis = response.choices[0].message.content.strip()
        logger.info(f"AI Analysis: {ai_analysis}")
        
        # Extract features
        parts = ai_analysis.split('|')
        detected_type = parts[0].strip().upper() if len(parts) > 0 else None
        detected_brand = parts[1].strip() if len(parts) > 1 else None
        detected_color = parts[2].strip().lower() if len(parts) > 2 else None
        detected_style = parts[3].strip().lower() if len(parts) > 3 else ""
        
        # Build search terms
        search_terms = []
        if detected_brand and detected_brand.lower() != 'unknown':
            search_terms.append(detected_brand)
        if detected_color:
            search_terms.append(detected_color)
        search_terms.extend(detected_style.split())
        
        # Determine category
        category_map = {
            'shoes': 'SHOES',
            'sneakers': 'SHOES',
            'footwear': 'SHOES',
            'clothes': 'CLOTHES',
            'clothing': 'CLOTHES',
            'shirt': 'CLOTHES',
            'tshirt': 'CLOTHES',
            'hoodie': 'CLOTHES',
            'cosmetics': 'COSMETICS',
            'makeup': 'COSMETICS',
            'lipstick': 'COSMETICS',
            'accessories': 'ACCESSORIES'
        }
        
        search_category = None
        if detected_type:
            for key, value in category_map.items():
                if key in detected_type.lower():
                    search_category = value
                    break
        
        if not search_category and category:
            search_category = category
        elif not search_category:
            search_category = 'SHOES'  # Default
        
        # Search products in the category
        query = {'isActive': True, 'category': search_category}
        all_products = await db.products.find(query, {'_id': 0}).to_list(1000)
        
        # Score products based on match
        scored_products = []
        for product in all_products:
            score = 0
            product_text = f"{product['name']} {product['brand']} {product.get('description', '')} {' '.join(product.get('tags', []))}".lower()
            
            # Brand match (highest priority)
            if detected_brand and detected_brand.lower() in product_text:
                score += 50
            
            # Color match
            if detected_color and detected_color in product_text:
                score += 20
            
            # Style keywords match
            for term in search_terms:
                if term.lower() in product_text:
                    score += 10
            
            # Category match
            if product['category'] == search_category:
                score += 5
            
            scored_products.append((score, product))
        
        # Sort by score and get top results
        scored_products.sort(reverse=True, key=lambda x: x[0])
        similar_products = [p[1] for p in scored_products[:8]]
        
        if not similar_products:
            # Fallback: return all products from category
            similar_products = all_products[:8]
        
        # Enrich with price data
        for product in similar_products:
            prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(100)
            if prices:
                product['lowestPrice'] = min(p['currentPrice'] for p in prices)
                product['highestPrice'] = max(p['currentPrice'] for p in prices)
                product['priceCount'] = len(prices)
            else:
                product['lowestPrice'] = 0
                product['highestPrice'] = 0
                product['priceCount'] = 0
        
        # Log visual search
        search_doc = {
            'userId': current_user['id'],
            'query': f'visual_search_{search_category}',
            'category': search_category,
            'isImageSearch': True,
            'resultsCount': len(similar_products),
            'aiAnalysis': ai_analysis,
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        await db.search_history.insert_one(search_doc)
        
        return {
            'products': similar_products,
            'category': search_category,
            'analysis': {
                'type': detected_type,
                'brand': detected_brand,
                'color': detected_color,
                'style': detected_style
            },
            'message': f'AI detected: {detected_type or "product"} - {detected_brand or "unknown brand"} - {detected_color or "various colors"}',
            'powered_by': 'OpenAI Vision (GPT-4o-mini)'
        }
        
    except Exception as e:
        logger.error(f"Visual search error: {str(e)}")
        # Fallback to category-based search
        search_category = category if category else 'SHOES'
        query = {'isActive': True, 'category': search_category}
        products = await db.products.find(query, {'_id': 0}).limit(8).to_list(8)
        
        for product in products:
            prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(100)
            if prices:
                product['lowestPrice'] = min(p['currentPrice'] for p in prices)
                product['highestPrice'] = max(p['currentPrice'] for p in prices)
                product['priceCount'] = len(prices)
        
        return {
            'products': products,
            'category': search_category,
            'message': f'Showing {search_category.lower()} products. AI analysis unavailable.',
            'error': str(e)
        }

# Include router
app.include_router(api_router)

# Security Middlewares (order matters - first added = last executed)
# 1. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request Validation (body size, blocked IPs, DDoS)
app.add_middleware(RequestValidationMiddleware)

# 3. CORS Lockdown - replaced permissive CORS
app.add_middleware(CORSLockdownMiddleware)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_scheduler():
    from scheduler import init_scheduler
    from auth import init_admin_routes, admin_router, seed_admin_user
    from scraper_agent import init_scraper_agent
    from scrapers import aether_brain
    from aether_master import init_aether_master
    from catalog_auditor import init_catalog_auditor
    from data_quality_validator import init_data_quality_validator
    
    # Initialize security module
    await init_security(app, db)
    logger.info("Security module initialized")
    
    # Initialize scheduler
    init_scheduler(db)
    logger.info("Scheduler initialized - auto-scraping every 15 minutes")
    
    # Initialize admin routes
    init_admin_routes(db)
    app.include_router(admin_router)
    logger.info("Admin routes initialized")
    
    # Initialize self-healing scraper agent
    await init_scraper_agent(db)
    logger.info("Self-healing scraper agent initialized with Gemini LLM")
    
    # Initialize Aether Brain self-learning
    await aether_brain.init(db)
    logger.info("Aether Brain self-learning system initialized")
    
    # Initialize Aether Master site guardian
    await init_aether_master(db)
    logger.info("Aether Master site guardian initialized")
    
    # Initialize Catalog Auditor
    await init_catalog_auditor(db)
    logger.info("Catalog Auditor initialized")

    # Initialize Data Quality Validator
    await init_data_quality_validator(db)
    logger.info("Data Quality Validator initialized")
    
    # Seed default admin user
    await seed_admin_user()
