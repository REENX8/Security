"""Golden tests: pin the verdict for a hand-picked set of URLs.

Regressions in the model or feature extraction will trip these. The expected
labels are the most-tolerant grouping (safe vs. risky) so cosmetic threshold
changes do not flake the suite.
"""

from __future__ import annotations

import pytest

from app.ml.loader import load_scorer

scorer = load_scorer()


LEGIT_URLS = [
    "https://www.obec.go.th",
    "https://www.moe.go.th",
    "https://chula.ac.th/admission",
    "https://www.ku.ac.th",
    "https://mahidol.ac.th",
    "https://www.bot.or.th",
    "https://www.google.com",
    "https://github.com/explore",
    "https://www.wikipedia.org",
    "https://scb.co.th",
    "https://www.thairath.co.th",
]

RISKY_URLS = [
    "http://obec.com/verify-account",
    "https://rd-go-th-refund.online/e-service/login",
    "http://203.0.113.45/obec/secure/login",
    "https://moe.go.th.verify-login.top/signin",
    "http://chula-ac-th-scholarship.info/account/update",
    "https://www.ku.ac.th@phish-site.xyz/login",
    "http://secure-bot-or-th-update.club/webscr",
    "http://obec.go.th.evil-domain.net/wp-login.php",
]


@pytest.mark.parametrize("url", LEGIT_URLS)
def test_legitimate_urls_not_phishing(url):
    result = scorer.score(url)
    assert result["label"] != "phishing", (
        f"false positive on {url}: score={result['score']:.3f} "
        f"reason={result['reason']}"
    )


@pytest.mark.parametrize("url", RISKY_URLS)
def test_phishing_urls_flagged(url):
    result = scorer.score(url)
    assert result["label"] in ("phishing", "suspicious"), (
        f"missed phishing on {url}: score={result['score']:.3f} "
        f"reason={result['reason']}"
    )


def test_no_false_positives_on_legit_set():
    """Stronger guarantee than the parametrised test: ALL legit URLs are
    classified strictly as 'safe'."""
    fails = []
    for url in LEGIT_URLS:
        r = scorer.score(url)
        if r["label"] != "safe":
            fails.append((url, r["label"], r["score"]))
    assert not fails, f"non-safe verdicts on legit URLs: {fails}"
