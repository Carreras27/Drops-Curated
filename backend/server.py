from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from enum import Enum
import base64
import openai

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
async def login(login_data: UserLogin):
    user = await db.users.find_one({'email': login_data.email})
    if not user or not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    token = create_jwt_token(user['id'], user['email'])
    return {'token': token, 'user': User(**{k: v for k, v in user.items() if k not in ['password_hash', '_id']})}

@api_router.get('/auth/me', response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)

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
    """Get public statistics for social proof on landing page"""
    active_members = await db.subscribers.count_documents({'isActive': True, 'isPaid': True})
    total_products = await db.products.count_documents({})
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
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description='Search query'),
    limit: int = Query(10, ge=1, le=20)
):
    """
    Get search suggestions for autocomplete.
    Returns matching brands, categories, and product names.
    """
    search_term = q.strip().lower()
    
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
async def search_products(
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
    
    query = {}
    search_term = q.strip()
    
    # Store filter - filter by store/brand key (e.g., CREPDOG_CREW)
    if store:
        query['store'] = {'$regex': f'^{store}$', '$options': 'i'}
    # Search query - searches name, description, brand, tags, store
    elif search_term:
        # For very short search terms (<=3 chars like "On", "NIL"), ONLY search brand field
        # This prevents false positives like "Monk On Fire Hoodie" where "on" is just a preposition
        if len(search_term) <= 3:
            # STRICT BRAND-ONLY MATCH for short terms
            query['brand'] = {'$regex': f'^{search_term}$', '$options': 'i'}
        elif len(search_term) <= 5:
            # For medium terms (4-5 chars), use word boundary matching on brand and name
            word_regex = f'\\b{search_term}\\b'
            query['$or'] = [
                {'brand': {'$regex': f'^{search_term}$', '$options': 'i'}},
                {'brand': {'$regex': word_regex, '$options': 'i'}},
                {'name': {'$regex': word_regex, '$options': 'i'}},
                {'store': {'$regex': word_regex, '$options': 'i'}},
            ]
        else:
            # For longer search terms, use standard partial matching
            query['$or'] = [
                {'name': {'$regex': search_term, '$options': 'i'}},
                {'description': {'$regex': search_term, '$options': 'i'}},
                {'brand': {'$regex': search_term, '$options': 'i'}},
                {'tags': {'$regex': search_term, '$options': 'i'}},
                {'store': {'$regex': search_term, '$options': 'i'}},
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
    
    prices = await db.prices.find({'productId': product_id}, {'_id': 0}).sort('currentPrice', 1).to_list(100)
    
    return {'product': product, 'prices': prices}

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

@api_router.post('/otp/send')
async def send_otp_endpoint(data: OTPRequest):
    """Send OTP via WhatsApp using Meta Cloud API"""
    from whatsapp import send_otp as whatsapp_send_otp, IS_CONFIGURED
    
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
async def create_payment_order(data: CreateOrderRequest):
    """Create a Razorpay order for subscription"""
    phone = data.phone.strip()
    stored = otp_store.get(phone)
    if not stored or not stored.get('verified'):
        raise HTTPException(status_code=400, detail='Phone not verified. Complete OTP first.')

    amount = 39900  # ₹399 in paise

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
            'notes': {'phone': phone, 'plan': data.plan},
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
        'plan': data.plan,
        'createdAt': datetime.now(timezone.utc).isoformat(),
    })

    return {
        'order_id': order_data['id'],
        'amount': amount,
        'currency': 'INR',
        'key_id': RAZORPAY_KEY_ID,
        'sandbox': SANDBOX_MODE,
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

    # Activate membership
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)
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
            'plan': order.get('plan', 'monthly'),
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
    }
    
    result = await db.subscribers.update_one(
        {'phone': phone},
        {'$set': {
            'preferences': preferences,
            'updatedAt': datetime.now(timezone.utc).isoformat(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Subscriber not found')
    
    logger.info(f"[Preferences] Updated for {phone}: {len(data.brands)} brands, {data.alert_types}, {data.alert_frequency} frequency")
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
import time
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
from scheduler import get_scheduler_status, scrape_all_brands as run_full_scrape

@api_router.get('/scheduler/status')
async def scheduler_status():
    return get_scheduler_status()

@api_router.post('/scheduler/trigger')
async def trigger_scrape():
    """Manually trigger a full scrape cycle"""
    import asyncio
    asyncio.create_task(run_full_scrape())
    return {'message': 'Scrape cycle triggered', 'status': 'running'}

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

# ============ ALERT LOG ============
@api_router.get('/alerts/recent')
async def recent_alerts():
    alerts = await db.alert_log.find({}, {'_id': 0}).sort('createdAt', -1).limit(50).to_list(50)
    return {'alerts': alerts, 'count': len(alerts)}

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
    This should be called by a scheduled job at 8 PM IST.
    """
    from whatsapp import whatsapp_client, IS_CONFIGURED
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    digests = await db.daily_digest.find({'date': today, 'sent': {'$ne': True}}).to_list(1000)
    
    sent_count = 0
    failed_count = 0
    
    for digest in digests:
        phone = digest.get('phone', '')
        alerts = digest.get('alerts', [])
        
        if not alerts:
            continue
        
        # Group alerts by type
        new_drops = [a for a in alerts if a.get('type') == 'new_release']
        price_drops = [a for a in alerts if a.get('type') == 'price_drop']
        restocks = [a for a in alerts if a.get('type') == 'restock']
        
        # Build digest message
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
        
        message += "👉 Browse all drops on Drops Curated!"
        
        # Send the digest
        if IS_CONFIGURED:
            success, result = whatsapp_client.send_text_message(phone, message)
        else:
            success = True  # Sandbox mode
            logger.info(f"[Sandbox] Daily digest to {phone}: {len(alerts)} alerts")
        
        if success:
            sent_count += 1
            await db.daily_digest.update_one(
                {'_id': digest['_id']},
                {'$set': {'sent': True, 'sentAt': datetime.now(timezone.utc).isoformat()}}
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
    """
    from whatsapp import handle_stop_request, IS_CONFIGURED
    
    try:
        body = await request.json()
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

async def _store_scraped_products(scraped_products: list[dict], brand_key: str) -> dict:
    """Store scraped products and prices in MongoDB"""
    products_added = 0
    products_updated = 0
    prices_added = 0

    for item in scraped_products:
        # Generate a stable product ID from name + store
        slug = item["name"].lower().replace(" ", "-").replace("'", "")[:80]
        product_id = f"prod_{item['store']}_{hash(item['name']) % 100000}"

        existing = await db.products.find_one({"name": item["name"], "store": item["store"]})

        if existing:
            # Update existing product
            await db.products.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "imageUrl": item["image_url"],
                    "isActive": True,
                    "updatedAt": item["scraped_at"],
                }}
            )
            product_id = existing["id"]
            products_updated += 1
        else:
            product_doc = {
                "id": product_id,
                "name": item["name"],
                "slug": slug,
                "brand": item["brand"],
                "category": item["category"],
                "description": f'{item["brand"]} {item["category"].lower()} from {item["store"].replace("_", " ").title()}',
                "imageUrl": item["image_url"],
                "additionalImages": [],
                "attributes": {"sizes": item.get("available_sizes", [])},
                "tags": item.get("tags", []) + [item["brand"].lower(), item["category"].lower()],
                "store": item["store"],
                "isActive": True,
                "isTrending": False,
                "createdAt": item["scraped_at"],
            }
            await db.products.insert_one(product_doc)
            products_added += 1

        # Upsert price record
        await db.prices.update_one(
            {"productId": product_id, "store": item["store"]},
            {"$set": {
                "id": f"price_{product_id}_{item['store']}",
                "productId": product_id,
                "store": item["store"],
                "productUrl": item.get("product_url", ""),
                "currentPrice": item["price"],
                "originalPrice": item.get("original_price", item["price"]),
                "inStock": item.get("in_stock", True),
                "lastScrapedAt": item["scraped_at"],
                "createdAt": item["scraped_at"],
            }},
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

    scraped = await scraper.scrape_products(max_pages=3)
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
            scraped = await scraper.scrape_products(max_pages=3)
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    # Initialize scheduler
    init_scheduler(db)
    logger.info("Scheduler initialized - auto-scraping every 15 minutes")
    
    # Initialize admin routes
    init_admin_routes(db)
    app.include_router(admin_router)
    logger.info("Admin routes initialized")
    
    # Seed default admin user
    await seed_admin_user()
