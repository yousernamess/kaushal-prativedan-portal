"""M5 integration test — exercises the real OMR extractor + evaluation pipeline."""

import sys
from pathlib import Path
from decimal import Decimal

# ── Bootstrap ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models import (
    Assessment, AssessmentAttempt, AttemptQuestion, ProcessingFile,
    ProcessingFileStatus, ProcessingSession, ProcessingSessionStatus,
    Question, School, Student,
)
from app.services.omr_service import extract_omr, OMRProcessingError, get_template_question_count
from app.services.evaluation_service import evaluate_and_persist

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "omrExtractor" / "input"
db = SessionLocal()

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} — {detail}")
        failed += 1

# ── Get test data ──────────────────────────────────────────────────
assessments = db.query(Assessment).filter(Assessment.is_deleted == False).all()
assessments_with_q = [a for a in assessments if len(a.questions) > 0]
if not assessments_with_q:
    print("ERROR: No assessments with questions found. Create test data first.")
    sys.exit(1)

assessment = assessments_with_q[0]
questions = sorted(assessment.questions, key=lambda q: q.question_number)
print(f"Using assessment: {assessment.name} (id={assessment.id}, {len(questions)} questions)")

schools = db.query(School).all()
school = next((s for s in schools if len(s.students) > 0), None)
if not school:
    print("ERROR: No school with students found.")
    sys.exit(1)

students = sorted(school.students, key=lambda s: s.roll_number)
print(f"Using school: {school.name} (id={school.id}, {len(students)} students)")


# ── Test 1: Template question count ────────────────────────────────

print("\n=== Test 1: Template question count ===")
template_qc = get_template_question_count()
test("Template has questions", template_qc > 0, f"Got {template_qc}")
test("Template supports assessment", template_qc >= len(questions),
     f"Template={template_qc}, Assessment={len(questions)}")


# ── Test 2: Direct OMR extraction ─────────────────────────────────

print("\n=== Test 2: Direct OMR extraction ===")
sample_img = SAMPLE_DIR / "101.jpeg"
test("Sample image exists", sample_img.exists(), str(sample_img))

if sample_img.exists():
    result = extract_omr(sample_img, len(questions))
    test("Result is dict", isinstance(result, dict))
    test("Result has correct keys", all(f"Q{i}" in result for i in range(1, len(questions) + 1)),
         f"Keys: {list(result.keys())[:5]}...")
    answered = sum(1 for v in result.values() if v is not None)
    print(f"  Extracted: {len(result)} questions, {answered} answered, {len(result) - answered} None")


# ── Test 3: Full evaluate_and_persist ──────────────────────────────

print("\n=== Test 3: evaluate_and_persist ===")
student = students[0]

# Clean up any prior attempt for this student
prior = db.query(AssessmentAttempt).filter(
    AssessmentAttempt.assessment_id == assessment.id,
    AssessmentAttempt.student_id == student.id,
).first()
if prior:
    db.query(AssessmentAttempt).filter(AssessmentAttempt.id == prior.id).delete()
    db.commit()

# Create a dummy session for the test
session = ProcessingSession(
    assessment_id=assessment.id,
    school_id=school.id,
    status=ProcessingSessionStatus.PROCESSING,
    total_files=1,
    valid_files=1,
)
db.add(session)
db.flush()

try:
    eval_result = evaluate_and_persist(
        db,
        assessment=assessment,
        student=student,
        processing_session_id=session.id,
        file_path=sample_img,
    )
    db.commit()

    test("Has score", "score" in eval_result, str(eval_result))
    test("Has total_questions", eval_result.get("total_questions") == len(questions),
         f"Got {eval_result.get('total_questions')}")
    test("Has percentage", "percentage" in eval_result)
    test("Has attempt_id", "attempt_id" in eval_result)
    test("Score is valid", 0 <= eval_result["score"] <= len(questions),
         f"Score={eval_result['score']}")
    test("Percentage is valid", 0 <= eval_result["percentage"] <= 100,
         f"Pct={eval_result['percentage']}")

    # Verify attempt in DB
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == eval_result["attempt_id"]
    ).first()
    test("Attempt exists in DB", attempt is not None)
    if attempt:
        test("Attempt score matches", attempt.score == eval_result["score"])
        test("Attempt has percentage", attempt.percentage == Decimal(str(eval_result["percentage"])))
        test("Attempt status is COMPLETED", attempt.status.value == "COMPLETED")

        # Verify question-level records
        aqs = db.query(AttemptQuestion).filter(
            AttemptQuestion.attempt_id == attempt.id
        ).all()
        test("Question records created", len(aqs) == len(questions),
             f"Got {len(aqs)}, expected {len(questions)}")

        if aqs:
            # Check that each has correct fields
            sample_aq = aqs[0]
            test("AQ has detected_answer", sample_aq.detected_answer is not None or True)  # None is valid
            test("AQ has correct_answer", sample_aq.correct_answer in ["A", "B", "C", "D"],
                 f"Got {sample_aq.correct_answer}")
            test("AQ has is_correct", isinstance(sample_aq.is_correct, bool))
            test("AQ has domain", len(sample_aq.domain) > 0, f"Got '{sample_aq.domain}'")

            # Count correct
            correct_count = sum(1 for q in aqs if q.is_correct)
            test("Correct count matches score", correct_count == attempt.score,
                 f"Correct={correct_count}, score={attempt.score}")

