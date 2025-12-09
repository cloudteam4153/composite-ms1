from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import integrations, actions, classification
from config.settings import settings
from utils.logging_config import setup_logging
from utils.db_coordinator import DatabaseCoordinator

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

port = int(os.environ.get("FASTAPIPORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("Starting Composite Microservice...")
    logger.info(f"Atomic services configured:")
    logger.info(f"  - Integrations Service: {settings.INTEGRATIONS_SERVICE_URL}")
    logger.info(f"  - Actions Service: {settings.ACTIONS_SERVICE_URL}")
    logger.info(f"  - Classification Service: {settings.CLASSIFICATION_SERVICE_URL}")
    yield
    logger.info("Shutting down Composite Microservice...")


app = FastAPI(
    title="Composite Microservice",
    description="Composite microservice that encapsulates and coordinates all atomic microservices",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router=integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(router=actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(router=classification.router, prefix="/api/classification", tags=["Classification"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Composite Microservice API",
        "description": "This service coordinates and delegates requests to atomic microservices",
        "version": "1.0.0",
        "endpoints": {
            "integrations": "/api/integrations",
            "actions": "/api/actions",
            "classification": "/api/classification",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - checks composite service and all atomic services"""
    composite_health = {
        "status": "healthy",
        "service": "composite-ms1",
        "version": "1.0.0"
    }
    
    # Check all atomic services in parallel
    try:
        services_health = await DatabaseCoordinator.check_all_services_health()
        composite_health["atomic_services"] = services_health
    except Exception as e:
        logger.error(f"Error checking atomic services health: {str(e)}")
        composite_health["atomic_services"] = {
            "overall_status": "error",
            "error": str(e)
        }
    
    return composite_health


@app.get("/api/composite/dashboard")
async def get_dashboard():
    """
    Composite endpoint demonstrating parallel execution.
    Fetches data from multiple services concurrently.
    """
    from utils.service_client import integrations_client, actions_client, classification_client
    from utils.parallel_executor import execute_parallel
    
    # Define parallel tasks
    tasks = [
        integrations_client.get("/health"),
        actions_client.get("/health"),
        classification_client.get("/health")
    ]
    
    # Execute in parallel
    try:
        results = await execute_parallel(tasks)
        return {
            "status": "success",
            "services": {
                "integrations": results[0],
                "actions": results[1],
                "classification": results[2]
            }
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard data: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

