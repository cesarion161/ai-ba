"""Full analysis composite template — combines all branches with cross-branch dependencies."""

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

FULL_ANALYSIS = WorkflowTemplate(
    key="full_analysis",
    label="Full Business Analysis",
    nodes=[
        # ===== Market Research Branch =====
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
        # ===== Product Strategy Branch =====
        NodeTemplate(
            slug="product_questions",
            label="Product Strategy Questions",
            branch="product_strategy",
            node_type=NodeType.ASK_USER,
            depends_on=["lean_canvas_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What are the core features of your product?",
                    "What is your monetization strategy?",
                    "What is your product's key differentiator?",
                ]
            },
        ),
        NodeTemplate(
            slug="feature_research",
            label="Feature Landscape Research",
            branch="product_strategy",
            node_type=NodeType.RESEARCH,
            depends_on=["product_questions"],
            config={"tool": "tavily", "focus": "features"},
        ),
        NodeTemplate(
            slug="pricing_research",
            label="Pricing Model Research",
            branch="product_strategy",
            node_type=NodeType.RESEARCH,
            depends_on=["product_questions"],
            config={"tool": "tavily", "focus": "pricing"},
        ),
        NodeTemplate(
            slug="product_roadmap",
            label="Product Roadmap",
            branch="product_strategy",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["feature_research", "pricing_research"],
            config={"template": "product_roadmap"},
        ),
        NodeTemplate(
            slug="product_roadmap_critic",
            label="Product Roadmap Review",
            branch="product_strategy",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["product_roadmap"],
            config={"max_cycles": 2},
        ),
        # ===== UX & Requirements Branch =====
        NodeTemplate(
            slug="ux_questions",
            label="UX & Requirements Questions",
            branch="ux_requirements",
            node_type=NodeType.ASK_USER,
            depends_on=["lean_canvas_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "Who are the primary user personas?",
                    "What are the critical user journeys?",
                    "What platforms should be supported?",
                ]
            },
        ),
        NodeTemplate(
            slug="ux_research",
            label="UX Best Practices Research",
            branch="ux_requirements",
            node_type=NodeType.RESEARCH,
            depends_on=["ux_questions"],
            config={"tool": "tavily", "focus": "ux_patterns"},
        ),
        NodeTemplate(
            slug="user_stories",
            label="User Stories Document",
            branch="ux_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["ux_research"],
            config={"template": "user_stories"},
        ),
        NodeTemplate(
            slug="user_stories_critic",
            label="User Stories Review",
            branch="ux_requirements",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["user_stories"],
            config={"max_cycles": 2},
        ),
        # ===== Technical Architecture Branch =====
        NodeTemplate(
            slug="tech_questions",
            label="Technical Questions",
            branch="technical_architecture",
            node_type=NodeType.ASK_USER,
            depends_on=["product_roadmap_critic", "user_stories_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What is your team's tech stack expertise?",
                    "What are your scalability requirements?",
                    "Are there integration requirements?",
                ]
            },
        ),
        NodeTemplate(
            slug="tech_stack_research",
            label="Tech Stack Research",
            branch="technical_architecture",
            node_type=NodeType.RESEARCH,
            depends_on=["tech_questions"],
            config={"tool": "tavily", "focus": "technology"},
        ),
        NodeTemplate(
            slug="architecture_doc",
            label="Architecture Document",
            branch="technical_architecture",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["tech_stack_research"],
            config={"template": "architecture"},
        ),
        NodeTemplate(
            slug="architecture_critic",
            label="Architecture Review",
            branch="technical_architecture",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["architecture_doc"],
            config={"max_cycles": 2},
        ),
        # ===== Execution Planning Branch =====
        NodeTemplate(
            slug="execution_questions",
            label="Execution Planning Questions",
            branch="execution_planning",
            node_type=NodeType.ASK_USER,
            depends_on=["architecture_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What is your team size?",
                    "What is your total budget?",
                    "What is your target launch date?",
                ]
            },
        ),
        NodeTemplate(
            slug="cost_estimation",
            label="Cost Estimation",
            branch="execution_planning",
            node_type=NodeType.CALCULATE,
            depends_on=["execution_questions"],
            config={"calculation": "cost_estimation"},
        ),
        NodeTemplate(
            slug="execution_plan",
            label="Execution Plan Document",
            branch="execution_planning",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["cost_estimation"],
            config={"template": "execution_plan"},
        ),
        NodeTemplate(
            slug="execution_plan_critic",
            label="Execution Plan Review",
            branch="execution_planning",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["execution_plan"],
            config={"max_cycles": 2},
        ),
        # ===== Densification Branch =====
        NodeTemplate(
            slug="densify_developer",
            label="Densify for Developer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                "lean_canvas_critic",
                "product_roadmap_critic",
                "user_stories_critic",
                "architecture_critic",
                "execution_plan_critic",
            ],
            config={"role": "developer"},
        ),
        NodeTemplate(
            slug="densify_designer",
            label="Densify for Designer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                "lean_canvas_critic",
                "product_roadmap_critic",
                "user_stories_critic",
                "architecture_critic",
                "execution_plan_critic",
            ],
            config={"role": "designer"},
        ),
        NodeTemplate(
            slug="densify_pm",
            label="Densify for Product Manager",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                "lean_canvas_critic",
                "product_roadmap_critic",
                "user_stories_critic",
                "architecture_critic",
                "execution_plan_critic",
            ],
            config={"role": "product_manager"},
        ),
        # ===== Export Branch =====
        NodeTemplate(
            slug="format_export",
            label="Format & Export Archive",
            branch="export",
            node_type=NodeType.FORMAT_EXPORT,
            depends_on=["densify_developer", "densify_designer", "densify_pm"],
            requires_approval=False,
            config={"format": "zip"},
        ),
    ],
)
