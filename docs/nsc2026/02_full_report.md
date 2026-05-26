# รายงานฉบับสมบูรณ์ — NSC 2026 หมวด 23 ระดับนักเรียน

> สำหรับใช้ส่งในรอบนำเสนอผลงาน — ตามรูปแบบ NSC 2026 Booklet หน้า 29–30

---

## หน้าปก (Cover)

ตามตัวอย่าง NSC 2026 Booklet หน้า 43:

<center>

**รหัสโครงการ:** _______________

# (ชื่อโครงการภาษาไทย)
### *(ชื่อโครงการภาษาอังกฤษ)*
หมวด 23 โปรแกรมเพื่อการประยุกต์ใช้งาน · ระดับนักเรียน

</center>

**รายงานฉบับสมบูรณ์**
เสนอต่อ
*สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ
กระทรวงการอุดมศึกษา วิทยาศาสตร์ วิจัยและนวัตกรรม*

ได้รับทุนอุดหนุนโครงการวิจัย พัฒนาและวิศวกรรม
โครงการแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28
ประจำปีงบประมาณ 2569

**โดย:** ____________ (ผู้พัฒนา) · ____________ (อาจารย์ที่ปรึกษา) · ____________ (สถาบัน, จังหวัด)

---

## กิตติกรรมประกาศ (Acknowledgement)

ขอขอบพระคุณ **สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.)**
ที่ได้ให้การสนับสนุนทุนแก่ "โครงการระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงาน
ราชการและสถาบันการศึกษาไทย" ภายใต้ "การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์
แห่งประเทศไทย ครั้งที่ 28 (NSC 2026)" ทำให้โครงการนี้สำเร็จลุล่วงได้

ขอขอบพระคุณ ___________________ อาจารย์ที่ปรึกษา ที่ให้คำแนะนำตลอด
การพัฒนาโครงการ และ ___________________ หัวหน้าสถาบัน ที่ให้การสนับสนุน

---

## บทคัดย่อ (Abstract)

### ภาษาไทย

ปัจจุบันประชาชนไทยตกเป็นเหยื่อของเว็บไซต์ฟิชชิงที่เลียนแบบหน่วยงานราชการ
สถาบันการศึกษา และธนาคาร เป็นจำนวนหลายหมื่นเคสต่อปี โดยมีความเสียหายเฉลี่ย
ต่อรายผู้เสียหาย 5,000–10,000 บาท ระบบป้องกัน global ที่มีอยู่ พลาด URL ปลอม
ของแบรนด์ไทยจำนวนมากเพราะไม่มี whitelist และ training data เฉพาะของไทย

โครงการนี้นำเสนอ **แพลตฟอร์มตรวจจับ URL ฟิชชิงเฉพาะทาง** สำหรับเป้าหมาย
ที่เป็นแบรนด์ไทย ประกอบด้วย (1) ML ensemble RandomForest + XGBoost บน
33 features รวมถึง IDN/Homoglyph และ Path-impersonation features ที่
ออกแบบใหม่ในเวอร์ชัน schema v1.3.0 (2) Heuristic Rules Engine เพื่อความ
โปร่งใสและตรวจสอบได้ (3) Brand Watchlist + Webhook (รองรับ LINE Notify)
สำหรับแจ้งเตือนหน่วยงาน (4) Campaign Clustering เพื่อจัดกลุ่มฟิชชิงจาก kit
เดียวกัน (5) Public Threat Feed (JSON/CSV/STIX 2.1) แชร์เป็นสาธารณะ
ไม่ต้อง API key และ (6) Citizen Report Portal ให้ประชาชนแจ้งเว็บปลอมโดย
ไม่ต้อง login

ผลการทดสอบบนชุดข้อมูล Thai-targeting holdout ที่โมเดลไม่เคยเห็น (53 URL)
ได้ recall **100% (53/53)** ที่ threshold ≥ 0.7 (95% CI [0.93, 1.00])
และผ่าน CI gate ขั้นต่ำ 0.85 ระบบนี้เปิดเป็น open source ภายใต้ Apache 2.0
และพร้อมให้หน่วยงานต่าง ๆ นำไปใช้งานหรือต่อยอดได้ทันที

