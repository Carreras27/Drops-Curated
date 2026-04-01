"""
Backend API tests for Drops Curated v4 - Scheduler, Preferences, and Alerts
Tests: scheduler status, trigger scrape, user preferences CRUD, recent alerts
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSchedulerAPI:
    """Tests for scheduler endpoints - auto-scrape every 15 minutes"""
    
    def test_scheduler_status_returns_valid_structure(self):
        """GET /api/scheduler/status returns scheduler info"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        assert "is_running" in data
        assert "last_run" in data
        assert "next_run" in data
        assert "interval_minutes" in data
        
        # Verify types
        assert isinstance(data["is_running"], bool)
        assert data["interval_minutes"] == 15
        print(f"Scheduler status: is_running={data['is_running']}, last_run={data['last_run']}")
    
    def test_scheduler_status_has_results(self):
        """Scheduler status includes results from last run"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        
        data = response.json()
        # Results should be present if scheduler has run
        if data.get("last_run"):
            assert "results" in data
            results = data["results"]
            # Should have results for multiple brands
            assert len(results) > 0
            print(f"Scheduler has results for {len(results)} brands")
            
            # Check structure of a result
            for brand_key, result in results.items():
                assert "status" in result
                if result["status"] == "ok":
                    assert "scraped" in result
                    print(f"  {brand_key}: {result.get('scraped', 0)} scraped, {result.get('new', 0)} new, {result.get('price_drops', 0)} drops")
    
    def test_scheduler_trigger_starts_scrape(self):
        """POST /api/scheduler/trigger starts a scrape cycle"""
        response = requests.post(f"{BASE_URL}/api/scheduler/trigger")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"
        print(f"Trigger response: {data['message']}")


class TestPreferencesAPI:
    """Tests for user preferences endpoints - brand selection and alert types"""
    
    TEST_PHONE = "9876543210"  # Use existing subscriber phone from previous tests
    
    def test_save_preferences_with_specific_brands(self):
        """POST /api/preferences saves brand and alert preferences"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK", "VEG_NON_VEG"],
            "alert_types": ["price_drop", "new_release"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Preferences updated"
        print(f"Saved preferences for {self.TEST_PHONE}")
    
    def test_get_preferences_returns_saved_data(self):
        """GET /api/preferences/{phone} returns saved preferences"""
        # First save preferences
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK"],
            "alert_types": ["price_drop"]
        }
        requests.post(f"{BASE_URL}/api/preferences", json=payload)
        
        # Then retrieve
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["phone"] == self.TEST_PHONE
        assert "preferences" in data
        prefs = data["preferences"]
        assert prefs["brands"] == ["HUEMN", "FARAK"]
        assert prefs["alert_types"] == ["price_drop"]
        print(f"Retrieved preferences: brands={prefs['brands']}, types={prefs['alert_types']}")
    
    def test_save_preferences_empty_brands_means_all(self):
        """Empty brands array means alerts for all brands"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": [],  # Empty = all brands
            "alert_types": ["price_drop", "new_release"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        # Verify
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert data["preferences"]["brands"] == []
        print("Empty brands saved correctly (means all brands)")
    
    def test_save_preferences_price_drop_only(self):
        """Can save preferences with only price_drop alerts"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["URBAN_MONKEY"],
            "alert_types": ["price_drop"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert data["preferences"]["alert_types"] == ["price_drop"]
        print("Price drop only preference saved")
    
    def test_save_preferences_new_release_only(self):
        """Can save preferences with only new_release alerts"""
        payload = {
            "phone": self.TEST_PHONE,
            "brands": ["CAPSUL"],
            "alert_types": ["new_release"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert data["preferences"]["alert_types"] == ["new_release"]
        print("New release only preference saved")
    
    def test_get_preferences_nonexistent_phone_returns_404(self):
        """GET /api/preferences/{phone} returns 404 for unknown phone"""
        response = requests.get(f"{BASE_URL}/api/preferences/0000000000")
        assert response.status_code == 404
        print("404 returned for nonexistent phone")
    
    def test_save_preferences_all_14_brands(self):
        """Can save preferences with all 14 brands selected"""
        all_brands = [
            "CREPDOG_CREW", "ALMOST_GODS", "CODE_BROWN", "JAYWALKING",
            "HUEMN", "NOUGHTONE", "BLUORNG", "CAPSUL", "URBAN_MONKEY",
            "HOUSE_OF_KOALA", "FARAK", "HIYEST", "VEG_NON_VEG", "CULTURE_CIRCLE"
        ]
        payload = {
            "phone": self.TEST_PHONE,
            "brands": all_brands,
            "alert_types": ["price_drop", "new_release"]
        }
        response = requests.post(f"{BASE_URL}/api/preferences", json=payload)
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        data = response.json()
        assert len(data["preferences"]["brands"]) == 14
        print(f"All 14 brands saved: {len(data['preferences']['brands'])} brands")


class TestAlertsAPI:
    """Tests for alert log endpoints - recent WhatsApp alerts"""
    
    def test_recent_alerts_returns_list(self):
        """GET /api/alerts/recent returns recent alert log entries"""
        response = requests.get(f"{BASE_URL}/api/alerts/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "count" in data
        assert isinstance(data["alerts"], list)
        print(f"Recent alerts: {data['count']} entries")
    
    def test_recent_alerts_structure(self):
        """Alert entries have required fields"""
        response = requests.get(f"{BASE_URL}/api/alerts/recent")
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] > 0:
            alert = data["alerts"][0]
            # Check required fields
            assert "phone" in alert
            assert "store" in alert
            assert "message" in alert
            assert "sent" in alert
            assert "createdAt" in alert
            print(f"Alert structure valid: phone={alert['phone']}, store={alert['store']}, sent={alert['sent']}")
        else:
            print("No alerts in log yet")
    
    def test_recent_alerts_sorted_by_date(self):
        """Alerts are sorted by createdAt descending (most recent first)"""
        response = requests.get(f"{BASE_URL}/api/alerts/recent")
        assert response.status_code == 200
        
        data = response.json()
        if data["count"] >= 2:
            alerts = data["alerts"]
            # First alert should be more recent than second
            assert alerts[0]["createdAt"] >= alerts[1]["createdAt"]
            print("Alerts sorted correctly (most recent first)")
        else:
            print("Not enough alerts to verify sorting")


class TestScrapeStatusAPI:
    """Tests for scrape status - verify 7000+ products"""
    
    def test_scrape_status_shows_7000_plus_products(self):
        """GET /api/scrape/status shows 7000+ total products"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_products" in data
        assert data["total_products"] >= 7000
        print(f"Total products: {data['total_products']}")
    
    def test_scrape_status_shows_14_brands(self):
        """Scrape status shows all 14 brands"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "brands" in data
        assert len(data["brands"]) >= 14
        print(f"Brands in status: {len(data['brands'])}")
    
    def test_scrape_status_shows_14_scrapers(self):
        """Available scrapers list has 14 entries"""
        response = requests.get(f"{BASE_URL}/api/scrape/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "available_scrapers" in data
        assert len(data["available_scrapers"]) == 14
        print(f"Available scrapers: {data['available_scrapers']}")


class TestFullSubscriptionFlowWithPreferences:
    """End-to-end test: OTP → Details → Payment → Preferences → Success"""
    
    TEST_PHONE = "9876543218"
    
    def test_full_flow_with_preferences(self):
        """Complete subscription flow including preferences step"""
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
            "name": "Test User Prefs",
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
        
        # Step 5: Save preferences
        response = requests.post(f"{BASE_URL}/api/preferences", json={
            "phone": self.TEST_PHONE,
            "brands": ["HUEMN", "FARAK", "VEG_NON_VEG"],
            "alert_types": ["price_drop"]
        })
        assert response.status_code == 200
        print("Step 5: Preferences saved")
        
        # Verify preferences persisted
        response = requests.get(f"{BASE_URL}/api/preferences/{self.TEST_PHONE}")
        assert response.status_code == 200
        prefs = response.json()["preferences"]
        assert prefs["brands"] == ["HUEMN", "FARAK", "VEG_NON_VEG"]
        assert prefs["alert_types"] == ["price_drop"]
        print(f"Verified: brands={prefs['brands']}, types={prefs['alert_types']}")
        
        # Verify membership
        response = requests.get(f"{BASE_URL}/api/membership/{self.TEST_PHONE}")
        assert response.status_code == 200
        assert response.json()["membership_id"] == membership_id
        print(f"Full flow complete! Membership: {membership_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
