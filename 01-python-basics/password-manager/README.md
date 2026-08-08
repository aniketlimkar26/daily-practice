# 🔐 Password Manager CLI

**Roadmap stage:** Python Basics — Project 4
**Skills practiced:** encryption (AES via Fernet), password hashing (PBKDF2), JSON storage, secure coding practices, `unittest`

A local, encrypted password manager. Every entry is encrypted with a key
derived from your master password. The master password itself is **never
stored anywhere** — only a salted hash used to verify it.

## 🔒 Security Design (the actual point of this project)

| Concern | How it's handled |
|---|---|
| Storing the master password | **Never stored.** Only a salted PBKDF2 hash is kept, used purely to verify a login attempt. |
| Encrypting saved passwords | A separate encryption key is *derived* from the master password (PBKDF2, different salt) and used with **Fernet** (AES-128-CBC + HMAC) from the well-vetted `cryptography` library — not a custom cipher. |
| Brute-force resistance | PBKDF2 with **390,000 iterations** (OWASP's 2023 recommendation for PBKDF2-HMAC-SHA256), making each guess computationally expensive. |
| Timing attacks on login | Password verification uses `hmac.compare_digest` (constant-time comparison) instead of `==`. |
| Master password on the CLI | **Never accepted as a command-line argument.** Command-line args are visible in shell history and process lists (`ps aux`). It's always entered via a hidden `getpass` prompt. |
| Random password generation | Uses Python's `secrets` module, not `random` — `random` is predictable and unsafe for anything security-related. |

## ✨ Features

- `init` — create a new encrypted vault
- `add` — add or update an entry (manually typed or auto-generated password)
- `list` — see saved service/username pairs **without** decrypting anything
- `get` — retrieve and decrypt one entry
- `delete` — remove an entry
- `generate` — generate a strong random password (standalone, no vault needed)

## 📂 Project Structure

```
password-manager/
├── manager.py                  # CLI entry point (argparse subcommands)
├── vault.py                    # core: hashing, key derivation, encryption, CRUD
├── generator.py                # secure random password generator
├── test_password_manager.py    # unit tests (24 tests)
├── requirements.txt
└── README.md
```

## 🚀 Setup

```bash
pip install -r requirements.txt
```

## 🚀 Usage

```bash
# 1. Create your vault (prompts twice for a master password)
python manager.py init

# 2. Add an entry with an auto-generated password
python manager.py add --service Gmail --username me@gmail.com --generate --length 20

# 3. Add an entry with your own password (prompted, hidden)
python manager.py add --service GitHub --username myhandle

# 4. List saved entries (services/usernames only — passwords stay hidden)
python manager.py list

# 5. Retrieve one entry (decrypts and shows the password)
python manager.py get --service Gmail

# 6. Delete an entry
python manager.py delete --service Gmail

# 7. Just generate a password, no vault involved
python manager.py generate --length 24
python manager.py generate --length 12 --no-symbols
```

Every command that touches the vault (`add`, `list`, `get`, `delete`)
prompts you for your master password — this mirrors how real password
managers require you to unlock the vault each session.

## 🧪 Running Tests

```bash
python -m unittest test_password_manager.py -v
```
(Tests take a few seconds — that's the 390,000 PBKDF2 iterations doing
their job, even in test mode. This is expected and correct.)

## 🧠 What I Learned

- The difference between **hashing** (one-way, used for verification —
  passwords) and **encryption** (two-way, reversible with a key — stored
  secrets)
- Why you derive a *separate* key for encryption vs. the hash used for
  login verification, instead of reusing the same value for both
- Why salts matter (they defeat precomputed "rainbow table" attacks and
  ensure two identical passwords don't produce identical hashes)
- Why `secrets` exists as a separate module from `random` in the first
  place, and when each one is appropriate
- Why secrets should never be passed as CLI arguments, and how `getpass`
  solves that

## ⚠️ Disclaimer

This is a learning project to understand encryption/hashing concepts
hands-on. For actual personal password management, use a maintained,
audited tool (Bitwarden, 1Password, KeePass, etc.).

## 🔮 Possible Future Improvements

- [ ] "Change master password" command (re-encrypt all entries with a new key)
- [ ] Clipboard copy instead of printing passwords to the terminal
- [ ] Auto-lock / timeout after inactivity

---
📅 Part of my [Python Basics → Production Project roadmap](../README.md).
