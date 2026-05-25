"""URL scoring: features -> probability -> label -> human-readable reason."""

from __future__ import annotations

import datetime as dt

from phish_features import FeatureExtractor, ORDERED_FEATURES

from app.config import settings


def label_from_score(score: float) -> str:
    if score >= settings.threshold_phishing:
        return "phishing"
    if score >= settings.threshold_suspicious:
        return "suspicious"
    return "safe"


def _build_reason(feat: dict, label: str, is_whitelisted: bool) -> str:
    """Compose a Thai-language explanation from the strongest signals."""
    if is_whitelisted:
        return "โดเมนนี้อยู่ในรายชื่อหน่วยงานราชการ/สถาบันการศึกษาที่เชื่อถือได้"
    if label == "safe":
        return "ไม่พบสัญญาณความเสี่ยงที่ชัดเจน เป็นรูปแบบ URL ปกติ"

    reasons: list[str] = []

    if feat.get("is_typosquat"):
        closest = feat.get("closest_domain")
        dist = feat.get("min_edit_distance")
        reasons.append(
            f"โดเมนคล้ายกับเว็บไซต์ทางการ {closest} มาก "
            f"(edit distance: {dist}) อาจเป็นการปลอมแปลง"
        )
    # IDN / Punycode is a stronger lookalike signal than typosquat because
    # the displayed URL can appear pixel-identical to the real brand. List
    # these reasons next so the user sees the right framing.
    if feat.get("has_punycode"):
        closest = feat.get("closest_domain")
        if closest:
            reasons.append(
                f"URL ใช้ Punycode (xn--...) ซ่อนตัวอักษรที่อาจหน้าตาเหมือน "
                f"ชื่อเว็บจริง {closest}"
            )
        else:
            reasons.append(
                "URL ใช้ Punycode (xn--...) ซึ่งมักใช้ซ่อนตัวอักษร "
                "ที่หน้าตาเหมือนชื่อเว็บจริงจากภาษาอื่น"
            )
    elif (
        feat.get("has_mixed_script")
        and feat.get("homoglyph_distance", 999) < feat.get("min_edit_distance", 999)
    ):
        # Only flag mixed-script when the confusable-fold collapsed the
        # distance -- pure non-Thai-script legitimate domains would also
        # carry has_mixed_script=1 without being suspicious.
        closest = feat.get("closest_domain")
        if closest:
            reasons.append(
                f"ตัวอักษรในชื่อโดเมนใช้หลายภาษาผสมกัน "
                f"(เช่น Latin + Cyrillic) อาจปลอมเป็น {closest}"
            )
        else:
            reasons.append(
                "ตัวอักษรในชื่อโดเมนใช้หลายภาษาผสมกัน "
                "(เช่น Latin + Cyrillic) ซึ่งเป็นเทคนิคปลอมแปลงที่พบบ่อย"
            )
    if feat.get("has_ip"):
        reasons.append("URL ใช้หมายเลข IP แทนชื่อโดเมน ซึ่งพบบ่อยในเว็บฟิชชิง")
    if feat.get("num_at", 0) >= 1:
        reasons.append("URL มีอักขระ '@' ซึ่งมักใช้ซ่อนปลายทางจริง")
    if feat.get("num_subdomains", 0) >= 3:
        reasons.append("URL มีโดเมนย่อยซ้อนกันจำนวนมาก อาจปลอมเป็นเว็บทางการ")
    age = feat.get("domain_age_days", -1)
    if 0 <= age < 90:
        reasons.append(f"โดเมนเพิ่งจดทะเบียนเมื่อ {int(age)} วันก่อน")
    if feat.get("is_self_signed"):
        reasons.append("ใบรับรอง TLS เป็นแบบ self-signed ไม่น่าเชื่อถือ")
    if not feat.get("has_https"):
        reasons.append("การเชื่อมต่อไม่ได้เข้ารหัส (ไม่มี HTTPS)")
    if feat.get("num_hyphens", 0) >= 4:
        reasons.append("ชื่อโดเมนมีเครื่องหมายขีดจำนวนมาก ผิดปกติ")

    if reasons:
        return " · ".join(reasons[:3])
    return "ตรวจพบรูปแบบ URL ที่มีความเสี่ยงตามแบบจำลองการเรียนรู้ของเครื่อง"


class Scorer:
    """Encapsulates the model, scaler and feature extractor."""

    def __init__(self, model, scaler, extractor: FeatureExtractor,
                 features_meta: dict) -> None:
        self.model = model
        self.scaler = scaler
        self.extractor = extractor
        self.features_meta = features_meta

    def score(self, url: str) -> dict:
        feat = self.extractor.extract_dict(url)
        vector = [float(feat[name]) for name in ORDERED_FEATURES]
        proba = self.model.predict_proba(self.scaler.transform([vector]))[0][1]
        score = round(float(proba), 4)
        label = label_from_score(score)

        is_whitelisted = (
            feat.get("min_edit_distance") == 0
            and not feat.get("is_typosquat")
            and not feat.get("has_ip")
        )

        reason = _build_reason(feat, label, is_whitelisted)

        return {
            "url": url,
            "score": score,
            "label": label,
            "reason": reason,
            "features": feat,
            "closest_domain": feat.get("closest_domain"),
            "edit_distance": (
                None if feat.get("min_edit_distance", 999) >= 999
                else int(feat["min_edit_distance"])
            ),
            "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