**คำสำคัญ:** ฟิชชิง, machine learning, IDN homograph, STIX, Sustainable Innovation,
หน่วยงานราชการไทย, ธนาคาร, ผู้สูงอายุ

### English

Thai citizens fall victim to phishing websites impersonating government
agencies, educational institutions and banks at the scale of tens of
thousands of incidents per year, with a median loss of THB 5,000–10,000
per victim. Existing global protection systems miss many Thai-brand
phishing URLs because they lack a Thai whitelist and Thai-specific
training data.

This project presents a **specialised phishing-URL detection platform**
targeting Thai brands, consisting of (1) a RandomForest + XGBoost
ensemble on 33 features including newly designed IDN/Homoglyph and
Path-impersonation features at schema v1.3.0, (2) a Heuristic Rules
Engine for transparency and auditability, (3) Brand Watchlist + Webhook
(LINE Notify compatible) for agency alerting, (4) Campaign Clustering
to group phishing URLs from the same kit, (5) Public Threat Feed
(JSON/CSV/STIX 2.1) shared with no API key, and (6) a Citizen Report
Portal allowing the public to report suspicious URLs without login.

On the Thai-targeting holdout (53 URLs the model never sees during
training), the system achieves **100% recall (53/53)** at the
phishing threshold (95% CI [0.93, 1.00]) and clears the CI gate of
0.85. The system is open-sourced under Apache 2.0 and is ready for
agencies to adopt or extend.

**Keywords:** phishing, machine learning, IDN homograph, STIX,
sustainable innovation, Thai government, banking, elderly users

---

## บทนำ

(เนื้อหาเหมือนกับข้อเสนอโครงการ ข้อ 2-4 แต่เขียนเป็น narrative เล่าเรื่องว่า
ทำไมต้องทำ → ทำอะไร → ผลลัพธ์เป็นอย่างไร)

ตามข้อมูลของ ETDA และ ThaiCERT ในปี 2567 มีการแจ้งเว็บปลอม / SMS หลอก
ที่อ้างชื่อหน่วยงานราชการมากกว่า 30,000 เคส โดยส่วนใหญ่เป็นการเลียนแบบ
brand ราชการที่ประชาชนไว้ใจ — สรรพากร, ไปรษณีย์ไทย, ETDA, ธนาคารออมสิน,
ธนาคารกรุงไทย, ฯลฯ ผู้เสียหายส่วนใหญ่เป็นผู้สูงอายุและประชาชนที่ไม่มีความรู้
ทางเทคนิคในการแยก URL จริงจาก URL ปลอม

ระบบที่ออกแบบโดยตรงสำหรับเป้าหมายนี้ต้องการ:

1. **Whitelist ของ Thai brand** ที่ครอบคลุม → ใช้ 500+ โดเมน
2. **Feature ที่จับการปลอมในระดับ URL string ได้** → 33 features ที่ออกแบบเอง
3. **โมเดลที่ฝึกบน Thai-specific data** → curated seed corpus 175 URL
4. **ระบบที่โปร่งใส** → Rules Engine แสดง rule_id ที่ทำงาน
5. **ช่องทางใช้งานที่ accessible** → extension + portal ฟรี ไม่ต้อง login

---

## สารบัญ

```
1. บทคัดย่อ
2. บทนำ
3. วัตถุประสงค์และเป้าหมาย
4. รายละเอียดของการพัฒนา
   4.1 Story Board
   4.2 ทฤษฎี / Algorithm / เทคโนโลยี
   4.3 เครื่องมือที่ใช้
   4.4 Software Specification
   4.5 ขอบเขตและข้อจำกัด
   4.6 อุปกรณ์ (ถ้ามี)
5. กลุ่มผู้ใช้โปรแกรม
6. ผลการทดสอบ
7. ปัญหาและอุปสรรค
8. แนวทางการพัฒนาต่อ
9. ข้อสรุปและข้อเสนอแนะ
10. เอกสารอ้างอิง
11. สถานที่ติดต่อ
12. ภาคผนวก: คู่มือติดตั้ง · คู่มือใช้งาน · Disclaimer · โปสเตอร์
```

---

## วัตถุประสงค์และเป้าหมาย

(เหมือนข้อเสนอ ข้อ 3 + 5)

---

## รายละเอียดของการพัฒนา

### 4.1 Story Board

