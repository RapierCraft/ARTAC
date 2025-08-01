"""
ARTAC File Lock Manager
Handles concurrent file access and conflict resolution for multi-agent collaboration
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import hashlib

from core.config import settings
from core.logging import get_logger
from core.database_postgres import db
from services.interaction_logger import interaction_logger, InteractionType, LogLevel

logger = get_logger(__name__)


class LockType(Enum):
    """Types of file locks"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"


class LockStatus(Enum):
    """Lock status"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    RELEASED = "released"


@dataclass
class FileLock:
    """File lock information"""
    lock_id: str
    project_id: str
    agent_id: str
    file_path: str
    lock_type: LockType
    status: LockStatus
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['lock_type'] = self.lock_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileLock':
        """Create from dictionary"""
        data['lock_type'] = LockType(data['lock_type'])
        data['status'] = LockStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class ConflictResolver:
    """Advanced conflict resolution strategies"""
    
    def __init__(self):
        self.resolution_strategies = {
            "auto_merge": self._auto_merge_strategy,
            "senior_override": self._senior_override_strategy,
            "timestamp_priority": self._timestamp_priority_strategy,
            "manual_review": self._manual_review_strategy
        }
    
    async def resolve_conflict(
        self,
        file_path: str,
        conflicts: List[Dict[str, Any]],
        strategy: str = "auto_merge"
    ) -> Dict[str, Any]:
        """Resolve file conflicts using specified strategy"""
        try:
            resolver = self.resolution_strategies.get(strategy, self._auto_merge_strategy)
            result = await resolver(file_path, conflicts)
            
            await interaction_logger.log_interaction(
                project_id=conflicts[0].get("project_id", ""),
                agent_id="system",
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="conflict_resolved",
                content=f"Resolved conflict in {file_path}",
                context={
                    "file_path": file_path,
                    "strategy": strategy,
                    "conflicts_count": len(conflicts)
                },
                metadata=result
            )
            
            return result
            
        except Exception as e:
            logger.log_error(e, {
                "action": "resolve_conflict",
                "file_path": file_path,
                "strategy": strategy
            })
            return {"success": False, "error": str(e)}
    
    async def _auto_merge_strategy(self, file_path: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Automatically merge non-conflicting changes"""
        try:
            # Sort conflicts by timestamp
            sorted_conflicts = sorted(conflicts, key=lambda x: x.get("timestamp", ""))
            
            # Read current file content
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    current_content = await f.read()
            else:
                current_content = ""
            
            merged_content = current_content
            successful_merges = []
            failed_merges = []
            
            for conflict in sorted_conflicts:
                try:
                    # Apply changes sequentially
                    if conflict.get("change_type") == "append":
                        merged_content += "\n" + conflict.get("content", "")
                        successful_merges.append(conflict)
                    elif conflict.get("change_type") == "replace":
                        # Simple replacement for now
                        old_content = conflict.get("old_content", "")
                        new_content = conflict.get("new_content", "")
                        if old_content in merged_content:
                            merged_content = merged_content.replace(old_content, new_content)
                            successful_merges.append(conflict)
                        else:
                            failed_merges.append(conflict)
                    else:
                        failed_merges.append(conflict)
                        
                except Exception as e:
                    failed_merges.append({**conflict, "error": str(e)})
            
            # Write merged content back
            if successful_merges:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(merged_content)
            
            return {
                "success": True,
                "strategy": "auto_merge",
                "successful_merges": len(successful_merges),
                "failed_merges": len(failed_merges),
                "requires_manual_review": len(failed_merges) > 0,
                "failed_conflicts": failed_merges
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _senior_override_strategy(self, file_path: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Senior agent changes override junior agent changes"""
        try:
            # Define agent hierarchy
            hierarchy = {"ceo": 100, "senior": 80, "developer": 60, "intern": 20}
            
            # Find the highest priority conflict
            highest_priority = -1
            winning_conflict = None
            
            for conflict in conflicts:
                agent_role = conflict.get("agent_role", "intern")
                priority = hierarchy.get(agent_role, 0)
                
                if priority > highest_priority:
                    highest_priority = priority
                    winning_conflict = conflict
            
            if winning_conflict:
                # Apply the winning conflict
                new_content = winning_conflict.get("new_content", "")
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(new_content)
                
                return {
                    "success": True,
                    "strategy": "senior_override",
                    "winning_agent": winning_conflict.get("agent_id"),
                    "winning_role": winning_conflict.get("agent_role"),
                    "overridden_conflicts": len(conflicts) - 1
                }
            else:
                return {"success": False, "error": "No valid conflicts to resolve"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _timestamp_priority_strategy(self, file_path: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Latest change wins"""
        try:
            # Sort by timestamp, latest first
            sorted_conflicts = sorted(
                conflicts,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            if sorted_conflicts:
                latest_conflict = sorted_conflicts[0]
                new_content = latest_conflict.get("new_content", "")
                
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(new_content)
                
                return {
                    "success": True,
                    "strategy": "timestamp_priority",
                    "winning_agent": latest_conflict.get("agent_id"),
                    "timestamp": latest_conflict.get("timestamp"),
                    "overridden_conflicts": len(conflicts) - 1
                }
            else:
                return {"success": False, "error": "No conflicts to resolve"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _manual_review_strategy(self, file_path: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mark for manual review"""
        return {
            "success": True,
            "strategy": "manual_review",
            "requires_manual_review": True,
            "conflicts": conflicts,
            "message": "Conflicts require manual review"
        }


class FileLockManager:
    """Manages file locks for concurrent access control"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.locks: Dict[str, FileLock] = {}  # lock_id -> FileLock
        self.file_locks: Dict[str, Set[str]] = {}  # file_path -> set of lock_ids
        self.agent_locks: Dict[str, Set[str]] = {}  # agent_id -> set of lock_ids
        self.conflict_resolver = ConflictResolver()
        self.lock_timeout = timedelta(minutes=30)  # Default lock timeout
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_locks())
    
    async def acquire_lock(
        self,
        agent_id: str,
        file_path: str,
        lock_type: LockType,
        timeout: int = 1800,  # 30 minutes default
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """Acquire a file lock"""
        try:
            # Normalize file path
            file_path = os.path.normpath(file_path)
            
            # Check if lock can be acquired
            can_acquire = await self._can_acquire_lock(agent_id, file_path, lock_type)
            
            if not can_acquire:
                # Add to pending queue
                return await self._queue_lock_request(agent_id, file_path, lock_type, timeout, metadata)
            
            # Create lock
            lock_id = f"lock_{uuid.uuid4().hex[:8]}"
            expires_at = datetime.utcnow() + timedelta(seconds=timeout)
            
            file_lock = FileLock(
                lock_id=lock_id,
                project_id=self.project_id,
                agent_id=agent_id,
                file_path=file_path,
                lock_type=lock_type,
                status=LockStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Store lock
            self.locks[lock_id] = file_lock
            
            if file_path not in self.file_locks:
                self.file_locks[file_path] = set()
            self.file_locks[file_path].add(lock_id)
            
            if agent_id not in self.agent_locks:
                self.agent_locks[agent_id] = set()
            self.agent_locks[agent_id].add(lock_id)
            
            # Log lock acquisition
            await interaction_logger.log_interaction(
                project_id=self.project_id,
                agent_id=agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="file_lock_acquired",
                content=f"Acquired {lock_type.value} lock on {file_path}",
                context={
                    "lock_id": lock_id,
                    "file_path": file_path,
                    "lock_type": lock_type.value,
                    "expires_at": expires_at.isoformat()
                },
                metadata=metadata or {}
            )
            
            return lock_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "acquire_lock",
                "agent_id": agent_id,
                "file_path": file_path
            })
            return None
    
    async def release_lock(self, lock_id: str, agent_id: str = None) -> bool:
        """Release a file lock"""
        try:
            if lock_id not in self.locks:
                return False
            
            file_lock = self.locks[lock_id]
            
            # Verify agent owns the lock (unless system override)
            if agent_id and file_lock.agent_id != agent_id:
                return False
            
            # Remove lock
            file_lock.status = LockStatus.RELEASED
            del self.locks[lock_id]
            
            # Clean up references
            if file_lock.file_path in self.file_locks:
                self.file_locks[file_lock.file_path].discard(lock_id)
                if not self.file_locks[file_lock.file_path]:
                    del self.file_locks[file_lock.file_path]
            
            if file_lock.agent_id in self.agent_locks:
                self.agent_locks[file_lock.agent_id].discard(lock_id)
                if not self.agent_locks[file_lock.agent_id]:
                    del self.agent_locks[file_lock.agent_id]
            
            # Log lock release
            await interaction_logger.log_interaction(
                project_id=self.project_id,
                agent_id=file_lock.agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="file_lock_released",
                content=f"Released {file_lock.lock_type.value} lock on {file_lock.file_path}",
                context={
                    "lock_id": lock_id,
                    "file_path": file_lock.file_path,
                    "lock_type": file_lock.lock_type.value
                }
            )
            
            # Process pending locks for this file
            await self._process_pending_locks(file_lock.file_path)
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "release_lock",
                "lock_id": lock_id
            })
            return False
    
    async def check_file_access(self, agent_id: str, file_path: str, access_type: str) -> Dict[str, Any]:
        """Check if agent can access file"""
        try:
            file_path = os.path.normpath(file_path)
            
            # Get current locks on file
            current_locks = await self.get_file_locks(file_path)
            
            # Check access permissions
            can_read = access_type == "read"
            can_write = access_type in ["write", "modify"]
            
            blocking_locks = []
            
            for lock in current_locks:
                if lock.agent_id == agent_id:
                    continue  # Agent owns the lock
                
                if access_type == "read" and lock.lock_type == LockType.READ:
                    continue  # Multiple read locks allowed
                
                # Any other combination is blocking
                blocking_locks.append(lock)
            
            return {
                "can_access": len(blocking_locks) == 0,
                "access_type": access_type,
                "blocking_locks": [lock.to_dict() for lock in blocking_locks],
                "current_locks": [lock.to_dict() for lock in current_locks]
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "check_file_access",
                "agent_id": agent_id,
                "file_path": file_path
            })
            return {"can_access": False, "error": str(e)}
    
    async def detect_conflicts(self, file_path: str) -> List[Dict[str, Any]]:
        """Detect potential conflicts for a file"""
        try:
            file_path = os.path.normpath(file_path)
            conflicts = []
            
            # Get all recent modifications to this file
            current_locks = await self.get_file_locks(file_path)
            write_locks = [lock for lock in current_locks if lock.lock_type in [LockType.WRITE, LockType.EXCLUSIVE]]
            
            if len(write_locks) > 1:
                # Multiple write locks indicate potential conflict
                conflicts.append({
                    "type": "concurrent_writes",
                    "file_path": file_path,
                    "agents": [lock.agent_id for lock in write_locks],
                    "locks": [lock.to_dict() for lock in write_locks]
                })
            
            # Check file modification times vs lock times
            if os.path.exists(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                for lock in current_locks:
                    if file_mtime > lock.created_at:
                        conflicts.append({
                            "type": "file_modified_after_lock",
                            "file_path": file_path,
                            "agent_id": lock.agent_id,
                            "lock_time": lock.created_at.isoformat(),
                            "file_mtime": file_mtime.isoformat()
                        })
            
            return conflicts
            
        except Exception as e:
            logger.log_error(e, {
                "action": "detect_conflicts",
                "file_path": file_path
            })
            return []
    
    async def get_file_locks(self, file_path: str) -> List[FileLock]:
        """Get all active locks for a file"""
        file_path = os.path.normpath(file_path)
        
        if file_path not in self.file_locks:
            return []
        
        return [
            self.locks[lock_id]
            for lock_id in self.file_locks[file_path]
            if lock_id in self.locks and self.locks[lock_id].status == LockStatus.ACTIVE
        ]
    
    async def get_agent_locks(self, agent_id: str) -> List[FileLock]:
        """Get all active locks for an agent"""
        if agent_id not in self.agent_locks:
            return []
        
        return [
            self.locks[lock_id]
            for lock_id in self.agent_locks[agent_id]
            if lock_id in self.locks and self.locks[lock_id].status == LockStatus.ACTIVE
        ]
    
    async def get_active_locks(self) -> List[FileLock]:
        """Get all active locks"""
        return [
            lock for lock in self.locks.values()
            if lock.status == LockStatus.ACTIVE
        ]
    
    async def force_release_locks(self, agent_id: str) -> int:
        """Force release all locks for an agent (emergency use)"""
        released_count = 0
        
        if agent_id in self.agent_locks:
            lock_ids = list(self.agent_locks[agent_id])
            
            for lock_id in lock_ids:
                if await self.release_lock(lock_id):
                    released_count += 1
        
        await interaction_logger.log_interaction(
            project_id=self.project_id,
            agent_id="system",
            interaction_type=InteractionType.SYSTEM_EVENT,
            action="force_release_locks",
            content=f"Force released {released_count} locks for agent {agent_id}",
            context={"agent_id": agent_id, "released_count": released_count},
            level=LogLevel.WARNING
        )
        
        return released_count
    
    async def _can_acquire_lock(self, agent_id: str, file_path: str, lock_type: LockType) -> bool:
        """Check if a lock can be acquired"""
        current_locks = await self.get_file_locks(file_path)
        
        for lock in current_locks:
            if lock.agent_id == agent_id:
                continue  # Agent already has a lock
            
            # Check compatibility
            if lock_type == LockType.READ and lock.lock_type == LockType.READ:
                continue  # Multiple read locks allowed
            
            # Any other combination blocks
            return False
        
        return True
    
    async def _queue_lock_request(
        self,
        agent_id: str,
        file_path: str,
        lock_type: LockType,
        timeout: int,
        metadata: Dict[str, Any]
    ) -> str:
        """Queue a lock request for later processing"""
        lock_id = f"pending_{uuid.uuid4().hex[:8]}"
        expires_at = datetime.utcnow() + timedelta(seconds=timeout)
        
        pending_lock = FileLock(
            lock_id=lock_id,
            project_id=self.project_id,
            agent_id=agent_id,
            file_path=file_path,
            lock_type=lock_type,
            status=LockStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.locks[lock_id] = pending_lock
        
        await interaction_logger.log_interaction(
            project_id=self.project_id,
            agent_id=agent_id,
            interaction_type=InteractionType.SYSTEM_EVENT,
            action="file_lock_queued",
            content=f"Queued {lock_type.value} lock request for {file_path}",
            context={
                "lock_id": lock_id,
                "file_path": file_path,
                "lock_type": lock_type.value
            }
        )
        
        return lock_id
    
    async def _process_pending_locks(self, file_path: str):
        """Process pending locks for a file"""
        try:
            pending_locks = [
                lock for lock in self.locks.values()
                if lock.file_path == file_path and lock.status == LockStatus.PENDING
            ]
            
            # Sort by creation time (FIFO)
            pending_locks.sort(key=lambda x: x.created_at)
            
            for lock in pending_locks:
                if await self._can_acquire_lock(lock.agent_id, lock.file_path, lock.lock_type):
                    # Activate the lock
                    lock.status = LockStatus.ACTIVE
                    
                    # Update references
                    if lock.file_path not in self.file_locks:
                        self.file_locks[lock.file_path] = set()
                    self.file_locks[lock.file_path].add(lock.lock_id)
                    
                    if lock.agent_id not in self.agent_locks:
                        self.agent_locks[lock.agent_id] = set()
                    self.agent_locks[lock.agent_id].add(lock.lock_id)
                    
                    await interaction_logger.log_interaction(
                        project_id=self.project_id,
                        agent_id=lock.agent_id,
                        interaction_type=InteractionType.SYSTEM_EVENT,
                        action="pending_lock_activated",
                        content=f"Activated pending {lock.lock_type.value} lock on {lock.file_path}",
                        context={
                            "lock_id": lock.lock_id,
                            "file_path": lock.file_path,
                            "lock_type": lock.lock_type.value
                        }
                    )
                    
                    break  # Only activate one lock at a time
                    
        except Exception as e:
            logger.log_error(e, {"action": "process_pending_locks"})
    
    async def _cleanup_expired_locks(self):
        """Background task to clean up expired locks"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_locks = []
                
                for lock_id, lock in list(self.locks.items()):
                    if current_time > lock.expires_at:
                        expired_locks.append(lock_id)
                
                for lock_id in expired_locks:
                    await self.release_lock(lock_id)
                    
                    await interaction_logger.log_interaction(
                        project_id=self.project_id,
                        agent_id="system",
                        interaction_type=InteractionType.SYSTEM_EVENT,
                        action="lock_expired",
                        content=f"Lock {lock_id} expired and was released",
                        context={"lock_id": lock_id},
                        level=LogLevel.WARNING
                    )
                
                if expired_locks:
                    logger.log_system_event("expired_locks_cleaned", {
                        "project_id": self.project_id,
                        "expired_count": len(expired_locks)
                    })
                
                # Sleep for 1 minute before next cleanup
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.log_error(e, {"action": "cleanup_expired_locks"})
                await asyncio.sleep(60)


# Global lock managers by project
project_lock_managers: Dict[str, FileLockManager] = {}


def get_lock_manager(project_id: str) -> FileLockManager:
    """Get or create lock manager for project"""
    if project_id not in project_lock_managers:
        project_lock_managers[project_id] = FileLockManager(project_id)
    return project_lock_managers[project_id]