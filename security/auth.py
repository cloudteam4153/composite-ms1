from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response, Request, Depends, Cookie, status
from fastapi.exceptions import HTTPException
from uuid import UUID

from config.settings import settings
from models.user import User
from utils.database import get_db
from sqlalchemy import select

from security.jwt import create_JWT_access_token, get_user_id_from_token
from security.hash import create_refresh_token, hash_refresh_token, verify_refresh_token


async def get_current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
 
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    # -------------------------------------------------
    # 1) Try access token first
    # -------------------------------------------------
    if access_token:
        try:
            user_id = get_user_id_from_token(access_token) 
            user = await db.get(User, user_id)

            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            # Access token is valid and user is active
            return user

        except HTTPException:
            pass

    # -------------------------------------------------
    # 2) Fallback: use refresh token
    # -------------------------------------------------
    if refresh_token:
        # Hash the incoming refresh token and look up the user by hash
        hashed = hash_refresh_token(refresh_token)

        stmt = select(User).where(
            User.hashed_refresh_token == hashed,
            User.refresh_token_expires_at > datetime.now(timezone.utc),
            User.is_active == True,
        )
        result = await db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if not user or not user.is_active:
            response.delete_cookie("access_token", path="/")
            response.delete_cookie("refresh_token", path="/")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        return user

    # No usable tokens
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


# -----------------------------------------------------------------------------
# Main Token Generation Flow
# -----------------------------------------------------------------------------
async def issue_tokens_and_set_cookies(
    *,
    response: Response,
    db: AsyncSession,
    user: User,
) -> tuple[str, str]:

    # 1) Create tokens
    access_token = create_JWT_access_token(user_id=user.id)
    refresh_token = create_refresh_token()

    # 2) Persist refresh token (hashed) + expiry
    user.hashed_refresh_token = hash_refresh_token(refresh_token)
    user.refresh_token_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_LIFESPAN_DAYS)
    )
    user.updated_at = datetime.now(timezone.utc)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 3) Set cookies
    is_prod = settings.ENVIRONMENT == "production"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        path="/",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        path="/",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_LIFESPAN_DAYS,
    )


    return access_token, refresh_token