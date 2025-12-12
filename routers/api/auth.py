from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

from utils.database import get_db
from models.user import User, UserRead, UserLoginCredentials
from models.oauth import OAuthRedirectURL, OAuth, OAuthProvider

from config.settings import settings
from security.auth import get_current_user
from services.google import build_google_flow, Flow
from fastapi import Response, Cookie, status
from security.auth import issue_tokens_and_set_cookies, hash_refresh_token
from security.password import hash_password, verify_password


router = APIRouter(
    prefix="/auth",
    tags=["Internal User Auth"],
)

# -----------------------------------------------------------------------------
# POST Endpoints
# -----------------------------------------------------------------------------

# Create new user and Login via Google OAuth Flow
@router.post("/login/google", response_model=OAuthRedirectURL, status_code=201, name="google_login")
async def google_login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    
    current_redirect_uri = str(request.url_for("google_login_callback"))
    normalized_uri = current_redirect_uri.replace("127.0.0.1", "localhost")
    if normalized_uri not in settings.GOOGLE_REDIRECT_URIS:
        raise HTTPException(
            status_code=500, 
            detail=f"Redirect URI not allowed: {normalized_uri}"
        )
    
    flow: Flow = build_google_flow(normalized_uri)
    authorization_url, state = flow.authorization_url()

    redirect_url = (
        request.query_params.get("redirect") or 
        request.headers.get("origin") or
        settings.DEFAULT_FRONTEND_URL
    )
    parsed = urlparse(redirect_url)

    clean_redirect_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip("/"),
        "", "", ""
    ))

    origin_only = f"{parsed.scheme}://{parsed.netloc}"

    if origin_only not in settings.ALLOWED_REDIRECT_ORIGINS:
        clean_redirect_url = settings.DEFAULT_FRONTEND_URL

    # Store OAuth temp record
    oauth_state = OAuth(
        state_token=state,
        provider=OAuthProvider.GOOGLE,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        redirect_url=clean_redirect_url
    )
    db.add(oauth_state)
    await db.commit()

    return OAuthRedirectURL(auth_url=authorization_url)


# Login user using Credentials
@router.post("/login/credentials", response_model=UserRead, status_code=200, name="credentials_login")
async def credentials_login(
    request: Request,
    response: Response,
    user_login: UserLoginCredentials,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == user_login.email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(user_login.plaintext_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    await issue_tokens_and_set_cookies(
        response=response,
        db=db,
        user=user,
    )

    return UserRead.model_validate(user)


# Refresh user access and refresh tokens
@router.post("/refresh", status_code=200, name="refresh_tokens")
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, include_in_schema=False),
):
    
    print("[refresh] cookie present:", bool(refresh_token))
    print("[refresh] cookie len:", len(refresh_token) if refresh_token else None)
    # show only a prefix/suffix of the cookie (still avoid printing full token)
    if refresh_token:
        print("[refresh] cookie head/tail:", refresh_token[:6], "...", refresh_token[-6:])

    if not refresh_token:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    print()
    hashed = hash_refresh_token(refresh_token)
    print("[refresh] computed sha256:", hashed[:12], "...", hashed[-12:])
    
    sample = await db.execute(
        select(User.id, User.hashed_refresh_token, User.refresh_token_expires_at, User.is_active)
        .order_by(User.updated_at.desc())
        .limit(5)
    )
    rows = sample.all()
    print("[refresh] recent users:")
    for uid, h, exp, active in rows:
        print("  -", uid, h[:12], "...", h[-12:], "exp:", exp, "active:", active)

    result = await db.execute(
        select(User).where(
            User.hashed_refresh_token == hashed,
            User.refresh_token_expires_at > datetime.now(timezone.utc),
            User.is_active == True,
        )
    )

    user = result.scalar_one_or_none()
    print("[refresh] user matched:", bool(user))

    if not user:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    await issue_tokens_and_set_cookies(response=response, db=db, user=user)

    return {"status": "refreshed"}


# -----------------------------------------------------------------------------
# GET Endpoints
# -----------------------------------------------------------------------------

# Get current user id
@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return { "user_id": str(current_user.id)}
