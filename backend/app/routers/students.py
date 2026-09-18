import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import School, Section, Student
from app.schemas import StudentCreate, StudentRead, StudentUpdate
from app.services.student_code import build_student_code

router = APIRouter(prefix="/students", tags=["Students"])


def item_or_404(item_id: int, db: Session) -> Student:
    item = db.get(Student, item_id)
    if not item: raise HTTPException(404, "Student not found")
    return item


def _build_code_for(school: School, student_name: str, class_number: int, db: Session) -> str:
    try:
        code = build_student_code(school.school_number, class_number, student_name)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    existing = db.query(Student.id).filter(Student.student_code == code).first()
    if existing:
        raise HTTPException(
            409,
            f"Student code '{code}' is already in use — student names must be unique within a school and class",
        )
    return code


@router.get("", response_model=list[StudentRead])
def list_students(search: str | None = None, school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Student).options(selectinload(Student.school))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Student.student_name.ilike(term), Student.student_code.ilike(term)))
    if school_id: query = query.filter(Student.school_id == school_id)
    if class_number: query = query.filter(Student.current_class == class_number)
    if section: query = query.filter(Student.current_section == section)
    return query.order_by(Student.student_code).all()


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    school = db.get(School, payload.school_id)
    if not school: raise HTTPException(422, "School does not exist")
    code = _build_code_for(school, payload.student_name, payload.current_class, db)
    item = Student(
        school_id=payload.school_id,
        student_code=code,
        student_name=payload.student_name,
        current_class=payload.current_class,
        current_section=payload.current_section,
    )
    db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This student already exists (code conflict)")
    db.refresh(item); return item


@router.put("/{item_id}", response_model=StudentRead)
def update_student(item_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    item = item_or_404(item_id, db)
    school = db.get(School, payload.school_id)
    if not school: raise HTTPException(422, "School does not exist")
    identity_changed = (
        item.school_id != payload.school_id
        or item.student_name != payload.student_name
        or item.current_class != payload.current_class
    )
    if identity_changed:
        code = _build_code_for(school, payload.student_name, payload.current_class, db)
        item.student_code = code
    item.school_id = payload.school_id
    item.student_name = payload.student_name
    item.current_class = payload.current_class
    item.current_section = payload.current_section
    try:
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "This student already exists (code conflict)")
    db.refresh(item); return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(item_id: int, db: Session = Depends(get_db)):
    db.delete(item_or_404(item_id, db)); db.commit()


@router.post("/import")
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(422, "Upload a CSV file")
    rows = list(csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig"))))
    required = {"Student Name", "School", "Class", "Section"}
    if not rows or not required.issubset(rows[0]):
        raise HTTPException(422, "CSV must contain: Student Name, School, Class, Section")

    errors: list[dict] = []
    students_to_create: list[Student] = []
    seen_codes: set[str] = set()

    for idx, row in enumerate(rows, start=1):
        row_errors: list[str] = []

        # --- validate school ---------------------------------------------------
        school_name = row.get("School", "").strip()
        school = db.query(School).filter(School.name.ilike(school_name)).first() if school_name else None
        if not school:
            row_errors.append(f"School '{school_name}' not found")

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

        try:
            code = build_student_code(school.school_number, class_number, student_name)  # type: ignore[arg-type]
        except ValueError:
            errors.append({"row": idx, "errors": ["Student Name must contain letters or digits"]})
            continue
        if code in seen_codes:
            errors.append({"row": idx, "errors": [f"Duplicate student code {code} within CSV"]})
            continue
        seen_codes.add(code)

        students_to_create.append(Student(
            school_id=school.id,
            student_code=code,
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
            raise HTTPException(409, "Import contains students whose codes already exist in the database")

    return {"created": created, "skipped": len(rows) - created, "errors": errors}


@router.get("/export/csv")
def export_students(school_id: int | None = None, class_number: int | None = None, section: str | None = None, db: Session = Depends(get_db)) -> StreamingResponse:
    students = list_students(school_id=school_id, class_number=class_number, section=section, db=db)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Student Code", "Student Name", "School", "Class", "Section"])
    writer.writerows([[item.student_code, item.student_name, item.school_name, item.current_class, item.current_section] for item in students])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=students.csv"})
