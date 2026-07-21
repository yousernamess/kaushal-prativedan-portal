```markdown
# Kaushal Prativedan Portal — Project Brief for Coding Agent

## What is this project?

A full-stack web portal for an NGO project called Vigyan Express running a school education programme called Kaushal Prativedan. The portal automates OMR (Optical Mark Recognition) answer sheet checking, scores student responses, and generates detailed PDF report cards per student.

The NGO runs baseline and endline exams for students across multiple schools, classes, and batches. Teachers scan filled OMR sheets using Adobe Scanner, upload them to the portal, and the system processes them automatically.

---

## Project Structure

```
Kaushal Prativedan Portal/
    omrExtractor/           ← Python OMR processing pipeline (mostly complete)
        src/
            preprocess.py
            calibrate.py
            align.py
            bubble_reader.py
            debug_overlay.py
            check.py
        templates/
            calibration_points.json
        input/
        output/
    backend/                ← FastAPI backend (partially complete)
        db/
            schema.sql
        src/
            main.py
            scorer.py
            reporter.py
    frontend/               ← React (not started)
    README.md
```

---

## OMR Template

- Name: Vigyan Express OMR Answer Sheet
- File: `omrExtractor/input/template.pdf`
- Size: A4 portrait, rendered at 2382x3368 pixels (Matrix 4,4 via PyMuPDF)
- Layout: 40 questions, 4 columns of 10 questions each (Q1-10, Q11-20, Q21-30, Q31-40)
- Options: A, B, C, D per question
- Corner fiducial markers: 4 solid black squares (~16px) at each corner for alignment
- Bubble radius: 29px at 2382x3368

---

## Tech Stack

- **OMR Pipeline**: Python, OpenCV, PyMuPDF (fitz), NumPy
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL on Supabase (free tier)
- **Frontend**: React
- **Hosting**: Railway or Render (backend), Vercel (frontend)
- **PDF Generation**: ReportLab + Matplotlib
- **PDF Processing**: PyMuPDF

---

## What is Complete

### 1. `omrExtractor/src/preprocess.py`
Loads PDF or image, converts to BGR, resizes to 2382x3368.
Uses `fitz.Matrix(4, 4)` for high quality rendering.
Key function: `load_image_from_path(path)` returns BGR numpy array.

### 2. `omrExtractor/src/calibrate.py`
Interactive tool with scroll-to-zoom and space+drag pan.
Phase 1: click center then edge of a bubble to measure radius.
Phase 2: click 12 anchor points (3 per column x 4 columns).
Interpolates all 160 bubble centers from anchors.
Saves to `templates/calibration_points.json`.

Output JSON format:
```json
{
  "template_name": "vigyan_express_40_v1",
  "version": 1,
  "image_width": 2382,
  "image_height": 3368,
  "question_count": 40,
  "options": ["A", "B", "C", "D"],
  "bubble_radius": 29,
  "fill_threshold": 0.55,
  "roi_padding": 3,
  "bubbles": {
    "Q1": { "A": [235, 1555], "B": [316, 1555], "C": [397, 1555], "D": [478, 1555] },
    ...
  }
}
```

### 3. `omrExtractor/src/align.py`
Detects 4 corner fiducial markers using contour detection.
Applies perspective warp to canonicalize scanned sheets to 2382x3368.
Marker detection uses area bounds (100-1200px²) and squareness check.
Destination points (measured from blank template):
- top_left: (96, 215)
- top_right: (2285, 215)
- bottom_left: (96, 3152)
- bottom_right: (2285, 3152)

Key functions:
- `find_markers(image)` → dict of corner name to (x, y)
- `align(image)` → warped image at 2382x3368
- `debug_markers(image, output_path)` → saves debug image

Works reliably with Adobe Scanner output. Raw phone photos not supported by design.

### 4. `omrExtractor/src/bubble_reader.py`
Loads image → calls `align()` → converts to grayscale → applies fixed threshold (128) → reads bubbles.
Uses circular ROI mask for each bubble.
Two-condition answer selection:
- `ABSOLUTE_THRESHOLD = 0.35` — minimum fill ratio to count as filled
- `DIFFERENCE_THRESHOLD = 0.08` — minimum gap between best and second best

Supports variable question count via `question_count` parameter.

Key function:
```python
read_omr(image_path, template, question_count=None)
→ { "Q1": "B", "Q2": None, "Q3": "A", ... }
```

### 5. `omrExtractor/src/debug_overlay.py`
Draws green circles at bubble centers, orange ROI boxes, red center dots on the scanned image.
Used to visually verify template alignment.
Run: `python src/debug_overlay.py your_scan.pdf`

### 6. `backend/src/scorer.py`
Takes detected answers and exam config, returns scores.
Unanswered questions within question_count are marked wrong.
Questions beyond question_count are skipped.

Input:
```python
detected_answers = { "Q1": "B", "Q2": None, ... }
exam_config = {
    "question_count": 15,
    "answer_key": { "Q1": "B", ... },
    "skill_map": { "Application": [1,2,3,4,5], ... }
}
```

Output:
```python
{
    "total_score": 12,
    "total_marks": 15,
    "per_question": {
        "Q1": { "detected": "B", "correct": "B", "is_correct": True },
        ...
    },
    "skill_scores": {
        "Application": { "score": 4, "total": 5 },
        ...
    }
}
```

### 7. `backend/src/reporter.py`
Generates A4 PDF report card using ReportLab + Matplotlib.
Contains:
- Header: Vigyan Express branding
- Student info: name, roll number, class, batch, exam type
- Score summary bar: total score, percentage, correct, incorrect
- Skill scores table + spider chart side by side (student vs class average)
- Per question table: question number, skill, detected answer, correct answer, result (✓/✗), class performance (X/Y got it right)
- Footer

Key function:
```python
generate_report(student, result, exam_config, class_results, output_path=None)
→ BytesIO or writes to file
```

NOTE: reporter.py needs to be updated once DB is connected to show full question text and options instead of just Q1, Q2 labels.

### 8. `backend/src/main.py`
Ties the full pipeline together. Currently has stubbed DB calls.
Parses filename format: `R001_RahulSharma.pdf` → roll_number, name.
Processes sheets sequentially.
Updates upload session progress after each sheet.

Key function:
```python
process_batch(image_paths, exam_config_id, batch_id, upload_session_id, omr_template_path=None)
→ {
    "session_id": 1,
    "total": 30,
    "processed": 29,
    "failed": 1,
    "failed_sheets": ["R005_AryaSingh.pdf"],
    "results": { "R001": { ... }, ... }
}
```

### 9. `backend/db/schema.sql`
Full PostgreSQL schema. Tables:
- `users` — admin accounts
- `schools` — school records
- `batches` — class + batch per school
- `students` — roll number + name, unique per batch
- `questions` — question text, options A-D, correct answer, skill, class, exam type
- `exam_configs` — reusable config: question count, class, exam type, skill map
- `exam_config_questions` — junction table linking questions to configs with ordering
- `upload_sessions` — tracks a batch upload with status, progress counters
- `omr_sheets` — individual sheet status and error tracking
- `results` — detected answers, skill scores, total score per student per exam

---

## What is Remaining

### Phase 1 — Backend completion

#### 1. Supabase Setup
- Create Supabase project
- Run `schema.sql` in Supabase SQL editor
- Get connection string
- Install `psycopg2` or `asyncpg`
- Create `backend/src/database.py` — connection pool and helper functions

#### 2. Replace DB stubs in `main.py`
Replace all `db_*` stub functions with real queries:
- `db_get_exam_config(exam_config_id)` — fetch config + questions via JOIN on `exam_config_questions`
- `db_get_or_create_student(roll_number, name, batch_id)` — upsert student
- `db_create_omr_sheet(upload_session_id, student_id, filename)` — insert record
- `db_save_result(...)` — insert into results
- `db_update_omr_sheet_status(...)` — update status
- `db_update_session_progress(...)` — update processed/failed counters
- `db_complete_session(...)` — set status to completed, set completed_at

#### 3. Update `scorer.py`
Currently takes `answer_key` as a flat dict.
Update to accept questions list from DB (fetched via `exam_config_questions` JOIN).
Answer key should be derived from `questions.correct_answer`.

#### 4. Update `reporter.py`
Update per-question table to show:
- Full question text
- All 4 options (A, B, C, D) with text
- Student's selected option highlighted
- Correct option highlighted
- Class performance: X out of Y students got it right

#### 5. FastAPI endpoints
Create `backend/src/api.py`:

```
POST /auth/login
POST /auth/logout

