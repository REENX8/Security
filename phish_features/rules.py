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
from collections.abc import Callable, Iterable
from urllib.parse import urlparse

from .schema import LOGIN_KEYWORDS, SUSPICIOUS_TLDS

Adjustment = "RuleHit"  # forward reference (resolved at runtime)


# Registrable domains that are corporate-controlled and do NOT delegate
# subdomains to untrusted users. An exact-host or true-subdomain match is
# pinned safe so legitimate brand portals (login/console/signin subdomains)
# are never blocked as phishing — including when the WHOIS/TLS signals that
# would otherwise vouch for them are unavailable (fail-open).
#
# SAFETY: only domains whose every subdomain is operator-controlled belong
# here. User-content hosts (amazonaws.com, github.io, blogspot.com,
# web.app, azurewebsites.net, *.herokuapp.com, …) are DELIBERATELY excluded —
# listing one would let an attacker host phishing on a "safe" subdomain.
KNOWN_GOOD_DOMAINS: frozenset[str] = frozenset({
    # Google
    "google.com", "youtube.com", "gmail.com", "googleapis.com",
    # Microsoft
    "microsoft.com", "microsoftonline.com", "office.com", "live.com",
    "windows.com", "bing.com", "outlook.com",
    # Apple
    "apple.com", "icloud.com",
    # Amazon (corporate domain only — NOT amazonaws.com user content)
    "amazon.com",
    # Meta
    "facebook.com", "instagram.com", "whatsapp.com",
    # Other major global services
    "netflix.com", "linkedin.com", "paypal.com", "x.com", "twitter.com",
    "github.com", "cloudflare.com", "dropbox.com", "wikipedia.org",
    "line.me",
    # Thai banks / large corporates (public brand domains)
    "scb.co.th", "kasikornbank.com", "krungsri.com", "bangkokbank.com",
    "ktb.co.th", "baac.or.th", "bot.or.th", "ttbbank.com",
    "ptt.com", "ais.co.th", "cp.co.th", "true.th",
})


def _parsed_host(url: str) -> str:
    """Lower-cased hostname with port stripped. Honours the ``@`` trick.

    ``urlparse('https://google.com@evil.xyz').hostname`` correctly returns
    ``evil.xyz`` (the real destination), so this never treats a credential-
    embedded lookalike as the trusted brand.
    """
    try:
        host = urlparse(url if "://" in (url or "") else f"http://{url}").hostname or ""
    except ValueError:
        return ""
    return host.lower().strip(".")


def rule_known_good_domain(url: str, feat: dict) -> RuleHit | None:
    """Pin safe for an exact host or true subdomain of a trusted brand domain.

    ``console.cloud.google.com`` ends with ``.google.com`` (Google-controlled),
    so it is pinned safe; ``google.com.evil.xyz`` and ``secure-google.com`` do
    NOT match (their registrable domain is the attacker's). A phishing pin from
    another rule still wins (see RulesEngine.evaluate), so this is a safety net,
    not an override of real attack indicators.
    """
    host = _parsed_host(url)
    if not host:
        return None
    for good in KNOWN_GOOD_DOMAINS:
        if host == good or host.endswith("." + good):
            return RuleHit(
                "KNOWN_GOOD_DOMAIN",
                delta=-0.60,
                pin_label="safe",
                message=(
                    f"โฮสต์เป็นโดเมนทางการของ {good} (หรือโดเมนย่อยที่แท้จริง) "
                    "ซึ่งอยู่ในรายชื่อแบรนด์ที่เชื่อถือได้"
                ),
            )
    return None


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


def rule_at_trick(url: str, feat: dict) -> RuleHit | None:
    """``https://bank.com@evil.xyz/`` -- ``@`` hides the real host."""
    if _IP_AT_RE.search(url or ""):
        return RuleHit(
            "AT_TRICK",
            delta=0.55,
            pin_label="phishing",
            message="URL ใช้อักขระ '@' เพื่อซ่อนปลายทางจริงไว้หลังเครื่องหมาย",
        )
    return None


def rule_punycode_brand_match(url: str, feat: dict) -> RuleHit | None:
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


