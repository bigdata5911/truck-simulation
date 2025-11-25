"""
Configuration settings for DriverBuddy application
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENV: str = os.getenv("ENV", "development")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "driverbuddy")
    DB_USER: str = os.getenv("DB_USER", "admin")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
    
    # SQS Queues
    SQS_EVENTS_QUEUE: str = os.getenv("SQS_EVENTS_QUEUE", "driverbuddy-events-queue")
    SQS_SMS_QUEUE: str = os.getenv("SQS_SMS_QUEUE", "driverbuddy-sms-queue")
    
    # Twilio (from environment variables)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_NUMBER: str = os.getenv("TWILIO_NUMBER", "")
    
    # Slack (from environment variables)
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Change in production
    
    # Vehicle state detection
    STOP_SPEED_THRESHOLD: float = 0.5  # km/h - vehicle is stopped if speed < this
    STOP_DURATION_SECONDS: int = 30  # minimum seconds to consider a stop
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

