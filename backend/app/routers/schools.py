from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import School
from app.schemas import SchoolCreate, SchoolRead, SchoolUpdate

router = APIRouter(prefix="/schools", tags=["Schools"])


def school_or_404(school_id: int, db: Session) -> School:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(404, "School not found")
    return school


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db)) -> list[School]:
    return db.query(School).options(selectinload(School.students), selectinload(School.sections)).order_by(School.name).all()


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db)) -> School:
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
def get_school(school_id: int, db: Session = Depends(get_db)) -> School:
    return db.query(School).options(selectinload(School.students), selectinload(School.sections)).filter(School.id == school_id).first() or school_or_404(school_id, db)


@router.put("/{school_id}", response_model=SchoolRead)
def update_school(school_id: int, payload: SchoolUpdate, db: Session = Depends(get_db)) -> School:
    school = school_or_404(school_id, db)
    school.name = payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A school with this name already exists")
    db.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: int, db: Session = Depends(get_db)) -> None:
    school = school_or_404(school_id, db)
    if school.students:
        raise HTTPException(409, "Cannot delete a school that has students")
    db.delete(school); db.commit()
