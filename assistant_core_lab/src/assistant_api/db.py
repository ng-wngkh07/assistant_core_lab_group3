import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    id: str = Field(primary_key=True, max_length=16)
    channel: str = Field(default="web", max_length=16, sa_column_kwargs={"server_default": "web"})
    created_at: datetime = Field(default_factory=utcnow)
    interactions: list["Interaction"] = Relationship(back_populates="session")


class Interaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(index=True, unique=True, max_length=32)
    session_id: str = Field(foreign_key="chat_session.id", index=True, max_length=16)
    intent: str = Field(index=True, max_length=16)
    topic: str | None = Field(default=None, max_length=32)
    resolved: bool = Field(default=True, sa_column_kwargs={"server_default": "1"})
    degraded: bool = Field(default=False, sa_column_kwargs={"server_default": "0"})
    latency_ms: float = Field(default=0.0, sa_column_kwargs={"server_default": "0"})
    created_at: datetime = Field(default_factory=utcnow, index=True)
    session: Optional["ChatSession"] = Relationship(back_populates="interactions")
    feedback: list["Feedback"] = Relationship(back_populates="interaction")


class Feedback(SQLModel, table=True):
    __table_args__ = (CheckConstraint("rating IN (-1, 0, 1)"),)
    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(foreign_key="interaction.request_id", index=True, max_length=32)
    rating: int
    comment: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    interaction: Optional["Interaction"] = Relationship(back_populates="feedback")


def make_engine(url: str):
    if url in ("sqlite://", "sqlite:///:memory:"):
        return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)


def hash_session(raw: str, salt: str) -> str:
    return hashlib.sha256((salt + raw).encode()).hexdigest()[:16]


class Repository:
    def __init__(self, engine, salt: str):
        self.engine = engine
        self.salt = salt

    def record_interaction(
        self,
        raw_session: str,
        request_id: str,
        intent: str,
        topic: str | None,
        resolved: bool,
        degraded: bool,
        latency_ms: float,
    ) -> None:
        session_id = hash_session(raw_session, self.salt)
        with Session(self.engine) as db:
            if db.get(ChatSession, session_id) is None:
                db.add(ChatSession(id=session_id))
            interaction = Interaction(
                request_id=request_id,
                session_id=session_id,
                intent=intent,
                topic=topic,
                resolved=resolved,
                degraded=degraded,
                latency_ms=latency_ms,
            )
            db.add(interaction)
            db.commit()

    def add_feedback(self, request_id: str, rating: int, comment: str | None = None) -> Feedback | None:
        """Persist feedback for an existing interaction; returns None if request_id is unknown."""
        with Session(self.engine) as db:
            interaction = db.exec(select(Interaction).where(Interaction.request_id == request_id)).first()
            if interaction is None:
                return None
            fb = Feedback(request_id=request_id, rating=rating, comment=comment)
            db.add(fb)
            db.commit()
            db.refresh(fb)
            return fb

    def list_feedback(self, limit: int = 100) -> list[Feedback]:
        """Return newest feedback entries first, up to `limit` rows."""
        if limit <= 0:
            return []
        with Session(self.engine) as db:
            statement = select(Feedback).order_by(Feedback.created_at.desc(), Feedback.id.desc()).limit(limit)
            return list(db.exec(statement).all())
