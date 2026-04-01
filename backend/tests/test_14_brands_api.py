"""
Test suite for Drops Curated - 14 Brands API Testing
Tests all 14 brands: Crep Dog Crew, Almost Gods, Code Brown, Jaywalking, Huemn, 
Noughtone, Bluorng, Capsul, Urban Monkey, House of Koala, Farak, Hiyest, 
Veg Non Veg, Culture Circle
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# All 14 brands with their expected store keys
EXPECTED_BRANDS = [
    {"key": "crepdog_crew", "name": "Crep Dog Crew", "store_key": "CREPDOG_CREW"},
    {"key": "almost_gods", "name": "Almost Gods", "store_key": "ALMOST_GODS"},
    {"key": "code_brown", "name": "Code Brown", "store_key": "CODE_BROWN"},
    {"key": "jaywalking", "name": "Jaywalking", "store_key": "JAYWALKING"},
    {"key": "huemn", "name": "Huemn", "store_key": "HUEMN"},
    {"key": "noughtone", "name": "Noughtone", "store_key": "NOUGHTONE"},
    {"key": "bluorng", "name": "Bluorng", "store_key": "BLUORNG"},
    {"key": "capsul", "name": "Capsul", "store_key": "CAPSUL"},
    {"key": "urban_monkey", "name": "Urban Monkey", "store_key": "URBAN_MONKEY"},
    {"key": "house_of_koala", "name": "House of Koala", "store_key": "HOUSE_OF_KOALA"},
    {"key": "farak", "name": "Farak", "store_key": "FARAK"},
    {"key": "hiyest", "name": "Hiyest", "store_key": "HIYEST"},
    {"key": "veg_non_veg", "name": "Veg Non Veg", "store_key": "VEG_NON_VEG"},
    {"key": "culture_circle", "name": "Culture Circle", "store_key": "CULTURE_CIRCLE"},
]


class TestScrapeStatus:
    """Test /api/scrape/status endpoint for 14 brands"""
    
    def test_scrape_status_returns_14_brands(self):
        """Verify scrape status returns all 14 brands"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        brands = data.get("brands", [])
        
        # Should have 14 brands
        assert len(brands) == 14, f"Expected 14 brands, got {len(brands)}"
        
        # Verify all expected brand keys are present
        brand_keys = {b["key"] for b in brands}
        expected_keys = {b["key"] for b in EXPECTED_BRANDS}
        assert brand_keys == expected_keys, f"Missing brands: {expected_keys - brand_keys}"
        
        print(f"✓ All 14 brands present: {sorted(brand_keys)}")
    
    def test_scrape_status_product_counts(self):
        """Verify each brand has product counts"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        brands = data.get("brands", [])
        
        for brand in brands:
            assert "productCount" in brand, f"Brand {brand['key']} missing productCount"
            assert brand["productCount"] > 0, f"Brand {brand['key']} has 0 products"
            print(f"  {brand['name']}: {brand['productCount']} products")
        
        total = data.get("total_products", 0)
        assert total >= 4900, f"Expected 4900+ products, got {total}"
        print(f"✓ Total products: {total}")
    
    def test_scrape_status_available_scrapers(self):
        """Verify all 14 scrapers are available"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        scrapers = set(data.get("available_scrapers", []))
        expected = {b["key"] for b in EXPECTED_BRANDS}
        
        assert scrapers == expected, f"Missing scrapers: {expected - scrapers}"
        print(f"✓ All 14 scrapers available")


