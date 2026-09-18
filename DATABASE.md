# DATABASE.md

# Database Design

Database: PostgreSQL (local install — Windows host, port 5432)
ORM: SQLAlchemy 2.0
Migrations: Alembic

---

## Tables

### School

```text
id          (PK, integer)
name        (string, 200, unique, indexed)
created_at  (datetime, timezone, server_default=now())
updated_at  (datetime, timezone, server_default=now(), onupdate=now())
```

**Relationships:**
- `students` → Student (one-to-many)
- `sections` → Section (one-to-many)

**API properties (computed):**
- `student_count` — count of students
- `section_count` — count of sections

---

### AcademicYear

```text
id          (PK, integer)
name        (string, 9, unique, indexed)
created_at  (datetime, timezone, server_default=now())
updated_at  (datetime, timezone, server_default=now(), onupdate=now())
```

**Validation:** Name must match `YYYY-YY` pattern (e.g. 2026-27).

---

### Section

```text
id          (PK, integer)
school_id   (FK → schools.id, indexed)
class_number (integer)
section_name (string, 20)
created_at  (datetime, timezone, server_default=now())
updated_at  (datetime, timezone, server_default=now(), onupdate=now())
```

**Constraints:**
- `UniqueConstraint(school_id, class_number, section_name)` — no duplicate sections per school/class

**Relationships:**
- `school` → School (many-to-one)

---

### Student

```text
id              (PK, integer)
school_id       (FK → schools.id, indexed)
roll_number     (integer, indexed)
student_name    (string, 200)
current_class   (integer)
current_section (string, 20)
created_at      (datetime, timezone, server_default=now())
updated_at      (datetime, timezone, server_default=now(), onupdate=now())
```

**Constraints:**
- `UniqueConstraint(school_id, roll_number)` — no duplicate roll numbers per school

**Relationships:**
- `school` → School (many-to-one)

**API properties (computed):**
- `school_name` — name of the school

**Rules:**
- Roll numbers are positive integers.
- Student ID is the internal primary key.
- Student may move between classes.
- Student may move between schools.

---

### Assessment

```text
id              (PK, integer)
name            (string, 200, indexed)
assessment_type (enum: Baseline | Endline)
academic_year_id (FK → academic_years.id, indexed)
class_number    (integer, indexed)
is_deleted      (boolean, default=False)
created_at      (datetime, timezone, server_default=now())
updated_at      (datetime, timezone, server_default=now(), onupdate=now())
```

**Relationships:**
- `questions` → Question (one-to-many, cascade delete)

**Notes:**
- Soft delete via `is_deleted` flag.
- `assessment_type` is an enum: `Baseline` or `Endline`.

---

### Question

```text
id              (PK, integer)
assessment_id   (FK → assessments.id, indexed)
question_number (integer)
correct_option  (string, 1)
domain          (string, 100)
```

**Constraints:**
- `UniqueConstraint(assessment_id, question_number)` — no duplicate question numbers per assessment

**Relationships:**
- `assessment` → Assessment (many-to-one)

**Rules:**
- `correct_option` must be A, B, C, or D.
- `question_number` must be 1–40.
- `domain` is a learning domain (e.g. Understanding, Observation, Application, Analysis, Scientific Reasoning).

---

## Enums

### AssessmentType

```text
BASELINE = "Baseline"
ENDLINE  = "Endline"
```

---

## Migration

Migrations (in `backend/alembic/versions/`, applied in order):
1. `20260805_01` — initial portal schema (schools, academic_years, sections, students, assessments, questions, batches, results, users, etc.)
2. `20260809_01` — add question text and options to `questions`
3. `20260810_01` — add OMR processing session and file tables
4. `20260810_02` — add assessment attempt and attempt question tables

Run with: `alembic upgrade head`
