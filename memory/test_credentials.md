# Test Credentials - Drops Curated

## Admin Panel Login
- **URL**: `/admin`
- **Email**: `admin@dropscurated.com`
- **Password**: `DropsCurated2024!`

## WhatsApp OTP Login (Sandbox Mode)
- **Phone**: Any 10-digit Indian number starting with 6-9 (e.g., `9876543210`, `9999888877`)
- **OTP**: Auto-filled in sandbox mode (displayed in toast notification)

## Registration Flow (Mandatory Fields)
Step 1: Enter WhatsApp number → Receive OTP (sandbox auto-fills)
Step 2: **Details Step** - All fields REQUIRED:
  - Full Name
  - Email Address
  - WhatsApp Number (auto-filled from Step 1)
  - Home Address
Step 3: Payment (sandbox auto-approves)
Step 4: **Preference Funnel** - Customize alert preferences:
  - Section A: Brand Selection (Top 5/10/Unlimited limit)
  - Section B: Trigger-Based Filtering (New Drops, Price Drops, Restock)
  - Section C: Specificity (Categories, Sizes)
  - Section D: Notification Frequency (Instant vs Daily Digest)
Step 5: Success - Membership card displayed

## Razorpay Payment (Sandbox Mode)
- Payment is auto-approved in sandbox mode
- Click "Confirm Payment (Sandbox)" to proceed

## Test Subscribers Created by Testing Agent
- `9876543210` - Test subscriber with custom preferences
- `9876543221-9876543225` - Test subscribers for categories/sizes
- `9876543230-9876543240` - Test subscribers for wallet tests
- `9111222333` - VIP Member test subscriber
- `9876543298`, `9876543299`, `9876543111` - Additional test subscribers

## Preference Funnel API Testing

### Save Preferences
```bash
curl -X POST "$API_URL/api/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "brands": ["SUPERKICKS", "HUEMN", "CAPSUL"],
    "brand_limit": 5,
    "alert_types": ["price_drop", "new_release", "restock"],
    "categories": ["sneakers"],
    "sizes": ["UK9", "UK10"],
    "price_range": {"min": 5000, "max": 25000},
    "keywords": ["jordan", "nike", "dunk"],
    "drop_threshold": 15,
    "alert_frequency": "daily"
  }'
```

### Get Preferences
```bash
curl "$API_URL/api/preferences/9876543210"
```

### Check Scheduler Status
```bash
curl "$API_URL/api/scheduler/status"
```

## API Endpoints
- POST `/api/otp/send` - Send OTP to phone
- POST `/api/otp/verify` - Verify OTP
- POST `/api/payment/create-order` - Create order (requires: phone, name, email, address)
- POST `/api/payment/verify` - Verify payment
- POST `/api/preferences` - Save user preferences (full preference funnel)
- GET `/api/preferences/{phone}` - Get user preferences
- GET `/api/membership/{phone}` - Get membership (returns email, address)
- POST `/api/wallet/apple` - Generate Apple Wallet pass
- POST `/api/wallet/google` - Generate Google Wallet pass
- GET `/api/scheduler/status` - Get scheduler status (shows auto_scrape and daily_digest jobs)
- GET `/api/alerts/digest/{phone}` - Get pending daily digest for a user
- POST `/api/alerts/send-digests` - Trigger daily digest send

## Scheduler Jobs
- **auto_scrape**: Runs every 15 minutes to scrape all 23 brands
- **daily_digest**: Runs at 8 PM IST (14:30 UTC) to send daily digest messages

## Wallet Integration Status
- **Apple Wallet**: API ready, requires Apple Developer certificates to activate
- **Google Wallet**: API ready, requires Google Cloud credentials to activate

Both wallet buttons show informative messages about requirements when clicked.

## Notes
- Meta WhatsApp Cloud API in SANDBOX mode (messages logged to console)
- Razorpay is in SANDBOX/TEST mode (payments auto-approve)
- Real WhatsApp messages are NOT sent (pending Meta template approval)
- Real payments are NOT processed
- Wallet passes are NOT generated until certificates are provided
