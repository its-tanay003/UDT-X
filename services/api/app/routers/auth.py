"""UDT-X Authentication & User Store Router.

Admin-provisioned accounts, password hashing, JWT creation/refresh,
and user profile & settings endpoints.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])

# Security & Crypto Config
SECRET_KEY = os.getenv("JWT_SECRET", "udtx-super-secret-enclave-key-2026-sigint-defense")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


# --- In-Memory Fast Store with Database Synchronization Fallback ---
class UserRecord(BaseModel):
    id: str
    email: str
    password_hash: str
    display_name: str
    role: str = "analyst"  # 'analyst' | 'admin'
    avatar_seed: str = "enclave-operator"
    created_at: str
    last_login_at: Optional[str] = None
    has_completed_tour: bool = False


# Initial Seed Users
INITIAL_USERS: dict[str, UserRecord] = {
    "admin@udtx.local": UserRecord(
        id="a0000000-0000-0000-0000-000000000001",
        email="admin@udtx.local",
        password_hash=pwd_context.hash("AdminEnclave2026!"),
        display_name="Station Commander",
        role="admin",
        avatar_seed="commander",
        created_at=datetime.now(timezone.utc).isoformat(),
        has_completed_tour=False,
    ),
    "analyst@udtx.local": UserRecord(
        id="a0000000-0000-0000-0000-000000000002",
        email="analyst@udtx.local",
        password_hash=pwd_context.hash("AnalystEnclave2026!"),
        display_name="Tier-1 Radar Lead",
        role="analyst",
        avatar_seed="radar-lead",
        created_at=datetime.now(timezone.utc).isoformat(),
        has_completed_tour=False,
    ),
}

# User Settings Store
USER_SETTINGS: dict[str, dict[str, Any]] = {
    "a0000000-0000-0000-0000-000000000001": {
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
    "a0000000-0000-0000-0000-000000000002": {
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
}


# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class ProvisionUserRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str
    role: str = "analyst"


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    has_completed_tour: Optional[bool] = None


# --- Helper Methods ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


# --- Dependency Injection for Protected Routes ---
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> UserRecord:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Enclave station token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_jwt_token(token)
    email: Optional[str] = payload.get("sub")
    if not email or email not in INITIAL_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity unrecognized or station decommissioned",
        )
    return INITIAL_USERS[email]


async def require_admin(
    current_user: UserRecord = Depends(get_current_user),
) -> UserRecord:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Station Commander / Admin role required for this operation",
        )
    return current_user


# --- Public & Authenticated Endpoints ---
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response) -> TokenResponse:
    user = INITIAL_USERS.get(req.email.lower())
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid enclave credentials. Access denied.",
        )

    user.last_login_at = datetime.now(timezone.utc).isoformat()

    access_token = create_jwt_token(
        data={"sub": user.email, "role": user.role, "uid": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_jwt_token(
        data={"sub": user.email, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Set secure http-only refresh cookie
    response.set_cookie(
        key="udtx_refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with TLS
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "avatar_seed": user.avatar_seed,
            "has_completed_tour": user.has_completed_tour,
            "last_login_at": user.last_login_at,
        },
    )


@router.post("/refresh", response_model=dict[str, str])
async def refresh_access_token(
    refresh_token: Optional[str] = Query(None),
) -> dict[str, str]:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )
    payload = decode_jwt_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token category",
        )
    email = payload.get("sub")
    if not email or email not in INITIAL_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user = INITIAL_USERS[email]
    new_access_token = create_jwt_token(
        data={"sub": user.email, "role": user.role, "uid": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("udtx_refresh_token")
    return {"status": "logged_out"}


@router.get("/me")
async def get_my_profile(
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "avatar_seed": current_user.avatar_seed,
        "has_completed_tour": current_user.has_completed_tour,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
    }


@router.patch("/me")
async def update_my_profile(
    req: UpdateProfileRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    if req.display_name:
        current_user.display_name = req.display_name
    if req.has_completed_tour is not None:
        current_user.has_completed_tour = req.has_completed_tour

    if req.new_password:
        if not req.current_password or not verify_password(
            req.current_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current station password incorrect",
            )
        current_user.password_hash = pwd_context.hash(req.new_password)

    if req.email and req.email.lower() != current_user.email:
        if not req.current_password or not verify_password(
            req.current_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password required to change station email address",
            )
        old_email = current_user.email
        current_user.email = req.email.lower()
        INITIAL_USERS[current_user.email] = current_user
        INITIAL_USERS.pop(old_email, None)

    return {"status": "updated", "user": current_user.model_dump(exclude={"password_hash"})}


@router.get("/users")
async def list_users(
    _admin: UserRecord = Depends(require_admin),
) -> list[dict[str, Any]]:
    return [u.model_dump(exclude={"password_hash"}) for u in INITIAL_USERS.values()]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def provision_analyst(
    req: ProvisionUserRequest,
    _admin: UserRecord = Depends(require_admin),
) -> dict[str, Any]:
    email_key = req.email.lower()
    if email_key in INITIAL_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Station account with this email already provisioned",
        )

    new_user = UserRecord(
        id=str(uuid4()),
        email=email_key,
        password_hash=pwd_context.hash(req.password),
        display_name=req.display_name,
        role=req.role if req.role in ["admin", "analyst"] else "analyst",
        avatar_seed=req.display_name.lower().replace(" ", "-"),
        created_at=datetime.now(timezone.utc).isoformat(),
        has_completed_tour=False,
    )
    INITIAL_USERS[email_key] = new_user

    # Initialize default settings
    USER_SETTINGS[new_user.id] = {
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
    }

    return {"status": "provisioned", "user": new_user.model_dump(exclude={"password_hash"})}
