"""
  This is the config module for the application.
  It is used to store the configuration of the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration for the Pydantic models.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jwt_secret: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RATE_LIMIT_PER_HOUR: int = 15

    # Brevo SMTP
    BREVO_SMTP_SERVER: str
    BREVO_SMTP_PORT: int
    BREVO_SMTP_USERNAME: str
    BREVO_SMTP_PASSWORD: str
    BREVO_SMTP_FROM: str

    # PostgreSQL Database
    DATABASE_URL: str

settings = Settings()