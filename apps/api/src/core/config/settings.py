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
    
    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    # Shopify OAuth
    SHOPIFY_API_KEY: str
    SHOPIFY_API_SECRET: str
    SHOPIFY_REDIRECT_URI: str
    SHOPIFY_SCOPES: str
    
    # Stripe
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    BILLING_MODE: str = "MOCK" # MOCK or STRIPE
    
    # Stripe Prices
    STRIPE_PRICE_BASIC: str
    STRIPE_PRICE_PRO: str
    STRIPE_PRICE_ENTERPRISE: str
    
    model_config = SettingsConfigDict(
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit CORS_ORIGINS en liste"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Instance globale
settings = Settings()
