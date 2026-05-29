import { useState } from "react";
import Layout from "../components/Layout.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { CardSkeleton } from "../components/Skeleton.jsx";
import { useLearn } from "../api/queries.js";

const AUDIENCES = [
  { key: "", label: "ทั้งหมด" },
  { key: "general", label: "ประชาชนทั่วไป" },
  { key: "elderly", label: "ผู้สูงอายุ" },
  { key: "student", label: "นักเรียน/นักศึกษา" },
  { key: "public-servant", label: "หน่วยงานราชการ" },
];

export default function Learn() {
  const [audience, setAudience] = useState("");
  const { data, isLoading, isError, error } = useLearn(audience);
  const cards = data?.cards || [];

  return (
    <Layout title="เรียนรู้เท่าทันฟิชชิง">
      <div className="mb-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-300">
        เนื้อหาให้ความรู้ภาษาไทยแบบสั้น อ้างอิงจาก ETDA / ThaiCERT —
        เปลี่ยนระบบตรวจจับให้เป็น <b>การปรับพฤติกรรมระยะยาว</b> ไม่ใช่แค่เครื่องมือกัน
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {AUDIENCES.map((a) => (
          <button
            key={a.key || "all"}
            onClick={() => setAudience(a.key)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${
              audience === a.key
                ? "bg-blue-600 text-white"
                : "border border-slate-700 text-slate-300 hover:bg-slate-800"
            }`}
          >
            {a.label}
          </button>
        ))}
      </div>

      {isError && <ErrorBanner error={error} />}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <CardSkeleton /><CardSkeleton />
        </div>
      ) : cards.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-500">
          ยังไม่มีเนื้อหาสำหรับกลุ่มนี้
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {cards.map((c) => (
            <article key={c.id}
                     className="flex flex-col rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-bold text-slate-100">{c.title}</h3>
                <span className="shrink-0 rounded-full bg-slate-800 px-2 py-0.5 text-[11px] text-slate-400">
                  {c.duration_minutes} นาที
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{c.body_th}</p>
              {c.actions_th?.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {c.actions_th.map((a, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-300">
                      <span className="text-safe">✓</span>{a}
                    </li>
                  ))}
                </ul>
              )}
              {c.sources?.length > 0 && (
                <div className="mt-3 border-t border-slate-800 pt-2 text-[11px] text-slate-500">
                  ที่มา: {c.sources.join(" · ")}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </Layout>
  );
}
