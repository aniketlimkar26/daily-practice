"""
generator.py — secure random password generation.

Uses the `secrets` module, NOT `random`. `random` is a pseudo-random
generator meant for simulations/games; it is predictable and NOT safe
for anything security-related. `secrets` is specifically designed for
generating tokens, passwords, and cryptographic secrets.
"""

import secrets
import string


def generate_password(length: int = 16, use_symbols: bool = True) -> str:
    if length < 4:
        raise ValueError("Password length must be at least 4.")

    letters = string.ascii_letters
    digits = string.digits
    symbols = "!@#$%^&*()-_=+[]{}"

    pool = letters + digits + (symbols if use_symbols else "")

    # Guarantee at least one of each character class for a stronger password.
    required = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(digits),
    ]
    if use_symbols:
        required.append(secrets.choice(symbols))

    remaining_length = length - len(required)
    password_chars = required + [secrets.choice(pool) for _ in range(remaining_length)]

    # Shuffle so the guaranteed characters aren't always at the start.
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)
