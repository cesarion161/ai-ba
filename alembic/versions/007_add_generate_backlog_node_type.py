"""add generate_backlog node type

Revision ID: 007
Revises: 006
Create Date: 2026-03-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'GENERATE_BACKLOG'")


def downgrade() -> None:
    op.execute(
        "UPDATE workflow_nodes SET node_type = 'generate_document' "
        "WHERE node_type = 'generate_backlog'"
    )
