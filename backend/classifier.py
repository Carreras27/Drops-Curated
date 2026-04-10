"""
Product Classification Service using Gemini Flash LLM
Batch API approach - classifies multiple products in single API calls for efficiency
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


# ============ BATCH API CLASSIFICATION ============

async def classify_batch_with_gemini(products: List[Dict]) -> List[Dict]:
    """
    Classify multiple products in a SINGLE API call using Gemini Flash.
    This is the batch approach - sends up to 20 products at once.
    
    Returns list of classification results in same order as input.
    """
    if not products:
        return []
    
    try:
        # Initialize Gemini chat with batch-optimized settings
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"batch_classify_{datetime.now().timestamp()}",
            system_message="""You are a streetwear product classifier. You will receive a batch of products and must classify ALL of them.
Respond with a JSON array containing classification for each product in the EXACT same order as received.
Be concise. Respond ONLY with valid JSON array, no markdown, no explanation."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Build batch items for the prompt
        batch_items = []
        for i, p in enumerate(products):
            batch_items.append({
                "idx": i,
                "title": p.get('name', ''),
                "brand": p.get('brand', ''),
                "category": p.get('category', '')
            })
        
        # Build the prompt
        prompt = f"""Classify these {len(products)} streetwear products. Return a JSON array with one object per product.

Products to classify:
{json.dumps(batch_items, indent=2)}

For EACH product, return this exact format in the array:
{{
    "idx": <same index as input>,
    "gender": "Men" or "Women" or "Unisex",
    "category": "SHOES" or "CLOTHES" or "ACCESSORIES" or "COLLECTABLES",
    "subcategory": one of [{', '.join(SUBCATEGORY_TYPES[:10])}...],
    "brand": "detected brand or use provided brand",
    "confidence": 0.0 to 1.0
}}

Classification Rules:
- (W) or Women's or wmns = "Women"
- (M) or Men's = "Men"  
- Otherwise = "Unisex"
- sneakers/shoes/slides/boots = "SHOES"
- hoodie/tee/jacket/pants = "CLOTHES"
- cap/bag/wallet/socks = "ACCESSORIES"
- bearbrick/figure/lego = "COLLECTABLES"

Return ONLY the JSON array, nothing else."""

        # Send to LLM
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        response_text = response.strip()
        
        # Clean up response if it has markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        results = json.loads(response_text)
        
        # Validate it's an array
        if not isinstance(results, list):
            raise ValueError("Response is not an array")
        
        # Create a map by index for quick lookup
        results_map = {r.get('idx', i): r for i, r in enumerate(results)}
        
        # Map results back to products in correct order
        classified = []
        for i, product in enumerate(products):
            result = results_map.get(i, {})
            
            # Validate and normalize
            gender = result.get('gender', 'Unisex')
            if gender not in ['Men', 'Women', 'Unisex']:
                gender = 'Unisex'
                
            category = result.get('category', product.get('category', 'CLOTHES'))
            if category not in ['SHOES', 'CLOTHES', 'ACCESSORIES', 'COLLECTABLES']:
                category = product.get('category', 'CLOTHES')
            
            classified.append({
                'gender': gender,
                'category': category,
                'subcategory': result.get('subcategory', 'Other'),
                'brand': result.get('brand', product.get('brand', '')),
                'confidence': min(1.0, max(0.0, float(result.get('confidence', 0.8))))
            })
        
        logger.info(f"[Batch API] Successfully classified {len(products)} products in single call")
        return classified
        
    except json.JSONDecodeError as e:
        logger.warning(f"[Batch API] JSON parse error: {e}")
        # Fall back to rule-based for all products
        return [fallback_classification(p.get('name', ''), p.get('brand', ''), p.get('category', '')) for p in products]
    except Exception as e:
        logger.error(f"[Batch API] Error: {e}")
        # Fall back to rule-based for all products
        return [fallback_classification(p.get('name', ''), p.get('brand', ''), p.get('category', '')) for p in products]


