# Drops Curated - Product Requirements Document

## Overview
**Drops Curated** is a premium paid discovery platform for Indian luxury streetwear. Users browse curated drops publicly and pay ₹399/month for WhatsApp alerts on price drops, new collections, and restocks within 10 seconds.

## Design Language: "Warm Minimalist VIP"
- **Background**: #FDFBF7 (Warm White/Eggshell)
- **Primary**: #001F3F (Deep Navy)
- **Accent**: #D4AF37 (Antique Gold)
- **Typography**: Playfair Display (serif headers) + Inter (sans-serif body)
- **Vibe**: Digital boutique, luxury, exclusive

## Tech Stack
- **Frontend**: React, Tailwind CSS, Lucide React
- **Backend**: Python FastAPI
- **Database**: MongoDB
- **Payments**: Razorpay (sandbox mode)
- **Scraping**: httpx + BeautifulSoup (Crepdog, VegNonVeg), Playwright (Culture Circle)

## Business Model
- ₹399/month subscription via UPI (Razorpay)
- WhatsApp OTP registration (prevents spam bans)
- Digital membership card (Apple Wallet + Google Wallet)
- Brand partnerships: showcase collections + bulk membership discounts for VIP customers
- 0% commission on purchases

## 3 Core Pillars
1. **Best Price Comparison** — Real-time prices across stores
2. **Instant Price Drop Alerts** — WhatsApp alerts in <10 seconds
3. **New Collection Drops** — First to know about launches and restocks

## Current Brands (Live Scrapers)
1. **Crep Dog Crew** (Shopify JSON API) — ~750 products
2. **Veg Non Veg** (HTML parsing) — ~100 products
3. **Culture Circle** (Playwright + HTML) — ~114 products
- **Total**: ~998 real products

## Pages
1. **Landing** (`/`) — Hero + 3 pillars + stats + brand partners + CTA
2. **Browse** (`/browse`) — Product grid with search/brand/category filters
3. **Product Detail** (`/product/:id`) — Price comparison table, buy links
4. **Subscribe** (`/subscribe`) — 4-step flow: OTP → Details → Payment → Membership card
5. **Partners** (`/partners`) — Brand partnership info + contact form

## API Endpoints
### Public
- `GET /api/search?q=&limit=60` — Search/browse products
- `GET /api/products/{id}` — Product detail with prices
- `GET /api/scrape/status` — Brand/scrape status
- `GET /api/trending` — Trending products

### Subscription Flow
- `POST /api/otp/send` — Send WhatsApp OTP (sandbox returns OTP)
- `POST /api/otp/verify` — Verify OTP
- `POST /api/payment/create-order` — Create Razorpay order (₹399)
- `POST /api/payment/verify` — Verify payment, activate membership
- `GET /api/membership/{phone}` — Get membership details

### Brand Partners
- `POST /api/partner-inquiry` — Submit brand partnership inquiry

### Scraping
- `POST /api/scrape/{brand_key}` — Trigger brand scrape
- `POST /api/scrape/all` — Scrape all brands

## What's Implemented (April 2026)
- [x] Complete VIP luxury UI redesign
- [x] Fully responsive (mobile 375px, tablet 768px, desktop 1920px)
- [x] Public website (no login required to browse)
- [x] Real-time scrapers for 3 brands (998 products)
- [x] Product search with brand/category filters
- [x] Price comparison on product pages
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment flow (SANDBOX)
- [x] Digital membership card generation
- [x] Brand partnership page with inquiry form
- [x] All tests passing: 29/29 backend + 100% frontend

## Upcoming Tasks (Priority Order)
- [ ] **P0**: WhatsApp Business API integration (real OTP + alerts)
- [ ] **P0**: Razorpay production keys + UPI payment
- [ ] **P0**: Apple Wallet / Google Wallet pass generation
- [ ] **P1**: Scale scrapers to 20+ streetwear brands
- [ ] **P1**: Amazon.in, Flipkart, Myntra scrapers
- [ ] **P1**: Price history tracking + charts
- [ ] **P2**: Visual search (image upload)
- [ ] **P2**: Brand partner dashboard (self-serve)
- [ ] **P3**: Instagram drop tracking
- [ ] **P3**: Push notifications as backup to WhatsApp
