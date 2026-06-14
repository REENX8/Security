"""Sanity checks on the offline synthetic URL generator.

Focus on the v1.9 archetypes (cctld_clone, user_content_host, query_blob) and
the invariant that generated hosts must never collide with any committed
phishing holdout — otherwise the "independent" holdout would leak into training.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

from ml_pipeline.synthetic_generator import SyntheticGenerator
from phish_features import Whitelist

ROOT = Path(__file__).resolve().parents[1]

_HOLDOUTS = (
    ROOT / "data" / "real_phish_holdout.csv",
    ROOT / "data" / "generic_phish_holdout.csv",
    ROOT / "data" / "thai_phish_holdout.csv",
)
_USER_CONTENT = (
    "pages.dev", "github.io", "web.app", "workers.dev",
    "sealos.app", "netlify.app", "weebly.com",
)
_CCTLD_RE = re.compile(r"\.(com|co|net)\.(kz|pl|ru|br|in|id|ng|at|ve|ua|land)(/|$)")


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    wl = Whitelist.from_csv(str(ROOT / "data" / "thai_gov_domains.csv"))
    gen = SyntheticGenerator(wl.domains, seed=42)
    return gen.generate(n_legit=3000, n_phish=3000)


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def test_new_phishing_archetypes_present(rows):
    """The three v1.9 phishing archetypes must each appear in a 3k sample."""
    phish = [r["url"] for r in rows if r["label"] == 1]
    cctld = sum(1 for u in phish if _CCTLD_RE.search(u))
    user_content = sum(1 for u in phish if any(p in u for p in _USER_CONTENT))
    query_blob = sum(1 for u in phish if re.search(r"\?[a-z]+=[A-Za-z0-9+/=]{80,}", u))
    assert cctld >= 20, f"cctld_clone under-represented ({cctld})"
    assert user_content >= 20, f"user_content_host under-represented ({user_content})"
    assert query_blob >= 20, f"query_blob under-represented ({query_blob})"


def test_benign_user_content_present(rows):
    """Benign examples on user-content platforms keep the suffix class-neutral."""
    benign_uc = sum(
        1 for r in rows
        if r["label"] == 0 and any(p in r["url"] for p in _USER_CONTENT)
    )
    assert benign_uc >= 20, f"benign user-content under-represented ({benign_uc})"


def test_generated_hosts_do_not_leak_holdout_hosts(rows):
    """Synthetic hosts must never equal a committed holdout host (no eval bleed)."""
    holdout_hosts: set[str] = set()
    for path in _HOLDOUTS:
        if not path.exists():
            continue
        import csv
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                h = _host(row.get("url", ""))
                if h:
                    holdout_hosts.add(h)
    gen_hosts = {_host(r["url"]) for r in rows}
    leak = gen_hosts & holdout_hosts
    assert not leak, f"generated hosts collide with holdout: {sorted(leak)[:10]}"


def test_generate_is_deterministic():
    wl = Whitelist.from_csv(str(ROOT / "data" / "thai_gov_domains.csv"))
    a = SyntheticGenerator(wl.domains, seed=42).generate(n_legit=200, n_phish=200)
    b = SyntheticGenerator(wl.domains, seed=42).generate(n_legit=200, n_phish=200)
    assert [r["url"] for r in a] == [r["url"] for r in b]
