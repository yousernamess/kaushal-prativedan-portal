"""READ-ONLY investigation script for M5 integration check."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.omr_service import extract_omr, _get_template
from app.core.database import SessionLocal
from app.models import *
from pathlib import Path

tpl = _get_template()
print("=== TEMPLATE ===")
print("question_count:", tpl["question_count"])
print("options:", tpl["options"])

source = Path(__file__).resolve().parent.parent / "omrExtractor" / "input" / "101.jpeg"
print("source image:", source, "exists:", source.exists())

# Run extractor directly
result = extract_omr(source, 40)
print("\n=== DIRECT EXTRACTOR OUTPUT ===")
for k in sorted(result.keys(), key=lambda x: int(x[1:])):
    print(f"  {k}={result[k]}")

from collections import Counter
answer_counts = Counter(result.values())
print("\nAnswer distribution:", dict(answer_counts))

# Compare with database
db = SessionLocal()
aqs = db.query(AttemptQuestion).filter(AttemptQuestion.attempt_id == 31).all()
print("\n=== DATABASE AttemptQuestion (attempt 31) ===")
print("Total records:", len(aqs))
db_detected = {}
for aq in aqs:
    q = db.query(Question).get(aq.question_id)
    qn = q.question_number if q else "?"
    key = f"Q{qn}"
    db_detected[key] = aq.detected_answer
    print(f"  {key}: detected={aq.detected_answer}, correct={aq.correct_answer}, is_correct={aq.is_correct}")

print("\n=== COMPARISON ===")
mismatches = 0
for k in sorted(result.keys(), key=lambda x: int(x[1:])):
    direct = result[k]
    db_val = db_detected.get(k, "MISSING")
    match = "OK" if direct == db_val else "MISMATCH"
    if match == "MISMATCH":
        mismatches += 1
        print(f"  {k}: DIRECT={direct}, DB={db_val} -- {match}")
    else:
        print(f"  {k}: {direct} == {db_val} -- OK")

print(f"\nMismatches: {mismatches} / {len(result)}")

# Score comparison
score_direct = 0
score_db = 0
questions = sorted(db.query(Assessment).get(6).questions, key=lambda q: q.question_number)
for q in questions:
    key = f"Q{q.question_number}"
    det_direct = result.get(key)
    det_db = db_detected.get(key)
    correct = q.correct_option
    if det_direct is not None and det_direct == correct:
        score_direct += 1
    if det_db is not None and det_db == correct:
        score_db += 1

print(f"\n=== SCORE COMPARISON ===")
print(f"Direct extractor score: {score_direct}/40")
print(f"Database score: {score_db}/40")
print(f"Frontend score: 19/40 (from user report)")

db.close()
