"""
Email Service — Gmail SMTP with STARTTLS.
Uses smtplib (stdlib) + Jinja2 HTML templates.
Credentials come from environment variables only.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config.settings import settings

logger = logging.getLogger(__name__)

_jinja_env = Environment(
    loader=FileSystemLoader("src/notifications/templates"),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, context: dict) -> str:
    try:
        template = _jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as exc:
        logger.error("Template render error (%s): %s", template_name, exc)
        return str(context)


def _send(to_address: str, subject: str, html_body: str) -> bool:
    if not settings.email_enabled:
        logger.info("Email disabled — skipping send to %s", to_address)
        return False

    if not settings.email_username or not settings.email_password:
        logger.warning("Email credentials not configured — skipping send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_username}>"
    msg["To"] = to_address
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.sendmail(settings.email_username, to_address, msg.as_string())
        logger.info("Email sent to %s | Subject: %s", to_address, subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check EMAIL_USERNAME / EMAIL_PASSWORD.")
        return False
    except Exception as exc:
        logger.error("SMTP error sending to %s: %s", to_address, exc)
        return False


def send_auto_route_notification(
    to_email: str,
    ticket_id: str,
    summary: str,
    category: str,
    priority: str,
    assignee: str,
    team: str,
    confidence: float,
) -> bool:
    """Send notification email when a ticket is auto-routed."""
    subject = f"[{priority}] Ticket Auto-Routed: {ticket_id} — {summary[:60]}"
    html = _render(
        "auto_route.html",
        {
            "ticket_id": ticket_id,
            "summary": summary,
            "category": category,
            "priority": priority,
            "assignee": assignee,
            "team": team,
            "confidence": f"{confidence:.0%}",
        },
    )
    return _send(to_email, subject, html)


def send_flagged_digest(
    to_email: str,
    flagged_tickets: list[dict],
) -> bool:
    """Send a digest email listing flagged tickets that need review."""
    if not flagged_tickets:
        return False
    subject = f"[Action Required] {len(flagged_tickets)} Ticket(s) Need Manual Review"
    html = _render("flagged_digest.html", {"tickets": flagged_tickets})
    return _send(to_email, subject, html)
