# DATABASE.md

# Database Design

## Tables

### School

```text
id (PK)
name
created_at
updated_at
```

---

### AcademicYear

```text
id (PK)
name
created_at
updated_at
```

Example

* 2026-27
* 2027-28

---

### Student

```text
id (PK)
school_id (FK -> School)

roll_number
student_name

current_class
current_section

created_at
updated_at
```

Rules

* Roll numbers are permanent.
* Student ID is the internal primary key.
* Student may move between classes.
* Student may move between schools.

---

### Section

```text
id (PK)

school_id (FK)

class_number

section_name

created_at
updated_at
```

Example

School A

Class 6

Section A

---

### Assessment

```text
id (PK)

name

assessment_type
(Baseline | Endline)

academic_year_id (FK)

class_number

created_at
updated_at
```

---

### Question

```text
id (PK)

assessment_id (FK)

question_number

correct_option

domain
```

Rules

* Question count: 10–40
* Exactly one correct option

---

### AssessmentSession

Represents one execution of an assessment.

```text
id (PK)

assessment_id (FK)

school_id (FK)

academic_year_id (FK)

class_number

section

created_at
```

---

### StudentAttempt

Represents one student's completed assessment.

```text
id (PK)

student_id (FK)

assessment_session_id (FK)

score

percentage

created_at
```

---

### StudentAnswer

```text
id (PK)

attempt_id (FK)

question_id (FK)

selected_option

is_correct
```

---

# Relationships

School

↓

Students

↓

Student Attempts

↓

Student Answers

Assessment

↓

Questions

↓

Assessment Session

↓

Student Attempts

---

# Delete Rules

School

Cannot be deleted if students exist.

Assessment

Soft delete only.

Student

Cannot be deleted if attempts exist.

Assessment Session

Never delete automatically.

---

# Indexes

Student

* school_id
* roll_number

Assessment

* class_number
* academic_year_id

StudentAttempt

* student_id
* assessment_session_id

StudentAnswer

* attempt_id
* question_id