def rule_punycode_credential(url: str, feat: dict) -> RuleHit | None:
    """IDN (punycode) host requesting credentials — homograph credential phish.

    ``rule_punycode_brand_match`` only pins when the decoded label folds within
    edit-distance 2 of a known brand. Attackers defeat that by picking a
    confusable that does NOT fold cleanly while the rendered URL still reads
    like the brand: ``xn--baangkok-o2b.go.th`` decodes to ``baangŶkok``
    (distance 9 from ``bangkok.go.th``), yet the address bar looks like Bangkok
    city government. A punycode host that also asks for credentials is an IDN
    homograph phishing setup. Mirroring ``rule_typosquat_with_login``'s
    conservatism, pin phishing only when an extra phishing signal is present
    (plain HTTP, cheap/abused TLD, or raw-IP host); otherwise raise the score
    and leave the final verdict to the model. No legitimate Thai gov/edu/bank
    host in scope uses a punycode label, so the false-positive surface is tiny.
    """
    if not (feat.get("has_punycode") and feat.get("has_login_keyword")):
        return None
    has_extra_signal = (
        not feat.get("has_https")
        or feat.get("has_suspicious_tld")
        or feat.get("has_ip")
    )
    if has_extra_signal:
        return RuleHit(
            "IDN_CRED",
            delta=0.45,
            pin_label="phishing",
            message=(
                "โฮสต์เป็นชื่อโดเมนแบบ Punycode (IDN) และ URL ขอข้อมูล login — "
                "เทคนิค IDN homograph เพื่อหลอกให้กรอกรหัสผ่านในหน้าเลียนแบบ"
            ),
        )
    return RuleHit(
        "IDN_CRED",
        delta=0.25,
        pin_label=None,
        message=(
            "โฮสต์เป็นชื่อโดเมนแบบ Punycode (IDN) และมีคำที่เกี่ยวกับ login — "
            "ตรวจสอบให้แน่ใจว่าเป็นเว็บจริงก่อนกรอกข้อมูล"
        ),
    )


def rule_typosquat_with_login(url: str, feat: dict) -> RuleHit | None:
    """Typosquat + login keyword -- a credential phishing setup.

    Hard-pins to phishing only when at least one additional phishing signal is
    present (cheap/abused TLD, plain HTTP, or raw-IP host). Without these, a
    legitimate HTTPS service whose brand name coincidentally resembles a Thai-gov
    domain (e.g. line.me ≈ life.ac.th) would be incorrectly force-classified as
    phishing. In that case we still raise the score but leave the final verdict
    to the ML model, which can weigh domain age and cert quality.
    """
    if not (feat.get("is_typosquat") and feat.get("has_login_keyword")):
        return None
    closest = feat.get("closest_domain") or "เว็บทางการ"
    has_extra_signal = (
        feat.get("has_suspicious_tld")
        or not feat.get("has_https")
        or feat.get("has_ip")
    )
    if has_extra_signal:
        return RuleHit(
            "TYPOSQUAT_CRED",
            delta=0.40,
            pin_label="phishing",
            message=(
                f"โดเมนคล้ายกับ {closest} และ URL ขอข้อมูล login/บัญชี — "
                "รูปแบบของการเก็บรหัสผ่านปลอม"
            ),
        )
    # Suspicious but not conclusive: raise score without forcing a verdict.
    return RuleHit(
        "TYPOSQUAT_CRED",
        delta=0.20,
        pin_label=None,
        message=(
            f"โดเมนคล้ายกับ {closest} และ URL มีคำที่เกี่ยวกับ login — "
            "ตรวจสอบให้แน่ใจว่าเป็นเว็บจริงก่อนกรอกข้อมูล"
        ),
    )


def rule_path_brand_impersonation(url: str, feat: dict) -> RuleHit | None:
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


def rule_ip_with_login(url: str, feat: dict) -> RuleHit | None:
    """IP host + credential keyword -- almost always phishing."""
    if feat.get("has_ip") and feat.get("has_login_keyword"):
        return RuleHit(
            "IP_CRED",
            delta=0.50,
            pin_label="phishing",
            message="URL ใช้หมายเลข IP แทนชื่อโดเมนและขอข้อมูล login",
        )
    return None


def rule_whitelisted_exact(url: str, feat: dict) -> RuleHit | None:
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


def rule_cheap_tld_no_https(url: str, feat: dict) -> RuleHit | None:
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


def rule_https_lookalike(url: str, feat: dict) -> RuleHit | None:
    """HTTPS + free cert + brand/credential signal -- modern phishing kit."""
    if (
        feat.get("has_https")
        and feat.get("cert_is_lets_encrypt")
        and (
            feat.get("is_typosquat")
            or feat.get("path_brand_hit")
            or feat.get("has_login_keyword")
        )
    ):
        return RuleHit(
            "HTTPS_LOOKALIKE",
            delta=0.30,
            pin_label="phishing",
            message=(
                "URL ใช้ HTTPS พร้อมใบรับรองฟรี (Let's Encrypt) "
                "และมีสัญญาณการปลอมแปลงแบรนด์ — "
                "รูปแบบที่พบบ่อยในชุดฟิชชิงยุคใหม่"
            ),
        )
    return None


def rule_login_keyword_dense(url: str, feat: dict) -> RuleHit | None:
    """High concentration of credential keywords raises suspicion."""
    if feat.get("num_login_keywords", 0) >= 3:
        return RuleHit(
            "LOGIN_KEYWORD_DENSE",
            delta=0.25,
            pin_label=None,
            message=(
                "URL มีคำที่เกี่ยวกับการเข้าสู่ระบบหลายคำ "
                "(เช่น login/verify/account/password) ซึ่งเป็นรูปแบบชุดฟิชชิงที่ใช้บ่อย"
            ),
        )
    return None


