from datetime import datetime
from enum import Enum
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssessmentType(str, Enum):
    BASELINE = "Baseline"
    ENDLINE = "Endline"


class QuestionDomain(str, Enum):
    EXPERIENTIAL_LEARNING = "Experiential Learning"
    KNOWLEDGE_BASE = "Knowledge Base"
    ANALYTICAL = "Analytical"

    @classmethod
    def values(cls) -> list[str]:
        return [d.value for d in cls]


class ProcessingSessionStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ProcessingFileStatus(str, Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    INVALID = "INVALID"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class School(TimestampMixin, Base):
    __tablename__ = "schools"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    school_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
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
    __table_args__ = (UniqueConstraint("student_code", name="uq_student_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    student_code: Mapped[str] = mapped_column(String(200), unique=True, index=True)
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
    academic_year: Mapped[AcademicYear] = relationship()


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("assessment_id", "question_number", name="uq_question_number"),
        CheckConstraint(
            "domain IN ('Experiential Learning', 'Knowledge Base', 'Analytical')",
            name="ck_question_domain",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    question_number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    option_a: Mapped[str | None] = mapped_column(String(200), nullable=True)
    option_b: Mapped[str | None] = mapped_column(String(200), nullable=True)
    option_c: Mapped[str | None] = mapped_column(String(200), nullable=True)
    option_d: Mapped[str | None] = mapped_column(String(200), nullable=True)
    correct_option: Mapped[str] = mapped_column(String(1))
    domain: Mapped[str] = mapped_column(String(100))
    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class ProcessingSession(TimestampMixin, Base):
    __tablename__ = "processing_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    status: Mapped[ProcessingSessionStatus] = mapped_column(
        SqlEnum(ProcessingSessionStatus), default=ProcessingSessionStatus.PENDING
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    valid_files: Mapped[int] = mapped_column(Integer, default=0)
    invalid_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    successful_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped[Assessment] = relationship()
    school: Mapped[School] = relationship()
    files: Mapped[list["ProcessingFile"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    attempts: Mapped[list["AssessmentAttempt"]] = relationship(back_populates="processing_session")


class ProcessingFile(TimestampMixin, Base):
    __tablename__ = "processing_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("processing_sessions.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    student_code: Mapped[str | None] = mapped_column(String(200), nullable=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    status: Mapped[ProcessingFileStatus] = mapped_column(
        SqlEnum(ProcessingFileStatus), default=ProcessingFileStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped[ProcessingSession] = relationship(back_populates="files")
    student: Mapped[Student | None] = relationship()


class AttemptStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_attempt_assessment_student"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    processing_session_id: Mapped[int] = mapped_column(
        ForeignKey("processing_sessions.id"), index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    status: Mapped[AttemptStatus] = mapped_column(
        SqlEnum(AttemptStatus), default=AttemptStatus.COMPLETED
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assessment: Mapped[Assessment] = relationship()
    student: Mapped[Student] = relationship()
    processing_session: Mapped[ProcessingSession] = relationship()
    questions: Mapped[list["AttemptQuestion"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
        CheckConstraint(
            "domain IN ('Experiential Learning', 'Knowledge Base', 'Analytical')",
            name="ck_attempt_question_domain",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"), index=True
    )
    detected_answer: Mapped[str | None] = mapped_column(String(1), nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(1))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    domain: Mapped[str] = mapped_column(String(100))

    attempt: Mapped[AssessmentAttempt] = relationship(back_populates="questions")
    question: Mapped[Question] = relationship()
