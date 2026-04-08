"""
Test My Preferences - Simulate Preferences API Tests
Tests the POST /api/preferences/simulate endpoint that shows users
what alerts they would receive based on their preference funnel settings.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSimulatePreferencesEndpoint:
    """Tests for POST /api/preferences/simulate endpoint"""
    
    def test_simulate_with_all_filters(self):
        """Test simulation with all preference funnel fields"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": ["SUPERKICKS", "HUEMN", "CAPSUL"],
            "brand_limit": 10,
            "alert_types": ["price_drop", "new_release"],
            "categories": ["sneakers"],
            "sizes": ["UK9", "UK10"],
            "price_range": {"min": 5000, "max": 25000},
            "keywords": ["jordan", "nike"],
            "drop_threshold": 15
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_matching_products" in data
        assert isinstance(data["total_matching_products"], int)
        
        # Verify estimated_daily_alerts structure
        assert "estimated_daily_alerts" in data
        alerts = data["estimated_daily_alerts"]
        assert "total" in alerts
        assert "breakdown" in alerts
        assert "frequency_impact" in alerts
        assert alerts["frequency_impact"] in ["Low", "Medium", "High"]
        
        # Verify breakdown structure
        breakdown = alerts["breakdown"]
        assert "new_drops" in breakdown
        assert "price_drops" in breakdown
        assert "restocks" in breakdown
        
    def test_simulate_returns_sample_daily_digest(self):
        """Test that simulation returns sample daily digest message"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 10,
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sample_daily_digest exists and is a string
        assert "sample_daily_digest" in data
        assert isinstance(data["sample_daily_digest"], str)
        assert "Daily Drops Digest" in data["sample_daily_digest"]
        
    def test_simulate_returns_filters_applied(self):
        """Test that simulation returns filters_applied summary"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": ["SUPERKICKS"],
            "brand_limit": 5,
            "alert_types": ["new_release"],
            "categories": ["garments"],
            "sizes": ["M", "L"],
            "price_range": {"min": 1000, "max": 10000},
            "keywords": ["hoodie"],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify filters_applied structure
        assert "filters_applied" in data
        filters = data["filters_applied"]
        assert "brands" in filters
        assert "categories" in filters
        assert "sizes" in filters
        assert "price_range" in filters
        assert "keywords" in filters
        
    def test_simulate_new_drops_section(self):
        """Test new_drops section in simulation response"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["new_release"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify new_drops structure
        assert "new_drops" in data
        new_drops = data["new_drops"]
        assert "count" in new_drops
        assert "sample" in new_drops
        assert "enabled" in new_drops
        assert new_drops["enabled"] == True
        assert isinstance(new_drops["sample"], list)
        
    def test_simulate_price_drops_section(self):
        """Test price_drops section in simulation response"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify price_drops structure
        assert "price_drops" in data
        price_drops = data["price_drops"]
        assert "count" in price_drops
        assert "sample" in price_drops
        assert "enabled" in price_drops
        assert "threshold" in price_drops
        assert price_drops["enabled"] == True
        assert price_drops["threshold"] == 10
        
    def test_simulate_restocks_section(self):
        """Test restocks section in simulation response"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["restock"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify restocks structure
        assert "restocks" in data
        restocks = data["restocks"]
        assert "count" in restocks
        assert "sample" in restocks
        assert "enabled" in restocks
        assert "note" in restocks
        assert restocks["enabled"] == True
        
    def test_simulate_with_no_filters_returns_all_products(self):
        """Test simulation with no filters returns maximum products"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # With no filters, should return many products
        assert data["total_matching_products"] > 0
        assert data["filters_applied"]["brands"] == "All brands"
        assert data["filters_applied"]["categories"] == "All categories"
        
    def test_simulate_with_strict_filters_returns_fewer_products(self):
        """Test simulation with strict filters returns fewer products"""
        # First get count with no filters
        response_all = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        all_count = response_all.json()["total_matching_products"]
        
        # Now with strict filters
        response_filtered = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": ["SUPERKICKS"],
            "brand_limit": 5,
            "alert_types": ["price_drop"],
            "categories": ["sneakers"],
            "sizes": ["UK9"],
            "price_range": {"min": 10000, "max": 20000},
            "keywords": ["jordan"],
            "drop_threshold": 20
        })
        filtered_count = response_filtered.json()["total_matching_products"]
        
        # Filtered should be less than or equal to all
        assert filtered_count <= all_count
        
    def test_simulate_frequency_impact_calculation(self):
        """Test that frequency_impact is calculated correctly"""
        # Test with no filters (should be High)
        response_high = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop", "new_release", "restock"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 5
        })
        
        assert response_high.status_code == 200
        data_high = response_high.json()
        
        # Verify frequency_impact is one of the valid values
        assert data_high["estimated_daily_alerts"]["frequency_impact"] in ["Low", "Medium", "High"]
        
    def test_simulate_sample_products_have_required_fields(self):
        """Test that sample products have required fields for display"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop", "new_release"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check new_drops samples
        if data["new_drops"]["sample"]:
            for product in data["new_drops"]["sample"]:
                assert "name" in product
                assert "lowestPrice" in product
                
        # Check price_drops samples
        if data["price_drops"]["sample"]:
            for product in data["price_drops"]["sample"]:
                assert "name" in product
                assert "lowestPrice" in product
                assert "originalPrice" in product
                assert "dropPercent" in product
                
    def test_simulate_with_disabled_alert_types(self):
        """Test that disabled alert types return empty samples"""
        # Only enable new_release, disable price_drop
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["new_release"],  # Only new_release
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # new_release should be enabled
        assert data["new_drops"]["enabled"] == True
        
        # price_drop should be disabled with empty sample
        assert data["price_drops"]["enabled"] == False
        assert data["price_drops"]["sample"] == []
        
    def test_simulate_with_different_drop_thresholds(self):
        """Test simulation with different price drop thresholds"""
        # Test with 5% threshold
        response_5 = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 5
        })
        
        # Test with 30% threshold
        response_30 = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["price_drop"],
            "categories": [],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 30
        })
        
        assert response_5.status_code == 200
        assert response_30.status_code == 200
        
        data_5 = response_5.json()
        data_30 = response_30.json()
        
        # Verify threshold is reflected in response
        assert data_5["price_drops"]["threshold"] == 5
        assert data_30["price_drops"]["threshold"] == 30
        
        # Lower threshold should find more or equal price drops
        assert data_5["price_drops"]["count"] >= data_30["price_drops"]["count"]


class TestSimulatePreferencesEdgeCases:
    """Edge case tests for simulate preferences"""
    
    def test_simulate_with_empty_request(self):
        """Test simulation with empty/default request"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use defaults
        assert "total_matching_products" in data
        assert "estimated_daily_alerts" in data
        
    def test_simulate_with_invalid_category(self):
        """Test simulation with invalid category (should still work)"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["new_release"],
            "categories": ["invalid_category"],
            "sizes": [],
            "price_range": None,
            "keywords": [],
            "drop_threshold": 10
        })
        
        # Should still return 200, just with 0 products
        assert response.status_code == 200
        
    def test_simulate_with_price_range_min_only(self):
        """Test simulation with only min price set"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["new_release"],
            "categories": [],
            "sizes": [],
            "price_range": {"min": 10000, "max": None},
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
        
    def test_simulate_with_price_range_max_only(self):
        """Test simulation with only max price set"""
        response = requests.post(f"{BASE_URL}/api/preferences/simulate", json={
            "brands": [],
            "brand_limit": 0,
            "alert_types": ["new_release"],
            "categories": [],
            "sizes": [],
            "price_range": {"min": None, "max": 5000},
            "keywords": [],
            "drop_threshold": 10
        })
        
        assert response.status_code == 200
