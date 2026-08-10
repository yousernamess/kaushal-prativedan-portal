"""Analytics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AssessmentOverviewResponse,
    SchoolAnalyticsResponse,
    StudentAnalyticsResponse,
)
from app.services.analytics_service import (
    assessment_overview,
    school_analytics,
    student_analytics,
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
