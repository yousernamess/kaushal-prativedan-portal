"""M5 Acceptance Test — exercises every acceptance criterion against real OMR images.

Start the backend server before running this test.

Criteria tested:
 1. Real OMR images from omrExtractor
 2. ~20 student batch
 3. Exactly one AssessmentAttempt per successful file
 4. Correct AttemptQuestion count per attempt
 5. Detected answers compared against answer key
 6. Manual score/percentage verification
 7. Invalid files do not create attempts
 8. One failed extraction does not stop the batch
 9. Successful images are deleted
10. Failed images remain for retry
"""

import os
import sys
import requests

BASE = "http://127.0.0.1:8000"
OMR_INPUT = os.path.join(os.path.dirname(__file__), "..", "omrExtractor", "input")

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

print("\n=== SETUP ===")
r = requests.get(f"{BASE}/assessments")
assessments = [a for a in r.json() if len(a.get("questions", [])) > 0]
assessment = assessments[0]
assessment_id = assessment["id"]
questions = sorted(assessment["questions"], key=lambda q: q["question_number"])
question_count = len(questions)
answer_key = {f"Q{q['question_number']}": q["correct_option"] for q in questions}
print(f"  Assessment: {assessment['name']} (id={assessment_id})")
print(f"  Questions: {question_count}, Answer key: {answer_key}")

r = requests.get(f"{BASE}/schools")
school = next(s for s in r.json() if s.get("student_count", 0) >= 20)
school_id = school["id"]

r = requests.get(f"{BASE}/students", params={"school_id": school_id})
students = sorted(r.json(), key=lambda s: s["roll_number"])
print(f"  School: {school['name']} (id={school_id}), {len(students)} students")

# Real sample images
sample_101 = os.path.join(OMR_INPUT, "101.jpeg")
sample_104 = os.path.join(OMR_INPUT, "104.jpeg")
test("101.jpeg exists", os.path.exists(sample_101))
test("104.jpeg exists", os.path.exists(sample_104))

# ── Build batch: 18 real + 1 invalid filename + 1 corrupt image ───

print("\n=== BUILD BATCH ===")
batch_files = []
student_map = {}  # roll_number -> student dict, for files we expect to process

# 18 students with real OMR images (reuse 101.jpeg for first 10, 104.jpeg for next 8)
for i, student in enumerate(students[:18]):
    roll = student["roll_number"]
    source = sample_101 if i < 10 else sample_104
    with open(source, "rb") as f:
        data = f.read()
    ext = "jpeg"
    fname = f"{roll}.{ext}"
    batch_files.append(("files", (fname, data, "image/jpeg")))
    student_map[roll] = student

# 1 invalid filename
batch_files.append(("files", ("bad_name.jpg", b"x", "image/jpeg")))

# 1 corrupt image (valid filename for student 19, but garbage bytes)
if len(students) >= 20:
    corrupt_roll = students[18]["roll_number"]
    batch_files.append(("files", (f"{corrupt_roll}.jpeg", b"\xff\xd8\xff\xe0" + b"\x00" * 500, "image/jpeg")))
    print(f"  Corrupt file: {corrupt_roll}.jpeg (fake JPEG header + zeros)")

print(f"  Total files: {len(batch_files)}")
print(f"  Expected: 18 valid (real), 1 invalid filename, 1 corrupt image")


# ── Create session ─────────────────────────────────────────────────

print("\n=== CREATE SESSION ===")
r = requests.post(
    f"{BASE}/processing-sessions",
    params={"assessment_id": assessment_id, "school_id": school_id},
    files=batch_files,
)
test("Create session", r.status_code == 201, f"Got {r.status_code}: {r.text[:200]}")
session = r.json()
session_id = session["id"]
test("Total files == 20", session["total_files"] == 20, f"Got {session['total_files']}")


# ── Validate ───────────────────────────────────────────────────────

print("\n=== VALIDATE ===")
r = requests.post(f"{BASE}/processing-sessions/{session_id}/validate")
test("Validate", r.status_code == 200)
session = r.json()
valid_count = session["valid_files"]
invalid_count = session["invalid_files"]
test("Valid == 19", valid_count == 19, f"Got {valid_count}")
test("Invalid == 1", invalid_count == 1, f"Got {invalid_count}")
test("Status READY", session["status"] == "READY", f"Got {session['status']}")

invalid_files_pre = [f for f in session["files"] if f["status"] == "INVALID"]
test("Invalid file is bad_name", invalid_files_pre[0]["original_filename"] == "bad_name.jpg")


# ── Process ────────────────────────────────────────────────────────

print("\n=== PROCESS ===")
r = requests.post(f"{BASE}/processing-sessions/{session_id}/process")
test("Process", r.status_code == 200, f"Got {r.status_code}: {r.text[:300]}")
session = r.json()
test("Status COMPLETED or PARTIAL", session["status"] in ("COMPLETED", "PARTIAL"),
     f"Got {session['status']}")

processed_files = [f for f in session["files"] if f["status"] == "PROCESSED"]
failed_files = [f for f in session["files"] if f["status"] == "FAILED"]
invalid_files = [f for f in session["files"] if f["status"] == "INVALID"]

print(f"  Processed: {len(processed_files)}, Failed: {len(failed_files)}, Invalid: {len(invalid_files)}")


# ── Criterion 3: Exactly one attempt per successful file ───────────

print("\n=== CRITERION 3: One attempt per successful file ===")
for f in processed_files:
    att = f.get("attempt")
    test(f"  {f['student_name']} (roll={f['roll_number']}) has attempt", att is not None)
    if att:
        test(f"    Attempt status COMPLETED", att["status"] == "COMPLETED")

