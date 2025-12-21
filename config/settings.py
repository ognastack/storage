from pydantic import field_validator
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Ogna Storage"
    PROJECT_DESCRIPTION: str = "Ogna Stack Storage Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # API settings
    API_V1_STR: str = "/v1"

    # Security
    SECRET_KEY: str = 'superlongjwtsecret'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # S3 CONFIG
    STORAGE_TYPE: str = "S3"
    S3_ACCESS_KEY: str = ''
    S3_ENDPOINT_URL: str = ''
    S3_SECRET_KEY: str = ''

    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://yourdomain.com",
    ]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()
