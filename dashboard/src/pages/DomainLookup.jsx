import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Layout from "../components/Layout.jsx";
import { getDomainHistory } from "../api/client.js";

export default function DomainLookup() {
  const [host, setHost] = useState("");
  const lookup = useMutation({ mutationFn: getDomainHistory });

  return (
    <Layout title="ตรวจประวัติโดเมน">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-300">
          ดูประวัติคะแนนทุก URL ของ host ที่ระบุในระยะ 90 วันล่าสุด —
          ใช้ตรวจว่า host หนึ่งเคยถูก flag เป็นฟิชชิงไหม, score มีแนวโน้มอย่างไร, ถูกตรวจกี่ครั้ง
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="hostname (ไม่ต้องใส่ http://)"
            className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            onKeyDown={(e) => e.key === "Enter" && host.trim() && lookup.mutate(host.trim())}
          />
          <button
            onClick={() => lookup.mutate(host.trim())}
            disabled={!host.trim() || lookup.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
          >
            {lookup.isPending ? "..." : "ค้นหา"}
          </button>
        </div>

        {lookup.error && (
          <div className="rounded-lg bg-phishing/10 px-3 py-2 text-sm text-phishing">
            {lookup.error.message}
          </div>
        )}

        {lookup.data && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Card label="ตรวจทั้งหมด" value={lookup.data.total_checks} />
              <Card label="คะแนนเฉลี่ย" value={(lookup.data.mean_score * 100).toFixed(0) + "%"} />
              <Card label="คะแนนสูงสุด" value={(lookup.data.max_score * 100).toFixed(0) + "%"} />
              <Card
                label="พบครั้งแรก"
                value={new Date(lookup.data.first_seen).toLocaleDateString("th-TH")}
              />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60">
              <div className="border-b border-slate-800 p-4 font-semibold">
                Timeline รายวัน
              </div>
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-400">
                  <tr>
                    <th className="px-3 py-2">วันที่</th>
                    <th className="px-3 py-2 text-right">ตรวจ</th>
                    <th className="px-3 py-2 text-right">คะแนนเฉลี่ย</th>
                    <th className="px-3 py-2 text-right">คะแนนสูงสุด</th>
                    <th className="px-3 py-2 text-right">ปลอดภัย</th>
                    <th className="px-3 py-2 text-right">น่าสงสัย</th>
                    <th className="px-3 py-2 text-right">ฟิชชิง</th>
                  </tr>
                </thead>
                <tbody>
                  {lookup.data.timeline.map((d) => (
                    <tr key={d.date} className="border-t border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{d.date}</td>
                      <td className="px-3 py-2 text-right">{d.checks}</td>
                      <td className="px-3 py-2 text-right">{(d.avg_score * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-right">{(d.max_score * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-right text-safe">{d.safe || ""}</td>
                      <td className="px-3 py-2 text-right text-suspicious">{d.suspicious || ""}</td>
                      <td className="px-3 py-2 text-right text-phishing">{d.phishing || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60">
              <div className="border-b border-slate-800 p-4 font-semibold">
                การตรวจสอบล่าสุด
              </div>
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-400">
                  <tr>
                    <th className="px-3 py-2">URL</th>
                    <th className="px-3 py-2 text-right">คะแนน</th>
                    <th className="px-3 py-2">verdict</th>
                    <th className="px-3 py-2">เวลา</th>
                  </tr>
                </thead>
                <tbody>
                  {lookup.data.recent_urls.map((u, i) => (
                    <tr key={i} className="border-t border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{u.url}</td>
                      <td className="px-3 py-2 text-right">{(u.score * 100).toFixed(0)}%</td>
                      <td className={`px-3 py-2 text-xs ${
                        u.label === "phishing" ? "text-phishing" :
                        u.label === "suspicious" ? "text-suspicious" : "text-safe"
                      }`}>
                        {u.label}
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-400">
                        {new Date(u.checked_at).toLocaleString("th-TH")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function Card({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-bold">{value}</div>
    </div>
  );
}
