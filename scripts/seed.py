#!/usr/bin/env python3
"""Seed assistant.db with simulated interaction and feedback data."""

from __future__ import annotations

import hashlib
import random
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

INTENTS = [
    ("rule", 140),
    ("fee", 61),
    ("office", 47),
    ("greeting", 26),
    ("unknown", 26),
]

TOPICS_BY_INTENT = {
    "rule": ["H26-5.3", "H26-2.1", "H26-4.2", "retake-rules", "graduation-req"],
    "fee": ["tuition-fee", "retake-fee", "scholarship", "late-payment"],
    "office": ["academic_affairs", "library", "student_support", "health_center"],
    "greeting": ["hello", "goodbye", "thanks"],
    "unknown": [None],
}

COMMENTS_NEGATIVE = [
    "Did not answer my question",
    "Wrong tuition rate calculation",
    "Office hours mentioned are outdated",
    "Too slow response",
]

COMMENTS_POSITIVE = [
    "Very helpful, thank you!",
    "Accurate information",
    "Quick answer",
]


def seed_database(db_path: str | Path, count: int = 300) -> None:
    db_file = Path(db_path)
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    random.seed(42)  # reproducible seed

    num_sessions = max(count // 5, 10)
    sessions = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for i in range(num_sessions):
        raw = f"session-{i}-{uuid.uuid4().hex[:6]}"
        sid = hashlib.sha256(f"dev-salt{raw}".encode()).hexdigest()[:16]
        created_at = (base_time + timedelta(minutes=i * 15)).isoformat()
        cur.execute(
            "INSERT OR IGNORE INTO chat_session (id, channel, created_at) VALUES (?, ?, ?)",
            (sid, "web", created_at),
        )
        sessions.append(sid)
    con.commit()

    intent_pool = []
    for intent, weight in INTENTS:
        num = int(round(count * (weight / 300.0)))
        intent_pool.extend([intent] * num)

    while len(intent_pool) < count:
        intent_pool.append("rule")
    random.shuffle(intent_pool)
    intent_pool = intent_pool[:count]

    feedback_to_insert = []
    for i, intent in enumerate(intent_pool):
        req_id = uuid.uuid4().hex[:12]
        sid = random.choice(sessions)
        topic_choices = TOPICS_BY_INTENT.get(intent, [None])
        topic = random.choice(topic_choices)
        resolved = 1 if intent != "unknown" else 0
        degraded = 1 if (intent == "unknown" and random.random() < 0.3) else 0

        base_latency = {"rule": 35.0, "fee": 22.0, "office": 18.0, "greeting": 12.0, "unknown": 45.0}[intent]
        latency_ms = round(max(5.0, random.gauss(base_latency, 5.0)), 1)
        created_at = (base_time + timedelta(minutes=i * 20)).isoformat()

        cur.execute(
            """
            INSERT INTO interaction (request_id, session_id, intent, topic, resolved, degraded, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (req_id, sid, intent, topic, resolved, degraded, latency_ms, created_at),
        )

        if random.random() < 0.35:
            if topic == "H26-5.3" and random.random() < 0.7:
                rating = -1
                comment = random.choice(COMMENTS_NEGATIVE)
            else:
                rating = random.choices([1, 0, -1], weights=[60, 15, 25])[0]
                if rating == 1:
                    comment = random.choice(COMMENTS_POSITIVE)
                elif rating == -1:
                    comment = random.choice(COMMENTS_NEGATIVE)
                else:
                    comment = None

            feedback_to_insert.append((req_id, rating, comment, created_at))

    for fb in feedback_to_insert:
        cur.execute(
            "INSERT INTO feedback (request_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
            fb,
        )

    con.commit()
    con.close()
    print(f"seeded {count} interactions into {db_file.name}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed.py <db_path> [count]")
        sys.exit(1)
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    seed_database(sys.argv[1], count)


if __name__ == "__main__":
    main()
