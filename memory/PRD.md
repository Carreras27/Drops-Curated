# Drops Curated — Product Requirements Document

## Original Problem Statement
Premium VIP subscription platform (₹399/month) for the Indian luxury streetwear market. Core value: real-time WhatsApp alerts for new drops and price reductions within 10 seconds.

## Brand Narrative
"Curated Excellence. Delivered Instantly." — India's most refined streetwear intelligence platform. A meticulously curated discovery ecosystem connecting discerning collectors with the finest limited drops, exclusive releases, and premium collections from India's most respected brands. Win-win: buyers get speed + convenience, brands get high-intent traffic — no intermediaries, no commissions.

## Architecture
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python + APScheduler + MongoDB
- **AI**: Gemini 2.5 Flash (Scraper Self-Healing via Emergent LLM Key)
- **Scraping**: Playwright + BeautifulSoup + AETHER SWARM v1.0
- **Monitoring**: AETHER MASTER v1.0 (autonomous 5-min health cycles)
- **Monetization**: 7-Day Local/DB Trial → Razorpay Subscriptions

## What's Been Implemented

### Landing Page (COMPLETE — Updated Feb 2026)
- Hero: "Curated Excellence. Delivered Instantly." + premium description
- Benefits for Buyers: 4 cards (alerts, discovery, privileged access, tailored)
- Platform Story: "A Win-Win Ecosystem" with centralized DB narrative
- Benefits for Brands: 4 cards (traffic, prestige, loyalty, insights)
- How It Works: 3-step win-win flow
- Footer disclaimer (independence/non-affiliation)
- Live stats social proof, brand marquee, live timestamp

### Scraping System (COMPLETE)
- 24 premium Indian streetwear brands tracked
- AETHER SWARM v1.0: Multi-persona rotation, AetherBrain self-learning, AetherHuman
- LLM Self-Healing Scraper Agent (Gemini 2.5 Flash)
- Auto-scrape every 15 minutes with staggered delays

### AETHER MASTER v1.0 (COMPLETE)
- Autonomous 5-minute health monitoring
- Auto-heals: service restarts, scraper retriggers
- Incident memory persisted to MongoDB
- Admin dashboard with latency bars, incidents, cycle history

### Admin Panel (COMPLETE)
- Dashboard, CRM (Analytics/Revenue/Broadcast), Subscribers, Brands
- Aether Master, Scraper Health, Agent Logs, AI Classification

### Frontend (PARTIALLY COMPLETE)
- Landing page, Browse page, Wishlist Portfolio, Subscribe page
- Warm cream / gold minimalist theme (NO dark mode)

### Backend (COMPLETE)
- FastAPI (3150+ lines), WhatsApp Cloud API, Razorpay, Cloudflare Turnstile
- AI classification, duplicate detection, rate limiting

## Prioritized Backlog

### P0 (In Progress)
- [ ] 7-Day Free Trial: Blurred pricing, locked filters, disabled wishlist

### P1
- [ ] SubscribePage: 10-digit Indian phone validation
- [ ] BrowsePage UI: sort options, empty state, "Wrong category?" button
- [ ] Apple/Google Wallet digital membership cards
- [ ] Production keys migration

### P2
- [ ] Drop Calendar UI
- [ ] Brand Partner Dashboard
- [ ] Refactor server.py into routes/ directory

## Date Log
- Feb 2026: AETHER SWARM v1.0 deployed
- Feb 2026: AETHER MASTER v1.0 + CRM Dashboard + Admin Panel
- Feb 2026: Landing page rewritten with premium narrative
