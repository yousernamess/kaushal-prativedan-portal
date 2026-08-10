"""M6A Analytics Service Tests â€” deterministic dataset, manual calculations.

Test dataset (created in setUp):

  School A: "Alpha School"
    Student 1: Alice   (class=6, section=A) â€” 8/10 = 80.00%
    Student 2: Bob     (class=6, section=A) â€” 7/10 = 70.00%
    Student 3: Charlie (class=6, section=B) â€” 6/10 = 60.00%

  School B: "Beta School"
    Student 4: Diana   (class=7, section=A) â€” 9/10 = 90.00%
    Student 5: Eve     (class=7, section=A) â€” 7/10 = 70.00%

  Assessment: "Science Test" (10 questions, 2 domains)

  Questions:
    Q1: domain=Knowledge,  correct=A
    Q2: domain=Knowledge,  correct=B
    Q3: domain=Knowledge,  correct=C
    Q4: domain=Knowledge,  correct=D
    Q5: domain=Knowledge,  correct=A
    Q6: domain=Application, correct=B
    Q7: domain=Application, correct=C
    Q8: domain=Application, correct=D
    Q9: domain=Application, correct=A
    Q10: domain=Application, correct=B

  Attempts (detected answers):
    Alice:   A B C D A | B C D A B â†’ 8/10 (Q6=wrong, Q9=wrong)
    Bob:     A B C D A | A C D A B â†’ 7/10 (Q6=wrong, Q9=wrong, Q7=wrong wait...)
    Charlie: A B C D A | B C D A B â†’ 6/10
    Diana:   A B C D A | B C D A B â†’ 9/10 (Q6=wrong)
    Eve:     A B C D A | A C D A B â†’ 7/10

  Let me be precise about detected answers and correctness:

  Alice (8/10):
    Q1=A(correct) âœ“, Q2=B âœ“, Q3=C âœ“, Q4=D âœ“, Q5=A âœ“,
    Q6=B âœ“, Q7=C âœ“, Q8=D âœ“, Q9=A âœ“, Q10=B âœ“ â†’ wait that's 10/10
    Let me redo:
    Q6 detected=A (wrong, correct=B), Q9 detected=B (wrong, correct=A)
    â†’ 8 correct

  Bob (7/10):
    Q1=A âœ“, Q2=B âœ“, Q3=C âœ“, Q4=D âœ“, Q5=A âœ“,
    Q6=A (wrong), Q7=C âœ“, Q8=D âœ“, Q9=B (wrong), Q10=A (wrong)
    â†’ 7 correct

  Charlie (6/10):
    Q1=A âœ“, Q2=B âœ“, Q3=D (wrong), Q4=D âœ“, Q5=A âœ“,
    Q6=B âœ“, Q7=C âœ“, Q8=A (wrong), Q9=A âœ“, Q10=A (wrong)
    â†’ 6 correct

  Diana (9/10):
    Q1=A âœ“, Q2=B âœ“, Q3=C âœ“, Q4=D âœ“, Q5=A âœ“,
    Q6=B âœ“, Q7=C âœ“, Q8=D âœ“, Q9=B (wrong), Q10=B âœ“
    â†’ 9 correct

  Eve (7/10):
    Q1=A âœ“, Q2=C (wrong), Q3=C âœ“, Q4=D âœ“, Q5=A âœ“,
    Q6=A (wrong), Q7=C âœ“, Q8=D âœ“, Q9=A âœ“, Q10=B âœ“
    â†’ 7 correct

Manual calculations for verification:

  Overall:
    scores: [8, 7, 6, 9, 7]
    percentages: [80, 70, 60, 90, 70]
    avg_score = 37/5 = 7.4
    avg_pct = 370/5 = 74.0
    highest = 90, lowest = 60

  School A (Alice, Bob, Charlie):
    scores: [8, 7, 6]
    percentages: [80, 70, 60]
    avg_score = 21/3 = 7.0
    avg_pct = 210/3 = 70.0
    highest=80, lowest=60

  School B (Diana, Eve):
    scores: [9, 7]
    percentages: [90, 70]
    avg_score = 16/2 = 8.0
    avg_pct = 160/2 = 80.0
    highest=90, lowest=70

  School ranks (by avg pct):
    School B: 80.0 â†’ rank 1
    School A: 70.0 â†’ rank 2

  Domain breakdown (all students, all 5 attempts):
    Knowledge (5 questions Ã— 5 attempts = 25 total):
      Alice: Q1âœ“ Q2âœ“ Q3âœ“ Q4âœ“ Q5âœ“ â†’ 5/5
      Bob:   Q1âœ“ Q2âœ“ Q3âœ“ Q4âœ“ Q5âœ“ â†’ 5/5
      Charlie: Q1âœ“ Q2âœ“ Q3âœ— Q4âœ“ Q5âœ“ â†’ 4/5
      Diana: Q1âœ“ Q2âœ“ Q3âœ“ Q4âœ“ Q5âœ“ â†’ 5/5
      Eve:   Q1âœ“ Q2âœ— Q3âœ“ Q4âœ“ Q5âœ“ â†’ 4/5
      Total: 23/25 = 92.0%

    Application (5 questions Ã— 5 attempts = 25 total):
      Alice: Q6âœ“ Q7âœ“ Q8âœ“ Q9âœ“ Q10âœ“ â†’ 5/5
      Bob:   Q6âœ— Q7âœ“ Q8âœ“ Q9âœ— Q10âœ— â†’ 2/5
      Charlie: Q6âœ“ Q7âœ“ Q8âœ— Q9âœ“ Q10âœ— â†’ 3/5
      Diana: Q6âœ“ Q7âœ“ Q8âœ“ Q9âœ— Q10âœ“ â†’ 4/5
      Eve:   Q6âœ— Q7âœ“ Q8âœ“ Q9âœ“ Q10âœ“ â†’ 4/5
      Total: 18/25 = 72.0%

  Student rankings (overall):
    Diana: 90 â†’ rank 1
    Alice: 80 â†’ rank 2
    Bob:   70 â†’ rank 3 (tied with Eve)
    Eve:   70 â†’ rank 3 (tied with Bob)
    Charlie: 60 â†’ rank 5

  Student rankings (school A):
    Alice: 80 â†’ rank 1
    Bob:   70 â†’ rank 2
    Charlie: 60 â†’ rank 3

  Student rankings (school B):
    Diana: 90 â†’ rank 1
    Eve:   70 â†’ rank 2

  Percentiles (overall, 5 students):
    Diana (90): lower=4 â†’ 4/5*100 = 80.0
    Alice (80): lower=3 â†’ 3/5*100 = 60.0
    Bob (70):   lower=1 â†’ 1/5*100 = 20.0
    Eve (70):   lower=1 â†’ 1/5*100 = 20.0
    Charlie (60): lower=0 â†’ 0/5*100 = 0.0

  Percentiles (school A, 3 students):
    Alice (80): lower=2 â†’ 2/3*100 = 66.67
    Bob (70):   lower=1 â†’ 1/3*100 = 33.33
    Charlie (60): lower=0 â†’ 0/3*100 = 0.0

  Percentiles (school B, 2 students):
    Diana (90): lower=1 â†’ 1/2*100 = 50.0
    Eve (70):   lower=0 â†’ 0/2*100 = 0.0
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from app.core.database import SessionLocal, Base, engine
from app.models import (
    AcademicYear, Assessment, AssessmentAttempt, AssessmentType,
    AttemptQuestion, AttemptStatus, Question, School, Section, Student,
)

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} â€” {detail}")
        failed += 1


# â”€â”€ Setup: create deterministic dataset â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Setting up test dataset ===")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clean any previous test data
db.query(AttemptQuestion).filter(
    AttemptQuestion.attempt_id.in_(
        db.query(AssessmentAttempt.id).filter(AssessmentAttempt.assessment_id == 999)
    )
).delete(synchronize_session="fetch")
db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == 999).delete()
db.query(Question).filter(Question.assessment_id == 999).delete()
db.query(Assessment).filter(Assessment.id == 999).delete()
db.query(Student).filter(Student.school_id.in_(
    db.query(School.id).filter(School.name.in_(["Alpha School", "Beta School"]))
)).delete(synchronize_session="fetch")
db.query(Section).filter(Section.school_id.in_(
    db.query(School.id).filter(School.name.in_(["Alpha School", "Beta School"]))
)).delete(synchronize_session="fetch")
db.query(School).filter(School.name.in_(["Alpha School", "Beta School"])).delete()
# Only delete our test academic year if no other assessments reference it
test_ay = db.query(AcademicYear).filter(AcademicYear.name == "TEST-M6A").first()
if test_ay:
    db.delete(test_ay)
db.commit()

# Academic year
ay = AcademicYear(name="TEST-M6A")
db.add(ay)
db.flush()

# Schools
school_a = School(name="Alpha School")
school_b = School(name="Beta School")
db.add_all([school_a, school_b])
db.flush()

# Sections
db.add_all([
    Section(school_id=school_a.id, class_number=6, section_name="A"),
    Section(school_id=school_a.id, class_number=6, section_name="B"),
    Section(school_id=school_b.id, class_number=7, section_name="A"),
])
db.flush()

# Students
alice = Student(school_id=school_a.id, roll_number=1, student_name="Alice",
                current_class=6, current_section="A")
bob = Student(school_id=school_a.id, roll_number=2, student_name="Bob",
              current_class=6, current_section="A")
charlie = Student(school_id=school_a.id, roll_number=3, student_name="Charlie",
                  current_class=6, current_section="B")
diana = Student(school_id=school_b.id, roll_number=1, student_name="Diana",
                current_class=7, current_section="A")
eve = Student(school_id=school_b.id, roll_number=2, student_name="Eve",
              current_class=7, current_section="A")
db.add_all([alice, bob, charlie, diana, eve])
db.flush()

# Assessment
assessment = Assessment(
    id=999,
    name="Science Test",
    assessment_type=AssessmentType.BASELINE,
    academic_year_id=ay.id,
    class_number=6,
)
db.add(assessment)
db.flush()

# Questions (10 questions, 2 domains)
questions_data = [
    (1, "Knowledge", "A"), (2, "Knowledge", "B"), (3, "Knowledge", "C"),
    (4, "Knowledge", "D"), (5, "Knowledge", "A"),
    (6, "Application", "B"), (7, "Application", "C"), (8, "Application", "D"),
    (9, "Application", "A"), (10, "Application", "B"),
]
questions = []
for qn, domain, correct in questions_data:
    q = Question(
        assessment_id=999, question_number=qn,
        question_text=f"Q{qn} text", correct_option=correct, domain=domain,
    )
    db.add(q)
    questions.append(q)
db.flush()

# Attempts with specific detected answers
# Format: student, score, detected_answers (list of 10)
attempts_data = [
    # Alice: 8/10 â€” Q6 wrong (detected A, correct B), Q9 wrong (detected B, correct A)
    (alice, 8, ["A","B","C","D","A", "A","C","D","B","B"]),
    # Bob: 7/10 â€” Q6 wrong (A), Q9 wrong (B), Q10 wrong (A)
    (bob, 7, ["A","B","C","D","A", "A","C","D","B","A"]),
    # Charlie: 6/10 â€” Q3 wrong (D), Q8 wrong (A), Q10 wrong (A)
    (charlie, 6, ["A","B","D","D","A", "B","C","A","A","A"]),
    # Diana: 9/10 â€” Q9 wrong (B)
    (diana, 9, ["A","B","C","D","A", "B","C","D","B","B"]),
    # Eve: 7/10 â€” Q2 wrong (C), Q6 wrong (A)
    (eve, 7, ["A","C","C","D","A", "A","C","D","A","B"]),
]

for student, score, detected in attempts_data:
    att = AssessmentAttempt(
        assessment_id=999,
        student_id=student.id,
        processing_session_id=1,  # dummy
        score=score,
        total_questions=10,
        percentage=Decimal(str(score)) / Decimal("10") * Decimal("100"),
        status=AttemptStatus.COMPLETED,
    )
    db.add(att)
    db.flush()

    for i, q in enumerate(questions):
        aq = AttemptQuestion(
            attempt_id=att.id,
            question_id=q.id,
            detected_answer=detected[i],
            correct_answer=q.correct_option,
            is_correct=(detected[i] == q.correct_option),
            domain=q.domain,
        )
        db.add(aq)

db.commit()
print(f"  Created: 2 schools, 5 students, 1 assessment, 10 questions, 5 attempts")


# â”€â”€ Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

from app.services.analytics_service import (
    assessment_overview,
    school_analytics,
    student_analytics,
    _competition_rank,
    _percentile,
)


# â”€â”€ Test 1-5: Student analytics (Alice) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 1-5: Student analytics (Alice, assessment 999) ===")
sa = student_analytics(db, 999, alice.id)

test("1. Student score", sa["score"] == 8,
     f"Expected 8, got {sa['score']}")
test("2. Student wrong count", sa["wrong"] == 2,
     f"Expected 2, got {sa['wrong']}")
test("3. Student percentage", abs(sa["percentage"] - 80.0) < 0.01,
     f"Expected 80.0, got {sa['percentage']}")
test("4. Student total_questions", sa["total_questions"] == 10,
     f"Expected 10, got {sa['total_questions']}")

# Domain breakdown for Alice
alice_domains = {d["domain"]: d for d in sa["domains"]}
test("5a. Alice Knowledge correct", alice_domains["Knowledge"]["correct"] == 5,
     f"Expected 5, got {alice_domains['Knowledge']['correct']}")
test("5b. Alice Knowledge pct", abs(alice_domains["Knowledge"]["percentage"] - 100.0) < 0.01,
     f"Expected 100.0, got {alice_domains['Knowledge']['percentage']}")
test("5c. Alice Application correct", alice_domains["Application"]["correct"] == 3,
     f"Expected 3, got {alice_domains['Application']['correct']}")
test("5d. Alice Application pct", abs(alice_domains["Application"]["percentage"] - 60.0) < 0.01,
     f"Expected 60.0, got {alice_domains['Application']['percentage']}")


# â”€â”€ Test 6-8: Student rank & percentile (Alice) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 6-8: Student rank & percentile (Alice) ===")
test("6. Alice overall rank", sa["overall_rank"] == 2,
     f"Expected 2, got {sa['overall_rank']}")
test("7. Alice school rank", sa["school_rank"] == 1,
     f"Expected 1, got {sa['school_rank']}")
test("8a. Alice overall percentile", abs(sa["overall_percentile"] - 60.0) < 0.01,
     f"Expected 60.0, got {sa['overall_percentile']}")
test("8b. Alice school percentile", abs(sa["school_percentile"] - 66.67) < 0.1,
     f"Expected 66.67, got {sa['school_percentile']}")


# â”€â”€ Test 9-10: School average & overall average â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 9-10: School & overall averages ===")
test("9. Alice school average", abs(sa["school_average"] - 70.0) < 0.01,
     f"Expected 70.0, got {sa['school_average']}")
test("10. Alice overall average", abs(sa["overall_average"] - 74.0) < 0.01,
     f"Expected 74.0, got {sa['overall_average']}")


# â”€â”€ Test 11-13: Assessment overview â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 11-13: Assessment overview ===")
ov = assessment_overview(db, 999)

test("11a. Total students assessed", ov["total_students_assessed"] == 5,
     f"Expected 5, got {ov['total_students_assessed']}")
test("11b. Average score", abs(ov["average_score"] - 7.4) < 0.01,
     f"Expected 7.4, got {ov['average_score']}")
test("11c. Average percentage", abs(ov["average_percentage"] - 74.0) < 0.01,
     f"Expected 74.0, got {ov['average_percentage']}")
test("11d. Highest percentage", abs(ov["highest_percentage"] - 90.0) < 0.01,
     f"Expected 90.0, got {ov['highest_percentage']}")
test("11e. Lowest percentage", abs(ov["lowest_percentage"] - 60.0) < 0.01,
     f"Expected 60.0, got {ov['lowest_percentage']}")

# Domain breakdown
ov_domains = {d["domain"]: d for d in ov["domains"]}
test("12a. Knowledge correct (all)", ov_domains["Knowledge"]["correct"] == 23,
     f"Expected 23, got {ov_domains['Knowledge']['correct']}")
test("12b. Knowledge total (all)", ov_domains["Knowledge"]["total"] == 25,
     f"Expected 25, got {ov_domains['Knowledge']['total']}")
test("12c. Knowledge pct", abs(ov_domains["Knowledge"]["percentage"] - 92.0) < 0.01,
     f"Expected 92.0, got {ov_domains['Knowledge']['percentage']}")
test("12d. Application correct (all)", ov_domains["Application"]["correct"] == 16,
     f"Expected 16, got {ov_domains['Application']['correct']}")
test("12e. Application pct", abs(ov_domains["Application"]["percentage"] - 64.0) < 0.01,
     f"Expected 64.0, got {ov_domains['Application']['percentage']}")

# School summaries
school_summaries = {s["school_id"]: s for s in ov["schools"]}
test("13a. Two school summaries", len(ov["schools"]) == 2,
     f"Expected 2, got {len(ov['schools'])}")
test("13b. School A avg pct", abs(school_summaries[school_a.id]["average_percentage"] - 70.0) < 0.01,
     f"Expected 70.0, got {school_summaries[school_a.id]['average_percentage']}")
test("13c. School B avg pct", abs(school_summaries[school_b.id]["average_percentage"] - 80.0) < 0.01,
     f"Expected 80.0, got {school_summaries[school_b.id]['average_percentage']}")
test("13d. School A rank", school_summaries[school_a.id]["school_rank"] == 2,
     f"Expected 2, got {school_summaries[school_a.id]['school_rank']}")
test("13e. School B rank", school_summaries[school_b.id]["school_rank"] == 1,
     f"Expected 1, got {school_summaries[school_b.id]['school_rank']}")


# â”€â”€ Test 14: School analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 14: School analytics (Alpha School) ===")
sba = school_analytics(db, 999, school_a.id)

test("14a. School A students assessed", sba["students_assessed"] == 3,
     f"Expected 3, got {sba['students_assessed']}")
test("14b. School A avg score", abs(sba["average_score"] - 7.0) < 0.01,
     f"Expected 7.0, got {sba['average_score']}")
test("14c. School A avg pct", abs(sba["average_percentage"] - 70.0) < 0.01,
     f"Expected 70.0, got {sba['average_percentage']}")
test("14d. School A highest", abs(sba["highest_percentage"] - 80.0) < 0.01,
     f"Expected 80.0, got {sba['highest_percentage']}")
test("14e. School A lowest", abs(sba["lowest_percentage"] - 60.0) < 0.01,
     f"Expected 60.0, got {sba['lowest_percentage']}")
test("14f. School A rank", sba["school_rank"] == 2,
     f"Expected 2, got {sba['school_rank']}")
test("14g. School A has 3 students", len(sba["students"]) == 3,
     f"Expected 3, got {len(sba['students'])}")


# â”€â”€ Test 15: Class filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 15: Class filter ===")
ov_class6 = assessment_overview(db, 999, class_number=6)
test("15a. Class 6 students", ov_class6["total_students_assessed"] == 3,
     f"Expected 3, got {ov_class6['total_students_assessed']}")
test("15b. Class 6 avg pct", abs(ov_class6["average_percentage"] - 70.0) < 0.01,
     f"Expected 70.0, got {ov_class6['average_percentage']}")

ov_class7 = assessment_overview(db, 999, class_number=7)
test("15c. Class 7 students", ov_class7["total_students_assessed"] == 2,
     f"Expected 2, got {ov_class7['total_students_assessed']}")
test("15d. Class 7 avg pct", abs(ov_class7["average_percentage"] - 80.0) < 0.01,
     f"Expected 80.0, got {ov_class7['average_percentage']}")


# â”€â”€ Test 16: Section filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 16: Section filter ===")
ov_secA = assessment_overview(db, 999, class_number=6, section="A")
test("16a. Section 6A students", ov_secA["total_students_assessed"] == 2,
     f"Expected 2, got {ov_secA['total_students_assessed']}")
# Alice 80, Bob 70 â†’ avg 75
test("16b. Section 6A avg pct", abs(ov_secA["average_percentage"] - 75.0) < 0.01,
     f"Expected 75.0, got {ov_secA['average_percentage']}")

ov_secB = assessment_overview(db, 999, class_number=6, section="B")
test("16c. Section 6B students", ov_secB["total_students_assessed"] == 1,
     f"Expected 1, got {ov_secB['total_students_assessed']}")
test("16d. Section 6B avg pct", abs(ov_secB["average_percentage"] - 60.0) < 0.01,
     f"Expected 60.0, got {ov_secB['average_percentage']}")


# â”€â”€ Test 17: Assessment with no attempts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 17: Assessment with no attempts ===")
# Assessment 3 exists but has 0 questions and 0 attempts
ov_no_att = assessment_overview(db, 3)
test("17a. No attempts â†’ 0 students", ov_no_att["total_students_assessed"] == 0,
     f"Expected 0, got {ov_no_att['total_students_assessed']}")
test("17b. No attempts â†’ 0 avg pct", ov_no_att["average_percentage"] == 0.0,
     f"Expected 0.0, got {ov_no_att['average_percentage']}")
test("17c. No attempts â†’ empty schools", ov_no_att["schools"] == [],
     f"Expected [], got {ov_no_att['schools']}")


# â”€â”€ Test 18: Single student â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 18: Single student (Diana, school B only)")
# Diana is the only student in school B
sa_diana = student_analytics(db, 999, diana.id)
test("18a. Diana score", sa_diana["score"] == 9,
     f"Expected 9, got {sa_diana['score']}")
test("18b. Diana overall rank", sa_diana["overall_rank"] == 1,
     f"Expected 1, got {sa_diana['overall_rank']}")
test("18c. Diana school rank", sa_diana["school_rank"] == 1,
     f"Expected 1, got {sa_diana['school_rank']}")
test("18d. Diana school percentile", abs(sa_diana["school_percentile"] - 50.0) < 0.01,
     f"Expected 50.0, got {sa_diana['school_percentile']}")
test("18e. Diana overall percentile", abs(sa_diana["overall_percentile"] - 80.0) < 0.01,
     f"Expected 80.0, got {sa_diana['overall_percentile']}")


# â”€â”€ Test 19: Competition ranking with ties â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 19: Competition ranking with ties ===")
ranks = _competition_rank([90.0, 80.0, 70.0, 70.0, 60.0])
test("19a. Rank 90", ranks[90.0] == 1, f"Expected 1, got {ranks[90.0]}")
test("19b. Rank 80", ranks[80.0] == 2, f"Expected 2, got {ranks[80.0]}")
test("19c. Rank 70 (tie)", ranks[70.0] == 3, f"Expected 3, got {ranks[70.0]}")
test("19d. Rank 60", ranks[60.0] == 4, f"Expected 4, got {ranks[60.0]}")

ranks2 = _competition_rank([82.0, 76.0, 76.0, 61.0])
test("19e. Rank 82", ranks2[82.0] == 1, f"Expected 1, got {ranks2[82.0]}")
test("19f. Rank 76 (tie)", ranks2[76.0] == 2, f"Expected 2, got {ranks2[76.0]}")
test("19g. Rank 61", ranks2[61.0] == 3, f"Expected 3, got {ranks2[61.0]}")


# â”€â”€ Test 20: Percentile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 20: Percentile ===")
pct = _percentile(80.0, [90.0, 80.0, 70.0, 70.0, 60.0])
test("20a. Percentile 80", abs(pct - 60.0) < 0.01,
     f"Expected 60.0, got {pct}")
pct2 = _percentile(70.0, [90.0, 80.0, 70.0, 70.0, 60.0])
test("20b. Percentile 70 (tie)", abs(pct2 - 20.0) < 0.01,
     f"Expected 20.0, got {pct2}")
pct3 = _percentile(60.0, [90.0, 80.0, 70.0, 70.0, 60.0])
test("20c. Percentile 60 (lowest)", abs(pct3 - 0.0) < 0.01,
     f"Expected 0.0, got {pct3}")
pct4 = _percentile(90.0, [90.0, 80.0, 70.0, 70.0, 60.0])
test("20d. Percentile 90 (highest)", abs(pct4 - 80.0) < 0.01,
     f"Expected 80.0, got {pct4}")


# â”€â”€ Test 21: Charlie's ranks (rank 5 overall, rank 3 in school A) â”€

print("\n=== Test 21: Charlie ranks ===")
sa_charlie = student_analytics(db, 999, charlie.id)
test("21a. Charlie overall rank", sa_charlie["overall_rank"] == 4,
     f"Expected 4, got {sa_charlie['overall_rank']}")
test("21b. Charlie school rank", sa_charlie["school_rank"] == 3,
     f"Expected 3, got {sa_charlie['school_rank']}")
test("21c. Charlie overall percentile", abs(sa_charlie["overall_percentile"] - 0.0) < 0.01,
     f"Expected 0.0, got {sa_charlie['overall_percentile']}")
test("21d. Charlie school percentile", abs(sa_charlie["school_percentile"] - 0.0) < 0.01,
     f"Expected 0.0, got {sa_charlie['school_percentile']}")


# â”€â”€ Test 22: Eve's tied rank with Bob â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 22: Eve tied rank with Bob ===")
sa_eve = student_analytics(db, 999, eve.id)
sa_bob = student_analytics(db, 999, bob.id)
test("22a. Eve overall rank (tied with Bob)", sa_eve["overall_rank"] == 3,
     f"Expected 3, got {sa_eve['overall_rank']}")
test("22b. Bob overall rank (tied with Eve)", sa_bob["overall_rank"] == 3,
     f"Expected 3, got {sa_bob['overall_rank']}")
test("22c. Eve overall percentile", abs(sa_eve["overall_percentile"] - 20.0) < 0.01,
     f"Expected 20.0, got {sa_eve['overall_percentile']}")
test("22d. Bob overall percentile", abs(sa_bob["overall_percentile"] - 20.0) < 0.01,
     f"Expected 20.0, got {sa_bob['overall_percentile']}")


# â”€â”€ Test 23: 404 errors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Test 23: 404 errors ===")
try:
    school_analytics(db, 999, 99999)
    test("23a. Missing school â†’ error", False, "Should have raised")
except ValueError:
    test("23a. Missing school â†’ error", True)

try:
    student_analytics(db, 999, 99999)
    test("23b. Missing student â†’ error", False, "Should have raised")
except ValueError:
    test("23b. Missing student â†’ error", True)

try:
    student_analytics(db, 998, alice.id)
    test("23c. Missing assessment â†’ error", False, "Should have raised")
except ValueError:
    test("23c. Missing assessment â†’ error", True)

# Student without attempt for this assessment
try:
    # Create a student with no attempt
    fake = Student(school_id=school_a.id, roll_number=99, student_name="Ghost",
                   current_class=6, current_section="A")
    db.add(fake)
    db.flush()
    student_analytics(db, 999, fake.id)
    test("23d. Student without attempt â†’ error", False, "Should have raised")
except ValueError:
    test("23d. Student without attempt â†’ error", True)
finally:
    db.delete(fake)
    db.commit()


# â”€â”€ Cleanup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("\n=== Cleanup ===")
db.query(AttemptQuestion).filter(
    AttemptQuestion.attempt_id.in_(
        db.query(AssessmentAttempt.id).filter(AssessmentAttempt.assessment_id == 999)
    )
).delete(synchronize_session="fetch")
db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == 999).delete()
db.query(Question).filter(Question.assessment_id == 999).delete()
db.query(Assessment).filter(Assessment.id == 999).delete()
db.query(Student).filter(Student.roll_number == 99).delete()
test_ay = db.query(AcademicYear).filter(AcademicYear.name == "TEST-M6A").first()
if test_ay:
    db.delete(test_ay)
db.commit()
db.close()
print("  Cleaned up test data")


# â”€â”€ Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print(f"\n{'='*50}")
print(f"M6A Analytics Tests: {passed} passed, {failed} failed")
print(f"{'='*50}")

if failed > 0:
    sys.exit(1)

