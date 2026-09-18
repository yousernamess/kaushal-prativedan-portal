import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import AcademicYear, Assessment, Question, QuestionDomain
from app.schemas import AssessmentCreate, AssessmentRead, AssessmentUpdate, QuestionInput, QuestionRead

# CSV column order (also serves as the export template header row).
CSV_COLUMNS = ["question_number", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "domain"]


def _escape_cell(value) -> str:
    """Normalize a value for CSV output; returns empty string for None."""
    return "" if value is None else str(value).replace("\n", " ").strip()


def _question_rows(assessment: Assessment) -> list[dict[str, str]]:
    """Render an assessment's questions as ordered dict rows for CSV export."""
    rows = []
    for q in sorted(assessment.questions, key=lambda x: x.question_number):
        rows.append({col: _escape_cell(getattr(q, col)) for col in CSV_COLUMNS})
    return rows


def _parse_question_rows(rows: list[dict]) -> list[QuestionInput]:
    """Validate raw CSV rows into QuestionInput objects."""
    questions: list[QuestionInput] = []
    for idx, raw in enumerate(rows, start=2):  # 1-indexed with header on row 1
        if not any((raw.get(k) for k in CSV_COLUMNS if k != "question_text")):
            continue  # skip fully-blank lines
        number_raw = str(raw.get("question_number", "")).strip()
        if not number_raw:
            raise HTTPException(422, f"Row {idx}: question_number is required")
        try:
            number = int(number_raw)
        except ValueError:
            raise HTTPException(422, f"Row {idx}: question_number must be an integer")
        correct = str(raw.get("correct_option", "")).strip().upper()
        if correct not in ("A", "B", "C", "D"):
            raise HTTPException(422, f"Row {idx}: correct_option must be A, B, C or D")
        domain = str(raw.get("domain", "")).strip()
        if not domain:
            raise HTTPException(422, f"Row {idx}: domain is required")
        domain = _canonical_domain(domain, idx)
        questions.append(
            QuestionInput(
                question_number=number,
                question_text=_escape_cell(raw.get("question_text")) or None,
                option_a=_escape_cell(raw.get("option_a")) or None,
                option_b=_escape_cell(raw.get("option_b")) or None,
                option_c=_escape_cell(raw.get("option_c")) or None,
                option_d=_escape_cell(raw.get("option_d")) or None,
                correct_option=correct,
                domain=domain,
            )
        )
    return questions

def _canonical_domain(value: str, row_idx: int) -> str:
    """Map a CSV domain cell to one of the 3 canonical domains (case-insensitive)."""
    lowered = value.strip().lower()
    for domain in QuestionDomain:
        if lowered == domain.value.lower():
            return domain.value
    allowed = ", ".join(QuestionDomain.values())
    raise HTTPException(422, f"Row {row_idx}: domain must be one of: {allowed}")


router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/domains", response_model=list[str])
def list_domains() -> list[str]:
    """The 3 canonical assessment domains."""
    return QuestionDomain.values()


def assessment_or_404(assessment_id: int, db: Session, include_deleted: bool = False) -> Assessment:
    query = db.query(Assessment).options(selectinload(Assessment.questions)).filter(Assessment.id == assessment_id)
    if not include_deleted:
        query = query.filter(Assessment.is_deleted.is_(False))
    item = query.first()
    if not item:
        raise HTTPException(404, "Assessment not found")
    return item


def validate_questions(questions: list[QuestionInput]) -> None:
    numbers = [question.question_number for question in questions]
    if len(numbers) != len(set(numbers)):
        raise HTTPException(422, "Question numbers must be unique")


@router.get("", response_model=list[AssessmentRead])
def list_assessments(academic_year_id: int | None = None, class_number: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Assessment).options(selectinload(Assessment.questions)).filter(Assessment.is_deleted.is_(False))
    if academic_year_id: query = query.filter(Assessment.academic_year_id == academic_year_id)
    if class_number: query = query.filter(Assessment.class_number == class_number)
    return query.order_by(Assessment.created_at.desc()).all()


