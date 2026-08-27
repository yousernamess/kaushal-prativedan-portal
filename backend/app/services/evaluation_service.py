"""Evaluation service — creates AssessmentAttempt + AttemptQuestion records.

This module is responsible for:
1. Matching OMR-detected answers against Assessment questions.
2. Creating or updating AssessmentAttempt records (one per student per assessment).
3. Creating AttemptQuestion records (one per question per attempt).
4. Computing score, total_questions, and percentage.
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentAttempt,
    AttemptQuestion,
    AttemptStatus,
    ProcessingFile,
    ProcessingFileStatus,
    Question,
    Student,
)
from app.services.omr_service import OMRProcessingError, extract_omr, get_template_question_count


def _compute_results(
    questions: list[Question],
    detected: dict[str, str | None],
) -> tuple[list[dict], int, int, Decimal]:
    """Compare detected answers against assessment questions.

    Returns:
        (question_results, score, total_questions, percentage)
    """
    total = len(questions)
    score = 0
    question_results: list[dict] = []

    for q in questions:
        key = f"Q{q.question_number}"
        detected_answer = detected.get(key)  # None if key missing or value is None
        is_correct = detected_answer is not None and detected_answer == q.correct_option
        if is_correct:
            score += 1
        question_results.append({
            "question_id": q.id,
            "detected_answer": detected_answer,
            "correct_answer": q.correct_option,
            "is_correct": is_correct,
            "domain": q.domain,
        })

    percentage = Decimal(score) / Decimal(total) * Decimal(100) if total > 0 else Decimal("0.00")
    percentage = percentage.quantize(Decimal("0.01"))

    return question_results, score, total, percentage


def evaluate_and_persist(
    db: Session,
    *,
    assessment: Assessment,
    student: Student,
    processing_session_id: int,
    file_path: Path,
) -> dict:
    """Extract OMR, evaluate answers, and persist attempt + question records.

    This function manages its OWN transaction for the attempt.  If extraction
    or persistence fails, it raises and the caller handles the ProcessingFile
    status update — but any previously-committed attempts for OTHER students
    remain intact.

    Args:
        db: Active SQLAlchemy session.
        assessment: The Assessment with questions loaded.
        student: The matched Student.
        processing_session_id: ID of the current ProcessingSession.
        file_path: Absolute path to the uploaded OMR image.

    Returns:
        dict with keys: score, total_questions, percentage, attempt_id

    Raises:
        OMRProcessingError: On any extraction/evaluation failure.
    """
    question_count = len(assessment.questions)
    if question_count == 0:
        raise OMRProcessingError("Assessment has no questions")

    # ── Step 1: Run OMR extraction ─────────────────────────────────
    detected = extract_omr(file_path, question_count)

    # ── Step 2: Evaluate ───────────────────────────────────────────
    questions = sorted(assessment.questions, key=lambda q: q.question_number)
    question_results, score, total, percentage = _compute_results(questions, detected)

    # ── Step 3: Upsert attempt ─────────────────────────────────────
    existing_attempt = (
        db.query(AssessmentAttempt)
        .filter(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.student_id == student.id,
        )
        .first()
    )

    if existing_attempt:
        # Update existing attempt (reprocessing / retry)
        attempt = existing_attempt
        attempt.score = score
        attempt.total_questions = total
        attempt.percentage = percentage
        attempt.status = AttemptStatus.COMPLETED
        attempt.processing_session_id = processing_session_id
        attempt.completed_at = datetime.now(timezone.utc)

        # Delete old question records and recreate
        for old_q in list(attempt.questions):
            db.delete(old_q)
        db.flush()
    else:
        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            student_id=student.id,
            processing_session_id=processing_session_id,
            score=score,
            total_questions=total,
            percentage=percentage,
            status=AttemptStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.flush()  # get attempt.id

    # ── Step 4: Create question-level records ──────────────────────
    for qr in question_results:
        aq = AttemptQuestion(
            attempt_id=attempt.id,
            question_id=qr["question_id"],
            detected_answer=qr["detected_answer"],
            correct_answer=qr["correct_answer"],
            is_correct=qr["is_correct"],
            domain=qr["domain"],
        )
        db.add(aq)

    db.flush()

    return {
        "score": score,
        "total_questions": total,
        "percentage": float(percentage),
        "attempt_id": attempt.id,
    }
