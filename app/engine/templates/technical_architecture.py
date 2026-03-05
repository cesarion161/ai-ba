from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

TECHNICAL_ARCHITECTURE = WorkflowTemplate(
    key="technical_architecture",
    label="Technical Architecture",
    nodes=[
        NodeTemplate(
            slug="tech_questions",
            label="Technical Questions",
            branch="technical_architecture",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "What is your team's tech stack expertise?",
                    "What are your scalability requirements?",
                    "Are there integration requirements with existing systems?",
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
    ],
)
