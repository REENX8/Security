import { useEffect, useState } from "react";
import LabelBadge from "./LabelBadge.jsx";
import RulesPanel from "./RulesPanel.jsx";
import { formatDateTime, formatPct, labelInfo } from "../lib/format.js";
import { useSubmitFeedback } from "../api/queries.js";

const VERDICTS = ["safe", "suspicious", "phishing"];
const VERDICT_TH = { safe: "ปลอดภัย", suspicious: "น่าสงสัย", phishing: "ฟิชชิง" };

export default function DetailModal({ item, onClose }) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [correctVerdict, setCorrectVerdict] = useState("safe");
  const [comment, setComment] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showFeatures, setShowFeatures] = useState(false);
  const submitFeedback = useSubmitFeedback();

  // close on escape
  useEffect(() => {
    if (!item) return undefined;
    setShowFeedback(false);
    setFeedbackSent(false);
    setShowFeatures(false);
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [item, onClose]);

  if (!item) return null;

  const info = labelInfo(item.label);

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    await submitFeedback.mutateAsync({
      url: item.url,
      verdict_given: item.label,
      correct_verdict: correctVerdict,
      comment: comment.trim(),
      source: "dashboard",
    });
    setFeedbackSent(true);
    setShowFeedback(false);
    setComment("");
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-slate-700 bg-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        <header
          className="flex items-center justify-between px-6 py-4"
          style={{ background: `${info.color}15`, borderBottom: `1px solid ${info.color}30` }}
        >
          <div className="flex items-center gap-3">
            <LabelBadge label={item.label} />
            <span className="text-2xl font-extrabold"
                  style={{ color: info.color }}>
              {formatPct(item.score)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {feedbackSent ? (
              <span className="text-xs text-green-400">ส่งรายงานแล้ว</span>
            ) : (
              <button
                onClick={() => setShowFeedback((v) => !v)}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
                title="แจ้งผลผิดพลาด"
              >
                🚩 แจ้งผลผิด
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </header>

        {showFeedback && (
          <form
            onSubmit={handleFeedbackSubmit}
            className="border-b border-slate-800 bg-slate-950 px-6 py-4"
          >
            <p className="mb-3 text-xs text-slate-400">
              ผลที่ระบบตัดสิน: <strong className="text-white">{VERDICT_TH[item.label] ?? item.label}</strong>
              {" "}— กรุณาระบุผลที่ถูกต้อง
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              {VERDICTS.map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setCorrectVerdict(v)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition
                    ${correctVerdict === v
                      ? "bg-blue-600 text-white"
                      : "border border-slate-700 text-slate-300 hover:bg-slate-800"}`}
                >
                  {VERDICT_TH[v]}
                </button>
              ))}
            </div>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="หมายเหตุเพิ่มเติม (ไม่บังคับ)"
              rows={2}
              maxLength={1024}
              className="mb-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs outline-none focus:border-blue-500"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowFeedback(false)}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800"
              >
                ยกเลิก
              </button>
              <button
                type="submit"
                disabled={submitFeedback.isPending}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {submitFeedback.isPending ? "กำลังส่ง..." : "ส่งรายงาน"}
              </button>
            </div>
          </form>
        )}

        <div className="space-y-4 px-6 py-5">
          <div>
            <div className="text-xs text-slate-500">URL</div>
            <div className="mt-1 break-all rounded-lg bg-slate-950 p-3 font-mono text-xs">
              {item.url}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500">เหตุผล</div>
            <p className="mt-1 rounded-lg border-l-4 border-blue-500 bg-slate-950 p-3 text-sm leading-relaxed">
              {item.reason || "—"}
            </p>
          </div>

          {item.rules && (
            <RulesPanel
              rules={item.rules}
              mlScore={item.ml_score}
              finalScore={item.score}
            />
          )}

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <KV label="ตรวจสอบเมื่อ" value={formatDateTime(item.checked_at)} />
            <KV label="โดเมนใกล้เคียง" value={item.closest_domain || "—"} />
            <KV label="Edit distance" value={item.edit_distance ?? "—"} />
          </div>

          {item.features && (
            <div>
              <button
                onClick={() => setShowFeatures((v) => !v)}
                className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400 hover:text-slate-200"
                aria-expanded={showFeatures}
              >
                <span>{showFeatures ? "▾" : "▸"}</span>
                ดูฟีเจอร์ทั้งหมด ({Object.keys(item.features).length})
              </button>
              {showFeatures && (
                <div className="overflow-hidden rounded-lg border border-slate-800">
                  <table className="w-full text-xs">
                    <tbody>
                      {Object.entries(item.features).map(([k, v], i) => (
                        <tr key={k}
                            className={i % 2 ? "bg-slate-950" : "bg-slate-900"}>
                          <td className="px-3 py-1.5 font-mono text-slate-400">{k}</td>
                          <td className="px-3 py-1.5 text-right font-mono text-slate-200">
                            {typeof v === "boolean" ? String(v) :
                             v === null ? "—" : String(v)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KV({ label, value }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 truncate text-sm font-semibold text-slate-200">{value}</div>
    </div>
  );
}
