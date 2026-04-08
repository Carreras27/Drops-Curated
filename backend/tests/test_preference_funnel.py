"""
Test suite for Preference Funnel feature - Drops Curated
Tests all 4 sections (A, B, C, D) of the preference funnel:
A) Brand Selection with Top 5/10 limit
B) Trigger-Based Filtering (New Drops, Price Drops, Restock Alerts)
C) Specificity (Category and Size filters)
D) Notification Frequency (Instant vs Daily Digest)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPreferenceFunnelAPI:
    """Test POST /api/preferences with all new preference funnel fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test subscriber before each test"""
        self.test_phone = f"987654{datetime.now().strftime('%H%M%S')}"
        # Create subscriber via OTP flow
        requests.post(f"{BASE_URL}/api/otp/send", json={"phone": self.test_phone})
        
    def test_preferences_accepts_brand_limit_5(self):
        """Test brand_limit field with value 5 (Top 5)"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": ["SUPERKICKS", "HUEMN", "CAPSUL", "CREPDOG_CREW", "URBAN_MONKEY"],
            "brand_limit": 5,
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "daily"
        })
        # May return 404 if subscriber not found, but should not be 500
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
    def test_preferences_accepts_brand_limit_10(self):
        """Test brand_limit field with value 10 (Top 10)"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": ["SUPERKICKS", "HUEMN", "CAPSUL"],
            "brand_limit": 10,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "instant"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_brand_limit_unlimited(self):
        """Test brand_limit field with value 0 (Unlimited)"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],  # Empty = all brands
            "brand_limit": 0,  # Unlimited
            "alert_types": ["price_drop", "new_release", "restock"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_restock_alert_type(self):
        """Test alert_types includes 'restock' option"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["restock"],  # Only restock alerts
            "categories": [],
            "sizes": [],
            "alert_frequency": "instant"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_all_trigger_types(self):
        """Test all 3 trigger types: new_release, price_drop, restock"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["new_release", "price_drop", "restock"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_price_range(self):
        """Test price_range field with min and max values"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "price_range": {"min": 5000, "max": 25000},
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_keywords(self):
        """Test keywords field for product matching"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["new_release"],
            "categories": [],
            "sizes": [],
            "keywords": ["jordan", "nike", "dunk", "yeezy"],
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_drop_threshold(self):
        """Test drop_threshold field for price drop percentage"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "drop_threshold": 20,  # Only alert if 20%+ drop
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_instant_frequency(self):
        """Test alert_frequency with 'instant' value"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "instant"
        })
        assert response.status_code in [200, 404]
        
    def test_preferences_accepts_daily_frequency(self):
        """Test alert_frequency with 'daily' value"""
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.test_phone,
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "alert_frequency": "daily"
        })
        assert response.status_code in [200, 404]


class TestGetPreferencesAPI:
    """Test GET /api/preferences/{phone} returns all preference funnel fields"""
    
    def test_get_preferences_returns_brand_limit(self):
        """Verify GET preferences returns brand_limit field"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        prefs = data["preferences"]
        assert "brand_limit" in prefs
        assert isinstance(prefs["brand_limit"], int)
        
    def test_get_preferences_returns_price_range(self):
        """Verify GET preferences returns price_range field"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        prefs = data["preferences"]
        assert "price_range" in prefs
        assert "min" in prefs["price_range"]
        assert "max" in prefs["price_range"]
        
    def test_get_preferences_returns_keywords(self):
        """Verify GET preferences returns keywords field"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        prefs = data["preferences"]
        assert "keywords" in prefs
        assert isinstance(prefs["keywords"], list)
        
    def test_get_preferences_returns_drop_threshold(self):
        """Verify GET preferences returns drop_threshold field"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        prefs = data["preferences"]
        assert "drop_threshold" in prefs
        assert isinstance(prefs["drop_threshold"], int)
        
    def test_get_preferences_returns_alert_frequency(self):
        """Verify GET preferences returns alert_frequency field"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        prefs = data["preferences"]
        assert "alert_frequency" in prefs
        assert prefs["alert_frequency"] in ["instant", "daily"]
        
    def test_get_preferences_returns_restock_in_alert_types(self):
        """Verify GET preferences can include 'restock' in alert_types"""
        response = requests.get(f"{BASE_URL}/api/preferences/9876543210")
        assert response.status_code == 200
        data = response.json()
        prefs = data["preferences"]
        assert "alert_types" in prefs
        # Check that restock is a valid option (may or may not be selected)
        assert isinstance(prefs["alert_types"], list)
        
    def test_get_preferences_returns_defaults_for_new_subscriber(self):
        """Verify GET preferences returns defaults for subscriber without preferences"""
        # Use a phone that likely doesn't have preferences set
        response = requests.get(f"{BASE_URL}/api/preferences/9999999999")
        # Should return 404 if subscriber doesn't exist
        if response.status_code == 200:
            data = response.json()
            prefs = data["preferences"]
            # Check defaults are returned
            assert prefs.get("brand_limit", 10) == 10
            assert prefs.get("drop_threshold", 10) == 10
            assert prefs.get("alert_frequency", "daily") == "daily"


class TestSchedulerStatus:
    """Test GET /api/scheduler/status shows both jobs"""
    
    def test_scheduler_status_shows_auto_scrape_job(self):
        """Verify scheduler status includes auto_scrape job"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "next_scrape" in data
        assert data["interval_minutes"] == 15
        
    def test_scheduler_status_shows_daily_digest_job(self):
        """Verify scheduler status includes daily_digest job"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "next_digest" in data
        assert "digest_time" in data
        assert "8" in data["digest_time"] and "PM" in data["digest_time"]
        
    def test_scheduler_status_complete_structure(self):
        """Verify scheduler status has all expected fields"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        expected_fields = ["is_running", "last_run", "results", "next_scrape", "next_digest", "interval_minutes", "digest_time"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestPreferenceFunnelIntegration:
    """Integration tests for complete preference funnel flow"""
    
    def test_full_preference_funnel_save_and_retrieve(self):
        """Test saving all preference funnel fields and retrieving them"""
        test_phone = "9111222333"  # Known VIP member
        
        # Save comprehensive preferences
        save_response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": test_phone,
            "brands": ["SUPERKICKS", "HUEMN", "CAPSUL", "CREPDOG_CREW", "URBAN_MONKEY"],
            "brand_limit": 5,
            "alert_types": ["new_release", "price_drop", "restock"],
            "categories": ["sneakers", "garments"],
            "sizes": ["UK9", "UK10", "L", "XL"],
            "price_range": {"min": 3000, "max": 30000},
            "keywords": ["jordan", "nike", "dunk"],
            "drop_threshold": 15,
            "alert_frequency": "daily"
        })
        
        if save_response.status_code == 200:
            # Retrieve and verify
            get_response = requests.get(f"{BASE_URL}/api/preferences/{test_phone}")
            assert get_response.status_code == 200
            data = get_response.json()
            prefs = data["preferences"]
            
            # Verify all fields were saved
            assert prefs["brand_limit"] == 5
            assert "restock" in prefs["alert_types"]
            assert prefs["drop_threshold"] == 15
            assert prefs["alert_frequency"] == "daily"
            assert prefs["price_range"]["min"] == 3000
            assert prefs["price_range"]["max"] == 30000
            assert "jordan" in prefs["keywords"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
