"""Analytics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AssessmentOverviewResponse,
    QuestionAnalyticsResponse,
    QuestionHistoryResponse,
    SchoolAnalyticsResponse,
    SchoolsComparisonResponse,
    StudentAnalyticsResponse,
    StudentReportQuestionsResponse,
)
from app.services.analytics_service import (
    assessment_overview,
    question_analytics,
    question_history,
    school_analytics,
    schools_comparison,
    student_analytics,
    student_report_questions,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/assessments/{assessment_id}/overview",
    response_model=AssessmentOverviewResponse,
)
def get_assessment_overview(
    assessment_id: int,
    school_id: int | None = Query(None),
    class_number: int | None = Query(None),
    section: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Assessment-wide analytics with optional school/class/section filters."""
    try:
        result = assessment_overview(
            db,
            assessment_id,
            school_id=school_id,
            class_number=class_number,
            section=section,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


@router.get(
    "/assessments/{assessment_id}/schools/{school_id}",
    response_model=SchoolAnalyticsResponse,
)
def get_school_analytics(
    assessment_id: int,
    school_id: int,
    db: Session = Depends(get_db),
):
    """Analytics for a specific school in a specific assessment."""
    try:
        result = school_analytics(db, assessment_id, school_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


@router.get(
    "/assessments/{assessment_id}/schools-comparison",
    response_model=SchoolsComparisonResponse,
)
def get_schools_comparison(
    assessment_id: int,
    db: Session = Depends(get_db),
):
    """Inter-school comparison: overall, domain-wise, and class-wise stats per school."""
    try:
        result = schools_comparison(db, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


@router.get(
    "/assessments/{assessment_id}/students/{student_id}",
    response_model=StudentAnalyticsResponse,
)
def get_student_analytics(
    assessment_id: int,
    student_id: int,
    db: Session = Depends(get_db),
):
    """Analytics for a specific student in a specific assessment."""
    try:
        result = student_analytics(db, assessment_id, student_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


# ── M6B: Question Analytics ────────────────────────────────────────


@router.get(
    "/assessments/{assessment_id}/questions",
    response_model=QuestionAnalyticsResponse,
)
def get_question_analytics(
    assessment_id: int,
    school_id: int | None = Query(None),
    class_number: int | None = Query(None),
    section: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Per-question analytics for an assessment with optional scope filters."""
    try:
        result = question_analytics(
            db, assessment_id,
            school_id=school_id, class_number=class_number, section=section,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


@router.get(
    "/assessments/{assessment_id}/questions/{question_id}/history",
    response_model=QuestionHistoryResponse,
)
def get_question_history(
    assessment_id: int,
    question_id: int,
    school_id: int | None = Query(None),
    class_number: int | None = Query(None),
    section: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Historical performance for a specific question across assessments."""
    try:
        result = question_history(
            db, assessment_id, question_id,
            school_id=school_id, class_number=class_number, section=section,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


# ── M7: Student Report Questions ──────────────────────────────────


@router.get(
    "/assessments/{assessment_id}/students/{student_id}/questions",
    response_model=StudentReportQuestionsResponse,
)
def get_student_report_questions(
    assessment_id: int,
    student_id: int,
    db: Session = Depends(get_db),
):
    """Per-question breakdown for a single student's attempt (M7 report)."""
    try:
        result = student_report_questions(db, assessment_id, student_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result
