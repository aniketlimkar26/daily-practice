"""
Unit tests for config.py, emailer.py, and bulk.py.
Uses unittest.mock to simulate smtplib so tests never touch a real
mail server or send real emails.

Run with:  python -m unittest test_email_automation.py -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bulk import load_recipients, render_template, send_bulk
from config import ConfigError, SMTPConfig, load_smtp_config
from emailer import build_message, send_email


def make_config():
    return SMTPConfig(
        server="smtp.example.com", port=587,
        sender_email="me@example.com", sender_password="app-password",
        sender_name="Test Sender",
    )


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_missing_env_file_raises_config_error(self):
        import os
        os.chdir(self.tmp_dir)
        try:
            # No .env file and no relevant env vars present -> should raise
            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(ConfigError):
                    load_smtp_config()
        finally:
            os.chdir(self.original_cwd)

    def test_valid_env_loads_correctly(self):
        env_vars = {
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "587",
            "SENDER_EMAIL": "me@example.com",
            "SENDER_PASSWORD": "secret",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            config = load_smtp_config()
            self.assertEqual(config.server, "smtp.example.com")
            self.assertEqual(config.port, 587)

    def test_invalid_port_raises_config_error(self):
        env_vars = {
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "not-a-number",
            "SENDER_EMAIL": "me@example.com",
            "SENDER_PASSWORD": "secret",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            with self.assertRaises(ConfigError):
                load_smtp_config()


class TestBuildMessage(unittest.TestCase):
    def test_basic_message_fields(self):
        config = make_config()
        msg = build_message(config, "alice@example.com", "Hello", "Hi Alice")
        self.assertEqual(msg["To"], "alice@example.com")
        self.assertEqual(msg["Subject"], "Hello")
        self.assertIn("me@example.com", msg["From"])

    def test_attachment_not_found_raises(self):
        config = make_config()
        with self.assertRaises(FileNotFoundError):
            build_message(config, "a@example.com", "Subj", "Body",
                           attachments=["/nonexistent/file.pdf"])

    def test_attachment_included_when_file_exists(self):
        config = make_config()
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            file_path = tmp_dir / "report.txt"
            file_path.write_text("some content")
            msg = build_message(config, "a@example.com", "Subj", "Body",
                                 attachments=[str(file_path)])
            # Multipart message should have 2 parts: body + attachment
            self.assertEqual(len(msg.get_payload()), 2)
        finally:
            shutil.rmtree(tmp_dir)


class TestSendEmail(unittest.TestCase):
    def test_dry_run_does_not_open_smtp_connection(self):
        config = make_config()
        msg = build_message(config, "a@example.com", "Subj", "Body")
        with patch("emailer.smtplib.SMTP") as mock_smtp:
            result = send_email(config, msg, "a@example.com", dry_run=True)
            self.assertTrue(result)
            mock_smtp.assert_not_called()

    def test_successful_send_calls_smtp_correctly(self):
        config = make_config()
        msg = build_message(config, "a@example.com", "Subj", "Body")

        with patch("emailer.smtplib.SMTP") as mock_smtp_class:
            mock_server = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server

            result = send_email(config, msg, "a@example.com", dry_run=False)

            self.assertTrue(result)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("me@example.com", "app-password")
            mock_server.sendmail.assert_called_once()

    def test_auth_failure_returns_false(self):
        import smtplib
        config = make_config()
        msg = build_message(config, "a@example.com", "Subj", "Body")

        with patch("emailer.smtplib.SMTP") as mock_smtp_class:
            mock_server = MagicMock()
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad creds")
            mock_smtp_class.return_value.__enter__.return_value = mock_server

            result = send_email(config, msg, "a@example.com", dry_run=False)
            self.assertFalse(result)


class TestBulkMailMerge(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.csv_path = self.tmp_dir / "contacts.csv"
        self.csv_path.write_text(
            "email,name,company\n"
            "alice@example.com,Alice,Acme Corp\n"
            "bob@example.com,Bob,Widgets Inc\n"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_load_recipients_parses_csv(self):
        recipients = load_recipients(self.csv_path)
        self.assertEqual(len(recipients), 2)
        self.assertEqual(recipients[0]["name"], "Alice")

    def test_load_recipients_requires_email_column(self):
        bad_csv = self.tmp_dir / "bad.csv"
        bad_csv.write_text("name,company\nAlice,Acme\n")
        with self.assertRaises(ValueError):
            load_recipients(bad_csv)

    def test_render_template_fills_placeholders(self):
        row = {"name": "Alice", "company": "Acme Corp"}
        result = render_template("Hi {name}, welcome to {company}!", row)
        self.assertEqual(result, "Hi Alice, welcome to Acme Corp!")

    def test_render_template_missing_column_raises(self):
        row = {"name": "Alice"}
        with self.assertRaises(ValueError):
            render_template("Hi {name}, your role is {role}", row)

    def test_send_bulk_dry_run_reports_all_sent(self):
        config = make_config()
        summary = send_bulk(config, self.csv_path, "Hi {name}", "Hello {name} from {company}",
                             dry_run=True, delay_seconds=0)
        self.assertEqual(summary["sent"], 2)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["total"], 2)

    def test_send_bulk_real_send_uses_mocked_smtp(self):
        config = make_config()
        with patch("emailer.smtplib.SMTP") as mock_smtp_class:
            mock_server = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server

            summary = send_bulk(config, self.csv_path, "Hi {name}", "Hello {name}",
                                 dry_run=False, delay_seconds=0)

            self.assertEqual(summary["sent"], 2)
            self.assertEqual(mock_server.sendmail.call_count, 2)


if __name__ == "__main__":
    unittest.main()
