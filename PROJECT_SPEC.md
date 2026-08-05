# Science Assessment Management System

## Project Specification (v1.0)

# Overview

Build a full-stack web application for NGOs/schools to automate the evaluation of OMR-based Science assessments.

The application should allow teachers to:

* Manage schools, academic years, classes, sections and students.
* Create Science assessments.
* Upload one or many OMR sheets.
* Automatically evaluate OMRs using an existing Python OpenCV engine.
* Generate detailed student report cards similar to ASSET.
* View school-level and overall analytics.

The OMR checker is already complete and should be treated as a black box.

Assume it exposes a Python function or module that returns JSON in the following format:

```json
{
    "roll_number": 23,
    "answers": [
        "B",
        "A",
        "",
        "D",
        "C"
    ]
}
```

Do NOT implement the OMR algorithm.

Only integrate with it.

---

# Tech Stack

Frontend

* React
* TypeScript
* TailwindCSS
* shadcn/ui
* React Router
* TanStack Query
* React Hook Form

Backend

* FastAPI
* SQLAlchemy ORM
* Alembic
* Pydantic

Database

* PostgreSQL
* Hosted on Railway

Backend Hosting

* Railway

Charts

* Recharts

Report Generation

* WeasyPrint (PDF)

---

# Project Modules

The application consists of five major modules.

1. Dashboard
2. Master Data
3. Assessments
4. Process OMR
5. Reports

---

# User Flow

Teacher logs in

↓

Creates or edits master data

↓

Creates assessment

↓

Processes OMR batch

↓

System evaluates answers

↓

Stores results

↓

Teacher opens report

↓

Analytics are generated

↓

PDF generated on demand

---

# Core Rules

Subject is ALWAYS Science.

There are exactly five learning domains.

Current placeholder domains:

* Understanding
* Observation
* Application
* Analysis
* Scientific Reasoning

These domains must be configurable later.

---

# Assessment Rules

Assessment Types

* Baseline
* Endline

Question Count

Minimum: 10

Maximum: 40

Every question contains

* Question Number
* Correct Option
* Domain

Only ONE correct answer exists.

Teachers can

* Create
* Edit
* Delete
* Duplicate

Assessments.

---

# Master Data

The following entities are managed separately.

Schools

Academic Years

Students

Sections

Teachers never type these repeatedly.

Everything is selected using dropdowns.

---

# Schools

Fields

* Name

CRUD required.

---

# Academic Years

Example

2026-27

2027-28

CRUD required.

---

# Classes

Only

Class 6

Class 7

Class 8

No CRUD required.

These are predefined.

---

# Sections

Examples

A

B

C

Section belongs to

School

and

Class

CRUD required.

---

# Students

Each student has

* Internal Student ID
* Student Name
* Roll Number
* School
* Current Class
* Current Section

Student ID is the database primary key.

Roll Number is permanent.

Roll Numbers do not change.

Students may move between classes or schools.

Current Class and Current Section may be updated.

---

# Assessment Creation

Teacher enters

Assessment Name

Academic Year

Class

Assessment Type

Baseline / Endline

Question Count

10-40

Then enters questions.

Each question has

Question Number

Correct Answer

Domain

Teachers may edit or delete questions later.

---

# Process OMR

This page should use a wizard.

## Step 1

Teacher selects

* Assessment
* School
* Academic Year
* Class
* Section (optional)

---

## Step 2

Teacher uploads

Single OMR

or

Batch OMRs

The filename convention is

StudentName_RollNumber.jpg

Example

Rahul_23.jpg

The backend extracts the roll number from the filename.

---

## Step 3

Backend sends image to the existing OMR engine.

OMR engine returns

```json
{
    "roll_number": 23,
    "answers": [
        "A",
        "B",
        "",
        "C"
    ]
}
```

---

## Step 4

System

Finds student

Loads assessment answer key

Compares answers

Calculates score

Stores attempt

Deletes uploaded image

Images are NEVER stored permanently.

---

# Evaluation

