// Shared formatting helpers + label styling.

export const LABELS = {
  safe: { th: "ปลอดภัย", color: "#22c55e", bg: "bg-safe/15", text: "text-safe" },
  suspicious: {
    th: "น่าสงสัย", color: "#eab308",
    bg: "bg-suspicious/15", text: "text-suspicious",
  },
  phishing: {
    th: "ฟิชชิง", color: "#ef4444",
    bg: "bg-phishing/15", text: "text-phishing",
  },
  unverified: {
    th: "ตรวจสอบไม่ได้", color: "#94a3b8",
    bg: "bg-slate-500/15", text: "text-slate-400",
  },
};

export function labelInfo(label) {
  return LABELS[label] || LABELS.unverified;
}

export function formatPct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("th-TH", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("th-TH", { day: "2-digit", month: "short" });
}

export function truncate(text, max = 60) {
  if (!text) return "";
  return text.length > max ? text.slice(0, max) + "…" : text;
}
