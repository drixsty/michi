import os

# Mock environment variables for Pydantic Settings
# This ensures core tests can run without a .env file (Hexagonal logic)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["ENVIRONMENT"] = "testing"

# SMTP
os.environ["SMTP_HOST"] = "localhost"
os.environ["SMTP_PORT"] = "1025"
os.environ["SMTP_USER"] = "test"
os.environ["SMTP_PASSWORD"] = "test"
os.environ["EMAIL_FROM"] = "test@michi.io"

# Shopify
os.environ["SHOPIFY_API_KEY"] = "test_key"
os.environ["SHOPIFY_API_SECRET"] = "test_secret"
os.environ["SHOPIFY_REDIRECT_URI"] = "http://localhost/callback"
os.environ["SHOPIFY_SCOPES"] = "read_products"

# Stripe
os.environ["STRIPE_API_KEY"] = "sk_test_core"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
os.environ["BILLING_MODE"] = "MOCK"
os.environ["STRIPE_PRICE_BASIC"] = "price_1"
os.environ["STRIPE_PRICE_PRO"] = "price_2"
os.environ["STRIPE_PRICE_ENTERPRISE"] = "price_3"
