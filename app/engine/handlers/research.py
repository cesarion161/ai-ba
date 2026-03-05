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

        # Extract context from upstream answers
        answers = {}
        for upstream_data in input_data.values():
            if isinstance(upstream_data, dict) and "answers" in upstream_data:
                answers = upstream_data["answers"]
                break

        business_idea = answers.get("0", answers.get("business_idea", "Unknown"))
        target_audience = answers.get("1", answers.get("target_audience", "Unknown"))

        # Build search queries
        queries = [
            f"{business_idea} market analysis",
            f"{business_idea} industry trends",
        ]
        if focus == "competitors":
            known = answers.get("4", answers.get("competitors", ""))
            queries = [
                f"{business_idea} competitors",
                f"{known} competitor analysis" if known else f"{business_idea} market players",
            ]

        # Run web searches
        all_results: list[dict] = []
        for query in queries:
            results = await search_web(query, max_results=max_results // len(queries))
            all_results.extend(results)

        # Synthesize with LLM
        sub = "competitor_analysis" if focus == "competitors" else "web_search"
        template_key = f"market_research/{sub}"
        try:
            prompt = prompt_engine.render(
                template_key,
                business_idea=business_idea,
                target_audience=target_audience,
                known_competitors=answers.get("4", "").split(",") if focus == "competitors" else [],
                user_feedback=user_feedback,
            )
        except Exception:
            prompt = f"Analyze the following research results about '{business_idea}':\n\n"
            for r in all_results[:5]:
                prompt += f"- {r['title']}: {r['content'][:200]}\n"

        messages = [
            {"role": "system", "content": "You are a market research analyst."},
            {"role": "user", "content": prompt},
        ]

        summary = await llm_gateway.complete(messages)

        return {
            "summary": summary,
            "sources": [r["url"] for r in all_results],
            "raw_results": all_results[:10],
        }
