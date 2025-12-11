from fastapi import APIRouter, HTTPException, Query, Path, Request, Response, Cookie
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import httpx

# from models import connection, message, oauth, sync
from utils.service_client import integrations_client
from utils.foreign_key_validator import ForeignKeyValidator
import logging
from config.settings import settings
from models import (
    user
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/connections", 
    tags=["Connections"]
)

# =============================================================================
# Connections Endpoints
# =============================================================================

@router.get("/")
async def list_connections(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    provider: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """List connections - delegates to integrations service"""
    params: Dict[str, Any] = {
        "skip": skip,
        "limit": limit
    }
    if provider:
        params["provider"] = provider
    if status:
        params["status"] = status
    if is_active is not None:
        params["is_active"] = is_active
    
    return await integrations_client.get("/connections", params=params)


@router.get("/{connection_id}")
async def get_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Get specific connection - delegates to integrations service"""
    return await integrations_client.get(f"/connections/{connection_id}")


@router.post("/")
async def create_connection(
    request: Request,
    connection_data: dict
):
    """Create new connection - delegates to integrations service"""
    return await integrations_client.post("/connections", json_data=connection_data)


@router.patch("/{connection_id}")
async def update_connection(
    request: Request,
    connection_id: UUID = Path(...),
    connection_update: Dict | None = None
):
    """Update connection - delegates to integrations service"""
    return await integrations_client.patch(
        f"/connections/{connection_id}",
        json_data=connection_update
    )


@router.delete("/{connection_id}")
async def delete_connection(connection_id: UUID = Path(...)):
    """Delete connection - delegates to integrations service"""
    return await integrations_client.delete(f"/connections/{connection_id}")


@router.post("/{connection_id}/test")
async def test_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Test connection - delegates to integrations service"""
    return await integrations_client.post(f"/connections/{connection_id}/test")


@router.post("/{connection_id}/refresh")
async def refresh_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Refresh connection - delegates to integrations service"""
    return await integrations_client.post(f"/connections/{connection_id}/refresh")