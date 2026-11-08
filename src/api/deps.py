import re
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

# Identity-provider user ids: Zitadel uses numeric strings, older GoTrue
# deployments used UUIDs. Restrict to a safe charset since ids end up in
# object keys and GraphQL variables.
_USER_ID = re.compile(r"^[A-Za-z0-9_.@-]{1,128}$")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Return the authenticated user's id from the gateway-issued token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated"
        )
        user_id: Optional[str] = payload.get("sub")
        if not user_id or not _USER_ID.match(str(user_id)):
            raise UnauthorizedError("Could not validate credentials")
        return str(user_id)
    except (JWTError, ValueError, TypeError):
        raise UnauthorizedError("Could not validate credentials")


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state"""
    return getattr(request.state, "request_id", None)
