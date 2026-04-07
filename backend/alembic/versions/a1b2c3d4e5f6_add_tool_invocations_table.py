"""Add tool_invocations table

Revision ID: a1b2c3d4e5f6
Revises: 7e4a4c965825
Create Date: 2026-04-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7e4a4c965825"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool_invocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(50), nullable=False),
        sa.Column("tool_input", sa.Text, nullable=False),
        sa.Column("tool_output", postgresql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_tool_invocation_message_id",
        "tool_invocations",
        ["message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tool_invocation_message_id", table_name="tool_invocations")
    op.drop_table("tool_invocations")
