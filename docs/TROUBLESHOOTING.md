# Troubleshooting

ปัญหาที่พบบ่อยและวิธีแก้ไข

---

## Backend

### โมเดลไม่โหลด — `503 MODEL_NOT_LOADED`

**สาเหตุ:** ไม่พบไฟล์ `models/ensemble.pkl`, `models/scaler.pkl` หรือ `models/features.json`

```bash
# ตรวจสอบ
ls -lh models/

# แก้ไข: retrain จาก committed seed corpus
make train
```

CI รัน `make train` ก่อน push อยู่แล้ว ถ้า clone ใหม่และไม่มี models/ ให้รัน `make train` ก่อน

---

### Backend ไม่ยอม boot — `CONFIG_ERROR: placeholder secret`

**สาเหตุ:** `APP_ENV=production` แต่ยังใช้ค่า default ของ `API_KEY`, `JWT_SECRET` หรือ `ADMIN_PASSWORD_HASH`

```bash
# ดู error
docker compose logs backend | grep CONFIG_ERROR

# แก้ไข: ตั้งค่าใน .env
API_KEY=your-random-key-here
JWT_SECRET=$(openssl rand -hex 32)
```

ใน development ตั้ง `APP_ENV=development` เพื่อข้าม guard นี้

---

### DB connection ล้มเหลว — `asyncpg.exceptions.ConnectionFailure`

**สาเหตุ:** PostgreSQL ยังไม่พร้อม หรือ `DATABASE_URL` ผิด

```bash
# ตรวจสอบ container status
docker compose ps

# รอให้ db ready แล้ว restart backend
docker compose restart backend

# ถ้าใช้ SQLite (development) ปล่อยว่าง DATABASE_URL ไว้
unset DATABASE_URL
make run
```

`/health/ready` จะคืน `{"db_ok": false}` ถ้า DB ยังไม่เชื่อมต่อได้

---

### `422 Validation Error` ทุก request ไปยัง `/check`

**สาเหตุ:** เกิดขึ้นเมื่อ `from __future__ import annotations` อยู่ใน router ที่ใช้ `@limiter.limit` — ปัญหานี้ถูกแก้แล้วใน v1.5.0

ถ้ายังเจออยู่ใน development build ที่แก้ code เอง ให้ลบ `from __future__ import annotations` ออกจาก `routers/check.py`

---

### WHOIS / TLS lookup ช้า หรือ timeout ตลอด

**สาเหตุ:** network block หรือ provider rate-limit

```bash
# ปิด network lookups ชั่วคราว
ENABLE_WHOIS=false
ENABLE_TLS=false

# หรือลด timeout
NETWORK_TIMEOUT=1.5
```

Prometheus counter `phish_network_timeout_total{kind="whois"}` บอกอัตรา timeout — ถ้าสูงผิดปกติให้ปิด WHOIS

---

### Redis ไม่เชื่อมต่อ

Backend fallback ไปใช้ in-process cache อัตโนมัติเมื่อ Redis หาไม่เจอ ไม่ต้อง restart ระบบยังทำงานได้
ดู log `WARNING: Redis unavailable, using in-process cache` เพื่อยืนยัน

```bash
# ตรวจสอบ Redis
docker compose exec redis redis-cli ping
# PONG = OK

# ถ้า Redis ตาย restart
docker compose restart redis
```

---

## LINE Bot

### Webhook ตอบ 401 — signature validation failed

**สาเหตุ:** `LINE_CHANNEL_SECRET` ไม่ตรงกับที่ตั้งใน LINE Developers Console

```bash
# ตรวจสอบ env
echo $LINE_CHANNEL_SECRET

# ดู error detail
docker compose logs backend | grep "line.*signature"
```

ตรวจสอบว่า webhook URL ใน LINE Developers Console ตรงกับ deployment จริง (`https://your-domain/api/v1/line/webhook`)

---

### Bot ไม่ตอบกลับ

1. ตรวจสอบ webhook URL ใน LINE Developers Console ว่า Verify แล้ว
2. ตรวจสอบ `LINE_CHANNEL_TOKEN` ไม่หมดอายุ
3. ดู log `docker compose logs backend | grep line_bot`

---

## Dashboard

### Login ล้มเหลว — 503

**สาเหตุ:** `ADMIN_PASSWORD_HASH` ไม่ได้ตั้งไว้ — dashboard login จงใจปิดเมื่อไม่มี hash

```bash
# สร้าง hash แล้วตั้งใน .env
python -c "from passlib.context import CryptContext; \
  print(CryptContext(['bcrypt']).hash('your-password'))"
# ใส่ผลลัพธ์เป็น ADMIN_PASSWORD_HASH=...
```

---

### Dashboard build ล้มเหลว

```bash
cd dashboard
npm install
npm run build   # ดู error output

# ถ้า lint error
npm run lint -- --fix
```

---

## ML Pipeline

### `make evaluate-gate` fail — Thai recall ต่ำกว่า 0.85

**สาเหตุ:** โมเดลเก่าหรือ feature schema ไม่ตรงกัน

```bash
# retrain จาก scratch
make train
make evaluate-gate
```

ถ้า recall ยังต่ำหลัง retrain ให้ดู `reports/confusion_matrix.png` และ `reports/missed_generic_analysis.md`

---

### Schema mismatch error ตอน boot

```
ValueError: model features.json disagrees with ORDERED_FEATURES
```

**แก้ไข:** retrain โมเดลใหม่หลังแก้ `phish_features/schema.py`

```bash
make train
# commit models/ ที่ regenerate แล้วพร้อมกับ code change
```

---

## CI

### `sync-docs-check` fail

```bash
# อัปเดต metric sentinels ใน docs
make evaluate      # สร้าง reports/evaluation_summary.json ใหม่
make sync-docs     # inject ตัวเลขเข้า docs
git add README.md  # commit sentinel updates
```

---

## ขอความช่วยเหลือเพิ่มเติม

- เปิด Issue: https://github.com/reenx8/security/issues
- ดู [`CONTRIBUTING.md`](../CONTRIBUTING.md) สำหรับ workflow การรายงานปัญหา
- Security issues: ดู [`SECURITY.md`](../SECURITY.md) — ห้าม file public issue
