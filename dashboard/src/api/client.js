// Backend API client.

const BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace(/\/+$/, "");
const API_KEY = import.meta.env.VITE_API_KEY || "dev-local-key-change-me";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...(options.headers || {}),
    },
  });

  if (!resp.ok) {
    let message = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      message = body.error || message;
    } catch (_) { /* ignore */ }
    throw new Error(message);
  }
  return resp.json();
}

export function getStats() {
  return request("/api/v1/stats");
}

export function getHistory({ limit = 50, offset = 0, label, search,
                             dateFrom, dateTo } = {}) {
  const params = new URLSearchParams({ limit, offset });
  if (label) params.set("label", label);
  if (search) params.set("search", search);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return request(`/api/v1/history?${params.toString()}`);
}

export function checkUrl(url) {
  return request("/api/v1/check", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function checkBatch(urls) {
  return request("/api/v1/check/batch", {
    method: "POST",
    body: JSON.stringify({ urls }),
  });
}

export function getHealth() {
  return request("/health");
}

// --- Whitelist ---

export function getWhitelist({ search = "", limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset });
  if (search) params.set("search", search);
  return request(`/api/v1/admin/whitelist?${params.toString()}`);
}

export function addWhitelistEntry(data) {
  return request("/api/v1/admin/whitelist", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteWhitelistEntry(domain) {
  return request(`/api/v1/admin/whitelist/${encodeURIComponent(domain)}`, {
    method: "DELETE",
  });
}

// --- Feedback ---

export function getFeedback({ verdict_given = "", correct_verdict = "",
                              limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset });
  if (verdict_given) params.set("verdict_given", verdict_given);
  if (correct_verdict) params.set("correct_verdict", correct_verdict);
  return request(`/api/v1/feedback?${params.toString()}`);
}

export function submitFeedback(data) {
  return request("/api/v1/feedback", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getFeedbackExportUrl() {
  return `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "")}/api/v1/feedback/export`;
}
