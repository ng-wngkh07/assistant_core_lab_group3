"""Tests for Lab 5 Database, Persistence, Privacy, and Statistics (Parts E-F).

Deliverable for Member 4 (Hoàng Bách):
- Database schema & model validation
- Privacy & session hashing checks (no PII stored)
- Repository interaction & feedback persistence
- Server restart / persistence across sessions
- Statistical analytics queries (F1–F3, H2)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from assistant_api.db import (
    ChatSession,
    Feedback,
    Interaction,
    Repository,
    hash_session,
    init_db,
    make_engine,
)
from assistant_api.main import create_app
from assistant_core.config import Settings

# ---------------------------------------------------------------------------
# 1. Database Schema, Models & Constraints
# ---------------------------------------------------------------------------


def test_database_tables_and_metadata():
    """Verify that all three required tables are registered in SQLModel metadata."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)

    table_names = set(ChatSession.metadata.tables.keys())
    assert {"chat_session", "interaction", "feedback"}.issubset(table_names)


def test_feedback_rating_check_constraint():
    """Verify rating CheckConstraint: only -1, 0, 1 are accepted; others raise IntegrityError."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    repo = Repository(engine, salt="test-salt")
    repo.record_interaction(
        raw_session="s1",
        request_id="req-valid",
        intent="fee",
        topic="tuition",
        resolved=True,
        degraded=False,
        latency_ms=12.5,
    )

    # Valid ratings work
    for rating in (-1, 0, 1):
        fb = repo.add_feedback("req-valid", rating=rating, comment=f"Rating {rating}")
        assert fb is not None
        assert fb.rating == rating

    # Invalid rating directly at DB level violates CheckConstraint
    with pytest.raises(IntegrityError):
        with Session(engine) as db:
            invalid_fb = Feedback(request_id="req-valid", rating=5, comment="Invalid rating")
            db.add(invalid_fb)
            db.commit()


def test_interaction_unique_request_id():
    """Verify UNIQUE constraint on interaction.request_id."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    repo = Repository(engine, salt="test-salt")
    repo.record_interaction("s1", "req-dup", "fee", None, True, False, 10.0)

    # Attempting to insert an interaction with duplicate request_id must fail
    with pytest.raises(IntegrityError):
        with Session(engine) as db:
            duplicate = Interaction(
                request_id="req-dup",
                session_id=hash_session("s1", "test-salt"),
                intent="office",
            )
            db.add(duplicate)
            db.commit()


# ---------------------------------------------------------------------------
# 2. Privacy & Data Minimization (PDPA Compliance)
# ---------------------------------------------------------------------------


def test_session_hashing_and_salt():
    """Verify session hashing is deterministic, truncated to 16 hex chars, and salted."""
    raw = "student-session-xyz-12345"
    salt1 = "super-secret-salt-1"
    salt2 = "super-secret-salt-2"

    h1 = hash_session(raw, salt1)
    h2 = hash_session(raw, salt1)
    h3 = hash_session(raw, salt2)

    assert len(h1) == 16
    assert h1 == h2  # deterministic with same salt
    assert h1 != h3  # different salt gives different hash
    assert raw not in h1  # raw session string is not exposed


def test_pdpa_compliance_no_pii_stored(service, settings):
    """Verify that interaction records store only metadata, and no personal question text or names."""
    app = create_app(settings, service)
    client = TestClient(app)
    r = client.post(
        "/v1/chat",
        json={
            "session_id": "confidential_session_001",
            "message": "My name is Alice, student ID 25127014. What is the tuition for 18 credits?",
        },
    )
    assert r.status_code == 200
    assert r.json()["request_id"] is not None

    # Check the database columns: ensure no user prompt text or personal data is persisted
    columns = [c.name for c in Interaction.__table__.columns]
    assert "message" not in columns
    assert "student_name" not in columns
    assert "phone" not in columns
    assert "prompt" not in columns


# ---------------------------------------------------------------------------
# 3. Repository Operations (R1–R2)
# ---------------------------------------------------------------------------


