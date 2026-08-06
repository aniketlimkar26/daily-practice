"""
vault.py — core logic for the Password Manager.

Security design (read this before touching anything!):

1. The master password is NEVER stored anywhere, in any form that could
   be reversed back into the password.

2. To VERIFY a master password on unlock, we store a salted PBKDF2 hash
   of it (verifier_salt + verifier_hash). This is the same pattern real
   systems use for login passwords: check "does this hash match?" rather
   than "is this the same string?".

3. To ENCRYPT/DECRYPT the saved entries, we derive a separate symmetric
   key from the master password using PBKDF2 with a different salt
   (key_salt). This key is only ever kept in memory for the duration of
   the program run — never written to disk.

4. Individual passwords are encrypted with Fernet (AES-128 in CBC mode
   with HMAC authentication, from the `cryptography` library) — a
   well-vetted implementation, not a custom cipher.

5. PBKDF2 iteration count (390,000) follows OWASP's 2023 recommendation
   for PBKDF2-HMAC-SHA256, to make brute-forcing the master password
   computationally expensive.
"""

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

PBKDF2_ITERATIONS = 390_000
SALT_BYTES = 16


class VaultError(Exception):
    """Raised for vault-related problems (wrong password, missing entry, etc.)."""


# --------------------------------------------------------------------------
# Key derivation & password hashing
# --------------------------------------------------------------------------
def _pbkdf2(password: str, salt: bytes, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=length
    )


def derive_encryption_key(master_password: str, key_salt: bytes) -> bytes:
    """Derive a 32-byte key from the master password, encoded for Fernet."""
    raw_key = _pbkdf2(master_password, key_salt, length=32)
    return base64.urlsafe_b64encode(raw_key)


def derive_verifier_hash(master_password: str, verifier_salt: bytes) -> str:
    """Derive a hash used ONLY to check whether a password is correct."""
    return _pbkdf2(master_password, verifier_salt, length=32).hex()


# --------------------------------------------------------------------------
# Vault file structure
# --------------------------------------------------------------------------
def vault_exists(vault_file: Path) -> bool:
    return vault_file.exists()


def create_vault(vault_file: Path, master_password: str) -> None:
    """Initialize a brand-new, empty vault protected by master_password."""
    if vault_file.exists():
        raise VaultError(f"Vault already exists at {vault_file}")

    key_salt = os.urandom(SALT_BYTES)
    verifier_salt = os.urandom(SALT_BYTES)
    verifier_hash = derive_verifier_hash(master_password, verifier_salt)

    data = {
        "key_salt": base64.b64encode(key_salt).decode(),
        "verifier_salt": base64.b64encode(verifier_salt).decode(),
        "verifier_hash": verifier_hash,
        "entries": [],
    }
    _save(vault_file, data)


def _load(vault_file: Path) -> dict:
    if not vault_file.exists():
        raise VaultError(f"No vault found at {vault_file}. Run 'init' first.")
    with open(vault_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(vault_file: Path, data: dict) -> None:
    with open(vault_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def unlock(vault_file: Path, master_password: str):
    """
    Verify the master password and return (fernet, data) for use in this
    session. Raises VaultError if the password is wrong.
    """
    data = _load(vault_file)
    verifier_salt = base64.b64decode(data["verifier_salt"])
    expected_hash = derive_verifier_hash(master_password, verifier_salt)

    # Use constant-time comparison to avoid leaking timing information
    # about how much of the hash matched (a real security concern!).
    if not hmac.compare_digest(expected_hash, data["verifier_hash"]):
        raise VaultError("Incorrect master password.")

    key_salt = base64.b64decode(data["key_salt"])
    fernet_key = derive_encryption_key(master_password, key_salt)
    return Fernet(fernet_key), data


# --------------------------------------------------------------------------
# CRUD operations on entries (require an unlocked fernet + data)
# --------------------------------------------------------------------------
def add_entry(vault_file: Path, fernet: Fernet, data: dict,
              service: str, username: str, password: str) -> None:
    encrypted = fernet.encrypt(password.encode("utf-8")).decode("utf-8")

    entries = data["entries"]
    for entry in entries:
        if entry["service"].lower() == service.lower():
            entry["username"] = username
            entry["encrypted_password"] = encrypted
            _save(vault_file, data)
            return

    entries.append({"service": service, "username": username, "encrypted_password": encrypted})
    _save(vault_file, data)


def list_entries(data: dict) -> list:
    """Return service + username only — never decrypts passwords."""
    return [{"service": e["service"], "username": e["username"]} for e in data["entries"]]


def get_entry(fernet: Fernet, data: dict, service: str) -> dict:
    for entry in data["entries"]:
        if entry["service"].lower() == service.lower():
            try:
                decrypted = fernet.decrypt(entry["encrypted_password"].encode("utf-8")).decode("utf-8")
            except InvalidToken:
                raise VaultError("Could not decrypt this entry (vault may be corrupted).")
            return {"service": entry["service"], "username": entry["username"], "password": decrypted}
    raise VaultError(f"No entry found for service '{service}'.")


def delete_entry(vault_file: Path, data: dict, service: str) -> None:
    entries = data["entries"]
    for i, entry in enumerate(entries):
        if entry["service"].lower() == service.lower():
            entries.pop(i)
            _save(vault_file, data)
            return
    raise VaultError(f"No entry found for service '{service}'.")
