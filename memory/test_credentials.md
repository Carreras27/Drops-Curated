# Test Credentials - Drops Curated

## WhatsApp OTP Login (Sandbox Mode)
- **Phone**: Any 10-digit Indian number starting with 6-9 (e.g., `9876543210`, `9999888877`)
- **OTP**: Auto-filled in sandbox mode (displayed in toast notification)

## Razorpay Payment (Sandbox Mode)
- Payment is auto-approved in sandbox mode
- Click "Confirm Payment (Sandbox)" to proceed

## Test Subscribers Created by Testing Agent
- `9876543221` - Test subscriber for categories/sizes
- `9876543222` - Test subscriber for categories/sizes
- `9876543223` - Test subscriber for categories/sizes
- `9876543224` - Test subscriber (preferences: garments, sneakers, M, L, UK9)
- `9876543225` - Test subscriber for categories/sizes
- `9999888877` - Test subscriber

## API Endpoints
- POST `/api/otp/send` - Send OTP to phone
- POST `/api/otp/verify` - Verify OTP
- POST `/api/payment/create-order` - Create Razorpay order
- POST `/api/payment/verify` - Verify payment
- POST `/api/preferences` - Save user preferences
- GET `/api/preferences/{phone}` - Get user preferences

## Notes
- Twilio and Razorpay are in SANDBOX/TEST mode
- Real WhatsApp messages are NOT sent (logged only)
- Real payments are NOT processed
