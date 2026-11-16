
"""Authentication utilities for creating and verifying login tokens."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv


# Load private settings from the .env file
load_dotenv()

# Read our private secret key
SECRET_KEY = os.getenv("SECRET_KEY")

# Stop the application if the secret key is missing
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from the .env file")


# Token settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: int) -> str:
    """Create a signed access token for a logged-in user."""

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def verify_access_token(token: str) -> int:
    """Verify a token and return the user's ID."""

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("Token does not contain a user ID")

        return int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise ValueError("Invalid or expired authentication token")
