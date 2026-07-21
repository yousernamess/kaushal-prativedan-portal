import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "omrExtractor" / "src"))

from bubble_reader import read_omr, load_template
from scorer import score

# ----------------------------------------------------
# Stub DB functions (replace with real DB calls later)
# ----------------------------------------------------

def db_get_exam_config(exam_config_id):
    """
    Returns exam config with questions and answer key.
    Stub -- replace with real DB query later.
    """
    return {
        "id":             exam_config_id,
        "config_name":    "Science Grade 6 Baseline",
        "question_count": 15,
        "class":          "6",
        "exam_type":      "baseline",
        "skill_map": {
            "Application":   [1, 2, 3, 4, 5],
            "Understanding": [6, 7, 8, 9, 10],
            "HOTS":          [11, 12, 13],
            "Knowledge":     [14, 15],
        },
        "questions": {
            "Q1":  {"text": "A plant was kept in a dark room...", "option_a": "Too much water",  "option_b": "Photosynthesis did not occur", "option_c": "Too much fertilizer", "option_d": "Too much air",     "correct": "B"},
            "Q2":  {"text": "An iron nail was kept in water...", "option_a": "Melting",          "option_b": "Evaporation",                 "option_c": "Rusting",             "option_d": "Condensation",     "correct": "C"},
            "Q3":  {"text": "Why do wet clothes dry faster?",   "option_a": "Higher humidity",  "option_b": "Evaporation occurs faster",   "option_c": "Condensation occurs", "option_d": "Air remains still","correct": "B"},
            "Q4":  {"text": "Why do electricians wear gloves?", "option_a": "Good conductor",   "option_b": "Rubber is an insulator",      "option_c": "Rubber is magnetic",  "option_d": "Rubber makes light","correct": "B"},
            "Q5":  {"text": "Why do farmers add fertilizers?",  "option_a": "Change soil color","option_b": "Increase nutrients",          "option_c": "Reduce water",        "option_d": "Increase insects", "correct": "B"},
            "Q6":  {"text": "Which gas is needed for photosynthesis?", "option_a": "Oxygen",    "option_b": "Carbon dioxide",              "option_c": "Nitrogen",            "option_d": "Hydrogen",         "correct": "B"},
            "Q7":  {"text": "Which organ pumps blood?",         "option_a": "Lungs",            "option_b": "Brain",                       "option_c": "Heart",               "option_d": "Kidney",           "correct": "C"},
            "Q8":  {"text": "Suspended magnet points which way?","option_a": "East-West",       "option_b": "North-South",                 "option_c": "Up-Down",             "option_d": "No direction",     "correct": "B"},
            "Q9":  {"text": "Good conductor of heat?",          "option_a": "Wood",             "option_b": "Plastic",                     "option_c": "Copper",              "option_d": "Rubber",           "correct": "C"},
            "Q10": {"text": "Silk is obtained from?",           "option_a": "Honeybee",         "option_b": "Silkworm",                    "option_c": "Frog",                "option_d": "Spider",           "correct": "B"},
            "Q11": {"text": "Best way to save water in school?","option_a": "Keep taps open",  "option_b": "Harvest rainwater",           "option_c": "Use more water",      "option_d": "Let water flow",   "correct": "B"},
            "Q12": {"text": "Best way to protect environment?", "option_a": "Use more plastic", "option_b": "Plant trees",                 "option_c": "Throw garbage",       "option_d": "Waste paper",      "correct": "B"},
            "Q13": {"text": "Shortage of electricity solution?","option_a": "Burn more coal",  "option_b": "Use solar energy",            "option_c": "Lights on all day",   "option_d": "Use more diesel",  "correct": "B"},
            "Q14": {"text": "Largest planet in Solar System?",  "option_a": "Earth",            "option_b": "Venus",                       "option_c": "Jupiter",             "option_d": "Mars",             "correct": "C"},
            "Q15": {"text": "Earth's only natural satellite?",  "option_a": "Sun",              "option_b": "Moon",                        "option_c": "Mars",                "option_d": "Venus",            "correct": "B"},
        }
    }


def db_get_or_create_student(roll_number, name, batch_id):
    """
    Returns student id.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] Get or create student: {roll_number} - {name} in batch {batch_id}")
    return 1


def db_create_omr_sheet(upload_session_id, student_id, filename):
    """
    Creates omr_sheet record, returns its id.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] Create OMR sheet: {filename}")
    return 1


def db_save_result(student_id, omr_sheet_id, exam_config_id, exam_type, score_result):
    """
    Saves result to DB.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] Save result: student={student_id} score={score_result['total_score']}/{score_result['total_marks']}")


def db_update_omr_sheet_status(omr_sheet_id, status, error_message=None):
    """
    Updates omr_sheet status.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] OMR sheet {omr_sheet_id} status: {status}")


