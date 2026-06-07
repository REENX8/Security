# ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานไทยด้วยการเรียนรู้ของเครื่องและกฎฮิวริสติก
### (Thai Phishing URL Detection System Using Machine Learning and Heuristic Rules)

> บทความวิชาการ — เรียบเรียงสรุปด้วยภาษาที่อ่านเข้าใจง่าย

---

## บทคัดย่อ

เว็บไซต์ฟิชชิงที่ปลอมแบบหน่วยงานราชการ สถาบันการศึกษา และสถาบันการเงินไทยเป็นภัยคุกคามที่ทวีความรุนแรงขึ้นอย่างต่อเนื่อง ผู้ใช้ที่ไม่ทันสังเกตอาจถูกหลอกให้เปิดเผยข้อมูลส่วนตัว รหัสผ่าน หรือข้อมูลทางการเงินโดยไม่รู้ตัว

งานวิจัยนี้นำเสนอ **ระบบรู้ทัน (RuThan)** ซึ่งเป็นระบบตรวจจับเว็บไซต์ฟิชชิงแบบครบวงจร โดยผสานการทำงานของ **โมเดลการเรียนรู้ของเครื่อง (Machine Learning Ensemble)** ที่ใช้ 44 คุณลักษณะ ร่วมกับ **กฎฮิวริสติกที่โปร่งใส** ซึ่งอธิบายผลการตรวจจับเป็นภาษาไทยได้ชัดเจน ระบบยังรองรับการทำงานผ่านหลายช่องทาง ได้แก่ ส่วนขยายเบราว์เซอร์ (Chrome/Firefox/Edge), dashboard บนเว็บ, LINE chatbot และ public threat feed

ผลการทดสอบพบว่าโมเดลสามารถตรวจจับ URL ฟิชชิงที่มุ่งเป้าหน่วยงานไทยได้ **100% (378/378 URLs)** ที่ค่า threshold ≥ 0.7 (95% CI: [0.990, 1.000]) และมีค่า F1-score จากการ cross-validation = 0.999 ± 0.000

**คำสำคัญ:** ฟิชชิง, การเรียนรู้ของเครื่อง, URL Detection, ความปลอดภัยไซเบอร์, หน่วยงานไทย

---

## 1. บทนำ

ภัยคุกคามทางไซเบอร์ในรูปแบบเว็บไซต์ฟิชชิงเป็นปัญหาที่พบมากในประเทศไทย โดยมิจฉาชีพมักปลอมแบบเว็บไซต์ราชการ ธนาคาร และมหาวิทยาลัย เพื่อหลอกลวงประชาชนให้กรอกข้อมูลส่วนตัวหรือทำธุรกรรมทางการเงินโดยไม่รู้ตัว

โดเมนที่ถูกปลอมแบบมักอยู่ในกลุ่ม `.go.th` (ราชการ) `.ac.th` (การศึกษา) และ `.or.th` (องค์กรไม่แสวงหากำไร) ซึ่งประชาชนให้ความเชื่อถือสูง เทคนิคที่ใช้ปลอม ได้แก่ การใช้ตัวอักษรที่มีลักษณะใกล้เคียง (homograph) การสะกดผิดเล็กน้อย (typosquat) และการซ่อน URL ด้วยบริการย่อลิงก์ (URL shortener)

งานวิจัยนี้แก้ปัญหาดังกล่าวด้วยการพัฒนาระบบที่ผสานเทคนิคสองแนวทางหลัก:

- **Machine Learning Ensemble** (scikit-learn + XGBoost) สำหรับการตัดสินใจเชิงสถิติจากคุณลักษณะ 44 รายการ
- **Rules Engine** ที่เขียนเป็นกฎโปร่งใส 7 ข้อ สำหรับอธิบายเหตุผลการตรวจจับเป็นภาษาไทยที่ผู้ใช้ทั่วไปเข้าใจได้

ระบบรู้ทันถูกออกแบบให้เป็น **end-to-end platform** ที่ผู้ใช้ทั่วไป ผู้ดูแลระบบ และหน่วยงานด้านความปลอดภัยสามารถใช้งานได้พร้อมกันผ่านหลายช่องทาง

---

## 2. วิธีการดำเนินงาน

### 2.1 การรวบรวมข้อมูล Seed Corpus

จัดทำชุดข้อมูล URL ที่เน้นเป้าหมายไทยจำนวน **1,261 URLs** ครอบคลุม **160+ แบรนด์** ในกลุ่มธนาคาร กระทรวง มหาวิทยาลัย รัฐวิสาหกิจ e-commerce สายการบิน โลจิสติกส์ และโทรคมนาคม โดยมีเกณฑ์คือไม่เกิน 8 URLs ต่อแบรนด์เพื่อความสมดุลของข้อมูล

ข้อมูล URL ฟิชชิงทั่วไปเพิ่มเติมได้จาก **OpenPhish** และ **PhishTank** พร้อมกระบวนการ deduplication ป้องกันข้อมูลซ้ำ

