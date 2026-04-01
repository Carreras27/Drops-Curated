# Drops Curated - Product Requirements Document

## Overview
**Drops Curated** is a premium paid discovery platform for Indian luxury streetwear. ₹399/month for WhatsApp alerts on price drops and new collections, delivered in under 10 seconds.

## Business Model
- ₹399/month subscription via UPI (Razorpay)
- WhatsApp OTP registration (prevents spam)
- Digital membership card (Apple/Google Wallet)
- Brand partnerships: showcase collections + bulk memberships for VIP customers
- 0% commission on purchases

## Tech Stack
- Frontend: React, Tailwind CSS, Lucide React
- Backend: Python FastAPI, MongoDB
- Payments: Razorpay (SANDBOX)
- WhatsApp: Twilio (SANDBOX)
- Scraping: Generic Shopify scraper + WooCommerce + httpx/BeautifulSoup + Playwright
- Scheduler: APScheduler (every 15 minutes)

## Live Brands (17 total, 9,300+ products)
| Brand | Platform | Products |
|-------|----------|----------|
| Crep Dog Crew | Shopify | 1660 |
| Capsul | Shopify | 1250 |
| Urban Monkey | Shopify | 1241 |
| Huemn | Shopify | 985 |
| Mainstreet Marketplace | Shopify | 750 |
| Limited Edt | Shopify | 750 |
| Superkicks | Shopify | 741 |
| Bluorng | Shopify | 551 |
| House of Koala | Shopify | 306 |
| Farak | Shopify | 270 |
| Almost Gods | Shopify | 190 |
| Jaywalking | Shopify | 190 |
| Veg Non Veg | HTML parse | 156 |
| Hiyest | WooCommerce | 126 |
| Culture Circle | Playwright | 114 |
| Code Brown | Shopify | 53 |
| Noughtone | Shopify | 26 |

## Core System Architecture
1. **Auto-Scraper** (every 15 min): Scrapes all 14 brands, detects price changes + new products
2. **Alert Engine**: Compares prices, sends targeted WhatsApp alerts based on user preferences
3. **Preference System**: Users choose:
   - **Brands**: Select specific brands or all 14
   - **Alert Types**: Price drops / new releases / both
   - **Categories**: Garments / Sneakers / Accessories (or all)
   - **Sizes**: XS, S, M, L, XL, XXL, UK6-UK12, Free Size (or all)

## Pages
1. **Landing** (`/`) — Hero, 3 pillars, stats, partners, CTA
2. **Browse** (`/browse`) — Grid with search/brand/category filters
3. **Product** (`/product/:id`) — Price comparison, buy links
4. **Subscribe** (`/subscribe`) — 5-step: OTP → Details → Payment → Preferences → Card
5. **Partners** (`/partners`) — Brand partnership + contact form

## What's Implemented (December 2025)
- [x] VIP luxury UI with funky Gen Z design elements
- [x] 17 brand scrapers (9,355+ real products)
- [x] **Auto-scraping every 15 minutes** (APScheduler)
- [x] Price drop detection + new product detection
- [x] WhatsApp alert engine (SANDBOX - Twilio)
- [x] User preferences (brand + alert type + category + size selection)
- [x] Size Guide modal with garments/sneakers sizing tables
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment (SANDBOX)
- [x] Digital membership card (UI)
- [x] Apple/Google Wallet API endpoints (requires certificates to activate)
- [x] Brand partnership page
- [x] All tests: 100% pass (7 iterations)

## Upcoming Tasks
- [ ] **P0**: Twilio production keys (real WhatsApp delivery)
- [ ] **P0**: Razorpay production keys (live UPI)
- [ ] **P0**: Apple/Google Wallet certificates setup
- [ ] **P1**: WhatsApp bot for preference management
- [ ] **P1**: Price history charts on product pages
- [ ] **P1**: Drop Calendar UI (upcoming releases)
- [ ] **P2**: Visual search (image upload)
- [ ] **P2**: Brand partner self-serve dashboard
- [ ] **P3**: Instagram drop tracking

## Wallet Integration Requirements (for activation)

### Apple Wallet
1. Apple Developer Account ($99/year)
2. Pass Type ID certificate from iOS Provisioning Portal
3. Export Certificates.p12 from Keychain
4. Generate certificate.pem and private.key
5. Download WWDR (Apple Worldwide Developer Relations) certificate

Environment variables needed:
```
APPLE_PASS_TYPE_ID=pass.com.yourorg.dropscurated
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_CERT_PATH=/path/to/certificate.pem
APPLE_KEY_PATH=/path/to/private.key
APPLE_WWDR_PATH=/path/to/wwdr.pem
```

### Google Wallet
1. Google Cloud Account
2. Enable Google Wallet API
3. Create Service Account with Wallet permissions
4. Download service account JSON key

Environment variables needed:
```
GOOGLE_WALLET_ISSUER_ID=YOUR_ISSUER_ID
GOOGLE_WALLET_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
```
