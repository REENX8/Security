"""Whitelist of trusted Thai domains + typosquat detection.

The whitelist is the anchor for the most powerful signal in the system:
how close (in edit distance) a URL's registrable domain is to a known-good
Thai government / education domain.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field

from .homoglyph import decode_idn, fold_confusables

# Prefer the fast C-backed library; fall back to a pure-Python implementation
# so the package never hard-fails on install issues.
try:  # pragma: no cover - exercised by environment
    from Levenshtein import distance as _lev_distance

    _HAVE_LEVENSHTEIN = True
except Exception:  # pragma: no cover
    _HAVE_LEVENSHTEIN = False

    def _lev_distance(a: str, b: str) -> int:
        """Pure-Python Levenshtein edit distance (fallback)."""
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(
                    min(
                        prev[j] + 1,
                        cur[j - 1] + 1,
                        prev[j - 1] + (ca != cb),
                    )
                )
            prev = cur
        return prev[-1]


# Distance <= this (and not an exact match) is flagged as a typosquat.
TYPOSQUAT_MAX_DISTANCE = 3

_MULTI_LABEL_SUFFIXES = (
    "go.th",
    "ac.th",
    "or.th",
    "co.th",
    "in.th",
    "mi.th",
    "net.th",
)


def registrable_domain(host: str) -> str:
    """Collapse a host down to its registrable domain.

    ``www.school.obec.go.th`` -> ``obec.go.th``
    ``mail.example.com``      -> ``example.com``
    """
    h = (host or "").lower().strip(".")
    if not h:
        return ""
    for suffix in _MULTI_LABEL_SUFFIXES:
        if h == suffix:
            return h
        if h.endswith("." + suffix):
            head = h[: -(len(suffix) + 1)]
            label = head.split(".")[-1]
            return f"{label}.{suffix}" if label else h
    labels = h.split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else h


@dataclass
class WhitelistEntry:
    domain: str
    agency_name: str = ""
    category: str = "other"


def brand_label(host: str) -> str:
    """The meaningful first label of a registrable domain.

    ``obec.go.th`` -> ``obec`` ; ``mail.chula.ac.th`` -> ``chula``.
    This is what attackers mutate, so typosquat distance is measured on it.
    """
    reg = registrable_domain(host)
    return reg.split(".")[0] if reg else ""


@dataclass
class Whitelist:
    """An immutable, sorted set of trusted domains."""

    entries: list[WhitelistEntry] = field(default_factory=list)
    _domains: list[str] = field(default_factory=list, repr=False)
    _exact: set[str] = field(default_factory=set, repr=False)
    _meta: dict[str, WhitelistEntry] = field(default_factory=dict, repr=False)
    _labels: list[str] = field(default_factory=list, repr=False)

    # ----- construction -------------------------------------------------
    @classmethod
    def from_entries(cls, entries: list[WhitelistEntry]) -> "Whitelist":
        # Deduplicate by domain, keep deterministic sorted order.
        by_domain: dict[str, WhitelistEntry] = {}
        for e in entries:
            dom = registrable_domain(e.domain) or e.domain.lower()
            by_domain.setdefault(
                dom, WhitelistEntry(dom, e.agency_name, e.category)
            )
        ordered = [by_domain[d] for d in sorted(by_domain)]
        wl = cls(entries=ordered)
        wl._domains = [e.domain for e in ordered]
        wl._exact = set(wl._domains)
        wl._meta = {e.domain: e for e in ordered}
        wl._labels = [brand_label(d) for d in wl._domains]
        return wl

    @classmethod
    def from_csv(cls, path: str) -> "Whitelist":
        rows: list[WhitelistEntry] = []
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                domain = (row.get("domain") or "").strip().lower()
                if not domain or domain.startswith("#"):
                    continue
                rows.append(
                    WhitelistEntry(
                        domain=domain,
                        agency_name=(row.get("agency_name") or "").strip(),
                        category=(row.get("category") or "other").strip(),
                    )
                )
        return cls.from_entries(rows)

    @classmethod
    def from_json(cls, path: str) -> "Whitelist":
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        rows = [
            WhitelistEntry(
                domain=item["domain"],
                agency_name=item.get("agency_name", ""),
                category=item.get("category", "other"),
            )
            for item in payload.get("entries", [])
        ]
        return cls.from_entries(rows)

    def to_json(self, path: str) -> None:
        payload = {
            "count": len(self.entries),
            "entries": [
                {
                    "domain": e.domain,
                    "agency_name": e.agency_name,
                    "category": e.category,
                }
                for e in self.entries
            ],
        }
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    # ----- queries ------------------------------------------------------
    @property
    def domains(self) -> list[str]:
        return list(self._domains)

    def is_whitelisted(self, host: str) -> bool:
        return registrable_domain(host) in self._exact

    def get_entry(self, domain: str) -> WhitelistEntry | None:
        return self._meta.get(domain)

    def closest(self, host: str) -> tuple[int, str | None]:
        """Return ``(min_edit_distance, closest_domain)`` for ``host``.

        Distance is measured between *brand labels* (the first label of the
        registrable domain) so that TLD-swap impersonations such as
        ``obec.com`` vs ``obec.go.th`` are caught -- a plain registrable-domain
        comparison would miss them.
        """
        target = brand_label(host)
        if not target or not self._labels:
            return (999, None)
        best_dist = 999
        best_dom: str | None = None
        for label, dom in zip(self._labels, self._domains):
            d = _lev_distance(target, label)
            if d < best_dist:
                best_dist, best_dom = d, dom
                if d == 0:
                    break
        return (best_dist, best_dom)

    def closest_normalized(self, host: str) -> tuple[int, str | None]:
        """Closest brand-label distance AFTER Punycode decode + confusable fold.

        Catches IDN homograph attacks (``chulа.com`` with Cyrillic ``а``,
        ``xn--chla-zxa.com``) that ``closest()`` misses because the raw
        label compares against the whitelist in ASCII space.
        """
        decoded = decode_idn(host)
        normalized_label = fold_confusables(brand_label(decoded))
        if not normalized_label or not self._labels:
            return (999, None)
        best_dist = 999
        best_dom: str | None = None
        for label, dom in zip(self._labels, self._domains):
            d = _lev_distance(normalized_label, label)
            if d < best_dist:
                best_dist, best_dom = d, dom
                if d == 0:
                    break
        return (best_dist, best_dom)

    def whitelist_features(self, host: str) -> dict:
        """Return the whitelist feature block for ``host``.

        An exact whitelist domain is never a typosquat. A non-whitelisted host
        whose brand label is within ``TYPOSQUAT_MAX_DISTANCE`` edits of a
        trusted brand (including distance 0, i.e. a TLD swap) is flagged.
        """
        distance, closest = self.closest(host)
        is_exact = self.is_whitelisted(host)
        if is_exact:
            distance = 0
        # A non-trusted host is a typosquat when its brand label either
        # exactly matches a trusted brand on the wrong TLD (distance 0), or
        # is a near-miss of one. Distance-based matches require a label of
        # >= 4 characters -- short labels (e.g. "scb") collide by chance.
        label_len = len(brand_label(host))
        is_typo = (not is_exact) and (
            distance == 0
            or (1 <= distance <= TYPOSQUAT_MAX_DISTANCE and label_len >= 4)
        )
        return {
            "min_edit_distance": int(distance),
            "closest_domain": closest,
            "is_typosquat": int(is_typo),
        }
