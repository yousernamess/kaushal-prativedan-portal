"""Add question text and options to questions table.

Revision ID: 20260809_01
Revises: 20260805_01
Create Date: 2026-08-09 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260809_01"
down_revision = "20260805_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("question_text", sa.String(500), nullable=True))
    op.add_column("questions", sa.Column("option_a", sa.String(200), nullable=True))
    op.add_column("questions", sa.Column("option_b", sa.String(200), nullable=True))
    op.add_column("questions", sa.Column("option_c", sa.String(200), nullable=True))
    op.add_column("questions", sa.Column("option_d", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "option_d")
    op.drop_column("questions", "option_c")
    op.drop_column("questions", "option_b")
    op.drop_column("questions", "option_a")
    op.drop_column("questions", "question_text")
