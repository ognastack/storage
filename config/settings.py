from pydantic import field_validator, model_validator
from typing import List, Optional
from pydantic_settings import BaseSettings

DEFAULT_INSECURE_JWT_SECRET = "superlongjwtsecret"


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Ogna Storage"
    PROJECT_DESCRIPTION: str = "Ogna Stack Storage Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # API settings
    API_V1_STR: str = "/v1"

    # Security & Upload limits
    # Secret of the short-lived HS256 token the OGNA gateway forwards after checking
    # the caller with the identity provider (Zitadel). GOTRUE_JWT_SECRET is still read
    # for older deployments that set only that name.
    OGNA_INTERNAL_JWT_SECRET: str = ""
    GOTRUE_JWT_SECRET: str = DEFAULT_INSECURE_JWT_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    MAX_UPLOAD_SIZE_MB: int = 50
    GRAPHQL_TIMEOUT_SECONDS: int = 10

    # S3 CONFIG
    STORAGE_TYPE: str = "S3"
    S3_ACCESS_KEY: str = ''
    S3_ENDPOINT_URL: str = ''
    S3_SECRET_KEY: str = ''
    S3_REGION: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_DEFAULT_REGION: Optional[str] = None

    # Database
    DATABASE_URL: str = ''
    DATABASE_PORT: str = ''
    DATABASE_USERNAME: str = ''
    DATABASE_PASSWORD: str = ''
    DATABASE_NAME: str = ''

    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://yourdomain.com",
    ]

    GRAPHQL_HOST: str = 'http://hasura:8080'
    GRAPHQL_ENDPOINT: str = '/v1/graphql'
    GRAPHQL_SECRET: str = '/v1/graphql'


    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def JWT_SECRET(self) -> str:
        return self.OGNA_INTERNAL_JWT_SECRET or self.GOTRUE_JWT_SECRET

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() != "development":
            if not self.JWT_SECRET or self.JWT_SECRET == DEFAULT_INSECURE_JWT_SECRET:
                raise ValueError(
                    "OGNA_INTERNAL_JWT_SECRET must be set to a strong secret in non-development environments"
                )
        return self

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()
