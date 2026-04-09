"""
Admin Authentication and Routes
- JWT-based admin authentication
- Admin dashboard API endpoints
- Subscriber management, revenue stats, scrape controls
"""
import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

# Admin router
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])
security = HTTPBearer()

# Config
ADMIN_JWT_SECRET = os.getenv('ADMIN_JWT_SECRET', 'drops-curated-admin-secret-change-in-prod')
ADMIN_JWT_ALGORITHM = 'HS256'
ADMIN_JWT_EXPIRATION_HOURS = 24

# Default admin credentials (change in production!)
DEFAULT_ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@dropscurated.com')
DEFAULT_ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'DropsCurated2024!')

# Database reference (set by server.py)
_db = None

def init_admin_routes(db):
    """Initialize admin routes with database reference"""
    global _db
    _db = db

# ============ MODELS ============
class AdminLogin(BaseModel):
    email: str
    password: str

class AdminUser(BaseModel):
    id: str
    email: str
    role: str
    created_at: str

# ============ AUTH HELPERS ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_admin_token(admin_id: str, email: str, role: str = 'admin') -> str:
    payload = {
        'admin_id': admin_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=ADMIN_JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm=ADMIN_JWT_ALGORITHM)

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify admin JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=[ADMIN_JWT_ALGORITHM])
        
        if payload.get('role') != 'admin':
            raise HTTPException(status_code=403, detail='Admin access required')
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

