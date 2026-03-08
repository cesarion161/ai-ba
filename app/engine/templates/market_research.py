from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

MARKET_RESEARCH = WorkflowTemplate(
    key="market_research",
    label="Market Research & Viability",
    nodes=[
        NodeTemplate(
            slug="intake_questions",
            label="Discovery & Intake Questions",
            branch="market_research",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe your product or service idea in detail. What does it do?",
                    "What specific problem does it solve, and how painful is this problem today?",
                    "Who is your target customer? (Role, company size, industry)",
                    "What alternatives or competitors exist today?",
                    "Why now? What market or technology shift makes this the right time?",
                    "What is your expected pricing model and price range?",
                    "What constraints already exist? (Budget, timeline, regulations, team size)",
                    "What would make this project fail? (Top 3 risks)",
                ]
            },
        ),
        NodeTemplate(
            slug="web_search",
            label="Market & Industry Research",
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
            label="Market Sizing (TAM/SAM/SOM)",
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
            config={"template": "lean_canvas", "branch": "market_research"},
        ),
        NodeTemplate(
            slug="lean_canvas_critic",
            label="Lean Canvas Review",
            branch="market_research",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["lean_canvas"],
            config={"max_cycles": 2, "branch": "market_research"},
        ),
        NodeTemplate(
            slug="feasibility_assessment",
            label="Feasibility Assessment",
            branch="market_research",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["lean_canvas_critic"],
            config={"template": "feasibility", "branch": "market_research"},
        ),
        NodeTemplate(
            slug="feasibility_critic",
            label="Feasibility Review",
            branch="market_research",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["feasibility_assessment"],
            config={"max_cycles": 2, "branch": "market_research"},
        ),
    ],
)
