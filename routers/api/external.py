from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db

from config.settings import settings
from security.auth import get_current_user
from services.google import build_google_flow, Flow

from models.user import UserRead
from models.oauth import OAuth, OAuthProvider


router = APIRouter(
    prefix="/external",
    tags=["Link External Accounts"],
)


# Links a Gmail account to a user
@router.post("/gmail", status_code=201, name="link_external_gmail")
async def link_external_gmail(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):

    current_redirect_uri = str(request.url_for("gmail_callback"))
    if current_redirect_uri not in settings.GOOGLE_REDIRECT_URIS:
        raise HTTPException(status_code=500, detail=f"Redirect URI not allowed: {current_redirect_uri}")
    
    flow: Flow = build_google_flow(current_redirect_uri)
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
    )

    # Store OAuth temp record
    oauth_state = OAuth(
        state_token=state,
        user_id=current_user.id,
        provider=OAuthProvider.GMAIL,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db.add(oauth_state)
    await db.commit()

    # Return to frontend (no HATEOAS since its a specific redirect)
    return JSONResponse(
        content={ 
            "user_id": current_user.id,
            "auth_url": authorization_url,
            "provider": OAuthProvider.GMAIL,
        }
    )