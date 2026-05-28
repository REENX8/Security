import Layout from "../components/Layout.jsx";

export default function About() {
  return (
    <Layout title="เกี่ยวกับโครงการ / Disclaimer">
      <div className="mx-auto max-w-4xl space-y-8">
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
