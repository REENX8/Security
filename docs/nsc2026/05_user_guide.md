# คู่มือการใช้งาน (User Guide)

> สำหรับ NSC 2026 รอบนำเสนอผลงาน — แนบใน Appendix ของรายงานฉบับสมบูรณ์
> ระบบมีกลุ่มผู้ใช้ 6 กลุ่ม คู่มือนี้แบ่งเป็น 6 ส่วนย่อยตามกลุ่ม

---

## 👤 ส่วนที่ 1: สำหรับประชาชนทั่วไป

### 1.1 ติดตั้งส่วนขยายเบราว์เซอร์ (วิธีที่ง่ายสุด)

1. ดาวน์โหลด `thai-phishing-detector-vX.Y.Z.zip` จากหน้า Release ของ GitHub
2. เปิด `chrome://extensions` (หรือ `edge://extensions`) เปิด Developer mode
3. คลิก **Load unpacked** เลือกโฟลเดอร์ที่แตก zip แล้ว
4. คลิก icon ส่วนขยายบน toolbar → **Options** ใส่ API endpoint และ API key
5. เสร็จ — เปิดเว็บปกติ ระบบจะตรวจให้อัตโนมัติ

### 1.2 ดู verdict

* **🟢 Badge เขียว = ปลอดภัย** — เว็บนี้ผ่านการตรวจสอบ
* **🟡 Badge เหลือง = น่าสงสัย** — มีสัญญาณบางอย่าง ระวัง
* **🔴 Badge แดง = ฟิชชิง** — หน้าจอจะแสดง warning เต็มจอ ห้ามกรอกข้อมูล

### 1.3 แจ้งเว็บปลอม (Citizen Report Portal)

ถ้าคุณเจอ URL ที่สงสัย แต่ยังไม่ติดตั้ง extension:

1. เปิด dashboard ของระบบ ไปที่หน้า **แจ้งเว็บฟิชชิง** (`/report`)
2. **ไม่ต้อง login** — ใส่ URL ที่สงสัย
3. กด **ตรวจสอบก่อนแจ้ง** เพื่อดูผลของระบบ
4. ระบุว่าคิดว่าเป็นอะไร (ฟิชชิง / น่าสงสัย / ปลอดภัย — ระบบตัดสินผิด)
5. กด **ส่งรายงาน**

### 1.4 อ่านเนื้อหาให้ความรู้

ดู awareness cards ที่ `/api/v1/learn` (ไม่ต้อง login)

หรือเรียกผ่าน chatbot / Line bot ที่ใช้ API นี้

---

## 👵 ส่วนที่ 2: สำหรับผู้สูงอายุ

### กฎทอง 3 ข้อ (จำง่าย)

1. **หน่วยงานราชการ ไม่ส่ง SMS / LINE เรียกเก็บเงินด่วน**
2. **ตำรวจ ไม่ขอ OTP หรือเลขหลังบัตรเดบิตทางโทรศัพท์**
3. **ก่อนกดลิงก์ใด ๆ → โทร 1212 หรือลูกหลานก่อน**

### ใช้ระบบนี้

1. ลูกหลานช่วยติดตั้ง browser extension ให้ครั้งเดียว
2. ถ้าเจอเว็บแดง = ห้ามกรอกข้อมูล กลับไปหน้าก่อน
3. ถ้าได้รับ SMS น่าสงสัย ส่งให้ลูกหลานช่วยตรวจที่หน้า `/report`

---

## 🏫 ส่วนที่ 3: สำหรับครู / อาจารย์

### ใช้สอน Digital Literacy

* ใช้ awareness cards ใน `/api/v1/learn?audience=student` เป็นเนื้อหาในห้อง
* ให้นักเรียนลองตรวจ URL จริงที่หน้า `/report`
* เปรียบเทียบ URL จริง vs URL ปลอม โดยใช้ feature breakdown ของระบบ

### ตัวอย่าง URL สำหรับสอน

```
https://www.obec.go.th              ← จริง (safe)
http://obec.com/verify-account      ← ปลอม (typosquat + login keyword)
https://chulа.com/login             ← ปลอม (Cyrillic 'а' — homograph)
http://203.0.113.45/obec/login      ← ปลอม (IP host + brand-in-path)
```

---

## 🏛️ ส่วนที่ 4: สำหรับฝ่าย IT หน่วยงานราชการ

### 4.1 ลงทะเบียน Brand Watchlist

```bash
curl -X POST https://your-deployment/api/v1/watchlist \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "brand": "obec",
    "description": "สำนักงานคณะกรรมการการศึกษาขั้นพื้นฐาน",
    "webhook_url": "https://hooks.slack.com/services/T00/B00/XYZ"
  }'
```

