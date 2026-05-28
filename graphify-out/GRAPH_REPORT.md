# Graph Report - .  (2026-05-28)

## Corpus Check
- 15 files · ~75,914 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1294 nodes · 2395 edges · 68 communities (61 shown, 7 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 366 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_URL Watchlist & Batch Check|URL Watchlist & Batch Check]]
- [[_COMMUNITY_Feedback & Analytics Dashboard|Feedback & Analytics Dashboard]]
- [[_COMMUNITY_FastAPI Backend & Auth|FastAPI Backend & Auth]]
- [[_COMMUNITY_Heuristic Rules Engine|Heuristic Rules Engine]]
- [[_COMMUNITY_ML Training Pipeline|ML Training Pipeline]]
- [[_COMMUNITY_Browser Extension Navigation|Browser Extension Navigation]]
- [[_COMMUNITY_Lexical Feature Extraction|Lexical Feature Extraction]]
- [[_COMMUNITY_Brand Watchlist & Webhooks|Brand Watchlist & Webhooks]]
- [[_COMMUNITY_External Threat Feed Ingestion|External Threat Feed Ingestion]]
- [[_COMMUNITY_Feature Extractor & Scorer|Feature Extractor & Scorer]]
- [[_COMMUNITY_Campaign Clustering|Campaign Clustering]]
- [[_COMMUNITY_React Dashboard UI|React Dashboard UI]]
- [[_COMMUNITY_NSC 2026 Submission Docs|NSC 2026 Submission Docs]]
- [[_COMMUNITY_LINE Bot Integration|LINE Bot Integration]]
- [[_COMMUNITY_IDNHomoglyph Defence|IDN/Homoglyph Defence]]
- [[_COMMUNITY_Citizen Report Portal|Citizen Report Portal]]
- [[_COMMUNITY_PostgreSQL Data Models|PostgreSQL Data Models]]
- [[_COMMUNITY_URL Unshortener|URL Unshortener]]
- [[_COMMUNITY_Content-based Fallback|Content-based Fallback]]
- [[_COMMUNITY_STIX Threat Feed Export|STIX Threat Feed Export]]
- [[_COMMUNITY_CICD Pipeline|CI/CD Pipeline]]
- [[_COMMUNITY_Docker & Deployment|Docker & Deployment]]
- [[_COMMUNITY_Demo & Presentation Scripts|Demo & Presentation Scripts]]
- [[_COMMUNITY_Test Suite|Test Suite]]
- [[_COMMUNITY_Configuration & Settings|Configuration & Settings]]
- [[_COMMUNITY_Whitelist Builder|Whitelist Builder]]
- [[_COMMUNITY_Thai Domain Corpus|Thai Domain Corpus]]
- [[_COMMUNITY_API Rate Limiting|API Rate Limiting]]
- [[_COMMUNITY_Feedback Auto-Retrain|Feedback Auto-Retrain]]
- [[_COMMUNITY_Extension Options UI|Extension Options UI]]
- [[_COMMUNITY_Warning Page|Warning Page]]
- [[_COMMUNITY_ML Model Evaluation|ML Model Evaluation]]
- [[_COMMUNITY_NSC QA & Flashcards|NSC QA & Flashcards]]
- [[_COMMUNITY_External Citations & References|External Citations & References]]
- [[_COMMUNITY_Shared phish_features Package|Shared phish_features Package]]
- [[_COMMUNITY_Data Export & Reporting|Data Export & Reporting]]
- [[_COMMUNITY_Popup HTMLJS Interface|Popup HTML/JS Interface]]
- [[_COMMUNITY_Security Policy|Security Policy]]
- [[_COMMUNITY_Contribution Guidelines|Contribution Guidelines]]
- [[_COMMUNITY_Changelog & Versioning|Changelog & Versioning]]
- [[_COMMUNITY_Render Deployment Config|Render Deployment Config]]
- [[_COMMUNITY_Dashboard Public Assets|Dashboard Public Assets]]
- [[_COMMUNITY_ML Feature Schema v1.4.0|ML Feature Schema v1.4.0]]
- [[_COMMUNITY_Async Task Workers|Async Task Workers]]
- [[_COMMUNITY_Logging & Monitoring|Logging & Monitoring]]
- [[_COMMUNITY_Seed Corpus Management|Seed Corpus Management]]
- [[_COMMUNITY_NSC 2026 User Guide|NSC 2026 User Guide]]
- [[_COMMUNITY_NSC 2026 Installation Guide|NSC 2026 Installation Guide]]
- [[_COMMUNITY_NSC 2026 Summary Form|NSC 2026 Summary Form]]
- [[_COMMUNITY_NSC 2026 Poster|NSC 2026 Poster]]
- [[_COMMUNITY_NSC 2026 Video Script|NSC 2026 Video Script]]
- [[_COMMUNITY_NSC 2026 Rubric Mapping|NSC 2026 Rubric Mapping]]
- [[_COMMUNITY_NSC 2026 Cover Proposal|NSC 2026 Cover Proposal]]
- [[_COMMUNITY_NSC 2026 Checklist|NSC 2026 Checklist]]
- [[_COMMUNITY_NSC 2026 Disclaimer|NSC 2026 Disclaimer]]
- [[_COMMUNITY_NSC 2026 Proposal|NSC 2026 Proposal]]
- [[_COMMUNITY_Extension Privacy Policy|Extension Privacy Policy]]
- [[_COMMUNITY_Extension README|Extension README]]
- [[_COMMUNITY_Extension Icons|Extension Icons]]
- [[_COMMUNITY_ROC Curve & Evaluation Plots|ROC Curve & Evaluation Plots]]
- [[_COMMUNITY_Confusion Matrix|Confusion Matrix]]
- [[_COMMUNITY_Feature Importance Plot|Feature Importance Plot]]
- [[_COMMUNITY_Thai vs Generic Recall Chart|Thai vs Generic Recall Chart]]
- [[_COMMUNITY_About Page|About Page]]

