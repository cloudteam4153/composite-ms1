from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Dict, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel

from utils.service_client import classification_client
from utils.foreign_key_validator import ForeignKeyValidator
from utils.parallel_executor import execute_parallel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/classification",
    tags=["Classification"]
)



# =============================================================================
# Classifications Endpoints
# =============================================================================

@router.post("/")
async def classify_messages(classification_request: dict, user_id: Optional[str] = None):
    """Classify messages - delegates to classification service"""
    # Validate that all message IDs exist
    if "message_ids" in classification_request:
        # Could add validation here if needed
        pass
    
    # Add user_id to the request if provided
    if user_id:
        classification_request["user_id"] = user_id
    
    return await classification_client.post(
        "/classifications",
        json_data=classification_request
    )


@router.get("/")
async def list_classifications(
    label: Optional[str] = None,
    min_priority: Optional[int] = None,
    max_priority: Optional[int] = None,
    msg_id: Optional[str] = None,
    user_id: Optional[str] = None,
    cls_id: Optional[str] = None,
):
    """List classifications - delegates to classification service"""
    params = {}

    if label:
        params["label"] = label
    if min_priority is not None:
        params["min_priority"] = min_priority
    if max_priority is not None:
        params["max_priority"] = max_priority
    if msg_id:
        params["msg_id"] = msg_id
    if user_id:
        params["user_id"] = user_id
    if cls_id:
        params["cls_id"] = cls_id

    return await classification_client.get("/classifications", params=params)



@router.get("/{classification_id}")
async def get_classification(classification_id: UUID = Path(...)):
    """Get specific classification - delegates to classification service"""
    return await classification_client.get(f"/classifications/{classification_id}")


@router.put("/{classification_id}")
async def update_classification(
    classification_id: UUID = Path(...),
    classification_update: Dict | None = None
):
    """Update classification - delegates to classification service"""
    return await classification_client.put(
        f"/classifications/{classification_id}",
        json_data=classification_update
    )


@router.delete("/{classification_id}")
async def delete_classification(classification_id: UUID = Path(...)):
    """Delete classification - delegates to classification service"""
    return await classification_client.delete(f"/classifications/{classification_id}")



