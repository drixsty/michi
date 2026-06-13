from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Michi MCP Server"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # GraphQL
    CORS_ORIGINS: str = "*"
    
    # Security (Must match main API)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Michi API Endpoint
    MICHI_API_URL: str = os.getenv("MICHI_API_URL", "http://localhost:8000/graphql")
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
