import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function LabelPie({ safe = 0, suspicious = 0, phishing = 0 }) {
  const data = [
    { name: "ปลอดภัย", value: safe, color: "#22c55e" },
    { name: "น่าสงสัย", value: suspicious, color: "#eab308" },
    { name: "ฟิชชิง", value: phishing, color: "#ef4444" },
  ].filter((d) => d.value > 0);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        สัดส่วนผลการตรวจสอบ
      </h3>
      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center text-sm text-slate-500">
          ยังไม่มีข้อมูล
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name"
                 cx="50%" cy="50%" outerRadius={100} innerRadius={55}
                 paddingAngle={3}>
              {data.map((d) => <Cell key={d.name} fill={d.color} />)}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#1e293b", border: "1px solid #334155",
                borderRadius: 8, color: "#e2e8f0",
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
