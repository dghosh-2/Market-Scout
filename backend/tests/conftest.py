"""Shared test fixtures.

We disable Langfuse, OpenAI, and DB connections at module load time so the
@observe decorators (applied at import time) are no-ops and tests are hermetic.
"""
from __future__ import annotations

import os
import sys

# These must be set BEFORE any `app.*` import — env-driven decorators read
# settings at decoration time (module load).
os.environ.setdefault("LANGFUSE_ENABLED", "false")
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("REDIS_URL", "")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Force a clean settings cache so subsequent imports see the env above.
from app.config import settings as _settings_mod  # noqa: E402
_settings_mod.get_settings.cache_clear()
