"""Stub handlers for all node types. Return mock data for testing."""
from __future__ import annotations

from typing import Any

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType


@register_handler(NodeType.RESEARCH)
class ResearchHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "summary": "Mock research results",
            "sources": ["https://example.com"],
            "data": {},
        }


@register_handler(NodeType.CALCULATE)
class CalculateHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "result": "Mock calculation",
            "figures": {},
        }


@register_handler(NodeType.GENERATE_DOCUMENT)
class GenerateDocumentHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "document": "# Mock Document\n\nContent here.",
            "title": "Mock Document",
        }


@register_handler(NodeType.ASK_USER)
class AskUserHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        questions = (node_config or {}).get("questions", ["Default question?"])
        return {"questions": questions, "awaiting_answers": True}


@register_handler(NodeType.CRITIC_REVIEW)
class CriticReviewHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "verdict": "pass",
            "feedback": "Looks good.",
            "score": 8.5,
        }


@register_handler(NodeType.DENSIFY)
class DensifyHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {"densified": "Mock densified output"}


@register_handler(NodeType.FORMAT_EXPORT)
class FormatExportHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {"archive_url": "s3://mock/export.zip"}
