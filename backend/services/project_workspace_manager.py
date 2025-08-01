"""
ARTAC Project Workspace Manager
Manages collaborative project workspaces for multi-agent development
"""

import asyncio
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess

from core.config import settings
from core.logging import get_logger
from services.git_manager import GitManager
from services.file_lock_manager import FileLockManager

logger = get_logger(__name__)


class ProjectWorkspace:
    """Manages a single project workspace with multi-agent collaboration"""
    
    def __init__(self, project_id: str, project_name: str, base_path: str = None):
        self.project_id = project_id
        self.project_name = project_name
        self.base_path = base_path or os.path.join(settings.WORKSPACE_ROOT, "projects")
        self.workspace_path = os.path.join(self.base_path, project_id)
        self.git_manager = GitManager(self.workspace_path)
        self.file_lock_manager = FileLockManager(project_id)
        
        # Workspace structure
        self.main_path = os.path.join(self.workspace_path, "main")
        self.agents_path = os.path.join(self.workspace_path, "agents")
        self.shared_path = os.path.join(self.workspace_path, "shared")
        self.artac_path = os.path.join(self.workspace_path, ".artac")
        
        # Metadata files
        self.assignments_file = os.path.join(self.artac_path, "assignments.json")
        self.permissions_file = os.path.join(self.artac_path, "permissions.json")
        self.config_file = os.path.join(self.artac_path, "config.json")
        
        self.agents: Dict[str, Dict] = {}
        self.assignments: Dict[str, Dict] = {}
        self.permissions: Dict[str, Dict] = {}
    
    async def initialize(self, git_repo_url: str = None) -> bool:
        """Initialize the project workspace"""
        try:
            # Create workspace directory structure
            os.makedirs(self.workspace_path, exist_ok=True)
            os.makedirs(self.main_path, exist_ok=True)
            os.makedirs(self.agents_path, exist_ok=True)
            os.makedirs(self.shared_path, exist_ok=True)
            os.makedirs(self.artac_path, exist_ok=True)
            
            # Initialize or clone Git repository
            if git_repo_url:
                await self.git_manager.clone_repository(git_repo_url, self.main_path)
            else:
                await self.git_manager.initialize_repository(self.main_path)
            
            # Create shared directories
            shared_dirs = ["docs", "configs", "assets", "logs"]
            for dir_name in shared_dirs:
                os.makedirs(os.path.join(self.shared_path, dir_name), exist_ok=True)
            
            # Initialize metadata files
            await self._initialize_metadata()
            
            logger.log_system_event("project_workspace_initialized", {
                "project_id": self.project_id,
                "project_name": self.project_name,
                "workspace_path": self.workspace_path,
                "git_initialized": True
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initialize_project_workspace",
                "project_id": self.project_id
            })
            return False
    
    async def _initialize_metadata(self):
        """Initialize metadata files"""
        # Default configuration
        config = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "created_at": datetime.utcnow().isoformat(),
            "settings": {
                "auto_merge": False,
                "require_review": True,
                "max_concurrent_agents": 10,
                "conflict_resolution": "manual"
            }
        }
        
        # Default permissions (hierarchical)
        permissions = {
            "ceo": {
                "level": 100,
                "can_read": ["*"],
                "can_write": ["*"],
                "can_merge": ["*"],
                "can_assign_tasks": True,
                "can_create_branches": True
            },
            "senior": {
                "level": 80,
                "can_read": ["*"],
                "can_write": ["src/*", "tests/*", "docs/*"],
                "can_merge": ["agent/*"],
                "can_assign_tasks": True,
                "can_create_branches": True
            },
            "developer": {
                "level": 60,
                "can_read": ["src/*", "tests/*", "docs/*"],
                "can_write": ["src/*", "tests/*"],
                "can_merge": [],
                "can_assign_tasks": False,
                "can_create_branches": True
            },
            "intern": {
                "level": 20,
                "can_read": ["src/*", "tests/*"],
                "can_write": ["src/components/*", "tests/unit/*"],
                "can_merge": [],
                "can_assign_tasks": False,
                "can_create_branches": True
            }
        }
        
        # Write metadata files
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        with open(self.permissions_file, 'w') as f:
            json.dump(permissions, f, indent=2)
        
        with open(self.assignments_file, 'w') as f:
            json.dump({}, f, indent=2)
    
    async def add_agent(self, agent_id: str, agent_role: str, agent_name: str) -> bool:
        """Add an agent to the project workspace"""
        try:
            # Create agent workspace
            agent_workspace = os.path.join(self.agents_path, agent_id)
            os.makedirs(agent_workspace, exist_ok=True)
            
            # Create agent branch
            branch_name = f"agent/{agent_id}"
            await self.git_manager.create_branch(branch_name, self.main_path)
            
            # Clone main branch to agent workspace
            await self.git_manager.clone_branch("main", agent_workspace)
            await self.git_manager.checkout_branch(branch_name, agent_workspace)
            
            # Register agent
            self.agents[agent_id] = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_role": agent_role,
                "workspace_path": agent_workspace,
                "branch_name": branch_name,
                "added_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            logger.log_system_event("agent_added_to_project", {
                "project_id": self.project_id,
                "agent_id": agent_id,
                "agent_role": agent_role,
                "workspace_path": agent_workspace
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "add_agent_to_project",
                "project_id": self.project_id,
                "agent_id": agent_id
            })
            return False
    
    async def assign_task(self, task_id: str, agent_id: str, task_data: Dict) -> bool:
        """Assign a task to an agent"""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found in project")
            
            # Load current assignments
            with open(self.assignments_file, 'r') as f:
                assignments = json.load(f)
            
            # Add new assignment
            assignments[task_id] = {
                "task_id": task_id,
                "agent_id": agent_id,
                "assigned_at": datetime.utcnow().isoformat(),
                "status": "assigned",
                **task_data
            }
            
            # Save assignments
            with open(self.assignments_file, 'w') as f:
                json.dump(assignments, f, indent=2)
            
            self.assignments = assignments
            
            logger.log_system_event("task_assigned", {
                "project_id": self.project_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "task_title": task_data.get("title", "")
            })
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "assign_task",
                "project_id": self.project_id,
                "task_id": task_id,
                "agent_id": agent_id
            })
            return False
    
    def check_permissions(self, agent_id: str, action: str, file_path: str = None) -> bool:
        """Check if agent has permission for action"""
        try:
            # Load permissions
            with open(self.permissions_file, 'r') as f:
                permissions = json.load(f)
            
            # Get agent role from agents data
            agent_role = self.agents.get(agent_id, {}).get("agent_role", "intern")
            agent_perms = permissions.get(agent_role, permissions["intern"])
            
            if action == "read":
                return self._check_path_permission(file_path, agent_perms["can_read"])
            elif action == "write":
                return self._check_path_permission(file_path, agent_perms["can_write"])
            elif action == "merge":
                return self._check_path_permission(file_path, agent_perms["can_merge"])
            elif action == "assign_tasks":
                return agent_perms.get("can_assign_tasks", False)
            elif action == "create_branches":
                return agent_perms.get("can_create_branches", False)
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "check_permissions",
                "agent_id": agent_id,
                "permission_action": action
            })
            return False
    
    def _check_path_permission(self, file_path: str, allowed_patterns: List[str]) -> bool:
        """Check if file path matches allowed patterns"""
        if not file_path:
            return True
        
        for pattern in allowed_patterns:
            if pattern == "*":
                return True
            if file_path.startswith(pattern.replace("*", "")):
                return True
        
        return False
    
    async def get_workspace_status(self) -> Dict[str, Any]:
        """Get current workspace status"""
        try:
            # Load current data
            with open(self.assignments_file, 'r') as f:
                assignments = json.load(f)
            
            # Get Git status
            git_status = await self.git_manager.get_status(self.main_path)
            
            # Get active locks
            active_locks = await self.file_lock_manager.get_active_locks()
            
            return {
                "project_id": self.project_id,
                "project_name": self.project_name,
                "agents_count": len(self.agents),
                "active_tasks": len([t for t in assignments.values() if t["status"] != "completed"]),
                "completed_tasks": len([t for t in assignments.values() if t["status"] == "completed"]),
                "git_status": git_status,
                "active_locks": len(active_locks),
                "workspace_path": self.workspace_path
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_workspace_status",
                "project_id": self.project_id
            })
            return {"error": str(e)}


