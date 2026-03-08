from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

TECHNICAL_ARCHITECTURE = WorkflowTemplate(
    key="technical_architecture",
    label="Technical Architecture",
    nodes=[
        NodeTemplate(
            slug="tech_questions",
            label="Technical Architecture Questions",
            branch="technical_architecture",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe the product and its core functionality.",
                    "What is your team's technical expertise? (Languages, frameworks, cloud platforms)",
                    "What are your scalability requirements? (Expected users at launch, 6 months, 1 year)",
                    "What external systems or APIs must be integrated?",
                    "What are your availability/uptime requirements?",
                    "Are there data residency or compliance constraints on infrastructure?",
                    "What is your infrastructure budget?",
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
            config={"template": "architecture", "branch": "technical_architecture"},
        ),
        NodeTemplate(
            slug="architecture_critic",
            label="Architecture Review",
            branch="technical_architecture",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["architecture_doc"],
            config={"max_cycles": 2, "branch": "technical_architecture"},
        ),
    ],
)
