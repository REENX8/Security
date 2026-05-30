# รู้ทัน — Standalone Console (admin + user, one static file)

`RuThan-AdminConsole.html` is a single self-contained **static web app** with
three surfaces, switchable from the bottom-right switcher:

| Surface | Thai | Access |
|---|---|---|
| `operator` | คอนโซลเจ้าหน้าที่ (admin) | **login required** (username + password) |
| `citizen`  | พอร์ทัลประชาชน (public user) | open, no login |
| `extension`| ตัวอย่างส่วนขยายเบราว์เซอร์ | demo |

It is fully static — just open the file (or host it anywhere). No build step,
no server required for the login itself.

## Admin login (username + password)

The operator surface is gated by a real login form. Accounts live in the
`AUTH_USERS` block near the top of the data module inside the file:

```js
const AUTH_USERS = {
  "admin":   "ruthan@2026",   // ← change before real use
  "officer": "daan@2026",
};
```

Edit that object to add/remove staff or change passwords, then re-share the
file. The session is kept in `sessionStorage` (clears on tab close); the
"ออกจากระบบ" button logs out. Because this is a static app, the check happens
in the browser — treat it as a front-door gate, not server-grade security.

## Connecting to the backend (optional)

The console renders bundled sample data out of the box. To pull **live** data
from the REENX8/Security FastAPI backend:

1. Point it at the backend — either edit the meta tag:
   `<meta name="ruthan-api" content="https://your-backend.example.go.th">`
   or from the browser console:
   `localStorage.setItem("ruthan-api-base", "https://your-backend.example.go.th")`
   (empty = same origin).
2. Set the backend key once in the file so it's sent automatically after login:
   `const ADMIN_API_KEY = "dev-local-key-change-me";` → your real key.

Endpoints used: `POST /api/v1/check`, `GET /api/v1/stats`, `GET /api/v1/history`,
`GET /api/v1/campaigns`, and the public `POST /api/v1/feedback`. If the backend
is unreachable, every surface gracefully falls back to the bundled client-side
rules engine (mirrors `phish_features/rules.py`), so the app always works.

The public citizen portal needs no login and submits reports to the public
`/api/v1/feedback` endpoint.
