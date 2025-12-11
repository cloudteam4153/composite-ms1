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
    prefix="/messages", 
    tags=["Messages"]
)



# =============================================================================
# Messages Endpoints
# =============================================================================

@router.get("/",status_code=200,name="composite_list_messages",)
async def composite_list_messages(
    request: Request,

    # Core filters
    user_id: Optional[UUID] = Query(None),
    external_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    label_ids: Optional[List[str]] = Query(None),

    # Text fields
    from_address: Optional[str] = Query(None),
    to_address: Optional[str] = Query(None),
    cc_address: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    body: Optional[str] = Query(None),
    snippet: Optional[str] = Query(None),

    # General search
    search: Optional[str] = Query(None),

    # Dates
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),

    # Sorting
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),

    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Composite proxy: forwards ALL message filtering params to Integrations-Service.
    """

    params = {
        "skip": skip,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    # Core filters
    if user_id is not None:
        params["user_id"] = str(user_id)

    if external_id is not None:
        params["external_id"] = external_id

    if thread_id is not None:
        params["thread_id"] = thread_id

    if label_ids is not None:
        params["label_ids"] = label_ids  # httpx encodes as repeated params

    # Direct text-attribute filters
    if from_address is not None:
        params["from_address"] = from_address

    if to_address is not None:
        params["to_address"] = to_address

    if cc_address is not None:
        params["cc_address"] = cc_address

    if subject is not None:
        params["subject"] = subject

    if body is not None:
        params["body"] = body

    if snippet is not None:
        params["snippet"] = snippet

    # free-text search
    if search is not None:
        params["search"] = search

    # Date filters
    if created_after is not None:
        params["created_after"] = created_after.isoformat()

    if created_before is not None:
        params["created_before"] = created_before.isoformat()

    # Forward auth header
    headers = {}
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth

    # Call Integrations-Service
    data = await integrations_client.get(
        endpoint="/messages",
        params=params,
        headers=headers,
    )

    return data


@router.post("/",status_code=200,name="send_message",)

@router.patch("/{message_id}")
async def update_message(
    request: Request,
    message_id: UUID = Path(...),
    message_update: Dict | None = None
):
    """Update message - delegates to integrations service"""
    return await integrations_client.patch(
        f"/messages/{message_id}",
        json_data=message_update
    )


@router.delete("/{message_id}")
async def delete_message(message_id: UUID = Path(...)):
    """Delete message - delegates to integrations service"""
    return await integrations_client.delete(f"/messages/{message_id}")


@router.delete("/")
async def bulk_delete_messages(
    message_ids: List[UUID] = Query(...)
):
    """Bulk delete messages - delegates to integrations service"""
    params = {"message_ids": [str(mid) for mid in message_ids]}
    return await integrations_client.delete("/messages", params=params)