def test_repository_lifecycle():
    """Test full repository flow: recording interactions, chat sessions, feedback, and list."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    repo = Repository(engine, salt="lifecycle-salt")

    # 1. First interaction in session -> creates ChatSession and Interaction
    repo.record_interaction(
        raw_session="user-ses-1",
        request_id="req-001",
        intent="rule",
        topic="retake-limit",
        resolved=True,
        degraded=False,
        latency_ms=15.2,
    )
    with Session(engine) as db:
        sessions = db.exec(select(ChatSession)).all()
        interactions = db.exec(select(Interaction)).all()
        assert len(sessions) == 1
        assert len(interactions) == 1
        assert interactions[0].request_id == "req-001"
        assert interactions[0].intent == "rule"

    # 2. Second interaction in the SAME session -> reuses ChatSession
    repo.record_interaction(
        raw_session="user-ses-1",
        request_id="req-002",
        intent="fee",
        topic="tuition",
        resolved=True,
        degraded=False,
        latency_ms=8.4,
    )
    with Session(engine) as db:
        assert len(db.exec(select(ChatSession)).all()) == 1  # Still 1 session
        assert len(db.exec(select(Interaction)).all()) == 2  # 2 interactions

    # 3. Add feedback for non-existent interaction -> returns None
    assert repo.add_feedback("non-existent-req", 1, "great") is None

    # 4. Add feedback for existing interaction -> returns Feedback object with DB ID
    fb1 = repo.add_feedback("req-001", 1, "Helpful answer!")
    assert fb1 is not None
    assert fb1.id is not None
    assert fb1.request_id == "req-001"
    assert fb1.rating == 1

    fb2 = repo.add_feedback("req-002", -1, "Not what I asked")
    assert fb2 is not None
    assert fb2.id is not None

    # 5. List feedback: newest first, respecting limit
    listed = repo.list_feedback(limit=10)
    assert len(listed) == 2
    assert listed[0].id == fb2.id  # Newest first
    assert listed[1].id == fb1.id

    limited = repo.list_feedback(limit=1)
    assert len(limited) == 1
    assert limited[0].id == fb2.id


# ---------------------------------------------------------------------------
# 4. Data Persistence Across Restarts (Survives Restart Requirement)
# ---------------------------------------------------------------------------


def test_sqlite_persistence_across_restart(tmp_path: Path):
    """Verify that interaction and feedback survive a full engine restart on disk."""
    db_file = tmp_path / "persistence_test.db"
    db_url = f"sqlite:///{db_file}"
    salt = "restart-salt"

    # Phase 1: Initialize database, record data, and disconnect
    engine1 = make_engine(db_url)
    init_db(engine1)
    repo1 = Repository(engine1, salt=salt)

    repo1.record_interaction(
        raw_session="persist-sess",
        request_id="persist-req-1",
        intent="office",
        topic="academic_affairs",
        resolved=True,
        degraded=False,
        latency_ms=25.0,
    )
    fb = repo1.add_feedback("persist-req-1", rating=1, comment="Survives restart!")
    assert fb is not None
    engine1.dispose()

    # Phase 2: Start a brand-new engine pointing to the same file (simulating server reboot)
    engine2 = make_engine(db_url)
    repo2 = Repository(engine2, salt=salt)

    feedbacks = repo2.list_feedback()
    assert len(feedbacks) == 1
    assert feedbacks[0].request_id == "persist-req-1"
    assert feedbacks[0].rating == 1
    assert feedbacks[0].comment == "Survives restart!"

    with Session(engine2) as db:
        inter = db.exec(select(Interaction).where(Interaction.request_id == "persist-req-1")).first()
        assert inter is not None
        assert inter.intent == "office"
        assert inter.topic == "academic_affairs"

    engine2.dispose()


def test_api_feedback_survives_server_restart(tmp_path: Path, service):
    """End-to-end API test: chat + feedback in one server instance, restart, retrieve via GET /v1/feedback."""
    db_file = tmp_path / "api_restart.db"
    db_url = f"sqlite:///{db_file}"
    settings = Settings(
        database_url=db_url,
        session_salt="api-salt",
        api_admin_key="admin-secret",
    )

    # Server Instance 1:
    engine1 = make_engine(db_url)
    init_db(engine1)
    repo1 = Repository(engine1, settings.session_salt)
    app1 = create_app(settings=settings, service=service, repo=repo1)
    client1 = TestClient(app1)

    # Chat and get request_id
    chat_resp = client1.post("/v1/chat", json={"message": "tuition for 10 credits", "session_id": "ses-pers-1"})
    assert chat_resp.status_code == 200
    req_id = chat_resp.json()["request_id"]

    # Send feedback
    fb_resp = client1.post("/v1/feedback", json={"request_id": req_id, "rating": 1, "comment": "Excellent answer!"})
    assert fb_resp.status_code == 201
    engine1.dispose()

    # Server Instance 2 (Simulating server stop/restart):
    engine2 = make_engine(db_url)
    repo2 = Repository(engine2, settings.session_salt)
    app2 = create_app(settings=settings, service=service, repo=repo2)
    client2 = TestClient(app2)

    # Query feedback with admin key
    get_resp = client2.get("/v1/feedback", headers={"X-API-Key": "admin-secret"})
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data) == 1
    assert data[0]["request_id"] == req_id
    assert data[0]["rating"] == 1
    assert data[0]["comment"] == "Excellent answer!"

    engine2.dispose()


# ---------------------------------------------------------------------------
# 5. Part F Statistical Queries Verification (F1–F3, H2)
# ---------------------------------------------------------------------------


def test_part_f_statistics_queries():
    """Verify statistical aggregation queries (F1: intent counts, F2: avg latency, F3: thumbs-down topics)."""
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    repo = Repository(engine, salt="stats-salt")

    # Seed controlled dataset
    # Intents: 3 x 'rule', 2 x 'fee', 1 x 'office'
    test_data = [
        ("s1", "r-1", "rule", "H26-1", True, False, 10.0, 1),
        ("s1", "r-2", "rule", "H26-1", True, False, 20.0, -1),
        ("s2", "r-3", "rule", "H26-2", True, False, 30.0, -1),
        ("s3", "r-4", "fee", "tuition", True, False, 15.0, 1),
        ("s4", "r-5", "fee", "tuition", True, False, 25.0, -1),
        ("s5", "r-6", "office", "library", True, False, 50.0, 0),
    ]

    for sess, req_id, intent, topic, resolved, degraded, lat, rating in test_data:
        repo.record_interaction(sess, req_id, intent, topic, resolved, degraded, lat)
        repo.add_feedback(req_id, rating, f"Feedback for {req_id}")

    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()

        # Test F1: Questions per intent
        cursor.execute("""
            SELECT intent, COUNT(*) AS requests
            FROM interaction
            GROUP BY intent
            ORDER BY requests DESC;
        """)
        f1_rows = cursor.fetchall()
        assert f1_rows == [("rule", 3), ("fee", 2), ("office", 1)]

        # Test F2: Average time taken per intent
        cursor.execute("""
            SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_latency
            FROM interaction
            GROUP BY intent
            ORDER BY avg_latency ASC;
        """)
        f2_rows = cursor.fetchall()
        avg_dict = {row[0]: row[1] for row in f2_rows}
        assert avg_dict["rule"] == 20.0
        assert avg_dict["fee"] == 20.0
        assert avg_dict["office"] == 50.0

        # Test F3: Which topics got the most thumbs-down? (rating = -1)
        cursor.execute("""
            SELECT i.topic, COUNT(*) AS thumbs_down
            FROM interaction i
            JOIN feedback f ON f.request_id = i.request_id
            WHERE f.rating = -1 AND i.topic IS NOT NULL
            GROUP BY i.topic
            ORDER BY thumbs_down DESC;
        """)
        f3_rows = cursor.fetchall()
        assert len(f3_rows) == 3
        topics = {row[0] for row in f3_rows}
        assert topics == {"H26-1", "H26-2", "tuition"}

        # Test H2: Degraded percentage query
        cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN degraded THEN 1 ELSE 0 END) AS degraded_cnt,
                ROUND(100.0 * SUM(CASE WHEN degraded THEN 1 ELSE 0 END) / COUNT(*), 2) AS degraded_pct
            FROM interaction;
        """)
        h2_row = cursor.fetchone()
        assert h2_row[0] == 6
        assert h2_row[1] == 0
        assert h2_row[2] == 0.0

    finally:
        conn.close()
