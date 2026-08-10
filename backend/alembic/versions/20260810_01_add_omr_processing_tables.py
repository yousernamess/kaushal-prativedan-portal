"""Add OMR processing session and file tables.

Revision ID: 20260810_01
Revises: 20260809_01
Create Date: 2026-08-10 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260810_01"
down_revision = "20260809_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL — values must match Python Enum names (UPPERCASE)
    # because SQLAlchemy's SqlEnum persists the enum name, not the value.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE processingsessionstatus AS ENUM (
                'PENDING', 'VALIDATING', 'READY', 'PROCESSING', 'COMPLETED', 'PARTIAL', 'FAILED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE processingfilestatus AS ENUM (
                'PENDING', 'VALID', 'INVALID', 'PROCESSED', 'FAILED', 'RETRYING'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # processing_sessions table
    op.create_table(
        "processing_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("valid_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("invalid_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("processed_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("successful_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_files", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ps_assessment_id", "processing_sessions", ["assessment_id"])
    op.create_index("ix_ps_school_id", "processing_sessions", ["school_id"])

    # processing_files table
    op.create_table(
        "processing_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("processing_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("roll_number", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_pf_session_id", "processing_files", ["session_id"])
    op.create_index("ix_pf_student_id", "processing_files", ["student_id"])


def downgrade() -> None:
    op.drop_table("processing_files")
    op.drop_table("processing_sessions")
    op.execute("DROP TYPE IF EXISTS processingfilestatus")
    op.execute("DROP TYPE IF EXISTS processingsessionstatus")
