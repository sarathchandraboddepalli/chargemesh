"""
ChargeMesh — FastAPI Application Factory
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import engine
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # Startup
    print(f"[ChargeMesh] Starting up in {settings.ENVIRONMENT} mode")
    yield
    # Shutdown
    await engine.dispose()
    print("[ChargeMesh] Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ChargeMesh API",
        description="EV Infrastructure Operating System for India's commercial EV market",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS — origins are configured via CORS_ALLOWED_ORIGINS in settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}

    return app


app = create_app()
