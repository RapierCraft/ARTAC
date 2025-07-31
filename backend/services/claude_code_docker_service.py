"""
ARTAC Claude Code Docker Service
Manages Claude Code sessions inside Docker containers for isolation
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import sys

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class DockerClaudeCodeSession:
    """Manages a Claude Code session inside a Docker container"""
    
    def __init__(self, agent_id: str, container_name: str = None):
        self.agent_id = agent_id
        self.session_id = str(uuid.uuid4())
        self.container_name = container_name or f"claude-agent-{agent_id}-{self.session_id[:8]}"
        self.container_id: Optional[str] = None
        self.is_active = False
        
        logger.log_agent_action(
            agent_id=self.agent_id,
            action="docker_session_created",
            details={"session_id": self.session_id, "container_name": self.container_name}
        )
    
    async def start_session(self) -> bool:
        """Start a Claude Code session in a Docker container"""
        try:
            # Build the docker run command
            docker_cmd = [
                "docker", "run", "-d",
                "--name", self.container_name,
                "--network", "artac-network",
                # Mount the workspace
                "-v", f"{os.path.abspath('.')}:/workspace/artac",
                # Environment variables
                "-e", f"AGENT_ID={self.agent_id}",
                "-e", f"SESSION_ID={self.session_id}",
                "-e", "ENVIRONMENT=development",
                "-e", "DEBUG=true",
                # Use the claude-dev image
                "artac-claude-dev:latest",
                # Keep container running
                "tail", "-f", "/dev/null"
            ]
            
            # Start the container
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to start Docker container: {result.stderr}")
                return False
            
            self.container_id = result.stdout.strip()
            
            # Install Claude Code in the container
            install_cmd = [
                "docker", "exec", self.container_name,
                "bash", "-c", 
                "curl -fsSL https://storage.googleapis.com/public-scripts/install-claude-cli.sh | bash"
            ]
            
            install_result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if install_result.returncode != 0:
                logger.warning(f"Claude Code installation failed: {install_result.stderr}")
                # Continue anyway - Claude might already be installed
            
            self.is_active = True
            
            logger.log_agent_action(
                agent_id=self.agent_id,
                action="docker_session_started",
                details={
                    "session_id": self.session_id,
                    "container_id": self.container_id,
                    "container_name": self.container_name
                }
            )
            
            return True
            
        except Exception as e:
            logger.log_error(e, {"agent_id": self.agent_id, "action": "start_docker_session"})
            return False
    
    async def execute_command(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """Execute a command in the Docker container"""
        if not self.is_active or not self.container_id:
            raise RuntimeError("Docker session not active")
        
        timeout = timeout or settings.CLAUDE_CODE_TIMEOUT
        
        try:
            # Execute command in container
            docker_exec_cmd = [
                "docker", "exec", "-i", self.container_name,
                "bash", "-c", f"cd /workspace/artac && {command}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *docker_exec_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "return_code": process.returncode,
                    "command": command,
                    "container": self.container_name
                }
                
            except asyncio.TimeoutError:
                process.terminate()
                return {
                    "success": False,
                    "error": "Command timed out",
                    "timeout": timeout,
                    "command": command
                }
                
        except Exception as e:
            logger.log_error(e, {
                "agent_id": self.agent_id,
                "command": command[:100],
                "action": "execute_docker_command"
            })
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def execute_claude_command(self, claude_command: str, timeout: int = None) -> Dict[str, Any]:
        """Execute a Claude Code command in the Docker container"""
        # Wrap the Claude command properly
        full_command = f"claude {claude_command}"
        return await self.execute_command(full_command, timeout)
    
    async def close_session(self, remove_container: bool = True):
        """Close the Docker session"""
        if self.container_id:
            try:
                if remove_container:
                    # Stop and remove container
                    subprocess.run(["docker", "stop", self.container_name], capture_output=True)
                    subprocess.run(["docker", "rm", self.container_name], capture_output=True)
                    
                    logger.log_agent_action(
                        agent_id=self.agent_id,
                        action="docker_session_removed",
                        details={"session_id": self.session_id, "container_name": self.container_name}
                    )
                else:
                    # Just stop the container, keep it for debugging
                    subprocess.run(["docker", "stop", self.container_name], capture_output=True)
                    
                    logger.log_agent_action(
                        agent_id=self.agent_id,
                        action="docker_session_stopped",
                        details={"session_id": self.session_id, "container_name": self.container_name}
                    )
                
            except Exception as e:
                logger.log_error(e, {"agent_id": self.agent_id, "action": "close_docker_session"})
            
            self.container_id = None
        
        self.is_active = False


class ClaudeCodeDockerService:
    """Service for managing Claude Code sessions in Docker containers"""
    
    def __init__(self):
        self.active_sessions: Dict[str, DockerClaudeCodeSession] = {}
        self._ensure_docker_setup()
    
    def _ensure_docker_setup(self):
        """Ensure Docker is available and claude-dev image is built"""
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "version"], capture_output=True)
            if result.returncode != 0:
                raise RuntimeError("Docker is not available")
            
            # Check if claude-dev image exists
            result = subprocess.run(
                ["docker", "images", "-q", "artac-claude-dev:latest"],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                logger.info("Building claude-dev Docker image...")
                # Build the image
                build_result = subprocess.run(
                    ["docker", "build", "-t", "artac-claude-dev:latest", "./claude-dev"],
                    cwd=os.path.dirname(os.path.dirname(__file__)),
                    capture_output=True,
                    text=True
                )
                
                if build_result.returncode != 0:
                    raise RuntimeError(f"Failed to build Docker image: {build_result.stderr}")
                
                logger.info("Claude-dev Docker image built successfully")
            
            # Ensure network exists
            subprocess.run(
                ["docker", "network", "create", "artac-network"],
                capture_output=True
            )
            
            logger.log_system_event("docker_claude_ready", {
                "image": "artac-claude-dev:latest",
                "network": "artac-network"
            })
            
        except Exception as e:
            logger.log_error(e, {"action": "ensure_docker_setup"})
            raise RuntimeError(f"Docker setup failed: {e}")
    
    async def get_or_create_session(self, agent_id: str) -> DockerClaudeCodeSession:
        """Get existing session or create new one for agent"""
        if agent_id not in self.active_sessions:
            session = DockerClaudeCodeSession(agent_id)
            if await session.start_session():
                self.active_sessions[agent_id] = session
            else:
                raise RuntimeError(f"Failed to start Docker session for agent {agent_id}")
        
        return self.active_sessions[agent_id]
    
    async def execute_for_agent(
        self, 
        agent_id: str, 
        command: str, 
        is_claude_command: bool = True,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Execute command for specific agent in Docker container"""
        session = await self.get_or_create_session(agent_id)
        
        if is_claude_command:
            return await session.execute_claude_command(command, timeout)
        else:
            return await session.execute_command(command, timeout)
    
    async def close_agent_session(self, agent_id: str, keep_container: bool = False):
        """Close session for specific agent"""
        if agent_id in self.active_sessions:
            await self.active_sessions[agent_id].close_session(remove_container=not keep_container)
            del self.active_sessions[agent_id]
    
    async def close_all_sessions(self, keep_containers: bool = False):
        """Close all active Docker sessions"""
        logger.log_system_event("closing_all_docker_sessions", {
            "session_count": len(self.active_sessions),
            "keep_containers": keep_containers
        })
        
        for agent_id in list(self.active_sessions.keys()):
            await self.close_agent_session(agent_id, keep_container=keep_containers)
    
    def get_session_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of agent's Docker session"""
        if agent_id not in self.active_sessions:
            return {"active": False}
        
        session = self.active_sessions[agent_id]
        return {
            "active": session.is_active,
            "session_id": session.session_id,
            "container_name": session.container_name,
            "container_id": session.container_id
        }
    
    def get_all_sessions_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active Docker sessions"""
        return {
            agent_id: self.get_session_status(agent_id)
            for agent_id in self.active_sessions
        }
    
    async def list_docker_containers(self) -> List[Dict[str, str]]:
        """List all Claude-related Docker containers"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=claude-agent-", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container_info = json.loads(line)
                    containers.append({
                        "id": container_info.get("ID"),
                        "name": container_info.get("Names"),
                        "status": container_info.get("Status"),
                        "created": container_info.get("CreatedAt")
                    })
            
            return containers
            
        except Exception as e:
            logger.log_error(e, {"action": "list_docker_containers"})
            return []


# Global Docker service instance
claude_code_docker_service = ClaudeCodeDockerService()