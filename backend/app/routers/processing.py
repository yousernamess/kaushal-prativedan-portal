"""OMR Processing Session endpoints."""

import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.core.database import get_db
from app.models import (
    Assessment,
    AssessmentAttempt,
    AttemptQuestion,
    ProcessingFile,
    ProcessingFileStatus,
    ProcessingSession,
    ProcessingSessionStatus,
    School,
    Student,
    User,
)
from app.schemas import (
    ProcessingFileRead,
    ProcessingProgressRead,
    ProcessingSessionListRead,
    ProcessingSessionRead,
    RetryRequest,
)
from app.services.evaluation_service import evaluate_and_persist
from app.services.omr_service import OMRProcessingError, get_template_question_count

router = APIRouter(prefix="/processing-sessions", tags=["Processing Sessions"])

# ── Constants ──────────────────────────────────────────────────────

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "output" / "uploads"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}
FILENAME_REGEX = re.compile(r"^(\d+)\.(jpg|jpeg|png|bmp|tiff|pdf)$", re.IGNORECASE)
MAX_RETRY_COUNT = 3


# ── Helpers ────────────────────────────────────────────────────────


def _session_dir(session_id: int) -> Path:
    return UPLOAD_ROOT / f"session_{session_id}"


def _build_assessment_summary(assessment: Assessment) -> dict:
    academic_year_name = ""
    if assessment.academic_year:
        academic_year_name = assessment.academic_year.name
    return {
        "id": assessment.id,
        "name": assessment.name,
        "assessment_type": assessment.assessment_type.value,
        "academic_year_name": academic_year_name,
        "class_number": assessment.class_number,
        "question_count": len(assessment.questions),
    }


def _build_school_summary(school: School) -> dict:
    return {
        "id": school.id,
        "name": school.name,
        "student_count": len(school.students),
    }


def _file_to_dict(f: ProcessingFile) -> dict:
    # Find the attempt for this student in the current session's assessment
    attempt_dict = None
    if f.student_id and hasattr(f, '_attempt_data'):
        attempt_dict = f._attempt_data

    result = {
        "id": f.id,
        "session_id": f.session_id,
        "original_filename": f.original_filename,
        "roll_number": f.roll_number,
        "student_id": f.student_id,
        "student_name": f.student.student_name if f.student else None,
        "status": f.status.value,
        "error_message": f.error_message,
        "retry_count": f.retry_count,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
        "attempt": attempt_dict,
    }
    return result


def _session_to_dict(session: ProcessingSession, db: Session = None) -> dict:
    assessment = session.assessment
    school = session.school

    # Load attempts for this session to attach to files
    attempt_map: dict[int, dict] = {}
    if db:
        attempts = (
            db.query(AssessmentAttempt)
            .options(selectinload(AssessmentAttempt.questions))
            .filter(AssessmentAttempt.processing_session_id == session.id)
            .all()
        )
        for att in attempts:
            attempt_map[att.student_id] = {
                "id": att.id,
                "assessment_id": att.assessment_id,
                "student_id": att.student_id,
                "processing_session_id": att.processing_session_id,
                "score": att.score,
                "total_questions": att.total_questions,
                "percentage": float(att.percentage),
                "status": att.status.value,
                "created_at": att.created_at,
                "completed_at": att.completed_at,
                "questions": [
                    {
                        "id": q.id,
                        "attempt_id": q.attempt_id,
                        "question_id": q.question_id,
                        "detected_answer": q.detected_answer,
                        "correct_answer": q.correct_answer,
                        "is_correct": q.is_correct,
                        "domain": q.domain,
                    }
                    for q in att.questions
                ],
            }

    # Attach attempt data to files
    files = []
    for f in session.files:
        f._attempt_data = attempt_map.get(f.student_id) if f.student_id else None
        files.append(_file_to_dict(f))

    return {
        "id": session.id,
        "assessment_id": session.assessment_id,
        "school_id": session.school_id,
        "status": session.status.value,
        "total_files": session.total_files,
        "valid_files": session.valid_files,
        "invalid_files": session.invalid_files,
        "processed_files": session.processed_files,
        "successful_files": session.successful_files,
        "failed_files": session.failed_files,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "assessment": _build_assessment_summary(assessment),
        "school": _build_school_summary(school),
        "files": files,
    }


