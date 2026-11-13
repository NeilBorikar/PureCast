"""Security utilities: Argon2 password hashing, JWT, refresh tokens, and API keys."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import argon2
import jwt
from argon2.exceptions import VerifyMismatchError

from purecast.core.config import get_settings
from purecast.core.errors import AuthenticationError

_pwd_hasher = argon2.PasswordHasher(
    time_cost=get_settings().ARGON2_TIME_COST,
    memory_cost=get_settings().ARGON2_MEMORY_COST,
    parallelism=get_settings().ARGON2_PARALLELISM,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return _pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify an Argon2id password hash."""
    try:
        return _pwd_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token (default 15 minutes)."""
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    tenant_id: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """Create a signed JWT refresh token (default 7 days).

    Returns:
        tuple of (raw_token, jti, expire_datetime)
    """
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    jti = secrets.token_urlsafe(32)
    to_encode: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    raw_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return raw_token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError as err:
        raise AuthenticationError("Token has expired") from err
    except jwt.InvalidTokenError as err:
        raise AuthenticationError("Invalid token") from err


def hash_token(raw_token: str) -> str:
    """Hash a token for secure storage in the database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "pc_live_") -> tuple[str, str, str]:
    """Generate a high-entropy API key.

    Returns:
        tuple of (raw_api_key, key_hash, prefix)
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{random_part}"
    key_hash = hash_api_key(raw_key)
    return raw_key, key_hash, prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256 for database lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    return secrets.compare_digest(hash_api_key(raw_key), stored_hash)
