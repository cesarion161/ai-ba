"""LangGraph orchestrator implementing scheduler-loop pattern for DAG execution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from langgraph.graph import END, StateGraph
from langgraph.types import Send, interrupt

from app.engine.handlers.base import get_handler
from app.engine.state import WorkflowState
from app.models.workflow_node import NodeStatus
from app.services.event_bus import (
    NODE_COMPLETED,
    NODE_FAILED,
    NODE_STATUS_CHANGED,
    WORKFLOW_COMPLETED,
    event_bus,
)

logger = structlog.get_logger()


async def scheduler_node(
    state: WorkflowState,
    *,
    session_factory: Any = None,
) -> dict:
    """Check which nodes are ready and store their slugs for fan-out."""
    if session_factory is None:
        return {"error": "No session factory provided"}

    async with session_factory() as session:
        from app.engine.resolver import resolve_ready_nodes

        project_id = uuid.UUID(state["project_id"])
        ready_nodes = await resolve_ready_nodes(session, project_id)
        await session.commit()

    slugs = [n.slug for n in ready_nodes]

    if not slugs:
        logger.info("scheduler: no ready nodes, ending", project_id=state["project_id"])
        await event_bus.publish(
            state["project_id"], WORKFLOW_COMPLETED,
            {"status": "paused_or_complete"},
        )
    else:
        logger.info("scheduler: dispatching nodes", count=len(slugs), slugs=slugs)

    return {"ready_slugs": slugs, "error": None}


def _fan_out_ready(state: WorkflowState) -> list[Send] | str:
    """Conditional edge: fan out to ready nodes or end."""
    slugs = state.get("ready_slugs", [])
    if not slugs:
        return END

    return [
        Send("execute_node", {**state, "current_node_slug": slug})
        for slug in slugs
    ]


async def execute_node(
    state: WorkflowState,
    *,
    session_factory: Any = None,
) -> dict:
    """Execute a single node via its handler, optionally pause for HITL."""
    slug = state["current_node_slug"]
    project_id = uuid.UUID(state["project_id"])

    if session_factory is None:
        return {"error": f"No session factory for node {slug}"}

    async with session_factory() as session:
        from app.services.node_service import get_node

        node = await get_node(session, project_id, slug)
        if not node:
            return {"error": f"Node {slug} not found"}

        # Mark as running
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now(UTC)
        await session.commit()
        await event_bus.publish(
            state["project_id"], NODE_STATUS_CHANGED,
            {"slug": slug, "status": "running"},
        )

        # Gather input from upstream outputs
        node_results = state.get("node_results", {})
        input_data: dict[str, Any] = {}
        for dep_slug, dep_output in node_results.items():
            input_data[dep_slug] = dep_output
        node.input_data = input_data
        await session.commit()

        # Inject requirements summary into input_data for context
        requirements_summary = state.get("requirements_summary", "")
        if requirements_summary:
            input_data["_requirements_summary"] = requirements_summary

        # Execute handler
        try:
            handler = get_handler(node.node_type)
            output = await handler.execute(node.config, input_data, node.user_feedback)
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.completed_at = datetime.now(UTC)
            await session.commit()
            logger.error("node execution failed", slug=slug, error=str(e))
            await event_bus.publish(
                state["project_id"], NODE_FAILED,
                {"slug": slug, "status": "failed", "error": str(e)},
            )
            return {"error": str(e)}

        node.output_data = output
        await session.commit()

        # HITL: if requires approval, pause for review
        if node.requires_approval:
            node.status = NodeStatus.AWAITING_REVIEW
            await session.commit()
            await event_bus.publish(
                state["project_id"], NODE_STATUS_CHANGED,
                {"slug": slug, "status": "awaiting_review"},
            )
            # LangGraph interrupt — graph pauses here
            decision = interrupt(
                {
                    "node_slug": slug,
                    "output": output,
                    "message": f"Node '{node.label}' awaiting review",
                }
            )
            # When resumed, decision comes from Command(resume=...)
            if decision == "approve":
                node.status = NodeStatus.APPROVED
                node.completed_at = datetime.now(UTC)
            elif decision == "reject":
                node.status = NodeStatus.REJECTED
            else:
                node.status = NodeStatus.APPROVED
                node.completed_at = datetime.now(UTC)
            await session.commit()
        else:
            node.status = NodeStatus.APPROVED
            node.completed_at = datetime.now(UTC)
            await session.commit()
            await event_bus.publish(
                state["project_id"], NODE_COMPLETED,
                {"slug": slug, "status": "approved"},
            )

        # Propagate completion
        from app.engine.resolver import propagate_completion

        await propagate_completion(session, node.id)
        await session.commit()

    return {
        "node_results": {slug: output},
        "completed_slugs": [slug],
    }


def build_workflow_graph(session_factory: Any = None) -> StateGraph:
    """Build the reusable workflow StateGraph with a bound session factory."""
    from functools import partial

    if session_factory is not None:
        bound_scheduler = partial(scheduler_node, session_factory=session_factory)
        bound_execute = partial(execute_node, session_factory=session_factory)
    else:
        bound_scheduler = scheduler_node
        bound_execute = execute_node

    graph = StateGraph(WorkflowState)

    graph.add_node("scheduler", bound_scheduler)
    graph.add_node("execute_node", bound_execute)

    graph.set_entry_point("scheduler")

    # After execute_node, go back to scheduler to check for newly ready nodes
    graph.add_edge("execute_node", "scheduler")

    # Scheduler sets ready_slugs, then conditional edge fans out or ends
    graph.add_conditional_edges("scheduler", _fan_out_ready, ["execute_node", END])

    return graph
