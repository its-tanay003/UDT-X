"""UDT-X Core API Service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.api.app.routers.soc import router as soc_router

app = FastAPI(
    title="UDT-X Core API",
    version="1.0.0",
    description="Unified Defense & Telemetry Platform (UDT-X) SOC & Anomaly API",
)

# Enable CORS for Dashboard Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include SOC & Alerts Endpoints
app.include_router(soc_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Service health status.
    """
    return {"status": "ok"}
