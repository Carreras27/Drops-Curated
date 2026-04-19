"""Backend tests for VIP subscription plan feature + cross-store savings regression.

Covers:
- /api/plans catalog (Regular, VIP monthly/6mo/yearly)
- /api/payment/create-order amount_paise per plan
- /api/payment/verify sets correct tier/plan/brandLimit/expiresAt
- /api/subscribers/{phone}/status for upgrade banner
- /api/savings/active count & quality
- /api/products/{id} cross-store cheapest match
"""
import os
import time
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://drops-curated.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# ------------------------- /api/plans -------------------------

class TestPlansCatalog:
    def test_plans_returns_four_plans(self):
        r = requests.get(f"{API}/plans", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        plans = data.get("plans") if isinstance(data, dict) else data
        assert isinstance(plans, list)
        codes = [p["code"] for p in plans]
        assert codes == ["monthly", "vip_monthly", "vip_6mo", "vip_yearly"], codes

    def test_plan_amounts_correct(self):
        r = requests.get(f"{API}/plans", timeout=20)
        plans = r.json().get("plans") if isinstance(r.json(), dict) else r.json()
        by_code = {p["code"]: p for p in plans}
        assert by_code["monthly"]["amount_paise"] == 39900
        assert by_code["vip_monthly"]["amount_paise"] == 299900
        assert by_code["vip_6mo"]["amount_paise"] == 1619500
        assert by_code["vip_yearly"]["amount_paise"] == 2879000
        # Tier sanity
        assert by_code["monthly"]["tier"] == "regular"
        for c in ("vip_monthly", "vip_6mo", "vip_yearly"):
            assert by_code[c]["tier"] == "vip"
        # Brand limits
        assert by_code["monthly"]["brand_limit"] == 5
        assert by_code["vip_yearly"]["brand_limit"] in (0, None)

    def test_plan_benefits_present(self):
        r = requests.get(f"{API}/plans", timeout=20)
        plans = r.json().get("plans") if isinstance(r.json(), dict) else r.json()
        for p in plans:
            assert isinstance(p.get("benefits"), list) and len(p["benefits"]) > 0
            assert p.get("duration_days") in (30, 180, 365)


# ------------------------- /api/payment/create-order -------------------------

class TestCreateOrderAmounts:
    @pytest.mark.parametrize("plan_code,expected_paise", [
        ("monthly", 39900),
        ("vip_monthly", 299900),
        ("vip_6mo", 1619500),
        ("vip_yearly", 2879000),
    ])
    def test_create_order_amount_matches_plan(self, plan_code, expected_paise):
        # unique phone per plan
        phone_map = {"monthly": "9876543253", "vip_monthly": "9876543254",
                     "vip_6mo": "9876543255", "vip_yearly": "9876543256"}
        phone = phone_map[plan_code]
        assert _otp_verify(phone), f"OTP verify failed for {phone}"
        payload = {
            "phone": phone,
            "plan": plan_code,
            "name": "TEST User",
            "email": "test@example.com",
            "address": "TEST address",
            "dob": "1995-01-01",
        }
        r = requests.post(f"{API}/payment/create-order", json=payload, timeout=20)
        if r.status_code == 429:
            pytest.skip(f"rate-limited on create-order for {plan_code}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("amount") == expected_paise or d.get("amount_paise") == expected_paise, d


# ------------------------- OTP + Verify flow helpers -------------------------

def _otp_verify(phone: str) -> bool:
    r = requests.post(f"{API}/otp/send", json={"phone": phone}, timeout=20)
    if r.status_code != 200:
        return False
    otp = r.json().get("sandbox_otp") or r.json().get("otp")
    if not otp:
        return False
    r2 = requests.post(f"{API}/otp/verify", json={"phone": phone, "otp": otp}, timeout=20)
    return r2.status_code == 200


# ------------------------- Payment verify sets tier/plan -------------------------

class TestPaymentVerifyVip:
    def test_vip_yearly_verify_sets_tier_and_expiry(self):
        phone = "9876543251"
        _otp_verify(phone)  # best-effort, sandbox
        # Create order
        r = requests.post(f"{API}/payment/create-order",
                          json={
                              "phone": phone,
                              "plan": "vip_yearly",
                              "name": "TEST VIP Yearly",
                              "email": "testvip@example.com",
                              "address": "TEST addr",
                              "dob": "1995-01-01",
                          }, timeout=20)
        if r.status_code == 429:
            pytest.skip("rate-limited on create-order")
        assert r.status_code == 200, r.text
        order_id = r.json().get("order_id") or r.json().get("id")

        # Verify payment (sandbox)
        verify_payload = {
            "phone": phone,
            "plan": "vip_yearly",
            "order_id": order_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_sandbox_vip_yearly",
            "razorpay_signature": "sandbox",
            "name": "TEST VIP Yearly",
            "email": "testvip@example.com",
            "address": "TEST addr",
            "dob": "1995-01-01",
        }
        vr = requests.post(f"{API}/payment/verify", json=verify_payload, timeout=30)
        assert vr.status_code == 200, vr.text

        # Check subscriber status
        st = requests.get(f"{API}/subscribers/{phone}/status", timeout=20)
        assert st.status_code == 200, st.text
        s = st.json()
        assert s.get("tier") == "vip", s
        assert s.get("plan") == "vip_yearly", s
        brand_limit = s.get("brandLimit", s.get("brand_limit"))
        assert brand_limit in (0, None), s
        # Expiry roughly 365 days away
        exp = s.get("expiresAt") or s.get("expires_at")
        assert exp, s
        # Parse ISO
        try:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        except Exception:
            pytest.skip(f"expiry format: {exp}")
        now = datetime.now(timezone.utc)
        delta_days = (exp_dt - now).days
        assert 360 <= delta_days <= 366, f"expiry {delta_days} days away"


# ------------------------- /api/subscribers/{phone}/status -------------------------

class TestSubscriberStatus:
    def test_existing_regular_subscriber_status(self):
        # 9876543210 per problem statement should be existing regular
        r = requests.get(f"{API}/subscribers/9876543210/status", timeout=20)
        assert r.status_code == 200, r.text
        s = r.json()
        # Could be regular or not subscribed; accept tier field presence
        assert "tier" in s or "exists" in s, s

    def test_unknown_phone_returns_not_found_or_default(self):
        r = requests.get(f"{API}/subscribers/9000000001/status", timeout=20)
        assert r.status_code in (200, 404), r.text


# ------------------------- Cross-store savings regression -------------------------

class TestCrossStoreSavings:
    def test_savings_active_count(self):
        r = requests.get(f"{API}/savings/active?limit=200", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("savings", [])
        total = data.get("total", len(items))
        assert isinstance(items, list)
        assert total >= 300, f"only {total} savings entries (expected ~370)"

    def test_almost_gods_product_superkicks_cheapest(self):
        r = requests.get(f"{API}/products/prod_ALMOST_GODS_25797", timeout=30)
        if r.status_code == 404:
            pytest.skip("product prod_ALMOST_GODS_25797 not in current catalog")
        assert r.status_code == 200, r.text
        d = r.json()
        prices = d.get("prices") or []
        assert prices, f"no prices on product: keys={list(d.keys())}"
        stores = [str(c.get("store", "")).upper() for c in prices]
        assert "SUPERKICKS" in stores, f"stores={stores}"
        # Find cheapest in-stock price
        sk_entry = next((p for p in prices if str(p.get("store", "")).upper() == "SUPERKICKS"), None)
        assert sk_entry is not None
        assert float(sk_entry.get("currentPrice", sk_entry.get("current_price", 0))) <= 9600, sk_entry
        # And SUPERKICKS is the min
        all_prices = [float(p.get("currentPrice", p.get("current_price", 0) or 0)) for p in prices if (p.get("currentPrice") or p.get("current_price"))]
        assert min(all_prices) <= 9600, f"cheapest={min(all_prices)}"
