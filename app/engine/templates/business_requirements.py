"""Business requirements standalone template — BRD, business rules, and process model."""

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

BUSINESS_REQUIREMENTS = WorkflowTemplate(
    key="business_requirements",
    label="Business Requirements Analysis",
    nodes=[
        NodeTemplate(
            slug="brd_questions",
            label="Business Requirements Questions",
            branch="business_requirements",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe your product or service idea in detail.",
                    "Describe the key business processes that the product will support or automate.",
                    "What business rules govern your domain? (e.g., approval thresholds, pricing rules, eligibility criteria)",
                    "What compliance or regulatory requirements apply?",
                    "Who are the key user roles and what actions can each role perform?",
                    "What are the critical data entities in your business?",
                    "What constraints exist? (Budget, timeline, regulations, technical limitations)",
                ]
            },
        ),
        NodeTemplate(
            slug="business_rules",
            label="Business Rules Catalog",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions"],
            config={"template": "business_rules", "branch": "business_requirements"},
        ),
        NodeTemplate(
            slug="process_model",
            label="Business Process Model",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions"],
            config={"template": "process_model", "branch": "business_requirements"},
        ),
        NodeTemplate(
            slug="brd",
            label="Business Requirements Document",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions", "business_rules", "process_model"],
            config={"template": "brd", "branch": "business_requirements"},
        ),
        NodeTemplate(
            slug="brd_critic",
            label="Business Requirements Review",
            branch="business_requirements",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["brd"],
            config={"max_cycles": 2, "branch": "business_requirements"},
        ),
    ],
)
