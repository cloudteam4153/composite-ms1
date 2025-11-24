from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel

from utils.service_client import classification_client
from utils.foreign_key_validator import ForeignKeyValidator
from utils.parallel_executor import execute_parallel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Health Endpoints
# =============================================================================

@router.get("/health")
async def get_health(echo: Optional[str] = Query(None)):
    """Health check endpoint - delegates to classification service"""
    params = {"echo": echo} if echo else None
    return await classification_client.get("/health", params=params)


@router.get("/health/{path_echo}")
async def get_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to classification service"""
    params = {"echo": echo} if echo else None
    return await classification_client.get(f"/health/{path_echo}", params=params)


# =============================================================================
# Messages Endpoints
# =============================================================================

@router.post("/messages")
async def create_message(message_data: dict):
    """Create message - delegates to classification service"""
    return await classification_client.post("/messages", json_data=message_data)


@router.get("/messages")
async def list_messages(
    channel: Optional[str] = None,
    sender: Optional[str] = None,
    limit: Optional[int] = Query(50)
):
    """List messages - delegates to classification service"""
    params = {}
    if channel:
        params["channel"] = channel
    if sender:
        params["sender"] = sender
    if limit:
        params["limit"] = limit
    
    return await classification_client.get("/messages", params=params)


@router.get("/messages/{message_id}")
async def get_message(message_id: UUID = Path(...)):
    """Get specific message - delegates to classification service"""
    return await classification_client.get(f"/messages/{message_id}")


# =============================================================================
# Classifications Endpoints
# =============================================================================

@router.post("/classifications")
async def classify_messages(classification_request: dict):
    """Classify messages - delegates to classification service"""
    # Validate that all message IDs exist
    if "message_ids" in classification_request:
        # Could add validation here if needed
        pass
    
    return await classification_client.post(
        "/classifications",
        json_data=classification_request
    )


@router.get("/classifications")
async def list_classifications(
    label: Optional[str] = None,
    min_priority: Optional[int] = None,
    max_priority: Optional[int] = None
):
    """List classifications - delegates to classification service"""
    params = {}
    if label:
        params["label"] = label
    if min_priority is not None:
        params["min_priority"] = min_priority
    if max_priority is not None:
        params["max_priority"] = max_priority
    
    return await classification_client.get("/classifications", params=params)


@router.get("/classifications/{classification_id}")
async def get_classification(classification_id: UUID = Path(...)):
    """Get specific classification - delegates to classification service"""
    return await classification_client.get(f"/classifications/{classification_id}")


@router.put("/classifications/{classification_id}")
async def update_classification(
    classification_id: UUID = Path(...),
    classification_update: dict = None
):
    """Update classification - delegates to classification service"""
    return await classification_client.put(
        f"/classifications/{classification_id}",
        json_data=classification_update
    )


@router.delete("/classifications/{classification_id}")
async def delete_classification(classification_id: UUID = Path(...)):
    """Delete classification - delegates to classification service"""
    return await classification_client.delete(f"/classifications/{classification_id}")


# =============================================================================
# Briefs Endpoints
# =============================================================================

@router.post("/briefs")
async def create_brief(brief_request: dict):
    """Create brief - delegates to classification service"""
    return await classification_client.post("/briefs", json_data=brief_request)


@router.get("/briefs")
async def list_briefs(
    user_id: Optional[UUID] = None,
    brief_date: Optional[date] = None
):
    """List briefs - delegates to classification service"""
    params = {}
    if user_id:
        params["user_id"] = str(user_id)
    if brief_date:
        params["brief_date"] = brief_date.isoformat()
    
    return await classification_client.get("/briefs", params=params)


@router.get("/briefs/{brief_id}")
async def get_brief(brief_id: UUID = Path(...)):
    """Get specific brief - delegates to classification service"""
    return await classification_client.get(f"/briefs/{brief_id}")


@router.delete("/briefs/{brief_id}")
async def delete_brief(brief_id: UUID = Path(...)):
    """Delete brief - delegates to classification service"""
    return await classification_client.delete(f"/briefs/{brief_id}")


# =============================================================================
# Tasks Endpoints (Classification Service)
# =============================================================================

@router.get("/tasks")
async def get_tasks(
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: Optional[int] = Query(50)
):
    """Get tasks - delegates to classification service"""
    params = {}
    if user_id:
        params["user_id"] = str(user_id)
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if limit:
        params["limit"] = limit
    
    return await classification_client.get("/tasks", params=params)


@router.get("/tasks/{task_id}")
async def get_task(task_id: UUID = Path(...)):
    """Get specific task - delegates to classification service"""
    return await classification_client.get(f"/tasks/{task_id}")


@router.post("/tasks")
async def create_task(task_data: dict):
    """Create task - delegates to classification service"""
    return await classification_client.post("/tasks", json_data=task_data)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: UUID = Path(...),
    task_update: dict = None
):
    """Update task - delegates to classification service"""
    return await classification_client.put(
        f"/tasks/{task_id}",
        json_data=task_update
    )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: UUID = Path(...)):
    """Delete task - delegates to classification service"""
    return await classification_client.delete(f"/tasks/{task_id}")


@router.post("/tasks/generate")
async def generate_tasks(task_generation_request: dict):
    """Generate tasks from classifications - delegates to classification service"""
    # Validate that all classification IDs exist
    if "classification_ids" in task_generation_request:
        classification_ids = task_generation_request["classification_ids"]
        # Could add parallel validation here
        pass
    
    return await classification_client.post(
        "/tasks/generate",
        json_data=task_generation_request
    )

