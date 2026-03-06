from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatRole
from app.services import audit_service

logger = structlog.get_logger()


async def save_message(
    session: AsyncSession,
    project_id: uuid.UUID,
    role: ChatRole,
    content: str,
    metadata: dict | None = None,
) -> ChatMessage:
    msg = ChatMessage(
        project_id=project_id,
        role=role,
        content=content,
        metadata_=metadata,
    )
    session.add(msg)
    await session.flush()
    return msg


async def get_history(
    session: AsyncSession,
    project_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChatMessage], int]:
    count_result = await session.execute(
        select(func.count()).where(ChatMessage.project_id == project_id)
    )
    total = count_result.scalar_one()

    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    messages = list(result.scalars().all())
    return messages, total


async def get_history_as_dicts(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict[str, str]]:
    """Get chat history formatted for LLM consumption."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def save_user_message(
    session: AsyncSession,
    project_id: uuid.UUID,
    user_content: str,
) -> ChatMessage:
    """Save user message and return it."""
    user_msg = await save_message(session, project_id, ChatRole.USER, user_content)
    await audit_service.record(
        session,
        "chat_message",
        "chat",
        project_id=project_id,
        details={"role": "user"},
    )
    await session.commit()
    await session.refresh(user_msg)
    return user_msg


def _sse_event(event: str, data: dict) -> dict:
    """Format an SSE event dict for sse-starlette."""
    return {"event": event, "data": json.dumps(data)}


async def stream_response_events(
    project_id: uuid.UUID,
    session: AsyncSession,
) -> AsyncIterator[dict]:
    """Yield SSE event dicts: assistant_token and assistant_done."""
    from app.models.project import Project
    from app.services.llm_gateway import llm_gateway

    project = await session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    history = await get_history_as_dicts(session, project_id)
    phase = project.chat_phase or "gathering_requirements"

    # Non-streaming phases: emit canned reply as single token + done
    if phase == "selecting_documents":
        content = (
            "Please select the document types you'd like generated using the document selector. "
            "Once you've made your selections, click **Confirm** to proceed."
        )
        yield _sse_event("assistant_token", {"token": content})
        msg = await _save_assistant(session, project_id, content)
        yield _sse_event("assistant_done", {"id": str(msg.id), "content": content})
        return

    if phase == "generating_graph":
        content = "I'm currently generating your workflow graph. Please wait..."
        yield _sse_event("assistant_token", {"token": content})
        msg = await _save_assistant(session, project_id, content)
        yield _sse_event("assistant_done", {"id": str(msg.id), "content": content})
        return

    if phase not in ("gathering_requirements", "graph_ready", "executing", "completed"):
        content = "I'm ready to help. What would you like to analyze?"
        yield _sse_event("assistant_token", {"token": content})
        msg = await _save_assistant(session, project_id, content)
        yield _sse_event("assistant_done", {"id": str(msg.id), "content": content})
        return

    # Streaming phases: call LLM
    from app.engine.agents.initial_analysis import InitialAnalysisAgent

    agent = InitialAnalysisAgent()

    try:
        system_prompt = _get_system_prompt()
    except Exception:
        system_prompt = agent._default_system_prompt()

    messages = [{"role": "system", "content": system_prompt}] + history

    full_content = ""
    try:
        async for token in llm_gateway.complete_stream(messages=messages, task_type="chat"):
            full_content += token
            yield _sse_event("assistant_token", {"token": token})
    except Exception:
        logger.exception("stream_response_error", project_id=str(project_id))
        if not full_content:
            full_content = await llm_gateway.complete(messages=messages, task_type="chat")
            yield _sse_event("assistant_token", {"token": full_content})

    # Check requirements completeness for gathering phase
    if phase == "gathering_requirements":
        completeness = await agent.is_requirements_complete(history)
        if completeness["complete"]:
            suffix = (
                "\n\n---\n**I have enough information to proceed.** "
                "Now let's select the document types you'd like me to generate. "
                "I'll show you the available options."
            )
            full_content += suffix
            yield _sse_event("assistant_token", {"token": suffix})
            project.chat_phase = "selecting_documents"
            await session.flush()

    # Save the complete assistant message
    msg = await _save_assistant(session, project_id, full_content)
    yield _sse_event("assistant_done", {"id": str(msg.id), "content": full_content})


async def _save_assistant(
    session: AsyncSession,
    project_id: uuid.UUID,
    content: str,
) -> ChatMessage:
    """Save assistant message, commit, and publish to event_bus."""
    from app.services.event_bus import event_bus

    assistant_msg = await save_message(session, project_id, ChatRole.ASSISTANT, content)
    await session.commit()
    await session.refresh(assistant_msg)
    # Notify other SSE listeners (e.g. project stream for sidebar)
    await event_bus.publish(
        str(project_id),
        "chat.message",
        {"role": "assistant", "content": content, "id": str(assistant_msg.id)},
    )
    return assistant_msg


def _get_system_prompt() -> str:
    from app.services.prompt_engine import prompt_engine

    return prompt_engine.render("chat/initial_analysis")
