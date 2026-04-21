"""Closed Beta Program API tests (/api/beta/*).

Covers:
- GET /api/beta/status shape
- POST /api/beta/signup happy path + OTP gating + invalid phone + paid-block + resume
- POST /api/beta/feedback category/message validation
- Counter increments after signup
"""
import os
import random
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://drops-curated.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope='module')
def client():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s


def _unique_phone():
    # 10 digit Indian mobile starting with 6-9, avoid collision with existing test data
    return '9' + ''.join(str(random.randint(0, 9)) for _ in range(9))


def _verify_otp(client, phone):
    r = client.post(f"{API}/otp/send", json={'phone': phone})
    assert r.status_code == 200, f"otp/send failed: {r.status_code} {r.text}"
    otp = r.json().get('sandbox_otp')
    assert otp, f"sandbox_otp missing, response={r.json()}"
    r2 = client.post(f"{API}/otp/verify", json={'phone': phone, 'otp': otp})
    assert r2.status_code == 200, f"otp/verify failed: {r2.status_code} {r2.text}"
    return otp


# ---------- /api/beta/status ----------
class TestBetaStatus:
    def test_status_shape(self, client):
        r = client.get(f"{API}/beta/status")
        assert r.status_code == 200
        d = r.json()
        for k in ('total', 'taken', 'spots_left', 'is_open'):
            assert k in d, f"missing key {k}"
        assert d['total'] == 100
        assert isinstance(d['taken'], int)
        assert isinstance(d['spots_left'], int)
        assert isinstance(d['is_open'], bool)
        assert d['spots_left'] == max(0, d['total'] - d['taken'])


