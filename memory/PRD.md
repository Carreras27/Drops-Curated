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

## Live Brands (14 total, 7,097+ products)
| Brand | Platform | Products |
|-------|----------|----------|
| Crep Dog Crew | Shopify | 1680 |
| Capsul | Shopify | 750 |
| Huemn | Shopify | 985 |
| Urban Monkey | Shopify | 743 |
| Bluorng | Shopify | 551 |
| House of Koala | Shopify | 306 |
| Farak | Shopify | 270 |
| Almost Gods | Shopify | 224 |
| Jaywalking | Shopify | 190 |
| Hiyest | WooCommerce | 126 |
| Veg Non Veg | HTML parse | 153 |
| Culture Circle | Playwright | 114 |
| Code Brown | Shopify | 53 |
| Noughtone | Shopify | 37 |

## Core System Architecture
1. **Auto-Scraper** (every 15 min): Scrapes all 14 brands, detects price changes + new products
2. **Alert Engine**: Compares prices, sends targeted WhatsApp alerts based on user preferences
3. **Preference System**: Users choose brands + alert types (price drops / new releases / both)

## Pages
1. **Landing** (`/`) — Hero, 3 pillars, stats, partners, CTA
2. **Browse** (`/browse`) — Grid with search/brand/category filters
3. **Product** (`/product/:id`) — Price comparison, buy links
4. **Subscribe** (`/subscribe`) — 5-step: OTP → Details → Payment → Preferences → Card
5. **Partners** (`/partners`) — Brand partnership + contact form

## What's Implemented (April 2026)
- [x] VIP luxury UI, fully responsive
- [x] 14 brand scrapers (7,097+ real products)
- [x] Auto-scraping every 15 minutes
- [x] Price drop detection + new product detection
- [x] WhatsApp alert engine (SANDBOX - Twilio)
- [x] User preferences (brand selection + alert types)
- [x] WhatsApp OTP registration (SANDBOX)
- [x] Razorpay UPI payment (SANDBOX)
- [x] Digital membership card
- [x] Brand partnership page
- [x] All tests: 100% pass (4 iterations)

## Upcoming Tasks
- [ ] **P0**: Twilio production keys (real WhatsApp delivery)
- [ ] **P0**: Razorpay production keys (live UPI)
- [ ] **P0**: Apple/Google Wallet pass generation
- [ ] **P1**: WhatsApp bot for preference management
- [ ] **P1**: Price history charts on product pages
- [ ] **P1**: Amazon.in, Flipkart, Myntra scrapers
- [ ] **P2**: Visual search (image upload)
- [ ] **P2**: Brand partner self-serve dashboard
- [ ] **P3**: Instagram drop tracking
