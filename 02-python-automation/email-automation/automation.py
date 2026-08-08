"""
Email Automation CLI
----------------------
Send single emails or bulk personalized emails (mail merge from CSV)
via SMTP, with attachments and a dry-run mode.

SETUP (required before sending real emails):
    1. Copy .env.example to .env
    2. Fill in your SMTP server details. For Gmail:
       SMTP_SERVER=smtp.gmail.com
       SMTP_PORT=587
       SENDER_EMAIL=you@gmail.com
       SENDER_PASSWORD=<a Gmail App Password, not your normal password>
    3. pip install -r requirements.txt

Usage:
    # Single email
    python automation.py send --to alice@example.com --subject "Hi" --body "Hello there!"
    python automation.py send --to alice@example.com --subject "Report" --body "See attached" --attach report.pdf

    # Bulk mail merge from CSV
    python automation.py bulk --csv contacts.csv --subject "Hi {name}!" --body "Hello {name}, welcome to {company}."

    # Always try --dry-run first!
    python automation.py send --to alice@example.com --subject "Test" --body "Test" --dry-run
    python automation.py bulk --csv contacts.csv --subject "Hi {name}" --body "..." --dry-run

Author: (your name) - Automation Project 1
"""

import argparse
import logging
import sys
from pathlib import Path

from bulk import send_bulk
from config import ConfigError, load_smtp_config
from emailer import build_message, send_email

LOG_FILE_NAME = "email_automation.log"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE_NAME, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def cmd_send(args) -> None:
    config = load_smtp_config()
    attachments = args.attach or []
    message = build_message(config, args.to, args.subject, args.body,
                             html=args.html, attachments=attachments)
    success = send_email(config, message, args.to, dry_run=args.dry_run)
    if not success:
        sys.exit(1)


def cmd_bulk(args) -> None:
    config = load_smtp_config()
    attachments = args.attach or []
    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    summary = send_bulk(
        config, csv_path, args.subject, args.body,
        html=args.html, attachments=attachments,
        dry_run=args.dry_run, delay_seconds=args.delay,
    )

    print(f"\nDone. Sent: {summary['sent']}/{summary['total']}  Failed: {summary['failed']}")
    if summary["failures"]:
        print("Failed recipients:", ", ".join(summary["failures"]))


def parse_args():
    parser = argparse.ArgumentParser(description="Email Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_send = subparsers.add_parser("send", help="Send a single email")
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", required=True)
    p_send.add_argument("--html", action="store_true", help="Treat body as HTML")
    p_send.add_argument("--attach", action="append", help="Path to a file to attach (repeatable)")
    p_send.add_argument("--dry-run", action="store_true", help="Preview without actually sending")

    p_bulk = subparsers.add_parser("bulk", help="Send personalized emails from a CSV (mail merge)")
    p_bulk.add_argument("--csv", required=True, help="Path to CSV with an 'email' column")
    p_bulk.add_argument("--subject", required=True, help="Subject template, e.g. 'Hi {name}!'")
    p_bulk.add_argument("--body", required=True, help="Body template, e.g. 'Hello {name}...'")
    p_bulk.add_argument("--html", action="store_true", help="Treat body as HTML")
    p_bulk.add_argument("--attach", action="append", help="Path to a file to attach to every email (repeatable)")
    p_bulk.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between sends (default: 1.0)")
    p_bulk.add_argument("--dry-run", action="store_true", help="Preview without actually sending")

    return parser.parse_args()


def main():
    setup_logging()
    args = parse_args()

    try:
        if args.command == "send":
            cmd_send(args)
        elif args.command == "bulk":
            cmd_bulk(args)
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
