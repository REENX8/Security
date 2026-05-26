import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Layout from "../components/Layout.jsx";
import {
  getWatchlist, addWatchlistEntry, deleteWatchlistEntry,
  getWebhookDeliveries,
} from "../api/client.js";

export default function Watchlist() {
  const qc = useQueryClient();
  const [brand, setBrand] = useState("");
  const [description, setDescription] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [showDeliveries, setShowDeliveries] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["watchlist"],
    queryFn: getWatchlist,
    refetchInterval: 30_000,
  });

  const add = useMutation({
    mutationFn: addWatchlistEntry,
    onSuccess: () => {
      setBrand(""); setDescription(""); setWebhookUrl("");
      qc.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  const remove = useMutation({
    mutationFn: deleteWatchlistEntry,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });

  const { data: deliveries } = useQuery({
    queryKey: ["webhook-deliveries"],
    queryFn: () => getWebhookDeliveries({ limit: 50 }),
    enabled: showDeliveries,
    refetchInterval: 15_000,
  });

  return (
    <Layout title="เฝ้าระวังแบรนด์">
      <div className="space-y-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-300">
          <div className="mb-1 text-base font-semibold text-slate-100">
            แจ้งเตือนทันทีเมื่อมีคนปลอมแบรนด์ที่คุณเฝ้าระวัง
          </div>
          ลงทะเบียน <b>คำสำคัญแบรนด์</b> (เช่น <code>obec</code>, <code>krungthai</code>)
          และ <b>URL webhook</b> — เมื่อระบบเจอ URL ฟิชชิงที่ปลอมแบรนด์นั้น
          จะ POST ข้อมูล (URL, score, reason) ไปยัง webhook ของคุณภายในไม่กี่วินาที
          ใช้ต่อกับ Slack / Line / SOAR / SIEM ของคุณได้
        </div>

        <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="text-base font-semibold">เพิ่มแบรนด์</div>
          <div className="grid gap-3 md:grid-cols-3">
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="brand (เช่น obec)"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="คำอธิบาย"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={() => add.mutate({
              brand: brand.trim().toLowerCase(),
              description,
              webhook_url: webhookUrl || null,
              enabled: true,
            })}
            disabled={!brand.trim() || add.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
          >
            {add.isPending ? "กำลังเพิ่ม..." : "เพิ่ม"}
          </button>
          {add.error && (
            <div className="text-sm text-phishing">{add.error.message}</div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 p-4 text-base font-semibold">
            แบรนด์ที่เฝ้าระวัง
          </div>
          {isLoading && <div className="p-4 text-slate-400">กำลังโหลด...</div>}
          {data && data.items.length === 0 && (
            <div className="p-4 text-slate-500">ยังไม่มีแบรนด์ในรายการ</div>
          )}
          {data && data.items.length > 0 && (
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-left text-xs text-slate-400">
                <tr>
                  <th className="px-3 py-3">แบรนด์</th>
                  <th className="px-3 py-3">คำอธิบาย</th>
                  <th className="px-3 py-3">Webhook</th>
                  <th className="px-3 py-3 text-right">จำนวนครั้งที่ตรง</th>
                  <th className="px-3 py-3">ครั้งล่าสุด</th>
                  <th className="px-3 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr key={row.id} className="border-t border-slate-800">
                    <td className="px-3 py-3 font-mono">{row.brand}</td>
                    <td className="px-3 py-3 text-slate-400">{row.description}</td>
                    <td className="px-3 py-3 font-mono text-xs text-slate-400">
                      {row.webhook_url
                        ? row.webhook_url.slice(0, 32) + (row.webhook_url.length > 32 ? "…" : "")
                        : "—"}
                    </td>
                    <td className="px-3 py-3 text-right">{row.hit_count}</td>
                    <td className="px-3 py-3 text-xs text-slate-400">
                      {row.last_hit_at
                        ? new Date(row.last_hit_at).toLocaleString("th-TH")
                        : "—"}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        onClick={() => remove.mutate(row.brand)}
                        className="rounded-lg bg-phishing/20 px-3 py-1 text-xs text-phishing hover:bg-phishing/30"
                      >
                        ลบ
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <button
            onClick={() => setShowDeliveries(!showDeliveries)}
            className="text-sm font-medium text-blue-400 hover:text-blue-300"
          >
            {showDeliveries ? "▼" : "▶"} ดูประวัติการส่ง webhook
          </button>
          {showDeliveries && deliveries && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-slate-400">
                  <tr>
                    <th className="px-3 py-2">เวลา</th>
                    <th className="px-3 py-2">แบรนด์</th>
                    <th className="px-3 py-2">URL ที่ตรวจ</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.items.map((d) => (
                    <tr key={d.id} className="border-t border-slate-800">
                      <td className="px-3 py-2 text-xs text-slate-400">
                        {new Date(d.created_at).toLocaleString("th-TH")}
                      </td>
                      <td className="px-3 py-2 font-mono">{d.brand}</td>
                      <td className="px-3 py-2 font-mono text-xs text-slate-400">
                        {d.url_checked.slice(0, 60)}
                      </td>
                      <td className="px-3 py-2 font-mono">
                        {d.error
                          ? <span className="text-phishing">ERR: {d.error.slice(0, 30)}</span>
                          : <span className="text-safe">{d.status_code}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}