@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    if not db.get(AcademicYear, payload.academic_year_id):
        raise HTTPException(422, "Academic year does not exist")
    validate_questions(payload.questions)
    data = payload.model_dump(exclude={"questions"})
    assessment = Assessment(**data)
    assessment.questions = [Question(**question.model_dump()) for question in payload.questions]
    db.add(assessment); db.commit()
    return assessment_or_404(assessment.id, db)


@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    return assessment_or_404(assessment_id, db)


@router.put("/{assessment_id}", response_model=AssessmentRead)
def update_assessment(assessment_id: int, payload: AssessmentUpdate, db: Session = Depends(get_db)):
    assessment = assessment_or_404(assessment_id, db)
    if not db.get(AcademicYear, payload.academic_year_id): raise HTTPException(422, "Academic year does not exist")
    for key, value in payload.model_dump().items(): setattr(assessment, key, value)
    db.commit()
    return assessment_or_404(assessment_id, db)


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = assessment_or_404(assessment_id, db)
    assessment.is_deleted = True
    db.commit()


@router.post("/{assessment_id}/duplicate", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def duplicate_assessment(assessment_id: int, db: Session = Depends(get_db)):
    source = assessment_or_404(assessment_id, db)
    duplicate = Assessment(name=f"{source.name} (Copy)", assessment_type=source.assessment_type, academic_year_id=source.academic_year_id, class_number=source.class_number)
    duplicate.questions = [Question(question_number=q.question_number, correct_option=q.correct_option, domain=q.domain) for q in source.questions]
    db.add(duplicate); db.commit()
    return assessment_or_404(duplicate.id, db)


@router.post("/{assessment_id}/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def add_question(assessment_id: int, payload: QuestionInput, db: Session = Depends(get_db)):
    assessment = assessment_or_404(assessment_id, db)
    if len(assessment.questions) >= 40: raise HTTPException(422, "An assessment cannot have more than 40 questions")
    if any(q.question_number == payload.question_number for q in assessment.questions): raise HTTPException(409, "Question number already exists")
    item = Question(assessment_id=assessment_id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@router.put("/questions/{question_id}", response_model=QuestionRead)
def update_question(question_id: int, payload: QuestionInput, db: Session = Depends(get_db)):
    item = db.get(Question, question_id)
    if not item: raise HTTPException(404, "Question not found")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    db.commit(); db.refresh(item); return item


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    item = db.get(Question, question_id)
    if not item: raise HTTPException(404, "Question not found")
    db.delete(item); db.commit()


@router.get("/{assessment_id}/export", tags=["Assessments"])
def export_assessment_csv(assessment_id: int, db: Session = Depends(get_db)):
    """Export an assessment's questions as a downloadable CSV template."""
    assessment = assessment_or_404(assessment_id, db)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(_question_rows(assessment))

    filename = "".join(ch for ch in assessment.name.lower() if ch.isalnum() or ch in ("-", "_")) or "assessment"
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}-questions.csv"'},
    )


@router.post("/{assessment_id}/import", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def import_assessment_csv(assessment_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Replace an assessment's questions from an uploaded CSV file (matching the export template)."""
    assessment = assessment_or_404(assessment_id, db)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Please upload a .csv file")

    raw = file.file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "CSV must be UTF-8 encoded")

    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception:
        raise HTTPException(422, "Could not parse CSV file")

    questions = _parse_question_rows(rows)
    if not questions:
        raise HTTPException(422, "CSV contains no questions")
    if len(questions) > 40:
        raise HTTPException(422, "An assessment cannot have more than 40 questions")
    validate_questions(questions)

    # Replace existing questions
    assessment.questions = [Question(**q.model_dump()) for q in questions]
    db.commit()
    return assessment_or_404(assessment_id, db)
