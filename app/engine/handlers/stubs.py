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


@register_handler(NodeType.GENERATE_BACKLOG)
class GenerateBacklogHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "document": "# Product Backlog\n\nMock backlog content.",
            "title": "Product Backlog",
            "format": "markdown",
            "backlog_json": {
                "metadata": {
                    "generated_at": "2026-03-10T00:00:00Z",
                    "total_story_points": 21,
                    "total_stories": 5,
                    "total_epics": 2,
                    "sprint_count": 2,
                },
                "epics": [
                    {
                        "id": "EPIC-001",
                        "title": "Mock Epic",
                        "description": "Mock epic description",
                        "priority": "high",
                        "target_release": "MVP",
                        "stories": [
                            {
                                "id": "US-001",
                                "title": "Mock Story",
                                "description": "As a user, I want mock, so that test",
                                "type": "user_story",
                                "priority": "high",
                                "story_points": 5,
                                "sprint": "Sprint 1",
                                "acceptance_criteria": ["Given/When/Then mock"],
                                "dependencies": [],
                                "labels": ["mvp"],
                            }
                        ],
                    }
                ],
                "standalone_tasks": [],
                "sprints": [
                    {
                        "name": "Sprint 1",
                        "goal": "Mock sprint goal",
                        "duration_weeks": 2,
                        "capacity_points": 21,
                        "story_ids": ["US-001"],
                    }
                ],
            },
        }


@register_handler(NodeType.FORMAT_EXPORT)
class FormatExportHandlerStub:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        return {"archive_url": "s3://mock/export.zip"}
