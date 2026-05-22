"""Application settings (pydantic-settings, read from environment / .env)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
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
    database_url: str = Field(
        default="postgresql+asyncpg://phish:phish@localhost:5432/phishdb"
    )

    # --- model artifacts ---
    model_dir: str = Field(default=str(ROOT / "models"))
    whitelist_path: str = Field(default=str(ROOT / "models" / "whitelist.json"))

    # --- security ---
    api_key: str = Field(default="dev-local-key-change-me")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    )

    # --- rate limiting ---
    rate_limit: str = Field(default="100/minute")

    # --- feature extraction (network lookups) ---
    enable_whois: bool = Field(default=True)
    enable_tls: bool = Field(default=True)
    network_timeout: float = Field(default=2.5)

    # --- scoring thresholds ---
    threshold_suspicious: float = Field(default=0.3)
    threshold_phishing: float = Field(default=0.7)

    # --- server ---
    app_name: str = Field(default="Thai Phishing URL Detector")

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