Compare

Student Answers

vs

Correct Answers

Calculate

Correct

Wrong

Blank

Score

Percentage

---

# Reports

Reports are NOT stored.

Reports are generated every time they are requested.

Reports include

Student Information

Assessment Information

Score

Percentage

Radar Chart

Domain-wise Performance

School Average

Overall Average

School Rank

Overall Rank

Percentile

Question-wise Analysis

Download PDF

Print

---

# Analytics

Analytics compare students against

1.

Students in the same school

AND

2.

Students from every school who took the same assessment.

Analytics include

School Average

Overall Average

School Rank

Overall Rank

Percentile

Domain Comparison

Student vs School Average

Student vs Overall Average

---

# Dashboard

Show

Total Schools

Total Assessments

Students Processed

Reports Generated

Recent Activity

Quick Actions

---

# Database

Tables

School

AcademicYear

Student

Section

Assessment

Question

AssessmentSession

StudentAttempt

StudentAnswer

---

School

id

name

---

AcademicYear

id

name

---

Student

id

school_id

roll_number

student_name

current_class

current_section

---

Section

id

school_id

class_number

section_name

---

Assessment

id

name

class

academic_year

assessment_type

created_at

updated_at

---

Question

id

assessment_id

question_number

correct_option

domain

---

AssessmentSession

Represents one execution of an assessment.

Contains

Assessment

School

Academic Year

Class

Section

Created At

---

StudentAttempt

Stores

Student

Assessment Session

Score

Percentage

Completed Time

---

StudentAnswer

Stores

Attempt

Question

Selected Option

Correct?

---

# API Design

Example endpoints

Authentication

POST /login

Dashboard

GET /dashboard

Schools

GET /schools

POST /schools

PUT /schools/{id}

DELETE /schools/{id}

Academic Years

GET /academic-years

POST /academic-years

PUT /academic-years/{id}

DELETE /academic-years/{id}

Sections

GET /sections

POST /sections

PUT /sections/{id}

DELETE /sections/{id}

Students

GET /students

POST /students

PUT /students/{id}

DELETE /students/{id}

Assessments

GET /assessments

POST /assessments

PUT /assessments/{id}

DELETE /assessments/{id}

Questions

GET /assessments/{id}/questions

POST /assessments/{id}/questions

PUT /questions/{id}

DELETE /questions/{id}

OMR

POST /process-omr

Reports

GET /reports/{attempt_id}

GET /reports/{attempt_id}/pdf

---

# Frontend Pages

Login

Dashboard

Master Data

Schools

Academic Years

Sections

Students

Assessments List

Assessment Editor

Process OMR Wizard

Reports List

Student Report

---

# Coding Rules

* Use SQLAlchemy ORM.
* Use Alembic for every schema change.
* Use Pydantic for request and response validation.
* Keep business logic inside service classes.
* Keep API routes thin.
* Use repository/service architecture where appropriate.
* Never mix OpenCV logic into API routes.
* The OMR engine must remain an isolated Python module.
* Write clean, typed, maintainable code.
* Follow REST conventions.
* Do not introduce unnecessary frameworks.

---

# Milestones

Milestone 1

* Backend setup
* Railway PostgreSQL
* Database models
* Alembic
* Project structure

Milestone 2

* School CRUD
* Academic Year CRUD
* Section CRUD
* Student CRUD

Milestone 3

* Assessment CRUD
* Question CRUD

Milestone 4

* Assessment Session
* Process OMR wizard UI

Milestone 5

* Integrate existing OMR engine
* Store attempts
* Store answers

Milestone 6

* Evaluation engine
* Analytics engine

Milestone 7

* Student report page
* PDF generation

Milestone 8

* Dashboard
* Polish
* Testing
* Deployment

---

# Important Constraints

* The OMR engine already exists.
* OMR images are deleted after processing.
* PDFs are generated on demand and are not stored.
* Analytics are generated from database records.
* The database is the single source of truth.
* The architecture should be modular, scalable and maintainable.
