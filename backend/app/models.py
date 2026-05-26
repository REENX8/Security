"""SQLAlchemy ORM models."""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
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


# ---------------------------------------------------------------------------
# Brand watchlist + webhook notifications  (v1.0 new module)
#
# Operators register the brands they care about ("krungthai", "obec", ...).
# When a new phishing URL is detected whose ``closest_domain`` brand label
# matches a watched brand, the system POSTs an alert to every webhook the
# operator has registered. This is the differentiator from feedback (which
# is post-hoc): watchlist is proactive.
# ---------------------------------------------------------------------------


class BrandWatch(Base):
    __tablename__ = "brand_watch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    description: Mapped[str] = mapped_column(String(256), default="")
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )
    # Stats updated by the watcher:
    last_hit_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hit_count: Mapped[int] = mapped_column(Integer, default=0)


class WebhookDelivery(Base):
    """One row per webhook attempt -- success or failure."""

    __tablename__ = "webhook_delivery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url_checked: Mapped[str] = mapped_column(String(2048), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )


# ---------------------------------------------------------------------------
# Phishing campaign clustering -- groups URLs that look like the same kit.
# A campaign fingerprint is the (closest_domain, suspicious_tld) tuple plus
# a normalised path shape. Stored separately so we can list campaigns and
# show their reach without scanning every UrlCheck row.
# ---------------------------------------------------------------------------


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fingerprint: Mapped[str] = mapped_column(
        String(256), nullable=False, unique=True, index=True
    )
    closest_domain: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    tld_signature: Mapped[str] = mapped_column(String(32), default="")
    path_shape: Mapped[str] = mapped_column(String(128), default="")
    url_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
    )
    last_seen: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )


# ---------------------------------------------------------------------------
# External threat feed ingestion (v1.1 new module)
#
# Operators can enable polling of OpenPhish and PhishTank. Each source has
# its own poll schedule. FeedIngestionRecord deduplicates URLs per source so
# the same URL is not re-scored on every poll.
# ---------------------------------------------------------------------------


class ExternalFeedSourceType(str, enum.Enum):
    openphish = "openphish"
    phishtank = "phishtank"


class ExternalFeedSource(Base):
    __tablename__ = "external_feed_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    source_type: Mapped[ExternalFeedSourceType] = mapped_column(
        Enum(ExternalFeedSourceType, name="external_feed_source_type_enum"), nullable=False
    )
    feed_url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_polled_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    total_urls_ingested: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
    )


class FeedIngestionRecord(Base):
    """Deduplication log — one row per (url, source) that has been processed."""

    __tablename__ = "feed_ingestion_records"
    __table_args__ = (UniqueConstraint("url_hash", "source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("external_feed_sources.id"), nullable=False, index=True
    )
    ingested_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )
