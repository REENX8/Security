# Thai Phishing Website Detection System for Thai Organizations Using Machine Learning and Heuristic Rules

> Academic Article

---

## Abstract

Phishing websites impersonating Thai government agencies, educational institutions, and financial organizations represent a continuously escalating cyber threat. Unsuspecting users may be deceived into disclosing personal information, passwords, or financial data without awareness.

This research presents **RuThan**, a comprehensive phishing website detection system that integrates a **Machine Learning Ensemble** utilizing 44 features with a **transparent heuristic rules engine** capable of explaining detection results in clear, human-readable terms. The system supports multiple delivery channels: browser extension (Chrome/Firefox/Edge), web dashboard, LINE chatbot, and public threat feed.

Evaluation results demonstrate that the model achieves **100% recall (378/378 URLs)** on Thai-targeting phishing URLs at threshold ≥ 0.7 (95% CI: [0.990, 1.000]), with a cross-validation F1-score of 0.999 ± 0.000.

**Keywords:** Phishing, Machine Learning, URL Detection, Cybersecurity, Thai Organizations

---

## 1. Introduction

Phishing websites are a prevalent cybersecurity threat in Thailand, where attackers routinely impersonate government portals, banks, and universities to deceive users into submitting personal information or conducting unauthorized financial transactions.

Commonly spoofed domains fall under `.go.th` (government), `.ac.th` (academic), and `.or.th` (non-profit) — top-level domains that users inherently trust. Techniques employed include visually similar character substitution (homograph attacks), minor spelling deviations (typosquatting), and URL obfuscation via link shortening services.

This research addresses these threats by developing a system that combines two complementary approaches:

- **Machine Learning Ensemble** (scikit-learn + XGBoost) for statistical decision-making across 44 engineered features
- **Rules Engine** comprising 7 transparent, interpretable rules for generating human-readable Thai-language explanations of detection outcomes

RuThan is designed as an **end-to-end platform** accessible simultaneously by general users, system administrators, and cybersecurity agencies through multiple channels.

---

## 2. Methodology

### 2.1 Seed Corpus Collection

A Thai-targeting URL dataset of **1,261 URLs** was compiled, covering **160+ brands** across banking, ministries, universities, state enterprises, e-commerce, airlines, logistics, and telecommunications sectors. A cap of 8 URLs per brand was enforced to maintain dataset balance.

Additional generic phishing URLs were sourced from **OpenPhish** and **PhishTank**, with deduplication applied throughout ingestion.

### 2.2 Feature Extraction

The `phish_features` package was developed to extract **44 features (v1.6.0)** organized into 7 groups:

| Feature Group | Examples |
|:---|:---|
| Lexical (10) | URL length, entropy, IP-as-hostname, subdomain count, non-standard port |
| Domain | TLD type, domain age, registrar |
| Whitelist/Typosquat | Levenshtein distance ≤ 2, brand label |
| TLS | Certificate validity, self-signed indicator, Let's Encrypt indicator |
| IDN/Homoglyph | Punycode detection, mixed-script detection |
| Path Impersonation | Login/credential keywords in path, brand hits |
| Rich Lexical | Token count, path entropy, keyword count |

### 2.3 Machine Learning Model Training

An ensemble model was trained using **scikit-learn + XGBoost** on a synthetic dataset of **12,000 rows** anchored to 500+ trusted Thai government, academic, and banking domains.

5-fold cross-validation was applied with the following classification thresholds:
- **Safe:** score ≤ 0.3
- **Suspicious:** score 0.3–0.7 (triggers content-based HTML fallback inspection)
- **Phishing:** score ≥ 0.7

### 2.4 Rules Engine and Content-Based Fallback

Seven heuristic rules were developed (typosquat, homograph, credential-harvesting path, IP-based URL, URL shortener, mixed-script domain, known-phishing-pattern) capable of overriding ML decisions without requiring model retraining.

For URLs in the gray zone (0.3–0.7), the system fetches and inspects page HTML for additional brand impersonation signals. **SSRF (Server-Side Request Forgery)** protection is enforced throughout.

### 2.5 Backend Architecture

