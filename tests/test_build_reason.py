"""Unit tests for _build_reason() in app.ml.scorer and _post_sync() in app.notifier.

All offline — no network I/O, no model loading.
"""
from __future__ import annotations

import os
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.ml.scorer import _build_reason  # noqa: E402
from app.notifier import _post_sync  # noqa: E402

# ============================================================
# _build_reason — covers lines 32-34, 42-49, 60-67, 72, 74, 79, 81
# ============================================================

class TestBuildReason:
    def test_whitelisted_returns_trusted_message(self):
        result = _build_reason({}, "safe", is_whitelisted=True)
        assert "เชื่อถือได้" in result

    def test_safe_label_returns_no_risk_message(self):
        result = _build_reason({}, "safe", is_whitelisted=False)
        assert "ไม่พบ" in result

    def test_typosquat_with_closest_domain(self):
        feat = {
            "is_typosquat": 1,
            "closest_domain": "krungthai.com",
            "min_edit_distance": 1,
        }
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "krungthai.com" in result
        assert "คล้ายกับ" in result

    def test_typosquat_without_closest_domain(self):
        feat = {"is_typosquat": 1, "min_edit_distance": 2}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        # Reason still mentions "คล้ายกับ" even with closest=None
        assert "คล้ายกับ" in result

    def test_punycode_with_closest_domain(self):
        feat = {"has_punycode": 1, "closest_domain": "obec.go.th"}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "Punycode" in result
        assert "obec.go.th" in result

    def test_punycode_without_closest_domain(self):
        feat = {"has_punycode": 1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "Punycode" in result

    def test_mixed_script_with_closest_domain(self):
        # homoglyph_distance < min_edit_distance triggers mixed-script branch
        feat = {
            "has_mixed_script": 1,
            "homoglyph_distance": 1,
            "min_edit_distance": 3,
            "closest_domain": "bbl.co.th",
        }
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "หลายภาษา" in result
        assert "bbl.co.th" in result

    def test_mixed_script_without_closest_domain(self):
        feat = {
            "has_mixed_script": 1,
            "homoglyph_distance": 1,
            "min_edit_distance": 5,
        }
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "หลายภาษา" in result

    def test_mixed_script_not_flagged_when_edit_distance_lower(self):
        # mixed_script only flagged when homoglyph_distance < min_edit_distance
        feat = {
            "has_mixed_script": 1,
            "homoglyph_distance": 5,
            "min_edit_distance": 2,
        }
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        # Should not contain "หลายภาษา" since condition is not met
        assert "หลายภาษา" not in result

    def test_ip_in_url(self):
        feat = {"has_ip": 1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "IP" in result

    def test_at_sign_in_url(self):
        feat = {"num_at": 1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "@" in result

    def test_new_domain(self):
        feat = {"domain_age_days": 30}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "30" in result
        assert "จดทะเบียน" in result

    def test_domain_age_zero(self):
        feat = {"domain_age_days": 0}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "จดทะเบียน" in result

    def test_domain_age_exactly_90_not_flagged(self):
        feat = {"domain_age_days": 90}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "จดทะเบียน" not in result

    def test_domain_age_negative_not_flagged(self):
        feat = {"domain_age_days": -1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "จดทะเบียน" not in result

    def test_self_signed_cert(self):
        feat = {"is_self_signed": 1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "self-signed" in result

    def test_no_signals_returns_ml_fallback(self):
        # has_https=1 prevents the "no HTTPS" branch; everything else absent
        feat = {"has_https": 1}
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        assert "แบบจำลอง" in result

    def test_multiple_signals_truncated_to_three(self):
        feat = {
            "is_typosquat": 1, "closest_domain": "a.com", "min_edit_distance": 1,
            "has_ip": 1,
            "num_at": 2,
            "domain_age_days": 5,
            "is_self_signed": 1,
        }
        result = _build_reason(feat, "phishing", is_whitelisted=False)
        # At most 3 reasons joined by " · "
        assert result.count("·") <= 2


# ============================================================
# _post_sync — covers lines 61-93 in notifier.py
# ============================================================

class TestPostSync:
    def test_json_post_success(self):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        with patch("urllib.request.urlopen", return_value=mock_resp):
            status, err = _post_sync("https://hook.example/test", {"key": "val"})
        assert status == 200
        assert err is None

    def test_http_error_returns_code_and_reason(self):
        exc = urllib.error.HTTPError(
            url="https://hook.example", code=500,
            msg="Internal Server Error", hdrs=None, fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            status, err = _post_sync("https://hook.example/test", {"key": "val"})
        assert status == 500
        assert err == "Internal Server Error"

    def test_network_error_returns_none_and_message(self):
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            status, err = _post_sync("https://hook.example/test", {"key": "val"})
        assert status is None
        assert "connection refused" in err

    def test_line_notify_uses_form_encoding(self):
        called_with = {}

        def capture_urlopen(req, timeout=None):
            called_with["body"] = req.data
            called_with["ct"] = req.get_header("Content-type")
            mock_resp = MagicMock()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.status = 200
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            status, err = _post_sync(
                "https://notify-api.line.me/api/notify",
                {"brand": "krungthai", "url": "http://x", "score": 0.9},
            )
        assert status == 200
        assert b"message=" in called_with["body"]
        assert "form-urlencoded" in called_with["ct"]

    def test_line_notify_bearer_token_extracted(self):
        captured_headers = {}

        def capture_urlopen(req, timeout=None):
            captured_headers.update(dict(req.headers.items()))
            mock_resp = MagicMock()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.status = 200
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            _post_sync(
                "https://notify-api.line.me/api/notify#token=mytoken123",
                {"brand": "test", "url": "http://x", "score": 0.5},
            )
        assert "Authorization" in captured_headers
        assert "mytoken123" in captured_headers["Authorization"]
