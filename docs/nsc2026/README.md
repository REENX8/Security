# NSC 2026 — Submission Package

> เอกสารทั้งหมดสำหรับยื่นเข้าแข่งขัน
> **การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28 (NSC 2026)**
> **หมวด 23 โปรแกรมเพื่อการประยุกต์ใช้งาน · ระดับนักเรียน**

---

## ไฟล์ในชุดส่ง

| # | ไฟล์ | สำหรับรอบ | ใช้ทำอะไร |
|---|------|------------|-----------|
| 00 | `00_cover_proposal.md` | ข้อเสนอ | หน้าปกข้อเสนอ พร้อมช่องลายเซ็น |
| 01 | `01_proposal.md` | ข้อเสนอ | ข้อเสนอโครงการเต็ม 9 ส่วนตาม booklet |
| 02 | `02_full_report.md` | นำเสนอ | รายงานฉบับสมบูรณ์ |
| 03 | `03_summary_form.md` | ชิงชนะเลิศ | แบบฟอร์มสรุป 1-1.5 หน้า |
| 04 | `04_installation_guide.md` | นำเสนอ (Appendix) | คู่มือติดตั้ง |
| 05 | `05_user_guide.md` | นำเสนอ (Appendix) | คู่มือใช้งาน 6 กลุ่มผู้ใช้ |
| 06 | `06_disclaimer.txt` | นำเสนอ | ข้อตกลงใช้ซอฟต์แวร์ (ใส่ใน Readme) |
| 07 | `07_poster.md` | นำเสนอ | เนื้อหาโปสเตอร์ A1 |
| 08 | `08_video_script.md` | ชิงชนะเลิศ | สคริปต์คลิป 7 นาที |
| 09 | `09_checklist.md` | ทุกรอบ | เช็คลิสต์ก่อนส่ง |
| 10 | `10_rubric_mapping.md` | ภายในทีม | mapping rubric กับระบบ |
| 11 | `11_demo_flashcards.md` | นำเสนอ (วันสาธิต) | URL ตัวอย่าง + ลำดับการ demo + backup plan |
| 12 | `12_qa_cheatsheet.md` | นำเสนอ (วันสาธิต) | คำตอบ Q&A กรรมการ พิมพ์ A5 พกติดตัว |

---

## ขั้นตอนการเตรียมส่ง

### ขั้นที่ 1 — ก่อนเปิดระบบ SIMS

1. ตัดสินใจชื่อทีม + รายชื่อสมาชิก (สูงสุด 3 คน)
2. ขอลายเซ็นอาจารย์ที่ปรึกษาและหัวหน้าสถาบันบน `00_cover_proposal.md`
3. กรอกข้อมูลส่วนตัวให้ครบในทุกไฟล์ที่มี `___________`

### ขั้นที่ 2 — แปลง Markdown → Word/PDF

ใช้ pandoc (ฟรี, ติดตั้งบน Linux/Mac/Windows ได้):

```bash
# ติดตั้ง pandoc + Thai fonts
apt-get install pandoc fonts-thai-tlwg          # Ubuntu/Debian

# แปลงไฟล์ทั้งหมด
cd docs/nsc2026
pandoc 00_cover_proposal.md -o cover.docx --reference-doc=template.docx
pandoc 01_proposal.md       -o proposal.docx   --reference-doc=template.docx
pandoc 02_full_report.md    -o full_report.docx --reference-doc=template.docx
pandoc 03_summary_form.md   -o summary.pdf
pandoc 04_installation_guide.md -o install.pdf
pandoc 05_user_guide.md     -o user.pdf
```

> **หมายเหตุ Font:** ในไฟล์ Word ที่ส่งให้ NSC ต้องใช้ **TH Sarabun New**
> ขนาด 16 ทั้งเอกสาร — pandoc จะใช้ font default ให้เปิดใน Word แล้วเลือก
> ทั้งเอกสาร → Ctrl+A → ตั้งเป็น TH Sarabun New 16 ก่อนส่ง

### ขั้นที่ 3 — รวมเป็น ZIP submission

```bash
# จาก repo root
make nsc-bundle
# → dist/nsc2026-submission.zip ที่มี source code + เอกสารครบ
```

ใน zip จะมี:
* source code ของระบบ (excluded: .venv, node_modules, dist, __pycache__)
* `models/` (ensemble.pkl, scaler.pkl, features.json, whitelist.json)
* `docs/nsc2026/` (เอกสารทั้งหมด)
* `README.md`, `LICENSE`, `CHANGELOG.md`, `VERSION`
* รายงาน `reports/` (กราฟ + metrics)

### ขั้นที่ 4 — อัพโหลด SIMS

ตาม `09_checklist.md`

---

## โครงการนี้ผ่านเกณฑ์อย่างไร

ดู `10_rubric_mapping.md` ที่ map แต่ละข้อของ rubric ตาม booklet กับ
หลักฐานในระบบ — ทุกข้อมีหลักฐานเป็นโค้ดและเอกสารที่อ้างอิงได้

---

## ติดต่อทีมงาน

| | ผู้พัฒนา | อาจารย์ที่ปรึกษา |
|---|----------|------------------|
| ชื่อ | _____________________ | _____________________ |
| สถาบัน | _____________________ | _____________________ |
| ระดับชั้น | _____________________ | — |
| Email | _____________________ | _____________________ |
| โทรศัพท์ | _____________________ | _____________________ |
