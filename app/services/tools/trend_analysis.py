from __future__ import annotations

from typing import Any

import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


async def analyze_trends(query: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.SERPAPI_API_KEY:
        logger.warning("SerpApi key not configured, returning empty results")
        return {"trends": [], "related_queries": []}

    try:
        from serpapi import GoogleSearch

        params = {
            "engine": "google_trends",
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        return {
            "trends": results.get("interest_over_time", {}).get("timeline_data", []),
            "related_queries": results.get("related_queries", []),
        }
    except Exception as e:
        logger.error("trend_analysis_failed", query=query, error=str(e))
        return {"trends": [], "related_queries": [], "error": str(e)}
