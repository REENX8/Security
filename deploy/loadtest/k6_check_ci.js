// k6 load test for /check — CI profile.
//
//   k6 run -e HOST=http://127.0.0.1:8000 -e API_KEY=ci-key deploy/loadtest/k6_check_ci.js
//
// This is the gate that runs inside GitHub Actions (see the `loadtest-e2e` job).
// It is DELIBERATELY looser than the staging SLO in k6_check.js: a cold,
// shared GitHub-hosted runner doing sklearn inference with no warm cache cannot
// hit the production p95<250ms target, and asserting it would flake the build.
// This profile uses a small fixed load + a generous p95 so it still catches a
// gross latency regression (e.g. a 10x blow-up) without false failures. Tighten
// LOADTEST_P95_MS once it proves stable on CI. The authoritative staging SLO
// stays in k6_check.js.
import http from "k6/http";
import { check, sleep } from "k6";

const HOST = __ENV.HOST || "http://127.0.0.1:8000";
const API_KEY = __ENV.API_KEY || "";
const P95_MS = __ENV.LOADTEST_P95_MS || "1500";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: [`p(95)<${P95_MS}`],
    http_req_failed: ["rate<0.05"],
  },
};

const URLS = [
  "https://www.obec.go.th",
  "https://chula.ac.th",
  "http://obec-verify.xyz/login",
  "http://krungthai-secure.top/account",
];

export default function () {
  const url = URLS[Math.floor(Math.random() * URLS.length)];
  // Always cache-bust so we measure real scoring latency, not cache hits.
  const bust = `?n=${Math.floor(Math.random() * 1e6)}`;
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = http.post(
    `${HOST}/api/v1/check`,
    JSON.stringify({ url: url + bust }),
    { headers, tags: { name: "check" } },
  );
  check(res, {
    "status 200": (r) => r.status === 200,
    "has label": (r) => r.body && r.body.includes("label"),
  });
  sleep(Math.random() * 0.5);
}
