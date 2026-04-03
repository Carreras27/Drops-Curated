# Test Credentials - Drops Curated

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
Step 4: Customize alert preferences (brands, categories, sizes)
Step 5: Success - Membership card displayed

## Razorpay Payment (Sandbox Mode)
- Payment is auto-approved in sandbox mode
- Click "Confirm Payment (Sandbox)" to proceed

## Test Subscribers Created by Testing Agent
- `9876543221-9876543225` - Test subscribers for categories/sizes
- `9876543230-9876543240` - Test subscribers for wallet tests
- `9111222333` - VIP Member test subscriber
- `9876543298`, `9876543299` - Mandatory fields test subscribers

## API Endpoints
- POST `/api/otp/send` - Send OTP to phone
- POST `/api/otp/verify` - Verify OTP
- POST `/api/payment/create-order` - Create order (requires: phone, name, email, address)
- POST `/api/payment/verify` - Verify payment
- POST `/api/preferences` - Save user preferences
- GET `/api/preferences/{phone}` - Get user preferences
- GET `/api/membership/{phone}` - Get membership (returns email, address)
- POST `/api/wallet/apple` - Generate Apple Wallet pass
- POST `/api/wallet/google` - Generate Google Wallet pass

## Wallet Integration Status
- **Apple Wallet**: API ready, requires Apple Developer certificates to activate
- **Google Wallet**: API ready, requires Google Cloud credentials to activate

Both wallet buttons show informative messages about requirements when clicked.

## Notes
- Twilio and Razorpay are in SANDBOX/TEST mode
- Real WhatsApp messages are NOT sent (logged only)
- Real payments are NOT processed
- Wallet passes are NOT generated until certificates are provided
