// MV3 service worker: checks every top-level navigation against the backend.

import { checkUrl } from "./api.js";
import { setBadge, clearBadge } from "./badge.js";
import {
  getSettings,
  setTabResult,
  getTabResult,
  clearTabResult,
} from "./storage.js";

const NOTIFY_PREFIX = "phish-warn-";

function isCheckable(url) {
  return url && (url.startsWith("http://") || url.startsWith("https://"));
}

function sameHost(a, b) {
  try {
    return new URL(a).host === new URL(b).host;
  } catch (_) {
    return false;
  }
}

async function handleNavigation(details) {
  if (details.frameId !== 0) return; // top-level frame only
  const url = details.url;
  if (!isCheckable(url)) return;

  const settings = await getSettings();
  if (!settings.enabled) return;
  // Never check the backend's own host (avoids a feedback loop).
  if (sameHost(url, settings.endpoint)) return;

  const result = await checkUrl(url);
  result.tabId = details.tabId;
  result.timestamp = result.timestamp || Date.now();

  await setTabResult(details.tabId, result);
  await setBadge(details.tabId, result.label);

  if (result.label === "phishing" && settings.notifications) {
    chrome.notifications.create(NOTIFY_PREFIX + details.tabId, {
      type: "basic",
      iconUrl: "icons/icon128.png",
      title: "⚠ เตือนภัยเว็บไซต์ฟิชชิง",
      message:
        `${url}\n\n${result.reason || "เว็บไซต์นี้อาจเป็นการปลอมแปลง"}`,
      priority: 2,
    });
  }
}

// --- navigation ---
chrome.webNavigation.onBeforeNavigate.addListener(handleNavigation);

// --- keep the badge correct when switching tabs ---
chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const result = await getTabResult(tabId);
  if (result) {
    await setBadge(tabId, result.label);
  } else {
    await clearBadge(tabId);
  }
});

// --- clean up closed tabs ---
chrome.tabs.onRemoved.addListener((tabId) => {
  clearTabResult(tabId);
});

// --- open the dashboard when a warning notification is clicked ---
chrome.notifications.onClicked.addListener(async (notificationId) => {
  if (!notificationId.startsWith(NOTIFY_PREFIX)) return;
  const settings = await getSettings();
  chrome.tabs.create({ url: settings.dashboardUrl });
  chrome.notifications.clear(notificationId);
});

// --- first-run defaults ---
chrome.runtime.onInstalled.addListener(async () => {
  await getSettings(); // materialises defaults if absent
});
