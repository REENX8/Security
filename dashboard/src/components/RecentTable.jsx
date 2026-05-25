import LabelBadge from "./LabelBadge.jsx";
import { formatDateTime, formatPct, truncate } from "../lib/format.js";

export default function RecentTable({ items = [] }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        การตรวจสอบล่าสุด
      </h3>
      {items.length === 0 ? (
        <div className="py-8 text-center text-sm text-slate-500">
          ยังไม่มีรายการตรวจสอบ
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                <th className="pb-2 pr-4">URL</th>
                <th className="pb-2 pr-4">คะแนน</th>
                <th className="pb-2 pr-4">ผล</th>
                <th className="pb-2">เวลา</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}
                    className="border-b border-slate-800/60 last:border-0">
                  <td className="py-2.5 pr-4 font-mono text-xs">
                    {truncate(item.url, 48)}
                  </td>
                  <td className="py-2.5 pr-4 font-semibold">
                    {formatPct(item.score)}
                  </td>
                  <td className="py-2.5 pr-4">
                    <LabelBadge label={item.label} />
                  </td>
                  <td className="py-2.5 text-xs text-slate-400">
                    {formatDateTime(item.checked_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
