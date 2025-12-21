from pydantic import BaseModel
from typing import List, Optional
import os

from pydantic.v1 import validator


class Settings(BaseModel):
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

    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://yourdomain.com",
    ]

    @validator("ALLOWED_HOSTS", pre=True)
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
