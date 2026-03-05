from __future__ import annotations

from typing import Any

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType


@register_handler(NodeType.ASK_USER)
class AskUserHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        questions = config.get("questions", ["Please provide more details about your project."])

        return {
            "questions": questions,
            "awaiting_answers": True,
        }
