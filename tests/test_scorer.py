"""Scorer + threshold logic tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.config import settings  # noqa: E402
from app.ml.loader import load_scorer  # noqa: E402
from app.ml.scorer import label_from_score  # noqa: E402


def test_label_thresholds():
    assert label_from_score(0.0) == "safe"
    assert label_from_score(settings.threshold_suspicious - 0.001) == "safe"
    assert label_from_score(settings.threshold_suspicious) == "suspicious"
    assert label_from_score(settings.threshold_phishing - 0.001) == "suspicious"
    assert label_from_score(settings.threshold_phishing) == "phishing"
    assert label_from_score(1.0) == "phishing"


class TestScorer:
    @classmethod
    def setup_class(cls):
        cls.scorer = load_scorer()

    def test_legit_whitelisted(self):
        result = self.scorer.score("https://www.obec.go.th")
        assert result["label"] == "safe"
        assert result["score"] < 0.3
        assert result["closest_domain"] == "obec.go.th"

    def test_tld_swap_typosquat_is_phishing(self):
        result = self.scorer.score("http://obec.com/verify-account")
        assert result["label"] == "phishing"
        assert result["features"]["is_typosquat"] == 1
        assert result["closest_domain"] == "obec.go.th"

    def test_ip_host_is_phishing(self):
        result = self.scorer.score("http://203.0.113.45/obec/login")
        assert result["label"] == "phishing"
        assert result["features"]["has_ip"] == 1

    def test_at_trick_is_phishing(self):
        result = self.scorer.score("http://obec.go.th@evil.xyz/login")
        assert result["label"] in ("phishing", "suspicious")

    def test_score_response_shape(self):
        result = self.scorer.score("https://example.com")
        for k in ("url", "score", "label", "reason", "features",
                  "closest_domain", "edit_distance", "checked_at"):
            assert k in result
        assert 0.0 <= result["score"] <= 1.0

    def test_legit_non_whitelisted(self):
        # google.com is not whitelisted but is unmistakably legitimate
        result = self.scorer.score("https://www.google.com")
        assert result["label"] == "safe"

    def test_punycode_reason_mentions_punycode(self):
        result = self.scorer.score("https://xn--obec-9bc.com/login")
        assert result["label"] in ("phishing", "suspicious")
        assert result["features"]["has_punycode"] == 1
        assert "Punycode" in result["reason"]

    def test_cyrillic_homoglyph_reason_mentions_mixed_script(self):
        # chulа.com with Cyrillic а should be flagged AND the reason should
        # explain WHY -- mixed-script lookalike, not just "high score".
        result = self.scorer.score("https://chulа.com/login")
        assert result["label"] in ("phishing", "suspicious")
        assert result["features"]["has_mixed_script"] == 1
        # The reason should explain the lookalike attack. Acceptable strings
        # cover: mixed-script rule ("หลายภาษา"), Punycode rule, typosquat rules
        # ("ปลอม", "คล้ายกับ"), or any explicit script name.
        reason = result["reason"]
        assert any(s in reason for s in (
            "หลายภาษา", "Cyrillic", "Punycode", "ปลอม", "คล้ายกับ",
        )), f"reason did not explain lookalike attack: {reason!r}"
