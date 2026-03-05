"""Integration test: HITL (Human-in-the-Loop) flows.

Tests approve, reject, edit, retry, skip operations
on workflow nodes with real database state transitions.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _create_project_and_answer(client: AsyncClient) -> tuple[str, str]:
    """Helper: create project, answer intake, return (project_id, intake_node_id)."""
    resp = await client.post(
        "/api/projects",
        json={
            "name": "HITL Test",
            "template_key": "market_research",
        },
    )
    project_id = resp.json()["id"]

    answer_resp = await client.post(
        f"/api/projects/{project_id}/nodes/intake_questions/answer",
        json={"answers": {"0": "SaaS app"}},
    )
    return project_id, answer_resp.json()["id"]


async def test_approve_awaiting_review_node(client: AsyncClient, db_session: AsyncSession):
    """Approve a node in AWAITING_REVIEW status."""
    project_id, _ = await _create_project_and_answer(client)

    # Manually set web_search to awaiting_review to simulate execution completion
    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    node = await get_node(db_session, project_id, "web_search")
    node.status = NodeStatus.AWAITING_REVIEW
    node.output_data = {"summary": "test results"}
    await db_session.commit()

    # Approve it
    resp = await client.post(f"/api/projects/{project_id}/nodes/web_search/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["completed_at"] is not None


async def test_reject_with_feedback(client: AsyncClient, db_session: AsyncSession):
    """Reject a node and verify feedback is stored."""
    project_id, _ = await _create_project_and_answer(client)

    # Set lean_canvas to awaiting_review
    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    node = await get_node(db_session, project_id, "lean_canvas")
    node.status = NodeStatus.AWAITING_REVIEW
    node.output_data = {"document": "draft doc"}
    await db_session.commit()

    # Reject with feedback
    resp = await client.post(
        f"/api/projects/{project_id}/nodes/lean_canvas/reject",
        json={"feedback": "Missing competitor section, add more detail on pricing"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["user_feedback"] == "Missing competitor section, add more detail on pricing"


async def test_retry_rejected_node(client: AsyncClient, db_session: AsyncSession):
    """Retry a rejected node — should go back to READY with incremented retry_count."""
    project_id, _ = await _create_project_and_answer(client)

    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    node = await get_node(db_session, project_id, "lean_canvas")
    node.status = NodeStatus.REJECTED
    node.user_feedback = "needs more data"
    await db_session.commit()

    resp = await client.post(f"/api/projects/{project_id}/nodes/lean_canvas/retry")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["retry_count"] == 1


async def test_retry_failed_node(client: AsyncClient, db_session: AsyncSession):
    """Retry a failed node — should go back to READY."""
    project_id, _ = await _create_project_and_answer(client)

    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    node = await get_node(db_session, project_id, "web_search")
    node.status = NodeStatus.FAILED
    await db_session.commit()

    resp = await client.post(f"/api/projects/{project_id}/nodes/web_search/retry")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


async def test_manual_edit_output(client: AsyncClient, db_session: AsyncSession):
    """Edit node output — creates artifact version and auto-approves."""
    project_id, _ = await _create_project_and_answer(client)

    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    node = await get_node(db_session, project_id, "lean_canvas")
    node.status = NodeStatus.AWAITING_REVIEW
    node.output_data = {"document": "v1 content"}
    await db_session.commit()

    # Edit output
    resp = await client.put(
        f"/api/projects/{project_id}/nodes/lean_canvas/output",
        json={"output_data": {"document": "v2 edited content", "title": "Lean Canvas"}},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["output_data"]["document"] == "v2 edited content"

    # Verify artifact was created
    artifacts_resp = await client.get(f"/api/projects/{project_id}/artifacts/node/lean_canvas")
    assert artifacts_resp.status_code == 200
    artifacts = artifacts_resp.json()["artifacts"]
    assert len(artifacts) == 1
    assert artifacts[0]["version"] == 1


async def test_skip_node(client: AsyncClient, db_session: AsyncSession):
    """Skip a pending node."""
    project_id, _ = await _create_project_and_answer(client)

    # Skip competitor_analysis (currently pending)
    resp = await client.post(f"/api/projects/{project_id}/nodes/competitor_analysis/skip")
    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"


async def test_invalid_approve_pending_node(client: AsyncClient):
    """Approve a node that isn't in AWAITING_REVIEW → 409."""
    resp = await client.post(
        "/api/projects",
        json={
            "name": "Invalid Approve",
            "template_key": "market_research",
        },
    )
    project_id = resp.json()["id"]

    # web_search is pending, can't approve
    resp = await client.post(f"/api/projects/{project_id}/nodes/web_search/approve")
    assert resp.status_code == 409


