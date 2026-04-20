"""
Telegram Bot integration for Drops Curated.

Provides:
  - Rich HTML-formatted alerts (price drops, new drops, restocks, cross-store
    savings, daily digest) mirroring the WhatsApp + Email surfaces.
  - Deep-link account connection flow: member clicks "Connect Telegram" →
    opens t.me/<bot>?start=<code> → bot verifies code → writes subscriber's
    telegram_chat_id so future alerts can be delivered.
  - Webhook handler for inbound messages (/start <code>, /stop, etc.)

Auto-activates when TELEGRAM_BOT_TOKEN is set. Falls back to sandbox log-only
mode otherwise so preview/dev keeps running.
"""
import logging
import os
import html
import secrets
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', '').strip()
APP_URL = os.environ.get('APP_URL', 'https://dropscurated.com').strip()

IS_CONFIGURED = bool(TELEGRAM_BOT_TOKEN)
_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else ''

# In-memory link-code store (code → phone, ttl=10min). Fine for single-instance
# preview. For multi-instance production swap to MongoDB / Redis.
_LINK_CODES: dict = {}
_LINK_TTL_S = 600


# ============ LINK-CODE FLOW ============
def create_link_code(phone: str) -> str:
    """Mint a one-time code that the /start deep-link will carry. Phone is the
    primary subscriber identifier."""
    # Prune expired first
    now = time.time()
    for c in list(_LINK_CODES.keys()):
        if _LINK_CODES[c]['expires'] < now:
            del _LINK_CODES[c]
    code = secrets.token_urlsafe(8)
    _LINK_CODES[code] = {'phone': phone, 'expires': now + _LINK_TTL_S}
    return code


def consume_link_code(code: str) -> Optional[str]:
    """Look up phone for a code and invalidate it. Returns None if expired/unknown."""
    entry = _LINK_CODES.pop(code, None)
    if not entry or entry['expires'] < time.time():
        return None
    return entry['phone']


def deep_link_for(code: str) -> str:
    """Return the t.me URL a user must click to link their account."""
    bot = TELEGRAM_BOT_USERNAME or 'Dropscurated_alerts_bot'
    return f"https://t.me/{bot}?start={code}"


# ============ HTML HELPERS ============
# Telegram supports a subset of HTML: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
# NO arbitrary tags, NO styles. We use the parse_mode="HTML" sendMessage API.
def _esc(s) -> str:
    return html.escape(str(s or ''), quote=False)


def _fmt_inr(v) -> str:
    try:
        return f"₹{int(float(v)):,}"
    except (TypeError, ValueError):
        return f"₹{v}"


# ============ LOW-LEVEL SEND ============
async def _send_message(chat_id, text: str, photo_url: Optional[str] = None,
                        reply_markup: Optional[dict] = None) -> tuple:
    """Send a message (or photo+caption) to a chat. Returns (success, message_id_or_err)."""
    if not IS_CONFIGURED:
        logger.info(f"[TelegramSandbox] Would send to chat={chat_id}: {text[:80]}")
        return True, 'sandbox'

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if photo_url:
                payload = {
                    'chat_id': chat_id,
                    'photo': photo_url,
                    'caption': text,
                    'parse_mode': 'HTML',
                }
                if reply_markup:
                    payload['reply_markup'] = reply_markup
                r = await client.post(f"{_API}/sendPhoto", json=payload)
            else:
                payload = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': False,
                }
                if reply_markup:
                    payload['reply_markup'] = reply_markup
                r = await client.post(f"{_API}/sendMessage", json=payload)

            data = r.json()
            if data.get('ok'):
                return True, data.get('result', {}).get('message_id')
            logger.error(f"[Telegram] API error: {data}")
            return False, data.get('description', 'unknown')
    except Exception as e:
        logger.error(f"[Telegram] Transport error: {e}")
        return False, f"err: {e}"


# ============ ALERT TEMPLATES ============
def _view_button(url: str, label: str = 'View Product') -> dict:
    return {'inline_keyboard': [[{'text': label, 'url': url}]]}


async def send_price_drop_alert(chat_id, product_name: str, new_price, old_price,
                                brand: str = '', image_url: str = '',
                                product_url: str = '', savings_pct: Optional[int] = None) -> tuple:
    save_badge = f"  💎 <b>Save {savings_pct}%</b>" if savings_pct else ''
    text = (
        f"🔥 <b>Price Drop Alert</b>\n\n"
        f"<b>{_esc(product_name)}</b>\n"
        f"<i>{_esc(brand)}</i>\n\n"
        f"<b>{_fmt_inr(new_price)}</b>  <s>{_fmt_inr(old_price)}</s>{save_badge}\n\n"
        f"Act fast — premium drops move quickly."
    )
    return await _send_message(chat_id, text, photo_url=image_url or None,
                               reply_markup=_view_button(product_url, 'View Product →') if product_url else None)


