"""phish_features -- shared feature-extraction contract.

Imported by BOTH the ML training pipeline and the FastAPI backend so the
model never sees train/serve skew.
"""

from .extractor import FeatureExtractor, classify_tld, extract_features
from .homoglyph import (
    decode_idn,
    fold_confusables,
    has_mixed_script,
    has_punycode,
    normalize_for_lookup,
)
from .lexical import get_host, normalize_url, shannon_entropy
from .schema import (
    FEATURE_SCHEMA_VERSION,
    IMPUTED_DEFAULTS,
    N_FEATURES,
    ORDERED_FEATURES,
    TLD_TYPE_MAP,
    vector_from_dict,
)
from .whitelist import (
    TYPOSQUAT_MAX_DISTANCE,
    Whitelist,
    WhitelistEntry,
    registrable_domain,
)

__version__ = "1.0.0"

__all__ = [
    "FeatureExtractor",
    "FEATURE_SCHEMA_VERSION",
    "IMPUTED_DEFAULTS",
    "N_FEATURES",
    "ORDERED_FEATURES",
    "TLD_TYPE_MAP",
    "TYPOSQUAT_MAX_DISTANCE",
    "Whitelist",
    "WhitelistEntry",
    "classify_tld",
    "decode_idn",
    "extract_features",
    "fold_confusables",
    "get_host",
    "has_mixed_script",
    "has_punycode",
    "normalize_for_lookup",
    "normalize_url",
    "registrable_domain",
    "shannon_entropy",
    "vector_from_dict",
]
