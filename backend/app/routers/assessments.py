from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import AcademicYear, Assessment, Question
from app.schemas import AssessmentCreate, AssessmentRead, AssessmentUpdate, QuestionInput, QuestionRead

router = APIRouter(prefix="/assessments", tags=["Assessments"])


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
