// k6 load test for /check (A9). Validates the p95 < 250 ms SLO.
//
//   k6 run -e HOST=https://staging.example.com -e API_KEY=xxx deploy/loadtest/k6_check.js
//
// Run against STAGING only.
import http from "k6/http";
import { check, sleep } from "k6";

const HOST = __ENV.HOST || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "";

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "1m", target: 200 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    // The documented SLO: 95% of /check requests under 250 ms.
    http_req_duration: ["p(95)<250"],
    http_req_failed: ["rate<0.01"],
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
  const bust = Math.random() < 0.3 ? `?n=${Math.floor(Math.random() * 1e5)}` : "";
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
  sleep(Math.random());
}
