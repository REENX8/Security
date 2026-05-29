import { useState } from "react";
import Sidebar from "./Sidebar.jsx";
import { useHealth } from "../api/queries.js";

export default function Layout({ title, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: health } = useHealth();

  return (
    <div className="flex h-full">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900/60 px-4 py-3 md:px-8">
          <div className="flex items-center gap-3">
            <button
              className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 md:hidden"
              onClick={() => setSidebarOpen(true)}
              aria-label="เมนู"
            >
              ☰
            </button>
            <h1 className="text-lg font-bold md:text-xl">{title}</h1>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {health?.schema_version && (
              <span className="hidden rounded-full border border-slate-700 px-2.5 py-1 font-mono text-[11px] text-slate-400 sm:inline">
                schema {health.schema_version}
                {health.model_metrics?.test_f1 != null &&
                  ` · F1 ${Number(health.model_metrics.test_f1).toFixed(3)}`}
              </span>
            )}
            <span className="flex items-center gap-2">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  health?.model_ready ? "bg-safe" : "bg-phishing"
                }`}
              />
              <span className="text-slate-400">
                {health?.model_ready ? "โมเดลพร้อมใช้งาน" : "โมเดลไม่พร้อม"}
              </span>
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
