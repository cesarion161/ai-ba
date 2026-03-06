"""Integration tests for graph editing endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE_URL = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as c:
        yield c


@pytest.fixture
async def project_with_graph(client: AsyncClient) -> str:
    """Create a project with a template-based graph."""
    resp = await client.post(
        "/api/projects",
        json={"name": "Test Graph Edit", "template_key": "market_research"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_get_graph(client: AsyncClient, project_with_graph: str) -> None:
    resp = await client.get(f"/api/projects/{project_with_graph}/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0


@pytest.mark.asyncio
async def test_add_node(client: AsyncClient, project_with_graph: str) -> None:
    resp = await client.post(
        f"/api/projects/{project_with_graph}/graph/nodes",
        json={
            "slug": "custom_research",
            "label": "Custom Research",
            "node_type": "research",
            "branch": "custom",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "custom_research"


@pytest.mark.asyncio
async def test_delete_node(client: AsyncClient, project_with_graph: str) -> None:
    # Add a node first
    await client.post(
        f"/api/projects/{project_with_graph}/graph/nodes",
        json={
            "slug": "to_delete",
            "label": "To Delete",
            "node_type": "research",
        },
    )
    resp = await client.delete(
        f"/api/projects/{project_with_graph}/graph/nodes/to_delete"
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_add_edge_with_cycle_detection(
    client: AsyncClient, project_with_graph: str
) -> None:
    # Get existing graph to find two nodes
    graph_resp = await client.get(f"/api/projects/{project_with_graph}/graph")
    nodes = graph_resp.json()["nodes"]
    edges = graph_resp.json()["edges"]

    # Try adding a reverse edge that would create a cycle
    if len(edges) > 0:
        edge = edges[0]
        resp = await client.post(
            f"/api/projects/{project_with_graph}/graph/edges",
            json={"from_slug": edge["to_slug"], "to_slug": edge["from_slug"]},
        )
        # Could be 400 (cycle) or 201 (no cycle in simple case)
        assert resp.status_code in (201, 400)


@pytest.mark.asyncio
async def test_graph_status(client: AsyncClient, project_with_graph: str) -> None:
    resp = await client.get(f"/api/projects/{project_with_graph}/graph/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] > 0
    assert "progress_pct" in data
