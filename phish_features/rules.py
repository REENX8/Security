"""Heuristic Rules Engine -- a transparent layer on top of the ML scorer.

ML gives us a calibrated probability and an explanation built from the
strongest individual features. A rules engine adds three things ML can't
on its own:

1. **Auditability.** Every rule has a stable id, a description and a
   visible score adjustment. When a verdict gets contested ("why was my
   site flagged?") the operator can point to the exact rules that fired
   instead of a feature importance plot.
2. **Operator override.** Rules can pin a verdict (eg. force-safe for
   on-the-fence whitelisted hosts, force-phishing for newly observed
   campaign hosts) without retraining the model.
3. **Fast iteration.** New phishing patterns can be deployed in minutes
   by adding a rule instead of waiting for the next training cycle.

The engine is intentionally tiny -- there's no DSL parser, no priorities,
no compile step. Rules are plain Python callables registered in a list,
applied in order, each returning an ``Adjustment`` or ``None``. The
scoring pipeline collects every adjustment, sums them clamped to [0, 1]
and returns the trail so the API can show what fired.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable
from typing import Iterable

from .schema import LOGIN_KEYWORDS, SUSPICIOUS_TLDS

Adjustment = "RuleHit"  # forward reference (resolved at runtime)


@dataclasses.dataclass(frozen=True)
class RuleHit:
    """A single rule firing on a URL/feature combination."""

    rule_id: str
    delta: float            # score delta in [-1.0, +1.0]; positive = more phishy
    pin_label: str | None   # 'safe' | 'phishing' | None to leave to score math
    message: str            # short Thai/English explanation surfaced via API


# A rule is a function (url, features) -> RuleHit | None.
Rule = Callable[[str, dict], "RuleHit | None"]


# ---------------------------------------------------------------------------
# Built-in rules
# ---------------------------------------------------------------------------

_IP_AT_RE = re.compile(r"://[^/]*@")


def rule_at_trick(url: str, feat: dict) -> "RuleHit | None":
    """``https://bank.com@evil.xyz/`` -- ``@`` hides the real host."""
    if _IP_AT_RE.search(url or ""):
        return RuleHit(
            "AT_TRICK",
            delta=0.55,
            pin_label="phishing",
            message="URL ใช้อักขระ '@' เพื่อซ่อนปลายทางจริงไว้หลังเครื่องหมาย",
        )
    return None


def rule_punycode_brand_match(url: str, feat: dict) -> "RuleHit | None":
    """Punycode + close to a trusted brand: high-confidence IDN spoof."""
    if feat.get("has_punycode") and feat.get("homoglyph_distance", 999) <= 2:
        return RuleHit(
            "IDN_HOMOGRAPH",
            delta=0.45,
            pin_label="phishing",
            message=(
                "URL ถูก encode เป็น Punycode และ decode แล้วใกล้กับชื่อแบรนด์จริง — "
                "เทคนิคนี้ทำให้ผู้ใช้เห็น URL เหมือนของจริงในแถบที่อยู่"
            ),
        )
    return None


def rule_typosquat_with_login(url: str, feat: dict) -> "RuleHit | None":
    """Typosquat + login keyword -- a credential phishing setup."""
    if feat.get("is_typosquat") and feat.get("has_login_keyword"):
        closest = feat.get("closest_domain") or "เว็บทางการ"
        return RuleHit(
            "TYPOSQUAT_CRED",
            delta=0.40,
            pin_label="phishing",
            message=(
                f"โดเมนคล้ายกับ {closest} และ URL ขอข้อมูล login/บัญชี — "
                "รูปแบบของการเก็บรหัสผ่านปลอม"
            ),
        )
    return None


def rule_path_brand_impersonation(url: str, feat: dict) -> "RuleHit | None":
    """Trusted brand sits in URL path but not in host -- a brand-bait kit."""
    if feat.get("path_brand_hit") and feat.get("has_suspicious_tld"):
        closest = feat.get("closest_domain") or ""
        suffix = f" ({closest})" if closest else ""
        return RuleHit(
            "PATH_BRAND_BAIT",
            delta=0.30,
            pin_label="phishing",
            message=(
                f"ชื่อแบรนด์ทางการ{suffix} ปรากฏใน path ของ URL "
                "ขณะที่ host ใช้ TLD ราคาถูก ซึ่งเป็นรูปแบบฟิชชิงที่พบบ่อย"
            ),
        )
    return None


