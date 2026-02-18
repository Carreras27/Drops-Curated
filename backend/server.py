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

app = FastAPI(title="IndiaShop API", version="1.0.0")
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

# ============ SEARCH & PRODUCTS ============
@api_router.get('/search')
async def search_products(
    q: str = Query(..., min_length=2),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    # Search in name, description, brand, and tags
    query = {
        '$or': [
            {'name': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}},
            {'brand': {'$regex': q, '$options': 'i'}},
            {'tags': {'$regex': q, '$options': 'i'}},
        ]
    }
    
    if category:
        query['category'] = category
    
    skip = (page - 1) * limit
    products = await db.products.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.products.count_documents(query)
    
    # Enrich products with price data
    for product in products:
        prices = await db.prices.find({'productId': product['id']}, {'_id': 0}).to_list(100)
        if prices:
            product['lowestPrice'] = min(p['currentPrice'] for p in prices)
            product['highestPrice'] = max(p['currentPrice'] for p in prices)
            product['priceCount'] = len(prices)
        else:
            product['lowestPrice'] = 0
            product['highestPrice'] = 0
            product['priceCount'] = 0
    
    return {
        'products': products,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    }

@api_router.get('/products/{product_id}')
async def get_product(product_id: str):
    product = await db.products.find_one({'id': product_id}, {'_id': 0})
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    prices = await db.prices.find({'productId': product_id}, {'_id': 0}).sort('currentPrice', 1).to_list(100)
    
    return {'product': product, 'prices': prices}

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
    brands = await db.brands.find(
        {'isActive': True},
        {'_id': 0}
    ).sort('popularityScore', -1).to_list(100)
    
    return {'brands': brands}

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
