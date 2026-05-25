"""Homoglyph / IDN normalisation utilities.

Phishers targeting Thai government and education brands often substitute
visually-identical characters from other Unicode scripts (Cyrillic, Greek,
fullwidth Latin) into the registered domain label, or encode the lookalike
domain as Punycode (``xn--...``). The lexical and edit-distance signals can
miss these attacks because the raw ASCII representation does not match a
known brand.

This module:

  * Decodes Punycode hostnames back to their Unicode form so confusable
    detection works on what the user actually sees.
  * Folds a curated set of Latin-confusable characters back to ASCII so
    the whitelist edit-distance comparison catches near-matches.
  * Detects mixed Unicode scripts inside a single domain label -- a strong
    signal of intentional homograph spoofing.

The mapping is deliberately small. It covers the ~30 substitutions that
appear repeatedly in IDN homograph reports (Unicode TR36, Chromium IDN
policy) and that show up in real attacks against Thai brands. Adding more
mappings risks normalising legitimate non-ASCII domains.
"""

from __future__ import annotations

import unicodedata

# Confusable -> ASCII fold. Conservative subset of Unicode confusables
# (the ones documented as commonly abused for homograph attacks).
CONFUSABLE_FOLD: dict[str, str] = {
    # Cyrillic letters that look identical to Latin lowercase
    "а": "a",  # CYRILLIC SMALL LETTER A
    "е": "e",  # CYRILLIC SMALL LETTER IE
    "о": "o",  # CYRILLIC SMALL LETTER O
    "р": "p",  # CYRILLIC SMALL LETTER ER
    "с": "c",  # CYRILLIC SMALL LETTER ES
    "х": "x",  # CYRILLIC SMALL LETTER HA
    "у": "y",  # CYRILLIC SMALL LETTER U
    "і": "i",  # CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
    "ј": "j",  # CYRILLIC SMALL LETTER JE
    "һ": "h",  # CYRILLIC SMALL LETTER SHHA
    "ӏ": "l",  # CYRILLIC SMALL LETTER PALOCHKA
    "ԁ": "d",  # CYRILLIC SMALL LETTER KOMI DE
    "ԛ": "q",  # CYRILLIC SMALL LETTER QA
    "ԝ": "w",  # CYRILLIC SMALL LETTER WE
    "ѕ": "s",  # CYRILLIC SMALL LETTER DZE
    "ѡ": "w",  # CYRILLIC SMALL LETTER OMEGA
    # Greek letters that look like Latin
    "ο": "o",  # GREEK SMALL LETTER OMICRON
    "α": "a",  # GREEK SMALL LETTER ALPHA
    "ρ": "p",  # GREEK SMALL LETTER RHO
    "υ": "u",  # GREEK SMALL LETTER UPSILON
    "ι": "i",  # GREEK SMALL LETTER IOTA
    "κ": "k",  # GREEK SMALL LETTER KAPPA
    "ν": "v",  # GREEK SMALL LETTER NU
    "χ": "x",  # GREEK SMALL LETTER CHI
    # Fullwidth Latin (used in some Asian-locale phish kits)
    "ａ": "a", "ｂ": "b", "ｃ": "c", "ｄ": "d",
    "ｅ": "e", "ｆ": "f", "ｇ": "g", "ｈ": "h",
    "ｉ": "i", "ｊ": "j", "ｋ": "k", "ｌ": "l",
    "ｍ": "m", "ｎ": "n", "ｏ": "o", "ｐ": "p",
    "ｑ": "q", "ｒ": "r", "ｓ": "s", "ｔ": "t",
    "ｕ": "u", "ｖ": "v", "ｗ": "w", "ｘ": "x",
    "ｙ": "y", "ｚ": "z",
    # Digits often substituted for letters
    "๑": "1",  # THAI DIGIT ONE (rare but seen in shortened links)
    "๐": "0",  # THAI DIGIT ZERO
}


def decode_idn(host: str) -> str:
    """Decode an IDN host (``xn--...``) to its Unicode form.

    Returns the original host unchanged if it does not contain Punycode
    labels or if decoding fails. The decoded form is what the user sees in
    a modern browser address bar -- which is exactly the surface attackers
    are exploiting.
    """
    if not host or "xn--" not in host.lower():
        return host
    out: list[str] = []
    for label in host.split("."):
        if label.lower().startswith("xn--"):
            try:
                out.append(label.encode("ascii").decode("idna"))
            except Exception:  # noqa: BLE001
                out.append(label)
        else:
            out.append(label)
    return ".".join(out)


def fold_confusables(text: str) -> str:
    """Map confusable Unicode characters to their ASCII lookalike.

    Also strips Unicode combining marks (NFKD then drop combining) so
    accented look-alikes like ``ć`` collapse to ``c``.
    """
    if not text:
        return text
    # Stage 1: NFKD decompose, then drop combining marks (handles a→a).
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    # Stage 2: explicit confusable fold for letters that do not decompose.
    return "".join(CONFUSABLE_FOLD.get(ch, ch) for ch in stripped).lower()


def _script_of(ch: str) -> str | None:
    """Return a coarse script tag for a single character, or None for ASCII/digits/punct."""
    cp = ord(ch)
    # Skip ASCII letters, digits, hyphen -- these are the baseline of all hostnames.
    if cp < 0x80:
        return None
    try:
        name = unicodedata.name(ch, "")
    except ValueError:
        return None
    if name.startswith("CYRILLIC"):
        return "Cyrillic"
    if name.startswith("GREEK"):
        return "Greek"
    if name.startswith("LATIN"):
        return "Latin"  # extended Latin (e.g. ć, ñ)
    if name.startswith("ARABIC"):
        return "Arabic"
    if name.startswith("HEBREW"):
        return "Hebrew"
    if name.startswith("THAI"):
        return "Thai"
    if "FULLWIDTH" in name:
        return "Fullwidth"
    if name.startswith("CJK") or name.startswith("HIRAGANA") or name.startswith("KATAKANA"):
        return "CJK"
    return "Other"


def has_mixed_script(host: str) -> bool:
    """True if any domain label mixes Unicode scripts in a suspicious way.

    A label is "mixed" when it contains characters from a non-ASCII script
    alongside ASCII letters (``chulа`` = Latin c-h-u-l + Cyrillic а), or
    contains characters from two non-ASCII scripts at once.
    """
    if not host:
        return False
    decoded = decode_idn(host)
    for label in decoded.split("."):
        if not label:
            continue
        has_ascii_letter = any("a" <= ch.lower() <= "z" for ch in label if ord(ch) < 0x80)
        scripts = {s for s in (_script_of(ch) for ch in label) if s}
        if has_ascii_letter and scripts:
            return True
        if len(scripts) > 1:
            return True
    return False


def has_punycode(host: str) -> bool:
    """True if any label of the host is Punycode-encoded."""
    if not host:
        return False
    return any(label.lower().startswith("xn--") for label in host.split("."))


def normalize_for_lookup(host: str) -> str:
    """Apply IDN decode + confusable fold for whitelist comparison."""
    return fold_confusables(decode_idn(host))
