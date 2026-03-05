"""Integration test: full workflow lifecycle with real database.

Tests:
- Create project → workflow instantiated with correct nodes
- Root nodes start as READY
- Dependent nodes start as PENDING
- Answer ask_user → node becomes APPROVED
- Dependency resolution marks downstream as READY
- Graph status reports correct progress
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_create_project_instantiates_dag(client: AsyncClient):
    """POST /api/projects creates project with market_research workflow nodes."""
    resp = await client.post("/api/projects", json={
        "name": "Test Project",
        "description": "Integration test project",
        "template_key": "market_research",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Project"
    assert data["template_key"] == "market_research"
    project_id = data["id"]

    # Verify graph was created
    graph_resp = await client.get(f"/api/projects/{project_id}/graph")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()
    assert len(graph["nodes"]) == 6  # market_research has 6 nodes
    assert len(graph["edges"]) == 7  # intake->web, intake->comp, web->sizing, web+comp+sizing->lean, lean->critic


async def test_root_nodes_are_ready(client: AsyncClient):
    """Root nodes (no dependencies) should start as READY."""
    resp = await client.post("/api/projects", json={
        "name": "Root Test",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    graph = (await client.get(f"/api/projects/{project_id}/graph")).json()

    # intake_questions is the only root — should be ready
    intake = next(n for n in graph["nodes"] if n["slug"] == "intake_questions")
    assert intake["status"] == "ready"

    # All others should be pending
    for node in graph["nodes"]:
        if node["slug"] != "intake_questions":
            assert node["status"] == "pending", f"{node['slug']} should be pending"


async def test_answer_ask_user_unlocks_downstream(client: AsyncClient, db_session: AsyncSession):
    """Answering an ask_user node approves it and makes dependents READY."""
    resp = await client.post("/api/projects", json={
        "name": "Answer Test",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    # Answer intake questions
    answer_resp = await client.post(
        f"/api/projects/{project_id}/nodes/intake_questions/answer",
        json={"answers": {
            "0": "AI tutoring platform",
            "1": "K-12 students",
            "2": "Personalized learning",
            "3": "$20-50/month",
            "4": "Khan Academy, Duolingo",
        }},
    )
    assert answer_resp.status_code == 200
    assert answer_resp.json()["status"] == "approved"

    # Trigger the resolver to propagate completion
    from app.engine.resolver import propagate_completion
    from app.services.node_service import get_node

    # Get the intake node to propagate from
    nodes_resp = await client.get(f"/api/projects/{project_id}/nodes")
    nodes = nodes_resp.json()["nodes"]
    intake = next(n for n in nodes if n["slug"] == "intake_questions")

    await propagate_completion(db_session, intake["id"])
    await db_session.commit()

    # Now check the graph
    graph = (await client.get(f"/api/projects/{project_id}/graph")).json()
    web = next(n for n in graph["nodes"] if n["slug"] == "web_search")
    comp = next(n for n in graph["nodes"] if n["slug"] == "competitor_analysis")
    assert web["status"] == "ready"
    assert comp["status"] == "ready"

    # market_sizing still pending (needs web_search)
    sizing = next(n for n in graph["nodes"] if n["slug"] == "market_sizing")
    assert sizing["status"] == "pending"


async def test_graph_status_reports_progress(client: AsyncClient):
    """GET /graph/status shows correct progress percentages."""
    resp = await client.post("/api/projects", json={
        "name": "Status Test",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    status = (await client.get(f"/api/projects/{project_id}/graph/status")).json()
    assert status["total_nodes"] == 6
    assert status["progress_pct"] == 0.0
    assert status["by_status"]["ready"] == 1
    assert status["by_status"]["pending"] == 5

    # Answer intake → one node approved
    await client.post(
        f"/api/projects/{project_id}/nodes/intake_questions/answer",
        json={"answers": {"0": "test"}},
    )

    status = (await client.get(f"/api/projects/{project_id}/graph/status")).json()
    assert status["by_status"]["approved"] == 1
    # 1/6 = 16.7%
    assert status["progress_pct"] == pytest.approx(16.7, abs=0.1)


async def test_create_project_full_analysis(client: AsyncClient):
    """Full analysis template creates 27 nodes across 7 branches."""
    resp = await client.post("/api/projects", json={
        "name": "Full Analysis Test",
        "template_key": "full_analysis",
    })
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    graph = (await client.get(f"/api/projects/{project_id}/graph")).json()
    assert len(graph["nodes"]) == 27

    branches = {n["branch"] for n in graph["nodes"]}
    assert branches == {
        "market_research", "product_strategy", "ux_requirements",
        "technical_architecture", "execution_planning", "densification", "export",
    }

    # Only intake_questions should be ready
    ready = [n for n in graph["nodes"] if n["status"] == "ready"]
    assert len(ready) == 1
    assert ready[0]["slug"] == "intake_questions"


async def test_list_and_get_project(client: AsyncClient):
    """CRUD: list and get project."""
    resp = await client.post("/api/projects", json={
        "name": "CRUD Test",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    # List
    list_resp = await client.get("/api/projects")
    assert list_resp.status_code == 200
    projects = list_resp.json()["projects"]
    assert any(p["id"] == project_id for p in projects)

    # Get
    get_resp = await client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "CRUD Test"


async def test_delete_project(client: AsyncClient):
    """DELETE /api/projects/{id} removes the project."""
    resp = await client.post("/api/projects", json={
        "name": "Delete Me",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    del_resp = await client.delete(f"/api/projects/{project_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404


async def test_list_nodes_with_filters(client: AsyncClient):
    """GET /nodes with branch/status/type filters."""
    resp = await client.post("/api/projects", json={
        "name": "Filter Test",
        "template_key": "market_research",
    })
    project_id = resp.json()["id"]

    # Filter by status
    ready = await client.get(f"/api/projects/{project_id}/nodes?status=ready")
    assert len(ready.json()["nodes"]) == 1

    # Filter by type
    ask = await client.get(f"/api/projects/{project_id}/nodes?node_type=ask_user")
    assert len(ask.json()["nodes"]) == 1
    assert ask.json()["nodes"][0]["slug"] == "intake_questions"

    # Filter by branch
    mr = await client.get(f"/api/projects/{project_id}/nodes?branch=market_research")
    assert len(mr.json()["nodes"]) == 6
