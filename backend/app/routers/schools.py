from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.database import get_db
from app.models import School, Section, Student, User
from app.schemas import SchoolCreate, SchoolRead, SchoolUpdate

router = APIRouter(prefix="/schools", tags=["Schools"])


def school_or_404(school_id: int, db: Session) -> School:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    return school


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[SchoolRead]:
    schools = db.query(School).order_by(School.name).all()
    student_counts = dict(
        db.query(Student.school_id, func.count(Student.id))
        .group_by(Student.school_id).all()
    )
    section_counts = dict(
        db.query(Section.school_id, func.count(Section.id))
        .group_by(Section.school_id).all()
    )
    return [
        SchoolRead(
            id=s.id, name=s.name, created_at=s.created_at, updated_at=s.updated_at,
            student_count=student_counts.get(s.id, 0),
            section_count=section_counts.get(s.id, 0),
        )
        for s in schools
    ]


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> School:
    school = School(**payload.model_dump())
    db.add(school)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A school with this name already exists")
    db.refresh(school)
    return school


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> SchoolRead:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    student_count = db.query(func.count(Student.id)).filter(Student.school_id == school_id).scalar() or 0
    section_count = db.query(func.count(Section.id)).filter(Section.school_id == school_id).scalar() or 0
    return SchoolRead(
        id=school.id, name=school.name, created_at=school.created_at, updated_at=school.updated_at,
        student_count=student_count, section_count=section_count,
    )


@router.put("/{school_id}", response_model=SchoolRead)
def update_school(school_id: int, payload: SchoolUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> School:
    school = school_or_404(school_id, db)
    school.name = payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A school with this name already exists")
    db.refresh(school)
    return school


@router.delete("/{school_id}/students", status_code=status.HTTP_200_OK)
def delete_school_students(school_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    """Bulk remove all students from a school."""
    school = school_or_404(school_id, db)
    count = db.query(func.count(Student.id)).filter(Student.school_id == school_id).scalar() or 0
    if count == 0:
        return {"deleted": 0}
    db.query(Student).filter(Student.school_id == school_id).delete()
    db.commit()
    return {"deleted": count}


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: int, force: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    school = school_or_404(school_id, db)
    if school.students and not force:
        raise HTTPException(409, "Cannot delete a school that has students")
    if force:
        db.query(Student).filter(Student.school_id == school_id).delete()
        db.query(Section).filter(Section.school_id == school_id).delete()
    db.delete(school); db.commit()
