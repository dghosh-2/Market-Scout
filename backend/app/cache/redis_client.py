"""Async Redis client singleton (Upstash-compatible)."""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as redis_async

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: Optional[redis_async.Redis] = None


def get_redis() -> redis_async.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.redis_url:
            raise RuntimeError(
                "REDIS_URL is not set. Configure an Upstash (rediss://...) "
                "or local Redis URL."
            )
        _client = redis_async.from_url(
            settings.redis_url,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:  # pragma: no cover
            pass
        _client = None