def rule_subdomain_camouflage(url: str, feat: dict) -> RuleHit | None:
    """Brand in subdomain chain but host is unrelated -- subdomain camouflage.

    e.g. ``www.krungthai.com.verify-now.xyz`` — the trusted brand appears as a
    subdomain label to fool visual inspection while the actual registrable domain
    is ``verify-now.xyz``.
    """
    if (
        feat.get("num_subdomains", 0) >= 2
        and feat.get("path_brand_hit") == 1
        and not feat.get("is_typosquat")
    ):
        return RuleHit(
            "SUBDOMAIN_CAMOUFLAGE",
            delta=0.35,
            pin_label="phishing",
            message=(
                "ชื่อแบรนด์ทางการปรากฏเป็น subdomain ของโดเมนที่ไม่เกี่ยวข้อง — "
                "เทคนิคที่ใช้หลอกให้ผู้ใช้เข้าใจผิดว่าเป็นเว็บจริง"
            ),
        )
    return None


def rule_encoded_ip_host(url: str, feat: dict) -> RuleHit | None:
    """Host written as a hex/octal IP literal — pure obfuscation.

    ``http://0x7f000001/`` or ``http://0177.0.0.1/`` resolve to a raw IP but
    sidestep the naive dotted-decimal IP regex (``has_ip``). There is no
    legitimate reason to address a host this way, so it is a high-precision
    phishing signal. ``has_encoded_ip`` is the v1.7.0 deterministic feature; no
    rule consumed it until now, so the model carried this alone.
    """
    if feat.get("has_encoded_ip"):
        return RuleHit(
            "ENCODED_IP_HOST",
            delta=0.45,
            pin_label="phishing",
            message=(
                "URL ใช้หมายเลข IP แบบเข้ารหัส (เลขฐานสิบหก/ฐานแปด) แทนชื่อโดเมน — "
                "เทคนิคซ่อนปลายทางจริงที่ไม่มีการใช้งานปกติ"
            ),
        )
    return None


def rule_self_signed_login(url: str, feat: dict) -> RuleHit | None:
    """Self-signed certificate on a page asking for credentials.

    A real login portal is served behind a CA-issued certificate. A
    self-signed cert collecting credentials is a near-certain phishing /
    man-in-the-middle setup, so pin to phishing.
    """
    if feat.get("is_self_signed") and feat.get("has_login_keyword"):
        return RuleHit(
            "SELF_SIGNED_CRED",
            delta=0.35,
            pin_label="phishing",
            message=(
                "หน้าเข้าสู่ระบบนี้ใช้ใบรับรอง TLS แบบ self-signed ที่ไม่น่าเชื่อถือ — "
                "เว็บทางการจะใช้ใบรับรองจากผู้ออกใบรับรองที่ตรวจสอบได้"
            ),
        )
    return None


def rule_redirect_confusion(url: str, feat: dict) -> RuleHit | None:
    """Open-redirect pattern combined with credential keyword.

    Attackers chain open-redirect endpoints on legitimate or semi-trusted
    hosts to bypass reputation checks, then land on a phishing page that
    harvests credentials.
    """
    if feat.get("path_redirect_hit") == 1 and feat.get("has_login_keyword"):
        return RuleHit(
            "REDIRECT_CONFUSION",
            delta=0.20,
            pin_label=None,
            message=(
                "URL มีรูปแบบ open-redirect และคำที่เกี่ยวกับ login — "
                "อาจถูกใช้เพื่อเปลี่ยนเส้นทางไปยังหน้าฟิชชิง"
            ),
        )
    return None


DEFAULT_RULES: tuple[Rule, ...] = (
    rule_known_good_domain,       # trusted-brand safety net (FP guard)
    rule_whitelisted_exact,       # safety net first
    rule_at_trick,
    rule_punycode_brand_match,
    rule_punycode_credential,     # IDN homograph + credential request
    rule_https_lookalike,         # HTTPS + free cert + brand/credential signal
    rule_login_keyword_dense,     # high credential-keyword density
    rule_typosquat_with_login,
    rule_path_brand_impersonation,
    rule_subdomain_camouflage,
    rule_redirect_confusion,
    rule_encoded_ip_host,         # hex/octal IP literal host
    rule_ip_with_login,
    rule_self_signed_login,       # self-signed cert + credential keyword
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
    "rule_punycode_credential",
    "rule_https_lookalike",
    "rule_login_keyword_dense",
    "rule_subdomain_camouflage",
    "rule_redirect_confusion",
    "rule_encoded_ip_host",
    "rule_self_signed_login",
    "rule_known_good_domain",
    "KNOWN_GOOD_DOMAINS",
]
