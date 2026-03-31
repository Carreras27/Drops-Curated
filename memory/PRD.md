# Drops Curated - Product Requirements Document

## Overview
**Drops Curated** is a premium paid discovery platform for the Indian luxury streetwear market. Users browse curated drops publicly and subscribe for WhatsApp alerts on new drops and price reductions.

## Design Language: "Warm Minimalist"
- **Background**: #FDFBF7 (Warm White/Eggshell)
- **Primary Text**: #001F3F (Deep Navy)
- **Accent**: #D4AF37 (Antique Gold)
- **Typography**: Playfair Display (headers) + Inter (body)
- **Vibe**: Digital boutique, high white space, soft shadows

## Tech Stack
- **Frontend**: React, Tailwind CSS, Lucide React, Shadcn UI
- **Backend**: Python FastAPI
- **Database**: MongoDB
- **Scraping**: httpx + BeautifulSoup (Crepdog, VegNonVeg), Playwright (Culture Circle)

## Current Brands (Live Scrapers)
1. **Crep Dog Crew** (Shopify JSON API) — ~750 products
2. **Veg Non Veg** (HTML parsing) — ~100 products
3. **Culture Circle** (Playwright + HTML) — ~114 products
- **Total**: ~998 real products

## Pages
1. **Landing** (`/`) — Hero, features, CTA, footer
2. **Browse** (`/browse`) — Product grid with search/filters
3. **Product Detail** (`/product/:id`) — Price comparison, buy links
4. **Subscribe** (`/subscribe`) — Plans (Free/Pro/Premium), WhatsApp form

## API Endpoints
- `GET /api/search?q=&limit=60` — Search/browse products
- `GET /api/products/{id}` — Product detail with prices
- `POST /api/subscribe` — WhatsApp subscription
- `GET /api/scrape/status` — Brand/scrape status
- `POST /api/scrape/{brand_key}` — Trigger brand scrape
- `POST /api/scrape/all` — Scrape all brands

## Monetization
- **Free**: Browse all drops, price comparison
- **Pro** (₹199/mo): WhatsApp price alerts, new drop notifications
- **Premium** (₹499/mo): Unlimited alerts, early access, exclusive deals

## What's Implemented (March 2026)
- [x] Complete Warm Minimalist UI redesign
- [x] Public website (no login required to browse)
- [x] Real-time scrapers for 3 brands (998 products)
- [x] Product search with filters
- [x] Price comparison on product pages
- [x] WhatsApp subscription form + backend
- [x] Subscription plans (Free/Pro/Premium)

## Upcoming Tasks
- [ ] **P0**: WhatsApp API integration (send actual alerts)
- [ ] **P0**: UPI payment integration for Pro/Premium plans
- [ ] **P1**: Scale scrapers to 20+ streetwear brands
- [ ] **P1**: Add Amazon.in, Flipkart, Myntra scrapers
- [ ] **P2**: Visual search (image upload to find similar products)
- [ ] **P2**: User authentication for saved preferences
- [ ] **P3**: Instagram drop tracking
- [ ] **P3**: Browser extension
