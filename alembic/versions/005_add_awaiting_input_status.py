"""add awaiting_input node status

Revision ID: 005
Revises: 004
Create Date: 2026-03-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "005"
down_revision: str = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE nodestatus ADD VALUE IF NOT EXISTS 'AWAITING_INPUT'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; convert any existing rows first
    op.execute("UPDATE workflow_nodes SET status = 'ready' WHERE status = 'awaiting_input'")
