"""Redis-backed semantic cache for research-report responses.

Each cache entry stores:
    key:      f"{prefix}:entry:{uuid}"
    value:    JSON-encoded {query, embedding[], report{}, created_at}
    TTL:      semantic_cache_ttl_seconds

The cache also maintains a Redis Set of all entry keys at f"{prefix}:keys" so
lookup can iterate the candidates and compute cosine similarity in Python with
numpy. This trades a small CPU cost for not needing Redis Stack / RediSearch;
works against vanilla Upstash.

Threshold (cosine similarity) >= settings.semantic_cache_threshold is required
for a hit.
"""
from __future__ import annotations

import json
import logging
import math
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.cache.redis_client import get_redis
from app.config.settings import get_settings
from app.telemetry.langfuse_client import observe, update_current_observation
from app.utils.async_llm import embed_text

logger = logging.getLogger(__name__)


def _normalize(query: str) -> str:
    return (query or "").strip().lower()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class SemanticCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.prefix = self.settings.semantic_cache_prefix
        self.threshold = float(self.settings.semantic_cache_threshold)
        self.ttl = int(self.settings.semantic_cache_ttl_seconds)
        self.max_scan = int(self.settings.semantic_cache_max_scan)

    def _index_key(self) -> str:
        return f"{self.prefix}:keys"

    def _entry_key(self, eid: str) -> str:
        return f"{self.prefix}:entry:{eid}"

    @observe(name="semantic_cache.lookup")
    async def lookup(self, query: str) -> Optional[Dict[str, Any]]:
        """Return a cached report if any prior query embedding is within threshold."""
        try:
            client = get_redis()
        except Exception as e:
            logger.debug("Redis not configured, skipping cache: %s", e)
            update_current_observation(cache_hit=False, reason="redis_unavailable")
            return None

        try:
            q_embedding = np.asarray(await embed_text(query), dtype=np.float32)
        except Exception as e:
            logger.warning("embedding failed in cache lookup: %s", e)
            update_current_observation(cache_hit=False, reason="embed_failed")
            return None

        try:
            members = await client.smembers(self._index_key())
        except Exception as e:
            logger.warning("redis SMEMBERS failed: %s", e)
            update_current_observation(cache_hit=False, reason="redis_smembers_failed")
            return None

        if not members:
            update_current_observation(cache_hit=False, reason="empty_index")
            return None

        # Scan at most max_scan entries to bound cost
        scanned = 0
        best_sim = -1.0
        best_entry: Optional[Dict[str, Any]] = None
        stale_keys: List[bytes] = []
        for raw_key in members:
            if scanned >= self.max_scan:
                break
            key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
            try:
                raw_val = await client.get(key)
            except Exception:
                continue
            if raw_val is None:
                stale_keys.append(raw_key)
                continue
            try:
                payload = json.loads(raw_val)
                emb = np.asarray(payload.get("embedding") or [], dtype=np.float32)
                if emb.size != q_embedding.size:
                    continue
                sim = _cosine(q_embedding, emb)
            except Exception:
                continue
            scanned += 1
            if sim > best_sim:
                best_sim = sim
                best_entry = payload

        if stale_keys:
            try:
                await client.srem(self._index_key(), *stale_keys)
            except Exception:
                pass

        if best_entry and best_sim >= self.threshold:
            update_current_observation(
                cache_hit=True,
                similarity=best_sim,
                threshold=self.threshold,
                scanned=scanned,
            )
            report = best_entry.get("report")
            if isinstance(report, dict):
                report = dict(report)
                report["_cache"] = {
                    "hit": True,
                    "similarity": best_sim,
                    "matched_query": best_entry.get("query"),
                }
            return report

        update_current_observation(
            cache_hit=False,
            best_similarity=max(best_sim, 0.0),
            threshold=self.threshold,
            scanned=scanned,
        )
        return None

    @observe(name="semantic_cache.write")
    async def write(self, query: str, report: Dict[str, Any]) -> None:
        try:
            client = get_redis()
        except Exception as e:
            logger.debug("Redis not configured, skipping cache write: %s", e)
            return
        try:
            embedding = await embed_text(query)
        except Exception as e:
            logger.warning("embedding failed in cache write: %s", e)
            return

        eid = str(uuid.uuid4())
        key = self._entry_key(eid)
        payload = json.dumps(
            {
                "id": eid,
                "query": _normalize(query),
                "embedding": list(embedding),
                "report": report,
                "created_at": time.time(),
            },
            default=str,
        )
        try:
            pipe = client.pipeline()
            pipe.set(key, payload, ex=self.ttl)
            pipe.sadd(self._index_key(), key)
            await pipe.execute()
            update_current_observation(
                cached=True,
                entry_id=eid,
                ttl_seconds=self.ttl,
                embedding_dim=len(embedding),
            )
        except Exception as e:
            logger.warning("redis cache write failed: %s", e)
            update_current_observation(cached=False, reason=str(e))


_cache_singleton: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = SemanticCache()
    return _cache_singleton
