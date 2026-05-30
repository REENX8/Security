// Backend API client with a hard 3-second timeout.

import { getSettings } from "./storage.js";

const TIMEOUT_MS = 3000;

// Returns a normalised result object. On any failure the label is
// "unverified" / "unreachable" so the extension never blocks navigation.
export async function checkUrl(url) {
  const settings = await getSettings();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const resp = await fetch(`${settings.endpoint}/api/v1/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!resp.ok) {
      let code = `HTTP ${resp.status}`;
      try {
        const body = await resp.json();
        code = body.error || code;
      } catch (_) { /* ignore */ }
      return { url, label: "unverified", reason: code, score: 0 };
    }

    const data = await resp.json();
    return {
      url,
      score: data.score,
      label: data.label,
      reason: data.reason,
      closestDomain: data.closest_domain,
      editDistance: data.edit_distance,
      checkedAt: data.checked_at,
      timestamp: Date.now(),
    };
  } catch (err) {
    clearTimeout(timer);
    const reason = err.name === "AbortError"
      ? "หมดเวลาเชื่อมต่อ (timeout)"
      : "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้";
    return { url, label: "unverified", reason, score: 0 };
  }
}
