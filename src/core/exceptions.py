from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """Base exception for API errors"""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Validation error exception"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class NotFoundError(BaseAPIException):
    """Not found error exception"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(BaseAPIException):
    """Unauthorized error exception"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(BaseAPIException):
    """Forbidden error exception"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ConflictError(BaseAPIException):
    """Conflict error exception"""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class InternalServerError(BaseAPIException):
    """Internal server error exception"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


class BucketNotFound(BaseAPIException):
    """Bucket not found exception"""

    def __init__(self, bucket_name: str):
        super().__init__(f"Bucket {bucket_name} not found", status_code=404)