### 2.2 การสกัดคุณลักษณะ (Feature Extraction)

พัฒนา package `phish_features` สำหรับสกัด **44 คุณลักษณะ (v1.6.0)** แบ่งออกเป็น 7 กลุ่ม:

| กลุ่มคุณลักษณะ | ตัวอย่าง |
|:---|:---|
| Lexical (10) | ความยาว URL, entropy, มี IP แทนชื่อโดเมน, จำนวน subdomain, port พิเศษ |
| Domain | ประเภท TLD, อายุ domain, registrar |
| Whitelist/Typosquat | Levenshtein distance ≤ 2, brand label |
| TLS | ความถูกต้องของ cert, self-signed, Let's Encrypt indicator |
| IDN/Homoglyph | punycode, mixed script detection |
| Path Impersonation | คำสำคัญ login/credential ใน path, brand hits |
| Rich Lexical | จำนวน token, path entropy, keyword count |

### 2.3 การฝึกโมเดล Machine Learning

ฝึกโมเดล ensemble โดยใช้ **scikit-learn + XGBoost** บนข้อมูลสังเคราะห์ (synthetic) จำนวน **12,000 แถว** ที่ anchor ไว้กับ 500+ โดเมนราชการ/การศึกษา/ธนาคารไทยที่เชื่อถือได้

ใช้ 5-fold cross-validation และกำหนด threshold สำหรับการจัดประเภทดังนี้:
- **Safe:** คะแนน ≤ 0.3
- **Suspicious:** คะแนน 0.3–0.7 (ส่ง content-based fallback ตรวจ HTML เพิ่มเติม)
- **Phishing:** คะแนน ≥ 0.7

### 2.4 การพัฒนา Rules Engine และ Content-based Fallback

พัฒนากฎฮิวริสติก **7 ข้อ** (typosquat, homograph, credential-harvesting path, IP-based URL, URL shortener, mixed-script domain, known-phishing-pattern) ที่สามารถ override ผลจาก ML ได้โดยไม่ต้องเทรนโมเดลใหม่

สำหรับ URL ในโซนเทา (0.3–0.7) ระบบจะดึง HTML ของหน้าเว็บมาตรวจสอบสัญญาณ brand impersonation เพิ่มเติม โดยมีการป้องกัน **SSRF (Server-Side Request Forgery)** เพื่อความปลอดภัย

### 2.5 การพัฒนาโครงสร้างระบบ Backend

สร้าง REST API ด้วย **FastAPI 0.115 + SQLAlchemy 2.0 (async) + PostgreSQL 16** โดยมี endpoints หลักดังนี้:
- `POST /api/v1/check` — ส่ง URL เพื่อตรวจวิเคราะห์ (public, ไม่ต้อง auth)
- `GET /api/v1/feed.{json,csv,stix}` — public threat feed สำหรับ TAXII consumers
- `POST /api/v1/feedback` — ประชาชนรายงาน false positive/negative
- `POST /api/v1/admin/retrain` — trigger staged retraining อัตโนมัติ

### 2.6 การพัฒนา Frontend และ Integration

พัฒนา 3 ส่วนติดต่อผู้ใช้หลัก:
1. **React Dashboard** (11 หน้า) สำหรับผู้ดูแลระบบและผู้ใช้ทั่วไป
2. **Chrome Extension (Manifest V3)** แสดง badge และ interstitial warning อัตโนมัติ
3. **LINE Messaging API Bot** ผู้ใช้ส่ง URL ใน LINE แล้วได้ผลตรวจกลับทันที

---

## 3. ผลการทดลอง

### 3.1 ประสิทธิภาพการตรวจจับ URL ฟิชชิงไทย

**ตารางที่ 1** ผลการทดสอบโมเดลบน Thai-targeting holdout set (v1.6.0)

| Metric | ผลลัพธ์ |
|:---:|:---:|
| Thai Phishing Recall | **100% (378/378)** |
| 95% Confidence Interval | [0.990, 1.000] |
| 5-fold CV F1 (synthetic) | **0.999 ± 0.000** |
| Generic Phishing Recall | 98.89% (89/90) |
| Threshold (Phishing) | ≥ 0.7 |

> เอนไซม์ผลโมเดลแสดงให้เห็นว่าที่ threshold ≥ 0.7 ระบบสามารถตรวจจับ URL ฟิชชิงที่มุ่งเป้าหน่วยงานไทยได้ครบถ้วน 100% โดยยังรักษาประสิทธิภาพการตรวจจับ URL ฟิชชิงทั่วไปไว้ที่เกือบ 99%

### 3.2 ขอบเขตการครอบคลุมของ Seed Corpus

ชุดข้อมูลทดสอบครอบคลุม **160+ แบรนด์ไทย** โดยกระจายทั่วทุกกลุ่ม และ Seed corpus audit script ยืนยันว่าไม่มีแบรนด์ใดแบรนด์หนึ่งครองสัดส่วนเกินเกณฑ์

**ตารางที่ 2** ตัวอย่างประเภทแบรนด์ใน Seed Corpus

