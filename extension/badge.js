// Toolbar badge helpers.

const BADGE = {
  safe:       { text: "✓", color: "#22c55e" }, // check
  suspicious: { text: "?",      color: "#eab308" },
  phishing:   { text: "!",      color: "#ef4444" },
  unverified: { text: "•", color: "#94a3b8" }, // dot
};

export async function setBadge(tabId, label) {
  const cfg = BADGE[label] || BADGE.unverified;
  try {
    await chrome.action.setBadgeText({ tabId, text: cfg.text });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: cfg.color });
    await chrome.action.setBadgeTextColor({ tabId, color: "#ffffff" });
  } catch (_) {
    // Tab may have been closed mid-update -- ignore.
  }
}

export async function clearBadge(tabId) {
  try {
    await chrome.action.setBadgeText({ tabId, text: "" });
  } catch (_) { /* ignore */ }
}
