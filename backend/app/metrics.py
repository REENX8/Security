"""Prometheus metrics for the API."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Dedicated registry so test runs don't pollute the global one.
REGISTRY = CollectorRegistry()

CHECKS_TOTAL = Counter(
    "phish_checks_total",
    "Total URL checks served",
    labelnames=("label", "cached"),
    registry=REGISTRY,
)
CHECK_LATENCY = Histogram(
    "phish_check_latency_seconds",
    "Latency of /check (including feature extraction)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    registry=REGISTRY,
)
MODEL_READY = Gauge(
    "phish_model_ready",
    "1 when the model is loaded and serving",
    registry=REGISTRY,
)
CACHE_SIZE = Gauge(
    "phish_cache_size",
    "Number of URLs currently in the dedupe cache",
    registry=REGISTRY,
)


def render_metrics() -> tuple[bytes, str]:
    """Return ``(body, content_type)`` for the /metrics response."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
