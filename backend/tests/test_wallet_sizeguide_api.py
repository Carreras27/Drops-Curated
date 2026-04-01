"""
Test Suite for Wallet API and Size Guide Features
Tests:
- POST /api/wallet/apple - Apple Wallet pass generation
- POST /api/wallet/google - Google Wallet pass generation
- Full subscription flow with wallet buttons
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWalletAPI:
    """Test Apple and Google Wallet API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_phone = "9876543230"
        self.test_name = "Test Wallet User"
        self.test_membership_id = f"DC-{datetime.now().strftime('%Y%m')}-99999"
        self.test_expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    
    def test_apple_wallet_endpoint_exists(self):
        """Test that Apple Wallet endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/apple",
            json={
                "phone": self.test_phone,
                "name": self.test_name,
                "membership_id": self.test_membership_id,
                "expires_at": self.test_expires_at
            }
        )
        # Should return 200 with info message (not configured)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "configured" in data, "Response should have 'configured' field"
        assert "message" in data, "Response should have 'message' field"
        print(f"Apple Wallet response: {data}")
    
    def test_apple_wallet_not_configured_response(self):
        """Test Apple Wallet returns proper 'not configured' message"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/apple",
            json={
                "phone": self.test_phone,
                "name": self.test_name,
                "membership_id": self.test_membership_id,
                "expires_at": self.test_expires_at
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should indicate not configured
        assert data.get("configured") == False, "Apple Wallet should not be configured"
        assert "certificate" in data.get("message", "").lower() or "apple" in data.get("message", "").lower(), \
            "Message should mention certificates or Apple"
        
        # Should have requirements list
        if "requirements" in data:
            assert isinstance(data["requirements"], list), "Requirements should be a list"
            print(f"Apple Wallet requirements: {data['requirements']}")
    
    def test_google_wallet_endpoint_exists(self):
        """Test that Google Wallet endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/google",
            json={
                "phone": self.test_phone,
                "name": self.test_name,
                "membership_id": self.test_membership_id,
                "expires_at": self.test_expires_at
            }
        )
        # Should return 200 with info message (not configured)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "configured" in data, "Response should have 'configured' field"
        assert "message" in data, "Response should have 'message' field"
        print(f"Google Wallet response: {data}")
    
    def test_google_wallet_not_configured_response(self):
        """Test Google Wallet returns proper 'not configured' message"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/google",
            json={
                "phone": self.test_phone,
                "name": self.test_name,
                "membership_id": self.test_membership_id,
                "expires_at": self.test_expires_at
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should indicate not configured
        assert data.get("configured") == False, "Google Wallet should not be configured"
        assert "google" in data.get("message", "").lower() or "cloud" in data.get("message", "").lower(), \
            "Message should mention Google or Cloud"
        
        # Should have requirements list
        if "requirements" in data:
            assert isinstance(data["requirements"], list), "Requirements should be a list"
            print(f"Google Wallet requirements: {data['requirements']}")
    
    def test_apple_wallet_validates_input(self):
        """Test Apple Wallet validates required fields"""
        # Missing required fields
        response = requests.post(
            f"{BASE_URL}/api/wallet/apple",
            json={}
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
    
    def test_google_wallet_validates_input(self):
        """Test Google Wallet validates required fields"""
        # Missing required fields
        response = requests.post(
            f"{BASE_URL}/api/wallet/google",
            json={}
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"


class TestFullSubscriptionFlowWithWallet:
    """Test full subscription flow to reach wallet buttons"""
    
    def test_full_flow_to_success_page(self):
        """Test complete subscription flow to verify wallet buttons are reachable"""
        test_phone = "9876543231"
        test_name = "Wallet Flow Test"
        
        # Step 1: Send OTP
        otp_response = requests.post(
            f"{BASE_URL}/api/otp/send",
            json={"phone": test_phone}
        )
        assert otp_response.status_code == 200, f"OTP send failed: {otp_response.text}"
        otp_data = otp_response.json()
        sandbox_otp = otp_data.get("sandbox_otp")
        assert sandbox_otp, "Sandbox OTP should be returned"
        print(f"Step 1 PASS: OTP sent, sandbox_otp={sandbox_otp}")
        
        # Step 2: Verify OTP
        verify_response = requests.post(
            f"{BASE_URL}/api/otp/verify",
            json={"phone": test_phone, "otp": sandbox_otp}
        )
        assert verify_response.status_code == 200, f"OTP verify failed: {verify_response.text}"
        print("Step 2 PASS: OTP verified")
        
        # Step 3: Create payment order
        order_response = requests.post(
            f"{BASE_URL}/api/payment/create-order",
            json={"phone": test_phone, "name": test_name, "plan": "monthly"}
        )
        assert order_response.status_code == 200, f"Create order failed: {order_response.text}"
        order_data = order_response.json()
        order_id = order_data.get("order_id")
        assert order_id, "Order ID should be returned"
        print(f"Step 3 PASS: Order created, order_id={order_id}")
        
        # Step 4: Verify payment (sandbox auto-approve)
        payment_response = requests.post(
            f"{BASE_URL}/api/payment/verify",
            json={
                "phone": test_phone,
                "order_id": order_id,
                "payment_id": "sandbox_pay",
                "signature": ""
            }
        )
        assert payment_response.status_code == 200, f"Payment verify failed: {payment_response.text}"
        payment_data = payment_response.json()
        assert payment_data.get("success") == True, "Payment should be successful"
        membership_id = payment_data.get("membership_id")
        expires_at = payment_data.get("expires_at")
        assert membership_id, "Membership ID should be returned"
        assert expires_at, "Expires at should be returned"
        print(f"Step 4 PASS: Payment verified, membership_id={membership_id}")
        
        # Step 5: Save preferences
        prefs_response = requests.post(
            f"{BASE_URL}/api/preferences",
            json={
                "phone": test_phone,
                "brands": ["HUEMN", "CREPDOG_CREW"],
                "alert_types": ["price_drop", "new_release"],
                "categories": ["garments", "sneakers"],
                "sizes": ["M", "L", "UK9"]
            }
        )
        assert prefs_response.status_code == 200, f"Save preferences failed: {prefs_response.text}"
        print("Step 5 PASS: Preferences saved")
        
        # Step 6: Test wallet APIs with real membership data
        apple_response = requests.post(
            f"{BASE_URL}/api/wallet/apple",
            json={
                "phone": test_phone,
                "name": test_name,
                "membership_id": membership_id,
                "expires_at": expires_at
            }
        )
        assert apple_response.status_code == 200, f"Apple Wallet failed: {apple_response.text}"
        print(f"Step 6a PASS: Apple Wallet API works - {apple_response.json().get('message', '')[:50]}")
        
        google_response = requests.post(
            f"{BASE_URL}/api/wallet/google",
            json={
                "phone": test_phone,
                "name": test_name,
                "membership_id": membership_id,
                "expires_at": expires_at
            }
        )
        assert google_response.status_code == 200, f"Google Wallet failed: {google_response.text}"
        print(f"Step 6b PASS: Google Wallet API works - {google_response.json().get('message', '')[:50]}")
        
        print("\n=== FULL SUBSCRIPTION FLOW WITH WALLET COMPLETE ===")


class TestExistingAPIsStillWork:
    """Verify existing APIs still work after wallet feature addition"""
    
    def test_otp_send_still_works(self):
        """Test OTP send endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/otp/send",
            json={"phone": "9876543232"}
        )
        assert response.status_code == 200
        assert "sandbox_otp" in response.json()
        print("OTP send: PASS")
    
    def test_preferences_endpoint_still_works(self):
        """Test preferences endpoint with categories and sizes"""
        # First create a subscriber via OTP flow
        test_phone = "9876543233"
        
        # Send and verify OTP
        otp_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        otp = otp_resp.json().get("sandbox_otp")
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": test_phone, "otp": otp})
        
        # Save preferences
        response = requests.post(
            f"{BASE_URL}/api/preferences",
            json={
                "phone": test_phone,
                "brands": ["HUEMN"],
                "alert_types": ["price_drop"],
                "categories": ["garments"],
                "sizes": ["M", "L"]
            }
        )
        assert response.status_code == 200
        print("Preferences save: PASS")
        
        # Get preferences
        get_response = requests.get(f"{BASE_URL}/api/preferences/{test_phone}")
        assert get_response.status_code == 200
        prefs = get_response.json().get("preferences", {})
        assert "categories" in prefs
        assert "sizes" in prefs
        print("Preferences get: PASS")
    
    def test_brands_endpoint_still_works(self):
        """Test brands endpoint"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        print("Brands endpoint: PASS")
    
    def test_subscriber_count_still_works(self):
        """Test subscriber count endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscribers/count")
        assert response.status_code == 200
        assert "count" in response.json()
        print("Subscriber count: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
