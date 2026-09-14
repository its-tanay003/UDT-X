"""Rate limiting configuration for UDT-X API services."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def rate_limit_key_func(request: Request) -> str:
    # Key by user token subject if present in Authorization header, else remote IP
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key_func, default_limits=["100/minute"])


def udtx_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Build a standard 429 response with Retry-After header."""
    return JSONResponse(
        {"error": f"Rate limit exceeded: {exc.detail}"},
        status_code=429,
        headers={"Retry-After": "60"},
    )
