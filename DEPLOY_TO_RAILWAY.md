# 🚂 Deploy Drops Curated to Railway

This guide migrates the app off Emergent to **Railway** — an always-on host
that costs ~$5/mo and won't put your scheduler to sleep. Your scrapers will
actually run on time.

Estimated time: **30 min** total.

---

## Why Railway?

| Emergent today | Railway after migration |
|---|---|
| Pods sleep → scheduler skips runs → brands go stale → wrong-price alerts | Always-on workers, scheduler runs reliably |
| ~$10/mo deployment + LLM credits via Emergent Universal Key | ~$5/mo + direct Gemini API at ~$0.075 per 1M tokens |
| Custom domain stuck at Cloudflare 1034 | One-click custom-domain setup |

---

## Prerequisites

You'll need accounts on three services (all free to start):

1. **Railway** — https://railway.app (sign in with GitHub)
2. **MongoDB Atlas** — https://www.mongodb.com/cloud/atlas/register (free 512MB cluster — enough for your 29k products)
3. **Google AI Studio** — https://aistudio.google.com (free Gemini API key)
4. **GitHub** — you'll push your code here from Emergent

---

## Step 1 — Push code to GitHub (3 min)

In the Emergent chat interface:

1. Click **"Save to GitHub"** (top-right or `...` menu)
2. Authorize GitHub if prompted
3. Choose a repo name (e.g. `drops-curated`)
4. Click **Save** — Emergent pushes `/app` to your new repo

Verify on GitHub that the repo contains `backend/`, `frontend/`, `railway.json`, `Procfile`, and `nixpacks.toml`.

---

## Step 2 — Create MongoDB Atlas database (10 min)

1. Sign up at https://www.mongodb.com/cloud/atlas/register
2. Choose **"M0 Free"** cluster (512MB, enough for now)
3. **Region**: pick the one geographically closest to your Railway region (Mumbai → Singapore is fine)
4. **Username + password**: write them down — you'll paste them into Railway
5. **Network Access**: click **"Allow access from anywhere"** (`0.0.0.0/0`) — Railway uses dynamic IPs
6. **Get connection string**: click **"Connect"** → **"Drivers"** → copy the URI
   - It looks like: `mongodb+srv://<user>:<pw>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
   - **Replace** `<pw>` with your actual password (URL-encoded if it has special chars)

### Migrate your data (one-time)

From your local machine or any environment with mongoexport:

```bash
# Dump from Emergent
mongodump --uri="<EMERGENT_MONGO_URL>" --db=test_database --out=./dump

# Restore to Atlas
mongorestore --uri="<ATLAS_MONGO_URL>" --db=test_database ./dump/test_database
```

If you can't run mongodump locally, message me — we can write a Python script that uses the existing backend code to export/import.

---

## Step 3 — Get a Gemini API key (2 min)

1. Go to https://aistudio.google.com/apikey
2. Click **"Create API key"**
3. **Copy** the key — it starts with `AIzaSy...`

Free tier: 15 requests per minute, 1500 per day. Plenty for our scraper-healer use case.

---

## Step 4 — Deploy to Railway (10 min)

1. Go to https://railway.app and click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Pick your `drops-curated` repo
4. Railway auto-detects Python/Node and starts building
5. While it builds, click the new service → **Variables** tab → paste these env vars:

### Required environment variables

```
# === Mongo ===
MONGO_URL=mongodb+srv://<user>:<pw>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=test_database

# === LLM ===
GEMINI_API_KEY=AIzaSy...

# === Public URL (set after first deploy completes) ===
APP_URL=https://your-app.up.railway.app
BACKEND_PUBLIC_URL=https://your-app.up.railway.app

# === Frontend (set in Railway frontend service, not backend) ===
REACT_APP_BACKEND_URL=https://your-app.up.railway.app

# === Brevo (email alerts) ===
BREVO_API_KEY=<copy from old backend/.env>
BREVO_SENDER_EMAIL=alerts@dropscurated.com
BREVO_SENDER_NAME=Drops Curated Alerts
BREVO_REPLY_TO=Dropscurated@gmail.com

# === Telegram ===
TELEGRAM_BOT_TOKEN=<copy>
TELEGRAM_BOT_USERNAME=Dropscurated_alerts_bot

