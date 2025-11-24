from fastapi import APIRouter, HTTPException, Query, Path, Request
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from utils.service_client import integrations_client
from utils.foreign_key_validator import ForeignKeyValidator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Health Endpoints
# =============================================================================

@router.get("/health")
async def get_health(echo: Optional[str] = Query(None)):
    """Health check endpoint - delegates to integrations service"""
    return await integrations_client.get("/health", params={"echo": echo} if echo else None)


@router.get("/health/{path_echo}")
async def get_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to integrations service"""
    params = {"echo": echo} if echo else None
    return await integrations_client.get(f"/health/{path_echo}", params=params)


# =============================================================================
# Connections Endpoints
# =============================================================================

@router.get("/connections")
async def list_connections(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    provider: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """List connections - delegates to integrations service"""
    params = {
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


@router.get("/connections/{connection_id}")
async def get_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Get specific connection - delegates to integrations service"""
    return await integrations_client.get(f"/connections/{connection_id}")


@router.post("/connections")
async def create_connection(
    request: Request,
    connection_data: dict
):
    """Create new connection - delegates to integrations service"""
    return await integrations_client.post("/connections", json_data=connection_data)


@router.patch("/connections/{connection_id}")
async def update_connection(
    request: Request,
    connection_id: UUID = Path(...),
    connection_update: dict = None
):
    """Update connection - delegates to integrations service"""
    return await integrations_client.patch(
        f"/connections/{connection_id}",
        json_data=connection_update
    )


@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: UUID = Path(...)):
    """Delete connection - delegates to integrations service"""
    return await integrations_client.delete(f"/connections/{connection_id}")


@router.post("/connections/{connection_id}/test")
async def test_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Test connection - delegates to integrations service"""
    return await integrations_client.post(f"/connections/{connection_id}/test")


@router.post("/connections/{connection_id}/refresh")
async def refresh_connection(
    request: Request,
    connection_id: UUID = Path(...)
):
    """Refresh connection - delegates to integrations service"""
    return await integrations_client.post(f"/connections/{connection_id}/refresh")


# =============================================================================
# Messages Endpoints
# =============================================================================

@router.get("/messages")
async def list_messages(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    thread_id: Optional[str] = None,
    label_ids: Optional[List[str]] = None,
    external_id: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    has_raw: Optional[bool] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    """List messages - delegates to integrations service"""
    params = {
        "skip": skip,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    if search:
        params["search"] = search
    if thread_id:
        params["thread_id"] = thread_id
    if label_ids:
        params["label_ids"] = label_ids
    if external_id:
        params["external_id"] = external_id
    if created_after:
        params["created_after"] = created_after.isoformat()
    if created_before:
        params["created_before"] = created_before.isoformat()
    if has_raw is not None:
        params["has_raw"] = has_raw
    
    return await integrations_client.get("/messages", params=params)


@router.get("/messages/{message_id}")
async def get_message(
    request: Request,
    message_id: UUID = Path(...)
):
    """Get specific message - delegates to integrations service"""
    return await integrations_client.get(f"/messages/{message_id}")


@router.post("/messages")
async def create_message(
    request: Request,
    message_data: dict
):
    """Create new message - delegates to integrations service"""
    # Validate foreign key relationships
    if "user_id" in message_data:
        await ForeignKeyValidator.validate_user_exists(UUID(message_data["user_id"]))
    
    return await integrations_client.post("/messages", json_data=message_data)


@router.patch("/messages/{message_id}")
async def update_message(
    request: Request,
    message_id: UUID = Path(...),
    message_update: dict = None
):
    """Update message - delegates to integrations service"""
    return await integrations_client.patch(
        f"/messages/{message_id}",
        json_data=message_update
    )


@router.delete("/messages/{message_id}")
async def delete_message(message_id: UUID = Path(...)):
    """Delete message - delegates to integrations service"""
    return await integrations_client.delete(f"/messages/{message_id}")


@router.delete("/messages")
async def bulk_delete_messages(
    message_ids: List[UUID] = Query(...)
):
    """Bulk delete messages - delegates to integrations service"""
    params = {"message_ids": [str(mid) for mid in message_ids]}
    return await integrations_client.delete("/messages", params=params)


# =============================================================================
# Syncs Endpoints
# =============================================================================

@router.get("/syncs")
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


@router.get("/syncs/{sync_id}")
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


@router.post("/syncs")
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


@router.patch("/syncs/{sync_id}")
async def update_sync(
    request: Request,
    sync_id: UUID = Path(...),
    sync_update: dict = None
):
    """Update sync - delegates to integrations service"""
    return await integrations_client.patch(
        f"/syncs/{sync_id}",
        json_data=sync_update
    )


@router.delete("/syncs/{sync_id}")
async def delete_sync(sync_id: UUID = Path(...)):
    """Delete sync - delegates to integrations service"""
    return await integrations_client.delete(f"/syncs/{sync_id}")

