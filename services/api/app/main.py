"""UDT-X Core API Service with Authentication, Rate Limiting, and CORS."""

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from services.api.app.routers.auth import router as auth_router
from services.api.app.routers.settings import router as settings_router
from services.api.app.routers.soc import router as soc_router


# Rate Limiting configuration (Redis / Memory backed)
def rate_limit_key_func(request: Request) -> str:
    # Key by user token subject if present in Authorization header, else remote IP
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key_func, default_limits=["100/minute"])

app = FastAPI(
    title="UDT-X Core API",
    version="1.0.0",
    description="Unified Defense & Telemetry Platform (UDT-X) SOC & Anomaly API",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS explicit origin configuration
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://127.0.0.1:3001,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(soc_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "udtx-api", "version": "1.0.0"}
