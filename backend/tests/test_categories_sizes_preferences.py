"""
Backend API tests for Drops Curated - Categories and Sizes Preferences
Tests: POST /api/preferences with categories/sizes, GET /api/preferences/{phone} returns categories/sizes
New feature: Users can filter alerts by product categories (garments, sneakers, accessories) and sizes (XS-XXL, UK6-UK12, Free Size)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCategoriesAndSizesPreferences:
    """Tests for categories and sizes in user preferences"""
    
    TEST_PHONE = "9876543221"  # New test phone for categories/sizes tests
    
    @pytest.fixture(autouse=True)
    def setup_subscriber(self):
        """Ensure subscriber exists before testing preferences"""
        # Send OTP
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": self.TEST_PHONE})
        assert response.status_code == 200
        otp = response.json().get("sandbox_otp")
        
        # Verify OTP to create subscriber
        response = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": self.TEST_PHONE, "otp": otp})
        assert response.status_code == 200
        print(f"Subscriber {self.TEST_PHONE} ready for testing")
    
    def test_save_preferences_with_categories(self):
        """POST /api/preferences saves categories array"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN"],
            "alert_types": ["price_drop", "new_release"],
            "categories": ["garments", "sneakers"],
            "sizes": []
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Preferences updated"
        print(f"Saved preferences with categories: {payload['categories']}")
    
    def test_get_preferences_returns_categories(self):
        """GET /api/preferences/{phone} returns saved categories"""
        # First save preferences with categories
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["FARAK"],
            "alert_types": ["price_drop"],
            "categories": ["garments", "accessories"],
            "sizes": []
        }
        requests.post(f"{BASE_URL}/api/preferences", json=payload)
        
        # Then retrieve
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["phone"] == self.TEST_PHONE
        assert "preferences" in data
        prefs = data["preferences"]
        assert "categories" in prefs
        assert prefs["categories"] == ["garments", "accessories"]
        print(f"Retrieved categories: {prefs['categories']}")
    
    def test_save_preferences_with_sizes(self):
        """POST /api/preferences saves sizes array"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["VEG_NON_VEG"],
            "alert_types": ["new_release"],
            "categories": [],
            "sizes": ["M", "L", "XL", "UK9", "UK10"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Preferences updated"
        print(f"Saved preferences with sizes: {payload['sizes']}")
    
    def test_get_preferences_returns_sizes(self):
        """GET /api/preferences/{phone} returns saved sizes"""
        # First save preferences with sizes
        payload = {
            "phone": self.TEST_PHONE,
            "brands": [],
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": ["S", "M", "L", "UK8"]
        }
        requests.post(f"{BASE_URL}/api/preferences", json=payload)
        
        # Then retrieve
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        
        data = response.json()
        prefs = data["preferences"]
        assert "sizes" in prefs
        assert prefs["sizes"] == ["S", "M", "L", "UK8"]
        print(f"Retrieved sizes: {prefs['sizes']}")
    
    def test_save_preferences_with_all_categories(self):
        """Can save all three categories: garments, sneakers, accessories"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK"],
            "alert_types": ["price_drop"],
            "categories": ["garments", "sneakers", "accessories"],
            "sizes": []
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert len(data["preferences"]["categories"]) == 3
        print(f"All 3 categories saved: {data['preferences']['categories']}")
    
    def test_save_preferences_with_all_sizes(self):
        """Can save all available sizes: XS, S, M, L, XL, XXL, UK6-UK12, Free Size"""
        all_sizes = ["XS", "S", "M", "L", "XL", "XXL", "UK6", "UK7", "UK8", "UK9", "UK10", "UK11", "UK12", "Free Size"]
        payload = {
            "phone": self.TEST_PHONE,
            "brands": [],
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": all_sizes
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert len(data["preferences"]["sizes"]) == 14
        print(f"All 14 sizes saved: {data['preferences']['sizes']}")
    
    def test_empty_categories_means_all_categories(self):
        """Empty categories array means alerts for all categories"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["CAPSUL"],
            "alert_types": ["new_release"],
            "categories": [],  # Empty = all categories
            "sizes": ["M"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert data["preferences"]["categories"] == []
        print("Empty categories saved correctly (means all categories)")
    
    def test_empty_sizes_means_all_sizes(self):
        """Empty sizes array means alerts for all sizes"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["URBAN_MONKEY"],
            "alert_types": ["price_drop"],
            "categories": ["sneakers"],
            "sizes": []  # Empty = all sizes
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert data["preferences"]["sizes"] == []
        print("Empty sizes saved correctly (means all sizes)")
    
    def test_save_preferences_with_categories_sizes_brands_combined(self):
        """Can save preferences with categories, sizes, brands, and alert_types all together"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK", "VEG_NON_VEG"],
            "alert_types": ["price_drop", "new_release"],
            "categories": ["garments", "sneakers"],
            "sizes": ["M", "L", "XL", "UK9", "UK10"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        # Verify all fields persisted
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        
        data = response.json()
        prefs = data["preferences"]
        assert prefs["brands"] == ["HUEMN", "FARAK", "VEG_NON_VEG"]
        assert prefs["alert_types"] == ["price_drop", "new_release"]
        assert prefs["categories"] == ["garments", "sneakers"]
        assert prefs["sizes"] == ["M", "L", "XL", "UK9", "UK10"]
        print(f"Full preferences saved: brands={len(prefs['brands'])}, categories={len(prefs['categories'])}, sizes={len(prefs['sizes'])}")


class TestFullSubscriptionFlowWithCategoriesSizes:
    """End-to-end test: OTP → Details → Payment → Preferences (with categories/sizes) → Success"""
    
    TEST_PHONE = "9876543222"
    
    def test_full_flow_with_categories_and_sizes(self):
        """Complete subscription flow including categories and sizes in preferences"""
        # Step 1: Send OTP
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": self.TEST_PHONE})
        assert response.status_code == 200
        otp = response.json().get("sandbox_otp")
        assert otp is not None
        print(f"Step 1: OTP sent - {otp}")
        
        # Step 2: Verify OTP
        response = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": self.TEST_PHONE, "otp": otp})
        assert response.status_code == 200
        assert response.json()["verified"] == True
        print("Step 2: OTP verified")
        
        # Step 3: Create payment order
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": self.TEST_PHONE,
            "name": "Test User Categories Sizes",
            "plan": "monthly"
        })
        assert response.status_code == 200
        order_id = response.json()["order_id"]
        assert response.json()["sandbox"] == True
        print(f"Step 3: Order created - {order_id}")
        
        # Step 4: Verify payment (sandbox auto-approve)
        response = requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": self.TEST_PHONE,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        })
        assert response.status_code == 200
        membership_id = response.json()["membership_id"]
        print(f"Step 4: Payment verified - {membership_id}")
        
        # Step 5: Save preferences with categories and sizes
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK"],
            "alert_types": ["price_drop", "new_release"],
            "categories": ["garments", "sneakers"],
            "sizes": ["M", "L", "UK9"]
        })
        assert response.status_code == 200
        print("Step 5: Preferences saved with categories and sizes")
        
        # Verify preferences persisted with categories and sizes
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        prefs = response.json()["preferences"]
        assert prefs["brands"] == ["HUEMN", "FARAK"]
        assert prefs["alert_types"] == ["price_drop", "new_release"]
        assert prefs["categories"] == ["garments", "sneakers"]
        assert prefs["sizes"] == ["M", "L", "UK9"]
        print(f"Verified: categories={prefs['categories']}, sizes={prefs['sizes']}")
        
        # Verify membership
        response = requests.get(f"{BASE_URL}/api/membership/{self.TEST_PHONE}")
        assert response.status_code == 200
        assert response.json()["membership_id"] == membership_id
        print(f"Full flow complete with categories/sizes! Membership: {membership_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
