from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.database import get_db
from app.models import AcademicYear, User
from app.schemas import AcademicYearCreate, AcademicYearRead, AcademicYearUpdate

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])


def item_or_404(item_id: int, db: Session) -> AcademicYear:
    item = db.get(AcademicYear, item_id)
    if not item: raise HTTPException(404, "Academic year not found")
    return item


@router.get("", response_model=list[AcademicYearRead])
def list_years(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AcademicYear).order_by(AcademicYear.name.desc()).all()


@router.post("", response_model=AcademicYearRead, status_code=status.HTTP_201_CREATED)
def create_year(payload: AcademicYearCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = AcademicYear(**payload.model_dump()); db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This academic year already exists")
    db.refresh(item); return item


@router.put("/{item_id}", response_model=AcademicYearRead)
def update_year(item_id: int, payload: AcademicYearUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = item_or_404(item_id, db)
    item.name = payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This academic year already exists")
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_year(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(item_or_404(item_id, db)); db.commit()
