import os
import pytest

# Mock environment variables for Pydantic Settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["ENVIRONMENT"] = "testing"
