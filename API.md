# API.md

# Authentication

POST /login

POST /logout

GET /me

---

# Dashboard

GET /dashboard

Returns

* Total schools
* Total students
* Total assessments
* Total attempts
* Recent activity

---

# Schools

GET /schools

GET /schools/{id}

POST /schools

PUT /schools/{id}

DELETE /schools/{id}

---

# Academic Years

GET /academic-years

POST /academic-years

PUT /academic-years/{id}

DELETE /academic-years/{id}

---

# Students

GET /students

Supports filters

* school
* class
* section

POST /students

PUT /students/{id}

DELETE /students/{id}

POST /students/import

Bulk CSV import.

---

# Sections

GET /sections

POST /sections

PUT /sections/{id}

DELETE /sections/{id}

---

# Assessments

GET /assessments

GET /assessments/{id}

POST /assessments

PUT /assessments/{id}

DELETE /assessments/{id}

POST /assessments/{id}/duplicate

---

# Questions

POST /assessments/{id}/questions

PUT /questions/{id}

DELETE /questions/{id}

---

# Assessment Sessions

POST /assessment-sessions

GET /assessment-sessions

GET /assessment-sessions/{id}

---

# OMR

POST /process-omr

Input

* Assessment Session
* Images

Output

* Success count
* Failed count
* Student attempts

---

# Reports

GET /reports

Supports filters

School

Academic Year

Class

Assessment

Student

GET /reports/{attempt_id}

GET /reports/{attempt_id}/pdf

---

# Analytics

GET /analytics/student/{attempt_id}

Returns

Student Score

School Average

Overall Average

School Rank

Overall Rank

Percentile

Domain Scores

Radar Chart data
