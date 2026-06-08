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

  // Feedback button (only for verified results)
  const reportBtn = node.querySelector("[data-report-btn]");
  if (label !== "unverified" && reportBtn) {
    reportBtn.hidden = false;
    const feedbackForm = node.querySelector("[data-feedback-form]");
    reportBtn.addEventListener("click", () => {
      reportBtn.hidden = true;
      feedbackForm.hidden = false;
    });
    node.querySelector("[data-cancel-feedback]").addEventListener("click", () => {
      feedbackForm.hidden = true;
      reportBtn.hidden = false;
    });
    node.querySelectorAll("[data-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        node.querySelectorAll("[data-choice]").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        btn.dataset.selectedChoice = btn.dataset.choice;
      });
    });
    const validationEl = node.querySelector("[data-feedback-validation]");
    node.querySelector("[data-submit-feedback]").addEventListener("click", async () => {
      const selected = node.querySelector("[data-choice].selected");
      if (!selected) {
        if (validationEl) { validationEl.hidden = false; }
        return;
      }
      if (validationEl) { validationEl.hidden = true; }
      const comment = node.querySelector("[data-comment]").value.trim();
      const statusEl = node.querySelector("[data-feedback-status]");
      try {
        await _submitFeedback(result, selected.dataset.choice, comment);
        statusEl.textContent = "ส่งรายงานเรียบร้อย";
        statusEl.hidden = false;
        feedbackForm.hidden = true;
        reportBtn.textContent = "ส่งรายงานแล้ว";
        reportBtn.hidden = false;
        reportBtn.disabled = true;
      } catch (err) {
        statusEl.textContent = `เกิดข้อผิดพลาด: ${err.message}`;
        statusEl.hidden = false;
      }
    });
  }

  const content = document.getElementById("content");
  content.innerHTML = "";
  content.appendChild(node);
}

async function _submitFeedback(result, correctVerdict, comment) {
  const settings = await getSettings();
  const endpoint = (settings.endpoint || "http://localhost:8000").replace(/\/+$/, "");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  let resp;
  try {
    resp = await fetch(`${endpoint}/api/v1/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: result.url,
        verdict_given: result.label,
        correct_verdict: correctVerdict,
        comment,
        source: "extension",
      }),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
}

async function init() {
  const settings = await getSettings();

  document.getElementById("dashboard-link").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: settings.dashboardUrl });
  });
  document.getElementById("about-link").addEventListener("click", (e) => {
    e.preventDefault();
    const base = (settings.dashboardUrl || "").replace(/\/+$/, "");
    chrome.tabs.create({ url: `${base}/about` });
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
