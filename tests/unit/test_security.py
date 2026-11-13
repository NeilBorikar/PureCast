"""Unit tests for security utilities: Argon2, JWT, token rotation, and API keys."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from purecast.core.errors import AuthenticationError
from purecast.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    hash_token,
    verify_api_key,
    verify_password,
)


@pytest.mark.unit
def test_argon2_password_hashing() -> None:
    """Validate Argon2id hashing and verification."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


@pytest.mark.unit
def test_jwt_access_token_creation_and_decoding() -> None:
    """Validate JWT access token lifecycle."""
    subject_id = str(uuid4())
    tenant_id = str(uuid4())
    role = "TENANT_ADMIN"

    token = create_access_token(
        subject=subject_id,
        tenant_id=tenant_id,
        role=role,
        extra_claims={"org_tier": "ENTERPRISE"},
    )
    payload = decode_token(token)

    assert payload["sub"] == subject_id
    assert payload["tenant_id"] == tenant_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert payload["org_tier"] == "ENTERPRISE"
    assert "exp" in payload
    assert "jti" in payload


@pytest.mark.unit
def test_jwt_expired_token_raises_error() -> None:
    """Validate that expired tokens raise AuthenticationError."""
    token = create_access_token(
        subject=str(uuid4()),
        tenant_id=str(uuid4()),
        role="HOUSEHOLD_OWNER",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    with pytest.raises(AuthenticationError, match="Token has expired"):
        decode_token(token)


@pytest.mark.unit
def test_jwt_tampered_token_raises_error() -> None:
    """Validate that tampered tokens raise AuthenticationError."""
    token = create_access_token(
        subject=str(uuid4()),
        tenant_id=str(uuid4()),
        role="HOUSEHOLD_OWNER",
    )
    tampered_token = token[:-5] + "XXXXX"

    with pytest.raises(AuthenticationError):
        decode_token(tampered_token)


@pytest.mark.unit
def test_jwt_refresh_token_generation() -> None:
    """Validate JWT refresh token format and unique JTI."""
    subject_id = str(uuid4())
    tenant_id = str(uuid4())

    raw_token_1, jti_1, exp_1 = create_refresh_token(subject_id, tenant_id)
    raw_token_2, jti_2, _ = create_refresh_token(subject_id, tenant_id)

    assert jti_1 != jti_2
    assert raw_token_1 != raw_token_2
    assert exp_1 > datetime.now(UTC)

    payload = decode_token(raw_token_1)
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti_1
    assert payload["sub"] == subject_id


@pytest.mark.unit
def test_token_hash_reproducibility() -> None:
    """Validate SHA-256 token hashing."""
    token = "sample_test_token_string"
    hash1 = hash_token(token)
    hash2 = hash_token(token)

    assert hash1 == hash2
    assert len(hash1) == 64


@pytest.mark.unit
def test_api_key_generation_and_verification() -> None:
    """Validate API key generation, prefixing, hashing, and verification."""
    raw_key, key_hash, prefix = generate_api_key(prefix="pc_test_")

    assert raw_key.startswith("pc_test_")
    assert prefix == "pc_test_"
    assert len(key_hash) == 64
    assert hash_api_key(raw_key) == key_hash
    assert verify_api_key(raw_key, key_hash) is True
    assert verify_api_key("pc_test_invalidkey", key_hash) is False
