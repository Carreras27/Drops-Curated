# Drops Curated - Product Requirements Document

## Overview
**Drops Curated** is a premium paid discovery platform for Indian luxury streetwear. Users browse curated drops publicly and pay ₹399/month for WhatsApp alerts on price drops, new collections, and restocks within 10 seconds.

## Business Model
- ₹399/month subscription via UPI (Razorpay)
- WhatsApp OTP registration (prevents spam bans)
- Digital membership card (Apple Wallet + Google Wallet)
- Brand partnerships: showcase collections + bulk membership discounts for VIP customers
- 0% commission on purchases

## Design Language: "Warm Minimalist VIP"
- Background: #FDFBF7 | Primary: #001F3F | Accent: #D4AF37
- Typography: Playfair Display + Inter
- Vibe: Digital boutique, luxury, exclusive

## Tech Stack
- Frontend: React, Tailwind CSS, Lucide React
- Backend: Python FastAPI, MongoDB
- Payments: Razorpay (SANDBOX)
- Scraping: Generic Shopify API scraper + WooCommerce + httpx/BeautifulSoup + Playwright

## Live Brands (14 total, 4,951 products)
| Brand | Platform | Products |
|-------|----------|----------|
| Crep Dog Crew | Shopify | 750 |
| Capsul | Shopify | 750 |
| Huemn | Shopify | 748 |
| Urban Monkey | Shopify | 743 |
| Bluorng | Shopify | 551 |
| House of Koala | Shopify | 306 |
| Farak | Shopify | 270 |
| Almost Gods | Shopify | 190 |
| Jaywalking | Shopify | 190 |
| Hiyest | WooCommerce | 126 |
| Culture Circle | Playwright | 114 |
| Veg Non Veg | HTML parsing | 86 |
| Code Brown | Shopify | 53 |
| Noughtone | Shopify | 26 |

## Pages
1. **Landing** (`/`) — Hero, 3 pillars, stats, partners, CTA
2. **Browse** (`/browse`) — Grid with search/brand/category filters
3. **Product Detail** (`/product/:id`) — Price comparison, buy links
4. **Subscribe** (`/subscribe`) — OTP → Details → Payment → Membership card
5. **Partners** (`/partners`) — Brand partnership info + contact form

## What's Implemented (April 2026)
- [x] VIP luxury UI (fully responsive)
- [x] 14 brand scrapers (4,951 real products)
- [x] Product search with brand/category filters
- [x] Price comparison on product pages
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment (SANDBOX)
- [x] Digital membership card
- [x] Brand partnership page
- [x] All tests: 28/28 backend + 100% frontend

## Upcoming Tasks
- [ ] **P0**: WhatsApp Business API (real OTP + alerts)
- [ ] **P0**: Razorpay production keys
- [ ] **P0**: Apple/Google Wallet pass generation
- [ ] **P1**: Price history tracking + charts
- [ ] **P1**: Amazon.in, Flipkart, Myntra scrapers
- [ ] **P2**: Visual search (image upload)
- [ ] **P2**: Brand partner dashboard
- [ ] **P3**: Instagram drop tracking