def db_update_session_progress(upload_session_id, processed, failed):
    """
    Updates upload session progress counters.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] Session {upload_session_id}: processed={processed} failed={failed}")


def db_complete_session(upload_session_id):
    """
    Marks upload session as completed.
    Stub -- replace with real DB query later.
    """
    print(f"  [DB] Session {upload_session_id} completed.")


# ----------------------------------------------------
# Filename parser
# ----------------------------------------------------
def parse_filename(filename):
    """
    Parses 'R001_RahulSharma.pdf' -> ('R001', 'Rahul Sharma')
    """
    stem = Path(filename).stem
    parts = stem.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Filename '{filename}' does not match expected format R001_StudentName.pdf")
    roll_number = parts[0]
    name        = parts[1].replace("_", " ")
    return roll_number, name


# ----------------------------------------------------
# Build answer key from exam config questions
# ----------------------------------------------------
def build_answer_key(exam_config):
    return {
        q_key: q_data["correct"]
        for q_key, q_data in exam_config["questions"].items()
    }


# ----------------------------------------------------
# Process a single OMR sheet
# ----------------------------------------------------
def process_sheet(image_path, exam_config, batch_id, upload_session_id, omr_template):
    filename    = Path(image_path).name
    roll_number, name = parse_filename(filename)

    print(f"\nProcessing: {filename}")

    # Get or create student
    student_id  = db_get_or_create_student(roll_number, name, batch_id)
    omr_sheet_id = db_create_omr_sheet(upload_session_id, student_id, filename)

    try:
        # Run OMR extraction
        detected_answers = read_omr(
            image_path,
            omr_template,
            question_count=exam_config["question_count"]
        )

        # Build answer key from questions
        answer_key = build_answer_key(exam_config)

        # Score
        score_input = {
            "question_count": exam_config["question_count"],
            "answer_key":     answer_key,
            "skill_map":      exam_config["skill_map"],
        }
        score_result = score(detected_answers, score_input)

        # Save to DB
        db_save_result(
            student_id,
            omr_sheet_id,
            exam_config["id"],
            exam_config["exam_type"],
            score_result
        )

        db_update_omr_sheet_status(omr_sheet_id, "done")

        return {
            "status":       "success",
            "roll_number":  roll_number,
            "name":         name,
            "score_result": score_result,
        }

    except Exception as e:
        error_msg = str(e)
        print(f"  ERROR: {error_msg}")
        db_update_omr_sheet_status(omr_sheet_id, "failed", error_msg)
        return {
            "status":      "failed",
            "roll_number": roll_number,
            "name":        name,
            "error":       error_msg,
        }


# ----------------------------------------------------
# Process a batch of OMR sheets
# ----------------------------------------------------
def process_batch(
    image_paths,
    exam_config_id,
    batch_id,
    upload_session_id,
    omr_template_path=None,
):
    # Load exam config from DB
    exam_config = db_get_exam_config(exam_config_id)

    # Load OMR template
    omr_template = load_template(omr_template_path) if omr_template_path else load_template()

    total     = len(image_paths)
    processed = 0
    failed    = 0
    results   = {}
    failed_sheets = []

    print(f"\n{'='*50}")
    print(f"Processing batch: {total} sheets")
    print(f"Exam config: {exam_config['config_name']}")
    print(f"{'='*50}")

    for image_path in image_paths:
        sheet_result = process_sheet(
            image_path,
            exam_config,
            batch_id,
            upload_session_id,
            omr_template,
        )

        if sheet_result["status"] == "success":
            processed += 1
            results[sheet_result["roll_number"]] = sheet_result["score_result"]
        else:
            failed += 1
            failed_sheets.append(Path(image_path).name)

        db_update_session_progress(upload_session_id, processed, failed)

    db_complete_session(upload_session_id)

    summary = {
        "session_id":     upload_session_id,
        "total":          total,
        "processed":      processed,
        "failed":         failed,
        "failed_sheets":  failed_sheets,
        "results":        results,
    }

    print(f"\n{'='*50}")
    print(f"Batch complete: {processed}/{total} processed, {failed} failed")
    if failed_sheets:
        print(f"Failed: {failed_sheets}")
    print(f"{'='*50}\n")

    return summary


# ----------------------------------------------------
# Standalone test
# ----------------------------------------------------
if __name__ == "__main__":
    import glob

    test_images = glob.glob(str(BASE_DIR / "omrExtractor" / "input" / "*.pdf"))

    if not test_images:
        print("No PDFs found in omrExtractor/input/")
        sys.exit(1)

    summary = process_batch(
        image_paths       = test_images,
        exam_config_id    = 1,
        batch_id          = 1,
        upload_session_id = 1,
    )

    print("Summary:")
    for roll, result in summary["results"].items():
        print(f"  {roll}: {result['total_score']}/{result['total_marks']}")