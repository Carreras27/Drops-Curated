"""
Final Pre-Launch Test Suite for Drops Curated
Tests all critical APIs and flows before going live.
"""
import pytest
import requests
import os
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://drops-curated.preview.emergentagent.com').rstrip('/')

class TestHealthAndStatus:
    """Health check and status endpoints"""
    
    def test_scrape_status_returns_17_brands(self):
        """Verify 17 brands are being tracked"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        data = response.json()
        assert 'brands' in data
        assert len(data['brands']) == 17, f"Expected 17 brands, got {len(data['brands'])}"
        assert data['total_products'] > 9000, f"Expected 9000+ products, got {data['total_products']}"
        print(f"✓ 17 brands tracked, {data['total_products']} products")
    
    def test_scheduler_status_shows_next_run(self):
        """Verify scheduler is configured with next_run"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert 'next_run' in data
        assert data['next_run'] is not None, "Scheduler next_run should be set"
        assert data['interval_minutes'] == 15
        print(f"✓ Scheduler active, next run: {data['next_run']}")


class TestProductsAPI:
    """Product search and listing endpoints"""
    
    def test_search_returns_products(self):
        """GET /api/search returns products"""
        response = requests.get(f"{BASE_URL}/api/search?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert len(data['products']) > 0
        assert 'total' in data
        print(f"✓ Search returns {len(data['products'])} products, total: {data['total']}")
    
    def test_search_with_query(self):
        """Search with query parameter"""
        response = requests.get(f"{BASE_URL}/api/search?q=nike&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        print(f"✓ Search 'nike' returns {len(data['products'])} products")
    
    def test_product_has_price_data(self):
        """Products should have price data"""
        response = requests.get(f"{BASE_URL}/api/search?limit=5")
        assert response.status_code == 200
        data = response.json()
        for product in data['products']:
            assert 'lowestPrice' in product
            assert 'highestPrice' in product
            assert 'priceCount' in product
        print("✓ Products have price data")


class TestSubscriptionFlow:
    """Full subscription flow: OTP -> Payment -> Preferences"""
    
    @pytest.fixture
    def test_phone(self):
        return f"98765{random.randint(10000, 99999)}"
    
    def test_otp_send(self, test_phone):
        """POST /api/otp/send sends OTP"""
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'sandbox_otp' in data  # Sandbox mode returns OTP
        print(f"✓ OTP sent to {test_phone}, sandbox OTP: {data['sandbox_otp']}")
        return data['sandbox_otp']
    
    def test_otp_verify(self, test_phone):
        """POST /api/otp/verify verifies OTP"""
        # First send OTP
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        otp = send_resp.json()['sandbox_otp']
        
        # Then verify
        response = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": test_phone, "otp": otp})
        assert response.status_code == 200
        data = response.json()
        assert data['verified'] == True
        print(f"✓ OTP verified for {test_phone}")
    
    def test_payment_create_order(self, test_phone):
        """POST /api/payment/create-order creates order"""
        # First verify phone
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        otp = send_resp.json()['sandbox_otp']
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": test_phone, "otp": otp})
        
        # Create order
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": test_phone,
            "name": "Test User",
            "plan": "monthly"
        })
        assert response.status_code == 200
        data = response.json()
        assert 'order_id' in data
        assert data['amount'] == 39900  # ₹399 in paise
        assert data['sandbox'] == True
        print(f"✓ Order created: {data['order_id']}")
        return data['order_id']
    
    def test_payment_verify(self, test_phone):
        """POST /api/payment/verify verifies payment"""
        # Setup: send OTP, verify, create order
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        otp = send_resp.json()['sandbox_otp']
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": test_phone, "otp": otp})
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": test_phone,
            "name": "Test User",
            "plan": "monthly"
        })
        order_id = order_resp.json()['order_id']
        
        # Verify payment
        response = requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": test_phone,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        })
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'membership_id' in data
        assert 'expires_at' in data
        print(f"✓ Payment verified, membership: {data['membership_id']}")
        return data


