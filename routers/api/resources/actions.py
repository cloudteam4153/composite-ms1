from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from utils.service_client import actions_client
from utils.parallel_executor import execute_parallel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/actions", 
    tags=["Actions"]
)



# =============================================================================
# Tasks Endpoints
# =============================================================================

@router.get("/tasks")
async def get_tasks(
    user_id: int = Query(..., description="User ID to filter tasks"),
    status: Optional[str] = None,
    priority: Optional[int] = Query(None, ge=1, le=5)
):
    """Get tasks - delegates to actions service"""
    params: Dict[str, Any] = {"user_id": user_id}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    
    return await actions_client.get("/tasks", params=params)


@router.get("/tasks/{task_id}")
async def get_task(task_id: int = Path(...)):
    """Get specific task - delegates to actions service"""
    return await actions_client.get(f"/tasks/{task_id}")


@router.post("/tasks")
async def create_task(task_data: dict):
    """Create new task - delegates to actions service"""
    return await actions_client.post("/tasks", json_data=task_data)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int = Path(...),
    task_update: Dict | None = None
):
    """Update task - delegates to actions service"""
    return await actions_client.put(
        f"/tasks/{task_id}",
        json_data=task_update
    )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int = Path(...)):
    """Delete task - delegates to actions service"""
    return await actions_client.delete(f"/tasks/{task_id}")


# @router.post("/tasks/batch")
# async def create_tasks_from_messages(
#     messages: List[dict],
#     user_id: int = Query(...)
# ):
#     """Create tasks from messages - delegates to actions service"""
#     params = {"user_id": user_id}
#     return await actions_client.post(
#         "/tasks/batch",
#         json_data=messages,
#         params=params
#     )


# # =============================================================================
# # Todo Endpoints (Not Implemented in atomic service)
# # =============================================================================

# @router.post("/todo")
# async def create_todo():
#     """Create todo - delegates to actions service (not implemented)"""
#     return await actions_client.post("/todo")


# @router.get("/todo")
# async def get_todos():
#     """Get todos - delegates to actions service (not implemented)"""
#     return await actions_client.get("/todo")


# @router.get("/todo/{todo_id}")
# async def get_todo(todo_id: int = Path(...)):
#     """Get specific todo - delegates to actions service (not implemented)"""
#     return await actions_client.get(f"/todo/{todo_id}")


# @router.put("/todo/{todo_id}")
# async def update_todo(
#     todo_id: int = Path(...),
#     todo_update: dict = None
# ):
#     """Update todo - delegates to actions service (not implemented)"""
#     return await actions_client.put(
#         f"/todo/{todo_id}",
#         json_data=todo_update
#     )


# @router.delete("/todo/{todo_id}")
# async def delete_todo(todo_id: int = Path(...)):
#     """Delete todo - delegates to actions service (not implemented)"""
#     return await actions_client.delete(f"/todo/{todo_id}")


# # =============================================================================
# # Followup Endpoints (Not Implemented in atomic service)
# # =============================================================================

# @router.post("/followup")
# async def create_followup():
#     """Create followup - delegates to actions service (not implemented)"""
#     return await actions_client.post("/followup")


# @router.get("/followup")
# async def get_followups():
#     """Get followups - delegates to actions service (not implemented)"""
#     return await actions_client.get("/followup")


# @router.get("/followup/{followup_id}")
# async def get_followup(followup_id: int = Path(...)):
#     """Get specific followup - delegates to actions service (not implemented)"""
#     return await actions_client.get(f"/followup/{followup_id}")


# @router.put("/followup/{followup_id}")
# async def update_followup(
#     followup_id: int = Path(...),
#     followup_update: dict = None
# ):
#     """Update followup - delegates to actions service (not implemented)"""
#     return await actions_client.put(
#         f"/followup/{followup_id}",
#         json_data=followup_update
#     )


# @router.delete("/followup/{followup_id}")
# async def delete_followup(followup_id: int = Path(...)):
#     """Delete followup - delegates to actions service (not implemented)"""
#     return await actions_client.delete(f"/followup/{followup_id}")

