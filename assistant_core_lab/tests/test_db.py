from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from assistant_api.db import ChatSession, Feedback, Interaction, Repository, hash_session, init_db, make_engine


def make_repo():
    engine = make_engine("sqlite://")
    init_db(engine)
    return Repository(engine, "salt"), engine


def test_session_id_is_hashed():
    repo, engine = make_repo()
    repo.record_interaction("student-42", "r1", "fee", None, True, False, 3.0)
    with Session(engine) as db:
        s = db.exec(select(ChatSession)).one()
    assert s.id == hash_session("student-42", "salt") and "student-42" not in s.id


def test_one_session_many_interactions():
    repo, engine = make_repo()
    for i in range(3):
        repo.record_interaction("s", f"r{i}", "rule", "H26-5.3", True, False, 10.0)
    with Session(engine) as db:
        assert len(db.exec(select(ChatSession)).all()) == 1
        assert len(db.exec(select(Interaction)).all()) == 3


def test_add_feedback_requires_existing_interaction():
    repo, _ = make_repo()
    assert repo.add_feedback("missing", 1, None) is None

    repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
    fb = repo.add_feedback("r1", -1, "wrong fee")
    assert fb is not None
    assert fb.id == 1
    assert fb.request_id == "r1"
    assert fb.rating == -1
    assert fb.comment == "wrong fee"
    assert fb.created_at is not None


def test_add_feedback_enforces_rating_constraint():
    repo, _ = make_repo()
    repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
    with pytest.raises(IntegrityError):
        repo.add_feedback("r1", 2, "out of range")


def test_list_feedback_newest_first_and_limit():
    repo, engine = make_repo()
    repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
    repo.record_interaction("s", "r2", "rule", "H26-1", True, False, 2.0)
    repo.record_interaction("s", "r3", "office", None, True, False, 3.0)

    same_ts = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)
    with Session(engine) as db:
        fb1 = Feedback(request_id="r1", rating=1, comment="first", created_at=same_ts)
        fb2 = Feedback(request_id="r2", rating=0, comment="second", created_at=same_ts)
        db.add(fb1)
        db.add(fb2)
        db.commit()
    fb3 = repo.add_feedback("r3", -1, "third")
    assert fb3 is not None

    listed = repo.list_feedback(limit=10)
    assert [item.request_id for item in listed] == ["r3", "r2", "r1"]

    limited = repo.list_feedback(limit=2)
    assert [item.request_id for item in limited] == ["r3", "r2"]

    assert repo.list_feedback(limit=0) == []
    assert repo.list_feedback(limit=-1) == []


def test_feedback_survives_engine_restart(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'feedback_repo.db'}"
    engine1 = make_engine(db_url)
    init_db(engine1)
    repo1 = Repository(engine1, "salt")
    repo1.record_interaction("s", "req-persist", "fee", None, True, False, 5.0)
    saved = repo1.add_feedback("req-persist", 1, "persisted")
    assert saved is not None
    engine1.dispose()

    engine2 = make_engine(db_url)
    repo2 = Repository(engine2, "salt")
    rows = repo2.list_feedback()
    assert len(rows) == 1
    assert rows[0].id == saved.id
    assert rows[0].request_id == "req-persist"
    assert rows[0].rating == 1
    assert rows[0].comment == "persisted"
    engine2.dispose()
