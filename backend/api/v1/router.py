"""
ARTAC API v1 Router
Main API router for all v1 endpoints
"""

from fastapi import APIRouter
from api.v1.endpoints import agents, tasks, system, demo, voice

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(demo.router, tags=["organization"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])