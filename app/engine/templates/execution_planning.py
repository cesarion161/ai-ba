from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

EXECUTION_PLANNING = WorkflowTemplate(
    key="execution_planning",
    label="Execution Planning",
    nodes=[
        NodeTemplate(
            slug="execution_questions",
            label="Execution Planning Questions",
            branch="execution_planning",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe the product to be built and its core features.",
                    "What is your current team size and composition? (Engineers, designers, PMs, QA)",
                    "What is your total budget for the build phase? (Include range if uncertain)",
                    "What is your target launch date or timeline constraint?",
                    "Do you have existing infrastructure, CI/CD, or development environments?",
                    "What is your risk tolerance? (Aggressive timeline vs conservative with buffers)",
                    "What are the biggest risks you foresee?",
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
            config={"template": "execution_plan", "branch": "execution_planning"},
        ),
        NodeTemplate(
            slug="execution_plan_critic",
            label="Execution Plan Review",
            branch="execution_planning",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["execution_plan"],
            config={"max_cycles": 2, "branch": "execution_planning"},
        ),
    ],
)
