"""
config.py — loads SMTP credentials from a local .env file.

SECURITY NOTE: credentials are NEVER hardcoded in source files and NEVER
committed to git. They live in a local `.env` file (gitignored) and are
loaded into environment variables at runtime via python-dotenv. Anyone
cloning this repo has to create their own `.env` from `.env.example`.

For Gmail specifically: you cannot use your normal account password.
You must generate an "App Password" (requires 2-Step Verification to be
enabled on your Google account) at:
    https://myaccount.google.com/apppasswords
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class SMTPConfig:
    server: str
    port: int
    sender_email: str
    sender_password: str
    sender_name: str = ""


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_smtp_config() -> SMTPConfig:
    load_dotenv()  # reads .env in the current directory into os.environ

    server = os.getenv("SMTP_SERVER")
    port = os.getenv("SMTP_PORT")
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    sender_name = os.getenv("SENDER_NAME", "")

    missing = [name for name, value in [
        ("SMTP_SERVER", server), ("SMTP_PORT", port),
        ("SENDER_EMAIL", sender_email), ("SENDER_PASSWORD", sender_password),
    ] if not value]

    if missing:
        raise ConfigError(
            f"Missing required setting(s) in .env: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill in your details."
        )

    try:
        port_int = int(port)
    except ValueError:
        raise ConfigError(f"SMTP_PORT must be a number, got: {port}")

    return SMTPConfig(
        server=server, port=port_int,
        sender_email=sender_email, sender_password=sender_password,
        sender_name=sender_name,
    )
