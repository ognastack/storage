import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from config.settings import settings
from src.core.exceptions import UnauthorizedError
import logging

# Security scheme
security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
    """Get current authenticated user"""
    try:

        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience="authenticated"
        )
        logger.info(payload)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Could not validate credentials")
    except JWTError:
        raise UnauthorizedError("Could not validate credentials")

    return uuid.UUID(user_id)


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state"""
    return getattr(request.state, "request_id", None)
