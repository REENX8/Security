# Thai Phishing Detector — Browser Extension

Manifest V3 extension that intercepts navigation to phishing URLs in real time
and warns the user with a full-page interstitial. Works in Chrome, Edge, Brave,
Opera and Firefox 121+.

> Source: this folder. Privacy policy: [`PRIVACY.md`](PRIVACY.md).
> Backend repo: <https://github.com/reenx8/security>.

---

## 🚀 Installation — end users

### Option A. Install the packaged `.zip` (recommended)

1. Download `thai-phishing-detector-vX.Y.Z.zip` from the [Releases page](
   https://github.com/reenx8/security/releases) (or build it yourself with
   `python scripts/build_extension.py`).
2. Extract the `.zip` to a folder you will not delete.
3. Follow the per-browser steps below.

### Option B. Load straight from the cloned repo

Skip downloading and point your browser at this `extension/` directory.

### Chrome / Brave / Opera

1. Visit `chrome://extensions` (or `brave://extensions`).
2. Toggle **Developer mode** (top-right).
3. Click **Load unpacked** and choose the extracted folder (or
   `Security/extension/`).
4. Open the extension's **Options**, point it at your API endpoint
   (default `http://localhost:8000`) and paste your **API key**.

### Microsoft Edge

1. Visit `edge://extensions`.
2. Toggle **Developer mode** (bottom-left).
3. Click **Load unpacked**.
4. Configure Options as above.

### Firefox 121 +

Firefox only loads signed extensions outside of the Developer Edition / Nightly,
so use one of:

- **Firefox Developer Edition / Nightly**:
  1. Visit `about:debugging#/runtime/this-firefox`.
  2. Click **Load Temporary Add-on…** and pick `manifest.json` from the
     extracted folder. Lives for the session only.
