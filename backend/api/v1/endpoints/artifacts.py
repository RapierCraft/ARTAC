"""
ARTAC Code Artifacts API Endpoints
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from core.logging import get_logger
from services.code_artifact_manager import code_artifact_manager, ArtifactType, ArtifactStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


# Request/Response Models
class CreateArtifactRequest(BaseModel):
    project_id: str
    agent_id: str
    agent_name: str
    file_path: str
    content: str
    artifact_type: ArtifactType
    task_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = {}


class UpdateArtifactStatusRequest(BaseModel):
    status: ArtifactStatus
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class CreateSnapshotRequest(BaseModel):
    project_id: str
    snapshot_name: str
    description: str
    created_by: str
    commit_sha: str
    tags: List[str] = []


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    agent_id: str
    agent_name: str
    file_path: str
    file_name: str
    artifact_type: str
    content: str
    content_hash: str
    status: str
    version: int
    parent_version: Optional[str]
    commit_sha: Optional[str]
    task_id: Optional[str]
    description: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


@router.post("/create", response_model=Dict[str, str])
async def create_artifact(request: CreateArtifactRequest):
    """Create a new code artifact"""
    try:
        artifact_id = await code_artifact_manager.create_artifact(
            project_id=request.project_id,
            agent_id=request.agent_id,
            agent_name=request.agent_name,
            file_path=request.file_path,
            content=request.content,
            artifact_type=request.artifact_type,
            task_id=request.task_id,
            description=request.description,
            metadata=request.metadata
        )
        
        logger.log_system_event("artifact_created_via_api", {
            "artifact_id": artifact_id,
            "project_id": request.project_id,
            "agent_id": request.agent_id
        })
        
        return {"artifact_id": artifact_id, "status": "created"}
        
    except Exception as e:
        logger.log_error(e, {
            "action": "create_artifact_api",
            "project_id": request.project_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}", response_model=Dict[str, Any])
async def get_project_artifacts(
    project_id: str = Path(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type")
):
    """Get all artifacts for a project with optional filters"""
    try:
        # Get base artifacts
        artifacts = await code_artifact_manager.get_project_artifacts(project_id)
        
        # Apply filters
        if status:
            artifacts = [a for a in artifacts if a.status.value == status]
        
        if agent_id:
            artifacts = [a for a in artifacts if a.agent_id == agent_id]
        
        if artifact_type:
            artifacts = [a for a in artifacts if a.artifact_type.value == artifact_type]
        
        # Convert to response format
        artifact_responses = []
        for artifact in artifacts:
            artifact_responses.append(ArtifactResponse(
                id=artifact.id,
                project_id=artifact.project_id,
                agent_id=artifact.agent_id,
                agent_name=artifact.agent_name,
                file_path=artifact.file_path,
                file_name=artifact.file_name,
                artifact_type=artifact.artifact_type.value,
                content=artifact.content,
                content_hash=artifact.content_hash,
                status=artifact.status.value,
                version=artifact.version,
                parent_version=artifact.parent_version,
                commit_sha=artifact.commit_sha,
                task_id=artifact.task_id,
                description=artifact.description,
                metadata=artifact.metadata,
                created_at=artifact.created_at.isoformat(),
                updated_at=artifact.updated_at.isoformat(),
                reviewed_by=artifact.reviewed_by,
                review_notes=artifact.review_notes
            ))
        
        # Get file tree structure
        file_tree = await code_artifact_manager.get_project_codebase_tree(project_id)
        
        return {
            "project_id": project_id,
            "artifacts": artifact_responses,
            "file_tree": file_tree,
            "total_count": len(artifact_responses),
            "stats": {
                "by_status": {},
                "by_agent": {},
                "by_type": {}
            }
        }
        
    except Exception as e:
        logger.log_error(e, {
            "action": "get_project_artifacts_api",
            "project_id": project_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str = Path(..., description="Artifact ID")):
    """Get a specific artifact by ID"""
    try:
        artifact = await code_artifact_manager.get_artifact(artifact_id)
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return ArtifactResponse(
            id=artifact.id,
            project_id=artifact.project_id,
            agent_id=artifact.agent_id,
            agent_name=artifact.agent_name,
            file_path=artifact.file_path,
            file_name=artifact.file_name,
            artifact_type=artifact.artifact_type.value,
            content=artifact.content,
            content_hash=artifact.content_hash,
            status=artifact.status.value,
            version=artifact.version,
            parent_version=artifact.parent_version,
            commit_sha=artifact.commit_sha,
            task_id=artifact.task_id,
            description=artifact.description,
            metadata=artifact.metadata,
            created_at=artifact.created_at.isoformat(),
            updated_at=artifact.updated_at.isoformat(),
            reviewed_by=artifact.reviewed_by,
            review_notes=artifact.review_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, {
            "action": "get_artifact_api",
            "artifact_id": artifact_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{artifact_id}/content", response_model=Dict[str, str])
async def get_artifact_content(artifact_id: str = Path(..., description="Artifact ID")):
    """Get artifact content only (for large files)"""
    try:
        content = await code_artifact_manager.get_artifact_content(artifact_id)
        
        if content is None:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return {"content": content}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, {
            "action": "get_artifact_content_api",
            "artifact_id": artifact_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{artifact_id}/status", response_model=Dict[str, str])
async def update_artifact_status(
    artifact_id: str,
    request: UpdateArtifactStatusRequest
):
    """Update artifact status (approve, deploy, etc.)"""
    try:
        success = await code_artifact_manager.update_artifact_status(
            artifact_id=artifact_id,
            new_status=request.status,
            reviewed_by=request.reviewed_by,
            review_notes=request.review_notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        logger.log_system_event("artifact_status_updated_via_api", {
            "artifact_id": artifact_id,
            "new_status": request.status.value,
            "reviewed_by": request.reviewed_by
        })
        
        return {"status": "updated", "new_status": request.status.value}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, {
            "action": "update_artifact_status_api",
            "artifact_id": artifact_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_id}", response_model=Dict[str, Any])
async def get_agent_artifacts(agent_id: str = Path(..., description="Agent ID")):
    """Get all artifacts created by a specific agent"""
    try:
        artifacts = await code_artifact_manager.get_agent_artifacts(agent_id)
        
        artifact_responses = []
        for artifact in artifacts:
            artifact_responses.append(ArtifactResponse(
                id=artifact.id,
                project_id=artifact.project_id,
                agent_id=artifact.agent_id,
                agent_name=artifact.agent_name,
                file_path=artifact.file_path,
                file_name=artifact.file_name,
                artifact_type=artifact.artifact_type.value,
                content=artifact.content,
                content_hash=artifact.content_hash,
                status=artifact.status.value,
                version=artifact.version,
                parent_version=artifact.parent_version,
                commit_sha=artifact.commit_sha,
                task_id=artifact.task_id,
                description=artifact.description,
                metadata=artifact.metadata,
                created_at=artifact.created_at.isoformat(),
                updated_at=artifact.updated_at.isoformat(),
                reviewed_by=artifact.reviewed_by,
                review_notes=artifact.review_notes
            ))
        
        return {
            "agent_id": agent_id,
            "artifacts": artifact_responses,
            "total_count": len(artifact_responses)
        }
        
    except Exception as e:
        logger.log_error(e, {
            "action": "get_agent_artifacts_api",
            "agent_id": agent_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file-versions/{project_id}", response_model=Dict[str, Any])
async def get_file_versions(
    project_id: str = Path(..., description="Project ID"),
    file_path: str = Query(..., description="File path")
):
    """Get all versions of a specific file"""
    try:
        versions = await code_artifact_manager.get_file_versions(project_id, file_path)
        
        return {
            "project_id": project_id,
            "file_path": file_path,
            "versions": [
                {
                    "version_id": v.version_id,
                    "artifact_id": v.artifact_id,
                    "version_number": v.version_number,
                    "content_hash": v.content_hash,
                    "changes_summary": v.changes_summary,
                    "created_by": v.created_by,
                    "created_at": v.created_at.isoformat(),
                    "commit_sha": v.commit_sha
                }
                for v in versions
            ],
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.log_error(e, {
            "action": "get_file_versions_api",
            "project_id": project_id,
            "file_path": file_path
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot", response_model=Dict[str, str])
async def create_codebase_snapshot(request: CreateSnapshotRequest):
    """Create a snapshot of the entire codebase"""
    try:
        snapshot_id = await code_artifact_manager.create_codebase_snapshot(
            project_id=request.project_id,
            snapshot_name=request.snapshot_name,
            description=request.description,
            created_by=request.created_by,
            commit_sha=request.commit_sha,
            tags=request.tags
        )
        
        logger.log_system_event("codebase_snapshot_created_via_api", {
            "snapshot_id": snapshot_id,
            "project_id": request.project_id,
            "created_by": request.created_by
        })
        
        return {"snapshot_id": snapshot_id, "status": "created"}
        
    except Exception as e:
        logger.log_error(e, {
            "action": "create_codebase_snapshot_api",
            "project_id": request.project_id
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=Dict[str, Any])
async def search_artifacts(
    project_id: Optional[str] = Query(None, description="Project ID filter"),
    agent_id: Optional[str] = Query(None, description="Agent ID filter"),
    artifact_type: Optional[str] = Query(None, description="Artifact type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    search_term: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(50, description="Maximum results"),
    offset: int = Query(0, description="Results offset")
):
    """Search artifacts with various filters"""
    try:
        # Convert string filters to enums if provided
        type_filter = ArtifactType(artifact_type) if artifact_type else None
        status_filter = ArtifactStatus(status) if status else None
        
        # Perform search
        results = await code_artifact_manager.search_artifacts(
            project_id=project_id,
            agent_id=agent_id,
            artifact_type=type_filter,
            status=status_filter,
            search_term=search_term
        )
        
        # Apply pagination
        total_count = len(results)
        paginated_results = results[offset:offset + limit]
        
        # Convert to response format
        artifact_responses = []
        for artifact in paginated_results:
            artifact_responses.append(ArtifactResponse(
                id=artifact.id,
                project_id=artifact.project_id,
                agent_id=artifact.agent_id,
                agent_name=artifact.agent_name,
                file_path=artifact.file_path,
                file_name=artifact.file_name,
                artifact_type=artifact.artifact_type.value,
                content=artifact.content,
                content_hash=artifact.content_hash,
                status=artifact.status.value,
                version=artifact.version,
                parent_version=artifact.parent_version,
                commit_sha=artifact.commit_sha,
                task_id=artifact.task_id,
                description=artifact.description,
                metadata=artifact.metadata,
                created_at=artifact.created_at.isoformat(),
                updated_at=artifact.updated_at.isoformat(),
                reviewed_by=artifact.reviewed_by,
                review_notes=artifact.review_notes
            ))
        
        return {
            "results": artifact_responses,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.log_error(e, {
            "action": "search_artifacts_api",
            "search_term": search_term
        })
        raise HTTPException(status_code=500, detail=str(e))