import { useEffect } from "react";
import LabelBadge from "./LabelBadge.jsx";
import { formatDateTime, formatPct, labelInfo } from "../lib/format.js";

export default function DetailModal({ item, onClose }) {
  // close on escape
  useEffect(() => {
    if (!item) return undefined;
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [item, onClose]);

  if (!item) return null;

  const info = labelInfo(item.label);

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
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </header>

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

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <KV label="ตรวจสอบเมื่อ" value={formatDateTime(item.checked_at)} />
            <KV label="โดเมนใกล้เคียง" value={item.closest_domain || "—"} />
            <KV label="Edit distance" value={item.edit_distance ?? "—"} />
          </div>

          {item.features && (
            <div>
              <div className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Features (21)
              </div>
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
