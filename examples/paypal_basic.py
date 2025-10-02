"""
Basic PayPal Payment Example

This example demonstrates how to integrate PayPal payments into a Streamlit app
using the streamlit-oauth PayPalComponent.

Setup:
1. Create a PayPal app at https://developer.paypal.com/dashboard/applications
2. Get your Sandbox credentials (Client ID & Secret)
3. Set environment variables or create a .env file:
   PAYPAL_CLIENT_ID=your_sandbox_client_id
   PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
   PAYPAL_REDIRECT_URI=https://your-app.streamlit.app/component/streamlit_oauth.authorize_button

Note: For production, use 'production' mode and Live credentials.
"""

import streamlit as st
from streamlit_oauth import PayPalComponent, PayPalError
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="PayPal Payment Demo", page_icon="💳")

st.title("💳 PayPal Payment Demo")
st.markdown("---")

# Get credentials from environment
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
# Redirect URI: Optional - where to redirect after payment
# If not set, PayPal uses the approval URL from order response
PAYPAL_REDIRECT_URI = os.getenv('PAYPAL_REDIRECT_URI', None)

if not all([PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET]):
    st.error("❌ Missing PayPal credentials. Please set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in your .env file.")
    st.info("""
    **Setup Instructions:**
    1. Go to https://developer.paypal.com/dashboard/applications
    2. Create a new app or use an existing one
    3. Copy your Sandbox Client ID and Secret
    4. Create a `.env` file with:
       ```
       PAYPAL_CLIENT_ID=your_client_id
       PAYPAL_CLIENT_SECRET=your_client_secret
       PAYPAL_REDIRECT_URI=https://your-domain/component/streamlit_oauth.authorize_button
       ```
    """)
    st.stop()

# Initialize PayPal component
paypal = PayPalComponent(
    client_id=PAYPAL_CLIENT_ID,
    client_secret=PAYPAL_CLIENT_SECRET,
    mode='sandbox'  # Use 'production' for live payments
)

st.success("✅ PayPal component initialized (Sandbox mode)")

# Payment form
st.subheader("🛒 Make a Payment")

col1, col2 = st.columns(2)
with col1:
    amount = st.number_input("Amount", min_value=1.0, max_value=10000.0, value=10.0, step=0.5)
with col2:
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "TWD", "JPY"], index=0)

description = st.text_input("Description", value="Test payment from Streamlit")

st.markdown("---")

# Payment flow
if 'payment' not in st.session_state:
    # Display previous cancellation message if exists
    if 'last_cancellation' in st.session_state:
        cancellation = st.session_state.last_cancellation
        reason_map = {
            'user_cancelled': 'You cancelled the payment on PayPal',
            'user_closed': 'Payment window was closed',
            'timeout': 'Payment timed out (exceeded 5 minutes)'
        }
        reason = reason_map.get(cancellation['reason'], 'Payment was not completed')
        st.warning(f"⚠️ {reason}")

        # Show retry button
        if st.button("🔄 Retry Payment", type="primary", key='retry_btn'):
            # Clear cancellation state before retry
            del st.session_state.last_cancellation
            st.rerun()
    else:
        st.info("👇 Click the button below to start the payment process")

    # Only show payment button if no pending cancellation message
    if 'last_cancellation' not in st.session_state:
        try:
            result = paypal.payment_button(
                name=f"Pay ${amount} {currency}",
                amount=amount,
                currency=currency,
                redirect_uri=PAYPAL_REDIRECT_URI,
                description=description,
                key='payment_btn',
                use_container_width=True
                # Note: icon parameter can cause path issues with emoji, omitted for now
            )

            if result:
                # Check for cancellation
                if result.get('cancelled'):
                    # Store cancellation in session state
                    st.session_state.last_cancellation = {
                        'order_id': result.get('order_id'),
                        'reason': result['reason'],
                        'timestamp': time.time(),
                        'amount': amount,
                        'currency': currency
                    }

                    # Optional: Track cancellation for analytics
                    if 'cancelled_payments' not in st.session_state:
                        st.session_state.cancelled_payments = []
                    st.session_state.cancelled_payments.append(st.session_state.last_cancellation)

                    # Rerun to show cancellation message
                    st.rerun()
                else:
                    # Successful payment
                    st.session_state.payment = result
                    st.rerun()

        except PayPalError as e:
            st.error(f"❌ Payment failed: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

else:
    # Payment successful
    payment = st.session_state.payment

    st.success("🎉 Payment Successful!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Order ID", payment['order_id'])
        st.metric("Status", payment['status'])

    with col2:
        if payment.get('payer'):
            payer = payment['payer']
            payer_name = payer.get('name', {})
            full_name = f"{payer_name.get('given_name', '')} {payer_name.get('surname', '')}".strip()
            st.metric("Payer", full_name or payer.get('email_address', 'N/A'))

        if payment.get('purchase_units'):
            amount_paid = payment['purchase_units'][0]['payments']['captures'][0]['amount']
            st.metric("Amount Paid", f"{amount_paid['value']} {amount_paid['currency_code']}")

    # Show full details
    with st.expander("📋 Full Payment Details"):
        st.json(payment)

    # Reset button
    if st.button("Make Another Payment", type="primary"):
        del st.session_state.payment
        st.rerun()

# Sidebar info
with st.sidebar:
    st.subheader("ℹ️ About")
    st.markdown("""
    This demo shows how to integrate PayPal payments into Streamlit apps.

    **Features:**
    - 🔒 Secure payment flow
    - 💳 Popup-based checkout
    - ✅ Order capture & verification
    - 🛡️ CSRF protection

    **Current Mode:** `sandbox`

    **Test Cards:** Use PayPal Sandbox test accounts from your developer dashboard.
    """)

    st.markdown("---")
    st.caption("Powered by streamlit-oauth")
