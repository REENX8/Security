# Load testing (A9)

Two equivalent load tests that assert the documented **p95 < 250 ms** SLO for
`POST /api/v1/check`. Run them against a **staging** deployment — never
production data.

## k6 (recommended for CI/scripted runs)

```bash
k6 run -e HOST=https://staging.example.com -e API_KEY=$KEY deploy/loadtest/k6_check.js
```

The run **fails** if `p(95) >= 250ms` or the error rate exceeds 1% (see the
`thresholds` block), so it can gate a release.

## Locust (interactive / exploratory)

```bash
pip install locust
locust -f deploy/loadtest/locustfile.py --host https://staging.example.com
# headless:
locust -f deploy/loadtest/locustfile.py --host https://$HOST --headless -u 200 -r 20 -t 2m --csv loadtest
```

## Notes

- ~30% of requests use a cache-busting query so the test exercises real scoring,
  not just cache hits. Tune this to match expected production cache locality.
- Set `API_KEY` for parity with extension/CLI traffic (rate limits are per key).
- Watch `/metrics` (`phish_check_latency_seconds`) and the Grafana panel during
  the run to correlate the client-side p95 with server-side latency.