| ประเภท | ตัวอย่าง |
|:---|:---|
| ธนาคารรัฐ | ธนาคารกรุงไทย, ออมสิน, ธ.ก.ส. |
| กระทรวง | กระทรวงการคลัง, กรมสรรพากร |
| มหาวิทยาลัย | จุฬาฯ, มธ., มข. |
| รัฐวิสาหกิจ | การไฟฟ้า, ปตท., AOT |
| E-Commerce / Logistics | Shopee, Lazada, ไปรษณีย์ไทย |

### 3.3 ผลการทดสอบ Automated Test Suite

ระบบผ่านการทดสอบ **331 automated tests** ครอบคลุมทุก component ได้แก่ feature extraction, rules engine, campaign clustering, feed ingestion, SIEM export, JWT login, LINE bot, feedback retrain และ SSRF protection

CI gate บังคับ **Thai recall ≥ 0.85** ทุกครั้งที่ push code มิฉะนั้น build จะ fail โดยอัตโนมัติ

### 3.4 ความสามารถของ Campaign Clustering

ระบบสามารถจัดกลุ่ม URL ที่มาจาก phishing kit เดียวกันด้วย fingerprint (brand + TLD + path skeleton) ช่วยให้ผู้ดูแลระบบเห็นภาพรวมของแคมเปญโจมตีและตอบสนองได้รวดเร็วขึ้น

---

## 4. สรุปและอภิปรายผล

### 4.1 อภิปรายผลการทดลอง

ระบบรู้ทันแสดงให้เห็นว่าการผสาน ML ensemble กับ rules engine ที่โปร่งใสให้ผลดีกว่าการใช้แนวทางใดแนวทางหนึ่งเพียงอย่างเดียว โดย ML ช่วยจับรูปแบบที่ซับซ้อนเชิงสถิติ ในขณะที่ rules engine ช่วยให้ผู้ใช้เข้าใจเหตุผลของการแจ้งเตือนได้ทันที โดยไม่ต้องรอเทรนโมเดลใหม่เมื่อพบรูปแบบฟิชชิงใหม่

การพัฒนา content-based fallback ช่วยจัดการกับ URL ในโซนเทาได้อย่างมีประสิทธิภาพ โดยไม่ต้องพึ่งพา headless browser ซึ่งใช้ทรัพยากรสูง

### 4.2 สรุปผลการทดลอง

- โมเดล ML ensemble ที่ใช้ 44 features ตรวจจับ URL ฟิชชิงไทยได้ **100% recall** (ยืนยันด้วย 95% CI: [0.990, 1.000])
- **Rules Engine 7 กฎ** ให้คำอธิบายภาษาไทยที่ชัดเจน และสามารถจัดการกรณีพิเศษได้โดยไม่ต้องเทรนโมเดลใหม่
- ระบบ multi-channel รองรับผู้ใช้ 3 กลุ่ม คือประชาชนทั่วไป (LINE/Extension), ผู้ดูแลระบบ (Dashboard), และหน่วยงานความปลอดภัย (TAXII/Threat Feed)
- **Feedback-driven auto-retrain** ช่วยให้โมเดลปรับตัวต่อรูปแบบฟิชชิงใหม่ได้อย่างต่อเนื่อง

---

## ข้อเสนอแนะ

ควรศึกษาเพิ่มเติมเกี่ยวกับ:
1. การเพิ่ม visual similarity detection สำหรับตรวจจับการปลอมหน้าเว็บด้วย screenshot comparison
2. การขยายขอบเขตไปยัง URL ฟิชชิงในแอปพลิเคชันโซเชียลมีเดียอื่น นอกเหนือจาก LINE
3. การพัฒนาโมเดลสำหรับตรวจจับฟิชชิงผ่าน SMS (smishing) ซึ่งมีแนวโน้มเพิ่มขึ้นในไทย

## กิตติกรรมประกาศ

ขอขอบคุณ **สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.)** ที่สนับสนุนทุนวิจัย และ **การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28 (NSC 2026)** ที่เป็นเวทีนำเสนอผลงาน รวมถึงโครงการ open-source ทั้งหมดที่เป็นฐานในการพัฒนาระบบนี้ ได้แก่ FastAPI, scikit-learn, XGBoost, React และ TailwindCSS

## เอกสารอ้างอิง

[1] APWG. (2024). *Phishing Activity Trends Report Q4 2024.* Anti-Phishing Working Group. https://apwg.org/trendsreports/

[2] Sahoo, D., Liu, C., & Hoi, S. C. H. (2017). Malicious URL Detection using Machine Learning: A Survey. *arXiv preprint arXiv:1701.07179.*

[3] สำนักงานพัฒนาธุรกรรมทางอิเล็กทรอนิกส์ (ETDA). (2024). *รายงานภัยไซเบอร์ในประเทศไทยประจำปี 2567.* กระทรวงดิจิทัลเพื่อเศรษฐกิจและสังคม.

[4] Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.

[5] Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.
