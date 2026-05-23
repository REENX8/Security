import LabelBadge from "./LabelBadge.jsx";
import { formatDateTime, formatPct, truncate } from "../lib/format.js";

export default function HistoryTable({
  items = [], total = 0, limit = 50, offset = 0, onPage, onRowClick, loading,
}) {
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
              <th className="px-4 py-3">URL</th>
              <th className="px-4 py-3">คะแนน</th>
              <th className="px-4 py-3">ผล</th>
              <th className="px-4 py-3">โดเมนที่ถูกแอบอ้าง</th>
              <th className="px-4 py-3">Edit dist.</th>
              <th className="px-4 py-3">เวลาตรวจสอบ</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                กำลังโหลด...
              </td></tr>
            )}
            {!loading && items.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                ไม่พบรายการที่ตรงกับเงื่อนไข
              </td></tr>
            )}
            {!loading && items.map((item) => (
              <tr key={item.id}
                  className="cursor-pointer border-b border-slate-800/60 last:border-0 hover:bg-slate-800/40"
                  onClick={() => onRowClick && onRowClick(item)}>
                <td className="px-4 py-3 font-mono text-xs" title={item.url}>
                  {truncate(item.url, 52)}
                </td>
                <td className="px-4 py-3 font-semibold">
                  {formatPct(item.score)}
                </td>
                <td className="px-4 py-3"><LabelBadge label={item.label} /></td>
                <td className="px-4 py-3 text-xs text-slate-300">
                  {item.closest_domain || "—"}
                </td>
                <td className="px-4 py-3 text-xs">
                  {item.edit_distance ?? "—"}
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">
                  {formatDateTime(item.checked_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-800 px-4 py-3 text-sm">
        <span className="text-slate-400">
          ทั้งหมด {total.toLocaleString()} รายการ · หน้า {page}/{pages}
        </span>
        <div className="flex gap-2">
          <button
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs
                       disabled:opacity-40 hover:bg-slate-800"
            disabled={offset <= 0}
            onClick={() => onPage(Math.max(0, offset - limit))}
          >
            ← ก่อนหน้า
          </button>
          <button
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs
                       disabled:opacity-40 hover:bg-slate-800"
            disabled={page >= pages}
            onClick={() => onPage(offset + limit)}
          >
            ถัดไป →
          </button>
        </div>
      </div>
    </div>
  );
}
