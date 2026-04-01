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

## Live Brands (21 total, 11,400+ products)

### Indian Stores
| Brand | Platform | Products | Type |
|-------|----------|----------|------|
| Crep Dog Crew | Shopify | 1660 | Resale/Hype |
| Capsul | Shopify | 1250 | Streetwear |
| Urban Monkey | Shopify | 1241 | Caps/Streetwear |
| Huemn | Shopify | 985 | Streetwear |
| Mainstreet Marketplace | Shopify | 750 | Hype/Resale |
| Superkicks | Shopify | 741 | Premium Sneakers |
| Kickass Kicks | Shopify | 750 | Sneakers |
| Hype Elixir | Shopify | 750 | Premium/Luxury |
| Bluorng | Shopify | 551 | Streetwear |
| House of Koala | Shopify | 306 | Streetwear |
| Farak | Shopify | 270 | Streetwear |
| Almost Gods | Shopify | 190 | Streetwear |
| Jaywalking | Shopify | 190 | Streetwear |
| Veg Non Veg | HTML parse | 156 | Sneakers |
| Hiyest | WooCommerce | 126 | Streetwear |
| Culture Circle | Playwright | 114 | Hype/Auth |
| Code Brown | Shopify | 53 | Streetwear |
| Noughtone | Shopify | 26 | Streetwear |

### International Stores
| Brand | Platform | Products | Region |
|-------|----------|----------|--------|
| Limited Edt | Shopify | 750 | Singapore |
| Stadium Goods | Shopify | 581 | USA (NYC) |
| Sneakersnstuff | Shopify | — | Sweden (blocked) |

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
- [x] VIP luxury UI, fully responsive
- [x] 14 brand scrapers (7,097+ real products)
- [x] Auto-scraping every 15 minutes
- [x] Price drop detection + new product detection
- [x] WhatsApp alert engine (SANDBOX - Twilio)
- [x] User preferences (brand + alert type + **category + size** selection)
- [x] **Size Guide modal** with garments/sneakers sizing tables
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment (SANDBOX)
- [x] Digital membership card (UI)
- [x] **Apple/Google Wallet API endpoints** (requires certificates to activate)
- [x] Brand partnership page
- [x] All tests: 100% pass (6 iterations)

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
