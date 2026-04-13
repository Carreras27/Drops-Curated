# Drops Curated — Product Requirements Document

## Original Problem Statement
Premium VIP subscription platform (₹399/month) for the Indian luxury streetwear market. Core value: real-time WhatsApp alerts for new drops and price reductions within 10 seconds.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python + APScheduler + MongoDB
- **AI**: Gemini 2.5 Flash (Scraper Self-Healing via Emergent LLM Key)
- **Scraping**: Playwright + BeautifulSoup + AETHER SWARM v1.0
- **Monetization**: 7-Day Local/DB Trial → Razorpay Subscriptions

## What's Been Implemented

### Scraping System (COMPLETE)
- 24 premium Indian streetwear brands tracked
- AETHER SWARM v1.0: Multi-persona rotation (7 Indian-city browser fingerprints), self-learning AetherBrain (MongoDB-persisted per-brand persona scoring), extreme human mimicry (AetherHuman)
- LLM Self-Healing Scraper Agent (Gemini 2.5 Flash) — auto-diagnoses failures, rewrites selectors
- Fingerprint caching, health tracking, proxy rotation
- Shipping tag/size filtering across all scrapers
- Auto-scrape every 15 minutes with staggered delays

### Frontend (PARTIALLY COMPLETE)
- Landing page with "Try Now" CTA
- Browse page with filters (categories, brands, sizes, accessories)
- Wishlist Portfolio with correct price calculations
- Subscribe page
- Admin dashboard
- Warm cream / gold minimalist theme (NO dark mode)

### Backend (COMPLETE)
- FastAPI with 3100+ line server.py
- WhatsApp alerts via Meta Cloud API
- Razorpay payment integration
- Cloudflare Turnstile CAPTCHA
- Rate limiting via slowapi
- AI product classification
- Duplicate detection

### 3rd Party Integrations
- Meta WhatsApp Cloud API (requires user key)
- Razorpay Payments (requires user key)
- Cloudflare Turnstile (configured in .env)
- Gemini 2.5 Flash via Emergent LLM Key (fully integrated)

## Prioritized Backlog

### P0 (In Progress)
- [ ] 7-Day Free Trial: Blurred pricing, locked filters, disabled wishlist for expired trials
  - TrialContext.js created, LandingPage CTAs updated
  - BrowsePage filter locking + ProductCard price blurring INCOMPLETE

### P1
- [ ] SubscribePage: Enforce 10-digit Indian phone validation (starting 6-9)
- [ ] BrowsePage UI: Price sort options, empty state, "Wrong category?" button
- [ ] Apple/Google Wallet digital membership cards
- [ ] Production keys migration (Razorpay, Meta WhatsApp)

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard
- [ ] Refactor server.py into routes/ directory (3100+ lines)

## Key DB Collections
- `products`: {id, name, brand, store, category, price, aiGender, ...}
- `subscribers`: {phone, name, membershipId, isActive, trialStartedAt, expiresAt...}
- `aether_learning`: {brand_key, persona_scores, best_persona, total_attempts, ...}
- `scraper_agent_logs`: {brand_key, strategy, success, message, timestamp, ...}
- `scraper_strategies`: {brand_key, strategy, confidence_score, custom_selectors, ...}
- `product_fingerprints`: {product_id, fingerprint, updated_at}

## Date Log
- Feb 2026: AETHER SWARM v1.0 deployed across all 24 scrapers
