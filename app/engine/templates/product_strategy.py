from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

PRODUCT_STRATEGY = WorkflowTemplate(
    key="product_strategy",
    label="Product Strategy",
    nodes=[
        NodeTemplate(
            slug="product_questions",
            label="Product Strategy Questions",
            branch="product_strategy",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "What are the core features of your product?",
                    "What is your monetization strategy?",
                    "What is your product's key differentiator?",
                    "What is your development timeline?",
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
    ],
)
