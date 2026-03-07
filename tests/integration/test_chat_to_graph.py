"""Integration tests: chat-driven flow from requirements gathering to graph generation.

Tests the full lifecycle:
  1. Create project via chat
  2. Converse until requirements are complete
  3. Select document types
  4. Graph is generated with correct nodes and edges
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import document_type_service

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# LLM mock helpers
# ---------------------------------------------------------------------------

def _make_complete_mock(responses: list[str]) -> AsyncMock:
    """Return a mock for llm_gateway.complete that yields responses in order."""
    mock = AsyncMock(side_effect=list(responses))
    return mock


async def _fake_stream(tokens: list[str]) -> AsyncIterator[str]:
    for t in tokens:
        yield t


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def seeded_client(client: AsyncClient, db_session: AsyncSession):
    """Client with document types seeded into the DB."""
    await document_type_service.seed_defaults(db_session)
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_requirements_complete_transitions_phase(
    seeded_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """When is_requirements_complete returns True, the project phase transitions to selecting_documents."""
    import uuid
    from app.models.chat import ChatMessage, ChatRole
    from app.models.project import Project

    # Create project in gathering_requirements phase with enough chat history
    project = Project(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Phase Transition Test",
        description="Test",
        template_key="chat_driven",
        chat_phase="gathering_requirements",
    )
    db_session.add(project)
    await db_session.flush()

    # Add conversation history (2 exchanges = 4 messages)
    messages = [
        (ChatRole.USER, "I want to build a food delivery app for college campuses"),
        (ChatRole.ASSISTANT, "Great idea! Who are your target customers?"),
        (ChatRole.USER, "College students aged 18-24, subscription model at $9.99/month"),
        (ChatRole.ASSISTANT, "That's a solid direction! Let me understand more."),
    ]
    for role, content in messages:
        db_session.add(ChatMessage(project_id=project.id, role=role, content=content))
    await db_session.flush()

    # Now add a new user message (the one that triggers the next AI response + completeness check)
    db_session.add(
        ChatMessage(
            project_id=project.id,
            role=ChatRole.USER,
            content="We'll partner with local restaurants near campus for delivery.",
        )
    )
    await db_session.commit()

    # Mock the LLM: streaming response + completeness check returns true
    mock_publish = AsyncMock()
    with patch("app.services.llm_gateway.llm_gateway") as mock_gw, \
         patch("app.services.event_bus.EventBus.publish", mock_publish):
        mock_gw.complete_stream = AsyncMock(
            return_value=_fake_stream(["Sounds like a solid plan!"])
        )
        mock_gw.complete = AsyncMock(
            return_value='{"complete": true, "summary": "Food delivery for college students"}'
        )

        # Trigger stream_response_events directly with the test session
        from app.services.chat_service import stream_response_events

        events = []
        async for event in stream_response_events(project.id, db_session):
            events.append(event)

    # Verify events were emitted
    event_types = [e["event"] for e in events]
    assert "assistant_token" in event_types
    assert "assistant_done" in event_types

    # Verify phase transitioned
    await db_session.refresh(project)
    assert project.chat_phase == "selecting_documents"


async def test_hard_cap_forces_completion(db_session: AsyncSession) -> None:
    """After 6 user messages, is_requirements_complete should force complete=True."""
    from app.engine.agents.initial_analysis import InitialAnalysisAgent

    agent = InitialAnalysisAgent()

    # Build a history with 6 user messages (12 total with assistant replies)
    history: list[dict[str, str]] = []
    for i in range(6):
        history.append({"role": "user", "content": f"User message {i}"})
        history.append({"role": "assistant", "content": f"Assistant response {i}"})

    # Should force complete without calling LLM
    result = await agent.is_requirements_complete(history)
    assert result["complete"] is True
    assert "User-provided context" in result["summary"]


async def test_min_messages_required(db_session: AsyncSession) -> None:
    """With only 1 user message, requirements should be incomplete."""
    from app.engine.agents.initial_analysis import InitialAnalysisAgent

    agent = InitialAnalysisAgent()
    history = [
        {"role": "user", "content": "I want to build an app"},
        {"role": "assistant", "content": "Tell me more!"},
    ]

    result = await agent.is_requirements_complete(history)
    assert result["complete"] is False


async def test_select_documents_generates_graph(
    seeded_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Selecting document types after requirements are complete builds a valid graph."""
    from app.models.chat import ChatMessage, ChatRole
    from app.models.project import Project

    # Manually create a project in "selecting_documents" phase
    import uuid

    project = Project(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Graph Gen",
        description="Test",
        template_key="chat_driven",
        chat_phase="selecting_documents",
    )
    db_session.add(project)
    await db_session.flush()

    # Add some chat history
    for role, content in [
        (ChatRole.USER, "I want to build a marketplace for vintage clothing"),
        (ChatRole.ASSISTANT, "Great idea! Who are your target customers?"),
        (ChatRole.USER, "Fashion-conscious millennials, aged 25-35"),
        (ChatRole.ASSISTANT, "I have enough information to proceed."),
    ]:
        db_session.add(
            ChatMessage(project_id=project.id, role=role, content=content)
        )
    await db_session.commit()

    # Mock the LLM for requirements reorganization and the event bus (no Redis in tests)
    mock_publish = AsyncMock()
    with patch("app.engine.agents.graph_generator.llm_gateway") as mock_gw, \
         patch("app.api.routes.chat.event_bus") as mock_bus_route, \
         patch("app.services.event_bus.EventBus.publish", mock_publish):
        mock_gw.complete = AsyncMock(
            return_value=(
                "Business: Vintage clothing marketplace. "
                "Target: Fashion-conscious millennials 25-35. "
                "Revenue: Commission on sales."
            )
        )
        mock_bus_route.publish = mock_publish

        resp = await seeded_client.post(
            f"/api/projects/{project.id}/chat/select-documents",
            json={"doc_type_keys": ["lean_canvas", "competitor_analysis"]},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "workflow" in data["content"].lower() or "nodes" in data["content"].lower()

    # Verify graph was created
    graph_resp = await seeded_client.get(f"/api/projects/{project.id}/graph")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()

    # Should have nodes from both lean_canvas and competitor_analysis templates
    node_slugs = {n["slug"] for n in graph["nodes"]}
    assert "lean_canvas" in node_slugs
    assert "competitor_analysis" in node_slugs
    assert "intake_questions" in node_slugs
    assert "web_search" in node_slugs
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0

    # Verify root nodes are READY
    for node in graph["nodes"]:
        if node["slug"] == "intake_questions":
            assert node["status"] == "ready"

    # Verify project phase updated
    proj_resp = await seeded_client.get(f"/api/projects/{project.id}")
    assert proj_resp.json()["chat_phase"] == "graph_ready"


async def test_select_documents_wrong_phase_rejected(
    seeded_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Selecting documents when not in selecting_documents phase returns 400."""
    import uuid
    from app.models.project import Project

    project = Project(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Wrong Phase",
        description="Test",
        template_key="chat_driven",
        chat_phase="gathering_requirements",
    )
    db_session.add(project)
    await db_session.commit()

    resp = await seeded_client.post(
        f"/api/projects/{project.id}/chat/select-documents",
        json={"doc_type_keys": ["lean_canvas"]},
    )
    assert resp.status_code == 400


async def test_message_count_hint_escalates(db_session: AsyncSession) -> None:
    """Verify the requirements check becomes more aggressive with more messages."""
    from app.engine.agents.initial_analysis import InitialAnalysisAgent

    agent = InitialAnalysisAgent()

    # 3 user messages — moderate hint
    history_3 = []
    for i in range(3):
        history_3.append({"role": "user", "content": f"Info {i}"})
        history_3.append({"role": "assistant", "content": f"Response {i}"})

    # 5 user messages — strong hint
    history_5 = []
    for i in range(5):
        history_5.append({"role": "user", "content": f"Info {i}"})
        history_5.append({"role": "assistant", "content": f"Response {i}"})

    with patch("app.engine.agents.initial_analysis.llm_gateway") as mock_gw:
        # Both return incomplete to test the hint mechanism
        mock_gw.complete = AsyncMock(
            return_value='{"complete": false, "summary": "Need more info"}'
        )

        result_3 = await agent.is_requirements_complete(history_3)
        assert result_3["complete"] is False

    # 5 messages but LLM parsing fails — should force complete
    with patch("app.engine.agents.initial_analysis.llm_gateway") as mock_gw:
        mock_gw.complete = AsyncMock(return_value="This is not valid JSON")

        result_5 = await agent.is_requirements_complete(history_5)
        # With 5 user messages and a parse failure, should force complete
        assert result_5["complete"] is True
