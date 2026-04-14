# Drops Curated — Product Requirements Document

## Original Problem Statement
Premium VIP subscription platform (₹399/month) for the Indian luxury streetwear market. Core value: real-time WhatsApp alerts for new drops and price reductions within 10 seconds.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python + APScheduler + MongoDB
- **AI**: Gemini 2.5 Flash (Scraper Self-Healing via Emergent LLM Key)
- **Scraping**: Playwright + BeautifulSoup + AETHER SWARM v1.0
- **Monitoring**: AETHER MASTER v1.0 (autonomous 5-min health cycles)
- **Monetization**: 7-Day Local/DB Trial → Razorpay Subscriptions

## What's Been Implemented

### Scraping System (COMPLETE)
- 24 premium Indian streetwear brands tracked
- AETHER SWARM v1.0: Multi-persona rotation, AetherBrain self-learning, AetherHuman extreme mimicry
- LLM Self-Healing Scraper Agent (Gemini 2.5 Flash)
- Fingerprint caching, health tracking, proxy rotation
- Auto-scrape every 15 minutes with staggered delays

### AETHER MASTER v1.0 (COMPLETE)
- Autonomous 5-minute health monitoring: MongoDB, Backend APIs, Frontend, Scrapers, Scheduler
- Auto-heals: service restarts, scraper retriggers, rate-limited to 3/hour
- Incident memory persisted to MongoDB `aether_master_memory`
- WhatsApp escalation for unresolved criticals
- Admin dashboard with latency bars, incidents, cycle history

### Admin Panel (COMPLETE)
- **Dashboard**: Overview stats, quick actions
- **CRM Dashboard**: Analytics (KPIs, signup chart, preferences), Revenue (MRR/ARR, monthly breakdown), WhatsApp Broadcast
- **Subscribers**: List, search, activate/deactivate
- **Brands**: View, toggle, trigger scrape
- **Aether Master**: Live health, latencies, incidents, history, manual cycle trigger
- **Scraper Health**: Per-brand status, success rates, force retry
- **Agent Logs**: LLM strategies, confidence scores, logs
- **AI Classification**: Progress, category/gender breakdowns

### Frontend (PARTIALLY COMPLETE)
- Landing page with "Try Now" CTA
- Browse page with filters
- Wishlist Portfolio with correct calculations
- Subscribe page
- Warm cream / gold minimalist theme (NO dark mode)

### Backend (COMPLETE)
- FastAPI with 3150+ line server.py
- WhatsApp alerts via Meta Cloud API
- Razorpay payment integration
- Cloudflare Turnstile CAPTCHA + slowapi rate limiting
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

### P1
- [ ] SubscribePage: Enforce 10-digit Indian phone validation (starting 6-9)
- [ ] BrowsePage UI: Price sort options, empty state, "Wrong category?" button
- [ ] Apple/Google Wallet digital membership cards
- [ ] Production keys migration (Razorpay, Meta WhatsApp)

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard
- [ ] Refactor server.py into routes/ directory (3150+ lines)

## Key DB Collections
- `products`, `subscribers`, `brands`, `prices`, `price_history`
- `aether_learning` (SWARM persona scores)
- `aether_master_memory` (health cycles + incidents)
- `scraper_agent_logs`, `scraper_strategies`
- `product_fingerprints`, `alert_log`, `broadcast_log`
- `security_logs`

## Date Log
- Feb 2026: AETHER SWARM v1.0 deployed across all 24 scrapers
- Feb 2026: AETHER MASTER v1.0 + CRM Dashboard + Admin Panel overhaul
