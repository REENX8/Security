// Popup: render the latest verdict for the active tab.

import { getTabResult, getSettings } from "./storage.js";

const COLORS = {
  safe: "#22c55e",
  suspicious: "#eab308",
  phishing: "#ef4444",
  unverified: "#94a3b8",
};

const LABEL_TH = {
  safe: "ปลอดภัย",
  suspicious: "น่าสงสัย",
  phishing: "ฟิชชิง",
  unverified: "ตรวจสอบไม่ได้",
};

function showState(html) {
  document.getElementById("content").innerHTML =
    `<div class="state">${html}</div>`;
}

function renderResult(result) {
  const tpl = document.getElementById("result-template");
  const node = tpl.content.cloneNode(true);

  const label = result.label || "unverified";
  const color = COLORS[label] || COLORS.unverified;
  const scorePct = Math.round((result.score || 0) * 100);

  const badge = node.querySelector("[data-badge]");
  badge.textContent = LABEL_TH[label] || label;
  badge.classList.add(label);

  node.querySelector("[data-score-text]").textContent =
    label === "unverified" ? "—" : `${scorePct}%`;

  const meter = node.querySelector("[data-meter]");
  meter.style.width = `${label === "unverified" ? 0 : scorePct}%`;
  meter.style.background = color;

  node.querySelector("[data-reason]").textContent =
    result.reason || "ไม่มีรายละเอียดเพิ่มเติม";

  if (result.closestDomain && result.editDistance != null) {
    const typoRow = node.querySelector("[data-typo-row]");
    const distRow = node.querySelector("[data-dist-row]");
    typoRow.hidden = false;
    distRow.hidden = false;
    node.querySelector("[data-closest]").textContent = result.closestDomain;
    node.querySelector("[data-distance]").textContent = result.editDistance;
  }

  node.querySelector("[data-url]").textContent = result.url || "";

  const content = document.getElementById("content");
  content.innerHTML = "";
  content.appendChild(node);
}

async function init() {
  const settings = await getSettings();

  document.getElementById("dashboard-link").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: settings.dashboardUrl });
  });
  document.getElementById("options-link").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) {
    showState("<p>ไม่พบแท็บที่ใช้งานอยู่</p>");
    return;
  }

  const result = await getTabResult(tab.id);
  if (!result) {
    showState(
      "<p>ยังไม่มีข้อมูลสำหรับหน้านี้</p>" +
      "<p style='font-size:11px;margin-top:6px;color:#64748b'>" +
      "ลองโหลดหน้าเว็บใหม่อีกครั้ง</p>"
    );
    return;
  }
  renderResult(result);
}

init();