ดูภาพ ASCII diagram ในข้อเสนอข้อ 6.1 หรือดาวน์โหลด `architecture.png` จาก
`reports/` (สามารถ render จาก draw.io หรือ Mermaid ได้)

### 4.2 ทฤษฎี / Algorithm / เทคโนโลยี

#### 4.2.1 Feature Schema v1.3.0 (รวม 33 features)

| กลุ่ม | จำนวน | ตัวอย่าง |
|------|------|----------|
| Lexical v1 | 10 | url_length, num_dots, has_ip, entropy |
| Lexical v1.1 | 5 | path_depth, max_digit_run, has_query_string |
| Domain | 4 | domain_age_days, is_thai_tld, tld_type, is_known_registrar |
| Whitelist | 2 | min_edit_distance, is_typosquat |
| TLS | 3 | has_valid_cert, cert_age_days, is_self_signed |
| Meta | 2 | whois_ok, tls_ok |
| **IDN v1.2** | 3 | has_punycode, has_mixed_script, homoglyph_distance |
| **Path v1.3** | 4 | **has_login_keyword, has_suspicious_tld, path_brand_hit, path_length** |

#### 4.2.2 ML Ensemble + Calibration

```python
# pseudo-code
rf  = RandomForestClassifier(n_estimators=200, class_weight="balanced", ...)
xgb = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, ...)
base = VotingClassifier([("rf", rf), ("xgb", xgb)], voting="soft")
model = CalibratedClassifierCV(base, method="isotonic", cv=5)
```

**ทำไมต้อง ensemble + calibration:**
* RF ดีในการจับ non-linear interaction
* XGB ดีในการเรียนรู้ tail (URL หายาก)
* Soft voting ใช้ probability เฉลี่ย ลด variance
* Isotonic calibration ทำให้ score มี meaning เป็น probability จริง
  (ไม่ใช่แค่ ranking) → threshold 0.7/0.3 มีความหมายข้ามดาต้าเซ็ต

#### 4.2.3 IDN / Homoglyph Defense

ผู้โจมตีใช้ตัวอักษรหน้าตาเหมือนจากภาษาอื่น (Cyrillic, Greek, Fullwidth) เช่น
`chulа.com` ใช้ Cyrillic `а` (U+0430) แทน Latin `a` (U+0061) — ระบบจะ:

1. **Decode IDN** (Punycode → Unicode)
2. **Fold confusables** ตาม Unicode TR36 (า → a, о → o, ...)
3. **เทียบ Levenshtein** กับ whitelist labels หลัง fold

ผลคือ `chulа.com` จะมี `homoglyph_distance = 0` กับ `chula.ac.th`

#### 4.2.4 Path Impersonation Detection (ใหม่ v1.3.0)

OpenPhish 2024-2025 รายงานว่ารูปแบบฟิชชิงที่นิยมที่สุดคือ host ดูปกติ
แต่เอา brand ใส่ใน path:

```
random-host-abc.cc/krungthai/login
secure-update.online/obec/verify-account
```

ระบบจึงตรวจ:
* `path_brand_hit = 1` ถ้ามี brand label ของ whitelist อยู่ใน path
* `has_login_keyword = 1` ถ้าใน path มีคำอย่าง login, signin, verify, ...
* `has_suspicious_tld = 1` ถ้า eTLD อยู่ใน list `.cc, .xyz, .icu, .cfd, ...`

#### 4.2.5 Heuristic Rules Engine

ML score + rule adjustments + rule pin = final score, final label

```python
class RulesEngine:
    def evaluate(url, features):
        hits = []
        for rule in DEFAULT_RULES:
            hit = rule(url, features)
            if hit: hits.append(hit)
        return RulesResult(hits, sum(deltas), pinned_label)
```

Built-in rules:

| Rule ID | เงื่อนไข | Δ score | Pin |
|---------|----------|---------|-----|
| `WHITELIST_EXACT` | host ตรง whitelist | -0.60 | safe |
| `AT_TRICK` | URL มี `@` ซ่อนปลายทาง | +0.55 | phishing |
| `IDN_HOMOGRAPH` | Punycode + close to brand | +0.45 | phishing |
| `TYPOSQUAT_CRED` | typosquat + login keyword | +0.40 | phishing |
| `PATH_BRAND_BAIT` | brand ใน path + cheap TLD | +0.30 | phishing |
| `IP_CRED` | IP host + login keyword | +0.50 | phishing |
| `CHEAP_TLD_PLAIN` | cheap TLD ไม่มี HTTPS | +0.20 | (no pin) |

