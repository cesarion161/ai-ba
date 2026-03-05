from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

MARKET_RESEARCH = WorkflowTemplate(
    key="market_research",
    label="Market Research",
    nodes=[
        NodeTemplate(
            slug="intake_questions",
            label="Intake Questions",
            branch="market_research",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "What is your product or service idea?",
                    "Who is your target audience?",
                    "What problem does it solve?",
                    "What is your expected price range?",
                    "Who are your known competitors?",
                ]
            },
        ),
        NodeTemplate(
            slug="web_search",
            label="Web Research",
            branch="market_research",
            node_type=NodeType.RESEARCH,
            depends_on=["intake_questions"],
            config={"tool": "tavily", "max_results": 10},
        ),
        NodeTemplate(
            slug="competitor_analysis",
            label="Competitor Analysis",
            branch="market_research",
            node_type=NodeType.RESEARCH,
            depends_on=["intake_questions"],
            config={"tool": "tavily", "focus": "competitors"},
        ),
        NodeTemplate(
            slug="market_sizing",
            label="Market Sizing",
            branch="market_research",
            node_type=NodeType.CALCULATE,
            depends_on=["web_search"],
            config={"calculation": "tam_sam_som"},
        ),
        NodeTemplate(
            slug="lean_canvas",
            label="Lean Canvas",
            branch="market_research",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["web_search", "competitor_analysis", "market_sizing"],
            config={"template": "lean_canvas"},
        ),
        NodeTemplate(
            slug="lean_canvas_critic",
            label="Lean Canvas Review",
            branch="market_research",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["lean_canvas"],
            config={"max_cycles": 2},
        ),
    ],
)
