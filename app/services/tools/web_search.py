from __future__ import annotations

from typing import Any

import structlog
from tavily import AsyncTavilyClient

from app.core.config import get_settings

logger = structlog.get_logger()


async def search_web(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, returning empty results")
        return []

    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    response = await client.search(query, max_results=max_results)

    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0),
        })

    logger.info("web_search_completed", query=query, num_results=len(results))
    return results
