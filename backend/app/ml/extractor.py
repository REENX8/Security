"""Thin adapter over the shared ``phish_features`` package.

There is intentionally NO feature math here -- the backend extracts features
with the exact same code the training pipeline used.
"""

from __future__ import annotations

from phish_features import FeatureExtractor, Whitelist

from app.config import settings


def build_extractor() -> FeatureExtractor:
    """Construct the FeatureExtractor used for serving."""
    whitelist = Whitelist.from_json(settings.whitelist_path)
    return FeatureExtractor(
        whitelist,
        enable_whois=settings.enable_whois,
        enable_tls=settings.enable_tls,
        network_timeout=settings.network_timeout,
    )
