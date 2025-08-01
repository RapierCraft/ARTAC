"""
ARTAC API v1 Router
Main API router for all v1 endpoints
"""

from fastapi import APIRouter
from api.v1.endpoints import agents, tasks, system, demo, voice, communication, inter_agent_communication, organizational_hierarchy, auto_scaling_hr, claude_auth, collaboration, ceo

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(demo.router, tags=["organization"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(communication.router, prefix="/communication", tags=["communication"])
api_router.include_router(inter_agent_communication.router, prefix="/inter-agent", tags=["inter-agent-communication"])
api_router.include_router(organizational_hierarchy.router, prefix="/hierarchy", tags=["organizational-hierarchy"])
api_router.include_router(auto_scaling_hr.router, prefix="/ahr", tags=["auto-scaling-hr"])
api_router.include_router(claude_auth.router, tags=["claude-auth"])
api_router.include_router(collaboration.router, prefix="/collaboration", tags=["multi-agent-collaboration"])
api_router.include_router(ceo.router, prefix="/ceo", tags=["ceo"])