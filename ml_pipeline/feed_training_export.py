"""Export verified feed phishing URLs to training/holdout corpora (F1).

Reads url_checks rows where label=phishing AND source is a known feed,
deduplicates against existing seed CSVs, and appends new URLs to:
  * data/live_feed_phishing.csv  (80% training split)
  * data/live_feed_holdout.csv   (20% holdout split)

Split is strictly by ingested_at timestamp (oldest 80% → train, newest 20% →
holdout) to prevent data leakage.

Usage (offline, requires DB):
    python -m ml_pipeline.feed_training_export [--since HOURS] [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "backend"))

from ml_pipeline.config import (  # noqa: E402
    FEED_EXPORT_MIN_AGE_HOURS,
    GENERIC_PHISH_SEED_CSV,
    LIVE_FEED_CSV,
    LIVE_FEED_HOLDOUT_CSV,
    THAI_PHISH_SEED_CSV,
    ensure_dirs,
)

_FEED_CSV_FIELDS = ["url", "label", "source", "ingested_at"]
_TRAIN_FRACTION = 0.80


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


def _load_existing_urls(*csv_paths: str) -> set[str]:
    """Return the set of URL hashes already in the given CSV files."""
    seen: set[str] = set()
    for path in csv_paths:
        p = Path(path)
        if not p.exists():
            continue
        with p.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                url = row.get("url", "")
                if url:
                    seen.add(_url_hash(url))
    return seen


def _append_rows(path: str, rows: list[dict], fields: list[str]) -> None:
    p = Path(path)
    write_header = not p.exists() or p.stat().st_size == 0
    with p.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def export_feed_urls(
    session,
    since_hours: int = 7 * 24,
    dry_run: bool = False,
) -> dict:
    """Export new feed phishing URLs from the DB to training/holdout CSVs.

    Args:
        session: synchronous SQLAlchemy session (or AsyncSession in sync context).
        since_hours: look back this many hours for new feed URLs.
        dry_run: if True, return counts but don't write any files.

    Returns a dict with keys: exported_train, exported_holdout, skipped_dups.
    """
    import sqlalchemy as sa

    # Import here so the module can be imported without a running backend.
    from app.models import UrlCheck

    ensure_dirs()

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)
    min_age = datetime.now(tz=timezone.utc) - timedelta(hours=FEED_EXPORT_MIN_AGE_HOURS)

    stmt = (
        sa.select(UrlCheck)
        .where(UrlCheck.label == "phishing")
        .where(UrlCheck.checked_at >= cutoff)
        .where(UrlCheck.checked_at <= min_age)
        # Only rows that came from a feed (features JSON contains feed_source).
        .where(UrlCheck.features["feed_source"].as_string() != None)  # noqa: E711
        .order_by(UrlCheck.checked_at)
    )

    rows = session.execute(stmt).scalars().all()

    existing = _load_existing_urls(
        THAI_PHISH_SEED_CSV,
        GENERIC_PHISH_SEED_CSV,
        LIVE_FEED_CSV,
        LIVE_FEED_HOLDOUT_CSV,
    )

    new_rows: list[dict] = []
    skipped = 0
    for row in rows:
        h = _url_hash(row.url)
        if h in existing:
            skipped += 1
            continue
        existing.add(h)
        new_rows.append({
            "url": row.url,
            "label": "phishing",
            "source": "feed",
            "ingested_at": row.checked_at.isoformat() if row.checked_at else "",
        })

    split = int(len(new_rows) * _TRAIN_FRACTION)
    train_rows = new_rows[:split]
    holdout_rows = new_rows[split:]

    if not dry_run:
        if train_rows:
            _append_rows(LIVE_FEED_CSV, train_rows, _FEED_CSV_FIELDS)
        if holdout_rows:
            _append_rows(LIVE_FEED_HOLDOUT_CSV, holdout_rows, _FEED_CSV_FIELDS)

    print(
        f"[feed-export] exported {len(new_rows)} new URLs "
        f"({len(train_rows)} train, {len(holdout_rows)} holdout) "
        f"since {cutoff.date()} (skipped {skipped} dups)"
    )
    return {
        "exported_train": len(train_rows),
        "exported_holdout": len(holdout_rows),
        "skipped_dups": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export feed phishing URLs to training corpus")
    parser.add_argument("--since", type=int, default=7 * 24,
                        help="Look back this many hours (default: 168 = 7 days)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Count but don't write files")
    args = parser.parse_args(argv)

    import os
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("[feed-export] DATABASE_URL not set", file=sys.stderr)
        return 1

    import sqlalchemy as sa

    engine = sa.create_engine(db_url)
    with sa.orm.Session(engine) as session:
        export_feed_urls(session, since_hours=args.since, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
