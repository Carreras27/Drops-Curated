"""
Real-time web scraper for Indian e-commerce sites
Uses Playwright for bot protection bypass
"""

import asyncio
from playwright.async_api import async_playwright
import random
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re

# User agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

class AmazonInScraper:
    """Scraper for Amazon.in"""
    
    async def scrape_search(self, query: str, max_products: int = 10):
        """Search and scrape products from Amazon.in"""
        products = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to Amazon.in search
                search_url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
                print(f"🔍 Scraping Amazon: {search_url}")
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Extract product cards
                product_cards = await page.query_selector_all('[data-component-type="s-search-result"]')
                
                for card in product_cards[:max_products]:
                    try:
                        # Extract name
                        name_elem = await card.query_selector('h2 a span')
                        name = await name_elem.inner_text() if name_elem else None
                        
                        # Extract price
                        price_elem = await card.query_selector('.a-price-whole')
                        price_text = await price_elem.inner_text() if price_elem else None
                        price = float(re.sub(r'[^0-9]', '', price_text)) if price_text else 0
                        
                        # Extract image
                        img_elem = await card.query_selector('img.s-image')
                        image_url = await img_elem.get_attribute('src') if img_elem else None
                        
                        # Extract URL
                        link_elem = await card.query_selector('h2 a')
                        product_url = await link_elem.get_attribute('href') if link_elem else None
                        if product_url and not product_url.startswith('http'):
                            product_url = f"https://www.amazon.in{product_url}"
                        
                        # Extract rating
                        rating_elem = await card.query_selector('[aria-label*="out of 5 stars"]')
                        rating_text = await rating_elem.get_attribute('aria-label') if rating_elem else None
                        
                        if name and price > 0:
                            products.append({
                                'name': name.strip(),
                                'brand': self._extract_brand(name),
                                'price': price,
                                'image_url': image_url,
                                'product_url': product_url,
                                'store': 'AMAZON_IN',
                                'in_stock': True,
                                'rating': rating_text,
                                'scraped_at': datetime.now(timezone.utc).isoformat()
                            })
                            print(f"  ✓ Found: {name[:50]}... - ₹{price}")
                    
                    except Exception as e:
                        print(f"  ✗ Error parsing card: {e}")
                        continue
                
            except Exception as e:
                print(f"❌ Amazon scraping error: {e}")
            
            finally:
                await browser.close()
        
        return products
    
    def _extract_brand(self, name: str) -> str:
        """Extract brand from product name"""
        brands = ['Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance', 'Asics', 
                  'Skechers', 'Crocs', 'Clarks', 'Woodland', 'Red Tape',
                  'H&M', 'Zara', 'Levi', 'Wrangler', 'UCB', 'Allen Solly']
        
        name_upper = name.upper()
        for brand in brands:
            if brand.upper() in name_upper:
                return brand
        
        return name.split()[0] if name else 'Unknown'


