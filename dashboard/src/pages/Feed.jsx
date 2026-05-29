import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Layout from "../components/Layout.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { CardSkeleton } from "../components/Skeleton.jsx";
import { getPublicFeed, getPublicFeedUrl } from "../api/client.js";

export default function Feed() {
  const [hours, setHours] = useState(24);
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["feed", hours],
    queryFn: () => getPublicFeed({ hours, limit: 200 }),
    refetchInterval: 60_000,
  });

  return (
    <Layout title="Threat Feed">
      <div className="space-y-4">
        <div className="rounded-2xl border border-emerald-600/30 bg-emerald-600/10 p-5 text-sm text-emerald-100">
          <div className="mb-1 text-base font-semibold">
            Public threat feed — สาธารณะ ไม่ต้อง API key
          </div>
          ฟีดของ URL ฟิชชิงที่ <code>label = phishing</code> ใน{" "}
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="rounded bg-emerald-900/40 px-1"
          >
            <option value="1">1 ชั่วโมง</option>
            <option value="6">6 ชั่วโมง</option>
            <option value="24">24 ชั่วโมง</option>
            <option value="72">72 ชั่วโมง</option>
            <option value="168">7 วัน</option>
          </select>
          {" "}ล่าสุด — ดึงไปใช้งานต่อได้:
          <div className="mt-2 flex flex-wrap gap-2 font-mono text-xs">
            <a className="rounded bg-emerald-900/40 px-2 py-1 hover:bg-emerald-900/60"
               href={getPublicFeedUrl("json") + `?hours=${hours}`} target="_blank" rel="noreferrer">
              feed.json
            </a>
            <a className="rounded bg-emerald-900/40 px-2 py-1 hover:bg-emerald-900/60"
               href={getPublicFeedUrl("csv") + `?hours=${hours}`} target="_blank" rel="noreferrer">
              feed.csv
            </a>
            <a className="rounded bg-emerald-900/40 px-2 py-1 hover:bg-emerald-900/60"
               href={getPublicFeedUrl("stix") + `?hours=${hours}`} target="_blank" rel="noreferrer">
              feed.stix (STIX 2.1 bundle)
            </a>
          </div>
        </div>

        {isLoading && <CardSkeleton rows={6} />}
        {isError && <ErrorBanner error={error} />}
        {data && (
          <>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm">
              <span className="text-slate-400">ทั้งหมด</span>{" "}
              <b>{data.count}</b> URLs · generated{" "}
              <span className="text-slate-400">
                {new Date(data.generated_at).toLocaleString("th-TH")}
              </span>
            </div>
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-sm">
                <thead className="bg-slate-900 text-left text-xs text-slate-400">
                  <tr>
                    <th className="px-3 py-3">URL</th>
                    <th className="px-3 py-3">closest_domain</th>
                    <th className="px-3 py-3 text-right">score</th>
                    <th className="px-3 py-3">checked_at</th>
                  </tr>
                </thead>
                <tbody>
                  {data.indicators.length === 0 && (
                    <tr><td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                      ไม่มี URL ฟิชชิงในช่วงเวลานี้ — ดีจัง
                    </td></tr>
                  )}
                  {data.indicators.map((row, i) => (
                    <tr key={i} className="border-t border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{row.url}</td>
                      <td className="px-3 py-2 font-mono text-xs text-slate-400">
                        {row.closest_domain || "—"}
                      </td>
                      <td className="px-3 py-2 text-right">{(row.score * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-xs text-slate-400">
                        {new Date(row.checked_at).toLocaleString("th-TH")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
