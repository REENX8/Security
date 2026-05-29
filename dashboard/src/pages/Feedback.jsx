import { useState } from "react";
import Layout from "../components/Layout.jsx";
import { Skeleton } from "../components/Skeleton.jsx";
import { useFeedback } from "../api/queries.js";
import { getFeedbackExportUrl } from "../api/client.js";
import LabelBadge from "../components/LabelBadge.jsx";

const LIMIT = 50;

const LABEL_FILTER_OPTIONS = [
  { value: "", label: "ทั้งหมด" },
  { value: "safe", label: "ปลอดภัย" },
  { value: "suspicious", label: "น่าสงสัย" },
  { value: "phishing", label: "ฟิชชิง" },
];

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("th-TH", {
    dateStyle: "short", timeStyle: "short",
  });
}

export default function Feedback() {
  const [verdictGiven, setVerdictGiven] = useState("");
  const [correctVerdict, setCorrectVerdict] = useState("");
  const [offset, setOffset] = useState(0);

  const params = {
    verdict_given: verdictGiven || undefined,
    correct_verdict: correctVerdict || undefined,
    limit: LIMIT,
    offset,
  };
  const { data, isLoading, isError, error } = useFeedback(params);

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  const exportUrl = `${getFeedbackExportUrl()}?x-api-key=${import.meta.env.VITE_API_KEY || "dev-local-key-change-me"}`;

  return (
    <Layout title="รายงานผลผิดพลาด">
      {/* Filters */}
      <div className="mb-5 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-400">ผลที่ระบบตัดสิน</label>
            <select
              value={verdictGiven}
              onChange={(e) => { setVerdictGiven(e.target.value); setOffset(0); }}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              {LABEL_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">ผลที่ถูกต้อง</label>
            <select
              value={correctVerdict}
              onChange={(e) => { setCorrectVerdict(e.target.value); setOffset(0); }}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              {LABEL_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-slate-500">ทั้งหมด {total} รายการ</span>
            <a
              href={exportUrl}
              download="feedback.csv"
              className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              Export CSV
            </a>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        {isLoading ? (
          <div className="space-y-2 py-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : isError ? (
          <p className="py-8 text-center text-red-400">{error?.message}</p>
        ) : items.length === 0 ? (
          <p className="py-8 text-center text-slate-500">ยังไม่มีรายงานผลผิดพลาด</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase text-slate-500">
                  <th className="pb-2 text-left">วันที่</th>
                  <th className="pb-2 text-left">URL</th>
                  <th className="pb-2 text-center">ผลที่ระบบตัดสิน</th>
                  <th className="pb-2 text-center">ผลที่ถูกต้อง</th>
                  <th className="pb-2 text-left">หมายเหตุ</th>
                  <th className="pb-2 text-left">แหล่งที่มา</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 text-xs text-slate-400 whitespace-nowrap">
                      {formatDate(item.created_at)}
                    </td>
                    <td className="py-2.5 max-w-xs">
                      <span className="block truncate font-mono text-xs text-slate-300" title={item.url}>
                        {item.url}
                      </span>
                    </td>
                    <td className="py-2.5 text-center">
                      <LabelBadge label={item.verdict_given} />
                    </td>
                    <td className="py-2.5 text-center">
                      <LabelBadge label={item.correct_verdict} />
                    </td>
                    <td className="py-2.5 max-w-xs">
                      <span className="block truncate text-xs text-slate-400" title={item.comment}>
                        {item.comment || <span className="text-slate-600">—</span>}
                      </span>
                    </td>
                    <td className="py-2.5">
                      <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        {item.source}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > LIMIT && (
          <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className="rounded px-3 py-1 hover:bg-slate-800 disabled:opacity-30"
            >
              ← ก่อนหน้า
            </button>
            <span>
              {offset + 1}–{Math.min(offset + LIMIT, total)} จาก {total}
            </span>
            <button
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
              className="rounded px-3 py-1 hover:bg-slate-800 disabled:opacity-30"
            >
              ถัดไป →
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
