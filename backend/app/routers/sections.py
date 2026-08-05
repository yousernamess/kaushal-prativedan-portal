from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models import School, Section
from app.schemas import SectionCreate, SectionRead, SectionUpdate

router = APIRouter(prefix="/sections", tags=["Sections"])


def item_or_404(item_id: int, db: Session) -> Section:
    item = db.get(Section, item_id)
    if not item: raise HTTPException(404, "Section not found")
    return item


@router.get("", response_model=list[SectionRead])
def list_sections(school_id: int | None = None, class_number: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Section)
    if school_id: query = query.filter(Section.school_id == school_id)
    if class_number: query = query.filter(Section.class_number == class_number)
    return query.order_by(Section.section_name).all()


@router.post("", response_model=SectionRead, status_code=status.HTTP_201_CREATED)
def create_section(payload: SectionCreate, db: Session = Depends(get_db)):
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    item = Section(**payload.model_dump()); db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This section already exists")
    db.refresh(item); return item


@router.put("/{item_id}", response_model=SectionRead)
def update_section(item_id: int, payload: SectionUpdate, db: Session = Depends(get_db)):
    item = item_or_404(item_id, db)
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    db.commit(); db.refresh(item); return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(item_id: int, db: Session = Depends(get_db)):
    db.delete(item_or_404(item_id, db)); db.commit()
