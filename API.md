# API.md

Base URL: `http://127.0.0.1:8000`

---

## Health

### GET /health

Returns `{"status": "ok"}`

---

## Schools

### GET /schools

Returns list of all schools with student/section counts.

**Response:** `SchoolRead[]`

```json
[
  {
    "id": 1,
    "name": "Sunrise Public School",
    "created_at": "2026-08-09T11:35:48.216178Z",
    "updated_at": "2026-08-09T11:35:48.216178Z",
    "student_count": 12,
    "section_count": 3
  }
]
```

### GET /schools/{school_id}

Returns a single school with counts.

**Response:** `SchoolRead`

### POST /schools

Create a new school.

**Request:** `{"name": "Sunrise Public School"}`

**Response:** `SchoolRead` (201)

**Errors:**
- 409: "A school with this name already exists"

### PUT /schools/{school_id}

Update a school name.

**Request:** `{"name": "New Name"}`

**Response:** `SchoolRead`

**Errors:**
- 404: "School not found"
- 409: "A school with this name already exists"

### DELETE /schools/{school_id}

Delete a school. Blocked if school has students.

**Query params:** `force` (bool, default false)

- `force=false`: Returns 409 if school has students
- `force=true`: Deletes all students, sections, and the school

**Response:** 204 No Content

**Errors:**
- 404: "School not found"
- 409: "Cannot delete a school that has students" (when force=false and school has students)

### DELETE /schools/{school_id}/students

Bulk remove all students from a school.

**Response:** `{"deleted": N}`

**Errors:**
- 404: "School not found"

---

## Academic Years

### GET /academic-years

Returns all academic years, ordered by name descending.

**Response:** `AcademicYearRead[]`

```json
[
  {"id": 1, "name": "2026-27"}
]
```

### POST /academic-years

Create a new academic year.

**Request:** `{"name": "2026-27"}`

**Validation:** Name must match `YYYY-YY` pattern.

**Response:** `AcademicYearRead` (201)

**Errors:**
- 409: "This academic year already exists"

### PUT /academic-years/{item_id}

Update an academic year.

**Request:** `{"name": "2027-28"}`

**Response:** `AcademicYearRead`

**Errors:**
- 404: "Academic year not found"
- 409: "This academic year already exists"

### DELETE /academic-years/{item_id}

Delete an academic year.

**Response:** 204 No Content

**Errors:**
- 404: "Academic year not found"

---

## Sections

### GET /sections

Returns sections, optionally filtered.

**Query params:**
- `school_id` (int, optional)
- `class_number` (int, optional)

**Response:** `SectionRead[]`

```json
[
  {"id": 1, "school_id": 1, "class_number": 6, "section_name": "A"}
]
```

### POST /sections

Create a single section.

**Request:** `{"school_id": 1, "class_number": 6, "section_name": "A"}`

**Validation:** `class_number` must be 6, 7, or 8.

**Response:** `SectionRead` (201)

**Errors:**
- 409: "This section already exists"
- 422: "School does not exist"

### POST /sections/bulk

Bulk create sections.

**Request:**
```json
{
  "school_id": 1,
  "class_number": 6,
  "section_names": "A, B, C"
}
```

**Validation:**
- `class_number` must be 6, 7, or 8
- `section_names` must be comma-separated, non-empty
- Duplicate names within the same request are rejected
- Existing sections for the same school/class are rejected

**Response:** `SectionRead[]` (201)

**Errors:**
- 409: "Sections already exist: B, C"
- 422: "School does not exist"
- 422: "Enter one or more unique comma-separated section names"

### PUT /sections/{item_id}

Update a section.

**Request:** `{"school_id": 1, "class_number": 6, "section_name": "B"}`

**Response:** `SectionRead`

**Errors:**
- 404: "Section not found"
- 409: "This section already exists"
- 422: "School does not exist"

### DELETE /sections/{item_id}

Delete a section.

**Response:** 204 No Content

**Errors:**
- 404: "Section not found"

---

## Students

### GET /students

Returns students, optionally filtered.

**Query params:**
- `search` (string, optional) — searches by name or roll number
- `school_id` (int, optional)
- `class_number` (int, optional)
- `section` (string, optional)

**Response:** `StudentRead[]`

```json
[
  {
    "id": 1,
    "school_id": 1,
    "roll_number": 14,
    "student_name": "Rahul Patel",
    "current_class": 6,
    "current_section": "A",
    "school_name": "Sunrise Public School"
  }
]
```

### POST /students

Create a student.

**Request:**
```json
{
  "school_id": 1,
  "roll_number": 14,
  "student_name": "Rahul Patel",
  "current_class": 6,
  "current_section": "A"
}
```

