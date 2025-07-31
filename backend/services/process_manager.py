"""
ARTAC Process Manager
Centralized management of Claude CLI processes in headless mode
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, List, Optional, Set
import psutil

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class ProcessManager:
    """Manages all Claude CLI processes to ensure they run headless"""
    
    def __init__(self):
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.process_agents: Dict[int, str] = {}  # pid -> agent_id mapping
        self.shutdown_requested = False
    
    def register_process(self, agent_id: str, process: asyncio.subprocess.Process):
        """Register a new Claude CLI process"""
        self.active_processes[agent_id] = process
        if process.pid:
            self.process_agents[process.pid] = agent_id
            
        logger.log_system_event("process_registered", {
            "agent_id": agent_id,
            "pid": process.pid,
            "total_processes": len(self.active_processes)
        })
    
    def unregister_process(self, agent_id: str):
        """Unregister a Claude CLI process"""
        if agent_id in self.active_processes:
            process = self.active_processes[agent_id]
            if process.pid and process.pid in self.process_agents:
                del self.process_agents[process.pid]
            del self.active_processes[agent_id]
            
            logger.log_system_event("process_unregistered", {
                "agent_id": agent_id,
                "total_processes": len(self.active_processes)
            })
    
    async def ensure_headless_mode(self):
        """Ensure all Claude CLI processes are running in headless mode"""
        try:
            # Check for any Claude processes that might have spawned terminals
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'claude' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline'] or []
                        
                        # Check if this is one of our managed processes
                        if proc.info['pid'] not in self.process_agents:
                            # This is an unknown Claude process - potentially with terminal
                            logger.log_system_event("unknown_claude_process_detected", {
                                "pid": proc.info['pid'],
                                "cmdline": cmdline
                            })
                            
                            # Kill it if it doesn't have headless flags
                            if '--no-interactive' not in cmdline and '--quiet' not in cmdline:
                                logger.log_system_event("terminating_non_headless_process", {
                                    "pid": proc.info['pid']
                                })
                                proc.terminate()
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.log_error(e, {"action": "ensure_headless_mode"})
    
    async def get_process_stats(self) -> Dict[str, any]:
        """Get statistics about managed processes"""
        stats = {
            "total_processes": len(self.active_processes),
            "active_agents": list(self.active_processes.keys()),
            "process_details": []
        }
        
        for agent_id, process in self.active_processes.items():
            try:
                if process.pid:
                    proc = psutil.Process(process.pid)
                    stats["process_details"].append({
                        "agent_id": agent_id,
                        "pid": process.pid,
                        "status": proc.status(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_mb": proc.memory_info().rss / 1024 / 1024,
                        "created": proc.create_time()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists
                stats["process_details"].append({
                    "agent_id": agent_id,
                    "pid": process.pid,
                    "status": "terminated"
                })
        
        return stats
    
    async def cleanup_orphaned_processes(self):
        """Clean up any orphaned Claude processes"""
        try:
            orphaned_pids = []
            
            for agent_id, process in list(self.active_processes.items()):
                if process.returncode is not None:
                    # Process has terminated
                    self.unregister_process(agent_id)
                    orphaned_pids.append(process.pid)
            
            if orphaned_pids:
                logger.log_system_event("cleaned_orphaned_processes", {
                    "orphaned_pids": orphaned_pids,
                    "remaining_processes": len(self.active_processes)
                })
                
        except Exception as e:
            logger.log_error(e, {"action": "cleanup_orphaned_processes"})
    
    async def shutdown_all_processes(self):
        """Gracefully shutdown all managed processes"""
        self.shutdown_requested = True
        
        logger.log_system_event("shutdown_all_processes_start", {
            "process_count": len(self.active_processes)
        })
        
        # Graceful shutdown
        for agent_id, process in list(self.active_processes.items()):
            try:
                if process.returncode is None:  # Still running
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown fails
                        process.kill()
                        await process.wait()
                
                self.unregister_process(agent_id)
                
            except Exception as e:
                logger.log_error(e, {
                    "action": "shutdown_process",
                    "agent_id": agent_id
                })
        
        logger.log_system_event("shutdown_all_processes_complete", {})
    
    async def monitor_processes(self):
        """Background task to monitor process health"""
        while not self.shutdown_requested:
            try:
                # Skip monitoring if sessions should persist
                if not settings.PERSIST_CLAUDE_SESSIONS:
                    await self.ensure_headless_mode()
                    await self.cleanup_orphaned_processes()
                
                # Log process statistics periodically
                if len(self.active_processes) > 0:
                    stats = await self.get_process_stats()
                    logger.log_system_event("process_health_check", {
                        "active_processes": stats["total_processes"],
                        "total_memory_mb": sum(p.get("memory_mb", 0) for p in stats["process_details"]),
                        "total_cpu_percent": sum(p.get("cpu_percent", 0) for p in stats["process_details"])
                    })
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.log_error(e, {"action": "monitor_processes"})
                await asyncio.sleep(10)  # Wait before retrying


# Global process manager instance
process_manager = ProcessManager()