import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import AssessmentType, AttemptStatus, ProcessingFileStatus, ProcessingSessionStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SchoolBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class SchoolCreate(SchoolBase): pass
class SchoolUpdate(SchoolBase): pass
class SchoolRead(SchoolBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    student_count: int
    section_count: int


class AcademicYearBase(BaseModel):
    name: str = Field(min_length=1, max_length=20)


class AcademicYearCreate(AcademicYearBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Must be in YYYY-YY format (e.g. 2026-27)")
        return v


class AcademicYearUpdate(AcademicYearBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Must be in YYYY-YY format (e.g. 2026-27)")
        return v


class AcademicYearRead(AcademicYearBase, ORMModel):
    id: int


class SectionBase(BaseModel):
    school_id: int
    class_number: int = Field(ge=6, le=8)
    section_name: str = Field(min_length=1, max_length=20)


class SectionCreate(SectionBase): pass
class SectionBulkCreate(BaseModel):
    school_id: int
    class_number: int = Field(ge=6, le=8)
    section_names: str = Field(min_length=1, max_length=500)
class SectionUpdate(SectionBase): pass
class SectionRead(SectionBase, ORMModel): id: int


class StudentBase(BaseModel):
    school_id: int
    roll_number: int = Field(gt=0)
    student_name: str = Field(min_length=1, max_length=200)
    current_class: int = Field(ge=6, le=8)
    current_section: str = Field(min_length=1, max_length=20)


class StudentCreate(StudentBase): pass
class StudentUpdate(StudentBase): pass
class StudentRead(StudentBase, ORMModel):
    id: int
    school_name: str


class QuestionInput(BaseModel):
    question_number: int = Field(ge=1, le=40)
    question_text: str | None = Field(default=None, max_length=500)
    option_a: str | None = Field(default=None, max_length=200)
    option_b: str | None = Field(default=None, max_length=200)
    option_c: str | None = Field(default=None, max_length=200)
    option_d: str | None = Field(default=None, max_length=200)
    correct_option: str = Field(pattern="^[A-D]$")
    domain: str = Field(min_length=1, max_length=100)


class AssessmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    assessment_type: AssessmentType
    academic_year_id: int
    class_number: int = Field(ge=6, le=8)


class AssessmentCreate(AssessmentBase):
    questions: list[QuestionInput] = Field(default=[], max_length=40)


class AssessmentUpdate(AssessmentBase): pass
class QuestionRead(QuestionInput, ORMModel): id: int
class AssessmentRead(AssessmentBase, ORMModel):
    id: int
    is_deleted: bool
    questions: list[QuestionRead] = []


# ── Processing Schemas ─────────────────────────────────────────────


class AssessmentSummary(ORMModel):
    """Read-only assessment metadata for processing sessions."""
    id: int
    name: str
    assessment_type: AssessmentType
    academic_year_name: str
    class_number: int
    question_count: int


class SchoolSummary(ORMModel):
    """Read-only school metadata for processing sessions."""
    id: int
    name: str
    student_count: int


class AttemptQuestionRead(ORMModel):
    id: int
    attempt_id: int
    question_id: int
    detected_answer: str | None
    correct_answer: str
    is_correct: bool
    domain: str


class AttemptRead(ORMModel):
    id: int
    assessment_id: int
    student_id: int
    processing_session_id: int
    score: int
    total_questions: int
    percentage: float
    status: AttemptStatus
    created_at: datetime
    completed_at: datetime | None
    questions: list[AttemptQuestionRead] = []


class ProcessingFileRead(ORMModel):
    id: int
    session_id: int
    original_filename: str
    roll_number: int
    student_id: int | None
    student_name: str | None = None
    status: ProcessingFileStatus
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    attempt: AttemptRead | None = None


class ProcessingSessionRead(ORMModel):
    id: int
    assessment_id: int
    school_id: int
    status: ProcessingSessionStatus
    total_files: int
    valid_files: int
    invalid_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    assessment: AssessmentSummary
    school: SchoolSummary
    files: list[ProcessingFileRead] = []


class ProcessingSessionListRead(ORMModel):
    """Lighter version for list views — no files array."""
    id: int
    assessment_id: int
    school_id: int
    status: ProcessingSessionStatus
    total_files: int
    valid_files: int
    invalid_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    assessment: AssessmentSummary
    school: SchoolSummary


class ProcessingProgressRead(ORMModel):
    session_id: int
    status: ProcessingSessionStatus
    total: int
    processed: int
    successful: int
    failed: int
    remaining: int


class RetryRequest(BaseModel):
    file_ids: list[int] = Field(min_length=1)


# ── Analytics Schemas ──────────────────────────────────────────────


class DomainBreakdown(BaseModel):
    domain: str
    correct: int
    total: int
    percentage: float


class SchoolSummaryForAnalytics(BaseModel):
    school_id: int
    school_name: str
    students_assessed: int
    average_score: float
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float
    domains: list[DomainBreakdown]
    school_rank: int


class StudentInSchool(BaseModel):
    student_id: int
    student_name: str
    roll_number: int
    score: int
    total_questions: int
    percentage: float


class AssessmentOverviewResponse(BaseModel):
    assessment_id: int
    total_students_assessed: int
    average_score: float
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float
    domains: list[DomainBreakdown]
    schools: list[SchoolSummaryForAnalytics]


class SchoolAnalyticsResponse(BaseModel):
    assessment_id: int
    school_id: int
    school_name: str
    students_assessed: int
    average_score: float
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float
    domains: list[DomainBreakdown]
    school_rank: int | None
    students: list[StudentInSchool]


class StudentAnalyticsResponse(BaseModel):
    assessment_id: int
    student_id: int
    student_name: str
    roll_number: int
    school_id: int
    school_name: str
    current_class: int
    current_section: str
    score: int
    total_questions: int
    wrong: int
    percentage: float
    domains: list[DomainBreakdown]
    school_domains: list[DomainBreakdown]
    overall_domains: list[DomainBreakdown]
    school_average: float
    overall_average: float
    school_rank: int
    overall_rank: int
    school_percentile: float
    overall_percentile: float
    assessment_name: str
    assessment_type: AssessmentType
    academic_year_name: str


# ── M7: Student Report Question-Level Schemas ─────────────────────


class StudentReportQuestionItem(BaseModel):
    question_number: int
    question_text: str | None
    domain: str
    detected_answer: str | None
    correct_answer: str
    is_correct: bool
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    percent_correct: float = 0.0


class StudentReportQuestionsResponse(BaseModel):
    assessment_id: int
    student_id: int
    questions: list[StudentReportQuestionItem]


# ── Auth Schemas ───────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class InviteRequest(BaseModel):
    email: str
    role: str = "user"


class InvitationRead(ORMModel):
    id: int
    email: str
    role: str
    is_used: bool
    expires_at: datetime
    created_at: datetime


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str
    full_name: str


class UserUpdateRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None


# ── M6B: Question Analytics Schemas ────────────────────────────────


class QuestionAnalyticsItem(BaseModel):
    question_id: int
    question_number: int
    question_text: str | None
    domain: str
    assessed: int
    correct: int
    wrong: int
    percentage: float


class QuestionAnalyticsScope(BaseModel):
    school_id: int | None = None
    class_number: int | None = None
    section: str | None = None


class QuestionAnalyticsResponse(BaseModel):
    assessment_id: int
    total_students_assessed: int
    scope: QuestionAnalyticsScope
    questions: list[QuestionAnalyticsItem]


class HistoricalAppearance(BaseModel):
    assessment_id: int
    assessment_name: str
    academic_year: str
    assessment_type: str
    question_number: int
    assessed: int
    correct: int
    percentage: float


class QuestionHistoryCurrent(BaseModel):
    assessment_id: int
    assessment_name: str
    academic_year: str
    assessment_type: str
    question_number: int
    assessed: int
    correct: int
    percentage: float


class QuestionHistoryResponse(BaseModel):
    question_id: int
    question_number: int
    question_text: str | None
    domain: str
    fingerprint_valid: bool
    fingerprint_match_count: int
    current: QuestionHistoryCurrent
    history: list[HistoricalAppearance]
