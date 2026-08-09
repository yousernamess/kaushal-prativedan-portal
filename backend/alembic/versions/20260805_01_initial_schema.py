"""Create initial portal schema.

Revision ID: 20260805_01
Revises:
Create Date: 2026-08-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20260805_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    assessment_type = sa.Enum("BASELINE", "ENDLINE", name="assessmenttype")
    op.create_table("schools", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_index("ix_schools_name", "schools", ["name"], unique=True)
    op.create_table("academic_years", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(9), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_index("ix_academic_years_name", "academic_years", ["name"], unique=True)
    op.create_table("sections", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False), sa.Column("class_number", sa.Integer(), nullable=False), sa.Column("section_name", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.UniqueConstraint("school_id", "class_number", "section_name", name="uq_section"))
    op.create_index("ix_sections_school_id", "sections", ["school_id"])
    op.create_table("students", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False), sa.Column("roll_number", sa.Integer(), nullable=False), sa.Column("student_name", sa.String(200), nullable=False), sa.Column("current_class", sa.Integer(), nullable=False), sa.Column("current_section", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.UniqueConstraint("school_id", "roll_number", name="uq_student_school_roll"))
    op.create_index("ix_students_school_id", "students", ["school_id"]); op.create_index("ix_students_roll_number", "students", ["roll_number"])
    op.create_table("assessments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("assessment_type", assessment_type, nullable=False), sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False), sa.Column("class_number", sa.Integer(), nullable=False), sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_index("ix_assessments_name", "assessments", ["name"]); op.create_index("ix_assessments_academic_year_id", "assessments", ["academic_year_id"]); op.create_index("ix_assessments_class_number", "assessments", ["class_number"])
    op.create_table("questions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False), sa.Column("question_number", sa.Integer(), nullable=False), sa.Column("correct_option", sa.String(1), nullable=False), sa.Column("domain", sa.String(100), nullable=False), sa.UniqueConstraint("assessment_id", "question_number", name="uq_question_number"))
    op.create_index("ix_questions_assessment_id", "questions", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("questions"); op.drop_table("assessments"); op.drop_table("students"); op.drop_table("sections"); op.drop_table("academic_years"); op.drop_table("schools")
    sa.Enum(name="assessmenttype").drop(op.get_bind(), checkfirst=True)
