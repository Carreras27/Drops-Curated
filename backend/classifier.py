"""
Product Classification Service using Gemini LLM
Normalizes product titles and classifies them by Gender, Category, and Brand
"""
import re
import os
import json
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Emergent LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Emergent LLM Key
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY', os.getenv('OPENAI_API_KEY'))

# ============ DATA CLEANING FUNCTIONS ============

def clean_product_title(title: str) -> str:
    """
    Normalize product title by:
    - Removing punctuation (brackets, dashes, special chars)
    - Converting to lowercase
    - Stripping noise words
    - Removing extra whitespace
    """
    if not title:
        return ""
    
    # Convert to lowercase
    cleaned = title.lower()
    
    # Remove content in brackets/parentheses but keep the content
    cleaned = re.sub(r'[\[\]\(\)\{\}]', ' ', cleaned)
    
    # Remove special characters but keep spaces and alphanumeric
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    
    # Remove noise words that don't add value
    noise_words = [
        'new', 'latest', 'exclusive', 'limited', 'edition', 'special',
        'sale', 'offer', 'discount', 'free', 'shipping', 'available',
        'stock', 'only', 'left', 'pairs', 'pieces', 'units',
        'prepaid', 'orders', 'cod', 'delivery'
    ]
    words = cleaned.split()
    words = [w for w in words if w not in noise_words]
    
    # Rejoin and clean up whitespace
    cleaned = ' '.join(words)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


# ============ LLM CLASSIFICATION ============

# Known streetwear brands for better accuracy
KNOWN_BRANDS = [
    "Nike", "Adidas", "Jordan", "Air Jordan", "Yeezy", "New Balance", "Puma", "Reebok",
    "Crep Dog Crew", "Capsul", "Urban Monkey", "Huemn", "Superkicks", "Mainstreet",
    "Bluorng", "House of Koala", "Farak", "Evemen", "Void Worldwide", "Almost Gods",
    "Jaywalking", "Code Brown", "Noughtone", "Hiyest", "Veg Non Veg", "Culture Circle",
    "Toffle", "Leave The Rest", "Deadbear", "Natty Garb", "Bomaachi",
    "Stussy", "Supreme", "Off-White", "Palace", "BAPE", "Fear of God", "Essentials",
    "Palm Angels", "Represent", "Amiri", "Rhude", "Gallery Dept", "Chrome Hearts",
    "ON", "ON Running", "ASICS", "Converse", "Vans", "Saucony", "Hoka", "Salomon",
    "Lego", "Bearbrick", "Funko", "Medicom", "Kaws"
]

# Category mappings
CATEGORY_MAPPINGS = {
    "sneakers": "SHOES",
    "shoes": "SHOES",
    "trainers": "SHOES",
    "boots": "SHOES",
    "slides": "SHOES",
    "sandals": "SHOES",
    "slippers": "SHOES",
    "hoodie": "CLOTHES",
    "hoodies": "CLOTHES",
    "sweatshirt": "CLOTHES",
    "t-shirt": "CLOTHES",
    "tee": "CLOTHES",
    "shirt": "CLOTHES",
    "jacket": "CLOTHES",
    "pants": "CLOTHES",
    "shorts": "CLOTHES",
    "joggers": "CLOTHES",
    "trousers": "CLOTHES",
    "jeans": "CLOTHES",
    "dress": "CLOTHES",
    "skirt": "CLOTHES",
    "sweater": "CLOTHES",
    "cardigan": "CLOTHES",
    "coat": "CLOTHES",
    "vest": "CLOTHES",
    "cap": "ACCESSORIES",
    "hat": "ACCESSORIES",
    "bag": "ACCESSORIES",
    "backpack": "ACCESSORIES",
    "wallet": "ACCESSORIES",
    "belt": "ACCESSORIES",
    "socks": "ACCESSORIES",
    "watch": "ACCESSORIES",
    "jewelry": "ACCESSORIES",
    "sunglasses": "ACCESSORIES",
    "glasses": "ACCESSORIES",
    "mask": "ACCESSORIES",
    "scarf": "ACCESSORIES",
    "gloves": "ACCESSORIES",
    "bearbrick": "COLLECTABLES",
    "figure": "COLLECTABLES",
    "figurine": "COLLECTABLES",
    "toy": "COLLECTABLES",
    "lego": "COLLECTABLES",
    "funko": "COLLECTABLES",
    "collectible": "COLLECTABLES",
    "collectable": "COLLECTABLES"
}