class TestPreferencesAPI:
    """User preferences endpoints"""
    
    @pytest.fixture
    def setup_subscriber(self):
        """Create a verified subscriber for testing"""
        phone = f"98765{random.randint(10000, 99999)}"
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = send_resp.json()['sandbox_otp']
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        return phone
    
    def test_save_preferences(self, setup_subscriber):
        """POST /api/preferences saves correctly"""
        phone = setup_subscriber
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": phone,
            "brands": ["CREPDOG_CREW", "HUEMN"],
            "alert_types": ["price_drop", "new_release"],
            "categories": ["garments", "sneakers"],
            "sizes": ["M", "L", "UK9"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Preferences updated'
        print(f"✓ Preferences saved for {phone}")
    
    def test_get_preferences(self, setup_subscriber):
        """GET /api/preferences/{phone} returns saved preferences"""
        phone = setup_subscriber
        # First save
        requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": phone,
            "brands": ["SUPERKICKS"],
            "alert_types": ["price_drop"],
            "categories": ["sneakers"],
            "sizes": ["UK10"]
        })
        
        # Then get
        response = requests.get(f"{BASE_URL}/api/preferences/{phone}")
        assert response.status_code == 200
        data = response.json()
        assert 'preferences' in data
        assert data['preferences']['brands'] == ["SUPERKICKS"]
        assert data['preferences']['sizes'] == ["UK10"]
        print(f"✓ Preferences retrieved for {phone}")


class TestWalletAPI:
    """Wallet pass generation endpoints"""
    
    def test_apple_wallet_returns_info(self):
        """POST /api/wallet/apple returns info message (not configured)"""
        response = requests.post(f"{BASE_URL}/api/wallet/apple", json={
            "phone": "9876543210",
            "name": "Test User",
            "membership_id": "DC-202604-12345",
            "expires_at": "2026-05-01T00:00:00Z"
        })
        assert response.status_code == 200
        data = response.json()
        assert 'configured' in data
        assert data['configured'] == False
        assert 'message' in data
        assert 'requirements' in data
        print(f"✓ Apple Wallet API returns info: {data['message'][:50]}...")
    
    def test_google_wallet_returns_info(self):
        """POST /api/wallet/google returns info message (not configured)"""
        response = requests.post(f"{BASE_URL}/api/wallet/google", json={
            "phone": "9876543210",
            "name": "Test User",
            "membership_id": "DC-202604-12345",
            "expires_at": "2026-05-01T00:00:00Z"
        })
        assert response.status_code == 200
        data = response.json()
        assert 'configured' in data
        assert data['configured'] == False
        assert 'message' in data
        print(f"✓ Google Wallet API returns info: {data['message'][:50]}...")


class TestBrandsAPI:
    """Brands endpoint"""
    
    def test_brands_endpoint(self):
        """GET /api/brands returns active brands"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        data = response.json()
        assert 'brands' in data
        print(f"✓ Brands endpoint returns {len(data['brands'])} brands")


class TestPartnerInquiry:
    """Partner inquiry endpoint"""
    
    def test_partner_inquiry(self):
        """POST /api/partner-inquiry creates inquiry"""
        response = requests.post(f"{BASE_URL}/api/partner-inquiry", json={
            "brand": "Test Brand",
            "contact": "Test Contact",
            "email": "test@example.com",
            "message": "Test inquiry"
        })
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'created'
        print("✓ Partner inquiry created")


class TestInputValidation:
    """Input validation tests"""
    
    def test_invalid_phone_rejected(self):
        """Invalid phone number is rejected"""
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": "12345"})
        assert response.status_code == 400
        print("✓ Invalid phone rejected")
    
    def test_invalid_otp_rejected(self):
        """Invalid OTP is rejected"""
        phone = f"98765{random.randint(10000, 99999)}"
        requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        response = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": "000000"})
        assert response.status_code == 400
        print("✓ Invalid OTP rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
