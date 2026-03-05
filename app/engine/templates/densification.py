from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

DENSIFICATION = WorkflowTemplate(
    key="densification",
    label="Densification",
    nodes=[
        NodeTemplate(
            slug="densify_developer",
            label="Densify for Developer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            config={"role": "developer"},
        ),
        NodeTemplate(
            slug="densify_designer",
            label="Densify for Designer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            config={"role": "designer"},
        ),
        NodeTemplate(
            slug="densify_pm",
            label="Densify for Product Manager",
            branch="densification",
            node_type=NodeType.DENSIFY,
            config={"role": "product_manager"},
        ),
    ],
)
