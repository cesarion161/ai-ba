"""Import all models so SQLAlchemy can resolve relationships."""

from app.models.artifact import NodeArtifact  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.workflow_node import NodeEdge, WorkflowNode  # noqa: F401
