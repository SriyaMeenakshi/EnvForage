"""
FastAPI application factory and lifespan management.
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import profiles, scripts, diagnose, troubleshoot, repair, verify
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Manage application startup and shutdown."""
    # Startup
    settings = get_settings()
    print(f"🚀 EnvForge API {settings.app_version} starting [{settings.environment}]")
    yield
    # Shutdown
    print("🛑 EnvForge API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-grade ML/AI environment provisioning platform. "
            "Generates setup scripts, diagnoses environments, and provides "
            "AI-assisted troubleshooting."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
    app.include_router(scripts.router, prefix="/api/v1", tags=["scripts"])
    app.include_router(diagnose.router, prefix="/api/v1", tags=["diagnose"])
    app.include_router(troubleshoot.router, prefix="/api/v1", tags=["ai"])
    app.include_router(repair.router, prefix="/api/v1", tags=["ai"])
    app.include_router(verify.router, prefix="/api/v1", tags=["verify"])

    # ── Health check ──────────────────────────────────────────
    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, Any]:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
