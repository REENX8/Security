# Quickstart — รู้ทัน Thai Phishing Detector

เริ่มต้นในไม่กี่นาที เลือกวิธีที่เหมาะกับคุณ

---

## วิธีที่ 1 — Docker Compose (แนะนำ)

ต้องการ: Docker 24+, Docker Compose v2

```bash
git clone https://github.com/reenx8/security.git
cd security

cp .env.example .env
# แก้ค่า API_KEY ให้เป็นค่าของคุณก่อน deploy จริง

docker compose up -d --build
```

ตรวจสอบว่าขึ้นแล้ว:

```bash
curl http://localhost:8000/version
# {"backend":"1.6.0","phish_features":"1.1.0","schema":"1.6.0"}

curl -X POST http://localhost:8000/api/v1/check \
     -H "Content-Type: application/json" \
     -d '{"url":"https://krungthai-secure.online/login"}'
# {"label":"phishing","score":0.99,...}
```

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Dashboard**: `make dashboard` → http://localhost:5173

---

## วิธีที่ 2 — Python standalone (SQLite, ไม่ต้อง Docker)

ต้องการ: Python 3.10+

```bash
git clone https://github.com/reenx8/security.git
cd security

make install      # ติดตั้ง dependencies
make run          # → http://localhost:8000
```

ใช้ SQLite อัตโนมัติเมื่อไม่ตั้ง `DATABASE_URL` เหมาะสำหรับ development และทดสอบ

---

## วิธีที่ 3 — Render Blueprint (cloud, one-click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

`render.yaml` สร้าง backend + PostgreSQL ใน Render โดยอัตโนมัติ ใช้เวลา ~3 นาที

**ต้องตั้งค่า environment variables ใน Render dashboard หลัง deploy:**

| Variable | ค่าที่ต้องตั้ง |
|----------|--------------|
| `API_KEY` | สุ่มสตริงใหม่ (อย่าใช้ค่า default) |
| `JWT_SECRET` | `openssl rand -hex 32` |
| `ADMIN_PASSWORD_HASH` | ดูวิธีสร้างด้านล่าง |

สร้าง bcrypt hash สำหรับรหัสผ่าน admin:

```bash
python -c "from passlib.context import CryptContext; \
  print(CryptContext(['bcrypt']).hash('your-password-here'))"
```

---

## ขั้นตอนต่อไป

| อยากทำอะไร | ดูที่ |
|-----------|------|
| ติดตั้ง browser extension | [`extension/README.md`](extension/README.md) |
| ตั้งค่า LINE bot | [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) |
| Deploy จริงบน production | [`docs/DEPLOY.md`](docs/DEPLOY.md) |
| รัน ML pipeline / retrain | [`README.md#ml-pipeline`](README.md#ml-pipeline) |
| แก้ปัญหาที่พบบ่อย | [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) |
| มีส่วนร่วมพัฒนา | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
