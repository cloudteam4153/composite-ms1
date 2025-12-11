from fastapi import APIRouter, Query, Path
from typing import Optional

from utils.service_client import (
    integrations_client,
    actions_client, 
    classification_client
)

# =============================================================================
# General Health Checks for All Microservices
# =============================================================================

router = APIRouter(
    prefix="/health",
    tags=["Microservices Health Checks"]
)



# -----------------------------------------------------------------------------
# Integrations Service
# -----------------------------------------------------------------------------

@router.get("/integrations")
async def get_integrations_health(echo: Optional[str] = Query(None)):
    """Health check endpoint - delegates to integrations service"""
    return await integrations_client.get("/health", params={"echo": echo} if echo else None)


@router.get("/integrations/{path_echo}")
async def get_integrations_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to integrations service"""
    params = {"echo": echo} if echo else None
    return await integrations_client.get(f"/health/{path_echo}", params=params)


# -----------------------------------------------------------------------------
# Actions Service
# -----------------------------------------------------------------------------

@router.get("/actions")
async def get_actions_health():
    """Health check endpoint - delegates to actions service"""
    return await actions_client.get("/health")

@router.get("/actions/{path_echo}")
async def get_actions_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to classification service"""
    params = {"echo": echo} if echo else None
    return await actions_client.get(f"/health/{path_echo}", params=params)



# -----------------------------------------------------------------------------
# Classifications Service
# -----------------------------------------------------------------------------

@router.get("/classifications")
async def get_classifications_health(echo: Optional[str] = Query(None)):
    """Health check endpoint - delegates to classification service"""
    params = {"echo": echo} if echo else None
    return await classification_client.get("/health", params=params)


@router.get("/classifications/{path_echo}")
async def get_classifications_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None)
):
    """Health check with path echo - delegates to classification service"""
    params = {"echo": echo} if echo else None
    return await classification_client.get(f"/health/{path_echo}", params=params)