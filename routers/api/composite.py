from fastapi import APIRouter, HTTPException, Query, Path, Request, Response, Cookie, Depends
from uuid import UUID
from datetime import datetime

from utils.service_client import integrations_client
import logging
from config.settings import settings
from security.auth import get_current_user

from models.user import User
from utils.service_client import (
    integrations_client,
    actions_client,
    classification_client,
)
from utils.parallel_executor import execute_parallel


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api",
    tags=["Composite API"]
)


@router.get("/dashboard", status_code=200)
async def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Composite dashboard endpoint.
    Fetches data from multiple services concurrently for the given user.
    """
    user_id_param = {"user_id": str(current_user.id)}

    # Define parallel tasks (coroutines), all filtered by user_id
    tasks = [
        integrations_client.get(
            "/connections",
            params=user_id_param,
        ),
        integrations_client.get(
            "/messages",
            params=user_id_param,
        ),
        # actions_client.get(
        #     "/tasks",
        #     params=user_id_param,
        # ),
        classification_client.get(
            "/classifications",
            params=user_id_param,
        ),
    ]

    try:
        # tasks_result,
        connections_result, messages_result,  classifications_result = (
            await execute_parallel(tasks)
        )

        return {
            "status": "success",
            "user_id": str(current_user.id),
            "connections": connections_result,
            "messages": messages_result,
            # "tasks": tasks_result,
            "classifications": classifications_result,
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard data: {str(e)}",
        )
