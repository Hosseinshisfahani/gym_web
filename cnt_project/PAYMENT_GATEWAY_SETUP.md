# Payment Gateway Integration Setup

This document explains how to configure and use the payment gateway integration for plan request payments.

## Supported Payment Gateways

- **ZarinPal** (Default)
- **IDPay**

## Configuration

### 1. Update Django Settings

Edit `gym_website/settings.py` and update the payment gateway configuration:

```python
# Payment Gateway Configuration
# ZarinPal Configuration
ZARINPAL_MERCHANT_ID = 'your-actual-merchant-id'  # Replace with your merchant ID

# IDPay Configuration  
IDPAY_API_KEY = 'your-actual-api-key'  # Replace with your API key

# Payment Gateway Settings
PAYMENT_GATEWAY_TYPE = 'zarinpal'  # Options: 'zarinpal', 'idpay'
```

### 2. Run Database Migration

Apply the new database migration for payment gateway fields:

```bash
python manage.py migrate
```

### 3. Gateway Setup Instructions

#### For ZarinPal:
1. Register at [zarinpal.com](https://zarinpal.com)
2. Get your Merchant ID from the dashboard
3. Update `ZARINPAL_MERCHANT_ID` in settings
4. For testing, use sandbox: the system automatically uses sandbox URLs in DEBUG mode

#### For IDPay:
1. Register at [idpay.ir](https://idpay.ir)
2. Get your API Key from the dashboard
3. Update `IDPAY_API_KEY` in settings
4. Set `PAYMENT_GATEWAY_TYPE = 'idpay'` in settings

## How It Works

### Payment Flow:
1. User selects a plan request payment
2. User chooses between:
   - **Gateway Payment** (Recommended): Direct online payment
   - **Manual Payment**: Transfer to card + receipt upload
3. For gateway payments:
   - User is redirected to payment gateway
   - After payment, gateway returns to callback URL
   - System verifies payment and creates plan request
   - User sees success/failure message

### Payment Statuses:
- `pending`: Payment initiated but not verified
- `approved`: Payment successfully verified
- `failed`: Payment failed or verification failed
- `rejected`: Manually rejected by admin

## Features

### Gateway Payment Benefits:
- ✅ Instant payment verification
- ✅ Automatic plan request creation
- ✅ No manual admin verification needed
- ✅ Better user experience
- ✅ Secure payment processing

### Manual Payment (Fallback):
- Still available if gateway is unavailable
- Requires admin verification
- Upload receipt functionality

## Testing

### ZarinPal Testing:
- Use sandbox merchant ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- System automatically uses sandbox URLs in DEBUG mode
- Test card numbers available in ZarinPal documentation

### IDPay Testing:
- Use test API key provided by IDPay
- System uses same URLs for testing and production

## Security

- All payment data is transmitted securely via HTTPS
- Gateway credentials are stored in Django settings
- Payment verification ensures transaction authenticity
- Authority tokens prevent payment manipulation

## Troubleshooting

### Common Issues:

1. **Payment fails immediately**
   - Check gateway credentials in settings
   - Verify internet connectivity
   - Check gateway service status

2. **Payment successful but not verified**
   - Check callback URL accessibility
   - Verify authority parameter in callback
   - Check logs for verification errors

3. **Gateway not accessible**
   - Ensure HTTPS is available for production
   - Check firewall settings
   - Verify callback URL domain

### Debug Mode:
- Enable Django DEBUG mode for detailed error messages
- Check logs in `logs/django.log` for payment gateway errors
- Test with small amounts first

## Support

For payment gateway specific issues:
- ZarinPal: [support.zarinpal.com](https://support.zarinpal.com)
- IDPay: [idpay.ir/contact](https://idpay.ir/contact)

For integration issues, check the Django logs and ensure all configuration steps are completed correctly. 