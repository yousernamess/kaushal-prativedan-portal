"""Comprehensive API tests for the Process OMR workflow."""

import io
import os
import sys

import requests

BASE = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "test_uploads")
OMR_SAMPLES = os.path.join(os.path.dirname(__file__), "..", "omrExtractor", "input")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Real OMR sample images: prefer extractor samples, fall back to real images
# in the backend output tree (smoke test / past uploads).
_SAMPLE_CANDIDATES = [
    os.path.join(OMR_SAMPLES, "101.jpeg"),
    os.path.join(os.path.dirname(__file__), "output", "smoke_test", "model_answer_sheet.png"),
    os.path.join(os.path.dirname(__file__), "output", "uploads", "session_18", "irltest.jpeg"),
]
_SAMPLE_1 = next((p for p in _SAMPLE_CANDIDATES if os.path.exists(p)), None)
_SAMPLE_2_CANDIDATES = [
    os.path.join(OMR_SAMPLES, "104.jpeg"),
    os.path.join(os.path.dirname(__file__), "output", "uploads", "session_36", "123.bmp"),
]
_SAMPLE_2 = next((p for p in _SAMPLE_2_CANDIDATES if os.path.exists(p)), None)

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


def create_test_image(filename, content=None):
    """Create a test file in the output directory.
    If content is None, use a real OMR sample image.
    """
    if content is None:
        # Use a real OMR sample image
        sample = _SAMPLE_1
        if sample:
            with open(sample, "rb") as f:
                content = f.read()
        else:
            content = b"\xff\xd8\xff\xe0" + b"\x00" * 500  # minimal JPEG-like bytes
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


# ── Setup: Get existing data ───────────────────────────────────────

print("\n=== Test 1: Get existing assessments and schools ===")
r = requests.get(f"{BASE}/assessments")
test("List assessments", r.status_code == 200)
assessments = r.json()
test("Has assessments", len(assessments) > 0, f"Found {len(assessments)}")
# Pick the first assessment that has questions
assessment = next((a for a in assessments if len(a.get("questions", [])) > 0), assessments[0])
assessment_id = assessment["id"]
print(f"  Using assessment: {assessment['name']} (id={assessment_id}, questions={len(assessment.get('questions', []))})")

r = requests.get(f"{BASE}/schools")
test("List schools", r.status_code == 200)
schools = r.json()
test("Has schools", len(schools) > 0, f"Found {len(schools)}")
school = schools[0]
school_id = school["id"]
print(f"  Using school: {school['name']} (id={school_id}, students={school['student_count']})")

# Get students for this school
r = requests.get(f"{BASE}/students", params={"school_id": school_id})
students = r.json()
test("Has students", len(students) > 0, f"Found {len(students)}")
print(f"  Students: {[s['roll_number'] for s in students[:5]]}")


# ── Test 2: Create session with valid files ───────────────────────

print("\n=== Test 2: Create session with valid and invalid files ===")
# Create test files using real OMR images for valid entries
test_files = []
first_student_roll = str(students[0]["roll_number"])
second_student_roll = str(students[1]["roll_number"]) if len(students) > 1 else "999"

# Load real OMR images for valid files
with open(_SAMPLE_1, "rb") as f:
    real_img_1 = f.read()
with open(_SAMPLE_2, "rb") as f:
    real_img_2 = f.read()

# Valid files (real OMR images)
test_files.append(("files", (first_student_roll + ".jpeg", real_img_1, "image/jpeg")))
test_files.append(("files", (second_student_roll + ".jpeg", real_img_2, "image/jpeg")))
# Invalid filename
test_files.append(("files", ("invalid_name.jpg", real_img_1, "image/jpeg")))
# Unsupported extension
test_files.append(("files", ("123.bmp", real_img_1, "image/bmp")))

r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": assessment_id, "school_id": school_id},
    files=test_files,
)
test("Create session", r.status_code == 201, f"Got {r.status_code}: {r.text[:200]}")
session = r.json()
session_id = session["id"]
test("Session has id", session_id is not None)
test("Session total_files", session["total_files"] == 4, f"Expected 4, got {session['total_files']}")
test("Session status is pending", session["status"] == "PENDING")
test("Session has assessment", session["assessment"]["id"] == assessment_id)
test("Session has school", session["school"]["id"] == school_id)
test("Session question_count", session["assessment"]["question_count"] == len(assessment.get("questions", [])))
print(f"  Session #{session_id} created with {session['total_files']} files")


# ── Test 3: Validate session ──────────────────────────────────────

print("\n=== Test 3: Validate session ===")
r = requests.post(f"{BASE}/processing-sessions/{session_id}/validate")
test("Validate session", r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}")
session = r.json()
test("Session has valid files", session["valid_files"] >= 1, f"Valid: {session['valid_files']}")
test("Session has invalid files", session["invalid_files"] >= 1, f"Invalid: {session['invalid_files']}")
test("Session status is ready or failed",
     session["status"] in ("READY", "FAILED"),
     f"Status: {session['status']}")

# Check individual file statuses
valid_files = [f for f in session["files"] if f["status"] == "VALID"]
invalid_files = [f for f in session["files"] if f["status"] == "INVALID"]
test("Valid files have student_id", all(f["student_id"] is not None for f in valid_files))
test("Invalid files have error_message", all(f["error_message"] is not None for f in invalid_files))
print(f"  Valid: {len(valid_files)}, Invalid: {len(invalid_files)}")
for f in invalid_files:
    print(f"    INVALID: {f['original_filename']} — {f['error_message']}")


