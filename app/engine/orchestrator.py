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

logger = structlog.get_logger()


async def scheduler_node(
    state: WorkflowState,
    *,
    session_factory: Any = None,
) -> list[Send] | dict:
    """Check which nodes are ready and fan out to them in parallel."""
    if session_factory is None:
        return {"error": "No session factory provided"}

    async with session_factory() as session:
        from app.engine.resolver import resolve_ready_nodes

        project_id = uuid.UUID(state["project_id"])
        ready_nodes = await resolve_ready_nodes(session, project_id)
        await session.commit()

    if not ready_nodes:
        logger.info("scheduler: no ready nodes, ending", project_id=state["project_id"])
        return {"error": None}

    sends = []
    for node in ready_nodes:
        sends.append(
            Send(
                "execute_node",
                {
                    **state,
                    "current_node_slug": node.slug,
                },
            )
        )

    logger.info(
        "scheduler: dispatching nodes",
        count=len(sends),
        slugs=[n.slug for n in ready_nodes],
    )
    return sends


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

        # Gather input from upstream outputs
        node_results = state.get("node_results", {})
        input_data: dict[str, Any] = {}
        for dep_slug, dep_output in node_results.items():
            input_data[dep_slug] = dep_output
        node.input_data = input_data
        await session.commit()

        # Execute handler
        try:
            handler = get_handler(node.node_type)
            output = await handler.execute(node.config, input_data, node.user_feedback)
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.completed_at = datetime.now(UTC)
            await session.commit()
            logger.error("node execution failed", slug=slug, error=str(e))
            return {"error": str(e)}

        node.output_data = output
        await session.commit()

        # HITL: if requires approval, pause for review
        if node.requires_approval:
            node.status = NodeStatus.AWAITING_REVIEW
            await session.commit()
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

        # Propagate completion
        from app.engine.resolver import propagate_completion

        await propagate_completion(session, node.id)
        await session.commit()

    return {
        "node_results": {slug: output},
        "completed_slugs": [slug],
    }


def build_workflow_graph() -> StateGraph:
    """Build the reusable workflow StateGraph."""
    graph = StateGraph(WorkflowState)

    graph.add_node("scheduler", scheduler_node)
    graph.add_node("execute_node", execute_node)

    graph.set_entry_point("scheduler")

    # After execute_node, go back to scheduler to check for newly ready nodes
    graph.add_edge("execute_node", "scheduler")

    # Scheduler conditionally ends or dispatches (handled by Send returns)
    graph.add_conditional_edges(
        "scheduler",
        lambda state: (
            END
            if state.get("error") is not None or not state.get("current_node_slug")
            else "execute_node"
        ),
        {END: END, "execute_node": "execute_node"},
    )

    return graph
