import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import String, cast, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.core.database import get_db
from app.models import School, Section, Student, User
from app.schemas import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


def item_or_404(item_id: int, db: Session) -> Student:
    item = db.get(Student, item_id)
    if not item: raise HTTPException(404, "Student not found")
    return item


@router.get("", response_model=list[StudentRead])
def list_students(search: str | None = None, school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Student).options(selectinload(Student.school))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Student.student_name.ilike(term), cast(Student.roll_number, String).ilike(term)))
    if school_id: query = query.filter(Student.school_id == school_id)
    if class_number: query = query.filter(Student.current_class == class_number)
    if section: query = query.filter(Student.current_section == section)
    return query.order_by(Student.roll_number).all()


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    item = Student(**payload.model_dump()); db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This roll number is already in use at this school")
    db.refresh(item); return item


@router.put("/{item_id}", response_model=StudentRead)
def update_student(item_id: int, payload: StudentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = item_or_404(item_id, db)
    if not db.get(School, payload.school_id): raise HTTPException(422, "School does not exist")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This roll number is already in use at this school")
    db.refresh(item); return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(item_or_404(item_id, db)); db.commit()


@router.post("/import")
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Upload a CSV file")
    rows = list(csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig"))))
    required = {"Roll Number", "Student Name", "School", "Class", "Section"}
    if not rows or not required.issubset(rows[0]):
        raise HTTPException(422, "CSV must contain: Roll Number, Student Name, School, Class, Section")

    errors: list[dict] = []
    students_to_create: list[Student] = []
    seen_roll_numbers: set[tuple[int, int]] = set()

    for idx, row in enumerate(rows, start=1):
        row_errors: list[str] = []

        # --- validate school ---------------------------------------------------
        school_name = row.get("School", "").strip()
        school = db.query(School).filter(School.name.ilike(school_name)).first() if school_name else None
        if not school:
            row_errors.append(f"School '{school_name}' not found")

        # --- validate roll number ----------------------------------------------
        roll_number: int | None = None
        roll_raw = row.get("Roll Number", "").strip()
        try:
            roll_number = int(roll_raw)
            if roll_number <= 0:
                row_errors.append("Roll Number must be a positive integer")
        except (ValueError, TypeError):
            row_errors.append(f"Roll Number '{roll_raw}' is not a valid integer")

        # --- validate student name ---------------------------------------------
        student_name = row.get("Student Name", "").strip()
        if not student_name:
            row_errors.append("Student Name is required")

        # --- validate class ----------------------------------------------------
        class_number: int | None = None
        class_raw = row.get("Class", "").strip()
        try:
            class_number = int(class_raw)
            if class_number not in (6, 7, 8):
                row_errors.append(f"Class must be 6, 7, or 8 (got {class_number})")
        except (ValueError, TypeError):
            row_errors.append(f"Class '{class_raw}' is not a valid integer")

        # --- validate section --------------------------------------------------
        section_name = row.get("Section", "").strip()
        if not section_name:
            row_errors.append("Section is required")
        elif school and class_number in (6, 7, 8):
            section_exists = db.query(Section.id).filter(
                Section.school_id == school.id,
                Section.class_number == class_number,
                Section.section_name.ilike(section_name),
            ).first()
            if not section_exists:
                row_errors.append(
                    f"Section '{section_name}' does not exist for class {class_number} at '{school.name}'"
                )

        # --- collect errors or stage student -----------------------------------
        if row_errors:
            errors.append({"row": idx, "errors": row_errors})
            continue

        roll_key = (school.id, roll_number)  # type: ignore[arg-type]
        if roll_key in seen_roll_numbers:
            errors.append({"row": idx, "errors": [f"Duplicate roll number {roll_number} for school '{school.name}' within CSV"]})
            continue
        seen_roll_numbers.add(roll_key)

        students_to_create.append(Student(
            school_id=school.id,
            roll_number=roll_number,  # type: ignore[arg-type]
            student_name=student_name,
            current_class=class_number,  # type: ignore[arg-type]
            current_section=section_name,
        ))

    created = 0
    if students_to_create:
        db.add_all(students_to_create)
        try:
            db.commit()
            created = len(students_to_create)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Import contains students that already exist in the database")

    return {"created": created, "skipped": len(rows) - created, "errors": errors}


@router.get("/export/csv")
def export_students(school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> StreamingResponse:
    students = list_students(school_id=school_id, class_number=class_number, section=section, db=db)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Roll Number", "Student Name", "School", "Class", "Section"])
    writer.writerows([[item.roll_number, item.student_name, item.school_name, item.current_class, item.current_section] for item in students])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=students.csv"})
