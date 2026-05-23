# Privacy Policy — Thai Phishing Detector

*Effective: 2026-05-23*

This document explains exactly what the **Thai Phishing Detector** browser
extension does with your data. It is provided to satisfy the Chrome Web Store,
Microsoft Edge Add-ons, and Mozilla Add-ons review requirements.

## TL;DR
- The extension sends **only the URL you are navigating to** to your
  configured backend server, and gets back a phishing verdict.
- It does **not** collect personal data, browsing history, account
  credentials, cookies, form input, or page content.
- It does **not** sell, share, or transmit data to any third-party server.
  All requests go to **the API endpoint you configure yourself** (default:
  `http://localhost:8000`).

## What the extension sends to the server
For every top-level page navigation in your browser, the extension issues a
single HTTPS request:

```
POST {YOUR_API_ENDPOINT}/api/v1/check
Headers:  X-API-Key: {YOUR_API_KEY}
Body:     { "url": "<the URL you are navigating to>" }
```

That is the entirety of what is transmitted. No other data leaves the
browser.

## What is stored locally
The extension stores the following in your browser's `chrome.storage.local`
and `chrome.storage.session`, never on a remote server:

| Key            | Contents | Lifetime |
|----------------|----------|----------|
| `settings`     | API endpoint URL, API key, dashboard URL, notification + blocking toggles | until uninstalled or cleared |
| `tabResults`   | Latest verdict per open tab (URL, score, label, reason) | until the tab is closed |
| `history`      | Last 100 verdicts (URL, score, label, reason, timestamp) | until cleared from Options |
| `bypass`       | Hosts where the user clicked "Proceed anyway" | until the browser restarts |

You can wipe `history` and `tabResults` at any time via the
**"ล้างประวัติการตรวจสอบ" / "Clear history"** button on the Options page.

## Permissions explained
| Permission              | Why it is requested |
|-------------------------|---------------------|
| `webNavigation`         | To observe top-level page navigations so a URL can be checked *before* you interact with the page. |
| `notifications`         | To raise a desktop alert when a phishing page is detected. |
| `storage`               | To remember your settings and last-100 history client-side. |
| `tabs` + `activeTab`    | To redirect the current tab to the warning interstitial when a phishing URL is detected, and to read the active tab in the popup. |
| `host_permissions: *`   | To allow the extension's content layer to act on URLs the user navigates to (URLs are not fetched by the extension itself). |

## Third-party services
The extension talks to **only one server**: the API endpoint you configure on
the Options page. That server is operated either by you or by your
organisation — the maintainers of this extension do not operate any hosted
service.

## Data retention on the server side
What the backend server logs is up to its operator. The reference
implementation in this repository stores every checked URL plus its verdict
in a Postgres `url_checks` table. Operators are responsible for setting an
appropriate retention policy.

## Contact
For privacy questions or removal requests, file an issue at
<https://github.com/reenx8/security/issues>.
