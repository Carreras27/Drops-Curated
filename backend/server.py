from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'house-of-kitchens-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Stripe Configuration
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', 'sk_test_emergent')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ======================
# MODELS
# ======================

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # "chef" or "customer"
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    created_at: str

class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    chef_id: str
    chef_name: str
    name: str
    description: str
    price: float
    image_url: str
    category: str
    is_available: bool = True
    created_at: str

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    category: str
    is_available: bool = True

class ChefAvailability(BaseModel):
    model_config = ConfigDict(extra="ignore")
    chef_id: str
    is_online: bool
    available_slots: List[Dict[str, str]] = []  # [{"start": "09:00", "end": "14:00"}]

class OrderItem(BaseModel):
    menu_item_id: str
    name: str
    price: float
    quantity: int
    chef_id: str

class OrderCreate(BaseModel):
    items: List[OrderItem]
    delivery_address: str
    origin_url: str

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_name: str
    items: List[OrderItem]
    total_amount: float
    delivery_address: str
    status: str  # "pending", "confirmed", "preparing", "on_the_way", "delivered", "cancelled"
    payment_status: str  # "pending", "paid", "failed"
    session_id: Optional[str] = None
    created_at: str

class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    chef_id: str
    customer_id: str
    customer_name: str
    rating: int
    comment: str
    created_at: str

class ReviewCreate(BaseModel):
    order_id: str
    chef_id: str
    rating: int
    comment: str

class CheckoutRequest(BaseModel):
    order_id: str
    origin_url: str

# ======================
# AUTH HELPERS
# ======================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
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
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid token')

# ======================
# AUTH ENDPOINTS
# ======================

@api_router.post('/auth/signup')
async def signup(user_data: UserSignup):
    # Check if user exists
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    
    # Create user
    user_id = f"user_{datetime.now(timezone.utc).timestamp()}"
    user_doc = {
        'id': user_id,
        'email': user_data.email,
        'password_hash': hash_password(user_data.password),
        'name': user_data.name,
        'role': user_data.role,
        'phone': user_data.phone,
        'avatar': f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_data.name}",
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Create chef availability if role is chef
    if user_data.role == 'chef':
        availability_doc = {
            'chef_id': user_id,
            'is_online': False,
            'available_slots': []
        }
        await db.chef_availability.insert_one(availability_doc)
    
    token = create_jwt_token(user_id, user_data.email, user_data.role)
    return {'token': token, 'user': User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})}

@api_router.post('/auth/login')
async def login(login_data: UserLogin):
    user = await db.users.find_one({'email': login_data.email})
    if not user or not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    token = create_jwt_token(user['id'], user['email'], user['role'])
    return {'token': token, 'user': User(**{k: v for k, v in user.items() if k not in ['password_hash', '_id']})}

@api_router.get('/auth/me', response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)

# ======================
# MENU ENDPOINTS
# ======================

@api_router.post('/menu', response_model=MenuItem)
async def create_menu_item(item_data: MenuItemCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can create menu items')
    
    item_id = f"item_{datetime.now(timezone.utc).timestamp()}"
    item_doc = {
        'id': item_id,
        'chef_id': current_user['id'],
        'chef_name': current_user['name'],
        **item_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.menu_items.insert_one(item_doc)
    return MenuItem(**{k: v for k, v in item_doc.items() if k != '_id'})

@api_router.get('/menu', response_model=List[MenuItem])
async def get_all_menu_items(search: Optional[str] = None):
    query = {'is_available': True}
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'category': {'$regex': search, '$options': 'i'}}
        ]
    items = await db.menu_items.find(query, {'_id': 0}).to_list(1000)
    return [MenuItem(**item) for item in items]

@api_router.get('/menu/chef/{chef_id}', response_model=List[MenuItem])
async def get_chef_menu_items(chef_id: str):
    items = await db.menu_items.find({'chef_id': chef_id}, {'_id': 0}).to_list(1000)
    return [MenuItem(**item) for item in items]

