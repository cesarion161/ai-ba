from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

EXPORT = WorkflowTemplate(
    key="export",
    label="Export",
    nodes=[
        NodeTemplate(
            slug="format_export",
            label="Format & Export Archive",
            branch="export",
            node_type=NodeType.FORMAT_EXPORT,
            requires_approval=False,
            config={"format": "zip"},
        ),
    ],
)
