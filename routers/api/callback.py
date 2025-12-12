from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
from typing import Optional, cast
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from enum import Enum as PyEnum

from google.oauth2.credentials import Credentials
from google.oauth2.id_token import verify_oauth2_token
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest

from services.google import build_google_flow, Flow
from security import token_cipher
from security.auth import issue_tokens_and_set_cookies
from config.settings import settings

from models.oauth import OAuthProvider, OAuth
from models.user import User, UserLoginMethod
from utils.service_client import integrations_client


router = APIRouter(
    prefix="/oauth/callback",
    tags=["OAuth Callbacks (Internal Use Only)"],
)


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class ConnectionStatus(PyEnum):
    """Status of an OAuth connection"""
    PENDING = "pending"      # OAuth flow initiated but not completed
    ACTIVE = "active"        # Successfully connected and tokens are valid
    EXPIRED = "expired"      # Tokens expired and refresh failed
    REVOKED = "revoked"      # User revoked access
    FAILED = "failed"        # OAuth flow failed


# Gmail Callback GET Endpoint (defined as per Google API spec; internal only)
@router.get("/google/login", status_code=200, name="google_login_callback")
async def google_login_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {error}")
    
    # Get OAuth Record
    query = select(OAuth).where(
        OAuth.state_token == state,
        OAuth.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(query)
    oauth_record = result.scalar_one_or_none()
    
    if not oauth_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token"
        )
    
    await db.delete(oauth_record)
    await db.commit()
    
    # Build Google Flow object with correct callback and Redirect URIs
    current_redirect_uri = str(request.url_for("google_login_callback"))
    current_redirect_uri = current_redirect_uri.replace("127.0.0.1", "localhost")
    
    if current_redirect_uri not in settings.GOOGLE_REDIRECT_URIS:
        raise HTTPException(status_code=500, detail=f"Redirect URI not allowed: {current_redirect_uri}")
    
    flow: Flow = build_google_flow(current_redirect_uri)

    # Exchange code for token
    try:
        flow.fetch_token(code=code)
    except GoogleAuthError as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate with Google. {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown authentication error occured. {e}")


    credentials: Credentials = cast(Credentials, flow.credentials)

    #### from here, get email, name, google account id, anything else useful and update User table
    try: 
        id_info = verify_oauth2_token(
            credentials.id_token,
            GoogleRequest(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=400, detail=f"Invalid ID token: {str(e)}")
    
    # Extract user information from the decoded token
    google_user_id = id_info.get("sub")  # Google's unique user ID
    email = id_info.get("email")
    first_name = id_info.get('given_name', '')
    last_name = id_info.get('family_name', '')

    if not google_user_id or not email:
        raise HTTPException(
            status_code=400,
            detail="Google account is missing required identity fields"
        )
    
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    
    if user:
        if user.login_method != UserLoginMethod.GOOGLE_OAUTH:
            raise HTTPException(
                status_code=409,
                detail="Email already registered with another login method."
            )
        
        if user.oauth_provider_id != google_user_id:
            raise HTTPException(
                status_code=409,
                detail="Email registered with different Google account"
            )
    else:
        # New user - create account
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            login_method=UserLoginMethod.GOOGLE_OAUTH,
            oauth_provider_id=google_user_id,
            hashed_password=None,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    

    redirect_url = oauth_record.redirect_url or settings.DEFAULT_FRONTEND_URL
    parsed = urlparse(redirect_url)
    origin_only = f"{parsed.scheme}://{parsed.netloc}"

    if origin_only not in settings.ALLOWED_REDIRECT_ORIGINS:
        redirect_url = settings.DEFAULT_FRONTEND_URL
    

    response = RedirectResponse(url=redirect_url)
    await issue_tokens_and_set_cookies(
        response=response,
        db=db,
        user=user
    )
    
    return response


# Gmail Callback GET Endpoint (defined as per Google API spec; internal only)
@router.get("/google/gmail", status_code=200, name="gmail_callback")
async def gmail_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    
    if error:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {error}")

    # Get OAuth Record
    query = select(OAuth).where(
        OAuth.state_token == state,
        OAuth.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(query)
    oauth_record = result.scalar_one_or_none()
    
    if not oauth_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token"
        )
    
    if not oauth_record.user_id:
        # This flow MUST be tied to an existing user
        raise HTTPException(
            status_code=400,
            detail="OAuth state is missing associated user",
        )
    
    # Cache user_id before deleting the state
    user_id = oauth_record.user_id

    # Immediately invalidate state (prevents replay)
    await db.delete(oauth_record)
    await db.commit()

    current_redirect_uri = str(request.url_for("gmail_callback"))
    current_redirect_uri = current_redirect_uri.replace("127.0.0.1", "localhost")
    if current_redirect_uri not in settings.GOOGLE_REDIRECT_URIS:
        raise HTTPException(
            status_code=500, 
            detail=f"Redirect URI not allowed: {current_redirect_uri}"
        )
    
    flow: Flow = build_google_flow(current_redirect_uri, gmail_scopes=True)

    try:
        flow.fetch_token(code=code)
        credentials: Credentials = cast(Credentials, flow.credentials)
    except GoogleAuthError as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate with Google. {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown authentication error occured. {e}")

    try: 
        id_info = verify_oauth2_token(
            credentials.id_token,
            GoogleRequest(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=400, detail=f"Invalid ID token: {str(e)}")
    
    # Extract user information from the decoded token
    gmail: str = id_info.get("email")

    if gmail is None:
        raise HTTPException(status_code=404, detail="Failed to get Gmail account ID.")
    try:
        access_token_encrypted = token_cipher.encrypt(str(credentials.token))
        refresh_token_encrypted = token_cipher.encrypt(str(credentials.refresh_token))
    except Exception as e:
        raise Exception(e)
    
    scopes = list(credentials.granted_scopes) if credentials.granted_scopes else []
    if credentials.expiry: # If none, assume token never expires (https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials)
        access_token_expiry = credentials.expiry

    new_conn = {
        "user_id": user_id,
        "provider": OAuthProvider(oauth_record.provider),
        "provider_account_id": gmail,
        "status": ConnectionStatus.ACTIVE,
        "scopes": scopes,
        "access_token": access_token_encrypted,
        "refresh_token": refresh_token_encrypted,
        "access_token_expiry": access_token_expiry,
        "is_active": True
        }

    resp = await integrations_client.post(
        "/connections",
        json_data=new_conn
    )

    redirect_url = oauth_record.redirect_url or settings.DEFAULT_FRONTEND_URL
    parsed = urlparse(redirect_url)
    origin_only = f"{parsed.scheme}://{parsed.netloc}"

    if origin_only not in settings.ALLOWED_REDIRECT_ORIGINS:
        redirect_url = settings.DEFAULT_FRONTEND_URL
    

    return RedirectResponse(url=redirect_url)
