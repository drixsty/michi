import pytest
from core.config.settings import Settings

def test_sentry_settings_load():
    # Test that SENTRY_DSN is correctly parsed by our Pydantic settings
    test_settings = Settings(
        DATABASE_URL="sqlite://",
        SECRET_KEY="test_secret",
        SMTP_HOST="localhost",
        SMTP_PORT=25,
        SMTP_USER="user",
        SMTP_PASSWORD="password",
        EMAIL_FROM="test@test.com",
        SHOPIFY_API_KEY="api_key",
        SHOPIFY_API_SECRET="api_secret",
        SHOPIFY_REDIRECT_URI="http://localhost/callback",
        SHOPIFY_SCOPES="read_products",
        STRIPE_API_KEY="stripe_key",
        STRIPE_WEBHOOK_SECRET="stripe_webhook",
        STRIPE_PRICE_BASIC="price_1",
        STRIPE_PRICE_PRO="price_2",
        STRIPE_PRICE_ENTERPRISE="price_3",
        SENTRY_DSN="https://example_pubkey@o0.ingest.sentry.io/0"
    )
    assert test_settings.SENTRY_DSN == "https://example_pubkey@o0.ingest.sentry.io/0"

def test_sentry_default_empty():
    test_settings = Settings(
        DATABASE_URL="sqlite://",
        SECRET_KEY="test_secret",
        SMTP_HOST="localhost",
        SMTP_PORT=25,
        SMTP_USER="user",
        SMTP_PASSWORD="password",
        EMAIL_FROM="test@test.com",
        SHOPIFY_API_KEY="api_key",
        SHOPIFY_API_SECRET="api_secret",
        SHOPIFY_REDIRECT_URI="http://localhost/callback",
        SHOPIFY_SCOPES="read_products",
        STRIPE_API_KEY="stripe_key",
        STRIPE_WEBHOOK_SECRET="stripe_webhook",
        STRIPE_PRICE_BASIC="price_1",
        STRIPE_PRICE_PRO="price_2",
        STRIPE_PRICE_ENTERPRISE="price_3"
    )
    # Default SENTRY_DSN must be an empty string
    assert test_settings.SENTRY_DSN == ""
