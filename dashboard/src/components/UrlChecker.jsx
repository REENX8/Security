import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useCheckUrl } from "../api/queries.js";
import LabelBadge from "./LabelBadge.jsx";
import RulesPanel from "./RulesPanel.jsx";
import { formatPct, labelInfo } from "../lib/format.js";

export default function UrlChecker() {
  const [url, setUrl] = useState("");
  const checkMutation = useCheckUrl();
  const queryClient = useQueryClient();

  const submit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    checkMutation.mutate(url.trim(), {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["stats"] });
        queryClient.invalidateQueries({ queryKey: ["history"] });
      },
    });
  };

  const result = checkMutation.data;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">
        ตรวจสอบ URL ด้วยตนเอง
      </h3>
      <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.go.th/login"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2
                     text-sm outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={checkMutation.isPending}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold
                     text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {checkMutation.isPending ? "กำลังตรวจ..." : "ตรวจสอบ"}
        </button>
      </form>

      {checkMutation.isError && (
        <p className="mt-3 text-sm text-phishing">
          เกิดข้อผิดพลาด: {checkMutation.error.message}
        </p>
      )}

      {result && (
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950 p-4">
          <div className="flex items-center justify-between">
            <LabelBadge label={result.label} />
            <span
              className="text-2xl font-extrabold"
              style={{ color: labelInfo(result.label).color }}
            >
              {formatPct(result.score)}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.round(result.score * 100)}%`,
                background: labelInfo(result.label).color,
              }}
            />
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-300">
            {result.reason}
          </p>
          {result.closest_domain && (
            <p className="mt-2 text-xs text-slate-500">
              โดเมนที่ใกล้เคียง: {result.closest_domain}
              {result.edit_distance != null &&
                ` (edit distance: ${result.edit_distance})`}
            </p>
          )}

          <div className="mt-4">
            <RulesPanel
              rules={result.rules}
              mlScore={result.ml_score}
              finalScore={result.score}
            />
          </div>
        </div>
      )}
    </div>
  );
}
