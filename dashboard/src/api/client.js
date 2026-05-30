// Backend API client — uses JWT Bearer token from localStorage.

import { clearToken, getToken } from "../lib/auth.js";

function normalizeBase(raw) {
  let v = (raw || "http://localhost:8000").replace(/\/+$/, "");
  if (v && !/^https?:\/\//i.test(v)) v = `https://${v}`;
  return v;
}

const BASE_URL = normalizeBase(import.meta.env.VITE_API_URL);

async function request(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers || {}) },
  });

  if (resp.status === 401) {
    clearToken();
    window.location.replace("/login");
    throw new Error("Session expired. Please log in again.");
  }

  if (!resp.ok) {
    let message = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      message = body.error || body.detail || message;
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

export async function exportFeedbackCsv() {
  const token = getToken();
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${BASE_URL}/api/v1/feedback/export`, { headers });
  if (resp.status === 401) {
    clearToken();
    window.location.replace("/login");
    throw new Error("Session expired.");
  }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "feedback.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// --- Brand watchlist ---

export function getWatchlist() {
  return request("/api/v1/watchlist");
}

export function addWatchlistEntry(data) {
  return request("/api/v1/watchlist", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteWatchlistEntry(brand) {
  return request(`/api/v1/watchlist/${encodeURIComponent(brand)}`, {
    method: "DELETE",
  });
}

export function getWebhookDeliveries({ brand = "", limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset });
  if (brand) params.set("brand", brand);
  return request(`/api/v1/watchlist/deliveries?${params.toString()}`);
}

// --- Campaigns ---

export function getCampaigns({ min_urls = 1, brand = "", limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ min_urls, limit, offset });
  if (brand) params.set("brand", brand);
  return request(`/api/v1/campaigns?${params.toString()}`);
}

// --- Domain reputation ---

export function getDomainHistory(host) {
  return request(`/api/v1/domain/${encodeURIComponent(host)}/history`);
}

// --- Public threat feed ---

export function getPublicFeed({ hours = 24, limit = 200 } = {}) {
  const params = new URLSearchParams({ hours, limit });
  return request(`/api/v1/feed.json?${params.toString()}`);
}

export function getPublicFeedUrl(format = "json") {
  return `${BASE_URL}/api/v1/feed.${format}`;
}

// --- Social / economic impact ---

export function getImpact(windowDays = 30) {
  return request(`/api/v1/impact?window_days=${windowDays}`);
}

// --- Awareness content ---

export function getLearn(audience) {
  const qs = audience ? `?audience=${encodeURIComponent(audience)}` : "";
  return request(`/api/v1/learn${qs}`);
}
