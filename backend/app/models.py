from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssessmentType(str, Enum):
    BASELINE = "Baseline"
    ENDLINE = "Endline"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class School(TimestampMixin, Base):
    __tablename__ = "schools"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    students: Mapped[list["Student"]] = relationship(back_populates="school")
    sections: Mapped[list["Section"]] = relationship(back_populates="school")

    @property
    def student_count(self) -> int:
        return len(self.students)

    @property
    def section_count(self) -> int:
        return len(self.sections)


class AcademicYear(TimestampMixin, Base):
    __tablename__ = "academic_years"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(9), unique=True, index=True)


class Section(TimestampMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("school_id", "class_number", "section_name", name="uq_section"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    class_number: Mapped[int] = mapped_column(Integer)
    section_name: Mapped[str] = mapped_column(String(20))
    school: Mapped[School] = relationship(back_populates="sections")


class Student(TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("school_id", "roll_number", name="uq_student_school_roll"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    roll_number: Mapped[int] = mapped_column(Integer, index=True)
    student_name: Mapped[str] = mapped_column(String(200))
    current_class: Mapped[int] = mapped_column(Integer)
    current_section: Mapped[str] = mapped_column(String(20))
    school: Mapped[School] = relationship(back_populates="students")

    @property
    def school_name(self) -> str:
        return self.school.name


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    assessment_type: Mapped[AssessmentType] = mapped_column(SqlEnum(AssessmentType))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"), index=True)
    class_number: Mapped[int] = mapped_column(Integer, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    questions: Mapped[list["Question"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("assessment_id", "question_number", name="uq_question_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    question_number: Mapped[int] = mapped_column(Integer)
    correct_option: Mapped[str] = mapped_column(String(1))
    domain: Mapped[str] = mapped_column(String(100))
    assessment: Mapped[Assessment] = relationship(back_populates="questions")
