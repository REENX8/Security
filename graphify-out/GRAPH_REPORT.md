# Graph Report - .  (2026-05-28)

## Corpus Check
- 157 files · ~72,057 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1297 nodes · 2373 edges · 68 communities (62 shown, 6 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 410 edges (avg confidence: 0.57)
- Token cost: 24,500 input · 7,700 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Research & Academic Citations|Research & Academic Citations]]
- [[_COMMUNITY_API Response Models|API Response Models]]
- [[_COMMUNITY_ML Evaluation Metrics|ML Evaluation Metrics]]
- [[_COMMUNITY_Heuristic Rules Engine|Heuristic Rules Engine]]
- [[_COMMUNITY_ML Pipeline & Config|ML Pipeline & Config]]
- [[_COMMUNITY_Browser Extension & Submission|Browser Extension & Submission]]
- [[_COMMUNITY_Content & URL Unshortener|Content & URL Unshortener]]
- [[_COMMUNITY_Lexical Feature Extraction|Lexical Feature Extraction]]
- [[_COMMUNITY_FastAPI Auth & Dependencies|FastAPI Auth & Dependencies]]
- [[_COMMUNITY_Extension Background Script|Extension Background Script]]
- [[_COMMUNITY_Brand Watchlist & Webhooks|Brand Watchlist & Webhooks]]
- [[_COMMUNITY_IDN & Homoglyph Defence|IDN & Homoglyph Defence]]
- [[_COMMUNITY_Dataset Collection|Dataset Collection]]
- [[_COMMUNITY_Extension Manifest|Extension Manifest]]
- [[_COMMUNITY_Database Helpers|Database Helpers]]
- [[_COMMUNITY_FastAPI App Lifecycle|FastAPI App Lifecycle]]
- [[_COMMUNITY_Campaign Clustering|Campaign Clustering]]
- [[_COMMUNITY_Feed Ingestion Service|Feed Ingestion Service]]
- [[_COMMUNITY_TLS & WHOIS Features|TLS & WHOIS Features]]
- [[_COMMUNITY_Typosquat Brand Matching|Typosquat Brand Matching]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]

## God Nodes (most connected - your core abstractions)
1. `FeedPoller` - 36 edges
2. `Whitelist` - 29 edges
3. `UrlCheck` - 27 edges
4. `Thai Public-Sector Phishing URL Detection System` - 26 edges
5. `BrandWatch` - 21 edges
6. `Label` - 20 edges
7. `ExternalFeedSource` - 20 edges
8. `WebhookDelivery` - 19 edges
9. `WhitelistEntry` - 19 edges
10. `request()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Browser Extension Icon 128px` --conceptually_related_to--> `Browser Extension Manifest V3`  [INFERRED]
  extension/icons/icon128.png → docs/nsc2026/02_full_report.md
- `Browser Extension Icon 16px` --conceptually_related_to--> `Browser Extension Manifest V3`  [INFERRED]
  extension/icons/icon16.png → docs/nsc2026/02_full_report.md
- `Browser Extension Icon 48px` --conceptually_related_to--> `Browser Extension Manifest V3`  [INFERRED]
  extension/icons/icon48.png → docs/nsc2026/02_full_report.md
- `Docker Compose Deployment (backend + PostgreSQL)` --semantically_similar_to--> `Render Blueprint Web Service (phish-backend)`  [INFERRED] [semantically similar]
  docker-compose.yml → render.yaml
- `Citizen Report Portal (No-Auth Public Reporting)` --semantically_similar_to--> `Extension Privacy Policy`  [INFERRED] [semantically similar]
  README.md → extension/PRIVACY.md

