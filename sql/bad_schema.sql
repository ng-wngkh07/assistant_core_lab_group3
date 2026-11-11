-- bad_schema.sql: A badly designed table storing assistant conversations and feedback in one flat table
-- This schema demonstrates severe anti-patterns: PII storage, non-normalized redundant data, and missing constraints.

CREATE TABLE assistant_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,             -- Sensitive student identifier
    student_name TEXT,           -- PII: Full personal name
    student_phone TEXT,          -- PII: Phone number
    session_id TEXT,             -- Raw unhashed session id
    full_question_text TEXT,     -- Plaintext prompt: May contain sensitive personal data
    answer_text TEXT,            -- Duplicated full answer text
    intent TEXT,
    topic TEXT,
    resolved TEXT,               -- Stored as loose text ("yes"/"no"/"true") without type safety
    degraded INTEGER,
    latency_ms REAL,
    feedback_rating INTEGER,     -- No CHECK constraint: allows arbitrary ratings like 100 or -99
    feedback_comment TEXT,
    created_at TEXT              -- Unvalidated text date
);
