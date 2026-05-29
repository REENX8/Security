import Layout from "../components/Layout.jsx";
import StatCard from "../components/StatCard.jsx";
import SevenDayChart from "../components/SevenDayChart.jsx";
import RecentTable from "../components/RecentTable.jsx";
import UrlChecker from "../components/UrlChecker.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { StatCardSkeleton } from "../components/Skeleton.jsx";
import { useStats, useHistory } from "../api/queries.js";
import { formatPct } from "../lib/format.js";

export default function Overview() {
  const { data: stats, isLoading, isError, error } = useStats();
  const { data: history } = useHistory({ limit: 10 });

  const total = stats?.total_checks ?? 0;
  const safeRate = total ? (stats.safe_count / total) : 0;

  return (
    <Layout title="ภาพรวมระบบ">
      {isError && <div className="mb-6"><ErrorBanner error={error} /></div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard title="การตรวจสอบทั้งหมด" icon="🔍"
                      value={total.toLocaleString()} accent="#3b82f6" />
            <StatCard title="พบเว็บฟิชชิง" icon="🚨"
                      value={(stats?.phishing_count ?? 0).toLocaleString()}
                      accent="#ef4444" />
            <StatCard title="เว็บน่าสงสัย" icon="⚠️"
                      value={(stats?.suspicious_count ?? 0).toLocaleString()}
                      accent="#eab308" />
            <StatCard title="อัตราปลอดภัย" icon="✅"
                      value={formatPct(safeRate)} accent="#22c55e"
                      sub={`ปลอดภัย ${(stats?.safe_count ?? 0).toLocaleString()} รายการ`} />
          </>
        )}
      </div>

      <div className="mt-6">
        <UrlChecker />
      </div>

      <div className="mt-6">
        <SevenDayChart data={stats?.checks_per_day || []} />
      </div>

      <div className="mt-6">
        <RecentTable items={history?.items || []} />
      </div>
    </Layout>
  );
}
