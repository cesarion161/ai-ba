import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class NodeStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(str, enum.Enum):
    RESEARCH = "research"
    CALCULATE = "calculate"
    GENERATE_DOCUMENT = "generate_document"
    ASK_USER = "ask_user"
    CRITIC_REVIEW = "critic_review"
    DENSIFY = "densify"
    FORMAT_EXPORT = "format_export"


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_project_node_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[NodeType] = mapped_column(nullable=False)
    status: Mapped[NodeStatus] = mapped_column(nullable=False, default=NodeStatus.PENDING)
    requires_approval: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=None)
    input_data: Mapped[dict | None] = mapped_column(JSONB, default=None)
    output_data: Mapped[dict | None] = mapped_column(JSONB, default=None)
    user_feedback: Mapped[str | None] = mapped_column(Text, default=None)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="nodes")  # noqa: F821
    artifacts: Mapped[list["NodeArtifact"]] = relationship(back_populates="node")  # noqa: F821

    # Edges where this node is the dependency (upstream)
    outgoing_edges: Mapped[list["NodeEdge"]] = relationship(
        foreign_keys="NodeEdge.from_node_id", back_populates="from_node"
    )
    # Edges where this node depends on another (downstream)
    incoming_edges: Mapped[list["NodeEdge"]] = relationship(
        foreign_keys="NodeEdge.to_node_id", back_populates="to_node"
    )


class NodeEdge(Base):
    __tablename__ = "node_edges"
    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", name="uq_edge"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False
    )

    from_node: Mapped["WorkflowNode"] = relationship(foreign_keys=[from_node_id])
    to_node: Mapped["WorkflowNode"] = relationship(foreign_keys=[to_node_id])
