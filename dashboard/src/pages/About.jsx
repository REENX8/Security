import Layout from "../components/Layout.jsx";
import StatCard from "../components/StatCard.jsx";
import { useHealth } from "../api/queries.js";

const FEATURE_GROUPS = [
  { title: "โครงสร้าง URL (Lexical)", count: 21 },
  { title: "โดเมน & ทะเบียน (Domain / WHOIS)", count: 7 },
  { title: "ใบรับรอง TLS", count: 7 },
  { title: "ตัวอักษรลวง / IDN (Homoglyph)", count: 3 },
  { title: "เลียนแบบแบรนด์ (Impersonation)", count: 4 },
];

const RULES = [
  { id: "AT_TRICK", desc: "URL ใช้ '@' ซ่อนปลายทางจริง (bank.com@evil.xyz)" },
  { id: "IDN_HOMOGRAPH", desc: "Punycode + ตัวอักษรลวงใกล้แบรนด์จริง" },
  { id: "TYPOSQUAT_CRED", desc: "โดเมนพิมพ์เลียน + ขอข้อมูล login" },
  { id: "PATH_BRAND_BAIT", desc: "ชื่อแบรนด์ใน path + host ใช้ TLD ราคาถูก" },
  { id: "IP_CRED", desc: "ใช้ IP แทนโดเมน + ขอข้อมูล login" },
  { id: "CHEAP_TLD_PLAIN", desc: "TLD น่าสงสัยและไม่มี HTTPS" },
  { id: "WHITELIST_EXACT", desc: "ตรงกับ whitelist หน่วยงานที่เชื่อถือได้ (override → safe)" },
];

const STACK = [
  "FastAPI", "SQLAlchemy 2.0 (async)", "scikit-learn", "XGBoost",
  "React 18 + Vite", "Chrome MV3 Extension", "STIX 2.1 Feed", "Prometheus",
];