class ProjectWorkspaceManager:
    """Manages multiple project workspaces"""
    
    def __init__(self):
        self.workspaces: Dict[str, ProjectWorkspace] = {}
        self.base_path = os.path.join(settings.WORKSPACE_ROOT, "projects")
        os.makedirs(self.base_path, exist_ok=True)
    
    async def create_project(self, project_name: str, git_repo_url: str = None) -> str:
        """Create a new project workspace"""
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        workspace = ProjectWorkspace(project_id, project_name, self.base_path)
        
        if await workspace.initialize(git_repo_url):
            self.workspaces[project_id] = workspace
            
            logger.log_system_event("project_created", {
                "project_id": project_id,
                "project_name": project_name,
                "git_repo_url": git_repo_url
            })
            
            return project_id
        else:
            raise RuntimeError(f"Failed to create project workspace: {project_name}")
    
    async def get_project(self, project_id: str) -> Optional[ProjectWorkspace]:
        """Get project workspace by ID"""
        if project_id in self.workspaces:
            return self.workspaces[project_id]
        
        # Try to load from disk
        project_path = os.path.join(self.base_path, project_id)
        if os.path.exists(project_path):
            config_file = os.path.join(project_path, ".artac", "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                workspace = ProjectWorkspace(project_id, config["project_name"], self.base_path)
                self.workspaces[project_id] = workspace
                return workspace
        
        return None
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = []
        
        if os.path.exists(self.base_path):
            for project_dir in os.listdir(self.base_path):
                if project_dir.startswith("proj_"):
                    workspace = await self.get_project(project_dir)
                    if workspace:
                        status = await workspace.get_workspace_status()
                        projects.append(status)
        
        return projects
    
    async def assign_agent_to_project(self, project_id: str, agent_id: str, agent_role: str, agent_name: str) -> bool:
        """Assign an agent to a project"""
        workspace = await self.get_project(project_id)
        if workspace:
            return await workspace.add_agent(agent_id, agent_role, agent_name)
        return False
    
    async def assign_task(self, project_id: str, task_id: str, agent_id: str, task_data: Dict) -> bool:
        """Assign a task to an agent in a project"""
        workspace = await self.get_project(project_id)
        if workspace:
            return await workspace.assign_task(task_id, agent_id, task_data)
        return False


# Global instance
project_workspace_manager = ProjectWorkspaceManager()