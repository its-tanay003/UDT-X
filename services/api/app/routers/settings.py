"""UDT-X User Settings & Station Config Router."""

import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.api.app.routers.auth import USER_SETTINGS, UserRecord, get_current_user, require_admin

router = APIRouter(prefix="/settings", tags=["Station & User Settings"])


class UserSettingsModel(BaseModel):
    alerting: dict[str, Any]
    display: dict[str, Any]
    data_export: dict[str, Any]


@router.get("", response_model=dict[str, Any])
async def get_settings(
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve personal settings for the authenticated analyst."""
    settings = USER_SETTINGS.get(
        current_user.id,
        {
            "alerting": {
                "sound_on_critical": True,
                "min_notification_severity": "high",
                "live_monitor_autoscroll": True,
            },
            "display": {
                "density": "comfortable",
                "sphere_particle_density": "high",
                "default_time_range": "24h",
            },
            "data_export": {"default_format": "CEF"},
        },
    )
    return settings


@router.put("", response_model=dict[str, Any])
async def update_settings(
    settings_data: UserSettingsModel,
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    """Persist updated analyst preferences."""
    USER_SETTINGS[current_user.id] = settings_data.model_dump()
    return {"status": "saved", "settings": USER_SETTINGS[current_user.id]}


@router.get("/station-config", response_model=dict[str, Any])
async def get_station_config(
    _admin: UserRecord = Depends(require_admin),
) -> dict[str, Any]:
    """Read-only operational station configuration (Admin only)."""
    return {
        "cors_origins": os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://127.0.0.1:3001,http://127.0.0.1:5173",
        ).split(","),
        "jwt_expiry_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        "rate_limiting_backend": "Redis (Baseline Cluster)",
        "enclave_mode": "PASSIVE_DATA_DIODE",
        "data_diode_direction": "INWARD_ONLY",
        "pipeline_version": "v1.0.0 PROD",
    }
