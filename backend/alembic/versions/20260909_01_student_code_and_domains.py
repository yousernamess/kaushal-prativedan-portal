"""Student codes, school numbers, and canonical assessment domains.

Revision ID: 20260909_01
Revises: 20260810_02
Create Date: 2026-09-09 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260909_01"
down_revision = "20260810_02"
branch_labels = None
depends_on = None

DOMAINS_SQL = "('Experiential Learning', 'Knowledge Base', 'Analytical')"


def upgrade() -> None:
    # ── Schools: manual 2-digit school number ──
    op.add_column(
        "schools",
        sa.Column("school_number", sa.Integer(), nullable=False),
    )
    op.create_unique_constraint("uq_school_number", "schools", ["school_number"])
    op.create_index("ix_schools_school_number", "schools", ["school_number"])

    # ── Students: replace sequential roll numbers with structured codes ──
    op.add_column(
        "students",
        sa.Column("student_code", sa.String(200), nullable=False, server_default=""),
    )
    op.create_unique_constraint("uq_student_code", "students", ["student_code"])
    op.create_index("ix_students_student_code", "students", ["student_code"])
    op.drop_constraint("uq_student_school_roll", "students", type_="unique")
    op.drop_index("ix_students_roll_number", table_name="students")
    op.drop_column("students", "roll_number")

    # ── Processing files: store the parsed student code instead of a roll number ──
    op.add_column(
        "processing_files",
        sa.Column("student_code", sa.String(200), nullable=True),
    )
    op.drop_column("processing_files", "roll_number")

    # ── Canonical assessment domains (exactly 3) ──
    op.create_check_constraint(
        "ck_question_domain",
        "questions",
        f"domain IN {DOMAINS_SQL}",
    )
    op.create_check_constraint(
        "ck_attempt_question_domain",
        "attempt_questions",
        f"domain IN {DOMAINS_SQL}",
    )


def downgrade() -> None:
    op.drop_constraint("ck_attempt_question_domain", "attempt_questions", type_="check")
    op.drop_constraint("ck_question_domain", "questions", type_="check")

    op.add_column(
        "processing_files",
        sa.Column("roll_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_column("processing_files", "student_code")

    op.add_column(
        "students",
        sa.Column("roll_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_index("ix_students_student_code", table_name="students")
    op.drop_constraint("uq_student_code", "students", type_="unique")
    op.drop_column("students", "student_code")
    op.create_index("ix_students_roll_number", "students", ["roll_number"])
    op.create_unique_constraint(
        "uq_student_school_roll", "students", ["school_id", "roll_number"]
    )

    op.drop_index("ix_schools_school_number", table_name="schools")
    op.drop_constraint("uq_school_number", "schools", type_="unique")
    op.drop_column("schools", "school_number")
