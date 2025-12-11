from __future__ import annotations
from fastapi import status
from fastapi.exceptions import HTTPException
from typing import Optional
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from config.settings import settings


# -----------------------------------------------------------------------------
# Access Token Functions (JWT)
# -----------------------------------------------------------------------------
def create_JWT_access_token(
        user_id: UUID, 
        expires_delta: Optional[timedelta] = None
) -> str:

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "exp": expire,         # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
        "type": "access"       # Token type
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_JWT_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )


def get_user_id_from_token(token: str) -> UUID:

    payload = decode_JWT_access_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
