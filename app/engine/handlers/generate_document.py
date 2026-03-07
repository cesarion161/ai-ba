from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine

logger = structlog.get_logger()


@register_handler(NodeType.GENERATE_DOCUMENT)
class GenerateDocumentHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        template_name = config.get("template", "generic")

        # Gather all upstream outputs
        requirements = input_data.pop("_requirements_summary", "")
        context_parts: dict[str, str] = {}
        for key, data in input_data.items():
            if isinstance(data, dict):
                if "summary" in data:
                    context_parts[key] = data["summary"]
                elif "result" in data:
                    context_parts[key] = data["result"]
                elif "document" in data:
                    context_parts[key] = data["document"]

        # Try to render template, fall back to generic prompt
        try:
            prompt = prompt_engine.render(
                f"market_research/{template_name}",
                research_summary=context_parts.get("web_search", ""),
                competitor_analysis=context_parts.get("competitor_analysis", ""),
                market_sizing=context_parts.get("market_sizing", ""),
                requirements_summary=requirements,
                user_feedback=user_feedback,
            )
        except Exception:
            prompt = f"Generate a {template_name} document based on:\n\n"
            if requirements:
                prompt += f"## Business Requirements\n{requirements}\n\n"
            for key, val in context_parts.items():
                prompt += f"## {key}\n{val[:1000]}\n\n"

        messages = [
            {"role": "system", "content": "You are a business strategy consultant."},
            {"role": "user", "content": prompt},
        ]

        document = await llm_gateway.complete(messages, max_tokens=8192)

        return {
            "document": document,
            "title": template_name.replace("_", " ").title(),
            "format": "markdown",
        }
