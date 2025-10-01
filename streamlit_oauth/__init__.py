import os
import streamlit.components.v1 as components
import asyncio
import streamlit as st
import base64
import time
import uuid
import hashlib
import secrets
import requests
from typing import Optional, Dict, Any

# OAuth2 dependencies (for original OAuth2Component)
try:
    from httpx_oauth.oauth2 import OAuth2, OAuth2ClientAuthMethod
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False
    OAuth2 = None
    OAuth2ClientAuthMethod = None

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


class StreamlitOauthError(Exception):
  """
  Exception raised from streamlit-oauth.
  """

class PayPalError(Exception):
  """
  Exception raised from PayPal operations.
  """

def _generate_state(key=None):
  """
  persist state for 300 seconds (5 minutes) to keep component state hash the same
  """
  state_key = f"state-{key}"
  
  if not st.session_state.get(state_key):
    st.session_state[state_key] = uuid.uuid4().hex
  return st.session_state[state_key]

def _generate_pkce_pair(pkce, key=None):
  """
  generate code_verifier and code_challenge for PKCE
  """
  pkce_key = f"pkce-{key}"

  if pkce != "S256":
    raise Exception("Only S256 is supported")
  if not st.session_state.get(pkce_key):
    code_verifier = secrets.token_urlsafe(96)
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().replace("=", "")
    st.session_state[pkce_key] = (code_verifier, code_challenge)
  return st.session_state[pkce_key]