### 4.2 เชื่อม LINE Notify

```bash
# รูปแบบ A: URL มี token เป็น query parameter
"webhook_url": "https://notify-api.line.me/api/notify?token=YOUR_TOKEN"

# รูปแบบ B: URL มี token เป็น hash fragment (ระบบจะถอดเป็น Bearer header ให้)
"webhook_url": "https://notify-api.line.me/api/notify#token=YOUR_TOKEN"
```

ระบบจะตรวจจับว่าเป็น LINE Notify อัตโนมัติและจัดรูปแบบข้อความเป็นภาษาไทย:

```
⚠️ Phishing alert
แบรนด์: obec
URL: http://obec.com/verify-account
คะแนน: 0.98
โดเมนคล้ายกับ obec.go.th และ URL ขอข้อมูล login/บัญชี...
```

### 4.3 ดู delivery log

ใน dashboard ไปที่หน้า **เฝ้าระวังแบรนด์** → คลิก "ดูประวัติการส่ง webhook"
หรือเรียก API:

```bash
curl https://.../api/v1/watchlist/deliveries -H "X-API-Key: $API_KEY"
```

### 4.4 เชื่อม STIX feed เข้า SIEM

```bash
# Threat feed (no auth) - ดึงได้ทุก 60 วินาที
curl https://your-deployment/api/v1/feed.stix?hours=24
```

ส่ง STIX bundle เข้า SIEM / TAXII consumer ของหน่วยงานได้ทันที

---

## 🔬 ส่วนที่ 5: สำหรับนักวิจัย / ชุมชน Security

### 5.1 ดึง Public Threat Feed

```bash
# JSON
curl https://your-deployment/api/v1/feed.json?hours=24

# CSV (ใช้กับ Excel/spreadsheet)
curl https://your-deployment/api/v1/feed.csv?hours=24

# STIX 2.1 bundle
curl https://your-deployment/api/v1/feed.stix?hours=72
```

### 5.2 ส่ง URL ตรวจเป็น batch

```bash
curl -X POST https://your-deployment/api/v1/check/batch \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urls":["url1","url2","url3"]}'
```

สูงสุด 50 URLs ต่อ request

### 5.3 ดู Campaign Clusters

```bash
curl https://your-deployment/api/v1/campaigns?min_urls=5 \
  -H "X-API-Key: $API_KEY"
```

จัดกลุ่ม URL ที่มาจาก phishing kit เดียวกัน (brand + tld + path-shape)

---

## 📊 ส่วนที่ 6: สำหรับ SOC / ผู้ดูแลระบบ

### 6.1 Dashboard 11 หน้า

| หน้า | URL | ใช้ทำอะไร |
|------|-----|-----------|
| ภาพรวม | `/` | stat cards, ตรวจ URL เดี่ยว, 7-day chart |
| ตรวจหลาย URL | `/bulk` | batch check + export CSV |
| ประวัติ | `/history` | filter + paginate + detail modal |
| สถิติเชิงลึก | `/stats` | top brands, label pie, hourly heatmap |
| **แคมเปญฟิชชิง** | `/campaigns` | campaign cluster list |
| **เฝ้าระวังแบรนด์** | `/watchlist` | brand + webhook CRUD + delivery log |
| **ตรวจประวัติโดเมน** | `/domain` | reputation timeline ของ host |
| **Threat Feed** | `/feed` | live feed viewer + download |
| Whitelist | `/admin` | จัดการ whitelist (hot-reload) |
| Feedback | `/feedback` | feedback list + export CSV |
| **แจ้งเว็บฟิชชิง** | `/report` | citizen portal (no login) |

### 6.2 Observability

```bash
# Prometheus metrics
curl https://your-deployment/metrics

# Health (model_ready, db_ok, schema_version, uptime, cache size)
curl https://your-deployment/health

# Version (backend + phish_features + schema)
curl https://your-deployment/version
```

ทุก response มี header `X-Request-ID` ใช้ trace request ผ่าน log ได้ —
ถ้า `LOG_FORMAT=json` ใน .env, access log จะเป็น structured JSON

### 6.3 Alert ที่แนะนำ

* `phish_model_ready == 0` → page on-call (โมเดลหาย)
* p95 latency > 500 ms ติดต่อกัน 5 นาที → investigate
* `webhook_delivery.status_code != 200` rate > 10% → เช็ค downstream
* ขนาด `url_checks` table > 10 GB → enable retention policy
