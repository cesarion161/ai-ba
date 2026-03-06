"""Chat API endpoints for conversational project creation."""

from __future__ import annotations

import json
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    DocumentSelectionRequest,
    ProjectFromChatRequest,
)
from app.models.database import get_db, async_session
from app.services import audit_service, chat_service, document_type_service
from app.services.event_bus import event_bus

logger = structlog.get_logger()

router = APIRouter(prefix="/api/projects", tags=["chat"])

PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/from-chat", response_model=ChatMessageResponse, status_code=201)
async def create_project_from_chat(
    body: ProjectFromChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Create a new project from an initial chat prompt."""
    from app.models.chat import ChatRole
    from app.models.project import Project

    # Derive name from prompt if not provided
    name = body.name or body.initial_prompt[:80].strip()
    if len(body.initial_prompt) > 80:
        name = name.rsplit(" ", 1)[0] + "..."

    project = Project(
        user_id=PLACEHOLDER_USER_ID,
        name=name,
        description=body.initial_prompt,
        template_key="chat_driven",
        chat_phase="gathering_requirements",
    )
    db.add(project)
    await db.flush()

    await audit_service.record(
        db,
        "create",
        "project",
        entity_id=project.id,
        project_id=project.id,
        user_id=PLACEHOLDER_USER_ID,
        details={"source": "chat"},
    )

    # Save initial user message
    await chat_service.save_message(db, project.id, ChatRole.USER, body.initial_prompt)

    # Get AI response
    from app.engine.agents.initial_analysis import InitialAnalysisAgent

    agent = InitialAnalysisAgent()
    history = [{"role": "user", "content": body.initial_prompt}]
    response_content = await agent.process_message(history, body.initial_prompt)

    assistant_msg = await chat_service.save_message(
        db, project.id, ChatRole.ASSISTANT, response_content
    )
    await db.commit()
    await db.refresh(assistant_msg)

    # Return the assistant's response with project_id
    return ChatMessageResponse.model_validate(assistant_msg)


@router.post("/{project_id}/chat")
async def send_chat_message(
    project_id: uuid.UUID,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Send a message and stream the AI response.

    Returns an SSE stream:
      - event: user_message   (the saved user message)
      - event: assistant_token (each streamed token)
      - event: assistant_done  (final saved assistant message)
    """
    from app.services import project_service

    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save user message in the request-scoped session
    user_msg = await chat_service.save_user_message(db, project_id, body.content)
    user_msg_data = ChatMessageResponse.model_validate(user_msg).model_dump(mode="json")

    async def event_generator():  # type: ignore[no-untyped-def]
        # 1. Emit saved user message so frontend can replace its optimistic one
        yield {"event": "user_message", "data": json.dumps(user_msg_data)}

        # 2. Stream AI response tokens, then the final saved message
        async with async_session() as bg_session:
            try:
                async for sse_event in chat_service.stream_response_events(
                    project_id, bg_session
                ):
                    yield sse_event
            except Exception:
                logger.exception("stream_error", project_id=str(project_id))

    return EventSourceResponse(event_generator())


@router.get("/{project_id}/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    project_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """Get paginated chat history."""
    messages, total = await chat_service.get_history(db, project_id, limit, offset)
    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total,
        has_more=offset + limit < total,
    )


@router.post("/{project_id}/chat/select-documents", response_model=ChatMessageResponse)
async def select_documents(
    project_id: uuid.UUID,
    body: DocumentSelectionRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Receive selected doc types, trigger graph generation."""
    from app.engine.agents.graph_generator import GraphGeneratorAgent
    from app.models.chat import ChatRole
    from app.services import project_service
    from app.services.graph_builder_service import build_graph_from_json

    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.chat_phase != "selecting_documents":
        raise HTTPException(status_code=400, detail=f"Invalid phase: {project.chat_phase}")

    # Validate doc type keys
    for key in body.doc_type_keys:
        dt = await document_type_service.get_by_key(db, key)
        if not dt:
            raise HTTPException(status_code=400, detail=f"Unknown document type: {key}")

    project.selected_doc_types = body.doc_type_keys
    project.chat_phase = "generating_graph"
    await db.flush()

    # Save selection as chat message
    selected_labels = ", ".join(body.doc_type_keys)
    await chat_service.save_message(
        db,
        project_id,
        ChatRole.USER,
        f"Selected documents: {selected_labels}",
        metadata={"type": "doc_selection", "keys": body.doc_type_keys},
    )

    # Generate graph
    generator = GraphGeneratorAgent()
    history = await chat_service.get_history_as_dicts(db, project_id)
    requirements = await generator.reorganize_requirements(history, body.doc_type_keys)
    graph_json = await generator.generate_graph(requirements, body.doc_type_keys)

    # Build graph in DB
    await build_graph_from_json(db, project_id, graph_json)

    project.chat_phase = "graph_ready"
    await db.flush()

    # Save confirmation message
    node_count = len(graph_json["nodes"])
    response_content = (
        f"I've generated a workflow with **{node_count} nodes** based on your selections. "
        "You can review and edit the graph, then click **Run** to start the analysis."
    )
    assistant_msg = await chat_service.save_message(
        db, project_id, ChatRole.ASSISTANT, response_content
    )

    await audit_service.record(
        db,
        "generate_graph",
        "project",
        entity_id=project_id,
        project_id=project_id,
        details={"node_count": node_count, "doc_types": body.doc_type_keys},
    )

    await db.commit()
    await db.refresh(assistant_msg)

    await event_bus.publish(
        str(project_id),
        "graph.generated",
        {"node_count": node_count, "phase": "graph_ready"},
    )

    return ChatMessageResponse.model_validate(assistant_msg)
