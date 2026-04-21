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

### Freshness Guard + Auto-Heal (CRITICAL FIX — Apr 2026)
- **Bug**: Users received wrong price alerts (e.g. EVEMEN soul t-shirt citing ₹3,486 → ₹2,520 when real site had dropped to ₹1,800). Root cause: ALL 25 brands had stale scrape data (oldest = Culture Circle, 1,469h / 61 days). Scheduler's `'interval'` trigger delayed first run by 90 min, and since backend restarts were more frequent than that, the scrape never fired in this pod instance.
- **Fix 1 (system rule)**: New `/app/backend/freshness.py` module. `MAX_ALERT_AGE_HOURS=10` (env-tunable). `alerts.py`, `cross_store_savings.py`, and `send_daily_digests` all gate alerts: if price data is older than the cap → silently drop + log to `stale_alerts_log` collection.
- **Fix 2 (scheduler)**: `scheduler.py` now passes `next_run_time=now+2min` to `add_job` so the first auto-scrape kicks off 2 min after startup instead of 90 min. Ensures a backend restart never leaves data stale for a full cycle.
- **Fix 3 (admin UI)**: New **Freshness** admin tab — shows fresh/stale brands, ages, recent stale-skip events, per-brand **"Rescrape now"** button backed by `POST /api/admin/freshness/rescrape/{brand_key}`.
- **Verified**: Manual rescrape of EVEMEN refreshed 83 products. Scheduler now running on schedule (confirmed `last_run=2026-04-21 09:56 UTC`).

### Turnstile Sandbox Bypass (LIVE — Apr 2026)
- **Backend** (`security_advanced.py`): `verify_turnstile_token` accepts a hardcoded well-known token (`SANDBOX_BYPASS_E2E_DO_NOT_USE_IN_PROD`) when `TURNSTILE_SANDBOX_BYPASS=1` is set in env. Real Cloudflare verification and 403 rejection of other fake tokens still work.
- **Frontend** (`SubscribePage.js`): `?test_bypass=1` URL param hides the Turnstile widget, pre-sets the sandbox token so the "Send OTP" button is enabled, and renders a prominent amber "TURNSTILE SANDBOX BYPASS ACTIVE — DEV/TEST ONLY" strip.
- Unlocks full-funnel Playwright testing (verify → details → payment → preferences → success) that was previously blocked by Cloudflare managed-challenge iframes.
- **Verified** via curl: OTP send + verify + beta signup all 200 with bypass; fake token still rejected.

