// MV3 service worker.
//
// Every top-level navigation is sent to the backend; a phishing verdict
// triggers (a) a desktop notification and (b) an interstitial warning page
// that intercepts the navigation. Users can bypass the warning per session.

import { checkUrl } from "./api.js";
import { setBadge, clearBadge } from "./badge.js";
import {
  getSettings,
  setTabResult,
  getTabResult,
  clearTabResult,
  isBypassed,
  addBypass,
} from "./storage.js";

const NOTIFY_PREFIX = "phish-warn-";
const WARNING_PATH = "warning.html";

function isCheckable(url) {
  return url && (url.startsWith("http://") || url.startsWith("https://"));
}

function safeHost(url) {
  try { return new URL(url).host; } catch (_) { return ""; }
}

function buildWarningUrl(result) {
  const params = new URLSearchParams({
    url: result.url || "",
    reason: result.reason || "",
    closest: result.closestDomain || "",
    score: String(result.score ?? ""),
  });
  return chrome.runtime.getURL(`${WARNING_PATH}?${params.toString()}`);
}

async function handleNavigation(details) {
  if (details.frameId !== 0) return;
  const url = details.url;
  if (!isCheckable(url)) return;

  const settings = await getSettings();
  if (!settings.enabled) return;
  // Avoid a feedback loop with the backend's own host.
  if (safeHost(url) === safeHost(settings.endpoint)) return;

  const result = await checkUrl(url);
  result.tabId = details.tabId;
  result.timestamp = result.timestamp || Date.now();

  await setTabResult(details.tabId, result);
  await setBadge(details.tabId, result.label);

  if (result.label === "phishing") {
    const host = safeHost(url);
    const bypassed = await isBypassed(host);
    if (settings.notifications && !bypassed) {
      chrome.notifications.create(NOTIFY_PREFIX + details.tabId, {
        type: "basic",
        iconUrl: "icons/icon128.png",
        title: "⚠ เตือนภัยเว็บไซต์ฟิชชิง",
        message:
          `${url}\n\n${result.reason || "เว็บไซต์นี้อาจเป็นการปลอมแปลง"}`,
        priority: 2,
      });
    }
    if (settings.blockPhishing && !bypassed) {
      try {
        await chrome.tabs.update(details.tabId,
                                 { url: buildWarningUrl(result) });
      } catch (_) { /* tab may have closed */ }
    }
  }
}

// --- navigation ---
chrome.webNavigation.onBeforeNavigate.addListener(handleNavigation);

// --- keep the badge correct when switching tabs ---
chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const result = await getTabResult(tabId);
  if (result) await setBadge(tabId, result.label);
  else await clearBadge(tabId);
});

chrome.tabs.onRemoved.addListener((tabId) => clearTabResult(tabId));

// --- open the dashboard when a warning notification is clicked ---
chrome.notifications.onClicked.addListener(async (notificationId) => {
  if (!notificationId.startsWith(NOTIFY_PREFIX)) return;
  const settings = await getSettings();
  chrome.tabs.create({ url: settings.dashboardUrl });
  chrome.notifications.clear(notificationId);
});

// --- bypass messages from warning.html ---
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "bypass" && msg.url) {
    addBypass(safeHost(msg.url)).then(() => sendResponse({ ok: true }));
    return true;  // async response
  }
  return false;
});

// --- first-run defaults ---
chrome.runtime.onInstalled.addListener(async () => {
  await getSettings();
});
