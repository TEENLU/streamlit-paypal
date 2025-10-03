import os
import streamlit.components.v1 as components
import streamlit as st
import time
import requests
from typing import Optional, Dict, Any

_RELEASE = False
# comment out the following line to use the local dev server
# use streamlit run __init__.py --server.enableCORS=false to run the local dev server
_RELEASE = True

if not _RELEASE:
  _authorize_button = components.declare_component(
    "authorize_button",
    url="http://localhost:3000", # vite dev server port
  )
else:
  parent_dir = os.path.dirname(os.path.abspath(__file__))
  build_dir = os.path.join(parent_dir, "frontend/dist")
  _authorize_button = components.declare_component("authorize_button", path=build_dir)


class PayPalError(Exception):
  """
  Exception raised from PayPal operations.
  """

# ============================================================================
# PayPal Component
# ============================================================================

class PayPalComponent:
  """
  PayPal payment component for Streamlit.

  This component provides a secure way to integrate PayPal payments into Streamlit apps
  using a popup-based checkout flow.
  """

  def __init__(self, client_id: str, client_secret: str, mode: str = 'sandbox'):
    """
    Initialize PayPal component.

    Args:
      client_id: PayPal client ID (different for sandbox/production)
      client_secret: PayPal client secret (never exposed to frontend)
      mode: 'sandbox' or 'production'
    """
    self.client_id = client_id
    self.client_secret = client_secret

    if mode not in ['sandbox', 'production']:
      raise ValueError("mode must be 'sandbox' or 'production'")

    self.mode = mode

    # Set API endpoints based on mode
    if mode == 'sandbox':
      self.api_base = 'https://api-m.sandbox.paypal.com'
      self.checkout_base = 'https://www.sandbox.paypal.com'
    else:
      self.api_base = 'https://api-m.paypal.com'
      self.checkout_base = 'https://www.paypal.com'

    # Session state for order tracking (CSRF protection)
    if 'paypal_pending_orders' not in st.session_state:
      st.session_state.paypal_pending_orders = {}

  def _get_access_token(self) -> str:
    """
    Get OAuth 2.0 access token using client credentials.
    Client secret is only used here, never exposed to frontend.
    """
    try:
      response = requests.post(
        f'{self.api_base}/v1/oauth2/token',
        auth=(self.client_id, self.client_secret),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={'grant_type': 'client_credentials'}
      )
      response.raise_for_status()
      return response.json()['access_token']
    except requests.exceptions.RequestException as e:
      raise PayPalError(f"Failed to get access token: {str(e)}")

  def _create_order(self, amount: float, currency: str, description: str, return_url: str) -> Dict[str, Any]:
    """
    Create PayPal order on backend (secure).

    Args:
      amount: Payment amount
      currency: Currency code (e.g., 'USD', 'TWD')
      description: Payment description
      return_url: Return URL for PayPal redirect (required)
                  After payment, PayPal redirects to this URL with token & PayerID params.
                  For popup flow: frontend detects params and closes popup immediately.
                  Use your app's URL (e.g., https://yourapp.streamlit.app)

    Returns:
      Order object with 'id' field
    """
    if not return_url:
      raise PayPalError("return_url is required. Provide your app's URL (e.g., https://yourapp.streamlit.app)")

    access_token = self._get_access_token()

    # Note: PayPal requires return_url to redirect with payment params (token, PayerID)
    # For popup flow: frontend detects these params and closes popup immediately
    cancel_url = return_url  # Use same URL for cancel (distinguished by params)

    # Build order request with return URL for popup flow
    order_request = {
      'intent': 'CAPTURE',
      'purchase_units': [{
        'amount': {
          'currency_code': currency,
          'value': f'{amount:.2f}'
        },
        'description': description
      }],
      'payment_source': {
        'paypal': {
          'experience_context': {
            'return_url': return_url,
            'cancel_url': cancel_url
          }
        }
      }
    }

    try:
      response = requests.post(
        f'{self.api_base}/v2/checkout/orders',
        headers={
          'Content-Type': 'application/json',
          'Authorization': f'Bearer {access_token}'
        },
        json=order_request
      )
      response.raise_for_status()
      order = response.json()

      # Store order ID with timestamp for CSRF protection
      st.session_state.paypal_pending_orders[order['id']] = time.time()

      return order
    except requests.exceptions.RequestException as e:
      raise PayPalError(f"Failed to create order: {str(e)}")

  def _capture_order(self, order_id: str) -> Dict[str, Any]:
    """
    Capture (complete) a PayPal order after user approval.

    Args:
      order_id: The order ID returned from popup

    Returns:
      Captured order details
    """
    # Security: Verify this order was created by us
    if order_id not in st.session_state.paypal_pending_orders:
      raise PayPalError("Unknown order ID - possible CSRF attack")

    # Security: Check order expiration (5 minutes)
    order_timestamp = st.session_state.paypal_pending_orders[order_id]
    if time.time() - order_timestamp > 300:
      del st.session_state.paypal_pending_orders[order_id]
      raise PayPalError("Order expired (>5 minutes)")

    access_token = self._get_access_token()

    try:
      response = requests.post(
        f'{self.api_base}/v2/checkout/orders/{order_id}/capture',
        headers={
          'Content-Type': 'application/json',
          'Authorization': f'Bearer {access_token}'
        }
      )
      response.raise_for_status()
      captured = response.json()

      # Clean up pending order
      del st.session_state.paypal_pending_orders[order_id]

      return captured
    except requests.exceptions.RequestException as e:
      raise PayPalError(f"Failed to capture order: {str(e)}")

  def payment_button(
    self,
    name: str,
    amount: float,
    currency: str = 'USD',
    description: str = '',
    return_url: str = None,
    key: Optional[str] = None,
    icon: Optional[str] = None,
    use_container_width: bool = False,
    popup_height: int = 800,
    popup_width: int = 600
  ) -> Optional[Dict[str, Any]]:
    """
    Render PayPal payment button with popup checkout flow.

    Args:
      name: Button label
      amount: Payment amount
      currency: Currency code (default: 'USD')
      description: Payment description
      return_url: Return URL for PayPal redirect (required)
                  After payment, PayPal redirects to this URL with token & PayerID params.
                  For popup flow: frontend detects params and closes popup immediately.
                  Use your app's URL (e.g., https://yourapp.streamlit.app)
                  Note: Doesn't need to be a real endpoint - popup closes before redirect completes.
      key: Unique key for this button
      icon: Button icon (data URI or URL)
      use_container_width: Expand button to container width
      popup_height: Popup window height
      popup_width: Popup window width

    Returns:
      - Payment result dict if successful
      - Cancellation dict if cancelled: {'cancelled': True, 'reason': str, 'order_id': str}
        Reasons: 'user_cancelled' (cancelled on PayPal), 'user_closed' (closed popup), 'timeout' (>5min)
      - None if pending
    """
    if not return_url:
      raise PayPalError("return_url is required. Provide your app's URL (e.g., https://yourapp.streamlit.app)")
    # Create order on backend (secure)
    order = self._create_order(
      amount=amount,
      currency=currency,
      description=description,
      return_url=return_url
    )

    # Get approval URL from order links
    # PayPal uses 'payer-action' or 'approve' depending on the flow
    approval_url = None
    for link in order.get('links', []):
      if link.get('rel') in ['approve', 'payer-action']:
        approval_url = link.get('href')
        break

    if not approval_url:
      raise PayPalError(f"No approval URL in order response. Links: {order.get('links')}")

    # Call frontend component (only passes order ID, no secrets)
    result = _authorize_button(
      authorization_url=approval_url,
      name=name,
      popup_height=popup_height,
      popup_width=popup_width,
      key=key,
      icon=icon,
      use_container_width=use_container_width,
      auto_click=False
    )

    # Process result from popup
    if result:
      try:
        # Check for cancellation
        if result.get('cancelled'):
          # Clean up cancelled order
          order_id = result.get('token')
          if order_id and order_id in st.session_state.paypal_pending_orders:
            del st.session_state.paypal_pending_orders[order_id]

          # Return cancellation info
          return {
            'cancelled': True,
            'reason': result.get('reason', 'unknown'),
            'order_id': order_id
          }

        if 'error' in result:
          raise PayPalError(result)

        # PayPal returns 'token' (order ID) in callback
        if 'token' in result and 'PayerID' in result:
          order_id = result['token']

          # Capture the order on backend (secure)
          captured = self._capture_order(order_id)

          # Return complete payment info
          return {
            'order_id': order_id,
            'status': captured.get('status'),
            'payer': captured.get('payer'),
            'purchase_units': captured.get('purchase_units'),
            'captured': captured
          }
      except PayPalError:
        raise
      except Exception as e:
        raise PayPalError(f"Unexpected error: {str(e)}")

    return None


# Development mode removed - use examples/paypal_basic.py for testing
