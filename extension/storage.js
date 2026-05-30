// chrome.storage.local helpers: settings + a last-100 results ring buffer.

// Production URLs — users who install from the store get these automatically.
// Self-hosters can override via the options page.
const DEFAULT_SETTINGS = {
  endpoint: "https://phish-backend.onrender.com",
  dashboardUrl: "https://phish-dashboard.onrender.com",
  notifications: true,
  enabled: true,
  blockPhishing: true,
};

const MAX_HISTORY = 100;

export async function getSettings() {
  const { settings } = await chrome.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(settings || {}) };
}

export async function saveSettings(partial) {
  const current = await getSettings();
  const merged = { ...current, ...partial };
  await chrome.storage.local.set({ settings: merged });
  return merged;
}

// Latest result for each tab (used by the badge + popup).
export async function setTabResult(tabId, result) {
  const { tabResults = {} } = await chrome.storage.local.get("tabResults");
  tabResults[tabId] = result;
  await chrome.storage.local.set({ tabResults });
  await pushHistory(result);
}

export async function getTabResult(tabId) {
  const { tabResults = {} } = await chrome.storage.local.get("tabResults");
  return tabResults[tabId] || null;
}

export async function clearTabResult(tabId) {
  const { tabResults = {} } = await chrome.storage.local.get("tabResults");
  delete tabResults[tabId];
  await chrome.storage.local.set({ tabResults });
}

async function pushHistory(result) {
  const { history = [] } = await chrome.storage.local.get("history");
  history.unshift(result);
  await chrome.storage.local.set({ history: history.slice(0, MAX_HISTORY) });
}

export async function getHistory() {
  const { history = [] } = await chrome.storage.local.get("history");
  return history;
}

export async function clearHistory() {
  await chrome.storage.local.set({ history: [], tabResults: {} });
}

// --- session-scoped bypass set (cleared when the browser restarts) ---
const SESSION = chrome.storage.session || chrome.storage.local;

export async function isBypassed(host) {
  if (!host) return false;
  const { bypass = [] } = await SESSION.get("bypass");
  return bypass.includes(host);
}

export async function addBypass(host) {
  if (!host) return;
  const { bypass = [] } = await SESSION.get("bypass");
  if (!bypass.includes(host)) {
    bypass.push(host);
    await SESSION.set({ bypass });
  }
}

export async function clearBypass() {
  await SESSION.set({ bypass: [] });
}
