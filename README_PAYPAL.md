# 💳 PayPal Integration for Streamlit

Easily integrate PayPal payments into your Streamlit apps with a secure, popup-based checkout flow.

## Features

- 🔒 **Secure**: Client Secret never exposed to frontend
- 💳 **Popup Checkout**: Professional payment experience
- ✅ **Auto Capture**: Automatic order capture after approval
- 🛡️ **CSRF Protected**: Built-in security measures
- 🌍 **Multi-Currency**: Support for USD, EUR, GBP, TWD, JPY, and more
- 🧪 **Sandbox Ready**: Easy testing with PayPal Sandbox

## Installation

```bash
pip install streamlit-oauth
```

## Quick Start

### 1. Get PayPal Credentials

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications)
2. Create a new app or use an existing one
3. Copy your **Sandbox** Client ID and Secret (for testing)
4. Configure your redirect URI: `https://your-domain/component/streamlit_oauth.authorize_button`

> **Note:** The callback URL uses `authorize_button` because this component is built on streamlit-oauth's architecture. This endpoint handles both OAuth and PayPal callbacks. The name refers to the user authorizing/approving the payment.

### 2. Basic Usage

```python
import streamlit as st
from streamlit_oauth import PayPalComponent, PayPalError
import os

# Initialize PayPal component
paypal = PayPalComponent(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
    mode='sandbox'  # or 'production'
)

# Create payment button
if 'payment' not in st.session_state:
    result = paypal.payment_button(
        name="Pay $10 USD",
        amount=10.00,
        currency='USD',
        redirect_uri='https://your-app.streamlit.app/component/streamlit_oauth.authorize_button',
        description='Purchase item',
        key='payment_btn'
    )

    if result:
        st.session_state.payment = result
        st.rerun()
else:
    payment = st.session_state.payment
    st.success(f"Payment successful! Order ID: {payment['order_id']}")
```

### 3. Environment Variables

Create a `.env` file:

```env
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_REDIRECT_URI=http://localhost:8501/component/streamlit_oauth.authorize_button
```

## API Reference

### `PayPalComponent`

```python
PayPalComponent(client_id, client_secret, mode='sandbox')
```

**Parameters:**
- `client_id` (str): PayPal Client ID (different for sandbox/production)
- `client_secret` (str): PayPal Client Secret (never exposed to frontend)
- `mode` (str): `'sandbox'` or `'production'`

### `payment_button()`

```python
payment_button(
    name,
    amount,
    currency='USD',
    redirect_uri=None,
    description='',
    key=None,
    icon=None,
    use_container_width=False,
    popup_height=800,
    popup_width=600
)
```

**Parameters:**
- `name` (str): Button label
- `amount` (float): Payment amount
- `currency` (str): Currency code (e.g., 'USD', 'EUR', 'TWD')
- `redirect_uri` (str): Redirect URI after payment (must match PayPal app settings)
- `description` (str): Payment description
- `key` (str): Unique button identifier
- `icon` (str): Button icon (data URI or URL)
- `use_container_width` (bool): Expand button to container width
- `popup_height` (int): Popup window height
- `popup_width` (int): Popup window width

**Returns:**
- `dict` or `None`: Payment result containing:
  - `order_id`: PayPal order ID
  - `status`: Payment status (e.g., 'COMPLETED')
  - `payer`: Payer information
  - `purchase_units`: Purchase details
  - `captured`: Full capture response

## Examples

### Custom Button Style

```python
result = paypal.payment_button(
    name="Buy Now - $29.99",
    amount=29.99,
    currency='USD',
    redirect_uri=os.getenv('PAYPAL_REDIRECT_URI'),
    icon='💳',
    use_container_width=True,
    popup_height=900,
    popup_width=700
)
```

### Error Handling

```python
try:
    result = paypal.payment_button(
        name="Pay Now",
        amount=50.00,
        currency='USD',
        redirect_uri=os.getenv('PAYPAL_REDIRECT_URI'),
        description='Premium subscription'
    )

    if result:
        st.success("Payment successful!")
        st.json(result)

except PayPalError as e:
    st.error(f"Payment failed: {str(e)}")
```

### Multiple Currencies