A REST API was built with **FastAPI 0.115 + SQLAlchemy 2.0 (async) + PostgreSQL 16**, exposing the following primary endpoints:
- `POST /api/v1/check` — submit URL for analysis (public, no auth required)
- `GET /api/v1/feed.{json,csv,stix}` — public threat feed for TAXII consumers
- `POST /api/v1/feedback` — user-submitted false positive/negative reports
- `POST /api/v1/admin/retrain` — trigger staged automated retraining

### 2.6 Frontend and Integration Development

Three primary user interfaces were developed:
1. **React Dashboard** (11 pages) for administrators and general users
2. **Chrome Extension (Manifest V3)** displaying badges and automatic interstitial warnings
3. **LINE Messaging API Bot** enabling users to submit URLs via LINE chat and receive instant results

---

## 3. Results

### 3.1 Thai Phishing URL Detection Performance

**Table 1.** Model evaluation on Thai-targeting holdout set (v1.6.0)

| Metric | Result |
|:---:|:---:|
| Thai Phishing Recall | **100% (378/378)** |
| 95% Confidence Interval | [0.990, 1.000] |
| 5-fold CV F1 (synthetic) | **0.999 ± 0.000** |
| Generic Phishing Recall | 98.89% (89/90) |
| Phishing Threshold | ≥ 0.7 |

> At threshold ≥ 0.7, the model achieves complete 100% recall on Thai-targeting phishing URLs while maintaining near-99% recall on generic phishing URLs.

### 3.2 Seed Corpus Coverage

The test corpus covers **160+ Thai brands** distributed across all sectors. A seed corpus audit script confirmed no single brand exceeds the per-brand URL cap.

**Table 2.** Sample brand categories in Seed Corpus

| Category | Examples |
|:---|:---|
| State-owned Banks | Krungthai Bank, GSB, BAAC |
| Ministries | Ministry of Finance, Revenue Department |
| Universities | Chulalongkorn, Thammasat, Khon Kaen |
| State Enterprises | EGAT, PTT, AOT |
| E-Commerce / Logistics | Shopee, Lazada, Thailand Post |

### 3.3 Automated Test Suite Results

The system passed **331 automated tests** covering all components: feature extraction, rules engine, campaign clustering, feed ingestion, SIEM export, JWT authentication, LINE bot, feedback retraining, and SSRF protection.

A CI gate enforces **Thai recall ≥ 0.85** on every code push; builds fail automatically if this threshold is not met.

### 3.4 Campaign Clustering Capability

The system clusters URLs originating from the same phishing kit using a fingerprint derived from brand + TLD + path skeleton. This provides administrators with a campaign-level view of attack activity and enables faster coordinated response.

---

## 4. Discussion and Conclusion

### 4.1 Discussion

RuThan demonstrates that combining an ML ensemble with a transparent rules engine outperforms either approach in isolation. ML captures complex statistical patterns while the rules engine provides users with immediate, interpretable explanations — without requiring model retraining when new phishing patterns emerge.

The content-based fallback effectively handles gray-zone URLs without relying on resource-intensive headless browser rendering.

### 4.2 Conclusion

- The 44-feature ML ensemble achieves **100% recall** on Thai-targeting phishing URLs (confirmed via 95% CI: [0.990, 1.000])
- The **7-rule Rules Engine** generates clear explanations and handles edge cases without model retraining
- The multi-channel platform serves three user groups: general public (LINE/Extension), administrators (Dashboard), and security agencies (TAXII/Threat Feed)
- **Feedback-driven auto-retrain** enables continuous model adaptation to emerging phishing patterns

---

## Recommendations

Future work should investigate:
1. Visual similarity detection via screenshot comparison to identify page-level impersonation
2. Extending coverage to phishing URLs propagated through social media platforms beyond LINE
3. Developing detection models for SMS-based phishing (smishing), which shows increasing prevalence in Thailand

---

## References

[1] APWG. (2024). *Phishing Activity Trends Report Q4 2024.* Anti-Phishing Working Group. https://apwg.org/trendsreports/

[2] Sahoo, D., Liu, C., & Hoi, S. C. H. (2017). Malicious URL Detection using Machine Learning: A Survey. *arXiv preprint arXiv:1701.07179.*

[3] Electronic Transactions Development Agency (ETDA). (2024). *Thailand Cyber Threat Report 2024.* Ministry of Digital Economy and Society.

[4] Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.

[5] Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.