async def classify_product_with_llm(
    title: str, 
    description: str = "", 
    existing_brand: str = "",
    existing_category: str = ""
) -> Dict:
    """
    Classify a SINGLE product with Gemini Flash (for real-time new product classification).
    For batch processing, use classify_batch_with_gemini instead.
    """
    try:
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"classify_{hash(title) % 100000}",
            system_message="""You are a streetwear product classifier. Given a product title, classify it accurately. 
Be concise and respond ONLY with valid JSON."""
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
- Detect brand from title first, fallback to store brand"""

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


# ============ EFFICIENT BATCH PROCESSING ============

async def classify_products_batch(products: List[Dict], batch_size: int = 15) -> List[Dict]:
    """
    Classify multiple products using BATCH API approach.
    
    - Sends up to `batch_size` products in a SINGLE API call
    - Much more efficient than 1-by-1 API calls
    - Automatically falls back to rule-based if API fails
    
    Args:
        products: List of products to classify
        batch_size: Products per API call (max 20 recommended for Gemini)
        
    Returns:
        List of classified products with AI fields added
    """
    classified = []
    total = len(products)
    
    logger.info(f"[Batch Processing] Starting classification of {total} products with batch_size={batch_size}")
    
    for i in range(0, total, batch_size):
        batch = products[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info(f"[Batch {batch_num}/{total_batches}] Processing {len(batch)} products...")
        
        # Get batch classifications in SINGLE API call
        classifications = await classify_batch_with_gemini(batch)
        
        # Combine products with their classifications
        for j, (product, classification) in enumerate(zip(batch, classifications)):
            normalized_title = clean_product_title(product.get('name', ''))
            
            classified.append({
                **product,
                'normalizedTitle': normalized_title,
                'aiGender': classification['gender'],
                'aiCategory': classification['category'],
                'aiSubcategory': classification.get('subcategory', 'Other'),
                'aiBrand': classification['brand'],
                'aiConfidence': classification['confidence'],
                'classifiedAt': datetime.now(timezone.utc).isoformat()
            })
        
        # Small delay between batches to respect rate limits
        if i + batch_size < total:
            await asyncio.sleep(0.5)  # 500ms between batches
    
    logger.info(f"[Batch Processing] Complete! Classified {len(classified)} products")
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


async def update_products_bulk(db, classified_products: List[Dict]) -> Dict:
    """
    Bulk update multiple products in MongoDB using bulk_write for efficiency.
    """
    from pymongo import UpdateOne
    
    if not classified_products:
        return {'updated': 0, 'errors': 0}
    
    operations = []
    for product in classified_products:
        operations.append(
            UpdateOne(
                {'id': product['id']},
                {'$set': {
                    'normalizedTitle': product.get('normalizedTitle'),
                    'aiGender': product.get('aiGender'),
                    'aiCategory': product.get('aiCategory'),
                    'aiSubcategory': product.get('aiSubcategory'),
                    'aiBrand': product.get('aiBrand'),
                    'aiConfidence': product.get('aiConfidence'),
                    'classifiedAt': product.get('classifiedAt')
                }}
            )
        )
    
    try:
        result = await db.products.bulk_write(operations, ordered=False)
        return {
            'updated': result.modified_count,
            'matched': result.matched_count,
            'errors': len(classified_products) - result.matched_count
        }
    except Exception as e:
        logger.error(f"Bulk update error: {e}")
        return {'updated': 0, 'errors': len(classified_products), 'error_msg': str(e)}


async def run_batch_classification(db, limit: int = None, skip_classified: bool = True, batch_size: int = 15) -> Dict:
    """
    Run batch classification on all products in the database.
    
    Uses efficient batch API approach:
    - Sends multiple products per API call
    - Bulk writes to MongoDB
    - Progress tracking
    
    Args:
        db: Database instance
        limit: Max products to process (None = all)
        skip_classified: Skip already classified products
        batch_size: Products per API call (default 15)
        
    Returns:
        Statistics about the classification run
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
    
    logger.info(f"[Run Batch] Starting classification of {total} products with batch_size={batch_size}")
    start_time = datetime.now()
    
    # Process in mega-batches for database writes (100 products at a time for DB)
    db_batch_size = 100
    total_success = 0
    total_errors = 0
    
    for i in range(0, total, db_batch_size):
        mega_batch = products[i:i + db_batch_size]
        
        # Classify this mega-batch (will internally use API batch_size)
        classified_products = await classify_products_batch(mega_batch, batch_size=batch_size)
        
        # Bulk write to database
        result = await update_products_bulk(db, classified_products)
        total_success += result.get('updated', 0)
        total_errors += result.get('errors', 0)
        
        # Progress update
        processed = min(i + db_batch_size, total)
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        
        logger.info(f"[Progress] {processed}/{total} ({processed/total*100:.1f}%) | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    stats = {
        'total': total,
        'classified': total_success,
        'errors': total_errors,
        'elapsed_seconds': round(elapsed, 2),
        'products_per_second': round(total / elapsed, 2) if elapsed > 0 else 0,
        'batch_size': batch_size,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"[Complete] Classification finished: {stats}")
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