## God Nodes (most connected - your core abstractions)
1. `FeedPoller` - 35 edges
2. `DbWhitelistEntry` - 30 edges
3. `Feedback` - 30 edges
4. `Whitelist` - 29 edges
5. `UrlCheck` - 27 edges
6. `Thai Public-Sector Phishing URL Detection System` - 26 edges
7. `Thai Phishing Detection System` - 26 edges
8. `ExternalFeedSource` - 25 edges
9. `Label` - 20 edges
10. `BrandWatch` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Public Threat Feed (JSON/CSV/STIX 2.1)` --semantically_similar_to--> `OpenPhish Live Phishing URL Feed`  [INFERRED] [semantically similar]
  README.md → docs/nsc2026/02_full_report.md
- `Citizen Report Portal` --semantically_similar_to--> `LINE Messaging API Bot`  [INFERRED] [semantically similar]
  README.md → docs/nsc2026/03_summary_form.md
- `Docker Compose Deployment (backend + PostgreSQL)` --semantically_similar_to--> `Render Blueprint Web Service (phish-backend)`  [INFERRED] [semantically similar]
  docker-compose.yml → render.yaml
- `Public Threat Feed (JSON/CSV/STIX 2.1)` --implements--> `STIX 2.1 Threat Intelligence Standard`  [INFERRED]
  README.md → docs/nsc2026/01_proposal.md
- `Citizen Report Portal (No-Auth Public Reporting)` --semantically_similar_to--> `Extension Privacy Policy`  [INFERRED] [semantically similar]
  README.md → extension/PRIVACY.md

## Hyperedges (group relationships)
- **Thai Phishing Detection Core Pipeline** — security_readme_phish_features_package, security_readme_ml_ensemble, security_readme_rules_engine [EXTRACTED 0.95]
- **NSC 2026 Presentation Day Artifacts** — nsc2026_11_demo_flashcards_demo_flashcards, nsc2026_12_qa_cheatsheet_qa_cheatsheet, nsc2026_11_demo_flashcards_demo_scripts [EXTRACTED 0.95]
- **Citizen-Facing Access Channels** — security_readme_browser_extension, security_readme_citizen_report_portal, security_readme_line_messaging_bot [INFERRED 0.85]

## Communities (68 total, 7 thin omitted)

### Community 0 - "URL Watchlist & Batch Check"
Cohesion: 0.05
Nodes (57): addWatchlistEntry(), BASE_URL, checkBatch(), checkUrl(), deleteWatchlistEntry(), getCampaigns(), getDomainHistory(), getFeedback() (+49 more)

### Community 1 - "Feedback & Analytics Dashboard"
Cohesion: 0.08
Nodes (53): getFeedbackExportUrl(), useFeedback(), FeedbackSource, DayBucket, ErrorResponse, FeedbackCreate, FeedbackListResponse, FeedbackOut (+45 more)

### Community 2 - "FastAPI Backend & Auth"
Cohesion: 0.07
Nodes (48): get_scorer(), Shared FastAPI dependencies., Reject requests without a valid ``X-API-Key`` header., Return the loaded scorer, or raise 503 if the model is unavailable., verify_api_key(), AppError, _json(), ModelNotLoadedError (+40 more)

### Community 3 - "Heuristic Rules Engine"
Cohesion: 0.09
Nodes (38): str, Heuristic Rules Engine -- a transparent layer on top of the ML scorer.  ML gives, Trusted brand sits in URL path but not in host -- a brand-bait kit., IP host + credential keyword -- almost always phishing., Exact whitelist match should never be phishing.      A safety net against false, Cheap TLD without HTTPS -- low-effort phishing kit., Outcome of running the engine over one (url, features) pair., Apply a list of rules to a (url, feature) pair. (+30 more)

### Community 4 - "ML Training Pipeline"
Cohesion: 0.07
Nodes (39): DataFrame, main(), Build the shipped whitelist artifact from the curated CSV.  Run this first. It p, ensure_dirs(), Shared paths and constants for the ML pipeline., _enforce_primary_threshold(), _eval_holdout_csv(), evaluate_real_holdout() (+31 more)

### Community 5 - "Browser Extension Navigation"
Cohesion: 0.10
Nodes (32): checkUrl(), buildWarningUrl(), handleNavigation(), isCheckable(), safeHost(), BADGE, clearBadge(), setBadge() (+24 more)

### Community 6 - "Lexical Feature Extraction"
Cohesion: 0.10
Nodes (37): _count_login_keywords(), _count_query_params(), count_subdomains(), extract_lexical(), get_host(), host_is_ip(), normalize_url(), bool (+29 more)

### Community 7 - "Brand Watchlist & Webhooks"
Cohesion: 0.13
Nodes (34): BrandWatch, One row per webhook attempt -- success or failure., WebhookDelivery, _brand_of(), _is_line_notify(), _line_payload(), maybe_alert(), _post_sync() (+26 more)

### Community 8 - "External Threat Feed Ingestion"
Cohesion: 0.11
Nodes (23): _fetch_feed_urls(), _fetch_urlhaus(), _is_thai_targeting(), _load_thai_brands(), _load_thai_phish_seed(), main(), bool, int (+15 more)

### Community 9 - "Feature Extractor & Scorer"
Cohesion: 0.07
Nodes (20): FeatureExtractor, bool, FeatureExtractor, float, str, build_extractor(), Construct the FeatureExtractor used for serving., load_scorer() (+12 more)

### Community 10 - "Campaign Clustering"
Cohesion: 0.08
Nodes (33): alignment_note, alignment_score, cross_validation, cv_f1_mean, cv_f1_std, cv_note, generic_real_holdout, mean_score (+25 more)

### Community 11 - "React Dashboard UI"
Cohesion: 0.11
Nodes (27): decode_idn(), fold_confusables(), has_mixed_script(), has_punycode(), normalize_for_lookup(), bool, str, Homoglyph / IDN normalisation utilities.  Phishers targeting Thai government and (+19 more)

### Community 12 - "NSC 2026 Submission Docs"
Cohesion: 0.10
Nodes (29): Browser Extension Icon 16px, Dashboard React App Entry (index.html), Brand Watchlist + Webhook, Browser Extension Manifest V3, Campaign Clustering Algorithm, CI Gate Thai Recall >= 0.85, Docker Compose Deployment, FastAPI Backend (+21 more)

### Community 13 - "LINE Bot Integration"
Cohesion: 0.14
Nodes (17): brand_label(), _lev_distance(), bool, int, str, Whitelist of trusted Thai domains + typosquat detection.  The whitelist is the a, An immutable, sorted set of trusted domains., Return ``(min_edit_distance, closest_domain)`` for ``host``.          Distance i (+9 more)

### Community 14 - "IDN/Homoglyph Defence"
Cohesion: 0.08
Nodes (26): action, default_icon, default_popup, default_title, author, browser_specific_settings, gecko, description (+18 more)

### Community 15 - "Citizen Report Portal"
Cohesion: 0.13
Nodes (25): build_fingerprint(), _path_shape(), Phishing campaign clustering.  A phishing campaign is a batch of URLs that share, Return a normalised path skeleton or '' when no path is present., Coarse signature of the host's last label., Deterministic clustering key.      ``<brand>|<tld>|<path-shape>`` is short and g, Upsert a campaign row for ``url`` and bump its counters.      Returns the campai, record_campaign() (+17 more)

### Community 16 - "PostgreSQL Data Models"
Cohesion: 0.08
Nodes (25): imputed_defaults, cert_age_days, domain_age_days, has_valid_cert, is_known_registrar, is_self_signed, tls_ok, whois_ok (+17 more)

### Community 17 - "URL Unshortener"
Cohesion: 0.15
Nodes (22): get_history(), get_stats(), insert_check(), Database read/write helpers for url_checks., Persist a scoring result and return the stored row., Return ``(total, rows)`` for a filtered, paginated history query., Aggregate dashboard statistics., Label (+14 more)

### Community 18 - "Content-based Fallback"
Cohesion: 0.13
Nodes (24): Background service that polls external threat feeds (OpenPhish, PhishTank).  URL, _url_hash(), _make_scorer(), _make_source(), _make_state(), ExternalFeedSource, Tests for external threat feed ingestion (FeedPoller)., Network error from OpenPhish raises so _poll_source can catch it. (+16 more)

### Community 19 - "STIX Threat Feed Export"
Cohesion: 0.13
Nodes (20): Thin adapter over the shared ``phish_features`` package.  There is intentionally, classify_tld(), _etld(), extract_features(), FeatureExtractor, _path_brand_hit(), bool, float (+12 more)

### Community 20 - "CI/CD Pipeline"
Cohesion: 0.11
Nodes (23): init_db(), Create tables if they do not exist (idempotent)., disclaimer(), health(), lifespan(), metrics_endpoint(), _rate_limited(), FastAPI application entry point. (+15 more)

### Community 21 - "Docker & Deployment"
Cohesion: 0.11
Nodes (24): ETDA Thai Cyberthreat Context (30,000+ phishing cases 2024), NSC 2026 Project Proposal (Category 23, Student Level), Random Forests (Breiman, Machine Learning, 2001), STIX 2.1 Threat Intelligence Standard, Unicode Technical Report #36: Unicode Security Considerations, XGBoost: A Scalable Tree Boosting System (Chen & Guestrin, KDD 2016), OpenPhish 2024-2025 Dataset, Path Impersonation Detection (v1.3.0) (+16 more)

### Community 22 - "Demo & Presentation Scripts"
Cohesion: 0.15
Nodes (21): bool, bytes, Request, str, _build_reply(), line_webhook(), LINE Messaging API webhook — phishing URL detection in Thai.  Setup:   1. Create, _send_reply() (+13 more)

### Community 23 - "Test Suite"
Cohesion: 0.15
Nodes (21): content_score_adjustment(), _is_private_host(), Lightweight content-based check for gray-zone URLs.  Fetches the HTML of a URL a, Return a score adjustment in [-0.20, +0.30] based on page content.      Positive, bool, float, str, _make_mock_client() (+13 more)

### Community 24 - "Configuration & Settings"
Cohesion: 0.16
Nodes (22): NSC 2026 Software License Agreement (Thai/English), OASIS STIX 2.1 Specification, OpenPhish Live Phishing URL Feed, Demo Flashcards for NSC 2026 Presentation, Demo Automation Scripts, Q&A Cheatsheet for NSC 2026 Presentation, Feedback-driven Auto-Retrain Pipeline, LINE Messaging API Bot (+14 more)

### Community 26 - "Thai Domain Corpus"
Cohesion: 0.09
Nodes (3): Integration tests for the v1.0 new routers: watchlist, feed, campaigns, domain h, No API key required -- this is intentional., test_feed_json_is_public()

### Community 27 - "API Rate Limiting"
Cohesion: 0.10
Nodes (20): dependencies, react, react-dom, react-router-dom, recharts, @tanstack/react-query, devDependencies, autoprefixer (+12 more)

### Community 28 - "Feedback Auto-Retrain"
Cohesion: 0.17
Nodes (13): Application settings (pydantic-settings, read from environment / .env)., Settings, str, BaseSettings, Path, build(), main(), bool (+5 more)

### Community 29 - "Extension Options UI"
Cohesion: 0.20
Nodes (18): _export(), main(), bool, int, Export confirmed feedback from the database and trigger a model retrain.  Usage:, Pull confirmed feedback rows from the DB; returns [] if DB unavailable., _retrain(), run() (+10 more)

### Community 30 - "Warning Page"
Cohesion: 0.13
Nodes (16): _coerce_date(), _imputed(), datetime, float, str, WHOIS-derived domain features.  WHOIS lookups are slow and unreliable; ``python-, Blocking WHOIS call -- always invoked inside a worker thread., _raw_whois() (+8 more)

### Community 31 - "ML Model Evaluation"
Cohesion: 0.29
Nodes (9): FeedPoller, ExternalFeedSource, FeedIngestionRecord, Deduplication log — one row per (url, source) that has been processed., bool, int, str, StreamingResponse (+1 more)

### Community 32 - "NSC QA & Flashcards"
Cohesion: 0.15
Nodes (18): NSC 2026 Cover Proposal Document, ETDA (Electronic Transactions Development Agency), NSC 2026 Full Report, Google Safe Browsing, Microsoft SmartScreen, Social Impact API (/api/v1/impact), Sustainable Innovation Framework (4 Pillars), ThaiCERT Cybersecurity Advisories (+10 more)

### Community 33 - "External Citations & References"
Cohesion: 0.15
Nodes (11): Small in-process TTL cache used by /check to dedupe rapid repeated checks.  In a, TTLCache, float, int, str, TTLCache behavioural tests., test_clear(), test_expired_entry_is_evicted() (+3 more)

### Community 34 - "Shared phish_features Package"
Cohesion: 0.21
Nodes (15): _cap_per_brand(), _existing(), _fetch_live(), _is_thai_targeting(), _load_whitelist_brands(), main(), _merge(), bool (+7 more)

### Community 35 - "Data Export & Reporting"
Cohesion: 0.34
Nodes (13): deleteWhitelistEntry(), WhitelistListResponse, AsyncSession, int, Request, str, DbWhitelistEntry, _hot_reload_whitelist() (+5 more)

### Community 36 - "Popup HTML/JS Interface"
Cohesion: 0.20
Nodes (14): Release v1.0.0 (2026-05-25), Release v1.1.0 (2026-05-26), Release v1.2.0 (2026-05-26), Docker Compose Deployment (backend + PostgreSQL), Brand Watchlist + Webhook Notifier, Campaign Clustering (Fingerprint-based), Content-based Gray-Zone Fallback (HTML Check), Real-time External Feed Ingestion (OpenPhish + PhishTank) (+6 more)

### Community 37 - "Security Policy"
Cohesion: 0.14
Nodes (6): Whitelist, Whitelist + typosquat detection tests., The normalized closest call must fold Cyrillic а back to ASCII a     so a homogl, test_closest_normalized_collapses_cyrillic_lookalike(), test_whitelist_from_entries_dedupes(), wl()

### Community 38 - "Contribution Guidelines"
Cohesion: 0.19
Nodes (9): Cross-cutting HTTP middleware.  Adds three things on top of the default Starlett, Stamp every request with a stable id + security headers + access log., RequestContextMiddleware, bool, float, int, Request, str (+1 more)

### Community 39 - "Changelog & Versioning"
Cohesion: 0.36
Nodes (12): AsyncSession, int, JSONResponse, feed_csv(), feed_json(), feed_stix(), list_feed_sources(), Public threat feed.  Unauthenticated, lightly rate-limited feed of high-confiden (+4 more)

### Community 40 - "Render Deployment Config"
Cohesion: 0.33
Nodes (11): _imputed(), _probe_unverified(), _probe_valid(), float, int, str, TLS certificate features.  Like WHOIS, the TLS probe is network-bound and run wi, Probe with full verification -- a clean handshake means a valid cert. (+3 more)

### Community 41 - "Dashboard Public Assets"
Cohesion: 0.18
Nodes (11): CI Job: Backend + ML Tests (pytest), CI Job: Dashboard Build (Vite), CI Job: Docker Image Build, CI Job: Extension Package (.zip), GitHub Actions CI Workflow, CI Job: ML Primary-Metric Gate (Thai holdout recall >= 0.85), Contribution Guide (CONTRIBUTING.md), ML Primary-Metric Quality Gate (recall >= 0.85) (+3 more)

### Community 42 - "ML Feature Schema v1.4.0"
Cohesion: 0.18
Nodes (3): extractor(), FeatureExtractor, FeatureExtractor end-to-end tests.

### Community 43 - "Async Task Workers"
Cohesion: 0.20
Nodes (9): accuracy, confusion_matrix, data_source, f1_score, precision, recall, roc_auc, test_rows (+1 more)

### Community 44 - "Logging & Monitoring"
Cohesion: 0.20
Nodes (9): mean_score, median_score, missed_count, missed_urls, recall_phishing_ci_95, recall_phishing_threshold, recall_suspicious_ci_95, recall_suspicious_threshold (+1 more)

### Community 45 - "Seed Corpus Management"
Cohesion: 0.20
Nodes (9): mean_score, median_score, missed_count, missed_urls, recall_phishing_ci_95, recall_phishing_threshold, recall_suspicious_ci_95, recall_suspicious_threshold (+1 more)

### Community 46 - "NSC 2026 User Guide"
Cohesion: 0.36
Nodes (9): _fetch_wikipedia_domains(), _load_existing(), main(), merge(), float, str, Expand ``data/thai_gov_domains.csv`` with the broader catalogue of Thai governme, Merge ``additions`` into ``existing`` without overwriting curated metadata. (+1 more)

### Community 47 - "NSC 2026 Installation Guide"
Cohesion: 0.32
Nodes (8): Browser Extension Popup UI, Extension Options Page (options.html), Extension Popup UI (popup.html), Extension Privacy Policy, Browser Extension README, Browser Extension (Manifest V3), Citizen Report Portal (No-Auth Public Reporting), Phishing Warning Interstitial Page (warning.html)

### Community 48 - "NSC 2026 Summary Form"
Cohesion: 0.25
Nodes (7): Base, get_session(), Async SQLAlchemy engine + session management., Declarative base for all ORM models., FastAPI dependency yielding a database session., AsyncSession, DeclarativeBase

### Community 50 - "NSC 2026 Video Script"
Cohesion: 0.33
Nodes (5): Prometheus metrics for the API., Return ``(body, content_type)`` for the /metrics response., render_metrics(), bytes, str

### Community 51 - "NSC 2026 Rubric Mapping"
Cohesion: 0.80
Nodes (5): demo_setup.sh script, die(), log(), ok(), wait_for_health()

### Community 52 - "NSC 2026 Cover Proposal"
Cohesion: 0.33
Nodes (3): Golden tests: pin the verdict for a hand-picked set of URLs.  Regressions in the, Stronger guarantee than the parametrised test: ALL legit URLs are     classified, test_no_false_positives_on_legit_set()

### Community 53 - "NSC 2026 Checklist"
Cohesion: 0.40
Nodes (4): _key(), Rate limiting (slowapi)., Rate-limit per API key when present, otherwise per client IP., str

### Community 54 - "NSC 2026 Disclaimer"
Cohesion: 0.50
Nodes (4): int, check(), main(), str

### Community 55 - "NSC 2026 Proposal"
Cohesion: 0.40
Nodes (3): client(), Shared pytest fixtures.  The backend app is configured against a temporary SQLit, A TestClient with full lifespan (model loading) executed.

### Community 56 - "Extension Privacy Policy"
Cohesion: 0.50
Nodes (3): confirmed, params, pct

### Community 57 - "Extension README"
Cohesion: 0.83
Nodes (3): demo_reset.sh script, log(), ok()

### Community 58 - "Extension Icons"
Cohesion: 0.67
Nodes (3): main(), post(), str

## Knowledge Gaps
- **204 isolated node(s):** `JSONResponse`, `bool`, `float`, `bytes`, `str` (+199 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DbWhitelistEntry` connect `Data Export & Reporting` to `URL Watchlist & Batch Check`, `Feedback & Analytics Dashboard`, `Security Policy`, `React Dashboard UI`, `LINE Bot Integration`, `NSC 2026 Summary Form`, `URL Unshortener`, `CI/CD Pipeline`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Why does `Whitelist` connect `LINE Bot Integration` to `Data Export & Reporting`, `ML Training Pipeline`, `Security Policy`, `External Threat Feed Ingestion`, `ML Feature Schema v1.4.0`, `React Dashboard UI`, `STIX Threat Feed Export`, `Warning Page`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `FeatureExtractor` connect `STIX Threat Feed Export` to `ML Training Pipeline`, `Feature Extractor & Scorer`, `ML Feature Schema v1.4.0`, `React Dashboard UI`, `LINE Bot Integration`, `Warning Page`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `FeedPoller` (e.g. with `ExternalFeedSource` and `FeedIngestionRecord`) actually correct?**
  _`FeedPoller` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `DbWhitelistEntry` (e.g. with `int` and `str`) actually correct?**
  _`DbWhitelistEntry` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Feedback` (e.g. with `AsyncSession` and `int`) actually correct?**
  _`Feedback` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Whitelist` (e.g. with `FeatureExtractor` and `bool`) actually correct?**
  _`Whitelist` has 7 INFERRED edges - model-reasoned connections that need verification._