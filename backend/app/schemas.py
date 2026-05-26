"""Pydantic v2 request / response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CheckRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048,
                     examples=["https://0bec.go.th/login"])

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url must not be empty")
        if " " in v:
            raise ValueError("url must not contain spaces")
        # Tolerant: a scheme is supplied later if missing. We only reject
        # input that cannot possibly be a URL.
        if "." not in v and "://" not in v:
            raise ValueError("url does not look like a valid address")
        return v


class CheckResponse(BaseModel):
    url: str
    score: float = Field(..., ge=0.0, le=1.0)
    ml_score: float | None = Field(default=None, ge=0.0, le=1.0)
    label: Literal["safe", "suspicious", "phishing"]
    reason: str
    features: dict[str, Any]
    rules: dict[str, Any] | None = None
    closest_domain: str | None = None
    edit_distance: int | None = None
    checked_at: str
    cached: bool = False


class BatchCheckRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)


class BatchCheckResponse(BaseModel):
    count: int
    results: list[CheckResponse]


class HistoryItem(BaseModel):
    id: str
    url: str
    score: float
    label: str
    reason: str
    closest_domain: str | None = None
    edit_distance: int | None = None
    checked_at: str
    features: dict[str, Any] | None = None


class HistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[HistoryItem]


class FlaggedDomain(BaseModel):
    domain: str
    count: int


class HourBucket(BaseModel):
    hour: int
    count: int


class DayBucket(BaseModel):
    date: str
    safe: int
    suspicious: int
    phishing: int


class StatsResponse(BaseModel):
    total_checks: int
    phishing_count: int
    suspicious_count: int
    safe_count: int
    phishing_rate: float
    top_flagged_domains: list[FlaggedDomain]
    checks_per_day: list[DayBucket]
    checks_by_hour: list[HourBucket]


class ErrorResponse(BaseModel):
    error: str
    code: str


# --- Whitelist ---

class WhitelistEntryIn(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255)
    agency_name: str = Field(default="", max_length=512)
    category: str = Field(default="other", max_length=64)


class WhitelistEntryOut(BaseModel):
    id: int
    domain: str
    agency_name: str
    category: str
    added_by: str
    is_seeded: bool
    created_at: str


class WhitelistListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WhitelistEntryOut]


# --- Feedback ---

class FeedbackCreate(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048)
    verdict_given: Literal["safe", "suspicious", "phishing", "unverified"]
    correct_verdict: Literal["safe", "suspicious", "phishing"]
    comment: str = Field(default="", max_length=1024)
    source: Literal["extension", "dashboard", "api"] = "dashboard"


class FeedbackOut(BaseModel):
    id: str
    url: str
    verdict_given: str
    correct_verdict: str
    comment: str
    source: str
    created_at: str


class FeedbackListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[FeedbackOut]
