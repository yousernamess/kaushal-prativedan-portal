-- Users (admins)
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(50) DEFAULT 'admin',
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Schools
CREATE TABLE schools (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Batches
CREATE TABLE batches (
    id          SERIAL PRIMARY KEY,
    school_id   INTEGER REFERENCES schools(id),
    class       VARCHAR(50) NOT NULL,
    batch_name  VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Students
CREATE TABLE students (
    id          SERIAL PRIMARY KEY,
    roll_number VARCHAR(50) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    batch_id    INTEGER REFERENCES batches(id),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (roll_number, batch_id)
);

-- Questions
CREATE TABLE questions (
    id              SERIAL PRIMARY KEY,
    created_by      INTEGER REFERENCES users(id),
    class           VARCHAR(50) NOT NULL,
    exam_type       VARCHAR(20) NOT NULL CHECK (exam_type IN ('baseline', 'endline')),
    question_text   TEXT NOT NULL,
    option_a        TEXT NOT NULL,
    option_b        TEXT NOT NULL,
    option_c        TEXT NOT NULL,
    option_d        TEXT NOT NULL,
    correct_answer  VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    skill           VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Exam Configs
CREATE TABLE exam_configs (
    id              SERIAL PRIMARY KEY,
    created_by      INTEGER REFERENCES users(id),
    config_name     VARCHAR(255) NOT NULL,
    question_count  INTEGER NOT NULL,
    class           VARCHAR(50) NOT NULL,
    exam_type       VARCHAR(20) NOT NULL CHECK (exam_type IN ('baseline', 'endline')),
    skill_map       JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Exam Config Questions (junction table)
CREATE TABLE exam_config_questions (
    id              SERIAL PRIMARY KEY,
    exam_config_id  INTEGER REFERENCES exam_configs(id) ON DELETE CASCADE,
    question_id     INTEGER REFERENCES questions(id),
    question_number INTEGER NOT NULL,
    UNIQUE (exam_config_id, question_number)
);

-- Upload Sessions
CREATE TABLE upload_sessions (
    id              SERIAL PRIMARY KEY,
    created_by      INTEGER REFERENCES users(id),
    batch_id        INTEGER REFERENCES batches(id),
    exam_config_id  INTEGER REFERENCES exam_configs(id),
    exam_type       VARCHAR(20) NOT NULL CHECK (exam_type IN ('baseline', 'endline')),
    status          VARCHAR(50) DEFAULT 'pending',
    total_sheets    INTEGER DEFAULT 0,
    processed       INTEGER DEFAULT 0,
    failed          INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    completed_at    TIMESTAMP
);

-- OMR Sheets
CREATE TABLE omr_sheets (
    id                  SERIAL PRIMARY KEY,
    upload_session_id   INTEGER REFERENCES upload_sessions(id),
    student_id          INTEGER REFERENCES students(id),
    filename            VARCHAR(255) NOT NULL,
    status              VARCHAR(50) DEFAULT 'pending',
    error_message       TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    processed_at        TIMESTAMP
);

-- Results
CREATE TABLE results (
    id                  SERIAL PRIMARY KEY,
    omr_sheet_id        INTEGER REFERENCES omr_sheets(id),
    student_id          INTEGER REFERENCES students(id),
    exam_config_id      INTEGER REFERENCES exam_configs(id),
    exam_type           VARCHAR(20) NOT NULL CHECK (exam_type IN ('baseline', 'endline')),
    detected_answers    JSONB NOT NULL,
    skill_scores        JSONB NOT NULL,
    total_score         INTEGER NOT NULL,
    total_marks         INTEGER NOT NULL,
    processed_at        TIMESTAMP DEFAULT NOW()
);