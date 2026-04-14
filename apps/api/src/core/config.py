"""
Configuration centrale avec Pydantic Settings.
Les variables d'environnement sont chargées depuis .env
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Configuration de l'application Michi"""
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Mock Data
    USE_MOCK_SHOPIFY: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # SMTP (Sprint 10)
    SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = "your_user"
    SMTP_PASSWORD: str = "your_password"
    EMAIL_FROM: str = "notifications@michi-app.io"
    
    # Shopify OAuth (Sprint 15)
    SHOPIFY_API_KEY: str = "your_shopify_key"
    SHOPIFY_API_SECRET: str = "your_shopify_secret"
    SHOPIFY_REDIRECT_URI: str = "http://localhost:8000/api/shopify/callback"
    SHOPIFY_SCOPES: str = "read_products,read_orders,read_inventory"
    
    # Stripe (Sprint 17)
    STRIPE_API_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    BILLING_MODE: str = "MOCK" # MOCK or STRIPE
    
    # Stripe Prices (Placeholders for dev)
    STRIPE_PRICE_BASIC: str = "price_Basic123"
    STRIPE_PRICE_PRO: str = "price_Pro123"
    STRIPE_PRICE_ENTERPRISE: str = "price_Enterprise123"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit CORS_ORIGINS en liste"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Instance globale
settings = Settings()
