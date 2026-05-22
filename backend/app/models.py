"""SQLAlchemy ORM models."""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import JSON, DateTime, Enum, Float, Integer, String, Uuid
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