# Subcategory for more specific filtering
SUBCATEGORY_TYPES = [
    "Sneakers", "Slides", "Boots", "Sandals",  # Footwear
    "T-Shirt", "Hoodie", "Sweatshirt", "Jacket", "Shirt", "Polo",  # Tops
    "Pants", "Shorts", "Joggers", "Jeans", "Trousers",  # Bottoms
    "Cap", "Hat", "Bag", "Backpack", "Wallet", "Socks", "Belt",  # Accessories
    "Bearbrick", "Figure", "Lego Set", "Collectible"  # Collectables
]


async def classify_product_with_llm(
    title: str, 
    description: str = "", 
    existing_brand: str = "",
    existing_category: str = ""
) -> Dict:
    """
    Use Gemini LLM to classify a product.
    Returns: {gender, category, subcategory, brand, confidence}
    """
    try:
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"classify_{hash(title) % 100000}",
            system_message="""You are a streetwear product classifier. Given a product title and optional description, 
classify it accurately. Be concise and respond ONLY with valid JSON."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Build the prompt
        prompt = f"""Classify this streetwear product:

Title: {title}
{f'Description: {description}' if description else ''}
{f'Store Brand: {existing_brand}' if existing_brand else ''}

Respond with ONLY this JSON format (no markdown, no explanation):
{{
    "gender": "Men" or "Women" or "Unisex",
    "category": "SHOES" or "CLOTHES" or "ACCESSORIES" or "COLLECTABLES",
    "subcategory": one of [{', '.join(SUBCATEGORY_TYPES)}],
    "brand": "detected brand name or '{existing_brand}' if unclear",
    "confidence": 0.0 to 1.0
}}

