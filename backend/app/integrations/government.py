"""Government integration connectors (B3).

Pluggable connectors to forward confirmed phishing reports to, and pull
blocklists from, Thai authorities — ETDA's 1212 Online and the Cyber Crime
Investigation Bureau's 1441. Neither exposes a public submission API, so the
default real connector is :class:`EmailIntakeConnector`, which emails a CSV
digest of confirmed phishing to the agency's intake mailbox. A real HTTP API
connector can implement the same :class:`GovernmentConnector` protocol later.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Protocol

logger = logging.getLogger("phish-detector")


@dataclass
class GovReport:
    url: str
    score: float
    closest_domain: str | None = None
    reason: str = ""


class GovernmentConnector(Protocol):
    """Forward reports to, and pull a blocklist from, a government service."""

    name: str

    def forward_report(self, report: GovReport) -> bool: ...

    def forward_reports(self, reports: list[GovReport]) -> bool: ...

    def fetch_blocklist(self) -> list[str]: ...


def reports_to_csv(reports: list[GovReport]) -> str:
    """Render reports as CSV (the attachment sent to the agency)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["url", "score", "closest_domain", "reason"])
    for r in reports:
        writer.writerow([r.url, f"{float(r.score):.4f}", r.closest_domain or "", r.reason or ""])
    return buf.getvalue()


@dataclass
class StubGovernmentConnector:
    """No-op connector: records forwards in memory and returns an empty blocklist."""

    name: str = "stub"
    forwarded: list[GovReport] = field(default_factory=list)

    def forward_report(self, report: GovReport) -> bool:
        return self.forward_reports([report])

    def forward_reports(self, reports: list[GovReport]) -> bool:
        self.forwarded.extend(reports)
        logger.info("gov[%s]: would forward %d report(s)", self.name, len(reports))
        return True

    def fetch_blocklist(self) -> list[str]:
        logger.info("gov[%s]: fetch_blocklist (stub -> [])", self.name)
        return []


@dataclass
class EmailIntakeConnector:
    """Forward confirmed phishing to an agency intake mailbox as a CSV email.

    Push-only: ``fetch_blocklist`` returns ``[]`` (email is not a pull channel).
    Sending is best-effort and returns False (logging a warning) when SMTP is
    not fully configured, so a misconfiguration never throws into a caller.
    """

    name: str = "email"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    use_tls: bool = True
    sender: str = ""
    recipients: tuple[str, ...] = ()

    @classmethod
    def from_settings(cls, settings) -> EmailIntakeConnector:
        recipients = tuple(
            r.strip() for r in (settings.gov_email_to or "").split(",") if r.strip()
        )
        return cls(
            smtp_host=settings.gov_email_smtp_host,
            smtp_port=settings.gov_email_smtp_port,
            smtp_user=settings.gov_email_smtp_user,
            smtp_password=settings.gov_email_smtp_password,
            use_tls=settings.gov_email_use_tls,
            sender=settings.gov_email_from or settings.gov_email_smtp_user,
            recipients=recipients,
        )

    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.sender and self.recipients)

    def _build_message(self, reports: list[GovReport]) -> EmailMessage:
        today = dt.date.today().isoformat()
        msg = EmailMessage()
        msg["Subject"] = f"[Thai Phishing Detector] รายงาน phishing {len(reports)} URL ({today})"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.set_content(
            "เรียนเจ้าหน้าที่\n\n"
            f"ระบบตรวจจับเว็บไซต์ฟิชชิงส่งรายงาน URL ที่ยืนยันว่าเป็น phishing "
            f"จำนวน {len(reports)} รายการ (แนบไฟล์ CSV)\n\n"
            "ส่งอัตโนมัติเพื่อการประสานงาน — โปรดตรวจสอบก่อนดำเนินการ\n"
        )
        msg.add_attachment(
            reports_to_csv(reports).encode("utf-8"),
            maintype="text",
            subtype="csv",
            filename=f"phishing-report-{today}.csv",
        )
        return msg

    def forward_report(self, report: GovReport) -> bool:
        return self.forward_reports([report])

    def forward_reports(self, reports: list[GovReport]) -> bool:
        if not reports:
            return True
        if not self.is_configured():
            logger.warning(
                "gov[email]: SMTP not configured (set GOV_EMAIL_* ) -- skipping %d report(s)",
                len(reports),
            )
            return False
        msg = self._build_message(reports)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.smtp_user:
                    smtp.login(self.smtp_user, self.smtp_password)
                smtp.send_message(msg)
        except Exception as exc:  # noqa: BLE001 - never throw into the caller
            logger.error("gov[email]: send failed: %s", exc)
            return False
        logger.info(
            "gov[email]: forwarded %d report(s) to %s", len(reports), ", ".join(self.recipients)
        )
        return True

    def fetch_blocklist(self) -> list[str]:
        return []


# Registry of available connectors. "stub" is a singleton; "email" is built from
# settings on demand (so credentials are read at selection time).
_CONNECTORS: dict[str, GovernmentConnector] = {
    "stub": StubGovernmentConnector(),
}


def get_connector(name: str, settings=None) -> GovernmentConnector:
    """Return the configured connector, falling back to the stub.

    ``email`` is constructed from ``settings`` (defaulting to the app settings).
    """
    if name == "email":
        if settings is None:
            from app.config import settings as app_settings

            settings = app_settings
        return EmailIntakeConnector.from_settings(settings)
    return _CONNECTORS.get(name, _CONNECTORS["stub"])