async def send_new_drop_alert(chat_id, product_name: str, price, brand: str = '',
                              image_url: str = '', product_url: str = '',
                              is_restock: bool = False) -> tuple:
    header = '📦 <b>Back in Stock</b>' if is_restock else '✨ <b>New Drop</b>'
    text = (
        f"{header}\n\n"
        f"<b>{_esc(product_name)}</b>\n"
        f"<i>{_esc(brand)}</i>\n\n"
        f"<b>{_fmt_inr(price)}</b>\n\n"
        f"Fresh arrival — curated for you."
    )
    return await _send_message(chat_id, text, photo_url=image_url or None,
                               reply_markup=_view_button(product_url, 'Secure Yours →') if product_url else None)


async def send_cross_store_save_alert(chat_id, product_name: str, brand: str,
                                      cheapest_price, source_price,
                                      cheapest_store: str, cheapest_url: str,
                                      image_url: str, savings_amount, savings_pct) -> tuple:
    store_label = cheapest_store.replace('_', ' ').title()
    text = (
        f"🔀 <b>Cheaper Elsewhere</b>\n\n"
        f"<b>{_esc(product_name)}</b>\n"
        f"<i>{_esc(brand)}</i>\n\n"
        f"<b>{_fmt_inr(cheapest_price)}</b>  <s>{_fmt_inr(source_price)}</s>  💎 <b>Save {savings_pct}%</b>\n"
        f"Available at <b>{_esc(store_label)}</b>\n\n"
        f"Save {_fmt_inr(savings_amount)} on the exact same product."
    )
    return await _send_message(chat_id, text, photo_url=image_url or None,
                               reply_markup=_view_button(cheapest_url, f'Buy at {store_label} →') if cheapest_url else None)


async def send_daily_digest(chat_id, date_str: str, alerts: list) -> tuple:
    new_drops = [a for a in alerts if a.get('type') == 'new_release']
    price_drops = [a for a in alerts if a.get('type') == 'price_drop']
    restocks = [a for a in alerts if a.get('type') == 'restock']
    cross_saves = [a for a in alerts if a.get('type') == 'cross_store_save']

    lines = [f"🌙 <b>Your Daily Drops · {_esc(date_str)}</b>\n"]
    if new_drops:
        lines.append(f"✨ <b>{len(new_drops)} New Arrivals</b>")
        for a in new_drops[:3]:
            d = a.get('data', {})
            lines.append(f"  • {_esc(d.get('name', 'Product')[:45])} — {_fmt_inr(d.get('price', 0))}")
        if len(new_drops) > 3:
            lines.append(f"  <i>…and {len(new_drops) - 3} more</i>")
        lines.append('')
    if price_drops:
        lines.append(f"🔥 <b>{len(price_drops)} Price Drops</b>")
        for a in price_drops[:3]:
            d = a.get('data', {})
            lines.append(f"  • {_esc(d.get('name', 'Product')[:45])} — {_fmt_inr(d.get('new_price', 0))} <s>{_fmt_inr(d.get('old_price', 0))}</s>")
        if len(price_drops) > 3:
            lines.append(f"  <i>…and {len(price_drops) - 3} more</i>")
        lines.append('')
    if restocks:
        lines.append(f"📦 <b>{len(restocks)} Back in Stock</b>")
        for a in restocks[:3]:
            d = a.get('data', {})
            lines.append(f"  • {_esc(d.get('name', 'Product')[:45])}")
        lines.append('')
    if cross_saves:
        lines.append(f"🔀 <b>{len(cross_saves)} Cheaper Elsewhere</b>")
        for a in cross_saves[:3]:
            d = a.get('data', {})
            store = (d.get('cheapestStore') or '').replace('_', ' ').title()
            lines.append(f"  • {_esc(d.get('name', 'Product')[:40])} — {_fmt_inr(d.get('cheapestPrice', 0))} at {_esc(store)} (save {d.get('savingsPct', 0)}%)")
        lines.append('')

    lines.append(f'<a href="{APP_URL}/browse">Browse all drops →</a>')
    text = '\n'.join(lines).strip()
    return await _send_message(chat_id, text)


