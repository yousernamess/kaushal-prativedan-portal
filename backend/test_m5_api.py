"""M5 API integration test — tests the full Process OMR workflow via HTTP."""

import os
import shutil
import sys
import requests

BASE = "http://127.0.0.1:8000"
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "omrExtractor", "input")

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


# ── Setup ──────────────────────────────────────────────────────────

print("\n=== Setup: Get existing data ===")
r = requests.get(f"{BASE}/assessments")
test("List assessments", r.status_code == 200)
assessments = r.json()
# Find assessment with most questions
assessments_with_q = [a for a in assessments if len(a.get("questions", [])) > 0]
test("Has assessments with questions", len(assessments_with_q) > 0)
assessment = assessments_with_q[0]
assessment_id = assessment["id"]
question_count = len(assessment["questions"])
print(f"  Using: {assessment['name']} (id={assessment_id}, {question_count} questions)")

r = requests.get(f"{BASE}/schools")
schools = r.json()
school = next((s for s in schools if s.get("student_count", 0) > 0), None)
test("Found school with students", school is not None)
school_id = school["id"]
print(f"  Using: {school['name']} (id={school_id})")

r = requests.get(f"{BASE}/students", params={"school_id": school_id})
students = r.json()
test("Has students", len(students) >= 2, f"Found {len(students)}")
student1 = students[0]
student2 = students[1]
print(f"  Student 1: roll={student1['roll_number']}, name={student1['student_name']}")
print(f"  Student 2: roll={student2['roll_number']}, name={student2['student_name']}")


# ── Test 1: Create session with real OMR files ─────────────────────

print("\n=== Test 1: Create session with real OMR files ===")
test_files = []
sample1 = next(
    (p for p in [
        os.path.join(SAMPLE_DIR, "101.jpeg"),
        os.path.join(os.path.dirname(__file__), "output", "smoke_test", "model_answer_sheet.png"),
        os.path.join(os.path.dirname(__file__), "output", "uploads", "session_18", "irltest.jpeg"),
    ] if os.path.exists(p)),
    None,
)
sample2 = next(
    (p for p in [
        os.path.join(SAMPLE_DIR, "104.jpeg"),
        os.path.join(os.path.dirname(__file__), "output", "uploads", "session_36", "123.bmp"),
    ] if os.path.exists(p)),
    None,
)
test("Sample image 1 exists", sample1 is not None)
test("Sample image 2 exists", sample2 is not None)

if sample1 and sample2:
    # Upload files named after student roll numbers
    with open(sample1, "rb") as f:
        test_files.append(("files", (f"{student1['roll_number']}.jpeg", f.read(), "image/jpeg")))
    with open(sample2, "rb") as f:
        test_files.append(("files", (f"{student2['roll_number']}.jpeg", f.read(), "image/jpeg")))
    # Add an invalid file
    test_files.append(("files", ("invalid_name.jpg", b"bad", "image/jpeg")))

    r = requests.post(
        f"{BASE}/processing-sessions",
        params={"assessment_id": assessment_id, "school_id": school_id},
        files=test_files,
    )
    test("Create session", r.status_code == 201, f"Got {r.status_code}: {r.text[:200]}")
    session = r.json()
    session_id = session["id"]
    test("Session has files", session["total_files"] == 3, f"Got {session['total_files']}")
    print(f"  Session #{session_id} created")


# ── Test 2: Validate ───────────────────────────────────────────────

print("\n=== Test 2: Validate session ===")
r = requests.post(f"{BASE}/processing-sessions/{session_id}/validate")
test("Validate session", r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}")
session = r.json()
test("Has valid files", session["valid_files"] >= 2, f"Valid: {session['valid_files']}")
test("Has invalid files", session["invalid_files"] >= 1, f"Invalid: {session['invalid_files']}")
test("Status is READY", session["status"] == "READY", f"Got {session['status']}")
print(f"  Valid: {session['valid_files']}, Invalid: {session['invalid_files']}")


# ── Test 3: Process (the big one!) ─────────────────────────────────

print("\n=== Test 3: Process session ===")
r = requests.post(f"{BASE}/processing-sessions/{session_id}/process")
test("Process session", r.status_code == 200, f"Got {r.status_code}: {r.text[:300]}")
session = r.json()
test("Status is COMPLETED or PARTIAL",
     session["status"] in ("COMPLETED", "PARTIAL"),
     f"Got {session['status']}")
test("Has successful files", session["successful_files"] >= 2,
     f"Successful: {session['successful_files']}")
print(f"  Status: {session['status']}")
print(f"  Successful: {session['successful_files']}, Failed: {session['failed_files']}")


# ── Test 4: Verify results have attempt data ───────────────────────

print("\n=== Test 4: Verify attempt data in results ===")
processed_files = [f for f in session["files"] if f["status"] == "PROCESSED"]
test("Has processed files", len(processed_files) >= 2, f"Got {len(processed_files)}")

for f in processed_files:
    att = f.get("attempt")
    test(f"File {f['original_filename']} has attempt", att is not None)
    if att:
        test(f"  Attempt has score", "score" in att and isinstance(att["score"], int))
        test(f"  Attempt has total_questions", att.get("total_questions") == question_count,
             f"Got {att.get('total_questions')}")
        test(f"  Attempt has percentage", "percentage" in att and att["percentage"] >= 0)
        test(f"  Attempt has questions", len(att.get("questions", [])) == question_count,
             f"Got {len(att.get('questions', []))}")

        # Verify question-level data
        for q in att.get("questions", []):
            test(f"  Q has correct_answer", q.get("correct_answer") in ["A", "B", "C", "D"])
            test(f"  Q has is_correct", isinstance(q.get("is_correct"), bool))
            test(f"  Q has domain", len(q.get("domain", "")) > 0)

        print(f"  {f['student_name']}: {att['score']}/{att['total_questions']} = {att['percentage']}%")


# ── Test 5: Verify invalid files NOT processed ─────────────────────

print("\n=== Test 5: Invalid files not processed ===")
invalid_files = [f for f in session["files"] if f["status"] == "INVALID"]
for f in invalid_files:
    test(f"Invalid file {f['original_filename']} has no attempt", f.get("attempt") is None)
    test(f"  Has error message", f.get("error_message") is not None)


# ── Test 6: Get session detail ─────────────────────────────────────

print("\n=== Test 6: Get session detail ===")
r = requests.get(f"{BASE}/processing-sessions/{session_id}")
test("Get session detail", r.status_code == 200)
detail = r.json()
test("Detail has files", len(detail["files"]) == detail["total_files"])
test("Detail has attempt data", any(f.get("attempt") for f in detail["files"]))


# ── Test 7: Progress endpoint ──────────────────────────────────────

print("\n=== Test 7: Progress endpoint ===")
r = requests.get(f"{BASE}/processing-sessions/{session_id}/progress")
test("Get progress", r.status_code == 200)
progress = r.json()
test("Progress shows no remaining", progress["remaining"] == 0)
test("Progress processed matches", progress["processed"] == progress["successful"] + progress["failed"])


# ── Test 8: Cleanup — delete test session ──────────────────────────

print("\n=== Test 8: Delete session ===")
r = requests.delete(f"{BASE}/processing-sessions/{session_id}")
test("Delete session", r.status_code == 204, f"Got {r.status_code}")


# ── Summary ────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"API Test Results: {passed} passed, {failed} failed")
print(f"{'='*50}")
if failed > 0:
    sys.exit(1)
