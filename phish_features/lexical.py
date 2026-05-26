"""Lexical URL features.

These are computed purely from the URL string -- no network, fully
deterministic, identical at training and serving time.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from urllib.parse import urlparse

_DIGIT_RUN_RE = re.compile(r"\d+")

# IPv4 literal, optionally with a port.
_IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?$")
# Bracketed IPv6 literal, e.g. [2001:db8::1]
_IPV6_RE = re.compile(r"^\[[0-9a-fA-F:]+\](?::\d+)?$")

# Public suffixes we treat as multi-label (so num_subdomains is meaningful).
_MULTI_LABEL_SUFFIXES = (
    "go.th",
    "ac.th",
    "or.th",
    "co.th",
    "in.th",
    "mi.th",
    "net.th",
    "com.au",
    "co.uk",
    "org.uk",
    "ac.uk",
)


def normalize_url(url: str) -> str:
    """Trim whitespace and supply a scheme so urlparse behaves predictably."""
    url = (url or "").strip()
    if url and "://" not in url:
        url = "http://" + url
    return url


def get_host(url: str) -> str:
    """Return the lower-cased hostname (no port, no userinfo)."""
    parsed = urlparse(normalize_url(url))
    host = parsed.hostname or ""
    return host.lower()


def shannon_entropy(text: str) -> float:
    """Shannon entropy (bits per character) of the string."""
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def host_is_ip(host: str) -> bool:
    """True when the host is an IPv4/IPv6 literal rather than a domain."""
    if not host:
        return False
    if _IPV4_RE.match(host):
        parts = host.split(":")[0].split(".")
        return all(0 <= int(p) <= 255 for p in parts)
    return bool(_IPV6_RE.match(host)) or (":" in host and host.replace(":", "").isalnum())


def registrable_suffix_len(host: str) -> int:
    """Number of labels that make up the public suffix + registrable domain.

    e.g. ``obec.go.th`` -> registrable is ``obec.go.th`` (3 labels);
    ``example.com`` -> 2 labels.
    """
    h = host.lower()
    for suffix in _MULTI_LABEL_SUFFIXES:
        if h == suffix or h.endswith("." + suffix):
            return suffix.count(".") + 2
    return 2


def count_subdomains(host: str) -> int:
    """Depth of subdomains in front of the registrable domain."""
    if not host or host_is_ip(host):
        return 0
    labels = [l for l in host.split(".") if l]
    extra = len(labels) - registrable_suffix_len(host)
    return max(extra, 0)


def extract_lexical(url: str) -> dict:
    """Return the lexical feature block for ``url``."""
    norm = normalize_url(url)
    parsed = urlparse(norm)
    host = (parsed.hostname or "").lower()

    host_labels = [lb for lb in host.split(".") if lb]
    path_parts = [p for p in parsed.path.split("/") if p]
    digit_runs = _DIGIT_RUN_RE.findall(host)

    return {
        "url_length": len(norm),
        "num_dots": norm.count("."),
        "num_hyphens": norm.count("-"),
        "num_at": norm.count("@"),
        "num_slash": norm.count("/"),
        "num_digits": sum(ch.isdigit() for ch in norm),
        "has_ip": int(host_is_ip(host)),
        "entropy": round(shannon_entropy(norm), 6),
        "has_https": int(parsed.scheme == "https"),
        "num_subdomains": count_subdomains(host),
        # v1.1 features
        "path_depth": len(path_parts),
        "domain_label_max_len": max((len(lb) for lb in host_labels), default=0),
        "has_port": int(
            parsed.port is not None and parsed.port not in (80, 443)
        ),
        "max_digit_run": max((len(r) for r in digit_runs), default=0),
        "has_query_string": int(bool(parsed.query)),
        # v1.3 features (path-impersonation surface; tld decided by extractor)
        "path_length": len(parsed.path or ""),
    }
