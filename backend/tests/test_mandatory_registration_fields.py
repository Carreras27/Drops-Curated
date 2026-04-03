"""
Test mandatory registration fields: Full Name, Email, WhatsApp, Home Address
Tests the new feature requiring all 4 fields during registration
"""
import pytest
import requests
import os
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def generate_phone():
    """Generate a random valid Indian phone number"""
    return f"9{''.join(random.choices(string.digits, k=9))}"

class TestMandatoryRegistrationFields:
    """Test mandatory registration fields in the subscription flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.phone = generate_phone()
        self.name = "Test User Registration"
        self.email = f"test_{self.phone}@example.com"
        self.address = "123 Test Street, Test City, Test State 123456"
        self.otp = None
    
    def test_otp_send_and_verify(self):
        """Test OTP send and verify flow"""
        # Send OTP
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": self.phone})
        assert response.status_code == 200, f"OTP send failed: {response.text}"
        data = response.json()
        assert "sandbox_otp" in data, "Sandbox OTP not returned"
        self.otp = data["sandbox_otp"]
        
        # Verify OTP
        response = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": self.phone, "otp": self.otp})
        assert response.status_code == 200, f"OTP verify failed: {response.text}"
        data = response.json()
        assert data.get("verified") == True, "OTP not verified"
        print(f"PASS: OTP send and verify for phone {self.phone}")
    
    def test_create_order_requires_all_fields(self):
        """Test that create-order requires name, email, and address"""
        # First verify phone
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": self.phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": self.phone, "otp": otp})
        
        # Test with all fields - should succeed
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": self.phone,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "plan": "monthly"
        })
        assert response.status_code == 200, f"Create order with all fields failed: {response.text}"
        data = response.json()
        assert "order_id" in data, "Order ID not returned"
        assert data.get("amount") == 39900, "Amount should be 39900 paise (₹399)"
        print(f"PASS: Create order with all mandatory fields")
    
    def test_create_order_missing_name(self):
        """Test that create-order fails without name"""
        phone = generate_phone()
        # Verify phone first
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        # Try without name - should fail validation
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "email": "test@example.com",
            "address": "123 Test Street, Test City 123456",
            "plan": "monthly"
        })
        # Pydantic validation should reject this
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print("PASS: Create order correctly rejects missing name")
    
    def test_create_order_missing_email(self):
        """Test that create-order fails without email"""
        phone = generate_phone()
        # Verify phone first
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        # Try without email - should fail validation
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": "Test User",
            "address": "123 Test Street, Test City 123456",
            "plan": "monthly"
        })
        # Pydantic validation should reject this
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"
        print("PASS: Create order correctly rejects missing email")
    
    def test_create_order_missing_address(self):
        """Test that create-order fails without address"""
        phone = generate_phone()
        # Verify phone first
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        # Try without address - should fail validation
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": "Test User",
            "email": "test@example.com",
            "plan": "monthly"
        })
        # Pydantic validation should reject this
        assert response.status_code == 422, f"Expected 422 for missing address, got {response.status_code}"
        print("PASS: Create order correctly rejects missing address")
    
    def test_order_stores_email_and_address(self):
        """Test that order stores email and address in database"""
        phone = generate_phone()
        name = "Test Storage User"
        email = f"storage_{phone}@example.com"
        address = "456 Storage Street, Storage City, Storage State 654321"
        
        # Verify phone
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        # Create order
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": name,
            "email": email,
            "address": address,
            "plan": "monthly"
        })
        assert response.status_code == 200
        order_id = response.json()["order_id"]
        
        # Verify payment (sandbox auto-approves)
        response = requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": phone,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        })
        assert response.status_code == 200, f"Payment verify failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Payment not successful"
        assert "membership_id" in data, "Membership ID not returned"
        print(f"PASS: Order created and payment verified with membership_id: {data['membership_id']}")
        
        # Now check membership endpoint returns email and address
        response = requests.get(f"{BASE_URL}/api/membership/{phone}")
        assert response.status_code == 200, f"Get membership failed: {response.text}"
        membership = response.json()
        
        # Verify email and address are stored
        assert membership.get("email") == email, f"Email not stored correctly. Expected: {email}, Got: {membership.get('email')}"
        assert membership.get("address") == address, f"Address not stored correctly. Expected: {address}, Got: {membership.get('address')}"
        assert membership.get("name") == name, f"Name not stored correctly. Expected: {name}, Got: {membership.get('name')}"
        print(f"PASS: Membership endpoint returns email and address correctly")
    
    def test_membership_endpoint_returns_all_fields(self):
        """Test GET /api/membership/{phone} returns email and address fields"""
        phone = generate_phone()
        name = "Membership Fields Test"
        email = f"membership_{phone}@example.com"
        address = "789 Membership Ave, Member City, Member State 789012"
        
        # Complete full registration flow
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": name,
            "email": email,
            "address": address,
            "plan": "monthly"
        })
        order_id = response.json()["order_id"]
        
        requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": phone,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        })
        
        # Get membership and verify all fields
        response = requests.get(f"{BASE_URL}/api/membership/{phone}")
        assert response.status_code == 200
        membership = response.json()
        
        # Check all required fields are present
        required_fields = ["membership_id", "name", "email", "address", "phone", "plan", "expires_at", "is_active"]
        for field in required_fields:
            assert field in membership, f"Missing field: {field}"
        
        assert membership["email"] == email
        assert membership["address"] == address
        assert membership["name"] == name
        assert membership["phone"] == phone
        assert membership["is_active"] == True
        print(f"PASS: Membership endpoint returns all required fields including email and address")


class TestCreateOrderRequestModel:
    """Test the CreateOrderRequest Pydantic model validation"""
    
    def test_valid_request_with_all_fields(self):
        """Test valid request with all mandatory fields"""
        phone = generate_phone()
        # Verify phone first
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": "Valid User",
            "email": "valid@example.com",
            "address": "Valid Address, Valid City 123456",
            "plan": "monthly"
        })
        assert response.status_code == 200
        print("PASS: Valid request with all fields accepted")
    
    def test_invalid_email_format(self):
        """Test that invalid email format is rejected"""
        phone = generate_phone()
        # Verify phone first
        response = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = response.json()["sandbox_otp"]
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json={
            "phone": phone,
            "name": "Test User",
            "email": "invalid-email",  # Invalid email format
            "address": "Valid Address, Valid City 123456",
            "plan": "monthly"
        })
        # Should fail validation due to invalid email
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        print("PASS: Invalid email format correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
