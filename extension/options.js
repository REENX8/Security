// Options page: load / save settings, clear history.

import { getSettings, saveSettings, getHistory, clearHistory }
  from "./storage.js";

const fields = ["endpoint", "apiKey", "dashboardUrl"];
const toggles = ["enabled", "notifications"];

function setStatus(msg, color = "#22c55e") {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.style.color = color;
  setTimeout(() => { el.textContent = ""; }, 2500);
}

async function refreshHistoryCount() {
  const history = await getHistory();
  document.getElementById("history-count").textContent =
    `มีบันทึกการตรวจสอบ ${history.length} รายการ`;
}

async function load() {
  const settings = await getSettings();
  fields.forEach((f) => { document.getElementById(f).value = settings[f] || ""; });
  toggles.forEach((t) => {
    document.getElementById(t).checked = Boolean(settings[t]);
  });
  await refreshHistoryCount();
}

async function save() {
  const partial = {};
  fields.forEach((f) => {
    partial[f] = document.getElementById(f).value.trim();
  });
  toggles.forEach((t) => {
    partial[t] = document.getElementById(t).checked;
  });

  if (!partial.endpoint) {
    setStatus("กรุณากรอก API Endpoint", "#ef4444");
    return;
  }
  // Strip a trailing slash for consistent request URLs.
  partial.endpoint = partial.endpoint.replace(/\/+$/, "");
  partial.dashboardUrl = (partial.dashboardUrl || "").replace(/\/+$/, "");

  await saveSettings(partial);
  setStatus("บันทึกแล้ว ✓");
}

document.getElementById("save").addEventListener("click", save);
document.getElementById("clear-history").addEventListener("click", async () => {
  await clearHistory();
  await refreshHistoryCount();
  setStatus("ล้างประวัติแล้ว ✓");
});

load();