# ============ SEED ADMIN ============
async def seed_admin_user():
    """Create default admin user if not exists"""
    global _db
    if _db is None:
        return
    
    existing = await _db.admins.find_one({'email': DEFAULT_ADMIN_EMAIL})
    if not existing:
        admin_doc = {
            'id': 'admin_001',
            'email': DEFAULT_ADMIN_EMAIL,
            'password_hash': hash_password(DEFAULT_ADMIN_PASSWORD),
            'role': 'admin',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await _db.admins.insert_one(admin_doc)
        print(f"[Admin] Seeded admin user: {DEFAULT_ADMIN_EMAIL}")

# ============ AUTH ENDPOINTS ============
@admin_router.post('/login')
async def admin_login(data: AdminLogin):
    """Admin login endpoint"""
    global _db
    
    # Check database for admin
    admin = await _db.admins.find_one({'email': data.email})
    
    if not admin:
        # Check against default credentials
        if data.email == DEFAULT_ADMIN_EMAIL and data.password == DEFAULT_ADMIN_PASSWORD:
            # Auto-seed and login
            await seed_admin_user()
            admin = await _db.admins.find_one({'email': data.email})
        else:
            raise HTTPException(status_code=401, detail='Invalid credentials')
    
    if not verify_password(data.password, admin['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    token = create_admin_token(admin['id'], admin['email'], admin.get('role', 'admin'))
    
    return {
        'token': token,
        'admin': {
            'id': admin['id'],
            'email': admin['email'],
            'role': admin.get('role', 'admin')
        }
    }

@admin_router.get('/me')
async def get_admin_profile(admin: dict = Depends(get_current_admin)):
    """Get current admin profile"""
    return {
        'id': admin['admin_id'],
        'email': admin['email'],
        'role': admin['role']
    }

# ============ DASHBOARD STATS ============
@admin_router.get('/stats/overview')
async def get_overview_stats(admin: dict = Depends(get_current_admin)):
    """Get dashboard overview statistics"""
    global _db
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # Subscriber stats
    total_subscribers = await _db.subscribers.count_documents({})
    active_subscribers = await _db.subscribers.count_documents({'isActive': True, 'isPaid': True})
    
    # New subscribers this month
    new_this_month = await _db.subscribers.count_documents({
        'createdAt': {'$gte': thirty_days_ago.isoformat()}
    })
    
    # Product stats
    total_products = await _db.products.count_documents({})
    classified_products = await _db.products.count_documents({'aiGender': {'$exists': True}})
    
    # Revenue calculation (₹399 per active subscriber)
    monthly_revenue = active_subscribers * 399
    
    # Brand stats
    total_brands = await _db.brands.count_documents({'isActive': True})
    
    # Alert stats
    total_alerts_sent = await _db.alert_log.count_documents({})
    alerts_this_week = await _db.alert_log.count_documents({
        'sentAt': {'$gte': seven_days_ago.isoformat()}
    })
    
    # Price drops detected
    price_drops_count = await _db.price_history.count_documents({
        'type': 'price_drop',
        'detectedAt': {'$gte': seven_days_ago.isoformat()}
    })
    
    return {
        'subscribers': {
            'total': total_subscribers,
            'active': active_subscribers,
            'new_this_month': new_this_month,
            'churn_rate': 0  # Calculate based on expired subscriptions
        },
        'revenue': {
            'monthly': monthly_revenue,
            'currency': 'INR',
            'per_subscriber': 399
        },
        'products': {
            'total': total_products,
            'classified': classified_products,
            'classification_rate': round((classified_products / total_products * 100) if total_products > 0 else 0, 1)
        },
        'brands': {
            'total': total_brands
        },
        'alerts': {
            'total_sent': total_alerts_sent,
            'this_week': alerts_this_week,
            'price_drops_detected': price_drops_count
        },
        'generated_at': now.isoformat()
    }

# ============ SUBSCRIBER MANAGEMENT ============
@admin_router.get('/subscribers')
async def list_subscribers(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,  # active, inactive, all
    search: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all subscribers with pagination"""
    global _db
    
    query = {}
    if status == 'active':
        query['isActive'] = True
        query['isPaid'] = True
    elif status == 'inactive':
        query['$or'] = [{'isActive': False}, {'isPaid': False}]
    
    if search:
        query['$or'] = [
            {'phone': {'$regex': search, '$options': 'i'}},
            {'name': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}}
        ]
    
    total = await _db.subscribers.count_documents(query)
    subscribers = await _db.subscribers.find(query, {'_id': 0}).skip((page - 1) * limit).limit(limit).to_list(limit)
    
    return {
        'subscribers': subscribers,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    }

@admin_router.get('/subscribers/{phone}')
async def get_subscriber_detail(phone: str, admin: dict = Depends(get_current_admin)):
    """Get detailed subscriber info"""
    global _db
    
    subscriber = await _db.subscribers.find_one({'phone': phone}, {'_id': 0})
    if not subscriber:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    # Get alert history
    alerts = await _db.alert_log.find({'phone': phone}, {'_id': 0}).sort('sentAt', -1).limit(20).to_list(20)
    
    # Get payment history
    orders = await _db.orders.find({'phone': phone}, {'_id': 0}).sort('createdAt', -1).limit(10).to_list(10)
    
    return {
        'subscriber': subscriber,
        'alerts': alerts,
        'orders': orders
    }

@admin_router.post('/subscribers/{phone}/deactivate')
async def deactivate_subscriber(phone: str, admin: dict = Depends(get_current_admin)):
    """Deactivate a subscriber"""
    global _db
    
    result = await _db.subscribers.update_one(
        {'phone': phone},
        {'$set': {'isActive': False, 'deactivatedAt': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    return {'message': 'Subscriber deactivated', 'phone': phone}

@admin_router.post('/subscribers/{phone}/reactivate')
async def reactivate_subscriber(phone: str, admin: dict = Depends(get_current_admin)):
    """Reactivate a subscriber"""
    global _db
    
    result = await _db.subscribers.update_one(
        {'phone': phone},
        {'$set': {'isActive': True, 'reactivatedAt': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    return {'message': 'Subscriber reactivated', 'phone': phone}

# ============ BRAND MANAGEMENT ============
@admin_router.get('/brands')
async def list_brands_admin(admin: dict = Depends(get_current_admin)):
    """List all brands with stats"""
    global _db
    
    brands = await _db.brands.find({}, {'_id': 0}).to_list(100)
    
    # Enrich with product counts
    for brand in brands:
        brand['productCount'] = await _db.products.count_documents({'store': brand.get('storeKey', brand.get('key'))})
    
    return {'brands': brands}

@admin_router.post('/brands/{brand_key}/toggle')
async def toggle_brand(brand_key: str, admin: dict = Depends(get_current_admin)):
    """Enable/disable a brand from scraping"""
    global _db
    
    brand = await _db.brands.find_one({'key': brand_key})
    if not brand:
        raise HTTPException(status_code=404, detail='Brand not found')
    
    new_status = not brand.get('isActive', True)
    
    await _db.brands.update_one(
        {'key': brand_key},
        {'$set': {'isActive': new_status, 'updatedAt': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'message': f'Brand {"enabled" if new_status else "disabled"}', 'brand': brand_key, 'isActive': new_status}

# ============ SCRAPER CONTROLS ============
@admin_router.post('/scraper/trigger')
async def trigger_scrape(admin: dict = Depends(get_current_admin)):
    """Manually trigger a full scrape cycle"""
    from scheduler import scrape_all_brands
    import asyncio
    
    asyncio.create_task(scrape_all_brands())
    
    return {'message': 'Scrape cycle triggered', 'status': 'running'}

@admin_router.post('/scraper/trigger/{brand_key}')
async def trigger_brand_scrape(brand_key: str, admin: dict = Depends(get_current_admin)):
    """Manually trigger scrape for a specific brand"""
    global _db
    from scrapers import SCRAPERS
    
    if brand_key not in SCRAPERS:
        raise HTTPException(status_code=404, detail='Brand scraper not found')
    
    # Run scrape in background
    import asyncio
    
    async def run_single_scrape():
        scraper = SCRAPERS[brand_key]()
        scraped = await scraper.scrape_products(max_pages=5)
        return len(scraped)
    
    asyncio.create_task(run_single_scrape())
    
    return {'message': f'Scrape triggered for {brand_key}', 'status': 'running'}

@admin_router.get('/scraper/status')
async def get_scraper_status(admin: dict = Depends(get_current_admin)):
    """Get current scraper status"""
    from scheduler import get_scheduler_status
    return get_scheduler_status()

# ============ AI CLASSIFICATION STATS ============
@admin_router.get('/classification/stats')
async def get_classification_stats(admin: dict = Depends(get_current_admin)):
    """Get AI classification statistics"""
    global _db
    
    total = await _db.products.count_documents({})
    classified = await _db.products.count_documents({'aiGender': {'$exists': True}})
    
    # Category breakdown
    category_pipeline = [
        {'$match': {'aiCategory': {'$exists': True}}},
        {'$group': {'_id': '$aiCategory', 'count': {'$sum': 1}}}
    ]
    categories = await _db.products.aggregate(category_pipeline).to_list(100)
    
    # Gender breakdown
    gender_pipeline = [
        {'$match': {'aiGender': {'$exists': True}}},
        {'$group': {'_id': '$aiGender', 'count': {'$sum': 1}}}
    ]
    genders = await _db.products.aggregate(gender_pipeline).to_list(100)
    
    # Subcategory breakdown
    subcategory_pipeline = [
        {'$match': {'aiSubcategory': {'$exists': True}}},
        {'$group': {'_id': '$aiSubcategory', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 20}
    ]
    subcategories = await _db.products.aggregate(subcategory_pipeline).to_list(20)
    
    # Confidence distribution
    confidence_pipeline = [
        {'$match': {'aiConfidence': {'$exists': True}}},
        {'$bucket': {
            'groupBy': '$aiConfidence',
            'boundaries': [0, 0.5, 0.7, 0.9, 1.01],
            'default': 'unknown',
            'output': {'count': {'$sum': 1}}
        }}
    ]
    confidence_dist = await _db.products.aggregate(confidence_pipeline).to_list(10)
    
    return {
        'total_products': total,
        'classified': classified,
        'unclassified': total - classified,
        'percentage': round((classified / total * 100) if total > 0 else 0, 2),
        'by_category': {item['_id']: item['count'] for item in categories},
        'by_gender': {item['_id']: item['count'] for item in genders},
        'by_subcategory': {item['_id']: item['count'] for item in subcategories},
        'confidence_distribution': confidence_dist
    }

@admin_router.post('/classification/run')
async def trigger_classification(
    limit: int = 1000,
    admin: dict = Depends(get_current_admin)
):
    """Trigger batch classification"""
    from classifier import run_batch_classification
    import asyncio
    
    async def run_job():
        return await run_batch_classification(_db, limit=limit, skip_classified=True)
    
    asyncio.create_task(run_job())
    
    return {'message': 'Classification job started', 'limit': limit}

# ============ ALERT LOGS ============
@admin_router.get('/alerts/logs')
async def get_alert_logs(
    page: int = 1,
    limit: int = 50,
    admin: dict = Depends(get_current_admin)
):
    """Get alert sending logs"""
    global _db
    
    total = await _db.alert_log.count_documents({})
    logs = await _db.alert_log.find({}, {'_id': 0}).sort('sentAt', -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    
    return {
        'logs': logs,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    }
