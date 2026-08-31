"""UDT-X Behavioral Baseline Client Library.

Provides detection engines (Phase 5) and external modules with a clean Python API
to retrieve the historical baseline of any host IP.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from baseline.models import BaselineProfile

logger = logging.getLogger("udtx.baseline.client")

_GLOBAL_REDIS_CLIENT: Any | None = None
_REDIS_INITIALIZED = False


def _get_redis() -> Any | None:
    global _GLOBAL_REDIS_CLIENT, _REDIS_INITIALIZED
    if _REDIS_INITIALIZED:
        return _GLOBAL_REDIS_CLIENT

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis  # type: ignore

        _GLOBAL_REDIS_CLIENT = redis.Redis.from_url(redis_url, decode_responses=True)
        _GLOBAL_REDIS_CLIENT.ping()
        logger.info("Connected baseline client to Redis at %s", redis_url)
    except Exception as exc:
        logger.debug(
            "Redis unavailable for baseline client fallback to default: %s",
            exc,
        )
        _GLOBAL_REDIS_CLIENT = None

    _REDIS_INITIALIZED = True
    return _GLOBAL_REDIS_CLIENT


def get_baseline(
    host_ip: str,
    redis_client: Any | None = None,
) -> BaselineProfile:
    """Retrieve the behavioral BaselineProfile for a host.

    Args:
        host_ip: Target host IPv4 or IPv6 address string.
        redis_client: Optional explicit redis client instance.

    Returns:
        BaselineProfile: The stored or empty profile for the host.
    """
    client = redis_client if redis_client is not None else _get_redis()
    if client is not None:
        try:
            raw = client.get(f"udtx:baseline:{host_ip}")
            if raw:
                data = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
                return BaselineProfile.model_validate(data)
        except Exception as exc:
            logger.warning(
                "Error fetching baseline from Redis: %s",
                exc,
            )

    return BaselineProfile(host_ip=host_ip)
