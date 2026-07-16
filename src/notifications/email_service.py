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


def send_recommendation_approval_email(tickets: list[dict]) -> bool:
    """
    Send one batch email listing all non-EDI team recommendations.
    Each ticket has an Approve button that hits /api/approve/{ticket_id}?token=...
    Sent to settings.approval_email.
    """
    if not tickets:
        return False

    if not settings.approval_email:
        logger.warning("APPROVAL_EMAIL not configured — skipping recommendation email.")
        return False

    rows_html = ""
    for t in tickets:
        tid   = t.get("Ticket_ID", "")
        token = t.get("Approval_Token", "")
        link  = f"{settings.api_base_url}/api/approve/{tid}?token={token}"
        prio  = t.get("AI_Priority", "")
        prio_colours = {"P1": "#ffc7ce", "P2": "#ffeb9c", "P3": "#bdd7ee", "P4": "#c6efce"}
        prio_bg = prio_colours.get(prio, "#f5f5f5")
        rows_html += f"""
        <tr>
          <td style='padding:9px 12px;border:1px solid #e8e8e8;font-weight:600'>{tid}</td>
          <td style='padding:9px 12px;border:1px solid #e8e8e8;background:{prio_bg};
                     text-align:center;font-weight:700'>{prio}</td>
          <td style='padding:9px 12px;border:1px solid #e8e8e8'>{t.get("Summary","")[:80]}</td>
          <td style='padding:9px 12px;border:1px solid #e8e8e8;color:#1677ff;font-weight:600'>
              {t.get("Assigned_Team_AI","")}</td>
          <td style='padding:9px 12px;border:1px solid #e8e8e8;color:#595959'>
              {t.get("AI_Category","")}</td>
          <td style='padding:9px 12px;border:1px solid #e8e8e8;text-align:center'>
            <a href='{link}'
               style='display:inline-block;background:#52c41a;color:#fff;padding:6px 18px;
                      border-radius:4px;text-decoration:none;font-weight:700;font-size:13px'>
              ✔ Approve
            </a>
          </td>
        </tr>"""

    final_excel_url = f"{settings.api_base_url}/api/tickets/download/final"
    html = f"""
    <html>
    <body style='font-family:Calibri,Arial,sans-serif;color:#1a1a2e;max-width:900px;margin:auto;padding:24px'>
      <div style='background:#001529;padding:18px 24px;border-radius:6px 6px 0 0'>
        <h2 style='color:#fff;margin:0'>AI Ticket Routing — Team Recommendations</h2>
        <p style='color:#8c9bb5;margin:6px 0 0'>Action required: review and approve each suggestion</p>
      </div>
      <div style='background:#f0f5ff;padding:14px 24px;border:1px solid #d6e4ff'>
        <p style='margin:0;color:#003eb3'>
          <b>{len(tickets)} ticket(s)</b> were routed to non-EDI teams by the AI as
          <b>recommendations</b>. These are <u>not final</u> until you approve them.<br>
          Click <b>Approve</b> next to each ticket to confirm the team assignment.
        </p>
      </div>
      <table style='width:100%;border-collapse:collapse;margin-top:0'>
        <tr style='background:#001529;color:#fff'>
          <th style='padding:10px 12px;border:1px solid #e8e8e8;text-align:left'>Ticket ID</th>
          <th style='padding:10px 12px;border:1px solid #e8e8e8'>Priority</th>
          <th style='padding:10px 12px;border:1px solid #e8e8e8;text-align:left'>Summary</th>
          <th style='padding:10px 12px;border:1px solid #e8e8e8;text-align:left'>Recommended Team</th>
          <th style='padding:10px 12px;border:1px solid #e8e8e8;text-align:left'>Category</th>
          <th style='padding:10px 12px;border:1px solid #e8e8e8'>Action</th>
        </tr>
        {rows_html}
      </table>
      <div style='margin-top:20px;padding:14px 24px;background:#f6ffed;
                  border:1px solid #b7eb8f;border-radius:0 0 6px 6px'>
        <p style='margin:0;color:#237804'>
          Once all tickets are approved, download the
          <a href='{final_excel_url}' style='color:#237804;font-weight:700'>Final Excel Report</a>
          — it will contain only confirmed assignments.
        </p>
      </div>
    </body>
    </html>"""

    subject = f"[Action Required] {len(tickets)} Ticket Routing Recommendation(s) — Please Approve"
    return _send(settings.approval_email, subject, html)
