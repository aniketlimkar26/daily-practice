# 📧 Email Automation CLI

**Roadmap stage:** Automation — Project 1
**Skills practiced:** `smtplib`, `email.mime`, environment-based config, CSV mail merge, `unittest.mock`

A command-line tool for sending single emails or personalized bulk
emails (mail merge from a CSV) via SMTP — with attachments, HTML
support, and a dry-run mode so you can preview before anything is
actually sent.

## 🔒 Credentials Are Never Hardcoded

SMTP credentials live in a local `.env` file, which is **gitignored** and
never committed. The repo only ships `.env.example` (no real secrets) —
you copy it to `.env` and fill in your own details.

**For Gmail specifically:** you cannot use your normal account password.
You need to generate an **App Password**:
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate an App Password: https://myaccount.google.com/apppasswords

## ✨ Features

- **Single email** — with optional HTML body and file attachments
- **Bulk mail merge** — personalize subject/body per recipient from a CSV
  (`{name}`, `{company}`, or any column you add)
- **Dry-run mode** — preview exactly what would be sent, with zero
  network connections opened, before sending anything real
- **Rate-limit friendly** — configurable delay between bulk sends, since
  providers like Gmail throttle/block rapid-fire sending
- **Logging** — every send attempt (success or failure) is logged to
  `email_automation.log`
- **Tested without needing a real mailbox** — all SMTP calls are mocked
  in tests using `unittest.mock`, so the test suite runs instantly and
  never sends real email

## 📂 Project Structure

```
email-automation/
├── automation.py                  # CLI entry point
├── config.py                      # loads SMTP credentials from .env
├── emailer.py                     # builds/sends a single email
├── bulk.py                        # CSV mail merge logic
├── create_sample_contacts.py      # generates a sample contacts.csv
├── test_email_automation.py       # unit tests (15 tests, mocked SMTP)
├── .env.example                   # template - copy to .env
├── requirements.txt
└── README.md
```

## 🚀 Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# then edit .env with your real SMTP details
```

## 🚀 Usage

### 1. Always try --dry-run first

```bash
python automation.py send --to alice@example.com --subject "Test" --body "Hello!" --dry-run
```

### 2. Send a single email (with an attachment)

```bash
python automation.py send --to alice@example.com --subject "Report" \
    --body "See attached." --attach report.pdf
```

### 3. Bulk mail merge

```bash
python create_sample_contacts.py
python automation.py bulk --csv contacts.csv \
    --subject "Hi {name}!" \
    --body "Hello {name}, welcome to {company}." \
    --dry-run

# Remove --dry-run once you've checked the preview
python automation.py bulk --csv contacts.csv \
    --subject "Hi {name}!" \
    --body "Hello {name}, welcome to {company}." \
    --delay 2
```

### 4. HTML email

```bash
python automation.py send --to alice@example.com --subject "Newsletter" \
    --body "<h1>Hello!</h1><p>This is <b>HTML</b>.</p>" --html
```

## 🧪 Running Tests

```bash
python -m unittest test_email_automation.py -v
```
Tests use `unittest.mock` to simulate `smtplib.SMTP` entirely — no real
network connection or mailbox is ever touched, and the whole suite runs
in well under a second.

## 🧠 What I Learned

- Sending real emails with `smtplib` + `email.mime` (multipart messages,
  attachments, STARTTLS)
- **Never commit secrets**: separating config (`.env`, gitignored) from
  code (`config.py`, committed) — the same discipline as Project 4's
  password manager
- Mocking external services in tests with `unittest.mock.patch` — you
  can thoroughly test code that talks to a real API/server without ever
  actually calling it, which is essential for a fast, reliable, and
  free-to-run test suite
- Mail merge: using `str.format()` with a CSV row as a template context,
  and validating the template's placeholders match the CSV's columns
  before sending anything
- Being a "good citizen" of an external service: adding a delay between
  bulk sends to respect provider rate limits, rather than hammering
  their API

## 🔮 Possible Future Improvements

- [ ] Read incoming emails via IMAP (auto-reply bot, inbox triage)
- [ ] Retry failed sends with exponential backoff
- [ ] Jinja2 templates instead of simple `.format()` for richer HTML emails

---
📅 Part of my [Python Basics → Production Project roadmap](../../README.md).
