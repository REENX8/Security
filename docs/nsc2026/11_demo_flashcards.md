# Demo Flashcards — URL ที่จะใช้สาธิตในรอบนำเสนอ

> พิมพ์หน้าเดียว A5 พกติดตัวระหว่างสาธิต โชว์ทีละ pattern ตามลำดับ
>
> ก่อนเริ่มสาธิต รัน `scripts/demo_setup.sh` แล้ว
> `scripts/demo_verify.py` จะตรวจให้ว่า 6 URL ด้านล่าง verdict ตรงตามคาด

---

## 🎬 ลำดับการสาธิต (5 นาที)

### Step 1 — URL ที่ปลอดภัย (โชว์ baseline ไม่ false positive)

| URL | คาดหวัง | จุดที่พูด |
|-----|---------|----------|
| `https://www.bot.or.th` | ✅ safe (0.0–0.2) | "เว็บธนาคารแห่งประเทศไทยจริง — score ใกล้ 0, label safe" |
| `https://chula.ac.th` | ✅ safe (0.0–0.2) | "เว็บจุฬาฯ จริง — ไม่เข้าข่ายฟิชชิงเลย" |

### Step 2 — Typosquat + cheap TLD (โชว์ ML จับ pattern)

| URL | คาดหวัง | จุดที่พูด |
|-----|---------|----------|
| `http://0bec-go-th.xyz/login` | 🚨 phishing (0.85+) | "พิมพ์ 0 (ศูนย์) แทน o, ใช้ TLD .xyz — Rules Engine ระบุ rule_id `TYPOSQUAT_CRED` + `CHEAP_TLD_PLAIN`" |

### Step 3 — Subdomain spoof (โชว์โจมตี advanced)

| URL | คาดหวัง | จุดที่พูด |
|-----|---------|----------|
| `https://moe.go.th.verify-login.top/signin` | 🚨 phishing (0.9+) | "ดูเหมือน moe.go.th แต่จริง ๆ host คือ verify-login.top — feature `is_typosquat` + `path_brand_hit` จับได้" |

### Step 4 — IP-based + path-brand bait

| URL | คาดหวัง | จุดที่พูด |
|-----|---------|----------|
| `http://203.0.113.45/obec/secure/login` | 🚨 phishing (0.85+) | "IP เปล่า + คำว่า obec ใน path + login keyword → rule `IP_CRED` + `PATH_BRAND_BAIT`" |

### Step 5 — @-trick (โชว์ catch trick URL classic)

| URL | คาดหวัง | จุดที่พูด |
|-----|---------|----------|
| `https://www.ku.ac.th@phish-site.xyz/login` | 🚨 phishing (0.95+) | "เครื่องหมาย @ ใน URL ทำให้ดู ku.ac.th แต่จริง ๆ ไปที่ phish-site.xyz — rule `AT_TRICK` pin ทันที" |

### Step 6 — Brand Watchlist webhook (โชว์ feature ที่หน่วยงานใช้จริง)

1. ในหน้า dashboard เปิด `/watchlist` → ลงทะเบียนแบรนด์ "krungthai" + webhook
   URL (ใช้ `https://webhook.site/<unique>` แสดงให้กรรมการเห็น)
2. ตรวจ URL `http://krungthai-secure-update.club/login`
3. รอ 2 วินาที — มาแสดงใน webhook.site = ข้อความ LINE format

### Step 7 — STIX 2.1 public threat feed

```
curl -s http://localhost:8000/api/v1/feed.stix | jq '.objects | length'
```

โชว์ว่ามี indicator มาตรฐาน STIX 2.1 พร้อมส่งเข้า SIEM ของหน่วยงาน

---

## 🎯 ประโยคปิด demo

> "ระบบทำงานครบทั้ง 6 หมวด pattern ฟิชชิงที่ ETDA report กับ rule_id ที่อธิบายได้
> ทุกการตัดสินใจ และมีช่องทางให้หน่วยงานรับแจ้งเตือนผ่าน LINE ทันที พร้อม
> public feed ให้ชุมชน security ใช้ฟรี"

---

## 🛟 Backup plan

* **Demo fails on judge laptop:** เปิด `docs/nsc2026/demo_video.mp4` แทน
* **Network down:** ระบบรัน local SQLite + cached model — ไม่ต้องเน็ตในการ
  สาธิตทั้งหมด (extension ก็ใช้ http://localhost:8000)
* **Reset ระหว่างรอบ:** `scripts/demo_reset.sh` คืน DB ใน <30 วินาที
