# Drops Curated — Product Requirements Document

## Original Problem Statement
Premium VIP subscription platform (₹399/month) for the Indian luxury streetwear market. Core value: real-time WhatsApp alerts for new drops and price reductions within 10 seconds.

## Brand Narrative
"Curated Excellence. Delivered Instantly." — India's most refined streetwear intelligence platform.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python + APScheduler + MongoDB
- **AI**: Gemini 2.5 Flash (Scraper Self-Healing via Emergent LLM Key)
- **Scraping**: Playwright + BeautifulSoup + AETHER SWARM v1.0
- **Monitoring**: AETHER MASTER v1.0 (autonomous 5-min health cycles)
- **Monetization**: 7-Day Free Trial → Razorpay Subscriptions ₹399/mo

## What's Been Implemented

### 7-Day Free Trial System (COMPLETE — Apr 2026)
- localStorage-based 7-day trial with `TrialProvider` context
- Expired: Prices blurred, wishlist locked (lock icons), filter panel locked with overlay
- Active: Full access with "X days remaining" banner
- UpgradeModal with ₹399/month CTA on any locked element click
- `BrowserRouter > TrialProvider > WishlistProvider` order (critical for Link)

### Landing Page (COMPLETE)
- Hero: "Curated Excellence. Delivered Instantly."
- Benefits for Buyers (4 cards), Benefits for Brands (4 cards)
- "A Win-Win Ecosystem" platform story, "How It Works" 3-step
- Footer disclaimer, brand marquee, live stats

### Browse Page (COMPLETE)
- Sort: Newest First, Price Low→High, Price High→Low, Name A-Z
- Empty state with Frown icon + Clear Filters + "Wrong category?" mailto
- Curated sections: Limited Edition, Trending, New Drops, Celebrity Style
- Filters: Brand, Category, Item Type, Gender (AI), Size First
- Trial-aware: locked filters + blurred prices when expired

### Subscribe Page (COMPLETE)
- Indian phone validation: 10 digits, starts with 6-9, no repeated digits
- OTP via WhatsApp, Razorpay payment, Turnstile CAPTCHA
- Size preference funnel

### JSON-LD Structured Data (COMPLETE)
- Homepage: @graph (Organization + WebSite + FAQPage + Service)
- Product pages: Product schema with LimitedAvailability
- Browse: ItemList schemas + BreadcrumbList
- No duplicate schemas

### Scraping System (COMPLETE)
- 24 brands, AETHER SWARM v1.0, Gemini self-healing
- Auto-scrape every 15 minutes

### AETHER MASTER v1.0 (COMPLETE)
- 5-min health monitoring, auto-heals, incident memory

### Admin Panel (COMPLETE)
- Dashboard, CRM, Subscribers, Brands, Aether Master, Scraper Health, Agent Logs, AI Classification

### Cross-Store Price Comparison (COMPLETE — Apr 2026)
- Product pages show the same SKU across all stores (e.g. Almost Gods ₹12,117 vs Superkicks ₹9,500)
- Token-overlap matcher with product-type-bucket guard (footwear / top / outerwear / bottom / dress / headwear / bag / accessory / homeware / collectible)
- Match rule: ≥4 shared distinctive tokens, OR (≥2 shared AND one side fully contained in the other with ≤1 extra word)
- Filters brand/type/fit/color/size/stop words; preserves single-digit model numbers ("Ja 1" ≠ "Ja 3")

### Cross-Store Savings Scanner (COMPLETE — Apr 2026)
- Nightly cron at 03:00 UTC (08:30 IST) scans all active products for cheaper cross-store listings
- Thresholds: ≥₹500 AND ≥10% savings
- Stores live feed in `cross_store_savings` collection (always-fresh, stale entries removed each run)
- Newly-discovered savings auto-queued into `daily_digest` with new alert type `cross_store_save`
- Daily digest sender includes "🔀 Cheaper Elsewhere" section
- APIs: `GET /api/savings/active` (public feed, filters: brand/category/min_savings_pct), `POST /api/admin/savings/run-scan`, `GET /api/admin/savings/status`

