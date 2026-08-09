import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import String, cast, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import School, Student
from app.schemas import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


def item_or_404(item_id: int, db: Session) -> Student:
    item = db.get(Student, item_id)
    if not item: raise HTTPException(404, "Student not found")
    return item


@router.get("", response_model=list[StudentRead])
def list_students(search: str | None = None, school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Student).options(selectinload(Student.school))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Student.student_name.ilike(term), cast(Student.roll_number, String).ilike(term)))
    if school_id: query = query.filter(Student.school_id == school_id)
    if class_number: query = query.filter(Student.current_class == class_number)
    if section: query = query.filter(Student.current_section == section)
    return query.order_by(Student.roll_number).all()


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    item = Student(**payload.model_dump()); db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This roll number is already in use at this school")
    db.refresh(item); return item


@router.put("/{item_id}", response_model=StudentRead)
def update_student(item_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    item = item_or_404(item_id, db)
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This roll number is already in use at this school")
    db.refresh(item); return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(item_id: int, db: Session = Depends(get_db)):
    db.delete(item_or_404(item_id, db)); db.commit()


@router.post("/import")
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, int]:
    if not file.filename or not file.filename.lower().endswith(".csv"): raise HTTPException(422, "Upload a CSV file")
    rows = list(csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig"))))
    required = {"Roll Number", "Student Name", "School", "Class", "Section"}
    if not rows or not required.issubset(rows[0]): raise HTTPException(422, "CSV must contain: Roll Number, Student Name, School, Class, Section")
    created = 0
    for row in rows:
        try:
            school = db.query(School).filter(School.name.ilike(row["School"].strip())).first()
            if not school: continue
            payload = StudentCreate(school_id=school.id, roll_number=row["Roll Number"], student_name=row["Student Name"], current_class=row["Class"], current_section=row["Section"])
            db.add(Student(**payload.model_dump())); created += 1
        except (ValueError, KeyError): continue
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Import contains duplicate student roll numbers")
    return {"created": created, "skipped": len(rows) - created}


@router.get("/export/csv")
def export_students(school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db)) -> StreamingResponse:
    students = list_students(school_id=school_id, class_number=class_number, section=section, db=db)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Roll Number", "Student Name", "School", "Class", "Section"])
    writer.writerows([[item.roll_number, item.student_name, item.school_name, item.current_class, item.current_section] for item in students])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=students.csv"})
