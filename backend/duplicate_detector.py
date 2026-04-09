"""
Duplicate Product Detector
Prevents duplicate products from being added to the database.
Duplicate = Same product name + brand
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def normalize_product_name(name: str) -> str:
    """
    Normalize product name for comparison:
    - Lowercase
    - Remove special characters
    - Remove extra whitespace
    - Remove common noise words
    """
    if not name:
        return ""
    
    # Lowercase
    normalized = name.lower()
    
    # Remove content in brackets but keep it for comparison
    normalized = re.sub(r'[\[\]\(\)\{\}]', ' ', normalized)
    
    # Remove special characters
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Remove noise words
    noise_words = ['new', 'latest', 'exclusive', 'limited', 'edition', 'special', 
                   'sale', 'offer', 'discount', 'the', 'a', 'an']
    words = normalized.split()
    words = [w for w in words if w not in noise_words]
    
    # Rejoin and clean whitespace
    normalized = ' '.join(words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def normalize_brand(brand: str) -> str:
    """Normalize brand name for comparison"""
    if not brand:
        return ""
    return brand.lower().strip()

def generate_product_hash(name: str, brand: str) -> str:
    """Generate a unique hash for product name + brand combination"""
    normalized_name = normalize_product_name(name)
    normalized_brand = normalize_brand(brand)
    
    # Create a hash key
    combined = f"{normalized_brand}::{normalized_name}"
    return combined

def is_duplicate(product1: Dict, product2: Dict) -> bool:
    """
    Check if two products are duplicates.
    Duplicate = Same normalized name + same normalized brand
    """
    hash1 = generate_product_hash(product1.get('name', ''), product1.get('brand', ''))
    hash2 = generate_product_hash(product2.get('name', ''), product2.get('brand', ''))
    
    return hash1 == hash2

async def check_duplicate_in_db(db, name: str, brand: str, store: str = None) -> Tuple[bool, Optional[Dict]]:
    """
    Check if a product already exists in the database.
    Returns (is_duplicate, existing_product)
    """
    # First check: exact name + brand match
    query = {
        'name': name,
        'brand': brand
    }
    
    existing = await db.products.find_one(query, {'_id': 0})
    if existing:
        return True, existing
    
    # Second check: normalized name + brand match
    normalized_name = normalize_product_name(name)
    normalized_brand = normalize_brand(brand)
    
    # Check against normalizedTitle if it exists
    query2 = {
        '$or': [
            {'normalizedTitle': normalized_name, 'brand': {'$regex': f'^{normalized_brand}$', '$options': 'i'}},
            {'normalizedTitle': normalized_name, 'aiBrand': {'$regex': f'^{normalized_brand}$', '$options': 'i'}}
        ]
    }
    
    existing2 = await db.products.find_one(query2, {'_id': 0})
    if existing2:
        return True, existing2
    
    return False, None

async def filter_duplicates(db, products: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter out duplicate products from a list.
    Returns (unique_products, duplicate_products)
    """
    unique = []
    duplicates = []
    seen_hashes = set()
    
    for product in products:
        product_hash = generate_product_hash(product.get('name', ''), product.get('brand', ''))
        
        # Check against products in this batch
        if product_hash in seen_hashes:
            duplicates.append({
                'product': product,
                'reason': 'duplicate_in_batch'
            })
            continue
        
        # Check against database
        is_dup, existing = await check_duplicate_in_db(
            db, 
            product.get('name', ''), 
            product.get('brand', ''),
            product.get('store', '')
        )
        
        if is_dup:
            duplicates.append({
                'product': product,
                'reason': 'exists_in_db',
                'existing_id': existing.get('id') if existing else None
            })
            continue
        
        # Not a duplicate
        seen_hashes.add(product_hash)
        unique.append(product)
    
    if duplicates:
        logger.info(f"[DuplicateDetector] Filtered {len(duplicates)} duplicates from {len(products)} products")
    
    return unique, duplicates

async def merge_duplicate_prices(db, product_id: str, new_price_data: Dict) -> bool:
    """
    If a duplicate is found, merge the price data instead of creating new product.
    This allows tracking prices from multiple stores for the same product.
    """
    try:
        # Add or update price entry
        await db.prices.update_one(
            {
                'productId': product_id,
                'store': new_price_data.get('store')
            },
            {'$set': {
                'currentPrice': new_price_data.get('price'),
                'originalPrice': new_price_data.get('original_price', new_price_data.get('price')),
                'productUrl': new_price_data.get('product_url', ''),
                'lastScrapedAt': datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"[DuplicateDetector] Error merging prices: {e}")
        return False

class DuplicateStats:
    """Track duplicate detection statistics"""
    
    def __init__(self):
        self.total_processed = 0
        self.duplicates_found = 0
        self.unique_added = 0
        self.prices_merged = 0
    
    def record(self, processed: int, duplicates: int, unique: int, merged: int = 0):
        self.total_processed += processed
        self.duplicates_found += duplicates
        self.unique_added += unique
        self.prices_merged += merged
    
    def to_dict(self) -> Dict:
        return {
            'total_processed': self.total_processed,
            'duplicates_found': self.duplicates_found,
            'unique_added': self.unique_added,
            'prices_merged': self.prices_merged,
            'duplicate_rate': round((self.duplicates_found / self.total_processed * 100) if self.total_processed > 0 else 0, 2)
        }

# Global stats tracker
duplicate_stats = DuplicateStats()
