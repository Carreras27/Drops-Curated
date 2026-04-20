"""Backend tests for Telegram bot alerts + /account/* endpoints.

Iteration 13 scope — see review_request in test_reports/iteration_12.json follow-up.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://drops-curated.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Existing paid VIP-yearly subscriber with telegramChatId=99999 already linked (per review_request)
PAID_PHONE = "9876543212"
# Phones used if we need fresh ones (9876543280-9876543290)
FRESH_POOL = [f"98765432{n}" for n in range(80, 91)]


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def verified_paid_phone(client):
    """Get a verified OTP session for the existing paid subscriber."""
    r = client.post(f"{API}/otp/send", json={"phone": PAID_PHONE})
    if r.status_code == 429:
        pytest.skip(f"Rate-limited on /otp/send for {PAID_PHONE}")
    assert r.status_code == 200, f"otp/send failed: {r.status_code} {r.text}"
    body = r.json()
    otp = body.get("sandbox_otp") or body.get("otp")
    assert otp, f"No sandbox_otp returned: {body}"
    # account/login to mark verified
    r2 = client.post(f"{API}/account/login", json={"phone": PAID_PHONE, "otp": otp})
    assert r2.status_code == 200, f"account/login failed: {r2.status_code} {r2.text}"
    return PAID_PHONE


# ============ Telegram admin + link-code + webhook ============
class TestTelegramBot:
    def test_admin_status_configured(self, client):
        r = client.get(f"{API}/admin/telegram/status")
        assert r.status_code == 200
        data = r.json()
        assert data.get("configured") is True
        assert data.get("bot_username") == "Dropscurated_alerts_bot"

    def test_link_code_returns_deep_link(self, client):
        r = client.post(f"{API}/telegram/link-code", json={"phone": PAID_PHONE})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "code" in data and isinstance(data["code"], str) and len(data["code"]) > 4
        assert data["deep_link"].startswith("https://t.me/Dropscurated_alerts_bot?start=")
        assert data["deep_link"].endswith(data["code"])

    def test_link_code_invalid_phone(self, client):
        r = client.post(f"{API}/telegram/link-code", json={"phone": "123"})
        assert r.status_code == 400

    def test_link_code_unknown_phone(self, client):
        r = client.post(f"{API}/telegram/link-code", json={"phone": "9000000001"})
        assert r.status_code == 404

    def test_webhook_help(self, client):
        upd = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "chat": {"id": 88888, "username": "tester", "type": "private"},
                "text": "/help",
            },
        }
        r = client.post(f"{API}/telegram/webhook", json=upd)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert data.get("action") == "help"

    def test_webhook_start_links_chat(self, client):
        """POST /telegram/webhook with /start <code> should link telegramChatId."""
        # Mint a fresh code (uses paid phone which exists)
        r = client.post(f"{API}/telegram/link-code", json={"phone": PAID_PHONE})
        assert r.status_code == 200
        code = r.json()["code"]

        test_chat_id = 123456789
        upd = {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "chat": {"id": test_chat_id, "username": "linktester", "type": "private"},
                "text": f"/start {code}",
            },
        }
        r2 = client.post(f"{API}/telegram/webhook", json=upd)
        assert r2.status_code == 200, r2.text
        data = r2.json()
        assert data.get("action") == "linked"
        assert data.get("phone") == PAID_PHONE

        # Cleanup: restore original chat_id=99999 per review_request setup
        # (we need a verified session — but that's a separate fixture; do via /start again with new code)
        # The later telegram-disconnect test will re-connect via webhook anyway; restore chat_id=99999 manually:
        # Mint another code and use it
        r3 = client.post(f"{API}/telegram/link-code", json={"phone": PAID_PHONE})
        code2 = r3.json()["code"]
        upd2 = {
            "update_id": 3,
            "message": {
                "message_id": 3,
                "chat": {"id": 99999, "username": "original", "type": "private"},
                "text": f"/start {code2}",
            },
        }
        client.post(f"{API}/telegram/webhook", json=upd2)

    def test_webhook_start_expired_code(self, client):
        upd = {
            "update_id": 99,
            "message": {
                "message_id": 99,
                "chat": {"id": 777, "type": "private"},
                "text": "/start invalid-code-xxxx",
            },
        }
        r = client.post(f"{API}/telegram/webhook", json=upd)
        assert r.status_code == 200
        assert r.json().get("action") == "expired-code"


# ============ /account/* endpoints (use verified paid phone) ============
class TestAccountEndpoints:
    def test_account_login_and_get(self, client, verified_paid_phone):
        # login was already done in fixture; just GET snapshot
        r = client.get(f"{API}/account/{verified_paid_phone}")
        assert r.status_code == 200, r.text
        sub = r.json()["subscriber"]
        assert sub["phone"] == verified_paid_phone
        assert sub["tier"] == "vip"
        assert sub["isPaid"] is True
        # telegramLinked reflects current telegramChatId (may have been relinked in prev test)
        assert isinstance(sub["telegramLinked"], bool)

    def test_account_channels_forces_email_on(self, client, verified_paid_phone):
        # Send channels=[] — email should still be set
        r = client.post(f"{API}/account/channels",
                        json={"phone": verified_paid_phone, "channels": []})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "email" in data["notificationChannel"].split(",")

        # Verify persistence via GET
        r2 = client.get(f"{API}/account/{verified_paid_phone}")
        assert r2.status_code == 200
        assert "email" in r2.json()["subscriber"]["notificationChannel"].split(",")

    def test_account_channels_whatsapp_telegram(self, client, verified_paid_phone):
        r = client.post(f"{API}/account/channels",
                        json={"phone": verified_paid_phone, "channels": ["whatsapp", "telegram"]})
        assert r.status_code == 200
        ch = set(r.json()["notificationChannel"].split(","))
        assert ch == {"email", "telegram", "whatsapp"}

    def test_account_channels_strips_unknown(self, client, verified_paid_phone):
        r = client.post(f"{API}/account/channels",
                        json={"phone": verified_paid_phone, "channels": ["sms", "carrier-pigeon"]})
        assert r.status_code == 200
        assert r.json()["notificationChannel"] == "email"

    def test_account_pause_and_resume(self, client, verified_paid_phone):
        # pause 7 days
        r = client.post(f"{API}/account/pause",
                        json={"phone": verified_paid_phone, "days": 7})
        assert r.status_code == 200
        assert r.json()["paused_days"] == 7

        r2 = client.get(f"{API}/account/{verified_paid_phone}")
        assert r2.json()["subscriber"]["alertsPausedUntil"] is not None

        # resume (days=0)
        r3 = client.post(f"{API}/account/pause",
                         json={"phone": verified_paid_phone, "days": 0})
        assert r3.status_code == 200

        r4 = client.get(f"{API}/account/{verified_paid_phone}")
        assert r4.json()["subscriber"]["alertsPausedUntil"] is None

    def test_account_pause_invalid_days(self, client, verified_paid_phone):
        r = client.post(f"{API}/account/pause",
                        json={"phone": verified_paid_phone, "days": -5})
        assert r.status_code == 400

    def test_account_requires_otp_verification(self, client):
        # Fresh un-verified phone → 401
        fake = "9876000001"
        r = client.get(f"{API}/account/{fake}")
        assert r.status_code in (401, 400)

        r2 = client.post(f"{API}/account/channels",
                         json={"phone": fake, "channels": ["whatsapp"]})
        assert r2.status_code in (401, 400)

    def test_telegram_disconnect(self, client, verified_paid_phone):
        r = client.post(f"{API}/account/telegram-disconnect",
                        json={"phone": verified_paid_phone})
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # Verify telegramLinked now false
        r2 = client.get(f"{API}/account/{verified_paid_phone}")
        assert r2.json()["subscriber"]["telegramLinked"] is False

        # RE-LINK for cleanliness — so future runs still see chatId=99999
        link = client.post(f"{API}/telegram/link-code", json={"phone": verified_paid_phone}).json()
        upd = {
            "update_id": 500,
            "message": {
                "message_id": 500,
                "chat": {"id": 99999, "username": "restored", "type": "private"},
                "text": f"/start {link['code']}",
            },
        }
        client.post(f"{API}/telegram/webhook", json=upd)
