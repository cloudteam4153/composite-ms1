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
    prefix="/syncs", 
    tags=["Syncs"]
)



# =============================================================================
# Syncs Endpoints
# =============================================================================

@router.get("/")
async def list_syncs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    sync_type: Optional[str] = None,
    connection_id: Optional[UUID] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    """List syncs - delegates to integrations service"""
    params = {
        "skip": skip,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    if status:
        params["status"] = status
    if sync_type:
        params["sync_type"] = sync_type
    if connection_id:
        params["connection_id"] = str(connection_id)
    if created_after:
        params["created_after"] = created_after.isoformat()
    if created_before:
        params["created_before"] = created_before.isoformat()
    
    return await integrations_client.get("/syncs", params=params)


@router.get("/{sync_id}")
async def get_sync(
    request: Request,
    sync_id: UUID = Path(...)
):
    """Get specific sync - delegates to integrations service"""
    return await integrations_client.get(f"/syncs/{sync_id}")


@router.get("/syncs/{sync_id}/status")
async def get_sync_status(
    request: Request,
    sync_id: UUID = Path(...)
):
    """Get sync status - delegates to integrations service"""
    return await integrations_client.get(f"/syncs/{sync_id}/status")


@router.post("/")
async def create_sync(
    request: Request,
    sync_data: dict
):
    """Create new sync - delegates to integrations service"""
    # Validate foreign key relationships
    if "connection_id" in sync_data and "user_id" in sync_data:
        await ForeignKeyValidator.validate_connection_exists(
            UUID(sync_data["connection_id"]),
            UUID(sync_data["user_id"])
        )
    
    return await integrations_client.post("/syncs", json_data=sync_data)


@router.patch("/{sync_id}")
async def update_sync(
    request: Request,
    sync_id: UUID = Path(...),
    sync_update: Dict | None = None
):
    """Update sync - delegates to integrations service"""
    return await integrations_client.patch(
        f"/syncs/{sync_id}",
        json_data=sync_update
    )


@router.delete("/{sync_id}")
async def delete_sync(sync_id: UUID = Path(...)):
    """Delete sync - delegates to integrations service"""
    return await integrations_client.delete(f"/syncs/{sync_id}")

