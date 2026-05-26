# Checklist การส่ง NSC 2026 (หมวด 23 ระดับนักเรียน)

> ทำเครื่องหมาย ✅ เมื่อเสร็จแต่ละข้อ

---

## รอบที่ 1 — ข้อเสนอโครงการ (Proposal Round)

ระบบ SIMS: <https://www.nstda.or.th/sims/>

### ก่อนเปิดระบบ
- [ ] เลือก **ระดับ:** นักเรียน
- [ ] เลือก **หมวด:** 23 โปรแกรมเพื่อการประยุกต์ใช้งาน
- [ ] เตรียมข้อมูลทีม: ชื่อ-นามสกุล, สถาบัน, ระดับชั้น, email, โทรศัพท์
- [ ] เตรียมข้อมูลอาจารย์ที่ปรึกษา + ลายเซ็น (อิเล็กทรอนิกส์ได้)
- [ ] เตรียมข้อมูลหัวหน้าสถาบัน + ลายเซ็น
- [ ] อ่าน Booklet NSC 2026 ครบ — โดยเฉพาะหน้า 25–28

### ไฟล์ที่ต้องส่ง
- [ ] **ไฟล์หน้าปก** ที่มีลายเซ็นอาจารย์ที่ปรึกษา + หัวหน้าสถาบัน (PDF)
- [ ] **ไฟล์ข้อเสนอโครงการ** (PDF) ที่มีหัวข้อครบ:
  - [ ] 1. ปก
  - [ ] 2. สาระสำคัญ + Keywords
  - [ ] 3. หลักการและเหตุผล
  - [ ] 4. วัตถุประสงค์
  - [ ] 5. ปัญหา/ประโยชน์
  - [ ] 6. เป้าหมายและขอบเขต
  - [ ] 7. รายละเอียดการพัฒนา (7.1 Story Board, 7.2 เทคนิค, 7.3 เครื่องมือ, 7.4 Spec, 7.5 ขอบเขต)
  - [ ] 8. บรรณานุกรม (≥ 3 แหล่ง)
  - [ ] 9. ประวัติผลงานวิชาการของผู้พัฒนา
- [ ] Format: **TH Sarabun New ขนาด 16**, A4, margins 1 นิ้ว, ใส่เลขหน้า
- [ ] อัพโหลดผ่าน SIMS ภายในกำหนด (เช็กในระบบ)

### ความสอดคล้องกับ rubric หมวด 23

| เกณฑ์ | น้ำหนัก | กลยุทธ์ที่ใช้ |
|------|---------|----------------|
| ความสมบูรณ์ | 20 | ใช้ template `01_proposal.md` ครบทุกหัวข้อ + ใส่ภาพประกอบ + ตาราง |
| ความยากง่าย | 20 | เน้น ML ensemble + IDN/Homoglyph + Schema v1.3 + Rules Engine |
| ความคิดสร้างสรรค์ | 20 | Citizen Portal + Public Feed + Brand Watchlist (LINE) + Campaign clustering |
| ประโยชน์ใช้งาน | 25 | กลุ่มเป้าหมายชัด, /impact ที่ quantify ผล, ใช้กับผู้สูงอายุได้ |
| ความน่าจะเสร็จ | 15 | ของจริง deploy ได้แล้ว (Docker, Render), 167 tests ผ่าน |

---

## รอบที่ 2 — นำเสนอผลงาน (Presentation Round)

### ไฟล์ที่ต้องส่ง (upload SIMS ภายใน 17 ก.ค. 2569, 17:00)
- [ ] **รายงานฉบับสมบูรณ์** (PDF) — ใช้ `02_full_report.md` แปลงเป็น Word ก่อน
- [ ] **คู่มือการติดตั้ง** — ใช้ `04_installation_guide.md`
- [ ] **คู่มือการใช้งาน** — ใช้ `05_user_guide.md`
- [ ] **Disclaimer** ใน Readme หรือหน้าแรกของโปรแกรม — ใช้ `06_disclaimer.txt`
- [ ] ตรวจสอบ format: TH Sarabun New 16, A4, margin 1 นิ้ว, เลขหน้า