**Validation:**
- `roll_number` must be > 0
- `current_class` must be 6, 7, or 8
- `student_name` must be 1–200 chars
- `current_section` must be 1–20 chars

**Response:** `StudentRead` (201)

**Errors:**
- 409: "This roll number is already in use at this school"
- 422: "School does not exist"

### PUT /students/{item_id}

Update a student.

**Request:** Same as POST.

**Response:** `StudentRead`

**Errors:**
- 404: "Student not found"
- 409: "This roll number is already in use at this school"
- 422: "School does not exist"

### DELETE /students/{item_id}

Delete a student.

**Response:** 204 No Content

**Errors:**
- 404: "Student not found"

### POST /students/import

Import students from CSV.

**Request:** `multipart/form-data` with `file` field.

**CSV columns:** `Roll Number, Student Name, School, Class, Section`

**Response:**
```json
{
  "created": 241,
  "skipped": 7,
  "errors": [
    {"row": 18, "errors": ["School \"ABC School\" not found"]},
    {"row": 42, "errors": ["Section \"D\" does not exist for Class 7 at \"Sunrise\""]},
    {"row": 91, "errors": ["Roll number 14 already exists in this school"]}
  ]
}
```

**Validation per row:**
- School exists (case-insensitive)
- Roll Number is a positive integer
- Student Name is non-empty
- Class is 6, 7, or 8
- Section exists for that school/class
- Duplicate roll numbers within CSV are caught

**Errors:**
- 422: "Upload a CSV file"
- 422: "CSV must contain: Roll Number, Student Name, School, Class, Section"
- 409: "Import contains students that already exist in the database"

### GET /students/export/csv

Export students as CSV, optionally filtered.

**Query params:**
- `school_id` (int, optional)
- `class_number` (int, optional)
- `section` (string, optional)

**Response:** `text/csv` with headers `Roll Number, Student Name, School, Class, Section`

---

## Assessments

### GET /assessments

Returns assessments (excluding soft-deleted).

**Query params:**
- `academic_year_id` (int, optional)
- `class_number` (int, optional)

**Response:** `AssessmentRead[]`

```json
[
  {
    "id": 1,
    "name": "Science Baseline 2026",
    "assessment_type": "Baseline",
    "academic_year_id": 1,
    "class_number": 6,
    "is_deleted": false,
    "questions": [
      {"id": 1, "question_number": 1, "correct_option": "A", "domain": "Understanding"}
    ]
  }
]
```

### GET /assessments/{assessment_id}

Returns a single assessment with questions.

**Response:** `AssessmentRead`

**Errors:**
- 404: "Assessment not found"

### POST /assessments

Create an assessment with questions.

**Request:**
```json
{
  "name": "Science Baseline 2026",
  "assessment_type": "Baseline",
  "academic_year_id": 1,
  "class_number": 6,
  "questions": [
    {"question_number": 1, "correct_option": "A", "domain": "Understanding"},
    {"question_number": 2, "correct_option": "B", "domain": "Observation"}
  ]
}
```

**Validation:**
- `assessment_type` must be "Baseline" or "Endline"
- `class_number` must be 6, 7, or 8
- `questions` must have 10–40 items
- Question numbers must be unique
- `correct_option` must be A, B, C, or D

**Response:** `AssessmentRead` (201)

**Errors:**
- 409: "Question number already exists"
- 422: "Academic year does not exist"
- 422: "Question numbers must be unique"

### PUT /assessments/{assessment_id}

Update an assessment (not questions).

**Request:** Same as POST without `questions`.

**Response:** `AssessmentRead`

**Errors:**
- 404: "Assessment not found"
- 422: "Academic year does not exist"

### DELETE /assessments/{assessment_id}

Soft delete an assessment.

**Response:** 204 No Content

**Errors:**
- 404: "Assessment not found"

### POST /assessments/{assessment_id}/duplicate

Duplicate an assessment with all its questions.

**Response:** `AssessmentRead` (201)

**Errors:**
- 404: "Assessment not found"

### POST /assessments/{assessment_id}/questions

Add a question to an assessment.

**Request:** `{"question_number": 1, "correct_option": "A", "domain": "Understanding"}`

**Response:** `QuestionRead` (201)

**Errors:**
- 404: "Assessment not found"
- 409: "Question number already exists"
- 422: "An assessment cannot have more than 40 questions"

### PUT /assessments/questions/{question_id}

Update a question.

**Request:** Same as POST.

**Response:** `QuestionRead`

**Errors:**
- 404: "Question not found"

### DELETE /assessments/questions/{question_id}

Delete a question.

**Response:** 204 No Content

**Errors:**
- 404: "Question not found"

---

## Not Implemented Yet

- Authentication (POST /login, POST /logout, GET /me)
- Dashboard (GET /dashboard)
- OMR Processing
- Analytics
- Reports