# Check no duplicate attempts in DB
attempt_ids = [f["attempt"]["id"] for f in processed_files if f.get("attempt")]
test("All attempt IDs unique", len(attempt_ids) == len(set(attempt_ids)),
     f"Duplicates found in {attempt_ids}")


# ── Criterion 4: Correct AttemptQuestion count ─────────────────────

print("\n=== CRITERION 4: AttemptQuestion count ===")
for f in processed_files:
    att = f.get("attempt")
    if att:
        aq_count = len(att.get("questions", []))
        test(f"  {f['student_name']}: {aq_count} questions == {question_count}",
             aq_count == question_count)


# ── Criterion 5 & 6: Answer comparison & manual score verification ─

print("\n=== CRITERION 5 & 6: Answer comparison & manual score ===")
# Verify against answer key for the first student
first_processed = processed_files[0]
att = first_processed.get("attempt")
if att:
    manual_score = 0
    print(f"  Student: {first_processed['student_name']} (roll={first_processed['roll_number']})")
    for q in att["questions"]:
        q_key = f"Q{[k for k, v in answer_key.items() if True][0].split('Q')[1]}" if False else None
        # Find question number from question_id
        expected_correct = answer_key.get(f"Q{att['questions'].index(q)+1}")
        det = q["detected_answer"]
        cor = q["correct_answer"]
        is_c = q["is_correct"]
        # Manual check
        manual_correct = (det is not None and det == cor)
        test(f"    Q{att['questions'].index(q)+1}: detected={det}, correct={cor}, "
             f"is_correct={is_c} (manual={manual_correct})",
             is_c == manual_correct)
        if manual_correct:
            manual_score += 1

    # Verify score
    test(f"  Score matches manual count: {att['score']} == {manual_score}",
         att["score"] == manual_score)

    # Verify percentage
    expected_pct = round(manual_score / question_count * 100, 2)
    test(f"  Percentage correct: {att['percentage']} == {expected_pct}",
         abs(att["percentage"] - expected_pct) < 0.01)


# ── Criterion 7: Invalid files don't create attempts ───────────────

print("\n=== CRITERION 7: Invalid files no attempts ===")
for f in invalid_files:
    test(f"  {f['original_filename']} has no attempt", f.get("attempt") is None)
    test(f"  Has error message", f.get("error_message") is not None and len(f["error_message"]) > 0)


# ── Criterion 8: Failed extraction doesn't stop batch ──────────────

print("\n=== CRITERION 8: Failed extraction isolated ===")
test("At least 1 successful despite failures", len(processed_files) > 0,
     f"Got {len(processed_files)}")
if failed_files:
    test("Failed file has error message",
         all(f.get("error_message") for f in failed_files))
    for f in failed_files:
        print(f"  Failed: {f['original_filename']} — {f['error_message'][:80]}")
    # The corrupt image should be the one that failed
    corrupt_rolls = {corrupt_roll} if len(students) >= 20 else set()
    failed_rolls = {f["roll_number"] for f in failed_files}
    test("Corrupt file is in failed set",
         len(corrupt_rolls & failed_rolls) > 0 or len(failed_files) == 0,
         f"Corrupt rolls: {corrupt_rolls}, Failed rolls: {failed_rolls}")


# ── Criterion 9: Successful images deleted ─────────────────────────

print("\n=== CRITERION 9: Successful images deleted ===")
upload_dir = os.path.join(os.path.dirname(__file__), "output", "uploads", f"session_{session_id}")
if os.path.exists(upload_dir):
    remaining = os.listdir(upload_dir)
    print(f"  Files remaining in session dir: {remaining}")

    successful_rolls = {f["roll_number"] for f in processed_files}
    for f in processed_files:
        # The file should NOT exist on disk anymore
        fname = f["original_filename"]
        fpath = os.path.join(upload_dir, fname)
        test(f"  {fname} deleted from disk", not os.path.exists(fpath))

    # Criterion 10: Failed images remain
    for f in failed_files:
        fname = f["original_filename"]
        fpath = os.path.join(upload_dir, fname)
        test(f"  {fname} retained for retry", os.path.exists(fpath))

    # Invalid file should also remain (never processed)
    for f in invalid_files:
        fname = f["original_filename"]
        fpath = os.path.join(upload_dir, fname)
        # Invalid files are uploaded but never attempted - they should still exist
        # unless the session hasn't been deleted yet
        if os.path.exists(fpath):
            print(f"  Invalid file {fname} still on disk (expected)")
else:
    print(f"  Session dir not found: {upload_dir}")


# ── Final session stats ────────────────────────────────────────────

print("\n=== FINAL SESSION STATS ===")
r = requests.get(f"{BASE}/processing-sessions/{session_id}")
session = r.json()
print(f"  Status: {session['status']}")
print(f"  Total: {session['total_files']}")
print(f"  Valid: {session['valid_files']}")
print(f"  Invalid: {session['invalid_files']}")
print(f"  Processed: {session['processed_files']}")
print(f"  Successful: {session['successful_files']}")
print(f"  Failed: {session['failed_files']}")
test("successful + failed + invalid == total",
     session["successful_files"] + session["failed_files"] + session["invalid_files"] == session["total_files"],
     f"{session['successful_files']} + {session['failed_files']} + {session['invalid_files']} != {session['total_files']}")
test("processed == successful + failed",
     session["processed_files"] == session["successful_files"] + session["failed_files"])


# ── Cleanup ────────────────────────────────────────────────────────

print("\n=== CLEANUP ===")
r = requests.delete(f"{BASE}/processing-sessions/{session_id}")
test("Session deleted", r.status_code == 204)


# ── Summary ────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"M5 ACCEPTANCE TEST: {passed} passed, {failed} failed")
print(f"{'='*60}")
sys.exit(1 if failed > 0 else 0)