async def send_welcome_message(chat_id, phone: str) -> tuple:
    masked = phone[:3] + 'X' * 4 + phone[-3:] if len(phone) >= 6 else phone
    text = (
        "🎉 <b>Connected!</b>\n\n"
        f"You're now linked to your Drops Curated account ({masked}).\n\n"
        "From now on, your drop alerts will land right here. "
        "Manage channels or pause alerts at any time from your account page."
    )
    return await _send_message(chat_id, text,
                               reply_markup={'inline_keyboard': [[{'text': 'Open Account', 'url': f'{APP_URL}/account'}]]})


# ============ WEBHOOK HANDLER ============
async def handle_webhook_update(db, update: dict) -> dict:
    """Process an incoming Telegram update. Called by FastAPI webhook endpoint.

    Handles:
      /start <code> → link a subscriber's telegram_chat_id
      /stop         → pause telegram alerts for this chat
      /help         → short help text
    """
    msg = update.get('message') or update.get('edited_message') or {}
    chat = msg.get('chat') or {}
    chat_id = chat.get('id')
    text = (msg.get('text') or '').strip()
    username = chat.get('username', '')

    if not chat_id:
        return {'ok': True, 'skipped': 'no-chat'}

    if text.startswith('/start'):
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ''
        if not code:
            await _send_message(chat_id,
                                "👋 <b>Welcome to Drops Curated Alerts</b>\n\n"
                                "To connect your account, go to your Drops Curated "
                                "account page and click <b>Connect Telegram</b>. "
                                f"\n\n{_esc(APP_URL)}/account")
            return {'ok': True, 'action': 'start-no-code'}
        phone = consume_link_code(code)
        if not phone:
            await _send_message(chat_id,
                                "❌ <b>Link expired</b>\n\n"
                                "That connection code is no longer valid. "
                                "Please generate a fresh one from your account page.")
            return {'ok': True, 'action': 'expired-code'}
        # Link subscriber to this chat
        await db.subscribers.update_one(
            {'phone': phone},
            {'$set': {
                'telegramChatId': chat_id,
                'telegramUsername': username,
                'telegramLinkedAt': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            }}
        )
        # Ensure telegram is in their channel preferences
        await db.subscribers.update_one(
            {'phone': phone},
            {'$set': {'preferences.telegram_username': username}}
        )
        await send_welcome_message(chat_id, phone)
        logger.info(f"[Telegram] Linked chat_id={chat_id} → phone={phone}")
        return {'ok': True, 'action': 'linked', 'phone': phone}

    if text.startswith('/stop'):
        res = await db.subscribers.update_one(
            {'telegramChatId': chat_id},
            {'$unset': {'telegramChatId': '', 'telegramUsername': ''}}
        )
        if res.modified_count:
            await _send_message(chat_id,
                                "🔕 <b>Telegram alerts paused</b>\n\n"
                                "You won't receive drop alerts here anymore. "
                                "Email alerts (if enabled) continue as usual.")
        else:
            await _send_message(chat_id, "No account linked to this chat.")
        return {'ok': True, 'action': 'stop'}

    if text.startswith('/help') or text == '/':
        await _send_message(chat_id,
                            "<b>Drops Curated Bot</b>\n\n"
                            "Commands:\n"
                            "• <code>/start &lt;code&gt;</code> — link your account\n"
                            "• <code>/stop</code> — pause Telegram alerts\n"
                            "• <code>/help</code> — this message\n\n"
                            f"Manage everything at {APP_URL}/account")
        return {'ok': True, 'action': 'help'}

    # Unknown message
    await _send_message(chat_id,
                        "I only understand a few commands — try <code>/help</code>, "
                        f"or manage your preferences at {APP_URL}/account")
    return {'ok': True, 'action': 'unknown'}


# ============ WEBHOOK MANAGEMENT ============
async def set_webhook(webhook_url: str) -> tuple:
    """Register our webhook with Telegram. Idempotent — safe to call on boot."""
    if not IS_CONFIGURED:
        logger.info(f"[TelegramSandbox] Would set webhook to {webhook_url}")
        return True, 'sandbox'
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{_API}/setWebhook",
                                  json={'url': webhook_url, 'allowed_updates': ['message']})
            data = r.json()
            if data.get('ok'):
                logger.info(f"[Telegram] Webhook set to {webhook_url}")
                return True, data.get('description', 'ok')
            logger.error(f"[Telegram] setWebhook failed: {data}")
            return False, data.get('description', 'unknown')
    except Exception as e:
        logger.error(f"[Telegram] setWebhook transport error: {e}")
        return False, str(e)


async def get_webhook_info() -> dict:
    """Query Telegram for current webhook status (debug)."""
    if not IS_CONFIGURED:
        return {'configured': False}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{_API}/getWebhookInfo")
            return r.json()
    except Exception as e:
        return {'ok': False, 'error': str(e)}