async def test_invalid_reject_pending_node(client: AsyncClient):
    """Reject a node that isn't in AWAITING_REVIEW → 409."""
    resp = await client.post(
        "/api/projects",
        json={
            "name": "Invalid Reject",
            "template_key": "market_research",
        },
    )
    project_id = resp.json()["id"]

    resp = await client.post(
        f"/api/projects/{project_id}/nodes/web_search/reject",
        json={"feedback": "bad"},
    )
    assert resp.status_code == 409


async def test_invalid_retry_approved_node(client: AsyncClient):
    """Retry an already-approved node → 409."""
    resp = await client.post(
        "/api/projects",
        json={
            "name": "Invalid Retry",
            "template_key": "market_research",
        },
    )
    project_id = resp.json()["id"]

    # Answer intake (auto-approves)
    await client.post(
        f"/api/projects/{project_id}/nodes/intake_questions/answer",
        json={"answers": {"0": "x"}},
    )

    # Retry should fail
    resp = await client.post(f"/api/projects/{project_id}/nodes/intake_questions/retry")
    assert resp.status_code == 409


async def test_node_not_found(client: AsyncClient):
    """Access nonexistent node → 404."""
    resp = await client.post(
        "/api/projects",
        json={
            "name": "404 Test",
            "template_key": "market_research",
        },
    )
    project_id = resp.json()["id"]

    resp = await client.get(f"/api/projects/{project_id}/nodes/nonexistent_slug")
    assert resp.status_code == 404


async def test_skip_then_downstream_checks(client: AsyncClient, db_session: AsyncSession):
    """Skipping a node counts as 'done' for dependency resolution."""
    project_id, _ = await _create_project_and_answer(client)

    from app.engine.resolver import propagate_completion
    from app.models.workflow_node import NodeStatus
    from app.services.node_service import get_node

    # Propagate intake completion to unblock web_search + competitor_analysis
    intake = await get_node(db_session, project_id, "intake_questions")
    await propagate_completion(db_session, intake.id)
    await db_session.commit()

    # Approve web_search
    ws = await get_node(db_session, project_id, "web_search")
    ws.status = NodeStatus.APPROVED
    ws.output_data = {"summary": "research"}
    await db_session.commit()
    await propagate_completion(db_session, ws.id)
    await db_session.commit()

    # Skip competitor_analysis
    await client.post(f"/api/projects/{project_id}/nodes/competitor_analysis/skip")

    # Propagate skip
    comp = await get_node(db_session, project_id, "competitor_analysis")
    await propagate_completion(db_session, comp.id)
    await db_session.commit()

    # market_sizing should now be ready (depends on web_search=approved)
    sizing = await get_node(db_session, project_id, "market_sizing")
    assert sizing.status == NodeStatus.READY

    # Approve market_sizing
    sizing.status = NodeStatus.APPROVED
    sizing.output_data = {"result": "TAM: $1B"}
    await db_session.commit()
    await propagate_completion(db_session, sizing.id)
    await db_session.commit()

    # lean_canvas depends on web_search(approved) +
    # competitor_analysis(skipped) + market_sizing(approved)
    # Should now be ready
    lean = await get_node(db_session, project_id, "lean_canvas")
    assert lean.status == NodeStatus.READY
