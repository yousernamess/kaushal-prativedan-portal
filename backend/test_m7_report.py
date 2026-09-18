"""M7 Student Report — backend tests.

Tests:
  1. student_analytics returns assessment_name, assessment_type, academic_year_name
  2. student_report_questions returns per-question breakdown
  3. 404 cases (bad assessment, bad student, no attempt)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from app.core.database import SessionLocal, Base, engine
from app.models import (
    AcademicYear, Assessment, AssessmentAttempt, AssessmentType,
    AttemptQuestion, AttemptStatus, ProcessingSession, ProcessingSessionStatus,
    Question, School, Section, Student,
)
from app.services.analytics_service import student_analytics, student_report_questions

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} -- {detail}")
        failed += 1


# ── Setup ──────────────────────────────────────────────────────────

print("\n=== Setting up M7 test dataset ===")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clean previous M7 test data
db.query(ProcessingSession).filter(ProcessingSession.assessment_id == 998).delete(synchronize_session="fetch")
db.query(AttemptQuestion).filter(
    AttemptQuestion.attempt_id.in_(
        db.query(AssessmentAttempt.id).filter(AssessmentAttempt.assessment_id == 998)
    )
).delete(synchronize_session="fetch")
db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == 998).delete()
db.query(Question).filter(Question.assessment_id == 998).delete()
db.query(Assessment).filter(Assessment.id == 998).delete()
db.query(Student).filter(Student.school_id.in_(
    db.query(School.id).filter(School.name.in_(["M7 Alpha School"]))
)).delete(synchronize_session="fetch")
db.query(Section).filter(Section.school_id.in_(
    db.query(School.id).filter(School.name.in_(["M7 Alpha School"]))
)).delete(synchronize_session="fetch")
db.query(School).filter(School.name == "M7 Alpha School").delete()
test_ay = db.query(AcademicYear).filter(AcademicYear.name == "TEST-M7").first()
if test_ay:
    db.delete(test_ay)
db.commit()

# Academic year
ay = AcademicYear(name="TEST-M7")
db.add(ay)
db.flush()

# School
school = School(name="M7 Alpha School", school_number=5)
db.add(school)
db.flush()

# Student
student = Student(
    school_id=school.id,
    student_code="0507m7teststudent",
    student_name="M7 Test Student",
    current_class=7,
    current_section="A",
)
db.add(student)
db.flush()

# Assessment (5 questions, 3 Knowledge + 2 Application)
assessment = Assessment(
    id=998,
    name="M7 Science Test",
    assessment_type=AssessmentType.BASELINE,
    academic_year_id=ay.id,
    class_number=7,
)
db.add(assessment)
db.flush()

# Questions
questions = []
for i, (domain, correct) in enumerate([
    ("Knowledge Base", "A"), ("Knowledge Base", "B"), ("Knowledge Base", "C"),
    ("Experiential Learning", "D"), ("Experiential Learning", "A"),
], start=1):
    q = Question(
        assessment_id=998,
        question_number=i,
        question_text=f"What is question {i} about {domain.lower()}?",
        option_a="Option A", option_b="Option B",
        option_c="Option C", option_d="Option D",
        correct_option=correct,
        domain=domain,
    )
    db.add(q)
    questions.append(q)
db.flush()

# A real processing session for the attempt to reference (FK requirement)
m7_session = ProcessingSession(
    assessment_id=998, school_id=school.id,
    status=ProcessingSessionStatus.COMPLETED,
)
db.add(m7_session)
db.flush()

# Attempt: 3/5 correct (Q1=A✓, Q2=B✓, Q3=wrong, Q4=D✓, Q5=wrong)
attempt = AssessmentAttempt(
    assessment_id=998,
    student_id=student.id,
    processing_session_id=m7_session.id,
    score=3,
    total_questions=5,
    percentage=Decimal("60.00"),
    status=AttemptStatus.COMPLETED,
)
db.add(attempt)
db.flush()

# Attempt questions
detected = ["A", "B", "A", "D", "B"]  # Q3 wrong (should be C), Q5 wrong (should be A)
for i, q in enumerate(questions):
    is_correct = detected[i] == q.correct_option
    aq = AttemptQuestion(
        attempt_id=attempt.id,
        question_id=q.id,
        detected_answer=detected[i],
        correct_answer=q.correct_option,
        is_correct=is_correct,
        domain=q.domain,
    )
    db.add(aq)

db.commit()
print("  Dataset ready.\n")

# ── Test 1: student_analytics includes assessment metadata ─────────

print("--- Test: student_analytics assessment metadata ---")

result = student_analytics(db, 998, student.id)

test(
    "assessment_name present",
    result.get("assessment_name") == "M7 Science Test",
    f"got {result.get('assessment_name')}",
)
test(
    "assessment_type present",
    result.get("assessment_type") == "Baseline",
    f"got {result.get('assessment_type')}",
)
test(
    "academic_year_name present",
    result.get("academic_year_name") == "TEST-M7",
    f"got {result.get('academic_year_name')}",
)
test(
    "existing fields still work",
    result.get("score") == 3 and result.get("percentage") == 60.0,
    f"score={result.get('score')}, pct={result.get('percentage')}",
)

# ── Test 1b: domain averages for radar chart ──────────────────────

print("\n--- Test: domain averages (radar chart data) ---")

test(
    "school_domains present",
    isinstance(result.get("school_domains"), list) and len(result["school_domains"]) > 0,
    f"got {result.get('school_domains')}",
)
test(
    "overall_domains present",
    isinstance(result.get("overall_domains"), list) and len(result["overall_domains"]) > 0,
    f"got {result.get('overall_domains')}",
)
# With only 1 student, school_domains == overall_domains == student domains
sd = {d["domain"]: d for d in result["school_domains"]}
od = {d["domain"]: d for d in result["overall_domains"]}
test(
    "school_domains has Knowledge Base",
    "Knowledge Base" in sd,
    f"keys: {list(sd.keys())}",
)
test(
    "overall_domains has Experiential Learning",
    "Experiential Learning" in od,
    f"keys: {list(od.keys())}",
)

# ── Test 2: student_report_questions ───────────────────────────────

print("\n--- Test: student_report_questions ---")

qr = student_report_questions(db, 998, student.id)

test(
    "returns correct number of questions",
    len(qr["questions"]) == 5,
    f"got {len(qr['questions'])}",
)

q1 = qr["questions"][0]
test("Q1 question_number", q1["question_number"] == 1, f"got {q1['question_number']}")
test("Q1 question_text present", q1["question_text"] is not None, "None")
test("Q1 domain", q1["domain"] == "Knowledge Base", f"got {q1['domain']}")
test("Q1 detected_answer", q1["detected_answer"] == "A", f"got {q1['detected_answer']}")
test("Q1 correct_answer", q1["correct_answer"] == "A", f"got {q1['correct_answer']}")
test("Q1 is_correct", q1["is_correct"] is True, f"got {q1['is_correct']}")

q3 = qr["questions"][2]
test("Q3 detected_answer (wrong)", q3["detected_answer"] == "A", f"got {q3['detected_answer']}")
test("Q3 correct_answer", q3["correct_answer"] == "C", f"got {q3['correct_answer']}")
test("Q3 is_correct (false)", q3["is_correct"] is False, f"got {q3['is_correct']}")

# Questions should be sorted by question_number
qnums = [q["question_number"] for q in qr["questions"]]
test("questions sorted by number", qnums == [1, 2, 3, 4, 5], f"got {qnums}")

# ── Test 2b: option text and percent_correct ──────────────────────

print("\n--- Test: option text + percent_correct ---")

q1 = qr["questions"][0]
test("Q1 option_a present", q1.get("option_a") == "Option A", f"got {q1.get('option_a')}")
test("Q1 option_b present", q1.get("option_b") == "Option B", f"got {q1.get('option_b')}")
test("Q1 option_c present", q1.get("option_c") == "Option C", f"got {q1.get('option_c')}")
test("Q1 option_d present", q1.get("option_d") == "Option D", f"got {q1.get('option_d')}")
test(
    "Q1 percent_correct present",
    isinstance(q1.get("percent_correct"), (int, float)),
    f"got {q1.get('percent_correct')}",
)
# With 1 student, percent_correct should be 100.0 for correct answers, 0.0 for wrong
test(
    "Q1 percent_correct (correct answer) = 100.0",
    q1["percent_correct"] == 100.0,
    f"got {q1['percent_correct']}",
)
q3 = qr["questions"][2]
test(
    "Q3 percent_correct (wrong answer) = 0.0",
    q3["percent_correct"] == 0.0,
    f"got {q3['percent_correct']}",
)

# ── Test 3: 404 cases ─────────────────────────────────────────────

print("\n--- Test: 404 error cases ---")

try:
    student_analytics(db, 99999, student.id)
    test("student_analytics bad assessment raises", False, "no error raised")
except ValueError as e:
    test("student_analytics bad assessment raises ValueError", "not found" in str(e).lower())

try:
    student_analytics(db, 998, 99999)
    test("student_analytics bad student raises", False, "no error raised")
except ValueError as e:
    test("student_analytics bad student raises ValueError", "not found" in str(e).lower())

try:
    student_report_questions(db, 99999, student.id)
    test("report_questions bad assessment raises", False, "no error raised")
except ValueError as e:
    test("report_questions bad assessment raises ValueError", "not found" in str(e).lower())

try:
    student_report_questions(db, 998, 99999)
    test("report_questions bad student raises", False, "no error raised")
except ValueError as e:
    test("report_questions bad student raises ValueError", "not found" in str(e).lower())

# ── Summary ────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
if failed > 0:
    print("SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")

db.close()
