import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import BaseAPIException

logger = logging.getLogger(__name__)


async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handler for base API exceptions"""
    logger.error(
        f"API Exception: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "status_code": exc.status_code,
            "details": exc.details,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for validation errors"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "errors": exc.errors(),
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "details": {"validation_errors": exc.errors()},
            "request_id": getattr(request.state, "request_id", None),
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.detail}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "status_code": exc.status_code,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handler for unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers"""
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)