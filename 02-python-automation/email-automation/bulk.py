"""
bulk.py — mail merge: send personalized emails to a list of recipients
loaded from a CSV file, using a template with {placeholders}.

CSV must have an 'email' column at minimum; any other columns (name,
company, etc.) can be used as placeholders in the subject/body template.

Example CSV:
    email,name,company
    alice@example.com,Alice,Acme Corp
    bob@example.com,Bob,Widgets Inc

Example template usage:
    subject = "Hello {name}!"
    body    = "Hi {name}, thanks for being part of {company}."
"""

import csv
import logging
import time
from pathlib import Path

from config import SMTPConfig
from emailer import build_message, send_email

logger = logging.getLogger(__name__)


def load_recipients(csv_path: Path) -> list:
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "email" not in (reader.fieldnames or []):
            raise ValueError(f"CSV must have an 'email' column. Found columns: {reader.fieldnames}")
        return list(reader)


def render_template(template: str, row: dict) -> str:
    """Fill {placeholders} in a template using values from a CSV row."""
    try:
        return template.format(**row)
    except KeyError as e:
        raise ValueError(f"Template references column {e} which is not in the CSV.")


def send_bulk(config: SMTPConfig, csv_path: Path, subject_template: str,
              body_template: str, html: bool = False, attachments: list = None,
              dry_run: bool = False, delay_seconds: float = 1.0) -> dict:
    """
    Send a personalized email to every row in the CSV.
    Returns a summary dict: {"sent": N, "failed": N, "failures": [emails]}
    """
    recipients = load_recipients(csv_path)
    sent = 0
    failed = 0
    failures = []

    for i, row in enumerate(recipients):
        to = row["email"]
        subject = render_template(subject_template, row)
        body = render_template(body_template, row)

        message = build_message(config, to, subject, body, html=html, attachments=attachments)
        success = send_email(config, message, to, dry_run=dry_run)

        if success:
            sent += 1
        else:
            failed += 1
            failures.append(to)

        # Small delay between real sends to avoid tripping the SMTP
        # provider's rate limits (Gmail, in particular, is aggressive
        # about throttling/blocking rapid-fire sends).
        if not dry_run and i < len(recipients) - 1:
            time.sleep(delay_seconds)

    return {"sent": sent, "failed": failed, "failures": failures, "total": len(recipients)}
