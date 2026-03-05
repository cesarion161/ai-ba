import pytest

from app.engine.handlers import stubs  # noqa: F401 — registers all stubs
from app.engine.handlers.base import NODE_HANDLERS, get_handler
from app.models.workflow_node import NodeType


def test_all_handlers_registered():
    for nt in NodeType:
        assert nt in NODE_HANDLERS, f"No handler registered for {nt.value}"


@pytest.mark.asyncio
async def test_research_stub():
    handler = get_handler(NodeType.RESEARCH)
    result = await handler.execute(None, {})
    assert "summary" in result
    assert "sources" in result


@pytest.mark.asyncio
async def test_calculate_stub():
    handler = get_handler(NodeType.CALCULATE)
    result = await handler.execute(None, {})
    assert "result" in result


@pytest.mark.asyncio
async def test_generate_document_stub():
    handler = get_handler(NodeType.GENERATE_DOCUMENT)
    result = await handler.execute(None, {})
    assert "document" in result


@pytest.mark.asyncio
async def test_ask_user_stub():
    config = {"questions": ["Q1?", "Q2?"]}
    handler = get_handler(NodeType.ASK_USER)
    result = await handler.execute(config, {})
    assert result["questions"] == ["Q1?", "Q2?"]
    assert result["awaiting_answers"] is True


@pytest.mark.asyncio
async def test_critic_review_stub():
    handler = get_handler(NodeType.CRITIC_REVIEW)
    result = await handler.execute(None, {})
    assert "verdict" in result
    assert "score" in result


@pytest.mark.asyncio
async def test_densify_stub():
    handler = get_handler(NodeType.DENSIFY)
    result = await handler.execute(None, {})
    assert "densified" in result


@pytest.mark.asyncio
async def test_format_export_stub():
    handler = get_handler(NodeType.FORMAT_EXPORT)
    result = await handler.execute(None, {})
    assert "archive_url" in result
