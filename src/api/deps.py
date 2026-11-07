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
            settings.GOTRUE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated"
        )
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Could not validate credentials")
        return uuid.UUID(str(user_id))
    except (JWTError, ValueError, TypeError):
        raise UnauthorizedError("Could not validate credentials")


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state"""
    return getattr(request.state, "request_id", None)