```python
currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "TWD", "JPY"])

result = paypal.payment_button(
    name=f"Pay {amount} {currency}",
    amount=amount,
    currency=currency,
    redirect_uri=os.getenv('PAYPAL_REDIRECT_URI')
)
```

## Security Features

### Built-in Protection

1. **Client Secret Security**: Client Secret only used on backend, never exposed to frontend
2. **Order ID Verification**: Backend verifies order was created by the app
3. **Time-based Expiration**: Orders expire after 5 minutes
4. **CSRF Protection**: Prevents cross-site request forgery attacks

### Best Practices

```python
# ✅ Good: Use environment variables
paypal = PayPalComponent(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
    mode='sandbox'
)

# ❌ Bad: Hardcode credentials
paypal = PayPalComponent(
    client_id='hardcoded_id',
    client_secret='hardcoded_secret',
    mode='sandbox'
)
```

## Testing with Sandbox

1. Use **Sandbox** mode during development
2. Create test accounts at [PayPal Sandbox](https://developer.paypal.com/tools/sandbox/)
3. Use Sandbox credentials in your `.env` file
4. Test payments with Sandbox buyer accounts

### Sandbox vs Production

| Environment | Client ID Source | API Endpoint | Checkout URL |
|------------|------------------|--------------|--------------|
| Sandbox | PayPal Developer Dashboard → App → Sandbox | `api-m.sandbox.paypal.com` | `www.sandbox.paypal.com` |
| Production | PayPal Developer Dashboard → App → Live | `api-m.paypal.com` | `www.paypal.com` |

## Going to Production

1. **Get Live Credentials**:
   - Verify your PayPal Business account
   - Go to your app in PayPal Developer Dashboard
   - Switch to "Live" tab to get production credentials

2. **Update Configuration**:
   ```python
   paypal = PayPalComponent(
       client_id=os.getenv('PAYPAL_LIVE_CLIENT_ID'),
       client_secret=os.getenv('PAYPAL_LIVE_CLIENT_SECRET'),
       mode='production'  # Important!
   )
   ```

3. **Update Redirect URI**:
   - Use your production domain
   - Configure in PayPal app settings

4. **Security Checklist**:
   - [ ] Use HTTPS (required for production)
   - [ ] Store credentials in secure environment variables
   - [ ] Never commit credentials to version control
   - [ ] Test thoroughly in sandbox first
   - [ ] Monitor transactions in PayPal dashboard

## Troubleshooting

### Common Issues

**Issue**: "Failed to get access token"
- **Solution**: Check your Client ID and Secret are correct and match the selected mode (sandbox/production)

**Issue**: "Unknown order ID - possible CSRF attack"
- **Solution**: Order expired (>5 minutes) or session state was cleared. Try creating a new payment.

**Issue**: Popup doesn't close after payment
- **Solution**: Ensure redirect URI is correctly configured in PayPal app settings and matches the one passed to `payment_button()`

**Issue**: "No approval URL in order response"
- **Solution**: Check PayPal API response. May indicate an issue with order creation or API credentials.

### Debug Mode

Enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example App

See `examples/paypal_basic.py` for a complete working example.

```bash
streamlit run examples/paypal_basic.py
```

## Architecture

```
┌─────────────────────────────────────┐
│ Streamlit App (Python Backend)      │
│                                     │
│  1. User clicks payment button      │
│  2. Create order (with secret) ──┐  │
│  3. Pass order_id to frontend    │  │
│     ↓                            │  │
│  ┌──────────────────────────┐   │  │
│  │ JavaScript Component     │   │  │
│  │  4. Open PayPal popup    │   │  │
│  │  5. User completes pay   │   │  │
│  │  6. Return order_id      │   │  │
│  └──────────────────────────┘   │  │
│     ↓                            │  │
│  7. Verify order_id             │  │
│  8. Capture order (with secret) ─┘  │
│  9. Return payment result           │
└─────────────────────────────────────┘
```

## Contributing

Contributions welcome! This project is forked from [streamlit-oauth](https://github.com/dnplus/streamlit-oauth) with PayPal payment integration.

## License

Same as original streamlit-oauth project.

## Credits

- Original `streamlit-oauth` by [Dylan Lu](https://github.com/dnplus)
- PayPal integration adapted for payment flows

---

**Need help?** Check the [examples](./examples/) directory or open an issue.