#### 4.2.6 Campaign Clustering Algorithm

```python
fingerprint = f"{brand}|{tld}|{path_shape}"
# path_shape: digits → "#", hex>=8 → "$hex"
```

URL ที่ fingerprint ตรงกันถือเป็น campaign เดียวกัน

#### 4.2.7 STIX 2.1 Output

```jsonc
{
  "type": "indicator",
  "spec_version": "2.1",
  "pattern_type": "stix",
  "pattern": "[url:value = 'https://...']",
  "indicator_types": ["malicious-activity"],
  "confidence": 97
}
```

### 4.3 เครื่องมือที่ใช้ในการพัฒนา

(เหมือนข้อเสนอ ข้อ 6.3)

### 4.4 Software Specification

ดูรายละเอียดเต็มที่ภาคผนวก: คู่มือติดตั้ง · คู่มือใช้งาน

### 4.5 ขอบเขตและข้อจำกัด

(เหมือนข้อเสนอ)

### 4.6 อุปกรณ์ที่ใช้กับโปรแกรม

* Server: VPS ขั้นต่ำ 1 vCPU / 1 GB RAM (ทดสอบบน DigitalOcean Basic, Render free tier)
* Database: PostgreSQL 16 หรือ SQLite (สำหรับ demo)
* Browser: Chrome ≥ 108, Edge ≥ 108, Firefox ≥ 121, Brave, Opera
* ไม่ต้องการ GPU — โมเดล inference ใช้ CPU พอ (~30 ms/URL)

---

## กลุ่มผู้ใช้โปรแกรม

| กลุ่ม | ใช้งานอย่างไร |
|------|----------------|
| ประชาชนทั่วไป | ติดตั้ง browser extension หรือใช้หน้า `/report` ของ dashboard |
| ผู้สูงอายุ / กลุ่มเปราะบาง | ใช้ extension (เตือนเต็มจอ) + เนื้อหา `/learn` เป็นภาษาไทย |
| ครู / อาจารย์ | ใช้สอน digital literacy ในห้อง — content ใน `/learn` |
| ฝ่าย IT หน่วยงานราชการ | ลงทะเบียน Brand Watchlist + เชื่อม webhook กับ LINE Notify / Slack |
| นักวิจัย / ชุมชน security | ดึง public threat feed (STIX) เข้า SIEM ของหน่วยงาน |
| ฝ่าย SOC | ดู campaigns / domain history ผ่าน dashboard |

---

## ผลการทดสอบ

### Thai-targeting Holdout (Primary Metric)

| Metric | v1.2.0 baseline | **v1.3.0 (โครงการนี้)** |
|--------|------|------|
| Recall ที่ threshold ≥ 0.7 | 98.11% (52/53) | **100% (53/53)** |
| 95% CI | [0.90, 1.00] | **[0.93, 1.00]** |
| Mean score | 0.986 | **0.994** |

### Cross-validation (5-fold synthetic, 6000 samples)

| Metric | v1.2.0 | **v1.3.0** |
|--------|--------|-----------|
| F1 mean | 0.992 ± 0.002 | **0.998 ± 0.001** |

### CI Gate

ทุก commit ผ่าน `python -m ml_pipeline.evaluate --enforce-threshold`
ต้องได้ Thai recall ≥ 0.85 (ตั้งโดย `THAI_RECALL_MIN_THRESHOLD`)

### Automated Test Suite

**167 pytest cases** ครอบคลุม:
* Feature extraction (`test_lexical.py`, `test_homoglyph.py`, `test_extractor.py`)
* Whitelist + typosquat (`test_whitelist.py`)
* Scoring (`test_scorer.py`)
* Cache (`test_cache.py`)
* Golden URLs — pin verdicts สำหรับ URL ราชการจริง + 8 phishing patterns
* Seed corpus sanity (`test_seed_corpus.py`)
* Rules engine (`test_rules.py`) — ทุก rule + clamp + pin priority
* Campaign clustering (`test_campaigns.py`)
* New endpoints (`test_new_endpoints.py`) — watchlist, feed, campaigns,
  domain, impact, learn, request-id, security headers

