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
    prefix="/briefs",
    tags=["Briefs"]
)



# =============================================================================
# Briefs Endpoints
# =============================================================================

@router.post("/")
async def create_brief(brief_request: dict):
    """Create brief - delegates to classification service"""
    return await classification_client.post("/briefs", json_data=brief_request)


@router.get("/")
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


@router.get("/{brief_id}")
async def get_brief(brief_id: UUID = Path(...)):
    """Get specific brief - delegates to classification service"""
    return await classification_client.get(f"/briefs/{brief_id}")


@router.delete("/{brief_id}")
async def delete_brief(brief_id: UUID = Path(...)):
    """Delete brief - delegates to classification service"""
    return await classification_client.delete(f"/briefs/{brief_id}")
