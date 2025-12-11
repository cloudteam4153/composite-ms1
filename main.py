from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any 

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers.api import (
    composite, auth, external, callback
)
from routers.api.resources import (
    actions,
    classifications,
    briefs,
    syncs,
    messages,
    connections,
    health
)

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

# -----------------------------------------------------------------------------
# API Router
# -----------------------------------------------------------------------------

# Composite logic
app.include_router(composite.router)
app.include_router(callback.router)
app.include_router(auth.router)
app.include_router(external.router)

# From Actions Service
app.include_router(actions.router)

# From Classifications Service
app.include_router(classifications.router)
app.include_router(briefs.router)

# From Integrations Service
app.include_router(syncs.router)
app.include_router(messages.router)
app.include_router(connections.router)

# Services health
app.include_router(health.router)

# -----------------------------------------------------------------------------
# ROOT 
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Health 
# -----------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint - checks composite service and all atomic services"""
    composite_health: Dict[str, Any] = {
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

# -----------------------------------------------------------------------------
# MAIN 
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