## Hyperedges (group relationships)
- **Core Phishing Detection Pipeline (phish_features + ML + Rules Engine + FastAPI)** — readme_readme_phish_features_package, readme_readme_ml_pipeline, readme_readme_rules_engine, readme_readme_fastapi_backend [EXTRACTED 0.95]
- **CI Quality Gates (pytest + lint + ML gate + docker + extension)** — ci_ci_backend_tests_job, ci_ci_ml_gate_job, ci_ci_dashboard_build_job, ci_ci_docker_build_job, ci_ci_extension_package_job [EXTRACTED 0.95]
- **Multi-Channel User Access (Browser Extension + Dashboard + LINE Bot + Public Feed)** — readme_readme_browser_extension, readme_readme_react_dashboard, readme_readme_line_bot, readme_readme_public_threat_feed, readme_readme_citizen_report_portal [INFERRED 0.85]
- **ML Pipeline Accuracy Validation: Model + Holdout + CI Gate** — nsc2026_02_full_report_ml_ensemble, nsc2026_02_full_report_thai_holdout_100pct_recall, nsc2026_02_full_report_ci_gate, reports_thai_vs_generic_recall_thai_vs_generic_recall [INFERRED 0.95]
- **NSC 2026 Submission Document Set** — nsc2026_00_cover_proposal_cover_proposal, nsc2026_02_full_report_full_report, nsc2026_03_summary_form_summary_form, nsc2026_04_installation_guide_installation_guide, nsc2026_05_user_guide_user_guide, nsc2026_07_poster_poster, nsc2026_08_video_script_video_script, nsc2026_09_checklist_submission_checklist, nsc2026_10_rubric_mapping_rubric_mapping [EXTRACTED 1.00]
- **Multi-Channel Phishing Detection: Extension + LINE Bot + Portal** — nsc2026_02_full_report_browser_extension_mv3, nsc2026_03_summary_form_line_bot, nsc2026_02_full_report_citizen_report_portal [INFERRED 0.95]

## Communities (68 total, 6 thin omitted)

### Community 0 - "Research & Academic Citations"
Cohesion: 0.05
Nodes (55): ETDA Thai Cyberthreat Context (30,000+ phishing cases 2024), NSC 2026 Project Proposal (Category 23, Student Level), Random Forests (Breiman, Machine Learning, 2001), STIX 2.1 Threat Intelligence Standard, Unicode Technical Report #36: Unicode Security Considerations, XGBoost: A Scalable Tree Boosting System (Chen & Guestrin, KDD 2016), NSC 2026 Software License Agreement (Thai/English), Release v1.0.0 (2026-05-25) (+47 more)

### Community 1 - "API Response Models"
Cohesion: 0.10
Nodes (46): DbWhitelistEntry, DayBucket, ErrorResponse, FlaggedDomain, HistoryItem, HistoryResponse, HourBucket, Pydantic v2 request / response models. (+38 more)

### Community 2 - "ML Evaluation Metrics"
Cohesion: 0.04
Nodes (47): alignment_note, alignment_score, cross_validation, cv_f1_mean, cv_f1_std, cv_note, generic_real_holdout, mean_score (+39 more)

### Community 3 - "Heuristic Rules Engine"
Cohesion: 0.09
Nodes (38): str, Heuristic Rules Engine -- a transparent layer on top of the ML scorer.  ML gives, Trusted brand sits in URL path but not in host -- a brand-bait kit., IP host + credential keyword -- almost always phishing., Exact whitelist match should never be phishing.      A safety net against false, Cheap TLD without HTTPS -- low-effort phishing kit., Outcome of running the engine over one (url, features) pair., Apply a list of rules to a (url, feature) pair. (+30 more)

### Community 4 - "ML Pipeline & Config"
Cohesion: 0.07
Nodes (39): DataFrame, main(), Build the shipped whitelist artifact from the curated CSV.  Run this first. It p, ensure_dirs(), Shared paths and constants for the ML pipeline., _enforce_primary_threshold(), _eval_holdout_csv(), evaluate_real_holdout() (+31 more)

### Community 5 - "Browser Extension & Submission"
Cohesion: 0.07
Nodes (44): Browser Extension Icon 128px, Browser Extension Icon 16px, Browser Extension Icon 48px, NSC 2026 Cover Proposal Document, Brand Watchlist + Webhook, Browser Extension Manifest V3, Campaign Clustering Algorithm, CI Gate Thai Recall >= 0.85 (+36 more)

### Community 6 - "Content & URL Unshortener"
Cohesion: 0.08
Nodes (36): content_score_adjustment(), _is_private_host(), Lightweight content-based check for gray-zone URLs.  Fetches the HTML of a URL a, Return a score adjustment in [-0.20, +0.30] based on page content.      Positive, _is_shortener(), Async URL unshortener — follows redirects for known short-link services., Return the final URL after following redirects, or the original URL on error., unshorten_url() (+28 more)