def _load_session(session_id: int, db: Session) -> ProcessingSession:
    session = (
        db.query(ProcessingSession)
        .options(
            selectinload(ProcessingSession.assessment)
            .selectinload(Assessment.questions),
            selectinload(ProcessingSession.school)
            .selectinload(School.students),
            selectinload(ProcessingSession.files)
            .selectinload(ProcessingFile.student),
        )
        .filter(ProcessingSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(404, "Processing session not found")
    return session


def _update_counters(session: ProcessingSession, db: Session) -> None:
    """Recalculate session counters from file statuses."""
    files = session.files
    session.total_files = len(files)
    session.valid_files = sum(1 for f in files if f.status != ProcessingFileStatus.INVALID)
    session.invalid_files = sum(1 for f in files if f.status == ProcessingFileStatus.INVALID)
    session.processed_files = sum(
        1 for f in files if f.status in (ProcessingFileStatus.PROCESSED, ProcessingFileStatus.FAILED)
    )
    session.successful_files = sum(1 for f in files if f.status == ProcessingFileStatus.PROCESSED)
    session.failed_files = sum(1 for f in files if f.status == ProcessingFileStatus.FAILED)


# ── OMR Processor (M5 real implementation) ─────────────────────────


def process_single_omr_file(
    db: Session,
    *,
    file_path: Path,
    question_count: int,
    session_id: int,
    file_id: int,
    assessment: Assessment,
    student: Student,
) -> dict:
    """Run OMR extraction + evaluation for a single file.

    Returns:
        {"success": True, "result": {...}}  — score, total, percentage, attempt_id
        {"success": False, "error": "..."}   — failure reason

    This function does NOT commit the transaction.  The caller is responsible
    for committing after all files in the batch are processed.  Each file's
    evaluation runs in a savepoint so a single failure doesn't roll back
    previously-succeeded files in the same batch.
    """
    savepoint = db.begin_nested()  # SAVEPOINT
    try:
        result = evaluate_and_persist(
            db,
            assessment=assessment,
            student=student,
            processing_session_id=session_id,
            file_path=file_path,
        )
        savepoint.commit()

        # Clean up the uploaded image on success
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass  # Non-fatal: file may already be gone

        return {"success": True, "result": result}

    except OMRProcessingError as e:
        savepoint.rollback()
        return {"success": False, "error": str(e)}
    except Exception as e:
        savepoint.rollback()
        return {"success": False, "error": f"Unexpected error: {type(e).__name__}: {e}"}


# ── Endpoints ──────────────────────────────────────────────────────


@router.post("", response_model=ProcessingSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    assessment_id: int,
    school_id: int,
    files: list[UploadFile],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── Validate assessment ──
    assessment = (
        db.query(Assessment)
        .options(selectinload(Assessment.questions), selectinload(Assessment.academic_year))
        .filter(Assessment.id == assessment_id, Assessment.is_deleted.is_(False))
        .first()
    )
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # ── Validate school ──
    school = (
        db.query(School)
        .options(selectinload(School.students))
        .filter(School.id == school_id)
        .first()
    )
    if not school:
        raise HTTPException(404, "School not found")

    # ── Validate files present ──
    if not files:
        raise HTTPException(422, "No files uploaded")

    # ── Create session ──
    session = ProcessingSession(
        assessment_id=assessment_id,
        school_id=school_id,
        status=ProcessingSessionStatus.PENDING,
    )
    db.add(session)
    db.flush()  # get session.id

    # ── Create upload directory ──
    upload_dir = _session_dir(session.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # ── Save files and create ProcessingFile records ──
    for upload in files:
        filename = upload.filename or "unknown"
        content = await upload.read()

        # Save to disk
        file_path = upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)

        # Parse roll number
        match = FILENAME_REGEX.match(filename)
        if not match:
            pf = ProcessingFile(
                session_id=session.id,
                original_filename=filename,
                roll_number=0,
                status=ProcessingFileStatus.INVALID,
                error_message="Invalid filename format — expected: ROLLNUMBER.extension (e.g. 101.jpg)",
            )
            db.add(pf)
            session.files.append(pf)
            continue

        roll_number = int(match.group(1))
        if roll_number <= 0:
            pf = ProcessingFile(
                session_id=session.id,
                original_filename=filename,
                roll_number=roll_number,
                status=ProcessingFileStatus.INVALID,
                error_message="Roll number must be a positive integer",
            )
            db.add(pf)
            session.files.append(pf)
            continue

        # Find student in selected school
        student = (
            db.query(Student)
            .filter(Student.school_id == school_id, Student.roll_number == roll_number)
            .first()
        )
        if not student:
            pf = ProcessingFile(
                session_id=session.id,
                original_filename=filename,
                roll_number=roll_number,
                status=ProcessingFileStatus.INVALID,
                error_message=f"No student found with roll number {roll_number} in the selected school",
            )
            db.add(pf)
            session.files.append(pf)
            continue

        # Create valid file record (will check duplicates after flush)
        pf = ProcessingFile(
            session_id=session.id,
            original_filename=filename,
            roll_number=roll_number,
            student_id=student.id,
            status=ProcessingFileStatus.PENDING,
        )
        db.add(pf)
        session.files.append(pf)

    db.flush()

    # ── Check for duplicate roll numbers in this batch ──
    session_files = [f for f in session.files]
    roll_seen: dict[int, list[ProcessingFile]] = {}
    for f in session_files:
        if f.status in (ProcessingFileStatus.INVALID,):
            continue
        roll_seen.setdefault(f.roll_number, []).append(f)

    for roll_number, file_list in roll_seen.items():
        if len(file_list) > 1:
            for f in file_list:
                f.status = ProcessingFileStatus.INVALID
                f.error_message = f"Duplicate roll number {roll_number} in this batch. Only one OMR sheet per student is allowed."
                f.student_id = None

    # ── Counters ──
    _update_counters(session, db)
    db.commit()
    db.refresh(session)

    return _session_to_dict(session, db)


@router.get("", response_model=list[ProcessingSessionListRead])
def list_sessions(
    assessment_id: int | None = None,
    _current_user: User = Depends(get_current_user),
    school_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(ProcessingSession)
        .options(
            selectinload(ProcessingSession.assessment)
            .selectinload(Assessment.questions),
            selectinload(ProcessingSession.school)
            .selectinload(School.students),
        )
    )
    if assessment_id:
        query = query.filter(ProcessingSession.assessment_id == assessment_id)
    if school_id:
        query = query.filter(ProcessingSession.school_id == school_id)
    sessions = query.order_by(ProcessingSession.created_at.desc()).all()
    return [_session_to_dict(s, db) for s in sessions]


@router.get("/{session_id}", response_model=ProcessingSessionRead)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)
    return _session_to_dict(session, db)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)
    # Delete files from disk
    upload_dir = _session_dir(session.id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    # Delete attempts (and their cascade of attempt_questions) before session
    attempts = (
        db.query(AssessmentAttempt)
        .filter(AssessmentAttempt.processing_session_id == session.id)
        .all()
    )
    for att in attempts:
        db.delete(att)
    db.flush()
    db.delete(session)
    db.commit()


@router.post("/{session_id}/validate", response_model=ProcessingSessionRead)
def validate_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)

    if session.status not in (ProcessingSessionStatus.PENDING, ProcessingSessionStatus.VALIDATING):
        raise HTTPException(422, "Session cannot be validated in its current state")

    session.status = ProcessingSessionStatus.VALIDATING
    db.flush()

    # Re-validate all PENDING files
    for f in session.files:
        if f.status != ProcessingFileStatus.PENDING:
            continue

        # Re-check student exists (student may have been deleted since upload)
        if f.student_id:
            student = db.get(Student, f.student_id)
            if not student or student.school_id != session.school_id:
                f.status = ProcessingFileStatus.INVALID
                f.error_message = f"Student with roll number {f.roll_number} no longer exists in the selected school"
                f.student_id = None
            else:
                f.status = ProcessingFileStatus.VALID
        else:
            # No student_id means it was already invalid
            pass

    _update_counters(session, db)

    if session.valid_files > 0:
        session.status = ProcessingSessionStatus.READY
    else:
        session.status = ProcessingSessionStatus.FAILED

    db.commit()
    db.refresh(session)
    return _session_to_dict(session, db)


@router.post("/{session_id}/process")
def process_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)

    if session.status != ProcessingSessionStatus.READY:
        raise HTTPException(422, "Session must be in 'ready' status to process")

    # Pre-flight: check template supports the assessment's question count
    assessment = session.assessment
    question_count = len(assessment.questions)
    template_qc = get_template_question_count()
    if question_count > template_qc:
        raise HTTPException(
            422,
            f"Assessment has {question_count} questions but the OMR template "
            f"only supports {template_qc}. Recalibrate the template or reduce "
            f"the number of questions.",
        )

    session.status = ProcessingSessionStatus.PROCESSING
    session.started_at = datetime.now(timezone.utc)
    db.flush()

    # Process each VALID file independently
    for f in session.files:
        if f.status != ProcessingFileStatus.VALID:
            continue

        file_path = _session_dir(session.id) / f.original_filename
        result = process_single_omr_file(
            db,
            file_path=file_path,
            question_count=question_count,
            session_id=session.id,
            file_id=f.id,
            assessment=assessment,
            student=f.student,
        )

        if result["success"]:
            f.status = ProcessingFileStatus.PROCESSED
            f.error_message = None
        else:
            f.status = ProcessingFileStatus.FAILED
            f.error_message = result.get("error", "Processing failed")

    _update_counters(session, db)

    # Determine final session status
    if session.successful_files == session.valid_files:
        session.status = ProcessingSessionStatus.COMPLETED
    elif session.successful_files > 0:
        session.status = ProcessingSessionStatus.PARTIAL
    else:
        session.status = ProcessingSessionStatus.FAILED

    session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return _session_to_dict(session, db)


