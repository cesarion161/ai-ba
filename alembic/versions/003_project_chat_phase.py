"""project_chat_phase

Revision ID: 003
Revises: 002
Create Date: 2026-03-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: str = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("chat_phase", sa.String(50), nullable=True))
    op.add_column("projects", sa.Column("selected_doc_types", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "selected_doc_types")
    op.drop_column("projects", "chat_phase")
