"""
Unit tests for vault.py and generator.py
Run with:  python -m unittest test_password_manager.py -v
"""

import shutil
import string
import tempfile
import unittest
from pathlib import Path

import vault
from generator import generate_password


class TestKeyDerivation(unittest.TestCase):
    def test_same_password_and_salt_gives_same_key(self):
        salt = b"0123456789abcdef"
        key1 = vault.derive_encryption_key("hunter2", salt)
        key2 = vault.derive_encryption_key("hunter2", salt)
        self.assertEqual(key1, key2)

    def test_different_password_gives_different_key(self):
        salt = b"0123456789abcdef"
        key1 = vault.derive_encryption_key("hunter2", salt)
        key2 = vault.derive_encryption_key("differentpw", salt)
        self.assertNotEqual(key1, key2)

    def test_different_salt_gives_different_key(self):
        key1 = vault.derive_encryption_key("hunter2", b"0123456789abcdef")
        key2 = vault.derive_encryption_key("hunter2", b"fedcba9876543210")
        self.assertNotEqual(key1, key2)

    def test_verifier_hash_is_deterministic(self):
        salt = b"0123456789abcdef"
        h1 = vault.derive_verifier_hash("hunter2", salt)
        h2 = vault.derive_verifier_hash("hunter2", salt)
        self.assertEqual(h1, h2)


class TestVaultLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.vault_file = self.tmp_dir / "vault.json"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_create_vault_writes_file(self):
        vault.create_vault(self.vault_file, "master123")
        self.assertTrue(self.vault_file.exists())

    def test_create_vault_twice_raises(self):
        vault.create_vault(self.vault_file, "master123")
        with self.assertRaises(vault.VaultError):
            vault.create_vault(self.vault_file, "master123")

    def test_vault_file_never_contains_plaintext_master_password(self):
        vault.create_vault(self.vault_file, "super-secret-master-pw")
        raw_content = self.vault_file.read_text()
        self.assertNotIn("super-secret-master-pw", raw_content)

    def test_unlock_with_correct_password_succeeds(self):
        vault.create_vault(self.vault_file, "master123")
        fernet, data = vault.unlock(self.vault_file, "master123")
        self.assertIsNotNone(fernet)
        self.assertEqual(data["entries"], [])

    def test_unlock_with_wrong_password_raises(self):
        vault.create_vault(self.vault_file, "master123")
        with self.assertRaises(vault.VaultError):
            vault.unlock(self.vault_file, "wrong-password")

    def test_unlock_missing_vault_raises(self):
        with self.assertRaises(vault.VaultError):
            vault.unlock(self.vault_file, "anything")


class TestEntryCRUD(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.vault_file = self.tmp_dir / "vault.json"
        vault.create_vault(self.vault_file, "master123")
        self.fernet, self.data = vault.unlock(self.vault_file, "master123")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_add_and_get_entry_roundtrips_correctly(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "correct-horse-battery-staple")
        entry = vault.get_entry(self.fernet, self.data, "Gmail")
        self.assertEqual(entry["password"], "correct-horse-battery-staple")
        self.assertEqual(entry["username"], "me@gmail.com")

    def test_stored_password_is_encrypted_on_disk(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "correct-horse-battery-staple")
        raw_content = self.vault_file.read_text()
        self.assertNotIn("correct-horse-battery-staple", raw_content)

    def test_get_entry_is_case_insensitive(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "pw123")
        entry = vault.get_entry(self.fernet, self.data, "gmail")
        self.assertEqual(entry["service"], "Gmail")

    def test_get_nonexistent_entry_raises(self):
        with self.assertRaises(vault.VaultError):
            vault.get_entry(self.fernet, self.data, "DoesNotExist")

    def test_adding_same_service_twice_updates_not_duplicates(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "old-password")
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "new-password")
        self.assertEqual(len(self.data["entries"]), 1)
        entry = vault.get_entry(self.fernet, self.data, "Gmail")
        self.assertEqual(entry["password"], "new-password")

    def test_list_entries_never_exposes_password(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "secretpw")
        entries = vault.list_entries(self.data)
        self.assertNotIn("password", entries[0])
        self.assertNotIn("encrypted_password", entries[0])

    def test_delete_entry_removes_it(self):
        vault.add_entry(self.vault_file, self.fernet, self.data,
                         "Gmail", "me@gmail.com", "pw")
        vault.delete_entry(self.vault_file, self.data, "Gmail")
        self.assertEqual(vault.list_entries(self.data), [])

    def test_delete_nonexistent_entry_raises(self):
        with self.assertRaises(vault.VaultError):
            vault.delete_entry(self.vault_file, self.data, "DoesNotExist")


class TestPasswordGenerator(unittest.TestCase):
    def test_default_length_is_16(self):
        pw = generate_password()
        self.assertEqual(len(pw), 16)

    def test_custom_length_respected(self):
        pw = generate_password(length=24)
        self.assertEqual(len(pw), 24)

    def test_too_short_length_raises(self):
        with self.assertRaises(ValueError):
            generate_password(length=2)

    def test_contains_upper_lower_and_digit(self):
        pw = generate_password(length=20)
        self.assertTrue(any(c.islower() for c in pw))
        self.assertTrue(any(c.isupper() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))

    def test_no_symbols_flag_excludes_symbols(self):
        pw = generate_password(length=30, use_symbols=False)
        allowed = string.ascii_letters + string.digits
        self.assertTrue(all(c in allowed for c in pw))

    def test_generated_passwords_are_not_identical(self):
        pw1 = generate_password()
        pw2 = generate_password()
        self.assertNotEqual(pw1, pw2)


if __name__ == "__main__":
    unittest.main()
