// 24-hour activity heatmap.

export default function HourHeatmap({ data = [] }) {
  const counts = Array.from({ length: 24 }, (_, h) => {
    const found = data.find((d) => d.hour === h);
    return found ? found.count : 0;
  });
  const max = Math.max(1, ...counts);

  const cellColor = (count) => {
    if (count === 0) return "#1e293b";
    const t = count / max; // 0..1
    // interpolate slate -> blue -> red
    const r = Math.round(59 + t * (239 - 59));
    const g = Math.round(130 - t * (130 - 68));
    const b = Math.round(246 - t * (246 - 68));
    return `rgb(${r}, ${g}, ${b})`;
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        ความถี่การตรวจสอบตามช่วงเวลา (24 ชม.)
      </h3>
      <div className="grid grid-cols-12 gap-1.5">
        {counts.map((count, h) => (
          <div key={h} className="text-center">
            <div
              className="aspect-square rounded-md transition hover:ring-2 hover:ring-blue-400"
              style={{ background: cellColor(count) }}
              title={`${h}:00 — ${count} ครั้ง`}
            />
            <div className="mt-1 text-[10px] text-slate-500">{h}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
        <span>น้อย</span>
        <div className="flex gap-1">
          {[0, 0.25, 0.5, 0.75, 1].map((t) => (
            <div key={t} className="h-3 w-6 rounded"
                 style={{ background: cellColor(t * max) }} />
          ))}
        </div>
        <span>มาก</span>
      </div>
    </div>
  );
}
