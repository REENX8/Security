# แบบฟอร์มสรุปข้อมูลโครงการ (1–1.5 หน้า A4)

> ใช้สำหรับรอบชิงชนะเลิศ NSC 2026 ตาม Booklet หน้า 32–33
> ขนาดตัวอักษร 14–16 · บันทึกชื่อด้วย รหัสโครงการ.pdf เช่น `28p23c0001.pdf`

---

**ชื่อโครงการ (ไทย):** ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย ด้วยการเรียนรู้ของเครื่องและกฎอ้างอิงที่โปร่งใส

**ชื่อโครงการ (อังกฤษ):** Thai Public-Sector Phishing URL Detection System using Machine Learning with a Transparent Rules Engine

**หมวด:** 23 โปรแกรมเพื่อการประยุกต์ใช้งาน · **ระดับ:** นักเรียน

**ทีมพัฒนา:** ___________________ · **อาจารย์ที่ปรึกษา:** ___________________ · **สถาบัน:** ___________________

---

### ความเป็นมา/ปัญหา

ETDA รายงานว่าปี 2567 ประชาชนไทยถูกหลอกผ่าน URL ฟิชชิงที่ปลอมหน่วยงาน
ราชการกว่า 30,000 เคส ความเสียหายเฉลี่ย 5,000–10,000 บาท/คน ระบบ
ป้องกัน global พลาด URL ปลอมแบรนด์ไทยเพราะไม่มี whitelist และข้อมูล
training เฉพาะของไทย

### สิ่งที่ทำ

แพลตฟอร์ม **end-to-end** ที่จับ URL ฟิชชิงเลียนแบบแบรนด์ไทย ประกอบด้วย
**5 ส่วนทำงานร่วมกัน:** (1) ML ensemble RF+XGB บน **37 features** v1.4.0
รวม IDN/Homoglyph + Path-impersonation + Lexical patterns ใหม่ (2) FastAPI backend พร้อม
**Rules Engine โปร่งใส** (3) **Brand Watchlist + Webhook** (LINE/Slack)
(4) **Campaign Clustering** จับ kit เดียวกัน (5) **Public Threat Feed**
STIX 2.1 (no auth) + **Citizen Report Portal** ไม่ต้อง login

### จุดเด่น (Creativity + Technique)

* **Schema v1.4.0**: เพิ่ม 4 features ใหม่ล่าสุดที่คำนวณจาก URL string ล้วน —
  `num_login_keywords` (count), `query_param_count`, `path_entropy`,
  `host_token_count` — ทำให้ Thai recall คงอยู่ที่ **100%** บน holdout 66 URL
* **IDN/Homoglyph defense**: decode Punycode + fold Unicode confusables
  จับ `chulа.com` (Cyrillic) และ `xn--rd-yia.com` ได้
* **Rules Engine**: ทุก verdict แสดง `rule_id` ที่ทำงาน — โปร่งใส, ตรวจสอบได้,
  override ML ได้โดยไม่ต้อง retrain
* **Public Threat Feed** STIX 2.1 + Citizen Report Portal — ไม่ต้อง API key
  ใครก็เอาไปใช้ต่อ ใครก็แจ้งเว็บปลอมได้

### ความแม่นยำ

* **Thai-targeting holdout (66 URL ที่โมเดลไม่เคยเห็น):** recall **100% (66/66)**
  ที่ threshold ≥ 0.7
* **Generic phishing holdout (90 URL):** recall **98.9% (89/90)**
* **CI gate ≥ 0.85** — automated, fail build ถ้า regress
* **206 automated tests** ผ่านทั้งหมด

### ประโยชน์ (Sustainable Innovation)

| มิติ | ประโยชน์ |
|------|----------|
| **Social** | ปกป้องคนไทยกลุ่มเปราะบาง — extension + portal ฟรี, ไม่ต้อง login |
| **Economic** | `/api/v1/impact` คำนวณยอดเสียหายที่ป้องกันได้ × ฿7,800/case ของ ETDA |
| **Environmental** | low-resource (ไม่ต้องการ GPU), single-binary deploy |
| **Open** | Apache 2.0 + STIX feed + dataset committed in repo |

### กลุ่มผู้ใช้

ประชาชน · ผู้สูงอายุ · ครู/อาจารย์ · ฝ่าย IT หน่วยงานราชการ · นักวิจัย security · SOC

### เทคโนโลยี

scikit-learn 1.5 · XGBoost 2.1 · FastAPI 0.115 · SQLAlchemy 2.0 async ·
PostgreSQL 16 · React 18 · Vite 5 · TailwindCSS · Chrome Manifest V3 ·
Docker · STIX 2.1

### ลิงก์โครงการ / source code

* Repository: https://github.com/reenx8/security
* Live demo: (ระบุ URL ของ deployment, ถ้ามี)
* คลิปแนะนำ: (ระบุ YouTube link หลังอัด)

---

**ผู้พัฒนา:** REENX8 · **email:** asdawesdzd22@gmail.com · **GitHub:** https://github.com/reenx8/security