class TestBrandSearch:
    """Test search functionality for each brand"""
    
    @pytest.mark.parametrize("brand_name,expected_store", [
        ("huemn", "HUEMN"),
        ("urban monkey", "URBAN_MONKEY"),
        ("farak", "FARAK"),
        ("almost gods", "ALMOST_GODS"),
        ("code brown", "CODE_BROWN"),
        ("jaywalking", "JAYWALKING"),
        ("noughtone", "NOUGHTONE"),
        ("bluorng", "BLUORNG"),
        ("capsul", "CAPSUL"),
        ("house of koala", "HOUSE_OF_KOALA"),
        ("hiyest", "HIYEST"),
        ("veg non veg", "VEG_NON_VEG"),
        ("culture circle", "CULTURE_CIRCLE"),
        ("crep dog crew", "CREPDOG_CREW"),
    ])
    def test_search_by_brand_name(self, brand_name, expected_store):
        """Search for each brand returns relevant products"""
        response = requests.get(f"{BASE_URL}/api/search", params={"q": brand_name, "limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        
        # Should return some products
        assert len(products) > 0, f"No products found for brand: {brand_name}"
        
        # At least some products should match the brand
        matching = [p for p in products if expected_store in p.get("store", "") or 
                   brand_name.lower() in p.get("brand", "").lower() or
                   brand_name.lower() in p.get("name", "").lower() or
                   brand_name.lower() in str(p.get("tags", [])).lower()]
        
        assert len(matching) > 0, f"No matching products for {brand_name}"
        print(f"✓ {brand_name}: {len(products)} results, {len(matching)} matching")


class TestCrossBrandSearch:
    """Test cross-brand search functionality"""
    
    def test_search_jacket_returns_multiple_brands(self):
        """Search for 'jacket' returns products from multiple brands"""
        response = requests.get(f"{BASE_URL}/api/search", params={"q": "jacket", "limit": 30})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        
        assert len(products) > 0, "No jacket products found"
        
        # Get unique stores
        stores = set(p.get("store", "") for p in products)
        print(f"✓ 'jacket' search: {len(products)} products from {len(stores)} stores: {stores}")
        
        # Should have products from multiple stores
        assert len(stores) >= 2, f"Expected products from multiple stores, got {stores}"
    
    def test_empty_search_returns_multiple_brands(self):
        """Empty search returns products from multiple brands"""
        response = requests.get(f"{BASE_URL}/api/search", params={"q": "", "limit": 60})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        total = data.get("total", 0)
        
        assert len(products) == 60, f"Expected 60 products, got {len(products)}"
        assert total >= 4900, f"Expected 4900+ total products, got {total}"
        
        # Get unique brands
        brands = set(p.get("brand", "") for p in products)
        print(f"✓ Empty search: {len(products)} products, {total} total, {len(brands)} unique brands")
    
    def test_search_tshirt_returns_results(self):
        """Search for 't-shirt' returns products"""
        response = requests.get(f"{BASE_URL}/api/search", params={"q": "t-shirt", "limit": 20})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        
        assert len(products) > 0, "No t-shirt products found"
        print(f"✓ 't-shirt' search: {len(products)} products")
    
    def test_search_hoodie_returns_results(self):
        """Search for 'hoodie' returns products"""
        response = requests.get(f"{BASE_URL}/api/search", params={"q": "hoodie", "limit": 20})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        
        assert len(products) > 0, "No hoodie products found"
        print(f"✓ 'hoodie' search: {len(products)} products")


class TestProductDetail:
    """Test product detail page for products from new brands"""
    
    def test_product_from_huemn(self):
        """Get product detail for a Huemn product"""
        # First search for a Huemn product
        search_resp = requests.get(f"{BASE_URL}/api/search", params={"q": "huemn", "limit": 1})
        assert search_resp.status_code == 200
        
        products = search_resp.json().get("products", [])
        if not products:
            pytest.skip("No Huemn products found")
        
        product_id = products[0]["id"]
        
        # Get product detail
        detail_resp = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert detail_resp.status_code == 200
        
        data = detail_resp.json()
        assert "product" in data
        assert "prices" in data
        print(f"✓ Huemn product detail: {data['product']['name']}")
    
    def test_product_from_urban_monkey(self):
        """Get product detail for an Urban Monkey product"""
        search_resp = requests.get(f"{BASE_URL}/api/search", params={"q": "urban monkey", "limit": 1})
        assert search_resp.status_code == 200
        
        products = search_resp.json().get("products", [])
        if not products:
            pytest.skip("No Urban Monkey products found")
        
        product_id = products[0]["id"]
        
        detail_resp = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert detail_resp.status_code == 200
        
        data = detail_resp.json()
        assert "product" in data
        print(f"✓ Urban Monkey product detail: {data['product']['name']}")
    
    def test_product_from_farak(self):
        """Get product detail for a Farak product"""
        search_resp = requests.get(f"{BASE_URL}/api/search", params={"q": "farak", "limit": 1})
        assert search_resp.status_code == 200
        
        products = search_resp.json().get("products", [])
        if not products:
            pytest.skip("No Farak products found")
        
        product_id = products[0]["id"]
        
        detail_resp = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert detail_resp.status_code == 200
        
        data = detail_resp.json()
        assert "product" in data
        print(f"✓ Farak product detail: {data['product']['name']}")


class TestSubscriptionFlow:
    """Test subscription flow still works"""
    
    def test_otp_send(self):
        """Test OTP send endpoint"""
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": "9876543210"})
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "sandbox_otp" in data  # Sandbox mode returns OTP
        print(f"✓ OTP sent: {data.get('sandbox_otp')}")
    
    def test_otp_verify(self):
        """Test OTP verify endpoint"""
        # First send OTP
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": "9876543211"})
        assert send_resp.status_code == 200
        otp = send_resp.json().get("sandbox_otp")
        
        # Verify OTP
        verify_resp = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": "9876543211", "otp": otp})
        assert verify_resp.status_code == 200
        
        data = verify_resp.json()
        assert data.get("verified") == True
        print(f"✓ OTP verified")
    
    def test_payment_create_order(self):
        """Test payment order creation"""
        # First verify phone
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": "9876543212"})
        otp = send_resp.json().get("sandbox_otp")
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": "9876543212", "otp": otp})
        
        # Create order
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": "9876543212",
            "name": "Test User",
            "plan": "monthly"
        })
        assert order_resp.status_code == 200
        
        data = order_resp.json()
        assert "order_id" in data
        assert data.get("sandbox") == True
        print(f"✓ Payment order created: {data.get('order_id')}")
    
    def test_full_subscription_flow(self):
        """Test complete subscription flow"""
        phone = "9876543213"
        
        # 1. Send OTP
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        assert send_resp.status_code == 200
        otp = send_resp.json().get("sandbox_otp")
        
        # 2. Verify OTP
        verify_resp = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        assert verify_resp.status_code == 200
        
        # 3. Create order
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": "Test Subscriber",
            "plan": "monthly"
        })
        assert order_resp.status_code == 200
        order_id = order_resp.json().get("order_id")
        
        # 4. Verify payment (sandbox auto-approves)
        payment_resp = requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": phone,
            "order_id": order_id,
            "payment_id": "pay_sandbox_test",
            "signature": "sig_sandbox_test"
        })
        assert payment_resp.status_code == 200
        
        data = payment_resp.json()
        assert data.get("success") == True
        assert "membership_id" in data
        print(f"✓ Full subscription flow complete: {data.get('membership_id')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
