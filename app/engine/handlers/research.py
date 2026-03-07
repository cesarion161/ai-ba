from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine
from app.services.tools.web_search import search_web

logger = structlog.get_logger()


@register_handler(NodeType.RESEARCH)
class ResearchHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        max_results = config.get("max_results", 10)
        focus = config.get("focus", "general")

        # Get requirements summary (injected by orchestrator from project)
        requirements = input_data.get("_requirements_summary", "")

        # Build search queries from requirements + focus
        base_queries = await self._build_search_queries(requirements, focus)

        # Run web searches
        all_results: list[dict] = []
        per_query = max(1, max_results // max(len(base_queries), 1))
        for query in base_queries:
            results = await search_web(query, max_results=per_query)
            all_results.extend(results)

        if not all_results:
            return {
                "summary": "No search results found. Check that TAVILY_API_KEY is configured.",
                "sources": [],
                "raw_results": [],
            }

        # Synthesize with LLM
        research_context = "\n".join(
            f"- [{r['title']}]({r['url']}): {r['content'][:300]}"
            for r in all_results[:10]
        )

        focus_instruction = {
            "competitors": "Focus on competitive landscape, strengths/weaknesses, market positioning.",
            "technology": "Focus on technology stack choices, architecture patterns, tools.",
            "features": "Focus on feature landscape, what similar products offer, gaps.",
            "pricing": "Focus on pricing models, strategies, benchmarks in this space.",
            "ux_patterns": "Focus on UX patterns, user experience best practices, design trends.",
        }.get(focus, "Provide a comprehensive market analysis.")

        messages = [
            {
                "role": "system",
                "content": "You are a market research analyst. Synthesize the research results into actionable insights.",
            },
            {
                "role": "user",
                "content": (
                    f"## Business Context\n{requirements}\n\n"
                    f"## Research Focus\n{focus_instruction}\n\n"
                    f"## Search Results\n{research_context}\n\n"
                    "Synthesize these results into a clear, structured analysis. "
                    "Include specific data points, trends, and actionable recommendations."
                ),
            },
        ]

        summary = await llm_gateway.complete(messages)

        return {
            "summary": summary,
            "sources": [r["url"] for r in all_results],
            "raw_results": all_results[:10],
        }

    async def _build_search_queries(self, requirements: str, focus: str) -> list[str]:
        """Use LLM to generate targeted search queries from requirements."""
        if not requirements:
            return [f"{focus} market analysis", f"{focus} industry trends"]

        messages = [
            {
                "role": "system",
                "content": (
                    "Generate 2-3 specific web search queries based on the business "
                    "requirements below. Return ONLY the queries, one per line. No numbering."
                ),
            },
            {
                "role": "user",
                "content": f"Requirements:\n{requirements}\n\nSearch focus: {focus}",
            },
        ]

        try:
            result = await llm_gateway.complete(messages)
            queries = [q.strip() for q in result.strip().split("\n") if q.strip()]
            return queries[:3]
        except Exception:
            logger.warning("Failed to generate search queries, using defaults")
            return [f"{focus} market analysis", f"{focus} industry trends"]
