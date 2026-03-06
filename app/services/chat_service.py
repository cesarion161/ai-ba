from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatRole
from app.services import audit_service


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


async def send_and_respond(
    session: AsyncSession,
    project_id: uuid.UUID,
    user_content: str,
) -> ChatMessage:
    """Save user message, route to appropriate agent, save and return AI response."""
    from app.models.project import Project

    # Save user message
    await save_message(session, project_id, ChatRole.USER, user_content)
    await audit_service.record(
        session,
        "chat_message",
        "chat",
        project_id=project_id,
        details={"role": "user"},
    )

    # Get project to check phase
    project = await session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get chat history for LLM
    history = await get_history_as_dicts(session, project_id)

    # Route to appropriate agent based on chat_phase
    phase = project.chat_phase or "gathering_requirements"

    if phase == "gathering_requirements":
        from app.engine.agents.initial_analysis import InitialAnalysisAgent

        agent = InitialAnalysisAgent()
        response_content = await agent.process_message(history, user_content)

        # Check if requirements are complete
        completeness = await agent.is_requirements_complete(history)
        if completeness["complete"]:
            response_content += (
                "\n\n---\n**I have enough information to proceed.** "
                "Now let's select the document types you'd like me to generate. "
                "I'll show you the available options."
            )
            project.chat_phase = "selecting_documents"
            await session.flush()

    elif phase == "selecting_documents":
        response_content = (
            "Please select the document types you'd like generated using the document selector. "
            "Once you've made your selections, click **Confirm** to proceed."
        )

    elif phase == "generating_graph":
        response_content = "I'm currently generating your workflow graph. Please wait..."

    elif phase in ("graph_ready", "executing", "completed"):
        # Free-form chat in later phases — just respond helpfully
        from app.engine.agents.initial_analysis import InitialAnalysisAgent

        agent = InitialAnalysisAgent()
        response_content = await agent.process_message(history, user_content)

    else:
        response_content = "I'm ready to help. What would you like to analyze?"

    # Save assistant response
    assistant_msg = await save_message(session, project_id, ChatRole.ASSISTANT, response_content)
    await session.commit()
    await session.refresh(assistant_msg)
    return assistant_msg
