"""AsyncOpenAI singleton + thin helpers used across the agent graph + cache."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from openai import AsyncOpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_async_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(api_key=settings.openai_api_key or "missing")
    return _client


async def embed_text(text: str, *, model: Optional[str] = None) -> List[float]:
    """Return a single embedding vector for the given text."""
    settings = get_settings()
    client = get_async_client()
    resp = await client.embeddings.create(
        model=model or settings.embedding_model,
        input=text,
    )
    return list(resp.data[0].embedding)


async def chat_completion(
    *,
    messages: Sequence[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    max_tokens: int = 1500,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Run a chat completion, returning {content, usage} for telemetry."""
    client = get_async_client()
    resp = await client.chat.completions.create(
        model=model,
        messages=list(messages),
        max_tokens=max_tokens,
        temperature=temperature,
    )
    content = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    usage_dict: Dict[str, Any] = {}
    if usage is not None:
        usage_dict = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
    return {"content": content, "usage": usage_dict, "model": model}
