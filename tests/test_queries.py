"""Tests for Lab 5 data seeding and analytical SQL queries (Part F: F1–F3, H2)."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from scripts.seed import seed_database


@pytest.fixture
def seeded_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_assistant.db"
    seed_database(db_file, count=300)
    return db_file


def test_seed_database(seeded_db: Path):
    """Verify that seeding populates sessions, interactions, and feedback."""
    con = sqlite3.connect(seeded_db)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM chat_session")
    session_count = cur.fetchone()[0]
    assert session_count >= 10

    cur.execute("SELECT COUNT(*) FROM interaction")
    interaction_count = cur.fetchone()[0]
    assert interaction_count == 300

    cur.execute("SELECT COUNT(*) FROM feedback")
    feedback_count = cur.fetchone()[0]
    assert feedback_count > 0

    con.close()


def test_sql_query_f1(seeded_db: Path):
    """F1: Questions per intent."""
    con = sqlite3.connect(seeded_db)
    cur = con.cursor()
    cur.execute("""
        SELECT intent, COUNT(*) AS requests
        FROM interaction
        GROUP BY intent
        ORDER BY requests DESC;
    """)
    rows = cur.fetchall()
    con.close()

    assert len(rows) == 5
    intents = [r[0] for r in rows]
    assert intents == ["rule", "fee", "office", "greeting", "unknown"]
    counts = [r[1] for r in rows]
    assert counts[0] == 140
    assert counts[1] == 61
    assert counts[2] == 47


def test_sql_query_f2(seeded_db: Path):
    """F2: Average latency per intent."""
    con = sqlite3.connect(seeded_db)
    cur = con.cursor()
    cur.execute("""
        SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_latency_ms
        FROM interaction
        GROUP BY intent
        ORDER BY avg_latency_ms DESC;
    """)
    rows = cur.fetchall()
    con.close()

    assert len(rows) == 5
    avg_map = {r[0]: r[1] for r in rows}
    assert avg_map["unknown"] > avg_map["rule"] > avg_map["fee"]


def test_sql_query_f3(seeded_db: Path):
    """F3: Topics with most thumbs-down."""
    con = sqlite3.connect(seeded_db)
    cur = con.cursor()
    cur.execute("""
        SELECT i.topic, COUNT(*) AS thumbs_down
        FROM interaction i
        JOIN feedback f ON f.request_id = i.request_id
        WHERE f.rating = -1 AND i.topic IS NOT NULL
        GROUP BY i.topic
        ORDER BY thumbs_down DESC;
    """)
    rows = cur.fetchall()
    con.close()

    assert len(rows) > 0
    # First row has highest thumbs-down
    assert rows[0][1] >= rows[-1][1]
