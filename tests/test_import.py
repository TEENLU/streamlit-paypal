"""
Basic smoke tests for streamlit-paypal package.
"""
import pytest


def test_import_paypal_component():
    """Test that PayPalComponent can be imported."""
    from streamlit_paypal import PayPalComponent
    assert PayPalComponent is not None


def test_import_paypal_error():
    """Test that PayPalError can be imported."""
    from streamlit_paypal import PayPalError
    assert PayPalError is not None


def test_paypal_component_init():
    """Test that PayPalComponent can be initialized."""
    from streamlit_paypal import PayPalComponent

    paypal = PayPalComponent(
        client_id="test_id",
        client_secret="test_secret",
        mode="sandbox"
    )

    assert paypal.client_id == "test_id"
    assert paypal.client_secret == "test_secret"
    assert paypal.mode == "sandbox"
    assert paypal.api_base == "https://api-m.sandbox.paypal.com"


def test_paypal_component_invalid_mode():
    """Test that invalid mode raises ValueError."""
    from streamlit_paypal import PayPalComponent

    with pytest.raises(ValueError, match="mode must be"):
        PayPalComponent(
            client_id="test_id",
            client_secret="test_secret",
            mode="invalid"
        )