### VIP Subscription Tier (COMPLETE — Apr 2026)
- **Plans**: Regular ₹399/mo (5 brands cap) · VIP ₹2,999/mo · VIP ₹16,195/6mo (−10%) · VIP ₹28,790/yr (−20%)
- **VIP benefits**: alerts for ALL 24+ brands (unlimited), cross-store savings feed, 15-min early-access, exclusive raffle entries, priority concierge, premium wallet card
- Central `PLAN_CATALOG` in `server.py` — single source of truth (tier, amount_paise, duration_days, brand_limit, benefits)
- New APIs: `GET /api/plans`, `GET /api/subscribers/{phone}/status`
- `create_payment_order` + `verify_payment` now derive amount/expiry from plan catalog; expiry stacks onto existing subscription (upgrade-friendly)
- Subscriber doc carries `tier` (`regular`/`vip`) + `brandLimit` (5 or 0=unlimited)
- **Landing page**: new Pricing section with side-by-side Regular + VIP cards, "Most Popular" VIP badge, 6-mo/yearly savings tiles
- **Subscribe page**: plan-selector with 4 radio cards, reads `?plan=` URL param, dynamic "Pay ₹X via UPI" button, upgrade-to-VIP banner for existing Regular subscribers (stacks remaining days)
- **Bug fix by testing agent**: `security.py` Motor `if db:` truth-test → `is not None` (was causing 500s on rate-limit paths)

### Brevo Email Alerts (COMPLETE SCAFFOLD — Apr 2026 · awaiting API key + DNS)
- New module `/app/backend/email_alerts.py` — sends rich HTML alerts via Brevo transactional API
- 5 template types mirroring the WhatsApp surface: `price_drop`, `new_drop`/`restock`, `cross_store_save`, `daily_digest`, `test`
- Premium luxury design language: navy + ivory + gold palette, serif headings, embedded product image, styled CTA button
- **Channel routing**: subscriber doc carries `notificationChannel` (`email` default | `whatsapp` | `both`). Both the instant-alert pipeline (`alerts.py`) and daily digest sender (`server.py`) honour it.
- Preference funnel UpdatePreferences model now accepts `notification_channel` + `telegram_username`.
- Auto-activates when `BREVO_API_KEY` set in `/app/backend/.env` — sandbox/log-only mode otherwise.
- New APIs: `GET /api/admin/email/status`, `POST /api/admin/email/test` (send demo of any template kind)
- Sender: `alerts@dropscurated.com`, reply-to `Dropscurated@gmail.com`
- Blocked on user: create Brevo account → paste API key into `.env` → add SPF/DKIM records to `dropscurated.com` DNS

## Prioritized Backlog

### P0 (In Progress)
- [ ] Notification Preferences UI on SubscribePage.js (Email default, WhatsApp warning modal, Telegram)

### P1
- [ ] Apple/Google Wallet digital membership cards
- [ ] Production keys migration (Razorpay, Meta WhatsApp)
- [ ] Savings Feed UI page (surface `/api/savings/active` to VIP members as a dedicated "Best Savings" tab)

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard
- [ ] Refactor server.py into routes/ directory (3500+ lines)

## Key DB Collections
products, subscribers, brands, prices, price_history, cross_store_savings, aether_learning, aether_master_memory, scraper_agent_logs, scraper_strategies, product_fingerprints, alert_log, broadcast_log, daily_digest, security_logs

## Date Log
- Feb 2026: AETHER SWARM v1.0, AETHER MASTER v1.0, CRM Dashboard, Admin Panel
- Feb 2026: Landing page premium narrative
- Apr 2026: P0 7-day free trial complete, P1 sort/empty state/phone validation, JSON-LD overhaul
- Apr 2026: Cross-store matcher rewritten (token-overlap + type-bucket + containment). Cross-store savings scanner shipped with nightly cron + `cross_store_save` alert type wired into daily digest.