Rules:
- If title contains (W) or Women's or female sizing, gender is "Women"
- If title contains (M) or Men's, gender is "Men"
- If unclear, default to "Unisex"
- Detect brand from title first, fallback to store brand
- Match subcategory to the most specific type"""

        # Send to LLM
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        response_text = response.strip()
        
        # Clean up response if it has markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        result = json.loads(response_text)
        
        # Validate and normalize
        result['gender'] = result.get('gender', 'Unisex')
        if result['gender'] not in ['Men', 'Women', 'Unisex']:
            result['gender'] = 'Unisex'
            
        result['category'] = result.get('category', existing_category or 'CLOTHES')
        if result['category'] not in ['SHOES', 'CLOTHES', 'ACCESSORIES', 'COLLECTABLES']:
            result['category'] = existing_category or 'CLOTHES'
            
        result['brand'] = result.get('brand', existing_brand) or existing_brand
        result['confidence'] = min(1.0, max(0.0, float(result.get('confidence', 0.7))))
        
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error for '{title}': {e}")
        return fallback_classification(title, existing_brand, existing_category)
    except Exception as e:
        logger.error(f"LLM classification error for '{title}': {e}")
        return fallback_classification(title, existing_brand, existing_category)


def fallback_classification(title: str, existing_brand: str = "", existing_category: str = "") -> Dict:
    """
    Fallback rule-based classification when LLM fails.
    """
    title_lower = title.lower()
    
    # Detect gender
    gender = "Unisex"
    if "(w)" in title_lower or "women" in title_lower or "wmns" in title_lower:
        gender = "Women"
    elif "(m)" in title_lower or " men " in title_lower or "mens" in title_lower:
        gender = "Men"
    
    # Detect category
    category = existing_category or "CLOTHES"
    subcategory = None
    for keyword, cat in CATEGORY_MAPPINGS.items():
        if keyword in title_lower:
            category = cat
            subcategory = keyword.title()
            break
    
    # Detect brand
    brand = existing_brand
    for known_brand in KNOWN_BRANDS:
        if known_brand.lower() in title_lower:
            brand = known_brand
            break
    
    return {
        "gender": gender,
        "category": category,
        "subcategory": subcategory or "Other",
        "brand": brand,
        "confidence": 0.5  # Lower confidence for fallback
    }


async def classify_product(product: Dict) -> Dict:
    """
    Main classification function for a single product.
    Returns product with added classification fields.
    """
    title = product.get('name', '')
    description = product.get('description', '')
    existing_brand = product.get('brand', '')
    existing_category = product.get('category', '')
    
    # Clean the title
    normalized_title = clean_product_title(title)
    
    # Get LLM classification
    classification = await classify_product_with_llm(
        title, description, existing_brand, existing_category
    )
    
    # Add classification fields to product
    return {
        **product,
        'normalizedTitle': normalized_title,
        'aiGender': classification['gender'],
        'aiCategory': classification['category'],
        'aiSubcategory': classification.get('subcategory', 'Other'),
        'aiBrand': classification['brand'],
        'aiConfidence': classification['confidence'],
        'classifiedAt': datetime.now(timezone.utc).isoformat()
    }


# ============ BATCH PROCESSING ============

async def classify_products_batch(products: List[Dict], batch_size: int = 10) -> List[Dict]:
    """
    Classify multiple products in batches with rate limiting.
    """
    classified = []
    total = len(products)
    
    for i in range(0, total, batch_size):
        batch = products[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")
        
        # Process batch concurrently
        tasks = [classify_product(p) for p in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for j, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error classifying product: {result}")
                # Use fallback for failed products
                classified.append({
                    **batch[j],
                    'normalizedTitle': clean_product_title(batch[j].get('name', '')),
                    'aiGender': 'Unisex',
                    'aiCategory': batch[j].get('category', 'CLOTHES'),
                    'aiSubcategory': 'Other',
                    'aiBrand': batch[j].get('brand', ''),
                    'aiConfidence': 0.0,
                    'classifiedAt': datetime.now(timezone.utc).isoformat()
                })
            else:
                classified.append(result)
        
        # Rate limiting: wait between batches
        if i + batch_size < total:
            await asyncio.sleep(1)  # 1 second between batches
    
    return classified


# ============ DATABASE OPERATIONS ============

async def update_product_classification(db, product_id: str, classification: Dict) -> bool:
    """
    Update a single product with classification data in MongoDB.
    """
    try:
        result = await db.products.update_one(
            {'id': product_id},
            {'$set': {
                'normalizedTitle': classification.get('normalizedTitle'),
                'aiGender': classification.get('aiGender'),
                'aiCategory': classification.get('aiCategory'),
                'aiSubcategory': classification.get('aiSubcategory'),
                'aiBrand': classification.get('aiBrand'),
                'aiConfidence': classification.get('aiConfidence'),
                'classifiedAt': classification.get('classifiedAt')
            }}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return False


async def run_batch_classification(db, limit: int = None, skip_classified: bool = True) -> Dict:
    """
    Run batch classification on all products in the database.
    Returns statistics about the classification run.
    """
    # Build query
    query = {}
    if skip_classified:
        query['aiGender'] = {'$exists': False}
    
    # Get products to classify
    cursor = db.products.find(query, {'_id': 0})
    if limit:
        cursor = cursor.limit(limit)
    
    products = await cursor.to_list(length=limit or 100000)
    total = len(products)
    
    if total == 0:
        return {'total': 0, 'classified': 0, 'errors': 0, 'message': 'No products to classify'}
    
    logger.info(f"Starting classification of {total} products...")
    
    # Classify in batches
    classified_products = await classify_products_batch(products, batch_size=5)
    
    # Update database
    success_count = 0
    error_count = 0
    
    for product in classified_products:
        if await update_product_classification(db, product['id'], product):
            success_count += 1
        else:
            error_count += 1
    
    stats = {
        'total': total,
        'classified': success_count,
        'errors': error_count,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Classification complete: {stats}")
    return stats


# ============ REAL-TIME CLASSIFICATION FOR NEW PRODUCTS ============

async def classify_new_product(db, product: Dict) -> Dict:
    """
    Classify a newly scraped product and save to database.
    Used by scrapers for real-time classification.
    """
    classified = await classify_product(product)
    
    # Update or insert the product with classification
    await db.products.update_one(
        {'id': classified['id']},
        {'$set': classified},
        upsert=True
    )
    
    return classified
