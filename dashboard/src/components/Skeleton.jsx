// Lightweight loading placeholders that match the shape of the content they
// replace, so the dashboard never shows a blank flash during a live demo.

export function Skeleton({ className = "" }) {
  return <div className={`animate-pulse rounded-md bg-slate-800/70 ${className}`} />;
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-3 h-8 w-20" />
    </div>
  );
}

export function CardSkeleton({ rows = 4 }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <Skeleton className="mb-4 h-4 w-40" />
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    </div>
  );
}
