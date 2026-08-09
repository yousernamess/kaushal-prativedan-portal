from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models import AssessmentType


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
    name: str = Field(pattern=r"^\d{4}-\d{2}$")


class AcademicYearCreate(AcademicYearBase): pass
class AcademicYearUpdate(AcademicYearBase): pass
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
