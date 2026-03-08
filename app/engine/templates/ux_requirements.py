from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

UX_REQUIREMENTS = WorkflowTemplate(
    key="ux_requirements",
    label="UX & Requirements",
    nodes=[
        NodeTemplate(
            slug="ux_questions",
            label="UX & Requirements Questions",
            branch="ux_requirements",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe your product and the problem it solves.",
                    "Describe your primary user personas. (Role, goals, frustrations)",
                    "What are the 3-5 critical user journeys? Walk through each step-by-step.",
                    "What platforms must be supported? (Web, iOS, Android, desktop, API-only)",
                    "What accessibility requirements apply? (WCAG level, screen reader support)",
                    "What does a successful first-time user experience look like?",
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
            config={"template": "user_stories", "branch": "ux_requirements"},
        ),
        NodeTemplate(
            slug="user_stories_critic",
            label="User Stories Review",
            branch="ux_requirements",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["user_stories"],
            config={"max_cycles": 2},
        ),
    ],
)