@api_router.get('/menu/my', response_model=List[MenuItem])
async def get_my_menu_items(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can access this')
    items = await db.menu_items.find({'chef_id': current_user['id']}, {'_id': 0}).to_list(1000)
    return [MenuItem(**item) for item in items]

@api_router.put('/menu/{item_id}', response_model=MenuItem)
async def update_menu_item(item_id: str, item_data: MenuItemCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can update menu items')
    
    item = await db.menu_items.find_one({'id': item_id, 'chef_id': current_user['id']})
    if not item:
        raise HTTPException(status_code=404, detail='Menu item not found')
    
    await db.menu_items.update_one(
        {'id': item_id},
        {'$set': item_data.model_dump()}
    )
    
    updated_item = await db.menu_items.find_one({'id': item_id}, {'_id': 0})
    return MenuItem(**updated_item)

@api_router.delete('/menu/{item_id}')
async def delete_menu_item(item_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can delete menu items')
    
    result = await db.menu_items.delete_one({'id': item_id, 'chef_id': current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Menu item not found')
    return {'message': 'Menu item deleted successfully'}

# ======================
# CHEF AVAILABILITY
# ======================

@api_router.get('/chef/availability/{chef_id}', response_model=ChefAvailability)
async def get_chef_availability(chef_id: str):
    availability = await db.chef_availability.find_one({'chef_id': chef_id}, {'_id': 0})
    if not availability:
        return ChefAvailability(chef_id=chef_id, is_online=False, available_slots=[])
    return ChefAvailability(**availability)

@api_router.put('/chef/availability', response_model=ChefAvailability)
async def update_chef_availability(availability_data: ChefAvailability, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can update availability')
    
    await db.chef_availability.update_one(
        {'chef_id': current_user['id']},
        {'$set': availability_data.model_dump()},
        upsert=True
    )
    return availability_data

@api_router.get('/chefs', response_model=List[User])
async def get_all_chefs():
    chefs = await db.users.find({'role': 'chef'}, {'_id': 0, 'password_hash': 0}).to_list(1000)
    return [User(**chef) for chef in chefs]

# ======================
# ORDER ENDPOINTS
# ======================

@api_router.post('/orders', response_model=Order)
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'customer':
        raise HTTPException(status_code=403, detail='Only customers can create orders')
    
    # Calculate total
    total_amount = sum(item.price * item.quantity for item in order_data.items)
    
    order_id = f"order_{datetime.now(timezone.utc).timestamp()}"
    order_doc = {
        'id': order_id,
        'customer_id': current_user['id'],
        'customer_name': current_user['name'],
        'items': [item.model_dump() for item in order_data.items],
        'total_amount': total_amount,
        'delivery_address': order_data.delivery_address,
        'status': 'pending',
        'payment_status': 'pending',
        'session_id': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.orders.insert_one(order_doc)
    return Order(**{k: v for k, v in order_doc.items() if k != '_id'})

@api_router.get('/orders/my', response_model=List[Order])
async def get_my_orders(current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'customer':
        orders = await db.orders.find({'customer_id': current_user['id']}, {'_id': 0}).sort('created_at', -1).to_list(1000)
    else:
        # Chef sees orders containing their items
        orders = await db.orders.find(
            {'items.chef_id': current_user['id']},
            {'_id': 0}
        ).sort('created_at', -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.get('/orders/{order_id}', response_model=Order)
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({'id': order_id}, {'_id': 0})
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    
    # Check access rights
    if current_user['role'] == 'customer' and order['customer_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail='Access denied')
    elif current_user['role'] == 'chef':
        has_item = any(item['chef_id'] == current_user['id'] for item in order['items'])
        if not has_item:
            raise HTTPException(status_code=403, detail='Access denied')
    
    return Order(**order)

@api_router.put('/orders/{order_id}/status')
async def update_order_status(order_id: str, status: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can update order status')
    
    order = await db.orders.find_one({'id': order_id})
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    
    has_item = any(item['chef_id'] == current_user['id'] for item in order['items'])
    if not has_item:
        raise HTTPException(status_code=403, detail='Access denied')
    
    await db.orders.update_one({'id': order_id}, {'$set': {'status': status}})
    return {'message': 'Order status updated'}

# ======================
# PAYMENT ENDPOINTS
# ======================

@api_router.post('/checkout', response_model=CheckoutSessionResponse)
async def create_checkout(checkout_data: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'customer':
        raise HTTPException(status_code=403, detail='Only customers can checkout')
    
    # Get order
    order = await db.orders.find_one({'id': checkout_data.order_id, 'customer_id': current_user['id']})
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    
    if order['payment_status'] == 'paid':
        raise HTTPException(status_code=400, detail='Order already paid')
    
    # Create success and cancel URLs
    success_url = f"{checkout_data.origin_url}/order-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_data.origin_url}/checkout?order_id={checkout_data.order_id}"
    
    # Initialize Stripe
    webhook_url = f"{checkout_data.origin_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(order['total_amount']),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'order_id': checkout_data.order_id,
            'customer_id': current_user['id'],
            'customer_email': current_user['email']
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction_doc = {
        'session_id': session.session_id,
        'order_id': checkout_data.order_id,
        'customer_id': current_user['id'],
        'amount': float(order['total_amount']),
        'currency': 'usd',
        'payment_status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction_doc)
    
    # Update order with session_id
    await db.orders.update_one({'id': checkout_data.order_id}, {'$set': {'session_id': session.session_id}})
    
    return session

@api_router.get('/checkout/status/{session_id}', response_model=CheckoutStatusResponse)
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    # Get transaction
    transaction = await db.payment_transactions.find_one({'session_id': session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail='Transaction not found')
    
    # If already paid, return cached status
    if transaction.get('payment_status') == 'paid':
        return CheckoutStatusResponse(
            status='complete',
            payment_status='paid',
            amount_total=int(transaction['amount'] * 100),
            currency=transaction['currency'],
            metadata=transaction.get('metadata', {})
        )
    
    # Check with Stripe
    webhook_url = f"{os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction and order if paid
    if checkout_status.payment_status == 'paid' and transaction.get('payment_status') != 'paid':
        await db.payment_transactions.update_one(
            {'session_id': session_id},
            {'$set': {'payment_status': 'paid', 'status': 'complete'}}
        )
        await db.orders.update_one(
            {'session_id': session_id},
            {'$set': {'payment_status': 'paid', 'status': 'confirmed'}}
        )
    
    return checkout_status

@api_router.post('/webhook/stripe')
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get('Stripe-Signature')
    
    webhook_url = f"{os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction and order
        if webhook_response.payment_status == 'paid':
            await db.payment_transactions.update_one(
                {'session_id': webhook_response.session_id},
                {'$set': {'payment_status': 'paid', 'status': 'complete'}}
            )
            await db.orders.update_one(
                {'session_id': webhook_response.session_id},
                {'$set': {'payment_status': 'paid', 'status': 'confirmed'}}
            )
        
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ======================
# REVIEWS
# ======================

@api_router.post('/reviews', response_model=Review)
async def create_review(review_data: ReviewCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'customer':
        raise HTTPException(status_code=403, detail='Only customers can create reviews')
    
    # Check if order exists and is delivered
    order = await db.orders.find_one({'id': review_data.order_id, 'customer_id': current_user['id']})
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    
    # Check if review already exists
    existing = await db.reviews.find_one({'order_id': review_data.order_id, 'customer_id': current_user['id']})
    if existing:
        raise HTTPException(status_code=400, detail='Review already submitted')
    
    review_id = f"review_{datetime.now(timezone.utc).timestamp()}"
    review_doc = {
        'id': review_id,
        'customer_id': current_user['id'],
        'customer_name': current_user['name'],
        **review_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    await db.reviews.insert_one(review_doc)
    return Review(**{k: v for k, v in review_doc.items() if k != '_id'})

@api_router.get('/reviews/chef/{chef_id}', response_model=List[Review])
async def get_chef_reviews(chef_id: str):
    reviews = await db.reviews.find({'chef_id': chef_id}, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [Review(**review) for review in reviews]

# ======================
# CHEF EARNINGS
# ======================

@api_router.get('/chef/earnings')
async def get_chef_earnings(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'chef':
        raise HTTPException(status_code=403, detail='Only chefs can access earnings')
    
    # Get all paid orders containing chef's items
    orders = await db.orders.find(
        {'items.chef_id': current_user['id'], 'payment_status': 'paid'},
        {'_id': 0}
    ).to_list(1000)
    
    total_earnings = 0.0
    total_orders = len(orders)
    
    for order in orders:
        # Calculate earnings from this order (only chef's items)
        for item in order['items']:
            if item['chef_id'] == current_user['id']:
                total_earnings += item['price'] * item['quantity']
    
    # Get average rating
    reviews = await db.reviews.find({'chef_id': current_user['id']}, {'_id': 0}).to_list(1000)
    avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
    
    return {
        'total_earnings': round(total_earnings, 2),
        'total_orders': total_orders,
        'average_rating': round(avg_rating, 1),
        'total_reviews': len(reviews)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
