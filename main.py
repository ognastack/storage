from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from src.core.logging import setup_logging
from src.core.middleware import setup_middleware
from src.errors.handlers import setup_exception_handlers
from src.api.router import api_router
from src.database.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    create_db_and_tables()
    yield
    # Shutdown
    # Add any cleanup code here if needed
    pass


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
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

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )