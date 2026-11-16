
"""Password security: hashing and verifying user passwords."""

import base64
import hashlib
import hmac
import secrets


# Number of times the password-hashing algorithm runs
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Convert a plain-text password into a secure password hash."""

    # unique random salt for this password
    salt = secrets.token_bytes(16)

    # Converting the password into a secure hash
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    # Encode the salt and hash so they can be stored as text
    salt_text = base64.b64encode(salt).decode("utf-8")
    hash_text = base64.b64encode(password_hash).decode("utf-8")

    return f"pbkdf2_sha256${ITERATIONS}${salt_text}${hash_text}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check whether a password matches its stored hash."""

    try:
        algorithm, iterations, salt_text, hash_text = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        if not 1 <= iterations <= 2_000_000:
            return False

        salt = base64.b64decode(salt_text, validate=True)
        original_hash = base64.b64decode(hash_text, validate=True)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(new_hash, original_hash)

    except (ValueError, TypeError, AttributeError):
        return False
