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
- WhatsApp: Meta WhatsApp Cloud API (SANDBOX - pending template approval)
- Scraping: Generic Shopify scraper + WooCommerce + httpx/BeautifulSoup + Playwright
- Scheduler: APScheduler (every 15 minutes + daily digest at 8 PM IST)

## Live Brands (23 total, 11,000+ products)
| Brand | Platform | Volume |
|-------|----------|--------|
| Crep Dog Crew | Shopify | High |
| Capsul | Shopify | High |
| Urban Monkey | Shopify | High |
| Huemn | Shopify | High |
| Superkicks | Shopify | High |
| Mainstreet Marketplace | Shopify | High |
| Bluorng | Shopify | Medium |
| House of Koala | Shopify | Medium |
| Farak | Shopify | Medium |
| Evemen | Shopify | Medium |
| Void Worldwide | Shopify | Medium |
| Almost Gods | Shopify | Low (Exclusive) |
| Jaywalking | Shopify | Low (Exclusive) |
| Code Brown | Shopify | Low (Exclusive) |
| Noughtone | Shopify | Low (Exclusive) |
| Hiyest | WooCommerce | Low (Exclusive) |
| Veg Non Veg | HTML parse | Low (Exclusive) |
| Culture Circle | Playwright | Low (Exclusive) |
| Toffle | Shopify | Low (Exclusive) |
| Leave The Rest | Shopify | Low (Exclusive) |
| Deadbear | Shopify | Low (Exclusive) |
| Natty Garb | Shopify | Low (Exclusive) |
| Bomaachi | Shopify | Low (Exclusive) |

## Core System Architecture
1. **Auto-Scraper** (every 15 min): Scrapes all 23 brands, detects price changes + new products + restocks
2. **Alert Engine**: Compares prices, sends targeted WhatsApp alerts based on user preferences
3. **Daily Digest** (8 PM IST): Summarizes all drops for users who prefer batched notifications
4. **Preference Funnel System**: Users can customize alerts with:

### Preference Funnel (NEW - April 2026)
**Section A - Brand Selection ("Follow" List)**
   - Top 5 / Top 10 / Unlimited brand limits
   - Volume indicators (High Vol, Medium, Exclusive)
   - Pro tip about low-volume brands for fewer alerts

**Section B - Trigger-Based Filtering**
   - New Drops Only: When a brand launches new collection
   - Price Drops Only: When product price decreases (with configurable threshold 5-30%)
   - Restock Alerts: When "Sold Out" items come back in stock

**Section C - Specificity (Best Cost Saver)**
   - Category Filter: Garments / Sneakers / Accessories
   - "My Size" Filter: Only alert if product drops in user's size (XS-XXL, UK6-UK12, Free Size)

**Section D - Notification Frequency**
   - Instant: Real-time alerts within 10 seconds
   - Daily Digest (RECOMMENDED): Single message at 8 PM summarizing all drops

**Optional Filters**
   - Budget Range: Min/Max price filter
   - Keywords: Match specific product terms (Jordan, Yeezy, Dunk, etc.)

## Pages
1. **Landing** (`/`) — Hero, 3 pillars, stats, partners, CTA
2. **Browse** (`/browse`) — Grid with search/brand/category filters, infinite scroll
3. **Product** (`/product/:id`) — Price comparison, buy links
4. **Subscribe** (`/subscribe`) — 5-step: OTP → Details → Payment → Preference Funnel → Card
5. **Partners** (`/partners`) — Brand partnership + contact form
6. **Brands** (`/brands`) — All tracked brands with links to filtered views

## What's Implemented (April 2026)
- [x] VIP luxury UI with funky Gen Z design elements
- [x] 23 brand scrapers (11,000+ real products)
- [x] **Auto-scraping every 15 minutes** (APScheduler)
- [x] Price drop detection + new product detection + restock detection
- [x] WhatsApp alert engine via Meta Cloud API (SANDBOX)
- [x] **Comprehensive Preference Funnel** (4 sections: A, B, C, D)
- [x] Brand limit enforcement (Top 5/10/Unlimited)
- [x] Trigger-based filtering (New Drops, Price Drops, Restock)
- [x] Category and Size specificity filters
- [x] Notification frequency (Instant vs Daily Digest at 8 PM)
- [x] Budget range and keyword filters
- [x] **"Test My Preferences" Simulation** (NEW)
  - Shows matching products count
  - Estimated daily alerts with breakdown
  - Sample daily digest preview
  - Contextual optimization tips
