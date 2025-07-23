import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/v1/api"
    PROJECT_NAME: str = "GET INN Restaurant Platform API"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/restaurant")
    DATABASE_SCHEMA: str = os.getenv("DATABASE_SCHEMA", "getinn_ops")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
    
    # Storage settings
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "documents")
    MEDIA_STORAGE_PATH: str = os.getenv("MEDIA_STORAGE_PATH", "/tmp/getinn/media")
    
    # External system integration settings
    INTEGRATIONS_ENABLED: bool = os.getenv("INTEGRATIONS_ENABLED", "False").lower() == "true"
    DEFAULT_TOKEN_REFRESH_INTERVAL: int = int(os.getenv("DEFAULT_TOKEN_REFRESH_INTERVAL", "3600"))  # seconds
    CREDENTIAL_ENCRYPTION_KEY: str = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")
    CREDENTIAL_ENCRYPTION_NONCE: str = os.getenv("CREDENTIAL_ENCRYPTION_NONCE", "")
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    AZURE_OPENAI_GPT41_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_GPT41_DEPLOYMENT", "gpt-41")
    AZURE_OPENAI_ENABLED: bool = os.getenv("AZURE_OPENAI_ENABLED", "False").lower() == "true"
    AZURE_OPENAI_MAX_TOKENS: int = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4000"))
    AZURE_OPENAI_TEMPERATURE: float = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.1"))
    
    # Bot management settings
    BOT_WEBHOOK_BASE_URL: str = os.getenv("BOT_WEBHOOK_BASE_URL", "")
    
    # Webhook settings
    USE_NGROK: bool = os.getenv("USE_NGROK", "false").lower() == "true"
    NGROK_AUTHTOKEN: Optional[str] = os.getenv("NGROK_AUTHTOKEN", None)
    NGROK_PORT: int = int(os.getenv("NGROK_PORT", "8000"))
    WEBHOOK_DOMAIN: str = os.getenv("WEBHOOK_DOMAIN", "https://api.getinn.ai")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()