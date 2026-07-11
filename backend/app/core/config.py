import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pronunciation Assessment AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkeychangeinproduction1234567890!@#"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # DB & Caching
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pronunciation_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    
    # S3 / R2 Configuration (Optional, fallback to local UPLOAD_DIR)
    S3_BUCKET: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None  # For Cloudflare R2
    
    # AI API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    # DPDP Compliance & Security Settings
    # 256-bit URL-safe base64-encoded key for AES encryption (Fernet)
    # Default is a generated one for development, but must be configured in production
    ENCRYPTION_KEY: str = "a1_B2-C3_D4-E5_F6-G7_H8-I9_J0-K1_L2-M3_N4="
    DATA_RESIDENCY_REGION: str = "ap-south-1"  # AWS Mumbai / Supabase India default
    AUDIO_RETENTION_SECONDS: int = 3600 * 24  # Delete audio files after 24 hours max (default: immediate after analyze, but clean up older leftover files if any)
    AUDIT_LOG_RETENTION_DAYS: int = 365
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if self.REDIS_URL.startswith("rediss://") and "ssl_cert_reqs" not in self.REDIS_URL:
            sep = "&" if "?" in self.REDIS_URL else "?"
            self.REDIS_URL += f"{sep}ssl_cert_reqs=none"

    @property
    def CELERY_REDIS_URL(self) -> str:
        url = self.REDIS_URL
        if url.startswith("rediss://"):
            if "ssl_cert_reqs=none" in url:
                return url.replace("ssl_cert_reqs=none", "ssl_cert_reqs=CERT_NONE")
            elif "ssl_cert_reqs" not in url:
                sep = "&" if "?" in url else "?"
                return url + f"{sep}ssl_cert_reqs=CERT_NONE"
        return url


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Configure NLTK data path to find pre-downloaded corpora in production/local builds
import nltk
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
nltk_data_dir = os.path.join(base_dir, "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