# === WhatsApp (sandbox for now) ===
WHATSAPP_ACCESS_TOKEN=<copy>
WHATSAPP_PHONE_NUMBER_ID=<copy>
WHATSAPP_BUSINESS_ACCOUNT_ID=<copy>
WHATSAPP_APP_SECRET=<copy>
WHATSAPP_API_VERSION=v21.0

# === Razorpay ===
RAZORPAY_KEY_ID=<copy>
RAZORPAY_KEY_SECRET=<copy>
REACT_APP_RAZORPAY_KEY_ID=<copy, same as above>

# === Cloudflare Turnstile ===
REACT_APP_TURNSTILE_SITE_KEY=<copy>
TURNSTILE_SECRET_KEY=<copy>
TURNSTILE_SANDBOX_BYPASS=0

# === Security ===
JWT_SECRET=<copy or regenerate with: openssl rand -hex 32>
FRONTEND_API_KEY=<copy>
ADMIN_IP_ALLOWLIST=
CORS_ORIGINS=https://dropscurated.com,https://www.dropscurated.com

# === Misc ===
ENABLE_HEALTH_CHECK=true
MAX_ALERT_AGE_HOURS=10
```

6. Click **"Deploy"** — wait ~3–5 min for build to finish
7. Once green, Railway gives you a `*.up.railway.app` URL
8. **Update** `APP_URL`, `BACKEND_PUBLIC_URL`, and `REACT_APP_BACKEND_URL` to that URL
9. Trigger a redeploy (Settings → Redeploy)

---

## Step 5 — Verify the deploy (2 min)

```bash
# Frontend
curl -I https://your-app.up.railway.app
# Expected: HTTP 200

# Backend API
curl https://your-app.up.railway.app/api/beta/status
# Expected: {"total":100,"taken":0,"spots_left":100,"is_open":true}

# Scrape status
curl https://your-app.up.railway.app/api/scrape/status
# Expected: JSON with total_products and brands array
```

If any fail, check **Railway logs** for the failing service.

---

## Step 6 — Connect dropscurated.com (5 min)

This is finally easier on Railway than Emergent:

### In Railway:
1. Open your service → **Settings** → **Networking** → **Custom Domain**
2. Add `dropscurated.com` → Railway shows you a CNAME target like `dropscurated-production.up.railway.app`

### In Cloudflare:
1. DNS → Records
2. **Delete** the two A records pointing at `162.159.142.117` and `172.66.2.113` (left over from Emergent)
3. Add: `CNAME @ → <railway-target>` — **DNS only (grey cloud)** initially
4. Wait 2–3 min for Railway to issue a cert (it auto-provisions)
5. Once Railway shows ✅ next to the domain, **turn the Cloudflare proxy back on (orange cloud)**
6. SSL/TLS → set to **"Full (strict)"**

---

## Step 7 — Re-point Telegram webhook (1 min)

Log in to admin on `https://dropscurated.com/admin`:
1. Email: `admin@dropscurated.com`, password: `DropsCurated2024!`
2. Go to **Telegram** tab
3. Click **"Use this host"** → **"Register webhook with Telegram"**
4. Send `/start` to [@Dropscurated_alerts_bot](https://t.me/Dropscurated_alerts_bot) — bot should reply

---

## Step 8 — Verify cost savings

After 24h, check:
- Railway dashboard → **Usage** — should be ~$0.20/day (~$6/mo)
- Google AI Studio → **Quota** — Gemini calls running at near-zero cost
- Compare with previous month's Emergent credit burn

Expected total: **$5–10/mo** vs. **$15–25/mo** on Emergent.

---

## Rollback plan

If anything breaks on Railway, your Emergent deployment at `drops-curated.emergent.host` is **still running**. To roll back:
1. In Cloudflare, change the CNAME back to `drops-curated.emergent.host`
2. Wait 5 min for DNS

Nothing in the migration deletes your Emergent setup — they coexist.

---

## What changed in the code (for reference)

You don't need to do anything — this is just so you know:

- **`backend/llm_client.py`** (new): single adapter that picks `GEMINI_API_KEY` first, then `EMERGENT_LLM_KEY` as fallback. Means the code works on either host without changes.
- **`backend/classifier.py`** & **`backend/scraper_agent.py`**: use the adapter instead of importing `emergentintegrations` directly.
- **`railway.json`, `Procfile`, `nixpacks.toml`**: Railway-specific config (ignored by Emergent).

No behaviour changes when running on Emergent.
