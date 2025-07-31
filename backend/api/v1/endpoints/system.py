"""
ARTAC System API Endpoints
System status and health monitoring endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from services.agent_manager import AgentManager
from services.rag_service import rag_service

router = APIRouter()


@router.get("/status")
async def get_system_status():
    """Get overall system status and metrics"""
    try:
        # This would get the actual agent manager instance
        # For now, return mock data
        return {
            "initialized": True,
            "total_agents": 5,
            "active_agents": 4,
            "busy_agents": 1,
            "total_active_tasks": 12,
            "claude_sessions": 4
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "0.1.0-alpha"
    }