### Community 7 - "Lexical Feature Extraction"
Cohesion: 0.10
Nodes (38): _count_login_keywords(), _count_query_params(), count_subdomains(), extract_lexical(), get_host(), host_is_ip(), normalize_url(), bool (+30 more)

### Community 8 - "FastAPI Auth & Dependencies"
Cohesion: 0.11
Nodes (34): get_scorer(), Shared FastAPI dependencies., Reject requests without a valid ``X-API-Key`` header., Return the loaded scorer, or raise 503 if the model is unavailable., verify_api_key(), AppError, _json(), ModelNotLoadedError (+26 more)

### Community 9 - "Extension Background Script"
Cohesion: 0.11
Nodes (31): checkUrl(), buildWarningUrl(), handleNavigation(), isCheckable(), safeHost(), BADGE, clearBadge(), setBadge() (+23 more)

### Community 10 - "Brand Watchlist & Webhooks"
Cohesion: 0.13
Nodes (35): BrandWatch, One row per webhook attempt -- success or failure., WebhookDelivery, _brand_of(), _is_line_notify(), _line_payload(), maybe_alert(), _post_sync() (+27 more)

### Community 11 - "IDN & Homoglyph Defence"
Cohesion: 0.10
Nodes (30): decode_idn(), fold_confusables(), has_mixed_script(), has_punycode(), normalize_for_lookup(), bool, str, Homoglyph / IDN normalisation utilities.  Phishers targeting Thai government and (+22 more)

### Community 12 - "Dataset Collection"
Cohesion: 0.11
Nodes (24): _fetch_feed_urls(), _fetch_urlhaus(), _is_thai_targeting(), _load_thai_brands(), _load_thai_phish_seed(), main(), bool, int (+16 more)

### Community 13 - "Extension Manifest"
Cohesion: 0.06
Nodes (32): action, default_icon, default_popup, default_title, author, background, service_worker, type (+24 more)

### Community 14 - "Database Helpers"
Cohesion: 0.13
Nodes (25): get_history(), get_stats(), insert_check(), Database read/write helpers for url_checks., Persist a scoring result and return the stored row., Return ``(total, rows)`` for a filtered, paginated history query., Aggregate dashboard statistics., Label (+17 more)

### Community 15 - "FastAPI App Lifecycle"
Cohesion: 0.10
Nodes (25): health(), lifespan(), metrics_endpoint(), _rate_limited(), FastAPI application entry point., Triple of versions that together identify the running build., Migrate whitelist.json → DB on first startup (idempotent)., Insert default OpenPhish and PhishTank source rows if not present (idempotent). (+17 more)

### Community 16 - "Campaign Clustering"
Cohesion: 0.12
Nodes (25): build_fingerprint(), _path_shape(), Phishing campaign clustering.  A phishing campaign is a batch of URLs that share, Return a normalised path skeleton or '' when no path is present., Coarse signature of the host's last label., Deterministic clustering key.      ``<brand>|<tld>|<path-shape>`` is short and g, Upsert a campaign row for ``url`` and bump its counters.      Returns the campai, record_campaign() (+17 more)

### Community 17 - "Feed Ingestion Service"
Cohesion: 0.13
Nodes (24): Background service that polls external threat feeds (OpenPhish, PhishTank).  URL, _url_hash(), _make_scorer(), _make_source(), _make_state(), ExternalFeedSource, Tests for external threat feed ingestion (FeedPoller)., Network error from OpenPhish raises so _poll_source can catch it. (+16 more)

### Community 18 - "TLS & WHOIS Features"
Cohesion: 0.08
Nodes (25): imputed_defaults, cert_age_days, domain_age_days, has_valid_cert, is_known_registrar, is_self_signed, tls_ok, whois_ok (+17 more)

