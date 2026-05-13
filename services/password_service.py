import hashlib
import hmac
import os
from typing import Tuple

# Stored format for salted hashes:
#   pbkdf2$<iterations>$<salt_hex>$<hash_hex>
_PBKDF2_PREFIX = "pbkdf2"
_DEFAULT_ITERATIONS = 200_000
_SALT_BYTES = 16
_HASH_BYTES = 32


def hash_password_pbkdf2(password: str, *, iterations: int = _DEFAULT_ITERATIONS) -> str:
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=_HASH_BYTES,
    )
    return f"{_PBKDF2_PREFIX}${iterations}${salt.hex()}${dk.hex()}"


def _verify_pbkdf2(stored: str, password: str) -> bool:
    try:
        _, iter_s, salt_hex, hash_hex = stored.split("$", 3)
        iterations = int(iter_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected),
    )
    return hmac.compare_digest(dk, expected)


def _verify_legacy_sha256(stored: str, password: str) -> bool:
    # Legacy: unsalted SHA-256 hex digest
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored)


def verify_password(stored_hash: str, password: str) -> Tuple[bool, bool]:
    """
    Returns:
      (is_valid, needs_rehash)

    needs_rehash is True for legacy SHA-256 or old PBKDF2 iteration values.
    """
    if not stored_hash:
        return False, False

    if stored_hash.startswith(f"{_PBKDF2_PREFIX}$"):
        ok = _verify_pbkdf2(stored_hash, password)
        # If valid but iterations differ from default, ask for rehash.
        needs_rehash = False
        try:
            _, iter_s, _, _ = stored_hash.split("$", 3)
            needs_rehash = int(iter_s) != _DEFAULT_ITERATIONS
        except Exception:
            needs_rehash = False
        return ok, needs_rehash

    # Legacy unsalted SHA-256 hexdigest
    ok = _verify_legacy_sha256(stored_hash, password)
    return ok, ok  # if valid legacy, we should rehash after login


def needs_pbkdf2_rehash(stored_hash: str) -> bool:
    return stored_hash and not stored_hash.startswith(f"{_PBKDF2_PREFIX}$")
