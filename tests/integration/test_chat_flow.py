"""Integration tests for chat-driven project creation flow."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as c:
        yield c


@pytest.mark.asyncio
async def test_create_project_from_chat(client: AsyncClient) -> None:
    response = await client.post(
        "/api/projects/from-chat",
        json={"initial_prompt": "A marketplace for vintage clothing"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["role"] == "assistant"
    assert len(data["content"]) > 0


@pytest.mark.asyncio
async def test_chat_history(client: AsyncClient) -> None:
    # Create project
    create_resp = await client.post(
        "/api/projects/from-chat",
        json={"initial_prompt": "Online tutoring platform"},
    )
    project_id = create_resp.json()["project_id"]

    # Get history
    history_resp = await client.get(f"/api/projects/{project_id}/chat")
    assert history_resp.status_code == 200
    data = history_resp.json()
    assert data["total"] >= 2  # user + assistant
    assert len(data["messages"]) >= 2


@pytest.mark.asyncio
async def test_send_chat_message(client: AsyncClient) -> None:
    # Create project
    create_resp = await client.post(
        "/api/projects/from-chat",
        json={"initial_prompt": "Food delivery for rural areas"},
    )
    project_id = create_resp.json()["project_id"]

    # Send message
    msg_resp = await client.post(
        f"/api/projects/{project_id}/chat",
        json={"content": "We target rural communities with limited restaurant access"},
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["role"] == "assistant"


@pytest.mark.asyncio
async def test_ui_config_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/config/ui")
    assert response.status_code == 200
    data = response.json()
    assert "status_colors" in data
    assert "node_status_colors" in data
    assert data["node_status_colors"]["approved"] == "#22C55E"


@pytest.mark.asyncio
async def test_document_types_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/document-types")
    assert response.status_code == 200
    # May be empty if not seeded, but endpoint works
    assert "document_types" in response.json()