### Community 19 - "Typosquat Brand Matching"
Cohesion: 0.15
Nodes (16): brand_label(), _lev_distance(), bool, int, str, An immutable, sorted set of trusted domains., Return ``(min_edit_distance, closest_domain)`` for ``host``.          Distance i, Closest brand-label distance AFTER Punycode decode + confusable fold.          C (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (14): bool, FeatureExtractor, float, str, _build_reason(), label_from_score(), URL scoring: features -> probability -> label -> human-readable reason., Compose a Thai-language explanation from the strongest signals. (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (19): classify_tld(), _etld(), extract_features(), FeatureExtractor, _path_brand_hit(), bool, float, int (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.21
Nodes (19): addWatchlistEntry(), addWhitelistEntry(), BASE_URL, checkBatch(), checkUrl(), deleteWatchlistEntry(), deleteWhitelistEntry(), getCampaigns() (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (21): bool, bytes, Request, str, _build_reply(), line_webhook(), LINE Messaging API webhook — phishing URL detection in Thai.  Setup:   1. Create, _send_reply() (+13 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (3): Integration tests for the v1.0 new routers: watchlist, feed, campaigns, domain h, No API key required -- this is intentional., test_feed_json_is_public()

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (10): DetailModal(), VERDICT_TH, VERDICTS, LabelBadge(), UrlChecker(), formatDate(), formatDateTime(), labelInfo() (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.30
Nodes (19): Feedback, FeedbackSource, SQLAlchemy ORM models., FeedbackCreate, FeedbackListResponse, FeedbackOut, AsyncSession, int (+11 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (20): dependencies, react, react-dom, react-router-dom, recharts, @tanstack/react-query, devDependencies, autoprefixer (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.17
Nodes (13): Application settings (pydantic-settings, read from environment / .env)., Settings, str, BaseSettings, Path, build(), main(), bool (+5 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (18): _export(), main(), bool, int, Export confirmed feedback from the database and trigger a model retrain.  Usage:, Pull confirmed feedback rows from the DB; returns [] if DB unavailable., _retrain(), run() (+10 more)

### Community 31 - "Community 31"
Cohesion: 0.15
Nodes (11): Small in-process TTL cache used by /check to dedupe rapid repeated checks.  In a, TTLCache, float, int, str, TTLCache behavioural tests., test_clear(), test_expired_entry_is_evicted() (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (17): ExternalFeedSource, AsyncSession, ExternalFeedSource, int, JSONResponse, Request, StreamingResponse, UrlCheck (+9 more)

### Community 33 - "Community 33"
Cohesion: 0.31
Nodes (7): FeedPoller, FeedIngestionRecord, Deduplication log — one row per (url, source) that has been processed., bool, ExternalFeedSource, int, str

### Community 34 - "Community 34"
Cohesion: 0.18
Nodes (5): useHistory(), useStats(), formatPct(), Overview(), Stats()

### Community 35 - "Community 35"
Cohesion: 0.21
Nodes (15): _cap_per_brand(), _existing(), _fetch_live(), _is_thai_targeting(), _load_whitelist_brands(), main(), _merge(), bool (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.16
Nodes (5): getPublicFeedUrl(), useHealth(), Layout(), NAV, Feed()

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (6): Whitelist, Whitelist + typosquat detection tests., The normalized closest call must fold Cyrillic а back to ASCII a     so a homogl, test_closest_normalized_collapses_cyrillic_lookalike(), test_whitelist_from_entries_dedupes(), wl()

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (6): useCheckBatch(), downloadCsv(), toCsv(), Bulk(), History(), queryClient

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (9): Cross-cutting HTTP middleware.  Adds three things on top of the default Starlett, Stamp every request with a stable id + security headers + access log., RequestContextMiddleware, bool, float, int, Request, str (+1 more)

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (12): _imputed(), _probe_unverified(), _probe_valid(), float, int, str, TLS certificate features.  Like WHOIS, the TLS probe is network-bound and run wi, Probe with full verification -- a clean handshake means a valid cert. (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.25
Nodes (10): _coerce_date(), _imputed(), datetime, float, str, WHOIS-derived domain features.  WHOIS lookups are slow and unreliable; ``python-, Blocking WHOIS call -- always invoked inside a worker thread., Return WHOIS features for ``host`` with a hard timeout + safe fallback. (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (3): extractor(), FeatureExtractor, FeatureExtractor end-to-end tests.

### Community 43 - "Community 43"
Cohesion: 0.20
Nodes (9): Base, get_session(), init_db(), Async SQLAlchemy engine + session management., Declarative base for all ORM models., FastAPI dependency yielding a database session., Create tables if they do not exist (idempotent)., AsyncSession (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (9): accuracy, confusion_matrix, data_source, f1_score, precision, recall, roc_auc, test_rows (+1 more)

### Community 45 - "Community 45"
Cohesion: 0.20
Nodes (9): mean_score, median_score, missed_count, missed_urls, recall_phishing_ci_95, recall_phishing_threshold, recall_suspicious_ci_95, recall_suspicious_threshold (+1 more)

### Community 46 - "Community 46"
Cohesion: 0.20
Nodes (9): mean_score, median_score, missed_count, missed_urls, recall_phishing_ci_95, recall_phishing_threshold, recall_suspicious_ci_95, recall_suspicious_threshold (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.36
Nodes (9): _fetch_wikipedia_domains(), _load_existing(), main(), merge(), float, str, Expand ``data/thai_gov_domains.csv`` with the broader catalogue of Thai governme, Merge ``additions`` into ``existing`` without overwriting curated metadata. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.53
Nodes (5): useAddWhitelistEntry(), useDeleteWhitelistEntry(), useWhitelist(), Admin(), CATEGORIES

### Community 50 - "Community 50"
Cohesion: 0.47
Nodes (4): getFeedbackExportUrl(), useFeedback(), Feedback(), LABEL_FILTER_OPTIONS

### Community 51 - "Community 51"
Cohesion: 0.33
Nodes (5): Prometheus metrics for the API., Return ``(body, content_type)`` for the /metrics response., render_metrics(), bytes, str

### Community 52 - "Community 52"
Cohesion: 0.33
Nodes (3): Golden tests: pin the verdict for a hand-picked set of URLs.  Regressions in the, Stronger guarantee than the parametrised test: ALL legit URLs are     classified, test_no_false_positives_on_legit_set()

### Community 53 - "Community 53"
Cohesion: 0.60
Nodes (4): useCheckUrl(), useSubmitFeedback(), CHOICES, Report()

### Community 54 - "Community 54"
Cohesion: 0.40
Nodes (4): _key(), Rate limiting (slowapi)., Rate-limit per API key when present, otherwise per client IP., str

### Community 55 - "Community 55"
Cohesion: 0.40
Nodes (4): FeatureExtractor, build_extractor(), Thin adapter over the shared ``phish_features`` package.  There is intentionally, Construct the FeatureExtractor used for serving.

### Community 56 - "Community 56"
Cohesion: 0.40
Nodes (4): float, Feature contract shared by the ML pipeline and the backend.  This module is the, Project a raw feature dict onto the ordered numeric model vector., vector_from_dict()

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (3): client(), Shared pytest fixtures.  The backend app is configured against a temporary SQLit, A TestClient with full lifespan (model loading) executed.

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (3): confirmed, params, pct

### Community 59 - "Community 59"
Cohesion: 0.67
Nodes (3): main(), post(), str

## Knowledge Gaps
- **227 isolated node(s):** `JSONResponse`, `bool`, `float`, `bytes`, `str` (+222 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_score_and_persist()` connect `FastAPI Auth & Dependencies` to `Content & URL Unshortener`, `Brand Watchlist & Webhooks`, `Database Helpers`, `Campaign Clustering`, `Community 20`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `FeatureExtractor` connect `Community 21` to `ML Pipeline & Config`, `Community 42`, `IDN & Homoglyph Defence`, `Typosquat Brand Matching`, `Community 20`, `Community 55`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `WhitelistEntry` connect `API Response Models` to `Typosquat Brand Matching`, `IDN & Homoglyph Defence`, `Community 37`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `FeedPoller` (e.g. with `ExternalFeedSource` and `ExternalFeedSourceType`) actually correct?**
  _`FeedPoller` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Whitelist` (e.g. with `FeatureExtractor` and `bool`) actually correct?**
  _`Whitelist` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `UrlCheck` (e.g. with `Base` and `AsyncSession`) actually correct?**
  _`UrlCheck` has 25 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Background service that polls external threat feeds (OpenPhish, PhishTank).  URL`, `FastAPI application entry point.`, `Migrate whitelist.json → DB on first startup (idempotent).` to the rest of the system?**
  _420 weakly-connected nodes found - possible documentation gaps or missing edges._