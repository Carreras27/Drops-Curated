# IndiaShop - Product Requirements Document

## Overview
IndiaShop is a real-time price comparison engine for the Indian e-commerce market, focusing on shoes, clothes, and cosmetics across 25+ sources including major marketplaces and indie streetwear brands.

## Target Sources
### Tier 1: Major Marketplaces
- Amazon.in
- Flipkart
- Myntra
- Ajio
- Nykaa

### Tier 2: Indie Streetwear Brands (20 brands)
Priority based on search volume and Instagram following:
- **Tier S** (Every 6h): Veg Non Veg, Super Kicks, Culture Circle
- **Tier A** (Every 12h): Crep Dog Crew, Blu Orange, Jaywalking, Almost Gods
- **Tier B** (Every 24h): Dawn Tawn, Comet, Midnight Law, Noughtone, Drippinn Moncky, Smokelab, Shiarai, Exhale, Toffle, Biskit, FKNS, Narendra Kumar, Ask by Avishi

## Core Features
1. **Text Search**: Search products across all sources
2. **Visual Search**: Upload image to find similar products
3. **Price Comparison**: Real-time price updates with discount tracking
4. **Price Alerts**: Notify users when prices drop
5. **Drop Calendar**: Track limited edition releases
6. **Trending Products**: Popular items based on search/watchlist data
7. **Instagram Integration**: Monitor brand drops on social media

## Monetization
1. **Affiliate Links** (70%): Commission from purchases
2. **Premium Subscription** (15%): ₹199/month for unlimited features
3. **Sponsored Listings** (10%): Brands pay for featured placement
4. **Instagram Drops** (5%): Charge brands for drop promotion

## Design System
- **Light Mode**: White base (#FFFFFF)
- **Dark Mode**: Black base (#0A0A0A)
- **Pop Colors**:
  - Primary: Electric Blue (#0066FF)
  - Secondary: Hot Pink (#FF0080)
  - Success: Neon Green (#00FF85)
  - Warning: Bright Orange (#FF6B00)
- **Typography**: Inter/Geist (minimalistic)
- **Style**: Clean, generous whitespace, sharp/subtle corners

## Tech Stack
- Frontend: Next.js 15, TypeScript, Tailwind CSS, Shadcn/UI
- Backend: FastAPI, Python, Celery, Redis
- Database: PostgreSQL + pgvector (Supabase)
- Scraping: Playwright, BeautifulSoup, Free proxies (MVP)
- AI: OpenAI CLIP for visual search
- Payment: Stripe for subscriptions

## Launch Plan
- Phase 1: Core search + 5 test brands
- Phase 2: Scale to 25+ brands + Instagram tracking
- Phase 3: Premium features + monetization
- Phase 4: Browser extension + mobile app
