"""
Quick test script for PayPalComponent

This script tests the basic PayPal component functionality without requiring
a full Streamlit app or real PayPal credentials.
"""

import sys
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# Mock streamlit session_state
if 'session_state' not in dir(st):
    st.session_state = {}

from streamlit_paypal import PayPalComponent, PayPalError

def test_component_initialization():
    """Test PayPalComponent initialization"""
    print("🧪 Test 1: Component Initialization")

    # Test sandbox mode
    paypal_sandbox = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='sandbox'
    )
    assert paypal_sandbox.mode == 'sandbox'
    assert paypal_sandbox.api_base == 'https://api-m.sandbox.paypal.com'
    assert paypal_sandbox.checkout_base == 'https://www.sandbox.paypal.com'
    print("  ✅ Sandbox mode initialized correctly")

    # Test production mode
    paypal_prod = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='production'
    )
    assert paypal_prod.mode == 'production'
    assert paypal_prod.api_base == 'https://api-m.paypal.com'
    assert paypal_prod.checkout_base == 'https://www.paypal.com'
    print("  ✅ Production mode initialized correctly")

    # Test invalid mode
    try:
        PayPalComponent(
            client_id='test_client_id',
            client_secret='test_client_secret',
            mode='invalid'
        )
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "mode must be 'sandbox' or 'production'" in str(e)
        print("  ✅ Invalid mode rejected correctly")

    print("✅ Test 1 passed\n")

def test_access_token():
    """Test access token retrieval"""
    print("🧪 Test 2: Access Token Retrieval")

    paypal = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='sandbox'
    )

    # Mock successful response
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {'access_token': 'test_token_123'}

    with patch('requests.post', return_value=mock_response) as mock_post:
        token = paypal._get_access_token()
        assert token == 'test_token_123'
        print("  ✅ Access token retrieved successfully")

        # Verify correct API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://api-m.sandbox.paypal.com/v1/oauth2/token'
        assert call_args[1]['auth'] == ('test_client_id', 'test_client_secret')
        print("  ✅ API called with correct credentials")

    print("✅ Test 2 passed\n")

def test_create_order():
    """Test order creation"""
    print("🧪 Test 3: Order Creation")

    paypal = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='sandbox'
    )

    # Mock access token
    with patch.object(paypal, '_get_access_token', return_value='test_token'):
        # Mock successful order creation
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'id': 'ORDER123',
            'status': 'CREATED',
            'links': [
                {'rel': 'approve', 'href': 'https://paypal.com/approve?token=ORDER123'}
            ]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            order = paypal._create_order(
                amount=10.50,
                currency='USD',
                description='Test payment',
                return_url='https://test.example.com'
            )

            assert order['id'] == 'ORDER123'
            assert 'ORDER123' in st.session_state.paypal_pending_orders
            print("  ✅ Order created successfully")
            print(f"  ✅ Order ID stored in session: ORDER123")

            # Verify API call
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
            json_data = call_args[1]['json']
            assert json_data['intent'] == 'CAPTURE'
            assert json_data['purchase_units'][0]['amount']['value'] == '10.50'
            assert json_data['purchase_units'][0]['amount']['currency_code'] == 'USD'
            print("  ✅ Order creation API called correctly")

    print("✅ Test 3 passed\n")

def test_capture_order_security():
    """Test order capture with security checks"""
    print("🧪 Test 4: Order Capture Security")

    paypal = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='sandbox'
    )

    # Test 4a: Unknown order ID (CSRF protection)
    try:
        paypal._capture_order('UNKNOWN_ORDER')
        assert False, "Should raise PayPalError"
    except PayPalError as e:
        assert 'CSRF' in str(e)
        print("  ✅ Unknown order ID rejected (CSRF protection)")

    # Test 4b: Expired order
    import time
    st.session_state.paypal_pending_orders = {
        'EXPIRED_ORDER': time.time() - 400  # 400 seconds ago (> 5 minutes)
    }

    try:
        paypal._capture_order('EXPIRED_ORDER')
        assert False, "Should raise PayPalError"
    except PayPalError as e:
        assert 'expired' in str(e).lower()
        print("  ✅ Expired order rejected (>5 minutes)")

    # Test 4c: Valid order capture
    st.session_state.paypal_pending_orders = {
        'VALID_ORDER': time.time()  # Current time
    }

    with patch.object(paypal, '_get_access_token', return_value='test_token'):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'id': 'VALID_ORDER',
            'status': 'COMPLETED',
            'payer': {'email_address': 'test@example.com'}
        }

        with patch('requests.post', return_value=mock_response):
            captured = paypal._capture_order('VALID_ORDER')
            assert captured['status'] == 'COMPLETED'
            assert 'VALID_ORDER' not in st.session_state.paypal_pending_orders
            print("  ✅ Valid order captured successfully")
            print("  ✅ Order removed from pending list after capture")

    print("✅ Test 4 passed\n")

def test_error_handling():
    """Test error handling"""
    print("🧪 Test 5: Error Handling")

    paypal = PayPalComponent(
        client_id='test_client_id',
        client_secret='test_client_secret',
        mode='sandbox'
    )

    # Test API failure
    import requests
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")

    with patch('requests.post', return_value=mock_response):
        try:
            paypal._get_access_token()
            assert False, "Should raise PayPalError"
        except PayPalError as e:
            assert 'Failed to get access token' in str(e)
            print("  ✅ API error handled correctly")

    print("✅ Test 5 passed\n")

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PayPalComponent Test Suite")
    print("=" * 60)
    print()

    try:
        test_component_initialization()
        test_access_token()
        test_create_order()
        test_capture_order_security()
        test_error_handling()

        print("=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Set up PayPal Sandbox credentials in .env file")
        print("2. Run: streamlit run examples/paypal_basic.py")
        print("3. Test with real PayPal Sandbox account")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
