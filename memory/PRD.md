# Drops Curated - Product Requirements Document

## Overview
Premium VIP subscription platform (₹399/month) for Indian luxury streetwear market. Core value: Real-time WhatsApp alerts for new drops and price reductions within 10 seconds.

## Tech Stack
- **Frontend**: React, Tailwind CSS, Recharts
- **Backend**: FastAPI, Python, APScheduler, slowapi
- **Database**: MongoDB (indiashop_db)
- **AI**: Gemini 2.5 Flash (Data Classification + Scraper Auto-healing)
- **Integrations**: Twilio (WhatsApp), Razorpay (Payments), Cloudflare Turnstile (CAPTCHA)

## Current Status
- **Products**: 11,411 tracked
- **Brands**: 23 premium streetwear brands
- **Mode**: Sandbox/Test (Twilio & Razorpay)

---

## Completed Features

### April 10, 2026
- [x] **Shipping Data Removal**: Cleaned 1,093 products, updated all scrapers with filtering methods
- [x] **Wishlist Portfolio Calculation Bug Fix**: Fixed `addedPrice` override bug in `WishlistPage.js` line 542
- [x] **Added Mids and Lows scraper**: Shopify-based, 201 products scraped
- [ ] **Footlocker India scraper**: Created but blocked by Akamai anti-bot (needs residential proxies)

### Previous Session
- [x] LLM-powered Self-Healing Scraper Agent (Gemini 2.5 Flash)
- [x] Scraper Health Dashboard & Agent Logs UI
- [x] Multi-layer Security Architecture (Turnstile, Rate Limiting, Sanitization)
- [x] Cloudflare DNS activation for dropscurated.com
- [x] Recharts Wishlist Portfolio dashboard
- [x] Size selection enforcement on ProductPage
- [x] Fixed low-contrast text on WishlistPage

### Earlier Sessions
- [x] Complete project pivot to "Drops Curated"
- [x] Luxury Warm Minimalist UI design
- [x] WhatsApp OTP auth via Twilio (Sandbox)
- [x] Razorpay subscription payment flow (Sandbox)
- [x] 23 custom brand scrapers (Shopify, WooCommerce, Playwright)
- [x] 15-minute background auto-scraping via APScheduler
- [x] WhatsApp alert dispatch logic for price drops

---

## Pending Issues

### P0 - Critical
- [ ] **Wishlist Portfolio Calculation Bug** - User reported wrong Total/Difference/Percentage values

### P1 - High Priority
- [ ] Scraper extracting invalid size data (some brands)
- [ ] Cloudflare 405 error on dropscurated.com (needs origin server routing)

### P2 - Medium Priority
- [ ] SubscribePage Indian phone validation + success UI
- [ ] BrowsePage UI overhaul (sort options, empty state, feedback button)
- [ ] server.py refactoring (>3,100 lines - extract to routes/)

---

## Backlog / Future Features

### P1
- [ ] Apple/Google Wallet .pkpass integration
- [ ] Production keys migration (Twilio, Razorpay)

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard

---

## Architecture

```
/app/
├── backend/
│   ├── scrapers/          # 23 brand scrapers with shipping filters
│   ├── server.py          # FastAPI (needs refactoring)
│   ├── security.py        # Rate limiting, sanitization
│   ├── security_advanced.py # Turnstile, pagination detection
│   ├── scraper_agent.py   # LLM Self-Healing
│   └── scheduler.py       # APScheduler
├── frontend/
│   └── src/
│       ├── components/    # TurnstileCaptcha, etc.
│       ├── context/       # WishlistContext
│       └── pages/         # Landing, Browse, Product, Subscribe, Wishlist, Admin
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `POST /api/auth/otp/send` - WhatsApp OTP (requires Turnstile)
- `POST /api/auth/otp/verify` - Verify OTP
- `POST /api/subscribe/order` - Create Razorpay order
- `POST /api/subscribe/verify` - Verify payment
- `GET /api/admin/agent-logs` - Scraper AI healing logs
- `GET /api/admin/security-stats` - Security metrics

## Test Credentials
- Phone: Any 10-digit Indian number (6-9 prefix)
- OTP: Check backend console logs
- Admin: See /app/memory/test_credentials.md
