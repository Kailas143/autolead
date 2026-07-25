from typing import List, Optional, Union, Any
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Aurvyz Outreach Automation"
    API_V1_STR: str = "/api/v1"

    # Server
    SERVER_NAME: str = "Aurvyz"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    SERVER_PORT: int = 8000

    # CORS
    BACKEND_CORS_ORIGINS: Any = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    return [v]
            return v
        return ["*"]

    # Database
    # These will be fetched from .env if present, otherwise use these defaults
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "autolead_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        
        # Fallback to individual components if DATABASE_URL is not provided
        user = info.data.get('POSTGRES_USER')
        password = info.data.get('POSTGRES_PASSWORD')
        server = info.data.get('POSTGRES_SERVER')
        port = info.data.get('POSTGRES_PORT')
        db = info.data.get('POSTGRES_DB')
        
        return f"postgresql+psycopg://{user}:{password}@{server}:{port}/{db}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        return f"redis://{info.data.get('REDIS_HOST')}:{info.data.get('REDIS_PORT')}/0"


    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Email
    EMAIL_SERVICE_MODE: str = "production"  # Set to "test" to skip Resend API calls
    RESEND_API_KEY: str = ""
    # Postmark (Uncommented as per request)
    POSTMARK_API_KEY: str = ""
    POSTMARK_SENDER: str = "hello@aurvyz.com"
    EMAIL_FROM: str = "hello@aurvyz.com"
    EMAIL_FROM_NAME: str = "Aurvyz"
    # Mailtrap
    MAILTRAP_API_TOKEN: str = ""

    # Zoho SMTP
    ZOHO_SMTP_HOST: str = "smtp.zoho.com"
    ZOHO_SMTP_PORT: int = 465
    ZOHO_SMTP_USER: str = ""
    ZOHO_SMTP_PASSWORD: str = ""

    APP_TIMEZONE: str = "Asia/Kolkata"

    # WhatsApp Evolution API
    EVOLUTION_API_URL: str = "http://evolution-api:8080"
    EVOLUTION_API_KEY: str = "supersecretkey"

    # AI
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # Internal Task Secret
    CRON_SECRET: str = "super-secret-cron-key"

    # Extra settings from .env
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    RATE_LIMIT: str = "100/minute"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
