# Q&A Cheat Sheet — รอบนำเสนอ NSC 2026

> พิมพ์หน้าเดียว A5 พกติดมือตอนตอบกรรมการ — แต่ละข้อมีคำตอบ 1-2 ประโยค
> และ "หลักฐาน" ที่ชี้ให้ดูได้

---

## เรื่องการพัฒนา

**Q: ทำเองทั้งหมดเลยไหม หรือใช้ AI ช่วย?**
→ ผมออกแบบ architecture เอง: feature schema v1.5.0, rules engine, IDN
defense, campaign clustering, evaluation framework AI เป็นเครื่องมือช่วย
type code บางส่วน แต่ทุก design decision (เลือก ensemble vs single,
schema fields, rule thresholds, fingerprint formula) ตัดสินใจเอง
**หลักฐาน:** CHANGELOG.md (decision log), commit history, scripts ที่ลายมือเฉพาะตัว

**Q: ทำไมไม่ใช้ BERT / GPT?**
→ Inference latency ต้อง < 250 ms p95, รันบน 1 vCPU / 1 GB RAM ได้
Transformer ต้องการ GPU + RAM สูง ไม่คุ้ม URL detection ใช้ lexical features
ก็ให้ผลดี (recall 100% บน Thai holdout)

**Q: ทำไม recall บน generic phishing ถึงต่ำกว่า Thai holdout?**
→ ตั้งใจ — ระบบนี้ออกแบบเพื่อ Thai-targeting โดยเฉพาะ (alignment score เป็นบวก)
generic เป็นเพียง cross-check ทางเลือก และ**ผันผวนสูงตาม snapshot ของ feed**
(วัดบน OpenPhish คนละวันได้ค่าต่างกันมาก) จึงไม่ผูกเป็นตัวเลขตายตัวในเอกสาร —
วัดสำหรับโมเดลปัจจุบันได้ด้วย `make evaluate` ที่เข้าถึง live feed ได้

---

## เรื่องโมเดล / Data

**Q: 12,000 rows ที่ใช้ฝึก = synthetic ใช่ไหม Bias ไหม?**
→ ใช่ synthetic แต่ anchored กับ Thai brand list 500+ โดเมนจริง การประเมิน
ใช้ holdout **378 URL จริง** ที่โมเดลไม่เคยเห็น ไม่ได้ใช้ synthetic วัด

**Q: ถ้า model มี false positive บนโดเมนใหม่ที่เพิ่ง register?**
→ Feature `domain_age_days` ลด score สำหรับโดเมนเก่า + Rules Engine มี
`WHITELIST_EXACT` pin safe + Citizen Portal รับแจ้ง FP → feedback retrain

**Q: ทำไมต้องมี Rules Engine ในเมื่อมี ML แล้ว?**
→ 3 เหตุผล: (1) Transparency — กรรมการบอกได้ว่า rule_id ใดทำงาน (2)
override โดยไม่ retrain (3) จับ pattern ที่ ML ขี้เกียจ เช่น `@-trick`
ที่เกิดน้อยใน data

---

## เรื่องการใช้งานจริง

**Q: ค่าใช้จ่ายในการรัน production?**
→ Render free tier $0/เดือนสำหรับ demo, production ขนาด 100k checks/วัน
~$10-20/เดือน CPU-only ไม่ต้อง GPU

**Q: เก็บข้อมูลส่วนตัวผู้ใช้ไหม?**
→ Extension ส่งแค่ URL ไม่มี cookies / form data / credentials
ดู `extension/PRIVACY.md` + Citizen Portal no-login

**Q: ผู้สูงอายุใช้เองได้ไหม?**
→ Extension ติดตั้งครั้งเดียว แล้วเตือนเต็มจอ — ไม่ต้องตั้งค่า เนื้อหา
`/learn` 4 ระดับ มีฉบับ "อ่านง่าย" สำหรับผู้ใช้กลุ่มนี้

---

## เรื่อง Creativity

**Q: LINE Bot ต่างจาก Brand Watchlist + LINE Notify อย่างไร?**
→ Watchlist + Notify = แจ้งเตือน **หน่วยงาน** เมื่อพบฟิชชิงปลอมแบรนด์ตน
LINE Messaging Bot = ให้ **ประชาชนทั่วไป** พิมพ์ URL ตรวจใน LINE chat
ไม่ต้องติดตั้งอะไร

**Q: URL Unshortening ทำงานอย่างไร?**
→ Async HEAD request ไปที่ short link → ดู `Location` header → ใช้
URL ปลายทางในการตรวจ ถ้าไม่รู้จัก provider ก็ข้าม (fail-open) มี timeout 5s

**Q: STIX 2.1 ต่างจาก JSON / CSV feed อย่างไร?**
→ STIX 2.1 เป็นมาตรฐาน OASIS สำหรับ threat intelligence — SIEM ของ
หน่วยงาน (Splunk, Elastic, Sentinel) parse ได้ทันทีโดยไม่ต้องเขียน
custom parser

---

## เรื่อง Impact / Sustainability

**Q: วัด Impact อย่างไร?**
→ `/api/v1/impact` คำนวณ ฿7,800 (median ETDA 2024) × blocked count เป็น
public JSON เรียลไทม์ ใครก็เรียกได้

**Q: Sustainable Innovation ของระบบนี้คืออะไร?**
→ 4 มิติ: Social (no-login portal สำหรับเปราะบาง), Economic (quantified
loss prevention), Environmental (CPU-only, low-resource), Open (Apache
2.0 + dataset เปิด + STIX feed)

**Q: ขยายผลอย่างไรในอนาคต?**
→ Fork repository → ปรับ whitelist ของหน่วยงานตน → deploy Render free
tier — ไม่ต้องจ่ายเงินซื้อ license ต่อเดือน

---

## เรื่องเทคนิคลึก (เผื่อกรรมการเจาะ)

**Q: ทำไมเลือก RF + XGB ไม่ใช่ deep learning?**
→ RF จับ non-linear interaction ดี, XGB จับ tail (rare patterns) ดี Soft
voting ลด variance, Isotonic calibration ทำให้ score มี meaning เป็น
probability จริง

**Q: Homoglyph defense ทำงานอย่างไร?**
→ (1) Punycode decode (xn-- → Unicode) (2) Unicode confusable fold ตาม
TR36 (`а` Cyrillic → `a` Latin) (3) Levenshtein distance กับ whitelist
หลัง fold

**Q: Campaign fingerprint คำนวณอย่างไร?**
→ `{brand}|{tld}|{path-shape}` โดย path-shape คือเปลี่ยน digit → `#`,
hex 8+ chars → `$hex` URL ที่มี fingerprint เดียวกัน = campaign เดียวกัน

---

## 🎯 ประโยคปิดทุกการตอบ

> "และนี่เป็นเหตุผลที่ผมเลือก approach นี้ ตามที่อ้างใน [ที่ X ของรายงาน]"
