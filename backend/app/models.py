"""SQLAlchemy ORM models."""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite for local demos).
JsonType = JSON().with_variant(JSONB(), "postgresql")


class Label(str, enum.Enum):
    safe = "safe"
    suspicious = "suspicious"
    phishing = "phishing"


class UrlCheck(Base):
    __tablename__ = "url_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[Label] = mapped_column(
        Enum(Label, name="label_enum"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(512), default="")
    features: Mapped[dict] = mapped_column(JsonType, default=dict)
    closest_domain: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    edit_distance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )

    def as_dict(self) -> dict:
        return {
            "id": str(self.id),
            "url": self.url,
            "score": self.score,
            "label": self.label.value,
            "reason": self.reason,
            "features": self.features,
            "closest_domain": self.closest_domain,
            "edit_distance": self.edit_distance,
            "checked_at": self.checked_at.isoformat(),
        }


class DbWhitelistEntry(Base):
    __tablename__ = "whitelist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    agency_name: Mapped[str] = mapped_column(String(512), default="")
    category: Mapped[str] = mapped_column(String(64), default="other")
    added_by: Mapped[str] = mapped_column(String(128), default="admin")
    is_seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )


class FeedbackSource(str, enum.Enum):
    extension = "extension"
    dashboard = "dashboard"
    api = "api"


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    verdict_given: Mapped[str] = mapped_column(String(32), nullable=False)
    correct_verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str] = mapped_column(String(1024), default="")
    source: Mapped[FeedbackSource] = mapped_column(
        Enum(FeedbackSource, name="feedback_source_enum"),
        default=FeedbackSource.dashboard,
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )
