import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Database - no default, must be set in .env
    DATABASE_URL: str
    
    # Security - no default, must be set in .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    UNVERIFIED_USER_CLEANUP_HOURS: int = 48

    # Celery / Redis
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Email - no defaults for sensitive fields
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
