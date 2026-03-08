"""Delivery standalone template — API contracts, data model, QA strategy, traceability."""

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

DELIVERY = WorkflowTemplate(
    key="delivery",
    label="Delivery Documentation",
    nodes=[
        NodeTemplate(
            slug="delivery_questions",
            label="Delivery Documentation Questions",
            branch="delivery",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe the product architecture at a high level.",
                    "What are the core API endpoints or service interfaces?",
                    "What are the main data entities and their relationships?",
                    "What are the critical user stories and acceptance criteria?",
                    "What are the non-functional requirements? (Performance, security)",
                    "What is the team's testing approach and tooling preferences?",
                ]
            },
        ),
        NodeTemplate(
            slug="api_contracts",
            label="API & Event Contract Specification",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["delivery_questions"],
            config={"template": "api_contracts", "branch": "delivery"},
        ),
        NodeTemplate(
            slug="data_model_spec",
            label="Data Model Specification",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["delivery_questions"],
            config={"template": "data_model", "branch": "delivery"},
        ),
        NodeTemplate(
            slug="qa_strategy",
            label="QA & Test Strategy",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["delivery_questions"],
            config={"template": "qa_strategy", "branch": "delivery"},
        ),
        NodeTemplate(
            slug="traceability_matrix",
            label="Traceability Matrix",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["api_contracts", "data_model_spec", "qa_strategy"],
            config={"template": "traceability_matrix", "branch": "delivery"},
        ),
    ],
)
