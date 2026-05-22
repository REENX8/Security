import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend,
} from "recharts";
import { formatDate } from "../lib/format.js";

export default function SevenDayChart({ data = [] }) {
  const chartData = data.map((d) => ({ ...d, label: formatDate(d.date) }));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        การตรวจสอบย้อนหลัง 7 วัน
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="label" stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: "#1e293b", border: "1px solid #334155",
              borderRadius: 8, color: "#e2e8f0",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="safe" name="ปลอดภัย"
                stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="suspicious" name="น่าสงสัย"
                stroke="#eab308" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="phishing" name="ฟิชชิง"
                stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
