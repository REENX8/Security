import Layout from "../components/Layout.jsx";
import TopTargetsBar from "../components/TopTargetsBar.jsx";
import LabelPie from "../components/LabelPie.jsx";
import HourHeatmap from "../components/HourHeatmap.jsx";
import StatCard from "../components/StatCard.jsx";
import { useStats } from "../api/queries.js";
import { formatPct } from "../lib/format.js";

export default function Stats() {
  const { data: stats, isError, error } = useStats();

  return (
    <Layout title="สถิติเชิงลึก">
      {isError && (
        <div className="mb-6 rounded-lg border border-phishing/40 bg-phishing/10 px-4 py-3 text-sm text-phishing">
          ไม่สามารถเชื่อมต่อ API ได้: {error.message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard title="อัตราการพบภัยคุกคาม" icon="📛"
                  value={formatPct(stats?.phishing_rate ?? 0)}
                  accent="#ef4444"
                  sub="ฟิชชิง + น่าสงสัย ต่อการตรวจทั้งหมด" />
        <StatCard title="โดเมนที่ถูกแอบอ้าง" icon="🎯"
                  value={(stats?.top_flagged_domains?.length ?? 0)}
                  accent="#eab308" sub="จำนวนโดเมนทางการที่พบการเลียนแบบ" />
        <StatCard title="การตรวจสอบทั้งหมด" icon="🔍"
                  value={(stats?.total_checks ?? 0).toLocaleString()}
                  accent="#3b82f6" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TopTargetsBar data={stats?.top_flagged_domains || []} />
        <LabelPie
          safe={stats?.safe_count || 0}
          suspicious={stats?.suspicious_count || 0}
          phishing={stats?.phishing_count || 0}
        />
      </div>

      <div className="mt-6">
        <HourHeatmap data={stats?.checks_by_hour || []} />
      </div>
    </Layout>
  );
}
