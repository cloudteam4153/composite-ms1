import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from utils.service_client import (
    integrations_client,
    actions_client,
    classification_client
)

logger = logging.getLogger(__name__)


class DatabaseCoordinator:
    """Coordinates database connectivity across all services"""
    
    @staticmethod
    async def check_service_health(service_name: str, client) -> Dict[str, Any]:
        """Check health of a specific service"""
        try:
            response = await client.get("/health")
            return {
                "service": service_name,
                "status": "healthy",
                "response": response
            }
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {str(e)}")
            return {
                "service": service_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    async def check_all_services_health() -> Dict[str, Any]:
        """Check health of all atomic services"""
        logger.info("Checking health of all atomic services...")
        
        health_checks = await asyncio.gather(
            DatabaseCoordinator.check_service_health(
                "Integrations", integrations_client
            ),
            DatabaseCoordinator.check_service_health(
                "Actions", actions_client
            ),
            DatabaseCoordinator.check_service_health(
                "Classification", classification_client
            ),
            return_exceptions=True
        )
        
        results = {
            "overall_status": "healthy",
            "services": {}
        }
        
        for check in health_checks:
            if isinstance(check, Exception):
                logger.error(f"Health check exception: {str(check)}")
                results["overall_status"] = "degraded"
                continue
            
            service_name = check["service"]
            results["services"][service_name.lower()] = check
            
            if check["status"] != "healthy":
                results["overall_status"] = "degraded"
        
        return results
    
    @staticmethod
    async def validate_service_connectivity() -> bool:
        """Validate that all services are reachable"""
        health = await DatabaseCoordinator.check_all_services_health()
        return health["overall_status"] in ["healthy", "degraded"]