GET  /schools
POST /schools

GET  /batches?school_id=
POST /batches

GET  /students?batch_id=
POST /students

GET  /questions?class=&exam_type=
POST /questions
PUT  /questions/{id}
DELETE /questions/{id}

GET  /exam-configs
POST /exam-configs
GET  /exam-configs/{id}

POST /upload-sessions              ← create session, upload sheets, trigger processing
GET  /upload-sessions/{id}/status  ← poll processing status
GET  /upload-sessions/{id}/results ← get full results for a session

GET  /results/student/{student_id} ← all results for a student
GET  /results/{id}/report          ← generate PDF report on demand
GET  /results/batch/{session_id}/zip ← generate zip of all PDFs for a session

GET  /db/size                      ← storage indicator for dashboard
```

### Phase 2 — Frontend (React)

Pages:
1. **Login** — admin authentication
2. **Dashboard** — overview: recent uploads, storage indicator, quick stats
3. **Questions** — create/edit questions per class and exam type
4. **Exam Configs** — create reusable configs by selecting questions, setting skill map
5. **Upload** — select batch, select exam config, upload OMR PDFs (single, multiple, or ZIP), set question count, trigger processing
6. **Upload Status** — live poll of processing progress, show failed sheets
7. **Results — Batch View** — table of all students in a session with scores
8. **Results — Student View** — search student, see all their results across exams
9. **Report Card** — inline PDF viewer for individual student report

### Phase 3 — Polish
- ZIP upload support (extract and process each PDF inside)
- Storage indicator on dashboard (Supabase API)
- Manual delete for old batches
- User guide document

---

## Key Business Rules

1. Reports are generated on demand from DB data, not stored as files
2. Processing only starts after admin explicitly sets question count
3. Unanswered questions within question_count = wrong (score 0)
4. Questions beyond question_count = skipped
5. Filenames must follow format: `R001_StudentName.pdf`
6. Each student is unique per batch (roll_number + batch_id)
7. Reports only generated after full batch is processed (need class stats)
8. Baseline and endline are separate exam types, each student gets one of each per batch year
9. Exam configs are reusable across batches and years
10. Questions are reusable across exam configs
11. Adobe Scanner is the required scanning method (raw photos not supported)
12. All admins share the same question bank and exam configs

---

## Dependencies

```
# omrExtractor
opencv-python
pymupdf
numpy

# backend
fastapi
uvicorn
psycopg2-binary
reportlab
matplotlib
python-multipart
python-jose        # JWT auth
passlib            # password hashing
```

---

## Notes for the Agent

- The OMR template is fixed (`vigyan_express_40_v1`). Do not change calibration logic.
- `align.py` works only with Adobe Scanner output. Do not add raw photo support.
- `bubble_reader.py` `ABSOLUTE_THRESHOLD` and `DIFFERENCE_THRESHOLD` are tuned — do not change without testing.
- All DB stubs in `main.py` are clearly marked with `[DB]` print statements — replace these with real queries.
- `reporter.py` needs question text added once DB is connected — the table structure is already correct, just needs data.
- The frontend should not allow the Process button to be active until question_count, exam_config, batch, and files are all set.
- ZIP support means extracting PDFs from the ZIP and treating each as an individual sheet.
```

Save this as `PROJECT_BRIEF.md` in the root `Kaushal Prativedan Portal/` folder.