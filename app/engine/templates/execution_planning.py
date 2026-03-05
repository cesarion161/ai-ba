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
                    "What is your team size and composition?",
                    "What is your total budget?",
                    "What is your target launch date?",
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
    ],
)
