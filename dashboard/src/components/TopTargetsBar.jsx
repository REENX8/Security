import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

export default function TopTargetsBar({ data = [] }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        โดเมนทางการที่ถูกแอบอ้างมากที่สุด
      </h3>
      {data.length === 0 ? (
        <Empty />
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} layout="vertical"
                    margin={{ left: 24, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" stroke="#64748b" fontSize={12}
                   allowDecimals={false} />
            <YAxis type="category" dataKey="domain" stroke="#64748b"
                   fontSize={11} width={120} />
            <Tooltip
              cursor={{ fill: "#1e293b" }}
              contentStyle={{
                background: "#1e293b", border: "1px solid #334155",
                borderRadius: 8, color: "#e2e8f0",
              }}
            />
            <Bar dataKey="count" name="จำนวนครั้ง" fill="#ef4444"
                 radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function Empty() {
  return (
    <div className="flex h-[320px] items-center justify-center text-sm text-slate-500">
      ยังไม่มีข้อมูลโดเมนที่ถูกแอบอ้าง
    </div>
  );
}
