// Warning interstitial: shown when the extension intercepts a phishing
// navigation. The original URL, verdict reason and impersonated domain are
// passed via query-string parameters.

(function () {
  const params = new URLSearchParams(window.location.search);
  const originalUrl = params.get("url") || "";
  const reason = params.get("reason") || "ตรวจพบรูปแบบที่อาจเป็นการปลอมแปลง";
  const closestDomain = params.get("closest") || "";
  const score = params.get("score") || "";

  document.getElementById("blocked-url").textContent = originalUrl;
  document.getElementById("reason").textContent = reason;

  if (closestDomain) {
    document.getElementById("closest-row").hidden = false;
    document.getElementById("closest-domain").textContent = closestDomain;
  }
  if (score) {
    document.getElementById("score-row").hidden = false;
    const pct = Math.round(Number(score) * 100);
    document.getElementById("score").textContent =
      Number.isFinite(pct) ? `${pct}%` : score;
  }

  document.title = "⚠ บล็อกแล้ว: " + (originalUrl.slice(0, 60) || "เว็บฟิชชิง");

  document.getElementById("back-btn").addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      chrome.tabs.getCurrent((tab) => tab && chrome.tabs.remove(tab.id));
    }
  });

  document.getElementById("proceed-btn").addEventListener("click", async () => {
    if (!originalUrl) return;
    const confirmed = window.confirm(
      "คุณยืนยันจะเปิดเว็บไซต์นี้หรือไม่?\n\n" +
      "Thai Phishing Detector เตือนว่าเว็บไซต์นี้อาจขโมยข้อมูลส่วนตัว " +
      "หรือรหัสผ่านของคุณ\n\nกด OK เพื่อยอมรับความเสี่ยงและเข้าใช้งานต่อ"
    );
    if (!confirmed) return;
    // Mark this host as bypassed for the session, then navigate.
    chrome.runtime.sendMessage(
      { type: "bypass", url: originalUrl },
      () => { window.location.replace(originalUrl); }
    );
  });
})();
