import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "ภาพรวม", icon: "📊", end: true },
  { to: "/impact", label: "ผลกระทบเชิงสังคม", icon: "🌏" },
  { to: "/bulk", label: "ตรวจหลาย URL", icon: "📦" },
  { to: "/history", label: "ประวัติการตรวจสอบ", icon: "🗂️" },
  { to: "/stats", label: "สถิติเชิงลึก", icon: "📈" },
  { to: "/campaigns", label: "แคมเปญฟิชชิง", icon: "🧩" },
  { to: "/watchlist", label: "เฝ้าระวังแบรนด์", icon: "🔔" },
  { to: "/domain", label: "ตรวจประวัติโดเมน", icon: "🔎" },
  { to: "/feed", label: "Threat Feed", icon: "📡" },
  { to: "/learn", label: "เรียนรู้เท่าทันฟิชชิง", icon: "📚" },
  { to: "/admin", label: "จัดการ Whitelist", icon: "🛡️" },
  { to: "/feedback", label: "รายงานผลผิดพลาด", icon: "🚩" },
  { to: "/report", label: "แจ้งเว็บฟิชชิง", icon: "✉️" },
  { to: "/about", label: "เกี่ยวกับ / Disclaimer", icon: "ℹ️" },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed z-30 h-full w-64 shrink-0 border-r border-slate-800 bg-slate-900
          transition-transform md:static md:translate-x-0
          ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-5">
          <img src="/shield.svg" alt="" className="h-9 w-9" />
          <div>
            <div className="text-sm font-bold leading-tight">
              Phishing Detector
            </div>
            <div className="text-xs text-slate-400">ระบบตรวจจับเว็บฟิชชิง</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition
                 ${isActive
                   ? "bg-blue-600 text-white"
                   : "text-slate-300 hover:bg-slate-800"}`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full border-t border-slate-800 p-4 text-xs text-slate-500">
          เฝ้าระวังเว็บไซต์ปลอม
          <br />หน่วยงานราชการ &amp; การศึกษาไทย
        </div>
      </aside>
    </>
  );
}
