import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

# Sample products data
SAMPLE_PRODUCTS = [
    # Nike Shoes
    {
        'id': 'prod_001',
        'name': 'Nike Air Max 270',
        'slug': 'nike-air-max-270',
        'brand': 'Nike',
        'category': 'SHOES',
        'gender': 'UNISEX',
        'description': 'The Nike Air Max 270 features Nike\'s biggest heel Air unit yet for a super-soft ride.',
        'imageUrl': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['7', '8', '9', '10', '11'], 'colors': ['Black', 'White', 'Blue']},
        'tags': ['sneakers', 'trending', 'nike'],
        'priceRange': 'PREMIUM',
        'isActive': True,
        'isTrending': True,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    {
        'id': 'prod_002',
        'name': 'Nike React Infinity Run',
        'slug': 'nike-react-infinity-run',
        'brand': 'Nike',
        'category': 'SHOES',
        'gender': 'UNISEX',
        'description': 'Designed to help reduce injury and keep you on the run.',
        'imageUrl': 'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['7', '8', '9', '10', '11'], 'colors': ['Black', 'White']},
        'tags': ['running', 'sports', 'nike'],
        'priceRange': 'PREMIUM',
        'isActive': True,
        'isTrending': False,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    
    # Adidas Shoes
    {
        'id': 'prod_003',
        'name': 'Adidas Ultraboost 22',
        'slug': 'adidas-ultraboost-22',
        'brand': 'Adidas',
        'category': 'SHOES',
        'gender': 'UNISEX',
        'description': 'Made with Primeblue, a high-performance recycled material.',
        'imageUrl': 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['7', '8', '9', '10', '11'], 'colors': ['Black', 'White', 'Grey']},
        'tags': ['running', 'sustainable', 'adidas'],
        'priceRange': 'PREMIUM',
        'isActive': True,
        'isTrending': True,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    
    # Veg Non Veg Streetwear
    {
        'id': 'prod_004',
        'name': 'VNV Classic Hoodie',
        'slug': 'vnv-classic-hoodie',
        'brand': 'Veg Non Veg',
        'category': 'CLOTHES',
        'gender': 'UNISEX',
        'description': 'Premium oversized hoodie with VNV signature branding.',
        'imageUrl': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Black', 'Grey']},
        'tags': ['streetwear', 'hoodie', 'vegnon veg', 'indian'],
        'priceRange': 'MID_RANGE',
        'isActive': True,
        'isTrending': True,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    {
        'id': 'prod_005',
        'name': 'VNV Graphic Tee',
        'slug': 'vnv-graphic-tee',
        'brand': 'Veg Non Veg',
        'category': 'CLOTHES',
        'gender': 'UNISEX',
        'description': 'Limited edition graphic t-shirt from Indian streetwear brand.',
        'imageUrl': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Black', 'White']},
        'tags': ['streetwear', 'tshirt', 'limited-edition'],
        'priceRange': 'BUDGET',
        'isActive': True,
        'isTrending': False,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    
    # Cosmetics
    {
        'id': 'prod_006',
        'name': 'Maybelline Superstay Matte Ink',
        'slug': 'maybelline-superstay-matte-ink',
        'brand': 'Maybelline',
        'category': 'COSMETICS',
        'gender': 'WOMEN',
        'description': 'Liquid lipstick with up to 16 hours of wear.',
        'imageUrl': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500',
        'additionalImages': [],
        'attributes': {'shades': ['Voyager', 'Pioneer', 'Lover'], 'finish': 'Matte'},
        'tags': ['lipstick', 'makeup', 'long-lasting'],
        'priceRange': 'BUDGET',
        'isActive': True,
        'isTrending': True,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    
    # More Streetwear
    {
        'id': 'prod_007',
        'name': 'Culture Circle Cargo Pants',
        'slug': 'culture-circle-cargo-pants',
        'brand': 'Culture Circle',
        'category': 'CLOTHES',
        'gender': 'UNISEX',
        'description': 'Utility cargo pants with multiple pockets.',
        'imageUrl': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['28', '30', '32', '34'], 'colors': ['Black', 'Olive', 'Khaki']},
        'tags': ['streetwear', 'pants', 'cargo', 'indian'],
        'priceRange': 'MID_RANGE',
        'isActive': True,
        'isTrending': True,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
    {
        'id': 'prod_008',
        'name': 'Super Kicks High Top',
        'slug': 'super-kicks-high-top',
        'brand': 'Super Kicks',
        'category': 'SHOES',
        'gender': 'UNISEX',
        'description': 'Classic high top sneakers from Indian brand.',
        'imageUrl': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500',
        'additionalImages': [],
        'attributes': {'sizes': ['7', '8', '9', '10', '11'], 'colors': ['White', 'Black']},
        'tags': ['sneakers', 'high-top', 'streetwear'],
        'priceRange': 'MID_RANGE',
        'isActive': True,
        'isTrending': False,
        'createdAt': datetime.now(timezone.utc).isoformat()
    },
]

# Sample prices for products
SAMPLE_PRICES = [
    # Nike Air Max 270 prices
    {'id': 'price_001', 'productId': 'prod_001', 'store': 'AMAZON_IN', 'productUrl': 'https://amazon.in', 'currentPrice': 12995, 'originalPrice': 14995, 'discountPercent': 13, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    {'id': 'price_002', 'productId': 'prod_001', 'store': 'FLIPKART', 'productUrl': 'https://flipkart.com', 'currentPrice': 12499, 'originalPrice': 14995, 'discountPercent': 17, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    {'id': 'price_003', 'productId': 'prod_001', 'store': 'MYNTRA', 'productUrl': 'https://myntra.com', 'currentPrice': 13495, 'originalPrice': 14995, 'discountPercent': 10, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # Nike React prices
    {'id': 'price_004', 'productId': 'prod_002', 'store': 'AMAZON_IN', 'productUrl': 'https://amazon.in', 'currentPrice': 10995, 'originalPrice': 12995, 'discountPercent': 15, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    {'id': 'price_005', 'productId': 'prod_002', 'store': 'FLIPKART', 'productUrl': 'https://flipkart.com', 'currentPrice': 10499, 'originalPrice': 12995, 'discountPercent': 19, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # Adidas Ultraboost prices
    {'id': 'price_006', 'productId': 'prod_003', 'store': 'AMAZON_IN', 'productUrl': 'https://amazon.in', 'currentPrice': 15995, 'originalPrice': 17999, 'discountPercent': 11, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    {'id': 'price_007', 'productId': 'prod_003', 'store': 'MYNTRA', 'productUrl': 'https://myntra.com', 'currentPrice': 16495, 'originalPrice': 17999, 'discountPercent': 8, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # VNV Hoodie prices
    {'id': 'price_008', 'productId': 'prod_004', 'store': 'VEG_NON_VEG', 'productUrl': 'https://vegnonveg.com', 'currentPrice': 3499, 'originalPrice': 4999, 'discountPercent': 30, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # VNV Tee prices
    {'id': 'price_009', 'productId': 'prod_005', 'store': 'VEG_NON_VEG', 'productUrl': 'https://vegnonveg.com', 'currentPrice': 1499, 'originalPrice': 1999, 'discountPercent': 25, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # Maybelline prices
    {'id': 'price_010', 'productId': 'prod_006', 'store': 'NYKAA', 'productUrl': 'https://nykaa.com', 'currentPrice': 599, 'originalPrice': 799, 'discountPercent': 25, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    {'id': 'price_011', 'productId': 'prod_006', 'store': 'AMAZON_IN', 'productUrl': 'https://amazon.in', 'currentPrice': 549, 'originalPrice': 799, 'discountPercent': 31, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # Culture Circle prices
    {'id': 'price_012', 'productId': 'prod_007', 'store': 'CULTURE_CIRCLE', 'productUrl': 'https://culturecircle.in', 'currentPrice': 2999, 'originalPrice': 3999, 'discountPercent': 25, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
    
    # Super Kicks prices
    {'id': 'price_013', 'productId': 'prod_008', 'store': 'SUPER_KICKS', 'productUrl': 'https://superkicks.in', 'currentPrice': 4499, 'originalPrice': 5999, 'discountPercent': 25, 'inStock': True, 'lastScrapedAt': datetime.now(timezone.utc).isoformat(), 'createdAt': datetime.now(timezone.utc).isoformat()},
]

async def seed_database():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'indiashop_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Starting database seed...")
    
    # Clear existing data
    await db.products.delete_many({})
    await db.prices.delete_many({})
    print("✓ Cleared existing data")
    
    # Insert products
    await db.products.insert_many(SAMPLE_PRODUCTS)
    print(f"✓ Inserted {len(SAMPLE_PRODUCTS)} products")
    
    # Insert prices
    await db.prices.insert_many(SAMPLE_PRICES)
    print(f"✓ Inserted {len(SAMPLE_PRICES)} prices")
    
    print("✅ Database seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
