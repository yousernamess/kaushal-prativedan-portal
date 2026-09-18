from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import School, Section, Student
from app.schemas import SchoolCreate, SchoolRead, SchoolUpdate

router = APIRouter(prefix="/schools", tags=["Schools"])


def school_or_404(school_id: int, db: Session) -> School:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    return school


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db)) -> list[SchoolRead]:
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
            id=s.id, name=s.name, school_number=s.school_number,
            created_at=s.created_at, updated_at=s.updated_at,
            student_count=student_counts.get(s.id, 0),
            section_count=section_counts.get(s.id, 0),
        )
        for s in schools
    ]


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db)) -> School:
    if db.query(School.id).filter(func.lower(School.name) == payload.name.lower()).first():
        raise HTTPException(409, "A school with this name already exists")
    if db.query(School.id).filter(School.school_number == payload.school_number).first():
        raise HTTPException(409, "A school with this number already exists")
    school = School(**payload.model_dump())
    db.add(school)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A school with this name or number already exists")
    db.refresh(school)
    return school


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: int, db: Session = Depends(get_db)) -> SchoolRead:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    student_count = db.query(func.count(Student.id)).filter(Student.school_id == school_id).scalar() or 0
    section_count = db.query(func.count(Section.id)).filter(Section.school_id == school_id).scalar() or 0
    return SchoolRead(
        id=school.id, name=school.name, school_number=school.school_number,
        created_at=school.created_at, updated_at=school.updated_at,
        student_count=student_count, section_count=section_count,
    )


@router.put("/{school_id}", response_model=SchoolRead)
def update_school(school_id: int, payload: SchoolUpdate, db: Session = Depends(get_db)) -> School:
    school = school_or_404(school_id, db)
    if db.query(School.id).filter(func.lower(School.name) == payload.name.lower(), School.id != school_id).first():
        raise HTTPException(409, "A school with this name already exists")
    if db.query(School.id).filter(School.school_number == payload.school_number, School.id != school_id).first():
        raise HTTPException(409, "A school with this number already exists")
    school.name = payload.name
    number_changed = school.school_number != payload.school_number
    school.school_number = payload.school_number
    if number_changed:
        # Regenerate every student code of this school from the new number.
        from app.services.student_code import build_student_code
        for student in school.students:
            student.student_code = build_student_code(
                payload.school_number, student.current_class, student.student_name
            )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A school with this name or number already exists")
    db.refresh(school)
    return school


@router.delete("/{school_id}/students", status_code=status.HTTP_200_OK)
def delete_school_students(school_id: int, db: Session = Depends(get_db)) -> dict:
    """Bulk remove all students from a school."""
    school = school_or_404(school_id, db)
    count = db.query(func.count(Student.id)).filter(Student.school_id == school_id).scalar() or 0
    if count == 0:
        return {"deleted": 0}
    db.query(Student).filter(Student.school_id == school_id).delete()
    db.commit()
    return {"deleted": count}


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: int, force: bool = False, db: Session = Depends(get_db)) -> None:
    school = school_or_404(school_id, db)
    if school.students and not force:
        raise HTTPException(409, "Cannot delete a school that has students")
    if force:
        db.query(Student).filter(Student.school_id == school_id).delete()
        db.query(Section).filter(Section.school_id == school_id).delete()
    db.delete(school); db.commit()
