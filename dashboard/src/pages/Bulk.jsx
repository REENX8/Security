import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Layout from "../components/Layout.jsx";
import LabelBadge from "../components/LabelBadge.jsx";
import DetailModal from "../components/DetailModal.jsx";
import { useCheckBatch } from "../api/queries.js";
import { formatPct, truncate } from "../lib/format.js";
import { downloadCsv, toCsv } from "../lib/csv.js";

const BATCH_LIMIT = 50;

export default function Bulk() {
  const [input, setInput] = useState(
    "https://www.obec.go.th\n" +
    "http://obec.com/verify-account\n" +
    "https://www.google.com\n" +
    "http://203.0.113.45/login"
  );
  const [detail, setDetail] = useState(null);
  const batchMutation = useCheckBatch();
  const qc = useQueryClient();

  const urls = useMemo(() => (
    input.split(/\r?\n/).map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#"))
  ), [input]);

  const tooMany = urls.length > BATCH_LIMIT;

  const submit = (e) => {
    e.preventDefault();
    if (!urls.length || tooMany) return;
    batchMutation.mutate(urls, {
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: ["stats"] });
        qc.invalidateQueries({ queryKey: ["history"] });
      },
    });
  };

  const results = batchMutation.data?.results || [];
  const summary = results.reduce(
    (acc, r) => { acc[r.label] = (acc[r.label] || 0) + 1; return acc; },
    { safe: 0, suspicious: 0, phishing: 0 },
  );

  const exportCsv = () => {
    const rows = results.map((r) => ({
      url: r.url, label: r.label, score: r.score,
      closest_domain: r.closest_domain || "",
      edit_distance: r.edit_distance ?? "",
      reason: r.reason || "",
    }));
    const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    downloadCsv(`bulk-check-${stamp}.csv`,
                toCsv(rows, ["url", "label", "score", "closest_domain",
                             "edit_distance", "reason"]));
  };

  return (
    <Layout title="ตรวจหลาย URL พร้อมกัน">
      <form onSubmit={submit}
            className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <label className="mb-2 block text-sm text-slate-300">
          วาง URL ทีละบรรทัด (สูงสุด {BATCH_LIMIT} URL ต่อครั้ง)
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={10}
          spellCheck={false}
          className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-sm outline-none focus:border-blue-500"
          placeholder="https://example.go.th/login"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <span className={`text-sm ${tooMany ? "text-phishing" : "text-slate-400"}`}>
            {urls.length} URLs
            {tooMany && ` — เกินจำกัด ${BATCH_LIMIT}`}
          </span>
          <button
            type="submit"
            disabled={!urls.length || tooMany || batchMutation.isPending}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {batchMutation.isPending ? "กำลังตรวจสอบ..." : "ตรวจสอบทั้งหมด"}
          </button>
        </div>
      </form>

      {batchMutation.isError && (
        <div className="mt-4 rounded-lg border border-phishing/40 bg-phishing/10 px-4 py-3 text-sm text-phishing">
          เกิดข้อผิดพลาด: {batchMutation.error.message}
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-3">
            <div className="text-sm">
              <span className="font-semibold">{results.length} URLs ถูกตรวจสอบ:</span>
              <span className="ml-3 text-safe">{summary.safe} ปลอดภัย</span>
              <span className="ml-3 text-suspicious">{summary.suspicious} น่าสงสัย</span>
              <span className="ml-3 text-phishing">{summary.phishing} ฟิชชิง</span>
            </div>
            <button
              onClick={exportCsv}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs hover:bg-slate-800"
            >
              📥 Export CSV
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                  <th className="px-4 py-3">URL</th>
                  <th className="px-4 py-3">คะแนน</th>
                  <th className="px-4 py-3">ผล</th>
                  <th className="px-4 py-3">เหตุผล</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, idx) => (
                  <tr key={idx}
                      className="cursor-pointer border-b border-slate-800/60 last:border-0 hover:bg-slate-800/40"
                      onClick={() => setDetail({
                        ...r,
                        id: idx, checked_at: r.checked_at,
                      })}>
                    <td className="px-4 py-3 font-mono text-xs" title={r.url}>
                      {truncate(r.url, 60)}
                    </td>
                    <td className="px-4 py-3 font-semibold">{formatPct(r.score)}</td>
                    <td className="px-4 py-3"><LabelBadge label={r.label} /></td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {truncate(r.reason, 80)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <DetailModal item={detail} onClose={() => setDetail(null)} />
    </Layout>
  );
}
