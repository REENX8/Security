export default function StatCard({ title, value, accent = "#3b82f6", icon, sub }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-start justify-between">
        <span className="text-sm text-slate-400">{title}</span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className="mt-2 text-3xl font-extrabold" style={{ color: accent }}>
        {value}
      </div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}