class FlipkartScraper:
    """Scraper for Flipkart"""
    
    async def scrape_search(self, query: str, max_products: int = 10):
        """Search and scrape products from Flipkart"""
        products = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '%20')}"
                print(f"🔍 Scraping Flipkart: {search_url}")
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Flipkart uses different selectors
                product_cards = await page.query_selector_all('[data-id]')
                
                for card in product_cards[:max_products]:
                    try:
                        # Extract name
                        name_elem = await card.query_selector('a[title]')
                        name = await name_elem.get_attribute('title') if name_elem else None
                        
                        # Extract price
                        price_elem = await card.query_selector('div._30jeq3')
                        price_text = await price_elem.inner_text() if price_elem else None
                        price = float(re.sub(r'[^0-9]', '', price_text)) if price_text else 0
                        
                        # Extract image
                        img_elem = await card.query_selector('img')
                        image_url = await img_elem.get_attribute('src') if img_elem else None
                        
                        # Extract URL
                        link_elem = await card.query_selector('a')
                        product_url = await link_elem.get_attribute('href') if link_elem else None
                        if product_url and not product_url.startswith('http'):
                            product_url = f"https://www.flipkart.com{product_url}"
                        
                        if name and price > 0:
                            products.append({
                                'name': name.strip(),
                                'brand': self._extract_brand(name),
                                'price': price,
                                'image_url': image_url,
                                'product_url': product_url,
                                'store': 'FLIPKART',
                                'in_stock': True,
                                'scraped_at': datetime.now(timezone.utc).isoformat()
                            })
                            print(f"  ✓ Found: {name[:50]}... - ₹{price}")
                    
                    except Exception as e:
                        continue
                
            except Exception as e:
                print(f"❌ Flipkart scraping error: {e}")
            
            finally:
                await browser.close()
        
        return products
    
    def _extract_brand(self, name: str) -> str:
        """Extract brand from product name"""
        brands = ['Nike', 'Adidas', 'Puma', 'Reebok', 'H&M', 'Zara']
        name_upper = name.upper()
        for brand in brands:
            if brand.upper() in name_upper:
                return brand
        return name.split()[0] if name else 'Unknown'


async def scrape_and_update_db(query: str, category: str = 'SHOES'):
    """
    Scrape products from multiple stores and update database
    """
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'indiashop_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"\n🚀 Starting real-time scraping for: {query}")
    print("=" * 60)
    
    # Scrape from both stores
    amazon_scraper = AmazonInScraper()
    flipkart_scraper = FlipkartScraper()
    
    amazon_products = await amazon_scraper.scrape_search(query, max_products=5)
    flipkart_products = await flipkart_scraper.scrape_search(query, max_products=5)
    
    all_scraped = amazon_products + flipkart_products
    
    print(f"\n📊 Scraped {len(all_scraped)} products total")
    
    # Update database
    products_added = 0
    prices_added = 0
    
    for scraped in all_scraped:
        # Create product
        product_id = f"prod_scraped_{scraped['store']}_{hash(scraped['name']) % 10000}"
        
        # Check if product exists
        existing = await db.products.find_one({'name': scraped['name'], 'brand': scraped['brand']})
        
        if not existing:
            product_doc = {
                'id': product_id,
                'name': scraped['name'],
                'slug': scraped['name'].lower().replace(' ', '-')[:50],
                'brand': scraped['brand'],
                'category': category,
                'description': f"{scraped['brand']} product from {scraped['store']}",
                'imageUrl': scraped['image_url'] or 'https://via.placeholder.com/500',
                'additionalImages': [],
                'attributes': {},
                'tags': [category.lower(), 'shoes', 'footwear', scraped['brand'].lower()],
                'isActive': True,
                'isTrending': False,
                'createdAt': datetime.now(timezone.utc).isoformat()
            }
            
            await db.products.insert_one(product_doc)
            products_added += 1
        else:
            product_id = existing['id']
        
        # Add price
        price_id = f"price_{product_id}_{scraped['store']}_{int(datetime.now(timezone.utc).timestamp())}"
        price_doc = {
            'id': price_id,
            'productId': product_id,
            'store': scraped['store'],
            'productUrl': scraped['product_url'],
            'currentPrice': scraped['price'],
            'inStock': scraped['in_stock'],
            'lastScrapedAt': scraped['scraped_at'],
            'createdAt': scraped['scraped_at']
        }
        
        await db.prices.insert_one(price_doc)
        prices_added += 1
    
    client.close()
    
    print(f"\n✅ Database updated!")
    print(f"  • Products added: {products_added}")
    print(f"  • Prices added: {prices_added}")
    print("=" * 60)
    
    return {
        'scraped': len(all_scraped),
        'products_added': products_added,
        'prices_added': prices_added
    }


if __name__ == "__main__":
    # Test scraping
    result = asyncio.run(scrape_and_update_db("nike shoes", "SHOES"))
    print(f"\n✅ Scraping complete: {result}")