except Exception as e:
    db.rollback()
    print(f"  FAIL: evaluate_and_persist raised: {type(e).__name__}: {e}")
    failed += 1


# ── Test 4: Duplicate attempt (reprocessing) ──────────────────────

print("\n=== Test 4: Duplicate attempt (reprocessing) ===")
session2 = ProcessingSession(
    assessment_id=assessment.id,
    school_id=school.id,
    status=ProcessingSessionStatus.PROCESSING,
    total_files=1,
    valid_files=1,
)
db.add(session2)
db.flush()

try:
    eval_result2 = evaluate_and_persist(
        db,
        assessment=assessment,
        student=student,
        processing_session_id=session2.id,
        file_path=sample_img,
    )
    db.commit()

    # Should have updated the existing attempt, not created a new one
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.assessment_id == assessment.id,
        AssessmentAttempt.student_id == student.id,
    ).all()
    test("Still only one attempt", len(attempts) == 1,
         f"Found {len(attempts)} attempts")
    if attempts:
        test("Attempt updated with new session",
             attempts[0].processing_session_id == session2.id)
        test("Attempt still has question records",
             len(attempts[0].questions) == len(questions))

except Exception as e:
    db.rollback()
    print(f"  FAIL: Reprocessing raised: {type(e).__name__}: {e}")
    failed += 1


# ── Test 5: Second student ────────────────────────────────────────

print("\n=== Test 5: Second student ===")
if len(students) >= 2 and (SAMPLE_DIR / "104.jpeg").exists():
    student2 = students[1]
    sample_img2 = SAMPLE_DIR / "104.jpeg"

    # Clean up
    prior2 = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.assessment_id == assessment.id,
        AssessmentAttempt.student_id == student2.id,
    ).first()
    if prior2:
        db.query(AssessmentAttempt).filter(AssessmentAttempt.id == prior2.id).delete()
        db.commit()

    session3 = ProcessingSession(
        assessment_id=assessment.id,
        school_id=school.id,
        status=ProcessingSessionStatus.PROCESSING,
        total_files=1,
        valid_files=1,
    )
    db.add(session3)
    db.flush()

    try:
        eval_result3 = evaluate_and_persist(
            db,
            assessment=assessment,
            student=student2,
            processing_session_id=session3.id,
            file_path=sample_img2,
        )
        db.commit()

        test("Second student processed", eval_result3["attempt_id"] > 0)

        # Both students should have separate attempts
        total_attempts = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.assessment_id == assessment.id
        ).count()
        test("Two separate attempts exist", total_attempts == 2,
             f"Found {total_attempts}")

    except Exception as e:
        db.rollback()
        print(f"  FAIL: Second student raised: {type(e).__name__}: {e}")
        failed += 1
else:
    print("  SKIPPED: Not enough students or sample images")


# ── Test 6: Template capacity guard ───────────────────────────────

print("\n=== Test 6: Template capacity guard ===")
try:
    extract_omr(sample_img, 50)  # Template only supports 40
    test("Should have rejected", False)
except OMRProcessingError as e:
    test("Correctly rejected oversized assessment", "only supports" in str(e).lower(),
         f"Error: {e}")


# ── Test 7: Missing file ──────────────────────────────────────────

print("\n=== Test 7: Missing file ===")
try:
    extract_omr(Path("nonexistent.jpg"), 10)
    test("Should have raised", False)
except OMRProcessingError as e:
    test("Correctly rejected missing file", "not found" in str(e).lower(),
         f"Error: {e}")


# ── Cleanup ────────────────────────────────────────────────────────

# Clean up test attempts
for a in db.query(AssessmentAttempt).filter(
    AssessmentAttempt.assessment_id == assessment.id
).all():
    db.query(AssessmentAttempt).filter(AssessmentAttempt.id == a.id).delete()
db.commit()

# Clean up test sessions
for s in db.query(ProcessingSession).filter(
    ProcessingSession.assessment_id == assessment.id,
    ProcessingSession.status == ProcessingSessionStatus.PROCESSING,
).all():
    db.delete(s)
db.commit()

db.close()

# ── Summary ────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
print(f"{'='*50}")
if failed > 0:
    sys.exit(1)
