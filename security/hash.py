from __future__ import annotations
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status, Response
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User



# -----------------------------------------------------------------------------
# Refresh Token Hashing
# -----------------------------------------------------------------------------
def create_refresh_token() -> str:
    return secrets.token_urlsafe(32) 

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def verify_refresh_token(token: str, hashed_token: str) -> bool:
    return hash_refresh_token(token) == hashed_token