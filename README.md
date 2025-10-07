# 💳 Streamlit PayPal

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Secure and elegant PayPal payment integration for Streamlit apps**

Easily integrate PayPal payments into your Streamlit applications with a secure, popup-based payment flow.

> This project is forked from [streamlit-oauth](https://github.com/dnplus/streamlit-oauth), focusing on PayPal payment integration.

## 🚀 Quick Start

### Installation

```bash
pip install streamlit-paypal
```

### Basic Usage

Create a `.env` file with your PayPal credentials:

```bash
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
```

Then use the component in your Streamlit app:

```python
import streamlit as st
from streamlit_paypal import PayPalComponent
import os

# Initialize PayPal component
paypal = PayPalComponent(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
    mode='sandbox'  # Use 'live' for production
)

# Create payment button
if 'payment' not in st.session_state:
    result = paypal.payment_button(
        name="Pay $10 USD",
        amount=10.00,
        currency='USD',
        description='Product Purchase',
        return_url='https://yourapp.streamlit.app'  # Required!
    )

    if result:
        st.session_state.payment = result
        st.rerun()
else:
    st.success(f"Payment successful! Order ID: {st.session_state.payment['order_id']}")
```

> **⚠️ Production Notice**: This component uses Streamlit session state for immediate interaction. For reliable order processing in production (handling network interruptions, browser closures, etc.), configure **PayPal Webhooks** to receive payment notifications server-side and persist order states.

## 📚 API Reference

### PayPalComponent

```python
paypal = PayPalComponent(
    client_id: str,           # PayPal Client ID
    client_secret: str,       # PayPal Client Secret
    mode: str = 'sandbox'     # 'sandbox' or 'live'
)

result = paypal.payment_button(
    name: str,                # Button text
    amount: float,            # Payment amount
    currency: str,            # Currency code (USD, EUR, TWD, etc.)
    description: str,         # Order description
    return_url: str           # Post-payment return URL (required)
)
```

### Return Value

On successful payment, returns a dictionary:

```python
{
    'order_id': 'xxx',        # PayPal Order ID
    'status': 'COMPLETED',    # Order status
    'payer_email': 'xxx',     # Payer's email
    'amount': '10.00',        # Payment amount
    'currency': 'USD'         # Currency code
}
```

## 🔒 Security Features

| Feature | Description |
|---------|-------------|
| Client Secret Protection | ✅ Secret stays server-side, zero frontend exposure |
| CSRF Protection | ✅ Order ID verification mechanism |
| Timeout Control | ✅ 5-minute auto-cancellation |
| Order Verification | ✅ Can only capture self-created orders |
| Replay Attack Protection | ✅ Order state tracking |

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/TEENLU/streamlit-paypal.git
cd streamlit-paypal

# Install in development mode
pip install -e .

# Run example
streamlit run examples/paypal_basic.py
```

### Frontend Development

```bash
cd streamlit_paypal/frontend
npm install
npm run dev
```

### Testing

```bash
python test_paypal_component.py
```

## 📊 Architecture Design

### Why Popup Mode?

1. **Simpler URL Handling**: Returns Python dict directly, no callback URL parsing needed
2. **Better UX**: Dedicated window feels more professional, doesn't interrupt main app flow
3. **State Management**: Auto-integrates with Streamlit session state
4. **Enhanced Security**: Reduces URL parameter exposure risks

### Production Architecture

This package provides the **frontend interaction layer** for immediate payment experiences.

**Recommended production setup**:

```
Streamlit App (this package)  →  Real-time UI, payment buttons, user experience
         ↓
PayPal Orders API             →  Create orders, popup payment flow
         ↓
Your Backend + Webhooks       →  Receive PAYMENT.CAPTURE.COMPLETED
                                  Persist orders, fulfillment, authorization
```

**Why use Webhooks?**
- ✅ Reliability: Process payments even if user closes browser
- ✅ Security: Server-to-Server verification
- ✅ Completeness: Receive all payment events (success, failure, refund, etc.)

Reference: [PayPal Webhooks Documentation](https://developer.paypal.com/docs/api-basics/notifications/webhooks/)

## 🙏 Acknowledgments

This project is forked from [dnplus/streamlit-oauth](https://github.com/dnplus/streamlit-oauth). Special thanks to the original author for the excellent popup mechanism architecture.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

**Version:** 1.0.0
**Status:** 🟢 Active Development
