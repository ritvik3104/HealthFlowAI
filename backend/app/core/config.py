import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """
    # API Version
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # JWT Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # Groq API Key
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # Mailgun API Key
    MAILGUN_API_KEY: Optional[str] = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN: Optional[str] = os.getenv("MAILGUN_DOMAIN")
    FROM_EMAIL: Optional[str] = os.getenv("FROM_EMAIL")


    class Config:
        # This tells Pydantic to look for a .env file
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create a single instance of the settings to be used throughout the application
settings = Settings()
