"""
Brevo email alerts — rich HTML notifications for Drops Curated members.

Mirrors the WhatsApp alert surface (price drops, new drops, restocks,
cross-store savings, daily digest) so a subscriber's `notificationChannel`
preference ('email' | 'whatsapp' | 'both') routes transparently to the
matching channel.

Auto-activates when BREVO_API_KEY is set in backend/.env. Falls back to
sandbox logging mode when unset so dev/preview keeps working.
"""
import logging
import os
from typing import Optional

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)

# ============ CONFIG ============
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', 'alerts@dropscurated.com').strip()
BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'Drops Curated Alerts').strip()
BREVO_REPLY_TO = os.environ.get('BREVO_REPLY_TO', 'Dropscurated@gmail.com').strip()
APP_URL = os.environ.get('APP_URL', 'https://dropscurated.com').strip()

IS_CONFIGURED = bool(BREVO_API_KEY)


def _client() -> Optional[sib_api_v3_sdk.TransactionalEmailsApi]:
    if not IS_CONFIGURED:
        return None
    cfg = sib_api_v3_sdk.Configuration()
    cfg.api_key['api-key'] = BREVO_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(cfg))


# ============ HTML HELPERS ============
_BASE_CSS = """
body{margin:0;padding:0;background:#F3F1ED;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#001F3F}
.wrap{max-width:600px;margin:0 auto;background:#FAF8F5}
.hdr{background:#001F3F;color:#FAF8F5;padding:28px 32px;text-align:left}
.hdr .logo{font-family:Georgia,serif;font-size:22px;letter-spacing:.02em;margin:0}
.hdr .tag{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#D4AF37;margin:4px 0 0}
.hero{padding:32px}
.kicker{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#D4AF37;font-weight:600;margin:0 0 10px}
h1{font-family:Georgia,serif;font-size:26px;line-height:1.2;margin:0 0 10px;font-weight:400}
p{line-height:1.55;font-size:14px;color:#001F3F;margin:0 0 14px}
.prod{margin:22px 0;padding:0;border:1px solid rgba(0,31,63,.08)}
.prod img{display:block;width:100%;height:auto}
.prod .info{padding:18px 20px}
.prod .pname{font-size:15px;font-weight:500;margin:0 0 4px;color:#001F3F}
.prod .pbrand{font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:rgba(0,31,63,.5);margin:0 0 12px}
.price-big{font-family:Georgia,serif;font-size:26px;color:#001F3F;margin:0}
.price-old{text-decoration:line-through;color:rgba(0,31,63,.35);font-size:14px;margin-left:10px;vertical-align:middle}
.save{display:inline-block;background:#D4AF37;color:#001F3F;padding:4px 10px;font-size:10px;letter-spacing:.15em;text-transform:uppercase;margin-left:10px;vertical-align:middle;font-weight:600}
.btn{display:inline-block;background:#001F3F;color:#FAF8F5 !important;padding:14px 30px;text-decoration:none;font-size:13px;letter-spacing:.05em;margin-top:14px;font-weight:500}
.btn:hover{opacity:.9}
.divider{height:1px;background:rgba(0,31,63,.08);margin:24px 0}
.ftr{background:#001F3F;color:rgba(250,248,245,.55);padding:24px 32px;font-size:11px;line-height:1.6}
.ftr a{color:#D4AF37;text-decoration:none}
"""


