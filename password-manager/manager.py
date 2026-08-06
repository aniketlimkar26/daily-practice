"""
Password Manager CLI
----------------------
A local, encrypted password manager. All entries are encrypted with a
key derived from your master password — the master password itself is
never stored, and is never accepted as a command-line argument (that
would leak it into shell history / process lists). It's always entered
via a hidden prompt.

Usage:
    python manager.py init
    python manager.py add --service Gmail --username me@gmail.com
    python manager.py add --service Gmail --username me@gmail.com --generate --length 20
    python manager.py list
    python manager.py get --service Gmail
    python manager.py delete --service Gmail
    python manager.py generate --length 20 --no-symbols

Author: (your name) - Python Basics Project 4
"""

import argparse
import getpass
import sys
from pathlib import Path

import vault
from generator import generate_password

VAULT_FILE_NAME = "vault.json"


def prompt_master_password(confirm: bool = False) -> str:
    password = getpass.getpass("Master password: ")
    if confirm:
        again = getpass.getpass("Confirm master password: ")
        if password != again:
            print("Error: passwords do not match.", file=sys.stderr)
            sys.exit(1)
    return password


def cmd_init(vault_file: Path) -> None:
    if vault.vault_exists(vault_file):
        print(f"Error: a vault already exists at {vault_file}", file=sys.stderr)
        sys.exit(1)
    print("Creating a new vault. Choose a strong master password — "
          "if you forget it, your data CANNOT be recovered.")
    password = prompt_master_password(confirm=True)
    vault.create_vault(vault_file, password)
    print(f"Vault created at {vault_file}")


def cmd_add(vault_file: Path, service: str, username: str,
            use_generate: bool, length: int, no_symbols: bool) -> None:
    master_password = prompt_master_password()
    try:
        fernet, data = vault.unlock(vault_file, master_password)
    except vault.VaultError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_generate:
        entry_password = generate_password(length=length, use_symbols=not no_symbols)
        print(f"Generated password: {entry_password}")
    else:
        entry_password = getpass.getpass("Password to store: ")

    vault.add_entry(vault_file, fernet, data, service, username, entry_password)
    print(f"Saved entry for '{service}'.")


def cmd_list(vault_file: Path) -> None:
    master_password = prompt_master_password()
    try:
        _, data = vault.unlock(vault_file, master_password)
    except vault.VaultError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    entries = vault.list_entries(data)
    if not entries:
        print("Vault is empty.")
        return
    print(f"{'Service':<20}Username")
    print("-" * 45)
    for e in entries:
        print(f"{e['service']:<20}{e['username']}")


def cmd_get(vault_file: Path, service: str) -> None:
    master_password = prompt_master_password()
    try:
        fernet, data = vault.unlock(vault_file, master_password)
        entry = vault.get_entry(fernet, data, service)
    except vault.VaultError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Service:  {entry['service']}")
    print(f"Username: {entry['username']}")
    print(f"Password: {entry['password']}")


def cmd_delete(vault_file: Path, service: str) -> None:
    master_password = prompt_master_password()
    try:
        _, data = vault.unlock(vault_file, master_password)
        vault.delete_entry(vault_file, data, service)
    except vault.VaultError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted entry for '{service}'.")


def cmd_generate(length: int, no_symbols: bool) -> None:
    print(generate_password(length=length, use_symbols=not no_symbols))


def parse_args():
    parser = argparse.ArgumentParser(description="Encrypted local password manager")
    parser.add_argument("--file", type=str, default=VAULT_FILE_NAME,
                         help="Path to the vault file (default: vault.json)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create a new vault")

    p_add = subparsers.add_parser("add", help="Add or update an entry")
    p_add.add_argument("--service", required=True)
    p_add.add_argument("--username", required=True)
    p_add.add_argument("--generate", action="store_true", help="Auto-generate the password")
    p_add.add_argument("--length", type=int, default=16)
    p_add.add_argument("--no-symbols", action="store_true")

    subparsers.add_parser("list", help="List saved services (no passwords shown)")

    p_get = subparsers.add_parser("get", help="Retrieve one entry (decrypts the password)")
    p_get.add_argument("--service", required=True)

    p_delete = subparsers.add_parser("delete", help="Delete an entry")
    p_delete.add_argument("--service", required=True)

    p_generate = subparsers.add_parser("generate", help="Generate a random password (no vault needed)")
    p_generate.add_argument("--length", type=int, default=16)
    p_generate.add_argument("--no-symbols", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()
    vault_file = Path(args.file)

    if args.command == "init":
        cmd_init(vault_file)
    elif args.command == "add":
        cmd_add(vault_file, args.service, args.username, args.generate, args.length, args.no_symbols)
    elif args.command == "list":
        cmd_list(vault_file)
    elif args.command == "get":
        cmd_get(vault_file, args.service)
    elif args.command == "delete":
        cmd_delete(vault_file, args.service)
    elif args.command == "generate":
        cmd_generate(args.length, args.no_symbols)


if __name__ == "__main__":
    main()
