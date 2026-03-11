from __future__ import annotations

import json
from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine

logger = structlog.get_logger()

SYSTEM_MESSAGE = (
    "You are a senior technical program manager with deep experience in agile delivery, "
    "backlog management, and sprint planning. You create structured, actionable backlogs "
    "that engineering teams can immediately import into their project management tools. "
    "You output valid JSON only."
)


@register_handler(NodeType.GENERATE_BACKLOG)
class GenerateBacklogHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        # Gather upstream outputs using the same pattern as generate_document
        context_parts: dict[str, str] = {}
        for key, data in input_data.items():
            if isinstance(data, dict):
                if "summary" in data:
                    context_parts[key] = data["summary"]
                elif "result" in data:
                    context_parts[key] = data["result"]
                elif "document" in data:
                    context_parts[key] = data["document"]

        template_context = {
            "user_stories": context_parts.get("user_stories_critic", ""),
            "execution_plan": context_parts.get("execution_plan_critic", ""),
            "traceability_matrix": context_parts.get("traceability_matrix", ""),
            "product_roadmap": context_parts.get("product_roadmap_critic", ""),
        }

        # Phase 1: Generate structured JSON via LLM
        prompt = prompt_engine.render("backlog/backlog", **template_context)

        messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ]

        raw_json = await llm_gateway.complete_structured(
            messages,
            response_format={"type": "json_object"},
            task_type="generate_backlog",
        )

        # Parse JSON, retry once on failure
        try:
            backlog_data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("backlog_json_parse_failed", retrying=True)
            messages.append({"role": "assistant", "content": raw_json})
            messages.append({
                "role": "user",
                "content": (
                    "The JSON you produced is invalid. Fix the syntax errors and return "
                    "ONLY valid JSON matching the schema. No commentary."
                ),
            })
            raw_json = await llm_gateway.complete_structured(
                messages,
                response_format={"type": "json_object"},
                task_type="generate_backlog",
            )
            backlog_data = json.loads(raw_json)

        # Phase 2: Render markdown deterministically from JSON
        markdown = prompt_engine.render("backlog/backlog_markdown", **backlog_data)

        return {
            "document": markdown,
            "title": "Product Backlog",
            "format": "markdown",
            "backlog_json": backlog_data,
        }
