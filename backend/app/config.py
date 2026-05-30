"""Application settings (pydantic-settings, read from environment / .env)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = <root>/backend/app/config.py -> parents[2].
ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    # --- database ---
    # asyncpg for PostgreSQL; aiosqlite also works for a zero-setup demo.
    # Managed providers (Render, Heroku, Railway) hand out a DSN that
    # starts with "postgres://" or "postgresql://" -- the async engine
    # needs an explicit "+asyncpg" driver hint. We patch it once in the
    # validator below so call sites can stay generic.
    database_url: str = Field(
        default="postgresql+asyncpg://phish:phish@localhost:5432/phishdb"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://") and "+asyncpg" not in v:
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    # --- model artifacts ---
    model_dir: str = Field(default=str(ROOT / "models"))
    whitelist_path: str = Field(default=str(ROOT / "models" / "whitelist.json"))

    # --- security ---
    api_key: str = Field(default="dev-local-key-change-me")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    )

    # --- JWT auth (dashboard login) ---
    # Generate hash: python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('yourpassword'))"
    admin_username: str = Field(default="admin")
    admin_password_hash: str = Field(default="")
    jwt_secret: str = Field(default="change-this-secret-in-production-use-openssl-rand-hex-32")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=480)  # 8 hours

    # --- rate limiting ---
    rate_limit: str = Field(default="100/minute")
    # /check and /check/batch are public (no API key needed for the extension).
    # Rate-limited per IP to prevent abuse. Set higher than the global limit
    # because many real users will hit this endpoint simultaneously.
    public_check_rate_limit: str = Field(default="30/minute")

    # --- feature extraction (network lookups) ---
    enable_whois: bool = Field(default=True)
    enable_tls: bool = Field(default=True)
    network_timeout: float = Field(default=2.5)

    # --- scoring thresholds ---
    threshold_suspicious: float = Field(default=0.3)
    threshold_phishing: float = Field(default=0.7)

    # --- caching / batch ---
    enable_cache: bool = Field(default=True)
    cache_ttl: float = Field(default=60.0)        # seconds
    cache_maxsize: int = Field(default=2048)
    batch_max_size: int = Field(default=50)
    # Set REDIS_URL (e.g. redis://redis:6379/0) to share the /check cache
    # across replicas. Empty = per-process in-memory cache. If a URL is given
    # but unreachable, the app logs a warning and uses the in-memory cache.
    redis_url: str = Field(default="")
    redis_namespace: str = Field(default="phish:cache:")

    # --- server ---
    app_name: str = Field(default="Thai Phishing URL Detector")
    log_format: str = Field(default="text")  # "text" or "json"

    # --- public threat feed ---
    enable_public_feed: bool = Field(default=True)

    # --- campaign clustering ---
    enable_campaign_tracking: bool = Field(default=True)

    # --- external threat feed ingestion ---
    external_feeds_enabled: bool = Field(default=False)
    external_feed_poll_interval: int = Field(default=60)   # minutes between polls
    external_feed_batch_size: int = Field(default=100)     # max URLs per source per poll
    phishtank_api_key: str = Field(default="")
    openphish_feed_url: str = Field(default="https://openphish.com/feed.txt")

    # --- URL unshortening ---
    enable_url_unshortening: bool = Field(default=True)
    unshorten_timeout: float = Field(default=5.0)

    # --- content-based gray-zone check ---
    gray_zone_content_check: bool = Field(default=False)
    content_check_timeout: float = Field(default=5.0)

    # --- LINE Messaging API bot ---
    line_channel_token: str = Field(default="")
    line_channel_secret: str = Field(default="")

    # --- feedback-driven auto-retrain ---
    feedback_retrain_enabled: bool = Field(default=False)
    feedback_retrain_interval_hours: int = Field(default=336)  # 14 days
    # Minimum confirmed-feedback rows that must accumulate before a retrain is
    # attempted (background loop + POST /admin/retrain).
    feedback_accumulation_threshold: int = Field(default=20)
    # Require the Thai-recall eval gate to pass before promoting a retrained
    # model. Keep True in production -- it is the floor that prevents a bad
    # feedback batch from degrading the live model.
    feedback_promote_requires_gate: bool = Field(default=True)

    @property
    def model_path(self) -> str:
        return str(Path(self.model_dir) / "ensemble.pkl")

    @property
    def scaler_path(self) -> str:
        return str(Path(self.model_dir) / "scaler.pkl")

    @property
    def features_json(self) -> str:
        return str(Path(self.model_dir) / "features.json")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