### ในวันนำเสนอ
- [ ] ทีมพัฒนามาเองทุกคน (NSC ไม่ให้ทำแทน)
- [ ] เตรียม Laptop ที่ติดตั้งระบบเรียบร้อย (offline-safe demo)
- [ ] เตรียม mobile hotspot สำรอง
- [ ] ซ้อมพูด 7 นาที (ตาม `08_video_script.md`)
- [ ] เตรียมโปสเตอร์ A1 — ใช้ `07_poster.md`
- [ ] แต่งกายสุภาพ
- [ ] เตรียมตอบคำถามกรรมการ (ดูส่วน Q&A ด้านล่าง)

### Rubric รอบนำเสนอ

| เกณฑ์ | น้ำหนัก | สิ่งที่กรรมการดู |
|------|---------|------------------|
| รายงาน + ติดตั้ง | 25 | ติดตั้งตามคู่มือได้ + รายงานครบ |
| Look & Feel | 15 | UI ของ dashboard + extension |
| Technique | 15 | depth ของ ML / rules engine |
| Creativity | 20 | citizen portal + open feed + LINE webhook |
| Economic + Social Impact | 20 | กลุ่มเป้าหมายชัด + /impact quantify |
| Presentation | 5 | พูดชัด ตอบคำถามได้ |

---

## รอบที่ 3 — ชิงชนะเลิศ (Final, 21 ส.ค. 2569 online)

- [ ] **คลิป 7 นาที** (`.mp4`) — ตั้งชื่อตามรหัสโครงการ เช่น `28p23c0001.mp4`
- [ ] **แบบฟอร์มสรุป** (1-1.5 หน้า, PDF) — ใช้ `03_summary_form.md`
- [ ] **ภาพทีมพัฒนา + อาจารย์** (ไฟล์ภาพ คมชัด, แต่งกายสุภาพ)
- [ ] อัพเดทรายงานฉบับสมบูรณ์ถ้ามีการปรับ
- [ ] ซ้อมการตอบคำถามแบบ online — เช็คกล้อง/ไมค์/แสง

---

## Q&A ที่กรรมการน่าจะถาม

| คำถาม | คำตอบที่เตรียมไว้ |
|------|---------------------|
| "คุณทำเองไหม หรือ AI ทำให้?" | บอกความจริง — ผมออกแบบ architecture เอง, AI เป็นเครื่องมือช่วย coding บางส่วน (ทุกคน student ใช้กัน) แต่ design decision, feature engineering, evaluation framework, holdout strategy, rules engine ทั้งหมดเป็นของผม |
| "ทำไม recall ถึงไม่ 100% บน generic phishing?" | ระบบออกแบบมาจับ Thai-targeting โดยเฉพาะ generic เป็น cross-check; alignment_score = +5.9 percentage points คือสิ่งที่ออกแบบไว้ |
| "ใช้กับเด็กประถมได้ไหม?" | ติดตั้ง extension ครั้งเดียว แล้วใช้งานปกติเลย, citizen portal ก็มี UI ง่าย, /learn มี content ที่อ่านง่าย |
| "ค่าใช้จ่ายในการรัน production?" | ใช้ Render free tier ได้ (~$0/เดือน demo), production scale 100k checks/วันใช้ ~$10-20/เดือน |
| "ข้อมูลส่วนตัวของผู้ใช้ไป?" | URL ไป backend อย่างเดียว, ไม่มี cookies/credentials, dashboard URL จริงไม่เก็บ form data (ดู extension/PRIVACY.md) |
| "ถ้า model มี bias ต่อโดเมนใหม่ของจริงที่เพิ่ง register?" | feature `domain_age_days` ใช้ + safety net `WHITELIST_EXACT` rule + feedback loop รับแจ้ง false positive |
| "ทำไมไม่ใช้ pre-trained model (BERT, GPT)?" | URL detection ต้องการ inference เร็ว (<300ms ต่อ check) + deploy on cheap VPS, transformer ใช้ resource เยอะเกิน + lexical features ให้ผลดีกว่าใน domain นี้ |

---

## หลังการแข่งขัน (ไม่ว่าผลจะเป็นอย่างไร)

- [ ] ขอบคุณอาจารย์ที่ปรึกษาและสถาบัน
- [ ] เก็บ feedback จากกรรมการ
- [ ] อัพเดท README + CHANGELOG ของ project
- [ ] เผยแพร่ผลให้ชุมชน (FB กลุ่ม NSC Thailand)
- [ ] ถ้าได้รับเงินรางวัล — ใช้พัฒนาต่อยอด (Roadmap ในรายงาน)