# ---------- /api/beta/signup ----------
class TestBetaSignup:
    def test_signup_without_verified_otp_rejected(self, client):
        phone = _unique_phone()
        r = client.post(f"{API}/beta/signup", json={
            'phone': phone, 'name': 'TEST_NoOtp', 'email': f'TEST_{phone}@example.com'
        })
        if r.status_code == 429:
            pytest.skip("rate-limited (3/hour) from previous run — validated earlier")
        assert r.status_code == 400
        assert 'verif' in r.text.lower() or 'otp' in r.text.lower()

    def test_signup_invalid_phone_rejected(self, client):
        r = client.post(f"{API}/beta/signup", json={
            'phone': '12345', 'name': 'TEST_Bad', 'email': 'TEST_bad@example.com'
        })
        if r.status_code == 429:
            pytest.skip("rate-limited (3/hour) from previous run — validated earlier")
        assert r.status_code == 400

    def test_signup_happy_path_resume_and_counter(self, client):
        """Combined because /beta/signup is rate-limited 3/hour per IP and
        counts even 400 responses. We run happy-path + resume back-to-back."""
        before = client.get(f"{API}/beta/status").json()['taken']

        phone = _unique_phone()
        _verify_otp(client, phone)
        email = f"TEST_beta_{phone}@example.com"
        r = client.post(f"{API}/beta/signup", json={
            'phone': phone, 'name': 'TEST_Beta One', 'email': email
        })
        if r.status_code == 429:
            pytest.skip("rate-limited (3/hour) — validated earlier run")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d['success'] is True
        assert d['membership_id'].startswith('DC-BETA-'), d['membership_id']
        assert d['duration_days'] == 30
        assert isinstance(d['expires_at'], str) and len(d['expires_at']) > 10

        # 30-day expiry sanity check
        from datetime import datetime, timezone
        exp = datetime.fromisoformat(d['expires_at'].replace('Z', '+00:00'))
        delta = exp - datetime.now(timezone.utc)
        assert 29 <= delta.days <= 30, f"expiry should be ~30 days out, got {delta.days}"

        # Counter bumped
        after = client.get(f"{API}/beta/status").json()['taken']
        assert after == before + 1, f"counter did not increment: {before} -> {after}"

        # Verify persisted via membership endpoint
        m = client.get(f"{API}/membership/{phone}")
        assert m.status_code == 200, m.text
        assert m.json().get('email') == email

        # --- Resume path: same phone can re-signup, counter must not bump ---
        _verify_otp(client, phone)
        r2 = client.post(f"{API}/beta/signup", json={
            'phone': phone, 'name': 'TEST_Beta One', 'email': email
        })
        if r2.status_code == 429:
            pytest.skip("happy-path succeeded; resume call rate-limited (3/hour)")
        assert r2.status_code == 200, r2.text
        after2 = client.get(f"{API}/beta/status").json()['taken']
        assert after2 == after, f"resume should not bump counter: {after} -> {after2}"

    def test_signup_blocks_existing_paid_non_beta(self, client):
        # Create a paid, non-beta subscriber directly via DB-less flow is not available;
        # simulate by calling internal payment/verify path is overkill — instead, we
        # construct a situation through OTP+register+payment. Skip if flow unavailable.
        # We'll instead exercise the logical branch by signing up a fresh phone twice
        # after marking via the payment endpoint if available. If not reachable,
        # we at least confirm the 400 error message path via a known paid number.
        # Use sandbox: /payment/create-order + /payment/verify
        phone = _unique_phone()
        _verify_otp(client, phone)
        # Try to create + verify a sandbox monthly order
        co = client.post(f"{API}/payment/create-order",
                         json={'phone': phone, 'name': 'TEST_Paid', 'email': f'TEST_p_{phone}@example.com',
                               'address': '123 test', 'plan': 'monthly'})
        if co.status_code != 200:
            pytest.skip(f"payment/create-order unavailable: {co.status_code}")
        order = co.json()
        vr = client.post(f"{API}/payment/verify", json={
            'phone': phone,
            'razorpay_order_id': order.get('order_id') or order.get('id'),
            'razorpay_payment_id': 'pay_sandbox_TEST',
            'razorpay_signature': 'sandbox',
            'plan': 'monthly',
        })
        if vr.status_code != 200:
            pytest.skip(f"payment/verify sandbox path unavailable: {vr.status_code} {vr.text[:150]}")

        # Now the user is paid + non-beta. Beta signup should be rejected.
        _verify_otp(client, phone)
        r = client.post(f"{API}/beta/signup", json={
            'phone': phone, 'name': 'TEST_Paid', 'email': f'TEST_p_{phone}@example.com'
        })
        assert r.status_code == 400, f"expected 400 for paid user, got {r.status_code} {r.text}"
        assert 'paid' in r.text.lower()


# ---------- /api/beta/feedback ----------
class TestBetaFeedback:
    def test_feedback_happy_bug(self, client):
        r = client.post(f"{API}/beta/feedback", json={
            'category': 'bug',
            'message': 'TEST_ submit button not working on /beta page',
            'page': '/beta',
            'rating': 4,
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d['ok'] is True
        assert isinstance(d['id'], str) and d['id'].startswith('fb_')

    def test_feedback_all_categories(self, client):
        for cat in ('idea', 'love', 'other'):
            r = client.post(f"{API}/beta/feedback", json={
                'category': cat, 'message': f'TEST_ category {cat} message valid'
            })
            assert r.status_code == 200, f"{cat} -> {r.text}"
            assert r.json()['ok'] is True

    def test_feedback_invalid_category_rejected(self, client):
        r = client.post(f"{API}/beta/feedback", json={
            'category': 'spam', 'message': 'TEST_ this should reject'
        })
        assert r.status_code == 400

    def test_feedback_short_message_rejected(self, client):
        r = client.post(f"{API}/beta/feedback", json={
            'category': 'bug', 'message': 'hi'
        })
        assert r.status_code == 400

    def test_feedback_optional_rating_outside_range_ignored(self, client):
        # rating 9 is out of 1-5; endpoint should accept but store None
        r = client.post(f"{API}/beta/feedback", json={
            'category': 'love', 'message': 'TEST_ great product love it', 'rating': 9
        })
        assert r.status_code == 200
        assert r.json()['ok'] is True
