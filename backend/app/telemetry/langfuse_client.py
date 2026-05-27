"""Langfuse tracing wrappers.

Provides a single `observe` decorator (re-exporting Langfuse's when available, or
a no-op fallback otherwise) plus `update_current_observation(...)` for attaching
custom metadata (token counts, cache hit/miss, etc.) inside instrumented code.
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_langfuse_client: Any = None
_initialized: bool = False
_available: bool = False


def _import_langfuse():
    try:
        from langfuse import Langfuse  # type: ignore
        try:
            from langfuse.decorators import langfuse_context, observe as lf_observe  # type: ignore
        except Exception:  # pragma: no cover - older/newer SDK layout
            from langfuse import observe as lf_observe  # type: ignore
            langfuse_context = None  # type: ignore
        return Langfuse, lf_observe, langfuse_context
    except Exception:
        return None, None, None


def init_langfuse() -> None:
    """Initialize the Langfuse client. Safe to call multiple times."""
    global _langfuse_client, _initialized, _available
    if _initialized:
        return
    _initialized = True

    settings = get_settings()
    if not settings.langfuse_enabled:
        logger.info("Langfuse disabled via LANGFUSE_ENABLED=false")
        return
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("Langfuse keys not configured; tracing disabled")
        return

    Langfuse, _lf_observe, _lf_ctx = _import_langfuse()
    if Langfuse is None:
        logger.warning("langfuse package not installed; tracing disabled")
        return

    try:
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        _available = True
        logger.info("Langfuse client initialized")
    except Exception as e:
        logger.warning("Failed to init Langfuse: %s", e)


def get_client() -> Any:
    return _langfuse_client


def is_enabled() -> bool:
    return _available


def _decorator_enabled() -> bool:
    """Decorator should wrap with langfuse only when fully configured."""
    settings = get_settings()
    return bool(
        settings.langfuse_enabled
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    )


def observe(name: Optional[str] = None, **decorator_kwargs: Any) -> Callable:
    """Decorator that traces a function via Langfuse when configured.

    No-op when LANGFUSE_ENABLED is false or keys are missing, so tests stay
    hermetic and dev runs without Langfuse don't emit 401s.
    """
    def wrap(fn: Callable) -> Callable:
        if not _decorator_enabled():
            return fn
        _, lf_observe, _ = _import_langfuse()
        if lf_observe is None:
            return fn
        try:
            return lf_observe(name=name or fn.__name__, **decorator_kwargs)(fn)
        except Exception as e:  # pragma: no cover
            logger.debug("langfuse observe failed for %s: %s", fn.__name__, e)
            return fn

    return wrap


def update_current_observation(**metadata: Any) -> None:
    """Attach metadata (e.g. token counts, cache_hit) to the current span.
    No-op when Langfuse is unavailable."""
    if not _available:
        return
    _, _, lf_ctx = _import_langfuse()
    if lf_ctx is None:
        return
    try:
        lf_ctx.update_current_observation(metadata=metadata)
    except Exception as e:  # pragma: no cover
        logger.debug("langfuse metadata update failed: %s", e)


async def shutdown_langfuse() -> None:
    """Flush in-flight events on shutdown."""
    if _langfuse_client is None:
        return
    try:
        flush = getattr(_langfuse_client, "flush", None)
        if flush:
            flush()
    except Exception as e:  # pragma: no cover
        logger.debug("langfuse flush failed: %s", e)


def trace_span(name: str) -> "_SpanCtx":
    """Lightweight manual span helper for cases the decorator can't cover."""
    return _SpanCtx(name)


class _SpanCtx:
    def __init__(self, name: str):
        self.name = name
        self._span = None

    def __enter__(self):
        if not _available or _langfuse_client is None:
            return self
        try:
            self._span = _langfuse_client.span(name=self.name)
        except Exception:
            self._span = None
        return self

    def update(self, **metadata: Any):
        if self._span is None:
            return
        try:
            self._span.update(metadata=metadata)
        except Exception:
            pass

    def __exit__(self, exc_type, exc, tb):
        if self._span is None:
            return False
        try:
            if exc is not None:
                self._span.end(level="ERROR", status_message=str(exc))
            else:
                self._span.end()
        except Exception:
            pass
        return False