class OAuth2Component:
  def __init__(self, client_id=None, client_secret=None, authroize_endpoint=None, token_endpoint=None, refresh_token_endpoint=None, revoke_token_endpoint=None, client=None, *, authorize_endpoint=None, token_endpoint_auth_method: OAuth2ClientAuthMethod = "client_secret_basic", revocation_endpoint_auth_method: OAuth2ClientAuthMethod = "client_secret_basic"):
    # Handle typo in backwards-compatible way
    authorize_endpoint = authorize_endpoint or authroize_endpoint
    if client:
      self.client = client
    else:
      self.client = OAuth2(
        client_id,
        client_secret,
        authorize_endpoint,
        token_endpoint,
        refresh_token_endpoint=refresh_token_endpoint,
        revoke_token_endpoint=revoke_token_endpoint,
        token_endpoint_auth_method=token_endpoint_auth_method,
        revocation_endpoint_auth_method=revocation_endpoint_auth_method,
      )

  def authorize_button(self, name, redirect_uri, scope, height=800, width=600, key=None, pkce=None, extras_params={}, icon=None, use_container_width=False, auto_click=False):
    # generate state based on key
    state = _generate_state(key)
    if pkce:
      code_verifier, code_challenge = _generate_pkce_pair(pkce, key)
      extras_params = {**extras_params, "code_challenge": code_challenge, "code_challenge_method": pkce}

    authorize_request = asyncio.run(self.client.get_authorization_url(
      redirect_uri=redirect_uri,
      scope=scope.split(" "),
      state=state,
      extras_params=extras_params
    ))

    # print(f'generated authorize request: {authorize_request}')

    result = _authorize_button(
      authorization_url=authorize_request,
      name=name, 
      popup_height=height,
      popup_width=width,
      key=key,
      icon=icon,
      use_container_width=use_container_width,
      auto_click=auto_click,
    )
    # print(f'result: {result}')

    if result:
      try:
        del st.session_state[f'state-{key}']
        del st.session_state[f'pkce-{key}'] 
      except:
        pass
      if 'error' in result:
        raise StreamlitOauthError(result)
      if 'state' in result and result['state'] != state:
        raise StreamlitOauthError(f"STATE {state} DOES NOT MATCH OR OUT OF DATE")
      if 'code' in result:
        args = {
          'code': result['code'],
          'redirect_uri': redirect_uri,
        }
        if pkce:
          args['code_verifier'] = code_verifier
        
        result['token'] = asyncio.run(self.client.get_access_token(**args))
      if 'id_token' in result:
        # TODO: verify id_token
        result['id_token'] = base64.b64decode(result['id_token'].split('.')[1] + '==')

    return result
  
  def refresh_token(self, token, force=False):
    """
    Returns a refreshed token if the token is expired, otherwise returns the same token
    """
    if force or token.get('expires_at') and token['expires_at'] < time.time():
      if token.get('refresh_token') is None:
        raise Exception("Token is expired and no refresh token is available")
      else:
        new_token = asyncio.run(self.client.refresh_token(token.get('refresh_token')))
        # Keep the old refresh token if the new one is missing it
        if not new_token.get('refresh_token'):
          new_token['refresh_token'] = token.get('refresh_token')
        token = new_token
    return token
  
  def revoke_token(self, token, token_type_hint="access_token"):
    """
    Revokes the token
    """
    if token_type_hint == "access_token":
      token = token['access_token']
    elif token_type_hint == "refresh_token":
      token = token['refresh_token']
    try:
      asyncio.run(self.client.revoke_token(token, token_type_hint))
    except:
      # discard exception if revoke fails
      pass
    return True


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

  def _create_order(self, amount: float, currency: str, description: str, return_url: str = None, cancel_url: str = None) -> Dict[str, Any]:
    """
    Create PayPal order on backend (secure).

    Args:
      amount: Payment amount
      currency: Currency code (e.g., 'USD', 'TWD')
      description: Payment description
      return_url: URL to redirect after approval (optional, uses approval URL if not set)
      cancel_url: URL to redirect on cancellation (optional)

    Returns:
      Order object with 'id' field
    """
    access_token = self._get_access_token()

    # Build order request
    order_request = {
      'intent': 'CAPTURE',
      'purchase_units': [{
        'amount': {
          'currency_code': currency,
          'value': f'{amount:.2f}'
        },
        'description': description
      }]
    }

    # Add payment source with return/cancel URLs if provided
    if return_url or cancel_url:
      order_request['payment_source'] = {
        'paypal': {
          'experience_context': {}
        }
      }
      if return_url:
        order_request['payment_source']['paypal']['experience_context']['return_url'] = return_url
      if cancel_url:
        order_request['payment_source']['paypal']['experience_context']['cancel_url'] = cancel_url

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
    redirect_uri: str = None,
    description: str = '',
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
      redirect_uri: Redirect URI after payment (must match PayPal app settings)
      description: Payment description
      key: Unique key for this button
      icon: Button icon (data URI or URL)
      use_container_width: Expand button to container width
      popup_height: Popup window height
      popup_width: Popup window width

    Returns:
      Payment result dict if successful, None if pending
    """
    # Create order on backend (secure)
    # Note: redirect_uri is optional for PayPal (unlike OAuth)
    # If not provided, PayPal uses the approval URL from order response
    order = self._create_order(
      amount=amount,
      currency=currency,
      description=description,
      return_url=redirect_uri,
      cancel_url=redirect_uri
    )

    # Get approval URL from order links
    approval_url = None
    for link in order.get('links', []):
      if link.get('rel') == 'approve':
        approval_url = link.get('href')
        break

    if not approval_url:
      raise PayPalError("No approval URL in order response")

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
        if 'error' in result:
          raise PayPalError(result)

        # PayPal returns 'token' (order ID) in callback
        if 'token' in result:
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


if not _RELEASE:
    import streamlit as st
    from dotenv import load_dotenv
    load_dotenv()
    AUTHORIZATION_URL = os.environ.get("AUTHORIZATION_URL")
    TOKEN_URL = os.environ.get("TOKEN_URL")
    REVOKE_URL = os.environ.get("REVOKE_URL")
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    REDIRECT_URI = os.environ.get("REDIRECT_URI")
    SCOPE = os.environ.get("SCOPE")
   
    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)
    if 'token' not in st.session_state:
      result = oauth2.authorize_button("Continue with Google", REDIRECT_URI, SCOPE, icon="data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' viewBox='0 0 48 48'%3E%3Cdefs%3E%3Cpath id='a' d='M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z'/%3E%3C/defs%3E%3CclipPath id='b'%3E%3Cuse xlink:href='%23a' overflow='visible'/%3E%3C/clipPath%3E%3Cpath clip-path='url(%23b)' fill='%23FBBC05' d='M0 37V11l17 13z'/%3E%3Cpath clip-path='url(%23b)' fill='%23EA4335' d='M0 11l17 13 7-6.1L48 14V0H0z'/%3E%3Cpath clip-path='url(%23b)' fill='%2334A853' d='M0 37l30-23 7.9 1L48 0v48H0z'/%3E%3Cpath clip-path='url(%23b)' fill='%234285F4' d='M48 48L17 24l-4-3 35-10z'/%3E%3C/svg%3E", use_container_width=True, pkce="S256", extras_params={"prompt": "consent", "access_type": "offline"})
      if result:
        st.session_state.token = result.get('token')
        st.rerun()
    else:
      token = st.session_state['token']
      st.json(token)
      if st.button("♻️ Refresh Token"):
        token = oauth2.refresh_token(token, force=True)
        st.session_state.token = token
        st.json(token)
        st.rerun()
      if st.button("🗑 Revoke Token"):
        oauth2.revoke_token(token)
        del st.session_state.token
        st.rerun()
    
