import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import Layout from "../components/Layout.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { CardSkeleton } from "../components/Skeleton.jsx";
import { getCampaigns } from "../api/client.js";

export default function Campaigns() {
  const [search, setSearch] = useState("");
  const [minUrls, setMinUrls] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["campaigns", { brand: search, min_urls: minUrls }],
    queryFn: () => getCampaigns({ brand: search, min_urls: minUrls, limit: 100 }),
    placeholderData: keepPreviousData,
  });

  return (
    <Layout title="แคมเปญฟิชชิง">
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-300">
          ระบบจัดกลุ่ม URL ฟิชชิงโดยอัตโนมัติด้วย <b>fingerprint</b>:{" "}
          แบรนด์ที่ถูกปลอม + TLD + รูปแบบ path
          URL หลายตัวที่มี fingerprint เดียวกันมักมาจาก <b>kit เดียวกัน</b> —
          ใช้ระบุแคมเปญและบล็อกทั้งกลุ่มได้
        </div>

        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="กรองแบรนด์ที่ถูกปลอม..."
            className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <select
            value={minUrls}
            onChange={(e) => setMinUrls(Number(e.target.value))}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            <option value="1">≥ 1 URL</option>
            <option value="2">≥ 2 URLs</option>
            <option value="5">≥ 5 URLs</option>
            <option value="10">≥ 10 URLs</option>
          </select>
        </div>

        {isLoading && <CardSkeleton rows={5} />}
        {error && <ErrorBanner error={error} />}

        {data && (
          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-left text-xs text-slate-400">
                <tr>
                  <th className="px-3 py-3">แบรนด์เป้าหมาย</th>
                  <th className="px-3 py-3">TLD</th>
                  <th className="px-3 py-3">รูปแบบ path</th>
                  <th className="px-3 py-3 text-right">จำนวน URL</th>
                  <th className="px-3 py-3">พบครั้งแรก</th>
                  <th className="px-3 py-3">พบล่าสุด</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                      ยังไม่มีแคมเปญในระบบ — ให้ระบบตรวจ URL ฟิชชิงจริงก่อน
                    </td>
                  </tr>
                )}
                {data.items.map((c) => (
                  <tr key={c.id} className="border-t border-slate-800 hover:bg-slate-900">
                    <td className="px-3 py-3 font-mono">{c.closest_domain || "—"}</td>
                    <td className="px-3 py-3 font-mono text-slate-400">
                      .{c.tld_signature || "?"}
                    </td>
                    <td className="px-3 py-3 font-mono text-xs text-slate-400">
                      {c.path_shape || "/"}
                    </td>
                    <td className="px-3 py-3 text-right font-semibold">
                      {c.url_count}
                    </td>
                    <td className="px-3 py-3 text-xs text-slate-400">
                      {new Date(c.first_seen).toLocaleString("th-TH")}
                    </td>
                    <td className="px-3 py-3 text-xs text-slate-400">
                      {new Date(c.last_seen).toLocaleString("th-TH")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="border-t border-slate-800 p-3 text-xs text-slate-500">
              ทั้งหมด {data.total} แคมเปญ
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
