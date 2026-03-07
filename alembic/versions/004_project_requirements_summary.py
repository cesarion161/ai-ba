"""project_requirements_summary

Revision ID: 004
Revises: 003
Create Date: 2026-03-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("requirements_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "requirements_summary")