### Notification Preferences UI on SubscribePage (COMPLETE — Apr 2026)
- Section A "How should we reach you?" with three rows:
  - **Email** — locked ON with "Default · Always on" pill (can't be unchecked)
  - **WhatsApp** — optional add-on. Enabling opens a **WhatsApp warning modal** (React Portal to `document.body` for mobile-Safari safety) explaining chat interruption + Meta per-message cost. Cancel keeps email-only; Confirm adds WhatsApp. Disable is instant.
  - **Telegram** — optional add-on. Enables straight through; post-checkout deep-link connection happens on `/account`.
- Live "Selected: Email · WhatsApp · Telegram" summary line reflects the active combination.
- Derived `notification_channel` string sent to `POST /api/preferences`: `email` | `both` (email+whatsapp back-compat) | `email,telegram` | `email,whatsapp,telegram`.
- Channels Set seeded from `?channels=email,whatsapp` URL param (set by Landing-page Flash-Alerts CTA).
- **Verified** by testing_agent_v3_fork (iteration_15.json) via code review on all 7 logic points (E2E blocked by Cloudflare Turnstile — expected for automation).

### Closed Beta Program (LIVE — Apr 2026)
- **Cap**: First 100 signups get 30 days free, zero payment, all brands unlocked (VIP-level access). Cap + resume-for-existing + paid-block logic all enforced in `/api/beta/signup`.
- Backend: `/api/beta/status`, `/api/beta/signup`, `/api/beta/feedback`, admin endpoints `/api/admin/beta/feedback` + `/api/admin/beta/testers` (cohort + channel mix).
- Frontend: `/beta` signup wizard (intro → phone → WhatsApp OTP → details → success) and `/beta/feedback` (bug/idea/love/other + optional 1–5 rating). Both routes registered in `App.js`.
- Landing page `BetaSpotsBanner` — thin fixed strip at top showing "X of 100 spots left — 30 days free, no card", urgency colour shifts at ≤30 and ≤10 remaining, dismissible for session. Header accepts `offsetTop` prop so it sits below the banner cleanly.
- Welcome email sent via Brevo on signup, admin pinged on every feedback submission.
- **Test pass by testing agent** (iteration_14.json) — 8/8 executable backend tests, full frontend happy-path + banner + dismiss + feedback.

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

### Brevo Email Alerts (LIVE — Apr 2026)
- New module `/app/backend/email_alerts.py` — sends rich HTML alerts via Brevo transactional API
- 5 template types mirroring the WhatsApp surface: `price_drop`, `new_drop`/`restock`, `cross_store_save`, `daily_digest`, `test`
- Premium luxury design language: navy + ivory + gold palette, serif headings, embedded product image, styled CTA button, dark-mode-safe
- **Channel routing**: subscriber doc carries `notificationChannel` (`email` default | `whatsapp` | `telegram` | combos). Both instant-alert pipeline and daily digest sender honour it.
- **BREVO_API_KEY** provisioned + **dropscurated.com DKIM/SPF/DMARC** fully authenticated via Cloudflare (`authenticated=true, verified=true`)
- Preference funnel `UpdatePreferences` model accepts `notification_channel` + `telegram_username`.
- New APIs: `GET /api/admin/email/status`, `POST /api/admin/email/test` (pulls real product+image from DB for template previews)
- Sender: `alerts@dropscurated.com`, reply-to `Dropscurated@gmail.com`

### Telegram Bot Alerts (LIVE — Apr 2026)
- New module `/app/backend/telegram_alerts.py` — rich HTML-formatted alerts using Telegram Bot API
- Bot: **@Dropscurated_alerts_bot** (public)
- 4 template types: `price_drop`, `new_drop`/`restock`, `cross_store_save`, `daily_digest` — image + inline buttons for "View Product"
- **Deep-link account connection**: member clicks "Connect Telegram" on `/account` → backend mints a one-time code (10-min TTL) → `t.me/Dropscurated_alerts_bot?start=<code>` opens the bot → webhook consumes code → subscriber's `telegramChatId` persisted atomically
- New APIs: `POST /api/telegram/link-code`, `POST /api/telegram/webhook`, `GET /api/admin/telegram/status`, `POST /api/admin/telegram/set-webhook`
- Webhook handles `/start <code>`, `/stop`, `/help` commands
- Alert pipeline (`alerts.py`) + daily digest sender (`server.py`) fan-out via `notificationChannel` (e.g. `email,whatsapp,telegram`)

### Member Account Page `/account` (LIVE — Apr 2026)
- New `/app/frontend/src/pages/AccountPage.js` — OTP-based login (no JWT, same trust as Subscribe flow), session-cached via sessionStorage
- 4 sections:
  - **Membership summary** — tier (VIP/Regular), plan, expiry, upgrade button, paused-status banner
  - **Notification channels** — Email locked-on with gold check, WhatsApp + Telegram as toggles. Telegram shows "Connect" CTA when unlinked, "Disconnect" when linked.
  - **Pause alerts** — 3/7/14/30-day vacation mode + Resume now
  - **Preferences summary** — read-only snapshot of filters, link to full edit flow
- Backend APIs: `/account/login`, `/account/{phone}`, `/account/channels` (always force-includes email), `/account/pause`, `/account/telegram-disconnect`
- Email footer's "Manage preferences" link now points here instead of `/subscribe`
- **100% test pass by testing agent** (iteration_13.json) — 15/15 backend, all frontend flows including locked email, toggle persistence, Telegram deep-link, pause/resume

## Prioritized Backlog

### P0
- _(none currently — last P0 shipped: Notification Preferences UI)_

### P1
- [ ] Apple/Google Wallet digital membership cards
- [ ] Production keys migration (Razorpay, Meta WhatsApp, **remove `TURNSTILE_SANDBOX_BYPASS=1` from prod env**)
- [ ] Savings Feed UI page (surface `/api/savings/active` to VIP members as a dedicated "Best Savings" tab)
- [ ] Admin Panel → Beta tab (testers cohort + feedback triage) — backend APIs ready, UI pending

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard
- [ ] Refactor server.py into routes/ directory (4300+ lines — including extracting beta module to /app/backend/routes/beta.py)
- [ ] Consolidate phone validation (validate_phone_number vs inline check in /otp/send)
- [ ] Move BETA_MAX_SPOTS to env var for non-prod overrides

## Key DB Collections
products, subscribers, brands, prices, price_history, cross_store_savings, aether_learning, aether_master_memory, scraper_agent_logs, scraper_strategies, product_fingerprints, alert_log, broadcast_log, daily_digest, security_logs

## Date Log
- Feb 2026: AETHER SWARM v1.0, AETHER MASTER v1.0, CRM Dashboard, Admin Panel
- Feb 2026: Landing page premium narrative
- Apr 2026: P0 7-day free trial complete, P1 sort/empty state/phone validation, JSON-LD overhaul
- Apr 2026: Cross-store matcher rewritten (token-overlap + type-bucket + containment). Cross-store savings scanner shipped with nightly cron + `cross_store_save` alert type wired into daily digest.