- **Stable Firefox**: install via the
  [Add-ons Store listing](#-firefox-add-ons-store) (once submitted) which
  provides a signed build.

> **Note on Firefox MV3.** Firefox 121+ supports `background.service_worker`
> with quirks (event-page semantics). The extension uses standard `chrome.*`
> APIs, all of which are aliased by Firefox. The warning interstitial,
> notifications, popup, options and `chrome.storage.session` bypass have all
> been validated against the Mozilla MV3 reference.

---

## 🔧 Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| API endpoint  | `http://localhost:8000` | Backend base URL |
| API key       | `dev-local-key-change-me` | Sent as `X-API-Key` header |
| Dashboard URL | `http://localhost:5173` | Opens when you click the dashboard link / a phishing notification |
| Enable detection | on | Master switch |
| Desktop notifications | on | Toast on phishing verdict |
| Block phishing pages | on | Show the full-page warning interstitial |

Open the **Options** page from `chrome://extensions → Details → Extension
options`, or from the popup footer.

---

## 🎨 Behaviour

| Verdict | Badge | Notification | Interstitial |
|---------|-------|--------------|--------------|
| `safe`        | green `✓` | — | — |
| `suspicious`  | yellow `?` | — | — |
| `phishing`    | red `!`    | yes (if enabled) | yes (if enabled) |
| `unverified`  | grey `·`   | — | — |

The interstitial offers **← กลับไปหน้าก่อนหน้า** (go back) and **ดำเนินการต่อ
(รับความเสี่ยงเอง)** (proceed anyway with confirmation). Hosts the user
proceeds on are stored in `chrome.storage.session` and skipped until the
browser restarts.

---

## 📦 Building a release `.zip`

```bash
python scripts/build_extension.py
# -> dist/thai-phishing-detector-v{VERSION}.zip
```

The script:

- reads the version from `extension/manifest.json`
- excludes `.md` files, OS junk and dev folders
- verifies every file the manifest references actually exists
- writes one flat `.zip` (manifest at root) — exactly the format the
  Chrome Web Store and the Firefox Add-ons Store accept.

CI runs this on every push to `main`/`feature/**` and uploads the artifact
(see [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

---

## 🏪 Chrome Web Store — submission checklist

> Submission requires a one-time **$5 USD** Chrome Web Store developer
> registration. Allow up to a few business days for review.

1. **Bump the version** in `extension/manifest.json` (every upload must
   strictly increment).
2. `python scripts/build_extension.py` to produce the `.zip`.
3. Sign in to the [Chrome Web Store developer dashboard](
   https://chrome.google.com/webstore/devconsole).
4. **Create a new item** and upload the `.zip`.
5. Fill in the store listing:
   - **Description** — copy the long description from the root [README.md](
     ../README.md).
   - **Icon**: `icons/icon128.png` (already 128 × 128).
   - **Screenshots** (1280 × 800 or 640 × 400) — capture the popup, the
     warning interstitial and the dashboard. Minimum one, recommended 3-5.
   - **Promotional tile** (440 × 280) — *optional*.
   - **Category** — *Security / Privacy*.
   - **Language** — *Thai* primary, *English* secondary.
6. Privacy practices tab:
   - **Privacy policy URL** — point to the published [`PRIVACY.md`](
     PRIVACY.md) (GitHub renders Markdown publicly).
   - **Single purpose** — *"Detect phishing URLs targeting Thai public-sector
     websites and warn the user before sensitive data is entered."*
   - **Permission justifications**:
     | Permission | Justification |
     |------------|---------------|
     | `webNavigation` | Required to observe top-level navigations and check the URL with the backend before the page can collect credentials. |
     | `tabs` + `activeTab` | Required to redirect the active tab to the local warning page (`warning.html`) when a phishing verdict is returned, and to read the active tab from the popup. |
     | `notifications` | Used to alert the user when a phishing page is detected. |
     | `storage` | Used to persist user settings, the per-tab verdict and the last-100 results client-side only. |
     | Host permission `<all_urls>` | Required because phishing can occur on any host; the extension does not run content scripts on these pages, it only reads the URL being navigated to. |
   - **Data usage** — *"The extension transmits the URL being navigated to,
     and only that, to the user-configured backend endpoint. No personal
     data, cookies, form input or page content is collected, sold or shared."*
7. **Distribution** — choose visibility (Public / Unlisted / Private), set
   the regions.
8. Click **Submit for review**.

---

## 🦊 Firefox Add-ons Store

The same `.zip` works for `addons.mozilla.org` (AMO). The manifest already
declares `browser_specific_settings.gecko.id` and a minimum Firefox version,
so the AMO validator accepts the package without changes.

1. Sign in to <https://addons.mozilla.org/developers/>.
2. **Submit a New Add-on** → upload the `.zip`.
3. Choose **Listed** distribution to publish on AMO.
4. Mozilla will sign the build and serve `.xpi` to end users.

---

## 🪟 Microsoft Edge Add-ons

The same `.zip` again works for the Edge Add-ons store.

1. Sign in to the
   [Microsoft Partner Center for Edge](https://partner.microsoft.com/en-us/dashboard/microsoftedge).
2. **Create new extension** → upload the `.zip`.
3. Fill in the listing (very similar fields to Chrome).
4. Submit for certification.

---

## 🛠️ Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Badge stays grey on every page | Backend unreachable. Open Options, verify the API endpoint and key. `curl <endpoint>/health`. |
| Popup says *"ยังไม่มีข้อมูลสำหรับหน้านี้"* | Open a fresh tab and navigate — the extension only checks `webNavigation.onBeforeNavigate` events. |
| Phishing site loads briefly before the warning | Expected: the verdict is async (typically <500 ms). The interstitial replaces the original page once it arrives. |
| `Failed to fetch` errors in the console | CORS — make sure `CORS_ORIGINS` in the backend includes the dashboard URL, and the `chrome-extension://...` regex is registered (it is by default). |
| Firefox: badge updates but no interstitial | Some Firefox MV3 builds restrict `chrome.tabs.update` to extension-internal URLs only if the tab origin matches. The fallback notification still fires. |
| Need to wipe the extension state | Options page → **ล้างประวัติการตรวจสอบ** ("Clear history"). |

---

## 🔒 Security notes

- The extension never stores or transmits the API key to anywhere except the
  endpoint you configure. It lives in `chrome.storage.local`, which is
  per-profile.
- The default API key is `dev-local-key-change-me`. **Always rotate this in
  production** by setting `API_KEY` on the backend and the matching value in
  the extension Options.
- For deployments shared with others, terminate the backend behind TLS
  (Caddy / nginx / Cloud Run / a reverse proxy) and update the endpoint to
  `https://...`.