export default function About() {
  const { data: health } = useHealth();
  const f1 = health?.model_metrics?.test_f1;

  return (
    <Layout title="เกี่ยวกับโครงการ / Disclaimer">
      <div className="mx-auto max-w-4xl space-y-8">
        <section className="space-y-4">
          <h3 className="text-lg font-bold">สถาปัตยกรรมเชิงเทคนิค (Technical Architecture)</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard title="ฟีเจอร์ที่สกัด" value="42" accent="#3b82f6" icon="🧬"
                      sub="schema v1.5.0" />
            <StatCard title="กฎที่โปร่งใส" value="7" accent="#a855f7" icon="📜"
                      sub="Rules Engine อธิบายได้" />
            <StatCard title="Recall ฟิชชิงไทย" value="100%" accent="#22c55e" icon="🎯"
                      sub="378/378 holdout" />
            <StatCard title="F1 (ชุดทดสอบ)"
                      value={f1 != null ? Number(f1).toFixed(3) : "—"}
                      accent="#eab308" icon="📊"
                      sub={f1 != null ? "จาก /health (สด)" : "กำลังโหลด"} />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
              <div className="mb-3 text-sm font-semibold text-slate-200">
                โมเดล Ensemble — 42 ฟีเจอร์ใน 5 กลุ่ม
              </div>
              <ul className="space-y-1.5 text-sm">
                {FEATURE_GROUPS.map((g) => (
                  <li key={g.title} className="flex items-center justify-between gap-2">
                    <span className="text-slate-300">{g.title}</span>
                    <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
                      {g.count}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 text-xs text-slate-500">
                Random Forest + XGBoost (soft-voting ensemble)
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
              <div className="mb-3 text-sm font-semibold text-slate-200">
                Rules Engine — 7 กฎที่อธิบายผลได้
              </div>
              <ul className="space-y-1.5 text-sm">
                {RULES.map((r) => (
                  <li key={r.id} className="flex gap-2">
                    <code className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-blue-300">
                      {r.id}
                    </code>
                    <span className="text-xs leading-5 text-slate-400">{r.desc}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
            <div className="mb-3 text-sm font-semibold text-slate-200">เทคโนโลยีที่ใช้</div>
            <div className="flex flex-wrap gap-2">
              {STACK.map((s) => (
                <span key={s} className="rounded-full border border-slate-700 bg-slate-800/50 px-3 py-1 text-xs text-slate-300">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="mb-3 text-xl font-bold">
            ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย
          </h2>
          <p className="text-sm text-slate-300">
            Thai Public-Sector Phishing URL Detection System using Machine
            Learning with a Transparent Rules Engine
          </p>
          <dl className="mt-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-400">โครงการ</dt>
              <dd className="font-medium">
                การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28
                (NSC 2026)
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">หมวด</dt>
              <dd className="font-medium">
                23 — โปรแกรมเพื่อการประยุกต์ใช้งาน (ระดับนักเรียน)
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">ผู้สนับสนุน</dt>
              <dd className="font-medium">
                สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.)
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">License</dt>
              <dd className="font-medium">Apache License 2.0</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="mb-3 text-lg font-bold">
            ข้อตกลงในการใช้ซอฟต์แวร์ (Disclaimer)
          </h3>
          <p className="mb-4 whitespace-pre-line text-sm leading-7 text-slate-300">
            {`ซอฟต์แวร์นี้เป็นผลงานที่พัฒนาขึ้นภายใต้โครงการ "ระบบตรวจจับเว็บไซต์
ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย ด้วยการเรียนรู้ของเครื่องและ
กฎอ้างอิงที่โปร่งใส" ซึ่งสนับสนุนโดยสำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยี
แห่งชาติ (สวทช.) ในการแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28
(NSC 2026) โดยมีวัตถุประสงค์เพื่อส่งเสริมให้นักเรียนและนักศึกษาได้เรียนรู้และ
ฝึกทักษะในการพัฒนาซอฟต์แวร์

ลิขสิทธิ์ของซอฟต์แวร์นี้เป็นของผู้พัฒนา ซึ่งผู้พัฒนาได้อนุญาตให้ สวทช.
เผยแพร่ซอฟต์แวร์นี้ตาม "ต้นฉบับ" โดยไม่มีการแก้ไขดัดแปลงใด ๆ ทั้งสิ้น
ให้แก่บุคคลทั่วไปได้ใช้เพื่อประโยชน์ส่วนบุคคลหรือประโยชน์ทางการศึกษาที่ไม่มี
วัตถุประสงค์ในเชิงพาณิชย์ โดยไม่คิดค่าตอบแทนการใช้ซอฟต์แวร์

สวทช. ไม่มีหน้าที่ในการดูแล บำรุงรักษา จัดการอบรมการใช้งาน หรือพัฒนา
ประสิทธิภาพซอฟต์แวร์ รวมทั้งไม่รับรองความถูกต้องหรือประสิทธิภาพการทำงาน
ตลอดจนไม่รับประกันความเสียหายต่าง ๆ อันเกิดจากการใช้งานทั้งสิ้น`}
          </p>
          <p className="text-xs text-slate-500">
            ดูฉบับเต็มสองภาษาที่ <code>/api/v1/disclaimer</code> หรือไฟล์{" "}
            <code>LICENSE</code> ใน repository
          </p>
        </section>

        <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="mb-3 text-lg font-bold">แหล่งอ้างอิงและข้อมูลเพิ่มเติม</h3>
          <ul className="list-disc space-y-1 pl-6 text-sm text-slate-300">
            <li>
              Source code:{" "}
              <a
                href="https://github.com/reenx8/security"
                className="text-blue-400 hover:underline"
                target="_blank"
                rel="noreferrer"
              >
                github.com/reenx8/security
              </a>
            </li>
            <li>
              Public threat feed (no auth): <code>/api/v1/feed.json</code>,{" "}
              <code>/api/v1/feed.stix</code>
            </li>
            <li>
              API documentation: <code>/docs</code>
            </li>
          </ul>
        </section>
      </div>
    </Layout>
  );
}