---

## ปัญหาและอุปสรรค

| ปัญหา | วิธีแก้ |
|------|---------|
| Train/serve skew: ผลตอนฝึกกับตอน deploy ต่างกัน | สร้าง `phish_features` เป็น shared package, schema version check ที่ startup |
| Phishing kit เปลี่ยน pattern ทุกเดือน | ออกแบบ Rules Engine ที่เพิ่ม rule ใหม่ได้ทันทีโดยไม่ต้อง retrain |
| Synthetic data → recall ดีจอมปลอม | แยก holdout จริง 53 URL ออกก่อน train, ใช้เป็น primary metric |
| WHOIS/TLS lookup ช้า / fail | timeout-guarded + impute defaults; feature `whois_ok`/`tls_ok` ให้โมเดลรู้ |
| ส่งของให้ผู้ใช้ทั่วไป → ติดตั้งยาก | สร้างหน้า `/report` portal ไม่ต้อง login + extension MV3 |

---

## แนวทางการพัฒนาและประยุกต์ใช้ร่วมกับงานอื่น ๆ ในขั้นต่อไป

1. **LINE Official Account bot** — ให้ผู้ใช้พิมพ์ URL ส่งใน chat เพื่อตรวจ (Thai elderly ใช้ LINE มาก)
2. **SMS report gateway** — รับแจ้งฟิชชิงผ่าน SMS จากผู้สูงอายุที่ไม่ใช้ smartphone
3. **เชื่อม ETDA 1212 / ตำรวจไซเบอร์ 1441** — ส่ง finding ผ่าน API
4. **เปิด TAXII 2.1 server** เต็มรูปแบบ ไม่ใช่แค่ STIX bundle export
5. **Federated learning** — หน่วยงานหลายแห่ง deploy แล้ว aggregate signal โดยไม่ต้องแชร์ raw URL
6. **Visual fingerprint** — ใช้ headless browser ดูหน้าเว็บแล้วเปรียบเทียบกับ template ของหน่วยงานจริง

---

## ข้อสรุปและข้อเสนอแนะ

โครงการนี้แสดงให้เห็นว่าระบบตรวจจับฟิชชิงเฉพาะทางสำหรับเป้าหมายไทย เป็นไปได้
และให้ผลแม่นกว่าระบบ global ที่มีอยู่ในชุดข้อมูลที่ออกแบบมาวัดเป้าหมายตรง
โดยการรวม ML, Rules Engine, IDN defense และ Path-impersonation features
เข้าด้วยกัน

ระบบนี้ถูกออกแบบให้ **sustainable** ตาม theme NSC 2026 ใน 4 มิติพร้อมกัน:
* **Social** — protect citizens, no-login portal, accessibility-first
* **Economic** — quantified loss prevention via `/api/v1/impact`
* **Environmental** — low-resource architecture
* **Open** — Apache 2.0 + public threat feed + committed dataset

ข้อเสนอแนะต่อหน่วยงานราชการ: ลงทะเบียน brand watchlist พร้อม LINE Notify
webhook เพื่อให้รู้ก่อนความเสียหายลุกลาม และเชื่อม STIX feed เข้า SIEM
ของหน่วยงาน

---

## เอกสารอ้างอิง

(เหมือนข้อเสนอ ข้อ 8 — ETDA, Unicode TR36, STIX 2.1, XGBoost, RF, OpenPhish,
URLhaus, ThaiCERT)

---

## สถานที่ติดต่อของผู้พัฒนาและอาจารย์ที่ปรึกษา

| | ผู้พัฒนา | อาจารย์ที่ปรึกษา |
|---|----------|------------------|
| ชื่อ | _________ | _________ |
| สถาบัน | _________ | _________ |
| โทรศัพท์ | _________ | _________ |
| Email | _________ | _________ |

---

## ภาคผนวก

ดูไฟล์แยก:
* `docs/nsc2026/04_installation_guide.md` — คู่มือการติดตั้ง
* `docs/nsc2026/05_user_guide.md` — คู่มือการใช้งาน
* `docs/nsc2026/06_disclaimer.txt` — ข้อตกลงในการใช้ซอฟต์แวร์
* `docs/nsc2026/07_poster.md` — โปสเตอร์ A1
