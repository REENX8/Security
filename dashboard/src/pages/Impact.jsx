import { useState } from "react";
import Layout from "../components/Layout.jsx";
import StatCard from "../components/StatCard.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { StatCardSkeleton } from "../components/Skeleton.jsx";
import { useImpact } from "../api/queries.js";

const WINDOWS = [
  { days: 30, label: "30 วัน" },
  { days: 90, label: "90 วัน" },
  { days: 365, label: "1 ปี" },
];

const PILLARS = [
  { key: "social", title: "สังคม (Social)", icon: "🤝", accent: "#22c55e" },
  { key: "economic", title: "เศรษฐกิจ (Economic)", icon: "💰", accent: "#eab308" },
  { key: "environmental", title: "สิ่งแวดล้อม (Environmental)", icon: "🌱", accent: "#10b981" },
  { key: "openness", title: "การเปิดกว้าง (Openness)", icon: "🔓", accent: "#3b82f6" },
];

function thb(n) {
  return `฿${Number(n || 0).toLocaleString("th-TH")}`;
}

export default function Impact() {
  const [windowDays, setWindowDays] = useState(30);
  const { data, isLoading, isError, error } = useImpact(windowDays);

  return (
    <Layout title="ผลกระทบเชิงสังคมและเศรษฐกิจ">
      {isError && <div className="mb-6"><ErrorBanner error={error} /></div>}

      {/* hero: estimated loss prevented */}
      <div className="rounded-2xl border border-emerald-700/40 bg-gradient-to-br from-emerald-900/30 to-slate-900 p-6 md:p-8">
        <div className="text-sm text-emerald-300">
          มูลค่าความเสียหายที่ป้องกันได้โดยประมาณ (ช่วง {windowDays} วัน)
        </div>
        {isLoading ? (
          <div className="mt-2 h-12 w-64 animate-pulse rounded-md bg-slate-800/70" />
        ) : (
          <div className="mt-2 text-4xl font-extrabold text-emerald-400 md:text-5xl">
            {thb(data?.estimated_thb_loss_prevented)}
          </div>
        )}
        <p className="mt-3 max-w-3xl text-xs leading-relaxed text-slate-400">
          {data?.estimated_thb_loss_prevented_note ||
            "คำนวณจากจำนวน URL ฟิชชิงที่ตรวจพบ × ความเสียหายเฉลี่ยต่อเหตุการณ์"}
        </p>

        <div className="mt-4 flex gap-2">
          {WINDOWS.map((w) => (
            <button
              key={w.days}
              onClick={() => setWindowDays(w.days)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${
                windowDays === w.days
                  ? "bg-emerald-600 text-white"
                  : "border border-slate-700 text-slate-300 hover:bg-slate-800"
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {/* core counts */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard title="URL ฟิชชิงที่บล็อก" icon="🚨"
                      value={(data?.phishing_blocked ?? 0).toLocaleString()} accent="#ef4444" />
            <StatCard title="เว็บน่าสงสัยที่เตือน" icon="⚠️"
                      value={(data?.suspicious_warned ?? 0).toLocaleString()} accent="#eab308" />
            <StatCard title="โดเมนผู้โจมตี (distinct)" icon="🎯"
                      value={(data?.unique_attackers ?? 0).toLocaleString()} accent="#f97316" />
            <StatCard title="แบรนด์ที่เฝ้าระวัง" icon="🛡️"
                      value={(data?.brands_protected ?? 0).toLocaleString()} accent="#3b82f6" />
            <StatCard title="แคมเปญที่ระบุได้" icon="🧩"
                      value={(data?.campaigns_identified ?? 0).toLocaleString()} accent="#a855f7" />
            <StatCard title="ประชาชนที่ร่วมแจ้งเบาะแส" icon="🙋"
                      value={(data?.citizens_who_reported ?? 0).toLocaleString()} accent="#22c55e" />
          </>
        )}
      </div>

      {/* sustainability pillars */}
      <h2 className="mb-3 mt-8 text-base font-bold text-slate-200">
        นวัตกรรมเพื่อความยั่งยืน (Sustainable Innovation) — 4 มิติ
      </h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {PILLARS.map((p) => (
          <div key={p.key}
               className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <div className="flex items-center gap-2 text-sm font-semibold"
                 style={{ color: p.accent }}>
              <span className="text-lg">{p.icon}</span>{p.title}
            </div>
            {isLoading ? (
              <div className="mt-3 h-16 w-full animate-pulse rounded-md bg-slate-800/70" />
            ) : (
              <p className="mt-2 text-sm leading-relaxed text-slate-300">
                {data?.sustainability_pillars?.[p.key] || "—"}
              </p>
            )}
          </div>
        ))}
      </div>

      {data?.generated_at && (
        <p className="mt-6 text-xs text-slate-600">
          ข้อมูลคำนวณสด ณ {new Date(data.generated_at).toLocaleString("th-TH")}
          {" · "}schema {data.schema_ || data["schema_"] || "phish.impact.v1"}
        </p>
      )}
    </Layout>
  );
}