@router.get("/{session_id}/progress", response_model=ProcessingProgressRead)
def get_progress(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)
    return {
        "session_id": session.id,
        "status": session.status.value,
        "total": session.valid_files,
        "processed": session.processed_files,
        "successful": session.successful_files,
        "failed": session.failed_files,
        "remaining": max(session.valid_files - session.processed_files, 0),
    }


@router.post("/{session_id}/retry", response_model=ProcessingSessionRead)
def retry_failed(session_id: int, payload: RetryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)

    if session.status not in (ProcessingSessionStatus.COMPLETED, ProcessingSessionStatus.PARTIAL, ProcessingSessionStatus.FAILED):
        raise HTTPException(422, "Session must be completed or partially completed to retry")

    # Validate all requested files exist and are FAILED
    files_by_id = {f.id: f for f in session.files}
    for fid in payload.file_ids:
        f = files_by_id.get(fid)
        if not f:
            raise HTTPException(404, f"File {fid} not found in this session")
        if f.status != ProcessingFileStatus.FAILED:
            raise HTTPException(422, f"File {fid} is not in 'failed' status")
        if f.retry_count >= MAX_RETRY_COUNT:
            raise HTTPException(422, f"File {fid} has exceeded maximum retry count ({MAX_RETRY_COUNT})")

    # Start processing
    session.status = ProcessingSessionStatus.PROCESSING
    session.started_at = datetime.now(timezone.utc)
    db.flush()

    assessment = session.assessment
    question_count = len(assessment.questions)

    for fid in payload.file_ids:
        f = files_by_id[fid]
        f.status = ProcessingFileStatus.RETRYING
        f.retry_count += 1
        db.flush()

        file_path = _session_dir(session.id) / f.original_filename
        result = process_single_omr_file(
            db,
            file_path=file_path,
            question_count=question_count,
            session_id=session.id,
            file_id=f.id,
            assessment=assessment,
            student=f.student,
        )

        if result["success"]:
            f.status = ProcessingFileStatus.PROCESSED
            f.error_message = None
        else:
            f.status = ProcessingFileStatus.FAILED
            f.error_message = result.get("error", "Processing failed")

    _update_counters(session, db)

    # Determine final session status
    all_processed = all(
        f.status in (ProcessingFileStatus.PROCESSED, ProcessingFileStatus.INVALID, ProcessingFileStatus.PENDING)
        for f in session.files
    )
    if session.failed_files == 0 and all_processed:
        session.status = ProcessingSessionStatus.COMPLETED
    elif session.successful_files > 0:
        session.status = ProcessingSessionStatus.PARTIAL
    else:
        session.status = ProcessingSessionStatus.FAILED

    session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return _session_to_dict(session, db)


@router.delete("/{session_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(session_id: int, file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = _load_session(session_id, db)

    if session.status == ProcessingSessionStatus.PROCESSING:
        raise HTTPException(422, "Cannot delete files while session is processing")

    file = None
    for f in session.files:
        if f.id == file_id:
            file = f
            break
    if not file:
        raise HTTPException(404, "File not found in this session")

    # Remove from disk
    file_path = _session_dir(session.id) / file.original_filename
    if file_path.exists():
        file_path.unlink()

    db.delete(file)
    _update_counters(session, db)
    db.commit()
