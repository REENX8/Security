// Groups the 42 raw model features into human-readable sections with Thai
// labels, so the DetailModal explains the verdict instead of dumping a flat
// key/value table. Unknown keys fall back to their raw name.

export const FEATURE_GROUPS = [
  {
    title: "โครงสร้าง URL (Lexical)",
    keys: [
      "url_length", "num_dots", "num_hyphens", "num_at", "num_slash",
      "num_digits", "has_ip", "entropy", "has_https", "num_subdomains",
      "path_depth", "domain_label_max_len", "has_port", "max_digit_run",
      "has_query_string", "path_length", "num_login_keywords",
      "query_param_count", "path_entropy", "host_token_count",
      "digit_to_letter_ratio",
    ],
  },
  {
    title: "โดเมน & ทะเบียน (Domain / WHOIS)",
    keys: [
      "domain_age_days", "is_thai_tld", "tld_type_enc", "is_known_registrar",
      "whois_ok", "min_edit_distance", "is_typosquat",
    ],
  },
  {
    title: "ใบรับรอง TLS",
    keys: [
      "has_valid_cert", "cert_age_days", "is_self_signed", "tls_ok",
      "cert_is_lets_encrypt", "cert_validity_days", "cert_san_count",
    ],
  },
  {
    title: "ตัวอักษรลวง / IDN (Homoglyph)",
    keys: ["has_punycode", "has_mixed_script", "homoglyph_distance"],
  },
  {
    title: "เลียนแบบแบรนด์ (Impersonation)",
    keys: [
      "has_login_keyword", "has_suspicious_tld", "path_brand_hit",
      "host_has_brand_and_suspicious_tld",
    ],
  },
];

export const FEATURE_LABELS = {
  url_length: "ความยาว URL",
  num_dots: "จำนวนจุด (.)",
  num_hyphens: "จำนวนขีด (-)",
  num_at: "จำนวน @",
  num_slash: "จำนวน /",
  num_digits: "จำนวนตัวเลข",
  has_ip: "ใช้ IP แทนโดเมน",
  entropy: "entropy ของ URL",
  has_https: "ใช้ HTTPS",
  num_subdomains: "จำนวน subdomain",
  path_depth: "ความลึกของ path",
  domain_label_max_len: "ความยาว label สูงสุด",
  has_port: "ระบุพอร์ต",
  max_digit_run: "ลำดับตัวเลขยาวสุด",
  has_query_string: "มี query string",
  path_length: "ความยาว path",
  num_login_keywords: "คำที่สื่อ login",
  query_param_count: "จำนวน query param",
  path_entropy: "entropy ของ path",
  host_token_count: "จำนวน token ใน host",
  digit_to_letter_ratio: "อัตราตัวเลขต่อตัวอักษร",
  domain_age_days: "อายุโดเมน (วัน)",
  is_thai_tld: "เป็น TLD ไทย",
  tld_type_enc: "ประเภท TLD (เข้ารหัส)",
  is_known_registrar: "registrar ที่รู้จัก",
  whois_ok: "ดึง WHOIS สำเร็จ",
  min_edit_distance: "ระยะใกล้โดเมนจริง",
  is_typosquat: "เป็น typosquat",
  has_valid_cert: "ใบรับรองถูกต้อง",
  cert_age_days: "อายุใบรับรอง (วัน)",
  is_self_signed: "ใบรับรอง self-signed",
  tls_ok: "ตรวจ TLS สำเร็จ",
  cert_is_lets_encrypt: "ออกโดย Let's Encrypt",
  cert_validity_days: "อายุใช้งานใบรับรอง",
  cert_san_count: "จำนวน SAN",
  has_punycode: "มี Punycode (xn--)",
  has_mixed_script: "ผสมหลายภาษา",
  homoglyph_distance: "ระยะ homoglyph",
  has_login_keyword: "มีคำว่า login/verify",
  has_suspicious_tld: "TLD ราคาถูก/น่าสงสัย",
  path_brand_hit: "พบชื่อแบรนด์ใน path",
  host_has_brand_and_suspicious_tld: "แบรนด์ + TLD น่าสงสัย",
};

// A heuristic for "notable" values worth highlighting (a phishy signal).
const SUSPICIOUS_WHEN_TRUE = new Set([
  "has_ip", "is_typosquat", "is_self_signed", "has_punycode",
  "has_mixed_script", "has_login_keyword", "has_suspicious_tld",
  "path_brand_hit", "host_has_brand_and_suspicious_tld",
]);

export function isNotable(key, value) {
  // Absence of HTTPS / a valid cert is itself a phishy signal (checked before
  // the generic boolean rule, which would otherwise treat false as "not notable").
  if (key === "has_https" || key === "has_valid_cert") return value === false;
  if (typeof value === "boolean") {
    return SUSPICIOUS_WHEN_TRUE.has(key) ? value : false;
  }
  if (key === "homoglyph_distance") return value > 0;
  if (key === "min_edit_distance") return value > 0 && value <= 2;
  return false;
}

export function groupFeatures(features) {
  const known = new Set(FEATURE_GROUPS.flatMap((g) => g.keys));
  const groups = FEATURE_GROUPS.map((g) => ({
    title: g.title,
    rows: g.keys
      .filter((k) => k in features)
      .map((k) => [k, features[k]]),
  })).filter((g) => g.rows.length > 0);

  const extras = Object.entries(features).filter(([k]) => !known.has(k));
  if (extras.length) groups.push({ title: "อื่น ๆ", rows: extras });
  return groups;
}
