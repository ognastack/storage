from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from src.core.logging import setup_logging
from src.core.middleware import setup_middleware
from src.errors.handlers import setup_exception_handlers
from src.api.router import api_router
from src.schema.response.storage import HealthResponse

OPENAPI_TAGS = [
    {
        "name": "buckets",
        "description": "Manage storage buckets and files (upload, replace, list, download, and delete) across S3 or Local storage backends."
    },
    {
        "name": "health",
        "description": "Health, liveness, and readiness probes for monitoring."
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    yield
    # Shutdown
    # Add any cleanup code here if needed
    pass


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_tags=OPENAPI_TAGS,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup custom middleware
    setup_middleware(app)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    app.include_router(api_router)

    @app.get(
        "/health",
        tags=["health"],
        response_model=HealthResponse,
        summary="Root health check",
        description="Returns service health status, version, and active environment."
    )
    async def root_health():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )