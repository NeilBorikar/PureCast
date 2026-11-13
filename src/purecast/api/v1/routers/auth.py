"""Authentication endpoints: register, login, refresh, logout, me."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserMeResponse,
)
from purecast.core.config import get_settings
from purecast.core.deps import get_current_user, get_db
from purecast.core.errors import AuthenticationError, ConflictError
from purecast.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import RefreshToken, Tenant, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new tenant organization and primary administrator."""
    # Check tenant slug uniqueness
    res = await session.execute(select(Tenant).filter(Tenant.slug == req.tenant_slug))
    if res.scalars().first():
        raise ConflictError(f"Tenant slug '{req.tenant_slug}' is already taken")

    # Check user email uniqueness globally or within slug
    res = await session.execute(select(User).filter(User.email == req.email))
    if res.scalars().first():
        raise ConflictError(f"User with email '{req.email}' already exists")

    tenant = Tenant(
        name=req.tenant_name,
        slug=req.tenant_slug,
        tier="FULL",
        is_active=True,
    )
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=Role.TENANT_ADMIN.value,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role,
    )
    raw_refresh, jti, exp = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
    )

    db_refresh = RefreshToken(
        tenant_id=tenant.id,
        user_id=user.id,
        jti=jti,
        token_hash=hash_token(raw_refresh),
        expires_at=exp,
        revoked=False,
    )
    session.add(db_refresh)

    await log_audit(
        session=session,
        action="user:register",
        resource_type="tenant",
        tenant_id=tenant.id,
        user_id=user.id,
        resource_id=str(tenant.id),
    )

    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with email and password, issuing access and refresh tokens."""
    res = await session.execute(select(User).filter(User.email == req.email))
    user = res.scalars().first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated")

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
    raw_refresh, jti, exp = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
    )

    db_refresh = RefreshToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        jti=jti,
        token_hash=hash_token(raw_refresh),
        expires_at=exp,
        revoked=False,
    )
    session.add(db_refresh)

    await log_audit(
        session=session,
        action="user:login",
        resource_type="user",
        tenant_id=user.tenant_id,
        user_id=user.id,
        resource_id=str(user.id),
    )

    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    req: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Rotate refresh token: revoke consumed token and issue a fresh pair."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    jti = payload.get("jti")
    res = await session.execute(select(RefreshToken).filter(RefreshToken.jti == jti))
    stored_token = res.scalars().first()

    if not stored_token:
        raise AuthenticationError("Refresh token not found")

    # Reuse detection: if token is already revoked, invalidate all user sessions
    if stored_token.revoked:
        user_tokens = await session.execute(
            select(RefreshToken).filter(RefreshToken.user_id == stored_token.user_id)
        )
        for t in user_tokens.scalars().all():
            t.revoked = True
            t.revoked_at = datetime.now(UTC)
        await session.flush()
        raise AuthenticationError("Revoked token reuse detected. All sessions invalidated.")

    token_exp = stored_token.expires_at
    if token_exp.tzinfo is None:
        token_exp = token_exp.replace(tzinfo=UTC)
    if token_exp < datetime.now(UTC):
        raise AuthenticationError("Refresh token has expired")

    user_res = await session.execute(select(User).filter(User.id == stored_token.user_id))
    user = user_res.scalars().first()
    if not user or not user.is_active:
        raise AuthenticationError("User is no longer active")

    # Issue new pair
    new_access = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
    new_refresh, new_jti, new_exp = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
    )

    new_db_token = RefreshToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        jti=new_jti,
        token_hash=hash_token(new_refresh),
        expires_at=new_exp,
        revoked=False,
    )
    session.add(new_db_token)
    await session.flush()

    # Mark old token as revoked and rotated
    stored_token.revoked = True
    stored_token.revoked_at = datetime.now(UTC)
    stored_token.replaced_by = new_db_token.id
    session.add(stored_token)

    settings = get_settings()
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    req: LogoutRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Revoke a refresh token to end the session."""
    try:
        payload = decode_token(req.refresh_token)
        jti = payload.get("jti")
        if jti:
            res = await session.execute(select(RefreshToken).filter(RefreshToken.jti == jti))
            stored_token = res.scalars().first()
            if stored_token and not stored_token.revoked:
                stored_token.revoked = True
                stored_token.revoked_at = datetime.now(UTC)
                session.add(stored_token)
    except Exception:
        pass


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserMeResponse:
    """Fetch currently authenticated user details."""
    return UserMeResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
