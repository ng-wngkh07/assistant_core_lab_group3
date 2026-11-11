-- 001_init.sql: Initial schema for Study Assistant

CREATE TABLE IF NOT EXISTS chat_session (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL DEFAULT 'web',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    session_id TEXT NOT NULL,
    intent TEXT NOT NULL,
    topic TEXT,
    resolved BOOLEAN NOT NULL DEFAULT 1,
    degraded BOOLEAN NOT NULL DEFAULT 0,
    latency_ms REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_session(id)
);

CREATE INDEX IF NOT EXISTS idx_interaction_session_id ON interaction(session_id);
CREATE INDEX IF NOT EXISTS idx_interaction_intent ON interaction(intent);
CREATE INDEX IF NOT EXISTS idx_interaction_created_at ON interaction(created_at);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating IN (-1, 0, 1)),
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES interaction(request_id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_request_id ON feedback(request_id);
