# รู้ทัน — Standalone Console (admin + user, one file)

`RuThan-AdminConsole.html` is a single self-contained file with three surfaces,
switchable from the bottom-right switcher:

| Surface | Thai | Access |
|---|---|---|
| `operator` | คอนโซลเจ้าหน้าที่ (admin) | **login required** (API key) |
| `citizen`  | พอร์ทัลประชาชน (public user) | open, no login |
| `extension`| ตัวอย่างส่วนขยายเบราว์เซอร์ | demo |

## Connecting it to the backend (REENX8/Security FastAPI)

The console talks to the existing `/api/v1` API. Point it at your backend in
**either** way:

1. Edit the meta tag in the file:
   `<meta name="ruthan-api" content="https://your-backend.example.go.th">`
2. Or from the browser console (overrides the meta tag):
   `localStorage.setItem("ruthan-api-base", "https://your-backend.example.go.th")`

Leave it empty to call the **same origin** (serve the file from the API host).

### Endpoints used
- `POST /api/v1/check`      — URL scan (admin: sends `X-API-Key`)
- `GET  /api/v1/stats`      — overview KPIs/charts (also used to validate login)
- `GET  /api/v1/history`    — recent checks table
- `GET  /api/v1/campaigns`  — phishing campaign clustering
- `POST /api/v1/feedback`   — public citizen report (no key)

### Admin login
The operator surface is gated. Enter the backend `X-API-Key`
(`settings.api_key`, default `dev-local-key-change-me`). The key is kept in
`sessionStorage` and sent as `X-API-Key` on every admin request; "ออกจากระบบ"
clears it. If the backend is unreachable, a **demo (offline)** mode renders the
bundled sample data so the UI is still reviewable.

### Public user page
The citizen portal needs no login. It calls the backend when available and
gracefully falls back to the bundled client-side rules engine (which mirrors
`phish_features/rules.py`) when offline/unauthed. Reports go to the public
`/api/v1/feedback` endpoint.
