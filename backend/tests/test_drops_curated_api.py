"""
Drops Curated API Tests
Tests for: search, products, subscribe, scrape status endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSearchAPI:
    """Search endpoint tests - /api/search"""
    
    def test_search_empty_query_returns_products(self):
        """GET /api/search?q= should return all products"""
        response = requests.get(f"{BASE_URL}/api/search?q=&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert 'total' in data
        assert isinstance(data['products'], list)
        assert len(data['products']) > 0
        # Verify product structure
        product = data['products'][0]
        assert 'id' in product
        assert 'name' in product
        assert 'brand' in product
        assert 'imageUrl' in product
        print(f"✓ Empty query returned {len(data['products'])} products, total: {data['total']}")
    
    def test_search_with_query_filters_products(self):
        """GET /api/search?q=nike should filter products"""
        response = requests.get(f"{BASE_URL}/api/search?q=nike&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        # All returned products should match the query
        for product in data['products']:
            product_text = f"{product['name']} {product['brand']} {product.get('description', '')}".lower()
            # At least one field should contain 'nike'
            assert 'nike' in product_text or len(data['products']) == 0
        print(f"✓ Search 'nike' returned {len(data['products'])} products")
    
    def test_search_with_category_filter(self):
        """GET /api/search?category=SHOES should filter by category"""
        response = requests.get(f"{BASE_URL}/api/search?q=&category=SHOES&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        for product in data['products']:
            assert product['category'] == 'SHOES'
        print(f"✓ Category filter returned {len(data['products'])} SHOES products")
    
    def test_search_pagination(self):
        """GET /api/search with page parameter should paginate"""
        response1 = requests.get(f"{BASE_URL}/api/search?q=&limit=5&page=1")
        response2 = requests.get(f"{BASE_URL}/api/search?q=&limit=5&page=2")
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        # Pages should have different products
        ids1 = [p['id'] for p in data1['products']]
        ids2 = [p['id'] for p in data2['products']]
        assert ids1 != ids2 or data1['total'] <= 5
        print(f"✓ Pagination works: page1={len(ids1)} items, page2={len(ids2)} items")
    
    def test_search_returns_price_data(self):
        """Products should include price data"""
        response = requests.get(f"{BASE_URL}/api/search?q=&limit=5")
        assert response.status_code == 200
        data = response.json()
        for product in data['products']:
            assert 'lowestPrice' in product
            assert 'highestPrice' in product
            assert isinstance(product['lowestPrice'], (int, float))
        print(f"✓ Products include price data")


class TestProductDetailAPI:
    """Product detail endpoint tests - /api/products/{id}"""
    
    def test_get_product_by_id(self):
        """GET /api/products/{id} should return product with prices"""
        # First get a product ID from search
        search_resp = requests.get(f"{BASE_URL}/api/search?q=&limit=1")
        assert search_resp.status_code == 200
        products = search_resp.json()['products']
        if not products:
            pytest.skip("No products in database")
        
        product_id = products[0]['id']
        response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert 'product' in data
        assert 'prices' in data
        assert data['product']['id'] == product_id
        assert isinstance(data['prices'], list)
        print(f"✓ Product {product_id} returned with {len(data['prices'])} price sources")
    
    def test_get_product_not_found(self):
        """GET /api/products/invalid_id should return 404"""
        response = requests.get(f"{BASE_URL}/api/products/nonexistent_product_12345")
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        print(f"✓ Invalid product ID returns 404")
    
    def test_product_prices_structure(self):
        """Product prices should have correct structure"""
        search_resp = requests.get(f"{BASE_URL}/api/search?q=&limit=1")
        products = search_resp.json()['products']
        if not products:
            pytest.skip("No products in database")
        
        product_id = products[0]['id']
        response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        data = response.json()
        
        if data['prices']:
            price = data['prices'][0]
            assert 'currentPrice' in price
            assert 'store' in price
            assert 'inStock' in price
            print(f"✓ Price structure is correct: store={price['store']}, price={price['currentPrice']}")
        else:
            print(f"✓ Product has no prices (acceptable)")


# NOTE: Old /api/subscribe endpoint replaced with OTP-based flow
# See test_otp_payment_partner.py for new subscription tests


class TestScrapeStatusAPI:
    """Scrape status endpoint tests - /api/scrape/status"""
    
    def test_scrape_status_returns_brands(self):
        """GET /api/scrape/status should return brand data"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        data = response.json()
        
        assert 'brands' in data
        assert 'total_products' in data
        assert 'total_prices' in data
        assert 'available_scrapers' in data
        
        assert isinstance(data['brands'], list)
        assert data['total_products'] > 0
        print(f"✓ Scrape status: {len(data['brands'])} brands, {data['total_products']} products")
    
    def test_scrape_status_brand_structure(self):
        """Brand data should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        data = response.json()
        
        if data['brands']:
            brand = data['brands'][0]
            assert 'key' in brand
            assert 'name' in brand
            assert 'productCount' in brand
            assert 'isActive' in brand
            print(f"✓ Brand structure correct: {brand['name']} ({brand['productCount']} products)")


class TestTrendingAPI:
    """Trending products endpoint tests - /api/trending"""
    
    def test_trending_products(self):
        """GET /api/trending should return trending products"""
        response = requests.get(f"{BASE_URL}/api/trending?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert isinstance(data['products'], list)
        print(f"✓ Trending endpoint returned {len(data['products'])} products")


class TestBrandsAPI:
    """Brands endpoint tests - /api/brands"""
    
    def test_get_brands(self):
        """GET /api/brands should return active brands"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        data = response.json()
        assert 'brands' in data
        assert isinstance(data['brands'], list)
        print(f"✓ Brands endpoint returned {len(data['brands'])} brands")


class TestSubscriberCountAPI:
    """Subscriber count endpoint tests - /api/subscribers/count"""
    
    def test_subscriber_count(self):
        """GET /api/subscribers/count should return count"""
        response = requests.get(f"{BASE_URL}/api/subscribers/count")
        assert response.status_code == 200
        data = response.json()
        assert 'count' in data
        assert isinstance(data['count'], int)
        print(f"✓ Subscriber count: {data['count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