def _shell(inner_html: str, preheader: str = '') -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light only">
<meta name="supported-color-schemes" content="light only">
<title>Drops Curated Alert</title>
<!--[if mso]><style>*{{font-family:Arial,sans-serif !important}}</style><![endif]-->
<style>
:root {{ color-scheme: light only; supported-color-schemes: light only; }}
{_BASE_CSS}
/* Gmail dark-mode overrides — force brand colors, block auto-inversion */
u + .body .wrap,
body[data-ogsc] .wrap {{ background:#FAF8F5 !important }}
u + .body .hdr,
body[data-ogsc] .hdr {{ background:#001F3F !important; color:#FAF8F5 !important }}
u + .body .hdr .logo,
body[data-ogsc] .hdr .logo {{ color:#FAF8F5 !important }}
u + .body .hdr .tag,
body[data-ogsc] .hdr .tag {{ color:#D4AF37 !important }}
u + .body .hero,
body[data-ogsc] .hero {{ background:#FAF8F5 !important; color:#001F3F !important }}
u + .body h1,
u + .body p,
u + .body .pname,
u + .body .price-big,
body[data-ogsc] h1,
body[data-ogsc] p,
body[data-ogsc] .pname,
body[data-ogsc] .price-big {{ color:#001F3F !important }}
u + .body .kicker,
body[data-ogsc] .kicker {{ color:#D4AF37 !important }}
/* SAVE badge: gold background MUST stay gold; text MUST stay navy for contrast */
u + .body .save,
body[data-ogsc] .save {{ background:#D4AF37 !important; color:#001F3F !important }}
u + .body .btn,
body[data-ogsc] .btn {{ background:#001F3F !important; color:#FAF8F5 !important }}
u + .body .ftr,
body[data-ogsc] .ftr {{ background:#001F3F !important; color:rgba(250,248,245,.55) !important }}
</style>
</head>
<body class="body" style="margin:0;padding:0;background:#F3F1ED;">
<span style="display:none !important;max-height:0;overflow:hidden;color:transparent;visibility:hidden;opacity:0;font-size:1px;line-height:1px">{preheader}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F3F1ED"><tr><td align="center" style="padding:16px 0">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#FAF8F5">
<tr><td style="background:#001F3F;color:#FAF8F5;padding:28px 32px" class="hdr">
  <p style="margin:0;font-family:Georgia,serif;font-size:22px;color:#FAF8F5" class="logo">Drops Curated</p>
  <p style="margin:4px 0 0;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#D4AF37" class="tag">Curated Streetwear Intelligence</p>
</td></tr>
<tr><td style="background:#FAF8F5">{inner_html}</td></tr>
<tr><td style="background:#001F3F;color:rgba(250,248,245,.55);padding:24px 32px;font-size:11px;line-height:1.6" class="ftr">
  You're receiving this because email alerts are enabled in your Drops Curated preferences.<br>
  <a href="{APP_URL}/account" style="color:#D4AF37;text-decoration:none">Manage preferences</a> &nbsp;·&nbsp;
  <a href="{APP_URL}/account" style="color:#D4AF37;text-decoration:none">Unsubscribe</a>
  <br><br>© 2026 Drops Curated · Curated Intelligence for India's Premium Drops
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _fmt_inr(value) -> str:
    try:
        return f"₹{int(float(value)):,}"
    except (TypeError, ValueError):
        return f"₹{value}"


# ============ TEMPLATES ============
def _tpl_price_drop(name: str, brand: str, new_price, old_price,
                    image_url: str, product_url: str, savings_pct: Optional[int] = None) -> str:
    # Guard: only render "Save X%" badge when savings_pct is a real positive
    # number AND the old_price is actually higher than new_price. Otherwise
    # the badge is fictitious (e.g. merchant MSRP spam).
    real_save = False
    try:
        np = float(str(new_price).replace(',', '').replace('₹', '').strip())
        op = float(str(old_price).replace(',', '').replace('₹', '').strip())
        real_save = savings_pct and savings_pct > 0 and op > np * 1.01
    except (ValueError, TypeError):
        real_save = bool(savings_pct)

    save_badge = (f'<span class="save" style="display:inline-block;background:#D4AF37;color:#001F3F;'
                  f'padding:4px 10px;font-size:10px;letter-spacing:.15em;text-transform:uppercase;'
                  f'margin-left:10px;vertical-align:middle;font-weight:700">Save {savings_pct}%</span>') if real_save else ''
    # Only show the old price strikethrough if the save is genuine
    old_price_html = f'<span class="price-old">{_fmt_inr(old_price)}</span>' if real_save else ''
    img = f'<img src="{image_url}" alt="{name}">' if image_url else ''
    inner = f"""
<div class="hero">
  <p class="kicker">Price Drop Alert</p>
  <h1>The price just dropped on something you're watching.</h1>
  <p>A product you've been tracking is now available at a lower price. Act quickly — premium drops move fast in the community.</p>
  <div class="prod">{img}
    <div class="info">
      <p class="pbrand">{brand}</p>
      <p class="pname">{name}</p>
      <p class="price-big">{_fmt_inr(new_price)}{old_price_html}{save_badge}</p>
      <a href="{product_url}" class="btn">View Product →</a>
    </div>
  </div>
</div>"""
    preheader = f"{brand} {name} dropped to {_fmt_inr(new_price)}"
    return _shell(inner, preheader)


def _tpl_new_drop(name: str, brand: str, price, image_url: str, product_url: str,
                  tag: str = 'New Drop') -> str:
    img = f'<img src="{image_url}" alt="{name}">' if image_url else ''
    inner = f"""
<div class="hero">
  <p class="kicker">{tag}</p>
  <h1>Fresh on the shelf — curated for you.</h1>
  <p>Your preferences matched a new arrival from a brand you follow. First-mover advantage on premium streetwear starts here.</p>
  <div class="prod">{img}
    <div class="info">
      <p class="pbrand">{brand}</p>
      <p class="pname">{name}</p>
      <p class="price-big">{_fmt_inr(price)}</p>
      <a href="{product_url}" class="btn">Secure Yours →</a>
    </div>
  </div>
</div>"""
    return _shell(inner, f"New from {brand}: {name}")


def _tpl_cross_store(name: str, brand: str, cheapest_price, source_price,
                     cheapest_store: str, cheapest_url: str, image_url: str,
                     savings_amount, savings_pct) -> str:
    store_label = cheapest_store.replace('_', ' ').title()
    img = f'<img src="{image_url}" alt="{name}">' if image_url else ''
    inner = f"""
<div class="hero">
  <p class="kicker">Cheaper Elsewhere</p>
  <h1>Same product. Lower price. We found it.</h1>
  <p>Our cross-store engine spotted this exact item at a better price on another authorised store. Save {_fmt_inr(savings_amount)} instantly.</p>
  <div class="prod">{img}
    <div class="info">
      <p class="pbrand">{brand} · Available at {store_label}</p>
      <p class="pname">{name}</p>
      <p class="price-big">{_fmt_inr(cheapest_price)}<span class="price-old">{_fmt_inr(source_price)}</span><span class="save" style="display:inline-block;background:#D4AF37;color:#001F3F;padding:4px 10px;font-size:10px;letter-spacing:.15em;text-transform:uppercase;margin-left:10px;vertical-align:middle;font-weight:700">Save {savings_pct}%</span></p>
      <a href="{cheapest_url}" class="btn">Buy at {store_label} →</a>
    </div>
  </div>
</div>"""
    return _shell(inner, f"Save {_fmt_inr(savings_amount)} on {name}")


def _tpl_digest(date_str: str, alerts: list) -> str:
    new_drops = [a for a in alerts if a.get('type') == 'new_release']
    price_drops = [a for a in alerts if a.get('type') == 'price_drop']
    restocks = [a for a in alerts if a.get('type') == 'restock']
    cross_saves = [a for a in alerts if a.get('type') == 'cross_store_save']

    def card(d, price_label: str, url: Optional[str] = None, sub: str = ''):
        img = f'<img src="{d.get("image_url") or d.get("imageUrl","")}" alt="{d.get("name","")}">' if d.get('image_url') or d.get('imageUrl') else ''
        link = url or d.get('product_url') or d.get('productUrl') or f'{APP_URL}/products/{d.get("productId","")}'
        return f"""<div class="prod" style="margin-bottom:14px">{img}
  <div class="info">
    <p class="pbrand">{d.get('brand','')} {sub}</p>
    <p class="pname">{d.get('name','Product')}</p>
    <p class="price-big" style="font-size:20px">{price_label}</p>
    <a href="{link}" class="btn" style="padding:10px 22px;font-size:12px">View →</a>
  </div></div>"""

    sections = []
    if new_drops:
        cards = ''.join(card(a.get('data', {}), _fmt_inr(a.get('data', {}).get('price', 0))) for a in new_drops[:5])
        sections.append(f'<h1 style="font-size:20px;margin-top:32px">🆕 {len(new_drops)} New Arrivals</h1>{cards}')
    if price_drops:
        cards = ''.join(card(a.get('data', {}),
                              f"{_fmt_inr(a.get('data', {}).get('new_price', 0))} <span class=\"price-old\">{_fmt_inr(a.get('data', {}).get('old_price', 0))}</span>")
                          for a in price_drops[:5])
        sections.append(f'<h1 style="font-size:20px;margin-top:32px">💰 {len(price_drops)} Price Drops</h1>{cards}')
    if restocks:
        cards = ''.join(card(a.get('data', {}), _fmt_inr(a.get('data', {}).get('price', 0)), sub='· Back in Stock') for a in restocks[:5])
        sections.append(f'<h1 style="font-size:20px;margin-top:32px">📦 {len(restocks)} Back in Stock</h1>{cards}')
    if cross_saves:
        cards = ''.join(card(a.get('data', {}),
                              f"{_fmt_inr(a.get('data', {}).get('cheapestPrice', 0))} <span class=\"save\">Save {a.get('data', {}).get('savingsPct', 0)}%</span>",
                              url=a.get('data', {}).get('cheapestProductUrl'),
                              sub=f"· Cheaper at {(a.get('data', {}).get('cheapestStore','') or '').replace('_',' ').title()}")
                          for a in cross_saves[:5])
        sections.append(f'<h1 style="font-size:20px;margin-top:32px">🔀 {len(cross_saves)} Cheaper Elsewhere</h1>{cards}')

    body_html = ''.join(sections) or '<p>No new alerts today — we\'ll keep watching the drops.</p>'
    inner = f"""
<div class="hero">
  <p class="kicker">Your Daily Digest · {date_str}</p>
  <h1>Here's what moved in India's streetwear scene today.</h1>
  <p>Handpicked new arrivals, price drops, and cross-store savings that match your preferences.</p>
  {body_html}
  <div class="divider"></div>
  <a href="{APP_URL}/browse" class="btn">Browse All Drops →</a>
</div>"""
    return _shell(inner, f"{len(alerts)} drops curated for you today")


# ============ SEND CORE ============
def _send_email(to_email: str, subject: str, html: str, tags: Optional[list] = None) -> tuple:
    """Send one transactional email. Returns (success, message_id_or_error)."""
    if not to_email:
        return False, 'no-recipient'

    # Personalise unsubscribe link
    html = html.replace('{EMAIL}', to_email)

    if not IS_CONFIGURED:
        logger.info(f"[BrevoSandbox] Would email {to_email} | subject='{subject}' | tags={tags}")
        return True, 'sandbox'

    try:
        api = _client()
        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{'email': to_email}],
            sender={'name': BREVO_SENDER_NAME, 'email': BREVO_SENDER_EMAIL},
            reply_to={'email': BREVO_REPLY_TO, 'name': BREVO_SENDER_NAME},
            subject=subject,
            html_content=html,
            tags=tags or [],
        )
        resp = api.send_transac_email(email)
        msg_id = getattr(resp, 'message_id', None)
        logger.info(f"[Brevo] Sent to {to_email} | subject='{subject[:40]}' | id={msg_id}")
        return True, msg_id
    except ApiException as e:
        logger.error(f"[Brevo] API error to {to_email}: {e.status} {e.reason} — {e.body}")
        return False, f"api_error: {e.status}"
    except Exception as e:
        logger.error(f"[Brevo] Unexpected error to {to_email}: {e}")
        return False, f"err: {e}"


# ============ PUBLIC API (mirrors whatsapp module) ============
def send_price_drop_alert(email: str, product_name: str, new_price, old_price,
                          brand: str = '', image_url: str = '', product_url: str = '',
                          savings_pct: Optional[int] = None) -> tuple:
    html = _tpl_price_drop(product_name, brand, new_price, old_price, image_url, product_url, savings_pct)
    subject = f"Price drop: {product_name[:50]} — now {_fmt_inr(new_price)}"
    return _send_email(email, subject, html, tags=['price_drop', brand])


def send_new_drop_alert(email: str, product_name: str, price, brand: str = '',
                        image_url: str = '', product_url: str = '', is_restock: bool = False) -> tuple:
    tag = 'Back in Stock' if is_restock else 'New Drop'
    html = _tpl_new_drop(product_name, brand, price, image_url, product_url, tag=tag)
    prefix = 'Restocked' if is_restock else 'New'
    subject = f"{prefix}: {product_name[:55]}"
    return _send_email(email, subject, html, tags=[tag.lower().replace(' ', '_'), brand])


def send_cross_store_save_alert(email: str, product_name: str, brand: str,
                                cheapest_price, source_price, cheapest_store: str,
                                cheapest_url: str, image_url: str,
                                savings_amount, savings_pct) -> tuple:
    html = _tpl_cross_store(product_name, brand, cheapest_price, source_price,
                            cheapest_store, cheapest_url, image_url,
                            savings_amount, savings_pct)
    store_label = cheapest_store.replace('_', ' ').title()
    subject = f"Save {_fmt_inr(savings_amount)} on {product_name[:40]} at {store_label}"
    return _send_email(email, subject, html, tags=['cross_store_save', brand])


def send_daily_digest_email(email: str, date_str: str, alerts: list) -> tuple:
    html = _tpl_digest(date_str, alerts)
    subject = f"Your Drops Digest · {len(alerts)} drops curated for you"
    return _send_email(email, subject, html, tags=['daily_digest'])


def send_test_email(email: str) -> tuple:
    """Admin-only: send a self-test to verify sender/DKIM/inbox placement."""
    html = _tpl_new_drop(
        name='Test Alert — If you see this, setup is working',
        brand='Drops Curated',
        price=2999,
        image_url='https://drops-curated.preview.emergentagent.com/logo192.png',
        product_url=APP_URL,
        tag='Integration Test',
    )
    return _send_email(email, 'Drops Curated · Email delivery test', html, tags=['test'])
