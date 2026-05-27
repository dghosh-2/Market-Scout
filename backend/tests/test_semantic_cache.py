"""SemanticCache: lookup/write paths with mocked Redis + embeddings."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.cache import semantic_cache as sc_mod


def _make_fake_redis(entries):
    """entries: list of (key, payload_dict). Returns a mock redis client."""
    keys = [k.encode() for k, _ in entries]
    payloads = {k.encode(): json.dumps(p).encode() for k, p in entries}

    client = MagicMock()
    client.smembers = AsyncMock(return_value=set(keys))
    client.srem = AsyncMock(return_value=0)

    async def get(k):
        return payloads.get(k if isinstance(k, bytes) else k.encode())

    client.get = AsyncMock(side_effect=get)

    pipe = MagicMock()
    pipe.set = MagicMock()
    pipe.sadd = MagicMock()
    pipe.execute = AsyncMock(return_value=None)
    client.pipeline = MagicMock(return_value=pipe)
    return client


@pytest.mark.asyncio
async def test_lookup_returns_cached_when_similarity_above_threshold(monkeypatch):
    # Identical embedding → cosine sim = 1.0 → hit
    embedding = [1.0, 0.0, 0.0]

    async def fake_embed(text, model=None):
        return embedding

    monkeypatch.setattr(sc_mod, "embed_text", fake_embed)

    cached_report = {"ticker": "AAPL", "data": {"hello": "world"}}
    entry = {
        "id": "abc",
        "query": "tell me about apple",
        "embedding": embedding,
        "report": cached_report,
        "created_at": 0,
    }
    fake_redis = _make_fake_redis([("marketscout:cache:entry:abc", entry)])
    monkeypatch.setattr(sc_mod, "get_redis", lambda: fake_redis)

    cache = sc_mod.SemanticCache()
    cache.threshold = 0.85

    result = await cache.lookup("Apple analysis please")
    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["_cache"]["hit"] is True
    assert result["_cache"]["similarity"] == pytest.approx(1.0, abs=1e-6)


@pytest.mark.asyncio
async def test_lookup_returns_none_when_below_threshold(monkeypatch):
    # Orthogonal vectors → cosine sim = 0 → miss
    async def fake_embed(text, model=None):
        return [1.0, 0.0, 0.0]

    monkeypatch.setattr(sc_mod, "embed_text", fake_embed)

    entry = {
        "id": "abc",
        "query": "totally different",
        "embedding": [0.0, 1.0, 0.0],
        "report": {"data": {}},
        "created_at": 0,
    }
    fake_redis = _make_fake_redis([("marketscout:cache:entry:abc", entry)])
    monkeypatch.setattr(sc_mod, "get_redis", lambda: fake_redis)

    cache = sc_mod.SemanticCache()
    cache.threshold = 0.85
    result = await cache.lookup("anything")
    assert result is None


@pytest.mark.asyncio
async def test_lookup_returns_none_when_redis_unavailable(monkeypatch):
    def boom():
        raise RuntimeError("REDIS_URL is not set.")

    monkeypatch.setattr(sc_mod, "get_redis", boom)
    cache = sc_mod.SemanticCache()
    result = await cache.lookup("anything")
    assert result is None


@pytest.mark.asyncio
async def test_write_pipelines_set_and_sadd(monkeypatch):
    captured: dict = {}

    async def fake_embed(text, model=None):
        return [0.1] * 5

    monkeypatch.setattr(sc_mod, "embed_text", fake_embed)

    client = MagicMock()
    pipe = MagicMock()
    pipe.set = MagicMock(side_effect=lambda *a, **kw: captured.setdefault("set", (a, kw)))
    pipe.sadd = MagicMock(side_effect=lambda *a, **kw: captured.setdefault("sadd", (a, kw)))
    pipe.execute = AsyncMock(return_value=None)
    client.pipeline = MagicMock(return_value=pipe)
    monkeypatch.setattr(sc_mod, "get_redis", lambda: client)

    cache = sc_mod.SemanticCache()
    await cache.write("Analyze TSLA", {"ticker": "TSLA", "data": {"x": 1}})

    assert "set" in captured
    assert "sadd" in captured
    # SET key has the expected prefix
    set_args, _ = captured["set"]
    assert set_args[0].startswith("marketscout:cache:entry:")
