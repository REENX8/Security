import { formatPct } from "../lib/format.js";

// Surfaces the transparent rules engine: shows the ML model probability vs.
// the final score and lists every rule that fired, with its human-readable
// Thai message. This is the system's core "explainable hybrid" differentiator.
export default function RulesPanel({ rules, mlScore, finalScore }) {
  const hits = rules?.hits || [];
  const pinned = rules?.pinned_label;
  const hasMl = typeof mlScore === "number";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
        ทำไมระบบจึงตัดสินแบบนี้
      </div>

      {hasMl && (
        <div className="mb-3 grid grid-cols-2 gap-3">
          <ScorePill label="โมเดล ML" value={mlScore} accent="#3b82f6" />
          <ScorePill
            label="คะแนนสุดท้าย"
            value={finalScore}
            accent="#a855f7"
            note={
              rules?.score_delta
                ? `${rules.score_delta > 0 ? "+" : ""}${Math.round(
                    rules.score_delta * 100
                  )}% จากกฎ`
                : null
            }
          />
        </div>
      )}

      {pinned && (
        <div
          className={`mb-3 rounded-md px-3 py-2 text-xs font-medium ${
            pinned === "phishing"
              ? "bg-phishing/15 text-phishing"
              : "bg-safe/15 text-safe"
          }`}
        >
          กฎบังคับผล (pinned): {pinned === "phishing" ? "ฟิชชิง" : "ปลอดภัย"}
        </div>
      )}

      {hits.length > 0 ? (
        <ul className="space-y-2">
          {hits.map((h) => (
            <li
              key={h.rule_id}
              className="flex items-start gap-3 rounded-md border border-slate-800 bg-slate-900 p-3"
            >
              <span
                className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 font-mono text-[11px] ${
                  h.delta > 0
                    ? "bg-phishing/20 text-phishing"
                    : "bg-safe/20 text-safe"
                }`}
                title={`score delta ${h.delta > 0 ? "+" : ""}${h.delta}`}
              >
                {h.rule_id}
              </span>
              <span className="text-sm leading-relaxed text-slate-300">
                {h.message}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">
          ไม่มีกฎ (rule) ใดถูกกระตุ้น — ผลตัดสินมาจากโมเดล ML ล้วน
        </p>
      )}
    </div>
  );
}

function ScorePill({ label, value, accent, note }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2">
      <div className="text-[11px] text-slate-500">{label}</div>
      <div className="text-lg font-bold" style={{ color: accent }}>
        {formatPct(value)}
      </div>
      {note && <div className="text-[10px] text-slate-500">{note}</div>}
    </div>
  );
}
