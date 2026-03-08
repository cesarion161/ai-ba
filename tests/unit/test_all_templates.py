"""Verify all registered templates are valid and consistent."""

from app.engine.templates.registry import TEMPLATE_REGISTRY
from app.models.workflow_node import NodeType


def test_all_templates_valid():
    """Every template in the registry should pass validation (no cycles, no missing deps)."""
    assert len(TEMPLATE_REGISTRY) >= 8
    for key, template in TEMPLATE_REGISTRY.items():
        assert template.key == key
        assert len(template.nodes) > 0
        # Validation runs in __post_init__, so if we get here, it passed


def test_full_analysis_has_all_branches():
    full = TEMPLATE_REGISTRY["full_analysis"]
    branches = {n.branch for n in full.nodes}
    expected = {
        "market_research",
        "business_requirements",
        "product_strategy",
        "ux_requirements",
        "technical_architecture",
        "execution_planning",
        "delivery",
        "densification",
        "export",
    }
    assert branches == expected


def test_full_analysis_single_root():
    full = TEMPLATE_REGISTRY["full_analysis"]
    roots = full.root_slugs()
    assert roots == ["intake_questions"]


def test_full_analysis_export_is_terminal():
    """format_export should have no downstream dependents."""
    full = TEMPLATE_REGISTRY["full_analysis"]
    export_slug = "format_export"
    # No node should depend on format_export
    for node in full.nodes:
        assert export_slug not in node.depends_on, (
            f"Node '{node.slug}' depends on terminal node '{export_slug}'"
        )


def test_all_node_types_used_in_full_analysis():
    full = TEMPLATE_REGISTRY["full_analysis"]
    types_used = {n.node_type for n in full.nodes}
    assert types_used == set(NodeType)


def test_all_prompts_render():
    """Verify all prompt templates referenced by market_research branch render."""
    from app.services.prompt_engine import prompt_engine

    templates_to_test = [
        (
            "market_research/web_search",
            {"business_idea": "X", "target_audience": "Y", "user_feedback": None},
        ),
        (
            "market_research/competitor_analysis",
            {"business_idea": "X", "known_competitors": ["A"], "user_feedback": None},
        ),
        (
            "market_research/market_sizing",
            {"research_data": "data", "business_context": "ctx"},
        ),
        (
            "market_research/lean_canvas",
            {
                "research_summary": "r",
                "competitor_analysis": "c",
                "market_sizing": "m",
                "user_answers": "a",
                "user_feedback": None,
            },
        ),
        (
            "product_strategy/product_roadmap",
            {
                "product_overview": "p",
                "feature_research": "f",
                "pricing_research": "pr",
                "user_answers": "a",
                "user_feedback": None,
            },
        ),
        (
            "ux_requirements/user_stories",
            {
                "user_personas": "p",
                "user_journeys": "j",
                "platforms": "web",
                "ux_research": "r",
                "user_feedback": None,
            },
        ),
        (
            "technical_architecture/architecture",
            {
                "product_requirements": "r",
                "tech_expertise": "t",
                "scalability": "s",
                "integrations": "i",
                "tech_research": "tr",
                "user_feedback": None,
            },
        ),
        (
            "execution_planning/execution_plan",
            {
                "team_info": "t",
                "budget": "b",
                "timeline": "tl",
                "risks": "r",
                "cost_estimation": "c",
                "user_feedback": None,
            },
        ),
    ]

    # New templates added for business requirements, feasibility, and delivery
    new_templates = [
        (
            "market_research/feasibility",
            {
                "lean_canvas": "lc",
                "research_summary": "rs",
                "competitor_analysis": "ca",
                "market_sizing": "ms",
                "user_answers": "ua",
                "user_feedback": None,
            },
        ),
        (
            "business_requirements/brd",
            {
                "lean_canvas": "lc",
                "feasibility_assessment": "fa",
                "process_model": "pm",
                "business_rules": "br",
                "user_answers": "ua",
                "user_feedback": None,
            },
        ),
        (
            "business_requirements/business_rules",
            {
                "lean_canvas": "lc",
                "feasibility_assessment": "fa",
                "user_answers": "ua",
                "user_feedback": None,
            },
        ),
        (
            "business_requirements/process_model",
            {
                "lean_canvas": "lc",
                "feasibility_assessment": "fa",
                "user_answers": "ua",
                "user_feedback": None,
            },
        ),
        (
            "delivery/api_contracts",
            {
                "architecture_doc": "ad",
                "product_requirements": "pr",
                "user_stories": "us",
                "user_feedback": None,
            },
        ),
        (
            "delivery/data_model",
            {
                "architecture_doc": "ad",
                "product_requirements": "pr",
                "business_rules": "br",
                "user_feedback": None,
            },
        ),
        (
            "delivery/qa_strategy",
            {
                "product_requirements": "pr",
                "user_stories": "us",
                "architecture_doc": "ad",
                "nfr_context": "nfr",
                "execution_plan": "ep",
                "user_feedback": None,
            },
        ),
        (
            "delivery/traceability_matrix",
            {
                "lean_canvas": "lc",
                "brd": "brd",
                "product_roadmap": "prm",
                "user_stories": "us",
                "architecture_doc": "ad",
                "execution_plan": "ep",
                "qa_strategy": "qa",
                "user_feedback": None,
            },
        ),
    ]
    templates_to_test.extend(new_templates)

    for template_key, context in templates_to_test:
        result = prompt_engine.render(template_key, **context)
        assert len(result) > 50, f"Template '{template_key}' rendered too short"
