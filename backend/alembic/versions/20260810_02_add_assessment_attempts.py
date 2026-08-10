"""Add assessment attempt and attempt question tables.

Revision ID: 20260810_02
Revises: 20260810_01
Create Date: 2026-08-10 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260810_02"
down_revision = "20260810_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create AttemptStatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE attemptstatus AS ENUM ('COMPLETED', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # assessment_attempts table
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("processing_session_id", sa.Integer(), sa.ForeignKey("processing_sessions.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("assessment_id", "student_id", name="uq_attempt_assessment_student"),
    )
    op.create_index("ix_aa_assessment_id", "assessment_attempts", ["assessment_id"])
    op.create_index("ix_aa_student_id", "assessment_attempts", ["student_id"])
    op.create_index("ix_aa_session_id", "assessment_attempts", ["processing_session_id"])

    # attempt_questions table
    op.create_table(
        "attempt_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("detected_answer", sa.String(1), nullable=True),
        sa.Column("correct_answer", sa.String(1), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )
    op.create_index("ix_aq_attempt_id", "attempt_questions", ["attempt_id"])
    op.create_index("ix_aq_question_id", "attempt_questions", ["question_id"])


def downgrade() -> None:
    op.drop_table("attempt_questions")
    op.drop_table("assessment_attempts")
    op.execute("DROP TYPE IF EXISTS attemptstatus")