- [x] Size Guide modal with garments/sneakers sizing tables
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment (SANDBOX)
- [x] Digital membership card (UI)
- [x] Apple/Google Wallet API endpoints (requires certificates to activate)
- [x] Brand partnership page
- [x] Real-Time Raffle & Entry Management with EQL-like bot-blocking
- [x] Infinite scroll Browse page
- [x] Celebrity Style section (Travis Scott, Kanye West, Ranveer Singh, etc.)
- [x] Dynamic "Brands Listed" footer with auto-scroll marquee
- [x] Dedicated `/brands` page
- [x] Excel generator for brand analytics
- [x] All tests: 100% pass (10 iterations)

## Upcoming Tasks
- [ ] **P0**: Meta WhatsApp template approval (real message delivery)
- [ ] **P0**: Razorpay production keys (live UPI)
- [ ] **P0**: Apple/Google Wallet certificates setup
- [ ] **P1**: WhatsApp bot for preference management
- [ ] **P1**: Price history charts on product pages
- [ ] **P1**: Drop Calendar UI (upcoming releases)
- [ ] **P2**: Visual search (image upload)
- [ ] **P2**: Brand partner self-serve dashboard
- [ ] **P3**: Instagram drop tracking

## API Endpoints

### Authentication
- `POST /api/otp/send` - Send WhatsApp OTP
- `POST /api/otp/verify` - Verify OTP

### Payments
- `POST /api/payment/create-order` - Create Razorpay order
- `POST /api/payment/verify` - Verify payment

### Preferences (Preference Funnel)
- `POST /api/preferences` - Save/update user preferences
  - `phone`: string
  - `brands`: string[] (empty = all brands)
  - `brand_limit`: 5 | 10 | 0 (unlimited)
  - `alert_types`: ("price_drop" | "new_release" | "restock")[]
  - `categories`: ("garments" | "sneakers" | "accessories")[]
  - `sizes`: string[]
  - `price_range`: {min?: number, max?: number}
  - `keywords`: string[]
  - `drop_threshold`: number (5-30%)
  - `alert_frequency`: "instant" | "daily"
- `GET /api/preferences/{phone}` - Get user preferences
- `POST /api/preferences/simulate` - **Test My Preferences** simulation
  - Returns: total_matching_products, estimated_daily_alerts, sample_daily_digest, filters_applied, new_drops/price_drops/restocks sections with sample products

### Alerts
- `GET /api/alerts/recent` - Get recent alert logs
- `GET /api/alerts/digest/{phone}` - Get pending daily digest
- `POST /api/alerts/send-digests` - Trigger daily digest send (called by scheduler)

### Scheduler
- `GET /api/scheduler/status` - Get scheduler status (auto_scrape + daily_digest jobs)
- `POST /api/scheduler/trigger` - Manually trigger scrape cycle

### Products & Brands
- `GET /api/search` - Search products
- `GET /api/products/{id}` - Get product details
- `GET /api/brands` - Get all brands
- `GET /api/brands/report` - Generate Excel analytics

## Wallet Integration Requirements (for activation)

### Apple Wallet
Environment variables needed:
```
APPLE_PASS_TYPE_ID=pass.com.yourorg.dropscurated
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_CERT_PATH=/path/to/certificate.pem
APPLE_KEY_PATH=/path/to/private.key
APPLE_WWDR_PATH=/path/to/wwdr.pem
```

### Google Wallet
Environment variables needed:
```
GOOGLE_WALLET_ISSUER_ID=YOUR_ISSUER_ID
GOOGLE_WALLET_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
```
