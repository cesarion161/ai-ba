from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway

logger = structlog.get_logger()


@register_handler(NodeType.DENSIFY)
class DensifyHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        target_role = config.get("role", "developer")

        # Collect all documents from upstream
        documents: list[str] = []
        for key, data in input_data.items():
            if isinstance(data, dict):
                if "document" in data:
                    documents.append(data["document"])
                elif "densified" in data:
                    documents.append(data["densified"])
                elif "summary" in data:
                    documents.append(data["summary"])

        combined = "\n\n---\n\n".join(documents)

        prompt = f"""You are a technical writer specializing in \
creating machine-readable directives.

Compress the following business analysis documents into dense, \
actionable directives for a {target_role}.

## Source Documents
{combined}

## Output Requirements
- Use imperative statements
- Be specific and actionable
- Remove all fluff and filler
- Organize by priority
- Include concrete metrics where available
- Format as a structured reference document

Output the densified directives.
"""

        messages = [
            {"role": "system", "content": f"Create directives optimized for a {target_role}."},
            {"role": "user", "content": prompt},
        ]

        densified = await llm_gateway.complete(messages, max_tokens=4096)

        return {
            "densified": densified,
            "target_role": target_role,
            "source_count": len(documents),
        }