def rule_ip_with_login(url: str, feat: dict) -> "RuleHit | None":
    """IP host + credential keyword -- almost always phishing."""
    if feat.get("has_ip") and feat.get("has_login_keyword"):
        return RuleHit(
            "IP_CRED",
            delta=0.50,
            pin_label="phishing",
            message="URL ใช้หมายเลข IP แทนชื่อโดเมนและขอข้อมูล login",
        )
    return None


def rule_whitelisted_exact(url: str, feat: dict) -> "RuleHit | None":
    """Exact whitelist match should never be phishing.

    A safety net against false positives when other signals (eg. an
    unusually long path on a real gov portal) accidentally trip the model.
    """
    if (
        feat.get("min_edit_distance") == 0
        and not feat.get("is_typosquat")
        and not feat.get("has_ip")
        and not feat.get("has_punycode")
    ):
        return RuleHit(
            "WHITELIST_EXACT",
            delta=-0.60,
            pin_label="safe",
            message="โดเมนตรงกับรายการ whitelist หน่วยงานที่เชื่อถือได้",
        )
    return None


def rule_cheap_tld_no_https(url: str, feat: dict) -> "RuleHit | None":
    """Cheap TLD without HTTPS -- low-effort phishing kit."""
    if (
        feat.get("has_suspicious_tld")
        and not feat.get("has_https")
        and not feat.get("has_ip")
    ):
        return RuleHit(
            "CHEAP_TLD_PLAIN",
            delta=0.20,
            pin_label=None,
            message="โดเมนใช้ TLD ที่ถูกใช้ปลอมบ่อยและไม่มี HTTPS",
        )
    return None


DEFAULT_RULES: tuple[Rule, ...] = (
    rule_whitelisted_exact,       # safety net first
    rule_at_trick,
    rule_punycode_brand_match,
    rule_typosquat_with_login,
    rule_path_brand_impersonation,
    rule_ip_with_login,
    rule_cheap_tld_no_https,
)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class RulesResult:
    """Outcome of running the engine over one (url, features) pair."""

    hits: list[RuleHit]
    score_delta: float
    pinned_label: str | None  # 'safe' | 'phishing' | None

    def applied_ids(self) -> list[str]:
        return [h.rule_id for h in self.hits]

    def to_dict(self) -> dict:
        return {
            "score_delta": round(self.score_delta, 4),
            "pinned_label": self.pinned_label,
            "hits": [
                {
                    "rule_id": h.rule_id,
                    "delta": round(h.delta, 4),
                    "pin_label": h.pin_label,
                    "message": h.message,
                }
                for h in self.hits
            ],
        }


class RulesEngine:
    """Apply a list of rules to a (url, feature) pair."""

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self.rules: list[Rule] = list(rules) if rules is not None else list(DEFAULT_RULES)

    def add(self, rule: Rule) -> None:
        self.rules.append(rule)

    def evaluate(self, url: str, features: dict) -> RulesResult:
        hits: list[RuleHit] = []
        delta_total = 0.0
        pinned: str | None = None
        for rule in self.rules:
            hit = rule(url, features)
            if hit is None:
                continue
            hits.append(hit)
            delta_total += hit.delta
            # Phishing pin wins over safe pin -- a real attack indicator
            # should never be silently overruled by a "looks legit" rule.
            if hit.pin_label == "phishing":
                pinned = "phishing"
            elif hit.pin_label == "safe" and pinned != "phishing":
                pinned = "safe"
        return RulesResult(
            hits=hits,
            score_delta=max(-1.0, min(1.0, delta_total)),
            pinned_label=pinned,
        )


__all__ = [
    "RuleHit",
    "RulesEngine",
    "RulesResult",
    "DEFAULT_RULES",
    "LOGIN_KEYWORDS",
    "SUSPICIOUS_TLDS",
]
