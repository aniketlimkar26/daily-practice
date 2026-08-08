"""
emailer.py — builds and sends emails via SMTP.

Design notes:
- Uses smtplib + email.mime, both standard library (no need for a
  heavyweight email SDK for this use case).
- Connects with STARTTLS, so credentials and message content are
  encrypted in transit.
- build_message() and send_email() are separate on purpose, so the
  message can be inspected/logged in --dry-run mode without ever
  opening a network connection.
"""

import logging
import mimetypes
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

from config import SMTPConfig

logger = logging.getLogger(__name__)


def build_message(config: SMTPConfig, to: str, subject: str, body: str,
                   html: bool = False, attachments: list = None) -> MIMEMultipart:
    msg = MIMEMultipart()
    from_header = f"{config.sender_name} <{config.sender_email}>" if config.sender_name else config.sender_email
    msg["From"] = from_header
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html" if html else "plain"))

    for file_path in (attachments or []):
        _attach_file(msg, Path(file_path))

    return msg


def _attach_file(msg: MIMEMultipart, file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Attachment not found: {file_path}")

    ctype, _ = mimetypes.guess_type(str(file_path))
    maintype, subtype = (ctype.split("/", 1) if ctype else ("application", "octet-stream"))

    with open(file_path, "rb") as f:
        part = MIMEBase(maintype, subtype)
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
    msg.attach(part)


def send_email(config: SMTPConfig, message: MIMEMultipart, to: str, dry_run: bool = False) -> bool:
    """
    Send a single pre-built message. Returns True on success.
    In dry-run mode, does not open a network connection at all —
    just logs what would have been sent.
    """
    if dry_run:
        logger.info("[DRY-RUN] Would send to %s | Subject: %s", to, message["Subject"])
        return True

    try:
        with smtplib.SMTP(config.server, config.port, timeout=15) as server:
            server.starttls()
            server.login(config.sender_email, config.sender_password)
            server.sendmail(config.sender_email, to, message.as_string())
        logger.info("Sent to %s | Subject: %s", to, message["Subject"])
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Authentication failed. Check SENDER_EMAIL/SENDER_PASSWORD "
                      "in .env (Gmail requires an App Password, not your normal password).")
        return False
    except smtplib.SMTPException as e:
        logger.error("Failed to send to %s: %s", to, e)
        return False
    except OSError as e:
        logger.error("Network error while sending to %s: %s", to, e)
        return False