async def classify_new_products_batch(db, products: List[Dict]) -> List[Dict]:
    """
    Classify multiple newly scraped products using batch API.
    More efficient than classifying one-by-one.
    """
    if not products:
        return []
    
    # Classify using batch API
    classified = await classify_products_batch(products, batch_size=min(15, len(products)))
    
    # Bulk update to database
    await update_products_bulk(db, classified)
    
    return classified


# ============ CLASSIFIER FEEDBACK LOOP ============

async def record_classification_feedback(
    db,
    product_id: str,
    feedback_type: str,  # 'correct', 'wrong_category', 'wrong_gender', 'wrong_brand'
    correct_value: str = None,
    user_id: str = None
) -> bool:
    """
    Record user feedback on AI classification.
    This allows the system to learn from corrections.
    """
    try:
        feedback_doc = {
            'product_id': product_id,
            'feedback_type': feedback_type,
            'correct_value': correct_value,
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.classification_feedback.insert_one(feedback_doc)
        
        # If wrong, update the product with correct value
        if feedback_type != 'correct' and correct_value:
            update_field = {
                'wrong_category': 'aiCategory',
                'wrong_gender': 'aiGender',
                'wrong_brand': 'aiBrand',
                'wrong_subcategory': 'aiSubcategory'
            }.get(feedback_type)
            
            if update_field:
                await db.products.update_one(
                    {'id': product_id},
                    {
                        '$set': {
                            update_field: correct_value,
                            'aiConfidence': 1.0,  # Human-corrected = 100% confidence
                            'humanCorrected': True,
                            'correctedAt': datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"[Feedback] Corrected {product_id}: {update_field} = {correct_value}")
        
        return True
    except Exception as e:
        logger.error(f"[Feedback] Error recording feedback: {e}")
        return False


async def get_classification_accuracy(db) -> Dict:
    """
    Calculate classification accuracy based on feedback.
    """
    try:
        total_feedback = await db.classification_feedback.count_documents({})
        correct_count = await db.classification_feedback.count_documents({'feedback_type': 'correct'})
        
        pipeline = [
            {'$group': {'_id': '$feedback_type', 'count': {'$sum': 1}}}
        ]
        breakdown = await db.classification_feedback.aggregate(pipeline).to_list(100)
        
        accuracy = (correct_count / total_feedback * 100) if total_feedback > 0 else 0
        
        return {
            'total_feedback': total_feedback,
            'correct': correct_count,
            'accuracy_percentage': round(accuracy, 2),
            'breakdown': {item['_id']: item['count'] for item in breakdown}
        }
    except Exception as e:
        logger.error(f"[Feedback] Error calculating accuracy: {e}")
        return {'error': str(e)}


async def get_products_needing_review(db, limit: int = 20) -> List[Dict]:
    """
    Get products with low confidence that need human review.
    """
    try:
        query = {
            'aiConfidence': {'$lt': 0.7, '$exists': True},
            'humanCorrected': {'$ne': True}
        }
        
        products = await db.products.find(
            query, 
            {'_id': 0, 'id': 1, 'name': 1, 'brand': 1, 'aiGender': 1, 'aiCategory': 1, 'aiSubcategory': 1, 'aiConfidence': 1, 'imageUrl': 1}
        ).sort('aiConfidence', 1).limit(limit).to_list(limit)
        
        return products
    except Exception as e:
        logger.error(f"[Feedback] Error getting products for review: {e}")
        return []


async def get_classification_stats(db) -> Dict:
    """
    Get statistics about product classifications.
    """
    try:
        total_products = await db.products.count_documents({})
        classified = await db.products.count_documents({'aiGender': {'$exists': True}})
        unclassified = total_products - classified
        
        # Get category breakdown
        category_pipeline = [
            {'$match': {'aiCategory': {'$exists': True}}},
            {'$group': {'_id': '$aiCategory', 'count': {'$sum': 1}}}
        ]
        categories = await db.products.aggregate(category_pipeline).to_list(10)
        
        # Get gender breakdown
        gender_pipeline = [
            {'$match': {'aiGender': {'$exists': True}}},
            {'$group': {'_id': '$aiGender', 'count': {'$sum': 1}}}
        ]
        genders = await db.products.aggregate(gender_pipeline).to_list(5)
        
        return {
            'total_products': total_products,
            'classified': classified,
            'unclassified': unclassified,
            'percentage_classified': round(classified / total_products * 100, 2) if total_products > 0 else 0,
            'by_category': {item['_id']: item['count'] for item in categories},
            'by_gender': {item['_id']: item['count'] for item in genders}
        }
    except Exception as e:
        logger.error(f"Error getting classification stats: {e}")
        return {'error': str(e)}
