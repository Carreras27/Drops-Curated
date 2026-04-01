"""
Drops Curated API Tests - OTP, Payment, Partner Inquiry
Tests for: OTP send/verify, payment create-order/verify, membership, partner-inquiry
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test phone number for sandbox testing
TEST_PHONE = "9876543210"


class TestOTPAPI:
    """OTP endpoint tests - /api/otp/send and /api/otp/verify"""
    
    def test_send_otp_valid_phone(self):
        """POST /api/otp/send with valid phone should return sandbox_otp"""
        payload = {"phone": TEST_PHONE}
        response = requests.post(f"{BASE_URL}/api/otp/send", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'sandbox_otp' in data
        assert data['sandbox_otp'] is not None
        assert len(data['sandbox_otp']) == 6
        print(f"✓ OTP sent successfully, sandbox_otp: {data['sandbox_otp']}")
        return data['sandbox_otp']
    
    def test_send_otp_invalid_phone_short(self):
        """POST /api/otp/send with short phone should fail"""
        payload = {"phone": "12345"}
        response = requests.post(f"{BASE_URL}/api/otp/send", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Short phone rejected: {data['detail']}")
    
    def test_send_otp_invalid_phone_wrong_prefix(self):
        """POST /api/otp/send with non-Indian prefix should fail"""
        payload = {"phone": "1234567890"}  # Starts with 1, not 6-9
        response = requests.post(f"{BASE_URL}/api/otp/send", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Invalid prefix phone rejected: {data['detail']}")
    
    def test_verify_otp_valid(self):
        """POST /api/otp/verify with correct OTP should succeed"""
        # First send OTP
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": TEST_PHONE})
        assert send_resp.status_code == 200
        otp = send_resp.json()['sandbox_otp']
        
        # Verify OTP
        verify_payload = {"phone": TEST_PHONE, "otp": otp}
        response = requests.post(f"{BASE_URL}/api/otp/verify", json=verify_payload)
        assert response.status_code == 200
        data = response.json()
        assert data['verified'] == True
        print(f"✓ OTP verified successfully")
    
    def test_verify_otp_invalid(self):
        """POST /api/otp/verify with wrong OTP should fail"""
        # First send OTP
        requests.post(f"{BASE_URL}/api/otp/send", json={"phone": TEST_PHONE})
        
        # Verify with wrong OTP
        verify_payload = {"phone": TEST_PHONE, "otp": "000000"}
        response = requests.post(f"{BASE_URL}/api/otp/verify", json=verify_payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Invalid OTP rejected: {data['detail']}")
    
    def test_verify_otp_expired(self):
        """POST /api/otp/verify without sending OTP should fail"""
        verify_payload = {"phone": "9999999999", "otp": "123456"}
        response = requests.post(f"{BASE_URL}/api/otp/verify", json=verify_payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Expired/missing OTP rejected: {data['detail']}")


class TestPaymentAPI:
    """Payment endpoint tests - /api/payment/create-order and /api/payment/verify"""
    
    def _verify_phone(self, phone=TEST_PHONE):
        """Helper to verify phone before payment tests"""
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = send_resp.json()['sandbox_otp']
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
    
    def test_create_order_success(self):
        """POST /api/payment/create-order should create sandbox order"""
        self._verify_phone()
        
        payload = {"phone": TEST_PHONE, "name": "TEST_User", "plan": "monthly"}
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert 'order_id' in data
        assert 'amount' in data
        assert 'currency' in data
        assert 'sandbox' in data
        assert data['amount'] == 39900  # ₹399 in paise
        assert data['currency'] == 'INR'
        assert data['sandbox'] == True
        print(f"✓ Order created: {data['order_id']}, amount: {data['amount']}")
        return data['order_id']
    
    def test_create_order_without_verification(self):
        """POST /api/payment/create-order without OTP verification should fail"""
        payload = {"phone": "8888888888", "name": "TEST_User", "plan": "monthly"}
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Unverified phone rejected: {data['detail']}")
    
    def test_verify_payment_success(self):
        """POST /api/payment/verify should activate membership in sandbox"""
        self._verify_phone()
        
        # Create order
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", 
                                   json={"phone": TEST_PHONE, "name": "TEST_User", "plan": "monthly"})
        order_id = order_resp.json()['order_id']
        
        # Verify payment (sandbox auto-approves)
        verify_payload = {
            "phone": TEST_PHONE,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        }
        response = requests.post(f"{BASE_URL}/api/payment/verify", json=verify_payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] == True
        assert 'membership_id' in data
        assert 'expires_at' in data
        assert data['membership_id'].startswith('DC-')
        print(f"✓ Payment verified, membership: {data['membership_id']}")
        return data['membership_id']
    
    def test_verify_payment_invalid_order(self):
        """POST /api/payment/verify with invalid order should fail"""
        verify_payload = {
            "phone": TEST_PHONE,
            "order_id": "invalid_order_12345",
            "payment_id": "sandbox_pay",
            "signature": ""
        }
        response = requests.post(f"{BASE_URL}/api/payment/verify", json=verify_payload)
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        print(f"✓ Invalid order rejected: {data['detail']}")


class TestMembershipAPI:
    """Membership endpoint tests - /api/membership/{phone}"""
    
    def _create_membership(self, phone=TEST_PHONE):
        """Helper to create a membership"""
        # Send and verify OTP
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": phone})
        otp = send_resp.json()['sandbox_otp']
        requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": phone, "otp": otp})
        
        # Create order
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", 
                                   json={"phone": phone, "name": "TEST_Member", "plan": "monthly"})
        order_id = order_resp.json()['order_id']
        
        # Verify payment
        requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": phone, "order_id": order_id, "payment_id": "sandbox_pay", "signature": ""
        })
    
    def test_get_membership_exists(self):
        """GET /api/membership/{phone} should return membership details"""
        self._create_membership()
        
        response = requests.get(f"{BASE_URL}/api/membership/{TEST_PHONE}")
        assert response.status_code == 200
        data = response.json()
        
        assert 'membership_id' in data
        assert 'name' in data
        assert 'phone' in data
        assert 'plan' in data
        assert 'expires_at' in data
        assert 'is_active' in data
        assert data['phone'] == TEST_PHONE
        print(f"✓ Membership found: {data['membership_id']}, expires: {data['expires_at']}")
    
    def test_get_membership_not_found(self):
        """GET /api/membership/{phone} for non-member should return 404"""
        response = requests.get(f"{BASE_URL}/api/membership/1111111111")
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        print(f"✓ Non-member returns 404: {data['detail']}")


class TestPartnerInquiryAPI:
    """Partner inquiry endpoint tests - /api/partner-inquiry"""
    
    def test_partner_inquiry_success(self):
        """POST /api/partner-inquiry should save inquiry"""
        payload = {
            "brand": "TEST_Brand",
            "contact": "TEST_Contact Person",
            "email": "test@testbrand.com",
            "message": "We want to partner with Drops Curated"
        }
        response = requests.post(f"{BASE_URL}/api/partner-inquiry", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert 'message' in data
        assert 'status' in data
        assert data['status'] == 'created'
        print(f"✓ Partner inquiry created successfully")
    
    def test_partner_inquiry_minimal(self):
        """POST /api/partner-inquiry with minimal data should succeed"""
        payload = {
            "brand": "TEST_MinimalBrand",
            "contact": "TEST_Contact",
            "email": "minimal@test.com",
            "message": ""  # Optional message
        }
        response = requests.post(f"{BASE_URL}/api/partner-inquiry", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'created'
        print(f"✓ Minimal partner inquiry created")
    
    def test_partner_inquiry_missing_required(self):
        """POST /api/partner-inquiry without required fields should fail"""
        payload = {
            "brand": "TEST_Brand"
            # Missing contact and email
        }
        response = requests.post(f"{BASE_URL}/api/partner-inquiry", json=payload)
        assert response.status_code == 422  # Validation error
        print(f"✓ Missing required fields rejected with 422")


class TestEndToEndSubscriptionFlow:
    """End-to-end subscription flow test"""
    
    def test_full_subscription_flow(self):
        """Complete flow: OTP → Verify → Create Order → Pay → Get Membership"""
        test_phone = "7777777777"
        
        # Step 1: Send OTP
        print("Step 1: Sending OTP...")
        send_resp = requests.post(f"{BASE_URL}/api/otp/send", json={"phone": test_phone})
        assert send_resp.status_code == 200
        otp = send_resp.json()['sandbox_otp']
        print(f"  ✓ OTP received: {otp}")
        
        # Step 2: Verify OTP
        print("Step 2: Verifying OTP...")
        verify_resp = requests.post(f"{BASE_URL}/api/otp/verify", json={"phone": test_phone, "otp": otp})
        assert verify_resp.status_code == 200
        assert verify_resp.json()['verified'] == True
        print(f"  ✓ Phone verified")
        
        # Step 3: Create Order
        print("Step 3: Creating payment order...")
        order_resp = requests.post(f"{BASE_URL}/api/payment/create-order", 
                                   json={"phone": test_phone, "name": "E2E Test User", "plan": "monthly"})
        assert order_resp.status_code == 200
        order_data = order_resp.json()
        order_id = order_data['order_id']
        print(f"  ✓ Order created: {order_id}")
        
        # Step 4: Verify Payment
        print("Step 4: Verifying payment...")
        pay_resp = requests.post(f"{BASE_URL}/api/payment/verify", json={
            "phone": test_phone,
            "order_id": order_id,
            "payment_id": "sandbox_pay",
            "signature": ""
        })
        assert pay_resp.status_code == 200
        pay_data = pay_resp.json()
        assert pay_data['success'] == True
        membership_id = pay_data['membership_id']
        print(f"  ✓ Payment verified, membership: {membership_id}")
        
        # Step 5: Get Membership
        print("Step 5: Fetching membership...")
        member_resp = requests.get(f"{BASE_URL}/api/membership/{test_phone}")
        assert member_resp.status_code == 200
        member_data = member_resp.json()
        assert member_data['membership_id'] == membership_id
        assert member_data['is_active'] == True
        print(f"  ✓ Membership active until: {member_data['expires_at']}")
        
        print("\n✓ FULL SUBSCRIPTION FLOW PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
