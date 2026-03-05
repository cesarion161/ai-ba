import pytest

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.engine.templates.market_research import MARKET_RESEARCH
from app.engine.templates.registry import TEMPLATE_REGISTRY, get_template
from app.models.workflow_node import NodeType


def test_market_research_template_valid():
    assert MARKET_RESEARCH.key == "market_research"
    assert len(MARKET_RESEARCH.nodes) == 6


def test_template_root_slugs():
    roots = MARKET_RESEARCH.root_slugs()
    assert roots == ["intake_questions"]


def test_template_cycle_detection():
    with pytest.raises(ValueError, match="Cycle detected"):
        WorkflowTemplate(
            key="bad",
            label="Bad",
            nodes=[
                NodeTemplate(
                    slug="a",
                    label="A",
                    branch="x",
                    node_type=NodeType.RESEARCH,
                    depends_on=["b"],
                ),
                NodeTemplate(
                    slug="b",
                    label="B",
                    branch="x",
                    node_type=NodeType.RESEARCH,
                    depends_on=["a"],
                ),
            ],
        )


def test_template_duplicate_slug():
    with pytest.raises(ValueError, match="Duplicate slug"):
        WorkflowTemplate(
            key="bad",
            label="Bad",
            nodes=[
                NodeTemplate(
                    slug="a",
                    label="A",
                    branch="x",
                    node_type=NodeType.RESEARCH,
                ),
                NodeTemplate(
                    slug="a",
                    label="A2",
                    branch="x",
                    node_type=NodeType.RESEARCH,
                ),
            ],
        )


def test_template_bad_dependency():
    with pytest.raises(ValueError, match="does not exist"):
        WorkflowTemplate(
            key="bad",
            label="Bad",
            nodes=[
                NodeTemplate(
                    slug="a",
                    label="A",
                    branch="x",
                    node_type=NodeType.RESEARCH,
                    depends_on=["nonexistent"],
                ),
            ],
        )


def test_registry():
    assert "market_research" in TEMPLATE_REGISTRY
    assert get_template("market_research") is MARKET_RESEARCH


def test_registry_missing():
    with pytest.raises(KeyError):
        get_template("nonexistent")