# ── Test 4: Process session ───────────────────────────────────────

if session["status"] == "READY" and session["valid_files"] > 0:
    print("\n=== Test 4: Process session ===")
    r = requests.post(f"{BASE}/processing-sessions/{session_id}/process")
    test("Process session", r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}")
    session = r.json()
    test("Session status is completed or partial",
            session["status"] in ("COMPLETED", "PARTIAL"),
         f"Status: {session['status']}")
    test("Session successful_files >= 1", session["successful_files"] >= 1)
    print(f"  Successful: {session['successful_files']}, Failed: {session['failed_files']}")

    # Check progress endpoint
    r = requests.get(f"{BASE}/processing-sessions/{session_id}/progress")
    test("Get progress", r.status_code == 200)
    progress = r.json()
    test("Progress total", progress["total"] == session["valid_files"])
    test("Progress processed", progress["processed"] == session["successful_files"] + session["failed_files"])
    test("Progress remaining", progress["remaining"] == 0)
else:
    print("\n=== Test 4: Skipped (no valid files to process) ===")


# ── Test 5: Duplicate roll number in batch ────────────────────────

print("\n=== Test 5: Duplicate roll number detection ===")
# Use a roll number that actually exists in the selected school, so the
# duplicate check (not the "no student found" check) is what triggers.
dup_roll = str(students[0]["roll_number"])
dup_files = []
dup_files.append(("files", (dup_roll + ".jpeg", real_img_1, "image/jpeg")))
dup_files.append(("files", (dup_roll + ".jpeg", real_img_1, "image/jpeg")))
if len(students) > 1:
    dup_files.append(("files", (str(students[1]["roll_number"]) + ".jpeg", real_img_2, "image/jpeg")))

r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": assessment_id, "school_id": school_id},
    files=dup_files,
)
test("Create session with dups", r.status_code == 201)
dup_session = r.json()
dup_session_id = dup_session["id"]

# Validate
r = requests.post(f"{BASE}/processing-sessions/{dup_session_id}/validate")
test("Validate dup session", r.status_code == 200)
dup_session = r.json()

dup_files_list = dup_session["files"]
dup_invalid = [f for f in dup_files_list if f["status"] == "INVALID"]
test("Duplicate files are invalid", len(dup_invalid) >= 2, f"Invalid count: {len(dup_invalid)}")
if dup_invalid:
    test("Dup error message mentions duplicate",
         "Duplicate" in (dup_invalid[0].get("error_message") or ""),
         f"Error: {dup_invalid[0].get('error_message')}")
    print(f"  Dup error: {dup_invalid[0]['error_message']}")

# Cleanup
requests.delete(f"{BASE}/processing-sessions/{dup_session_id}")


# ── Test 6: Get session detail ────────────────────────────────────

print("\n=== Test 6: Get session detail ===")
r = requests.get(f"{BASE}/processing-sessions/{session_id}")
test("Get session", r.status_code == 200)
detail = r.json()
test("Session has files array", "files" in detail)
test("Files count matches", len(detail["files"]) == detail["total_files"])
test("Session has assessment summary", "question_count" in detail["assessment"])


# ── Test 7: List sessions ─────────────────────────────────────────

print("\n=== Test 7: List sessions ===")
r = requests.get(f"{BASE}/processing-sessions")
test("List sessions", r.status_code == 200)
sessions_list = r.json()
test("Sessions list not empty", len(sessions_list) >= 1)
test("Session in list has assessment", "assessment" in sessions_list[0])
test("Session in list has school", "school" in sessions_list[0])


# ── Test 8: Delete session ────────────────────────────────────────

print("\n=== Test 8: Delete session ===")
# Create a session to delete
del_files = [("files", ("500.jpeg", real_img_1, "image/jpeg"))]
r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": assessment_id, "school_id": school_id},
    files=del_files,
)
test("Create session to delete", r.status_code == 201)
del_session_id = r.json()["id"]

r = requests.delete(f"{BASE}/processing-sessions/{del_session_id}")
test("Delete session", r.status_code == 204)

r = requests.get(f"{BASE}/processing-sessions/{del_session_id}")
test("Deleted session not found", r.status_code == 404)


# ── Test 9: Error cases ───────────────────────────────────────────

print("\n=== Test 9: Error cases ===")
# Non-existent assessment
r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": 99999, "school_id": school_id},
    files=[("files", ("1.jpg", b"x", "image/jpeg"))],
)
test("Non-existent assessment", r.status_code == 404)

# Non-existent school
r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": assessment_id, "school_id": 99999},
    files=[("files", ("1.jpg", b"x", "image/jpeg"))],
)
test("Non-existent school", r.status_code == 404)

# Process non-ready session
r = requests.post(f"{BASE}/processing-sessions/{session_id}/process")
test("Process non-ready session", r.status_code == 422, f"Got {r.status_code}")

# Retry with no failed files
r = requests.post(
    f"{BASE}/processing-sessions/{session_id}/retry",
    json={"file_ids": [99999]},
)
test("Retry non-existent file", r.status_code == 404)


# ── Summary ───────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
print(f"{'='*50}")

sys.exit(0 if failed == 0 else 1)
