from fastapi import APIRouter, HTTPException, Query, Path, Request, Response
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel

from utils.service_client import classification_client
from utils.foreign_key_validator import ForeignKeyValidator
from utils.parallel_executor import execute_parallel
from utils.response_handler import forward_request_headers, handle_service_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Health Endpoints
# =============================================================================

@router.get("/health")
async def get_health(
    request: Request,
    response: Response,
    echo: Optional[str] = Query(None)
):
    """Health check endpoint - delegates to classification service"""
    params = {"echo": echo} if echo else None
    headers = forward_request_headers(request)
    service_response = await classification_client.get("/health", params=params, headers=headers)
    return handle_service_response(service_response, response)


@router.get("/health/{path_echo}")
async def get_health_with_path(
    request: Request,
    response: Response,
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to classification service"""
    params = {"echo": echo} if echo else None
    headers = forward_request_headers(request)
    service_response = await classification_client.get(f"/health/{path_echo}", params=params, headers=headers)
    return handle_service_response(service_response, response)


# =============================================================================
# Messages Endpoints
# =============================================================================

@router.post("/messages")
async def create_message(
    request: Request,
    response: Response,
    message_data: dict
):
    """Create message - delegates to classification service"""
    service_response = await classification_client.post("/messages", json_data=message_data)
    return handle_service_response(service_response, response, is_post=True)


@router.get("/messages")
async def list_messages(
    request: Request,
    response: Response,
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
    
    headers = forward_request_headers(request)
    service_response = await classification_client.get("/messages", params=params, headers=headers)
    return handle_service_response(service_response, response)


@router.get("/messages/{message_id}")
async def get_message(
    request: Request,
    response: Response,
    message_id: UUID = Path(...)
):
    """Get specific message - delegates to classification service"""
    headers = forward_request_headers(request)
    service_response = await classification_client.get(f"/messages/{message_id}", headers=headers)
    return handle_service_response(service_response, response)


# =============================================================================
# Classifications Endpoints
# =============================================================================

@router.post("/classifications")
async def classify_messages(
    request: Request,
    response: Response,
    classification_request: dict
):
    """Classify messages - delegates to classification service (async operation)"""
    # Validate that all message IDs exist
    if "message_ids" in classification_request:
        # Could add validation here if needed
        pass
    
    service_response = await classification_client.post(
        "/classifications",
        json_data=classification_request
    )
    return handle_service_response(service_response, response, is_async=True)


@router.get("/classifications")
async def list_classifications(
    request: Request,
    response: Response,
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
    
    headers = forward_request_headers(request)
    service_response = await classification_client.get("/classifications", params=params, headers=headers)
    return handle_service_response(service_response, response)


@router.get("/classifications/{classification_id}")
async def get_classification(
    request: Request,
    response: Response,
    classification_id: UUID = Path(...)
):
    """Get specific classification - delegates to classification service"""
    headers = forward_request_headers(request)
    service_response = await classification_client.get(f"/classifications/{classification_id}", headers=headers)
    return handle_service_response(service_response, response)


@router.put("/classifications/{classification_id}")
async def update_classification(
    request: Request,
    response: Response,
    classification_id: UUID = Path(...),
    classification_update: dict = None
):
    """Update classification - delegates to classification service"""
    service_response = await classification_client.put(
        f"/classifications/{classification_id}",
        json_data=classification_update
    )
    return handle_service_response(service_response, response)


@router.delete("/classifications/{classification_id}")
async def delete_classification(
    request: Request,
    response: Response,
    classification_id: UUID = Path(...)
):
    """Delete classification - delegates to classification service"""
    service_response = await classification_client.delete(f"/classifications/{classification_id}")
    return handle_service_response(service_response, response)


# =============================================================================
# Briefs Endpoints
# =============================================================================

@router.post("/briefs")
async def create_brief(
    request: Request,
    response: Response,
    brief_request: dict
):
    """Create brief - delegates to classification service"""
    service_response = await classification_client.post("/briefs", json_data=brief_request)
    return handle_service_response(service_response, response, is_post=True)


@router.get("/briefs")
async def list_briefs(
    request: Request,
    response: Response,
    user_id: Optional[UUID] = None,
    brief_date: Optional[date] = None
):
    """List briefs - delegates to classification service"""
    params = {}
    if user_id:
        params["user_id"] = str(user_id)
    if brief_date:
        params["brief_date"] = brief_date.isoformat()
    
    headers = forward_request_headers(request)
    service_response = await classification_client.get("/briefs", params=params, headers=headers)
    return handle_service_response(service_response, response)


@router.get("/briefs/{brief_id}")
async def get_brief(
    request: Request,
    response: Response,
    brief_id: UUID = Path(...)
):
    """Get specific brief - delegates to classification service"""
    headers = forward_request_headers(request)
    service_response = await classification_client.get(f"/briefs/{brief_id}", headers=headers)
    return handle_service_response(service_response, response)


@router.delete("/briefs/{brief_id}")
async def delete_brief(
    request: Request,
    response: Response,
    brief_id: UUID = Path(...)
):
    """Delete brief - delegates to classification service"""
    service_response = await classification_client.delete(f"/briefs/{brief_id}")
    return handle_service_response(service_response, response)


# =============================================================================
# Tasks Endpoints (Classification Service)
# =============================================================================

@router.get("/tasks")
async def get_tasks(
    request: Request,
    response: Response,
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
    
    headers = forward_request_headers(request)
    service_response = await classification_client.get("/tasks", params=params, headers=headers)
    return handle_service_response(service_response, response)


@router.get("/tasks/{task_id}")
async def get_task(
    request: Request,
    response: Response,
    task_id: UUID = Path(...)
):
    """Get specific task - delegates to classification service"""
    headers = forward_request_headers(request)
    service_response = await classification_client.get(f"/tasks/{task_id}", headers=headers)
    return handle_service_response(service_response, response)


@router.post("/tasks")
async def create_task(
    request: Request,
    response: Response,
    task_data: dict
):
    """Create task - delegates to classification service"""
    service_response = await classification_client.post("/tasks", json_data=task_data)
    return handle_service_response(service_response, response, is_post=True)


@router.put("/tasks/{task_id}")
async def update_task(
    request: Request,
    response: Response,
    task_id: UUID = Path(...),
    task_update: dict = None
):
    """Update task - delegates to classification service"""
    service_response = await classification_client.put(
        f"/tasks/{task_id}",
        json_data=task_update
    )
    return handle_service_response(service_response, response)


@router.delete("/tasks/{task_id}")
async def delete_task(
    request: Request,
    response: Response,
    task_id: UUID = Path(...)
):
    """Delete task - delegates to classification service"""
    service_response = await classification_client.delete(f"/tasks/{task_id}")
    return handle_service_response(service_response, response)


@router.post("/tasks/generate")
async def generate_tasks(
    request: Request,
    response: Response,
    task_generation_request: dict
):
    """Generate tasks from classifications - delegates to classification service (async operation)"""
    # Validate that all classification IDs exist
    if "classification_ids" in task_generation_request:
        classification_ids = task_generation_request["classification_ids"]
        # Could add parallel validation here
        pass
    
    service_response = await classification_client.post(
        "/tasks/generate",
        json_data=task_generation_request
    )
    return handle_service_response(service_response, response, is_async=True)

