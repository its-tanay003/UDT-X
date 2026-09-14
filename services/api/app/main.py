"""UDT-X Core API Service with Authentication, Rate Limiting, and CORS."""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from services.api.app.limiter import limiter, udtx_rate_limit_exceeded_handler
from services.api.app.routers.auth import router as auth_router
from services.api.app.routers.settings import router as settings_router
from services.api.app.routers.soc import router as soc_router
from services.api.app.routers.copilot import router as copilot_router
from services.api.app.routers.privacy import router as privacy_router

app = FastAPI(
    title="UDT-X Core API",
    version="1.0.0",
    description="Unified Defense & Telemetry Platform (UDT-X) SOC & Anomaly API",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, udtx_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS explicit origin configuration with regex fallback for local ports
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(soc_router)
app.include_router(copilot_router)
app.include_router(privacy_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "udtx-api", "version": "1.0.0"}
