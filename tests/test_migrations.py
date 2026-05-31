"""A3 — verify `alembic upgrade head` builds a schema matching models.py."""
from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.database import Base
from app import models  # noqa: F401 - register tables on Base.metadata

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    return cfg


def test_upgrade_head_creates_all_model_tables(tmp_path):
    db_file = tmp_path / "migrate.db"
    saved = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"
    try:
        command.upgrade(_alembic_config(), "head")
    finally:
        if saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = saved

    # Introspect the migrated DB with a plain sync sqlite engine.
    engine = create_engine(f"sqlite:///{db_file}")
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    engine.dispose()

    assert tables == set(Base.metadata.tables), (
        "migrated schema diverges from models.py: "
        f"missing={set(Base.metadata.tables) - tables}, "
        f"extra={tables - set(Base.metadata.tables)}"
    )


def test_downgrade_base_drops_tables(tmp_path):
    db_file = tmp_path / "migrate2.db"
    saved = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"
    cfg = _alembic_config()
    try:
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")
    finally:
        if saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = saved

    engine = create_engine(f"sqlite:///{db_file}")
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    engine.dispose()
    assert tables == set()
