"""
ARTAC Tasks API Endpoints
Task management and monitoring endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    assigned_agent_id: str = None
    created_at: str
    updated_at: str
    completed_at: str = None


@router.get("/", response_model=List[TaskResponse])
async def get_tasks():
    """Get all tasks"""
    # Return mock data for now
    return [
        {
            "id": "1",
            "title": "Implement user authentication",
            "description": "Create secure user authentication system",
            "status": "completed",
            "priority": "high",
            "assigned_agent_id": "1",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z",
            "completed_at": "2024-01-01T01:00:00Z"
        },
        {
            "id": "2",
            "title": "Optimize database queries",
            "description": "Improve database performance",
            "status": "in_progress", 
            "priority": "medium",
            "assigned_agent_id": "2",
            "created_at": "2024-01-01T00:30:00Z",
            "updated_at": "2024-01-01T00:45:00Z"
        }
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task"""
    # Mock task retrieval
    return {
        "id": task_id,
        "title": "Sample Task",
        "description": "Sample task description",
        "status": "pending",
        "priority": "medium",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }