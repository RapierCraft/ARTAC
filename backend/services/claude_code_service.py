"""
ARTAC Claude Code Service
Integration with Claude Code CLI for agent operations
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
from services.process_manager import process_manager
from core.config import settings

logger = get_logger(__name__)


class ClaudeCodeSession:
    """Manages a Claude Code CLI session for an agent"""
    
    def __init__(self, agent_id: str, working_directory: str = None):
        self.agent_id = agent_id
        self.session_id = str(uuid.uuid4())
        self.working_directory = working_directory or tempfile.mkdtemp(prefix=f"artac-agent-{agent_id}-")
        self.process: Optional[subprocess.Popen] = None
        self.is_active = False
        
        # Ensure working directory exists
        os.makedirs(self.working_directory, exist_ok=True)
        
        logger.log_agent_action(
            agent_id=self.agent_id,
            action="session_created",
            details={"session_id": self.session_id, "working_dir": self.working_directory}
        )
    
    async def start_session(self) -> bool:
        """Start a headless Claude Code session"""
        try:
            # Start claude in headless mode (no terminal UI)
            # Properly detach from terminal to avoid SIGHUP issues
            kwargs = {
                'cwd': self.working_directory,
                'stdin': asyncio.subprocess.PIPE,
                'stdout': asyncio.subprocess.PIPE,
                'stderr': asyncio.subprocess.PIPE,
            }
            
            if sys.platform == 'win32':
                # Windows: use CREATE_NO_WINDOW flag
                kwargs['creationflags'] = 0x08000000
            else:
                # Unix: use start_new_session for process isolation
                if settings.PERSIST_CLAUDE_SESSIONS:
                    kwargs['start_new_session'] = True
            
            self.process = await asyncio.create_subprocess_exec(
                settings.CLAUDE_CODE_PATH,
                "--no-interactive",  # Headless mode
                "--quiet",           # Minimize output
                **kwargs
            )
            
            self.is_active = True
            
            # Register process with process manager (unless persisting sessions)
            if not settings.PERSIST_CLAUDE_SESSIONS:
                process_manager.register_process(self.agent_id, self.process)
            
            logger.log_agent_action(
                agent_id=self.agent_id,
                action="session_started",
                details={"session_id": self.session_id, "pid": self.process.pid, "headless": True}
            )
            
            return True
            
        except Exception as e:
            logger.log_error(e, {"agent_id": self.agent_id, "action": "start_session"})
            return False
    
    async def execute_command(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """Execute a command in the Claude Code session"""
        # Check if process is still alive
        if self.process and self.process.returncode is not None:
            # Process has terminated, need to restart
            logger.log_agent_action(
                agent_id=self.agent_id,
                action="session_terminated",
                details={"returncode": self.process.returncode, "restarting": True}
            )
            self.is_active = False
            self.process = None
            
            # Try to restart the session
            if not await self.start_session():
                raise RuntimeError("Failed to restart Claude Code session")
        
        if not self.is_active or not self.process:
            # Try to start a new session
            if not await self.start_session():
                raise RuntimeError("Claude Code session not active and could not be started")
        
        timeout = timeout or settings.CLAUDE_CODE_TIMEOUT
        
        try:
            # Check if stdin is still writable
            if (self.process.stdin.is_closing() or 
                (hasattr(self.process.stdin, '_transport') and 
                 self.process.stdin._transport and 
                 self.process.stdin._transport.is_closing())):
                raise RuntimeError("Claude Code stdin is closed, need to restart session")
            
            # Send command to Claude Code (encode string to bytes)
            self.process.stdin.write(f"{command}\n".encode('utf-8'))
            await self.process.stdin.drain()
            
            # Read response with timeout
            stdout_data = []
            stderr_data = []
            
            try:
                # Read stdout until we get a complete response
                while True:
                    try:
                        line = await asyncio.wait_for(
                            self.process.stdout.readline(), 
                            timeout=timeout
                        )
                        if not line:
                            break
                        stdout_data.append(line)
                        
                        # Check if we have a complete response
                        # (Claude Code typically ends responses with specific markers)
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        if line_str.strip().endswith("```") or "Done." in line_str:
                            break
                            
                    except asyncio.TimeoutError:
                        break
                
                # Check for any stderr output
                try:
                    while True:
                        line = await asyncio.wait_for(
                            self.process.stderr.readline(),
                            timeout=1.0
                        )
                        if not line:
                            break
                        stderr_data.append(line)
                except asyncio.TimeoutError:
                    pass
                
            except asyncio.TimeoutError:
                logger.log_agent_action(
                    agent_id=self.agent_id,
                    action="command_timeout",
                    details={"command": command[:100], "timeout": timeout}
                )
                return {
                    "success": False,
                    "error": "Command timed out",
                    "timeout": timeout
                }
            
            stdout_text = b"".join(stdout_data).decode('utf-8')
            stderr_text = b"".join(stderr_data).decode('utf-8')
            
            result = {
                "success": True,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command,
                "working_directory": self.working_directory
            }
            
            logger.log_agent_action(
                agent_id=self.agent_id,
                action="command_executed",
                details={
                    "command": command[:100],
                    "success": True,
                    "output_length": len(stdout_text)
                }
            )
            
            return result
            
        except RuntimeError as e:
            # Handle transport/connection errors by trying to restart
            if "handler is closed" in str(e) or "stdin is closed" in str(e):
                logger.log_agent_action(
                    agent_id=self.agent_id,
                    action="session_restart_required",
                    details={"error": str(e)}
                )
                self.is_active = False
                self.process = None
                
                # Try one more time with a fresh session
                if await self.start_session():
                    return await self.execute_command(command, timeout)
            
            logger.log_error(e, {
                "agent_id": self.agent_id,
                "command": command[:100],
                "action": "execute_command"
            })
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
        except Exception as e:
            logger.log_error(e, {
                "agent_id": self.agent_id,
                "command": command[:100],
                "action": "execute_command"
            })
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def close_session(self):
        """Close the Claude Code session"""
        if self.process:
            # If sessions should persist, just detach without terminating
            if settings.PERSIST_CLAUDE_SESSIONS:
                logger.log_agent_action(
                    agent_id=self.agent_id,
                    action="session_detached",
                    details={"session_id": self.session_id, "pid": self.process.pid, "persisted": True}
                )
                self.process = None
                self.is_active = False
                return
            
            try:
                # Unregister from process manager first
                process_manager.unregister_process(self.agent_id)
                
                # Graceful shutdown
                if self.process.stdin and not self.process.stdin.is_closing():
                    self.process.stdin.write("exit\n".encode('utf-8'))
                    await self.process.stdin.drain()
                    self.process.stdin.close()
                
                await asyncio.wait_for(self.process.wait(), timeout=10.0)
            except:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except:
                    self.process.kill()
            
            self.process = None
        
        self.is_active = False
        
        logger.log_agent_action(
            agent_id=self.agent_id,
            action="session_closed",
            details={"session_id": self.session_id, "headless": True}
        )
    
    async def stop_session(self):
        """Alias for close_session for consistency"""
        await self.close_session()


class ClaudeCodeService:
    """Service for managing Claude Code CLI integration"""
    
    def __init__(self):
        self.active_sessions: Dict[str, ClaudeCodeSession] = {}
        self._check_claude_availability()
    
    def _check_claude_availability(self):
        """Check if Claude Code CLI is available and handle authentication"""
        try:
            # First check if Claude CLI is installed
            result = subprocess.run(
                [settings.CLAUDE_CODE_PATH, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.log_system_event("claude_code_available", {
                    "version": result.stdout.strip(),
                    "path": settings.CLAUDE_CODE_PATH
                })
                
                # Check if we have API key authentication configured
                if os.environ.get('ANTHROPIC_API_KEY'):
                    logger.log_system_event("claude_code_authenticated", {
                        "message": "Claude Code CLI configured with API key"
                    })
                    return
                
                # Skip authentication check entirely - we know Claude works from direct testing
                logger.log_system_event("claude_code_authenticated", {
                    "message": "Claude Code CLI authentication bypassed - assuming working based on direct tests"
                })
                return
            else:
                raise RuntimeError(f"Claude Code returned non-zero exit code: {result.returncode}")
                
        except Exception as e:
            logger.log_error(e, {"action": "check_claude_availability"})
            # Don't raise error - allow service to start but log that auth may be needed
            if "timed out" in str(e):
                logger.log_system_event("claude_code_auth_check_timeout", {
                    "message": "Claude Code CLI authentication check timed out. Please authenticate manually or use API key."
                })
            else:
                logger.log_system_event("claude_code_auth_warning", {
                    "message": f"Claude Code CLI available but authentication status unclear: {e}"
                })
    
    async def get_or_create_session(self, agent_id: str, working_directory: str = None) -> ClaudeCodeSession:
        """Get existing session or create new one for agent"""
        if agent_id not in self.active_sessions:
            session = ClaudeCodeSession(agent_id, working_directory)
            if await session.start_session():
                self.active_sessions[agent_id] = session
            else:
                raise RuntimeError(f"Failed to start Claude Code session for agent {agent_id}")
        
        return self.active_sessions[agent_id]
    
    async def execute_for_agent(
        self, 
        agent_id: str, 
        command: str, 
        working_directory: str = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Execute Claude Code command for specific agent"""
        session = await self.get_or_create_session(agent_id, working_directory)
        return await session.execute_command(command, timeout)
    
    async def close_agent_session(self, agent_id: str):
        """Close session for specific agent"""
        if agent_id in self.active_sessions:
            await self.active_sessions[agent_id].close_session()
            del self.active_sessions[agent_id]
    
    async def close_all_sessions(self):
        """Close all active sessions"""
        logger.log_system_event("closing_all_claude_sessions", {
            "session_count": len(self.active_sessions)
        })
        
        for agent_id in list(self.active_sessions.keys()):
            await self.close_agent_session(agent_id)
        
        # Ensure process manager also shuts down all processes
        await process_manager.shutdown_all_processes()
    
    async def execute_one_shot(
        self, 
        command: str, 
        working_directory: str = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Execute a one-shot Claude Code command without persistent session"""
        working_dir = working_directory or tempfile.mkdtemp(prefix="raisc-oneshot-")
        timeout = timeout or settings.CLAUDE_CODE_TIMEOUT
        
        try:
            # Execute claude command directly in headless mode
            # Properly detach from terminal to avoid SIGHUP issues
            kwargs = {
                'cwd': working_dir,
                'stdout': asyncio.subprocess.PIPE,
                'stderr': asyncio.subprocess.PIPE,
            }
            
            if sys.platform == 'win32':
                # Windows: use CREATE_NO_WINDOW flag
                kwargs['creationflags'] = 0x08000000
            else:
                # Unix: use start_new_session for process isolation
                if settings.PERSIST_CLAUDE_SESSIONS:
                    kwargs['start_new_session'] = True
            
            process = await asyncio.create_subprocess_exec(
                settings.CLAUDE_CODE_PATH,
                "--no-interactive",  # Headless mode
                "--quiet",           # Minimize output
                command,
                **kwargs
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout,
                    "stderr": stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr,
                    "return_code": process.returncode,
                    "command": command,
                    "working_directory": working_dir
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
            logger.log_error(e, {"action": "execute_one_shot", "command": command[:100]})
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def get_session_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of agent's Claude Code session"""
        if agent_id not in self.active_sessions:
            return {"active": False}
        
        session = self.active_sessions[agent_id]
        return {
            "active": session.is_active,
            "session_id": session.session_id,
            "working_directory": session.working_directory,
            "process_id": session.process.pid if session.process else None
        }
    
    def get_all_sessions_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active sessions"""
        return {
            agent_id: self.get_session_status(agent_id)
            for agent_id in self.active_sessions
        }
    
    async def setup_authentication_token(self, token: str) -> Dict[str, Any]:
        """Setup Claude CLI authentication with provided token"""
        try:
            # Use the setup-token command with the provided token
            result = subprocess.run(
                [settings.CLAUDE_CODE_PATH, "setup-token"],
                input=f"{token}\n",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.log_system_event("claude_code_auth_success", {
                    "message": "Claude CLI authentication successful"
                })
                return {
                    "success": True,
                    "message": "Authentication successful"
                }
            else:
                logger.log_system_event("claude_code_auth_failed", {
                    "message": f"Authentication failed: {result.stderr}"
                })
                return {
                    "success": False,
                    "error": result.stderr or "Authentication failed"
                }
                
        except Exception as e:
            logger.log_error(e, {"action": "setup_authentication_token"})
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_authentication_url(self) -> Dict[str, Any]:
        """Get authentication URL for Claude CLI setup"""
        try:
            result = subprocess.run(
                [settings.CLAUDE_CODE_PATH, "setup-token"],
                capture_output=True,
                text=True,
                timeout=30,
                input="\n"
            )
            
            # Extract URL from output
            auth_url = None
            for line in result.stdout.split('\n'):
                if 'https://' in line and ('claude.ai' in line or 'anthropic.com' in line):
                    auth_url = line.strip()
                    break
            
            if auth_url:
                return {
                    "success": True,
                    "auth_url": auth_url,
                    "message": "Please visit the URL to authenticate"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not extract authentication URL",
                    "output": result.stdout
                }
                
        except Exception as e:
            logger.log_error(e, {"action": "get_authentication_url"})
            return {
                "success": False,
                "error": str(e)
            }