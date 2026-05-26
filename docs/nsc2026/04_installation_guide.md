# คู่มือการติดตั้ง (Installation Guide)

> สำหรับ NSC 2026 รอบนำเสนอผลงาน — แนบใน Appendix ของรายงานฉบับสมบูรณ์

---

## 1. ความต้องการของระบบ

### ขั้นต่ำ (สำหรับ demo / dev)
* Linux / macOS / Windows 10+ ที่มี **Docker Desktop** ติดตั้งแล้ว
* RAM: 2 GB · Disk: 1 GB ว่าง · ไม่ต้องการ GPU
* Network: เปิด port 8000 (API) และ 5173 (dashboard)

### Production
* Linux VPS (Ubuntu 22.04+ แนะนำ) 1 vCPU / 1 GB RAM
* PostgreSQL 14+ (หรือใช้ SQLite สำหรับ demo)
* HTTPS termination (Caddy / nginx / Cloud Run)

### Browser Extension
* Chrome ≥ 108, Edge ≥ 108, Brave, Opera, Firefox ≥ 121

---

## 2. ติดตั้งด้วย Docker Compose (แนะนำ)

```bash
# 1. clone repository
git clone https://github.com/reenx8/security.git
cd security

# 2. คัดลอกและแก้ environment file
cp .env.example .env
nano .env                              # แก้ API_KEY ก่อน deploy

# 3. boot ทั้งระบบ (PostgreSQL + backend)
docker compose up -d --build

# 4. ตรวจสอบว่าทำงานอยู่
curl http://localhost:8000/health
curl http://localhost:8000/version
# {"backend":"1.1.0","phish_features":"1.1.0","schema":"1.4.0"}
```

API พร้อมใช้งานที่ **http://localhost:8000** · ดู interactive API docs ที่ **/docs**

---

## 3. ติดตั้งโดยไม่ใช้ Docker (Python + SQLite, สำหรับ dev)

```bash
# 1. สร้าง virtualenv และติดตั้ง dependencies
python -m venv .venv && source .venv/bin/activate
make install                           # = pip install -e . + backend req + ml req

# 2. start backend ด้วย SQLite (zero setup)
make run                               # → http://localhost:8000
```

---

## 4. ติดตั้ง Dashboard (React)

```bash
cd dashboard
cp .env.example .env                   # ตั้ง VITE_API_URL + VITE_API_KEY
npm install
npm run dev                            # → http://localhost:5173

# หรือ build ขึ้น production
npm run build                          # → dashboard/dist/
```

---

## 5. ติดตั้ง Browser Extension

```bash
# 1. สร้างไฟล์ .zip
python scripts/build_extension.py
# → dist/thai-phishing-detector-v1.1.1.zip

# 2. แตก .zip ไว้ในโฟลเดอร์ถาวร
unzip dist/thai-phishing-detector-v1.1.1.zip -d ~/phish-ext/

# 3. Chrome / Edge / Brave:
#    เปิด chrome://extensions → เปิด Developer mode → Load unpacked
#    เลือกโฟลเดอร์ ~/phish-ext/
#
#    Firefox 121+:
#    เปิด about:debugging#/runtime/this-firefox
#    คลิก Load Temporary Add-on → เลือก manifest.json

# 4. เปิด Options ของ extension:
#    - API endpoint: http://localhost:8000
#    - API Key: ค่า API_KEY ในไฟล์ .env
```

---

## 6. Train โมเดลใหม่ (ถ้าต้องการ)

> โมเดลที่ฝึกแล้ว commit ไว้ใน repo ที่ `models/` ใช้ได้ทันที — ทำขั้นนี้ก็ต่อเมื่อ
> ต้องการ retrain ด้วย dataset ของตนเอง

```bash
make train                             # build_whitelist + collect_dataset + train
make evaluate                          # ประเมิน + เขียนกราฟ
make evaluate-gate                     # ⚠️ exit-code != 0 ถ้า Thai recall < 0.85
```

---

## 7. Deploy บน Render (one-click, ฟรี tier)

```bash
# 1. push repo ไปยัง GitHub
git push -u origin main

# 2. เปิด https://dashboard.render.com → New → Blueprint
#    เลือก repo ที่ push ไป Render จะอ่าน render.yaml และสร้างให้

# 3. หลัง deploy เสร็จ ตั้งค่า API_KEY ในแท็บ Environment ของ web service
```

---

## 8. ตรวจสอบหลังติดตั้ง

```bash
# ตรวจ URL ทดสอบ (whitelist exact)
curl -X POST http://localhost:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  -d '{"url":"https://www.obec.go.th"}'
# → label: "safe", score < 0.3

# ตรวจ URL ฟิชชิง (typosquat)
curl -X POST http://localhost:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
  -d '{"url":"http://obec.com/verify-account"}'
# → label: "phishing", score ≥ 0.7, rules.hits[].rule_id includes "TYPOSQUAT_CRED"

# ดู social-impact metrics (no auth)
curl http://localhost:8000/api/v1/impact

# ดู awareness cards (no auth)
curl http://localhost:8000/api/v1/learn

# ดู threat feed (no auth)
curl http://localhost:8000/api/v1/feed.json
```

---

## 9. ปัญหาที่พบบ่อย (Troubleshooting)

| อาการ | สาเหตุ / วิธีแก้ |
|------|-------------------|
| `model_ready: false` ใน /health | model artifacts ไม่อยู่ที่ `models/` — รัน `make train` |
| `db_ok: false` ใน /health | PostgreSQL ยังไม่พร้อม — รอ healthcheck หรือเช็ค `docker compose logs db` |
| Extension badge เป็นสีเทาตลอด | backend unreachable — เปิด options ใน extension เช็ค API endpoint และ key |
| `X-API-Key` ผิด | คัดลอกค่าจาก `.env` ของ backend ใส่ใน extension/dashboard options |
| Dashboard fetch ติด CORS | เพิ่ม origin ของ dashboard ใน `CORS_ORIGINS` ของ backend |
| `schema mismatch` error | ทรับ schema version ต่างจาก code — รัน `make train` ให้ retrain |
