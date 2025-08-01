"""
ARTAC Advanced Context Manager
Integrates all systems to provide comprehensive context management for agents
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import hashlib

from core.config import settings
from core.logging import get_logger
from services.interaction_logger import interaction_logger, InteractionType
from services.stateless_rag_manager import stateless_rag_manager
from services.task_hierarchy_manager import task_hierarchy_manager, TaskStatus
from services.project_workspace_manager import project_workspace_manager
from services.file_lock_manager import get_lock_manager

logger = get_logger(__name__)


@dataclass
class ContextRequest:
    """Context request with comprehensive parameters"""
    project_id: str
    agent_id: str
    query: str
    max_tokens: int = 180000
    include_history: bool = True
    time_range: str = "all"
    content_types: List[str] = None
    file_filter: str = None
    task_context: bool = True
    collaboration_context: bool = True
    code_context: bool = True
    error_context: bool = True
    priority_boost: List[str] = None  # Boost priority for specific agents or content types


class AdvancedContextManager:
    """Advanced context management with multi-system integration"""
    
    def __init__(self):
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache context for 15 minutes
        
        # Context strategies
        self.context_strategies = {
            "comprehensive": self._comprehensive_context_strategy,
            "task_focused": self._task_focused_context_strategy,
            "collaboration_focused": self._collaboration_focused_strategy,
            "debugging_focused": self._debugging_focused_strategy,
            "code_review_focused": self._code_review_focused_strategy
        }
    
    async def get_agent_context(
        self,
        request: ContextRequest,
        strategy: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Get comprehensive context for an agent"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request, strategy)
            if cache_key in self.context_cache:
                cached_data = self.context_cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                    return cached_data["context"]
            
            # Get context using specified strategy
            context_strategy = self.context_strategies.get(strategy, self._comprehensive_context_strategy)
            context = await context_strategy(request)
            
            # Cache the result
            self.context_cache[cache_key] = {
                "context": context,
                "timestamp": datetime.now()
            }
            
            # Log context retrieval
            await interaction_logger.log_interaction(
                project_id=request.project_id,
                agent_id=request.agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="advanced_context_retrieved",
                content=f"Retrieved {strategy} context for query: {request.query[:100]}...",
                context={
                    "strategy": strategy,
                    "tokens_used": context.get("total_tokens", 0),
                    "sources_count": len(context.get("sources", [])),
                    "query": request.query
                }
            )
            
            return context
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_agent_context",
                "project_id": request.project_id,
                "agent_id": request.agent_id,
                "strategy": strategy
            })
            return {"error": str(e), "context": "", "sources": []}
    
    async def _comprehensive_context_strategy(self, request: ContextRequest) -> Dict[str, Any]:
        """Comprehensive context including all available information"""
        context_parts = []
        all_sources = []
        total_tokens = 0
        remaining_tokens = request.max_tokens
        
        # Reserve tokens for different context types
        token_allocation = {
            "rag_context": int(remaining_tokens * 0.4),  # 40% for RAG
            "task_context": int(remaining_tokens * 0.2),  # 20% for tasks
            "collaboration_context": int(remaining_tokens * 0.15),  # 15% for collaboration
            "code_context": int(remaining_tokens * 0.15),  # 15% for code
            "system_context": int(remaining_tokens * 0.1)   # 10% for system info
        }
        
        # 1. Get RAG-based context using stateless unlimited context manager
        if token_allocation["rag_context"] > 0:
            # Map time_range to datetime filter
            time_filter = None
            if request.time_range == "last_day":
                time_filter = datetime.now() - timedelta(days=1)
            elif request.time_range == "last_week":
                time_filter = datetime.now() - timedelta(days=7)
            elif request.time_range == "last_month":
                time_filter = datetime.now() - timedelta(days=30)
            
            rag_context = await stateless_rag_manager.get_unlimited_context(
                project_id=request.project_id,
                agent_id=request.agent_id,
                query=request.query,
                max_tokens=token_allocation["rag_context"],
                strategy="hybrid",  # Use hybrid strategy for comprehensive results
                include_history=request.include_history,
                time_filter=time_filter
            )
            
            if rag_context.get("context"):
                context_parts.append("=== UNLIMITED RAG CONTEXT ===\n" + rag_context["context"])
                all_sources.extend(rag_context.get("sources", []))
                total_tokens += rag_context.get("total_tokens", 0)
        
        # 2. Get task context
        if request.task_context and token_allocation["task_context"] > 0:
            task_context = await self._get_task_context(request, token_allocation["task_context"])
            if task_context["context"]:
                context_parts.append("=== TASK CONTEXT ===\n" + task_context["context"])
                all_sources.extend(task_context.get("sources", []))
                total_tokens += task_context.get("tokens_used", 0)
        
        # 3. Get collaboration context
        if request.collaboration_context and token_allocation["collaboration_context"] > 0:
            collab_context = await self._get_collaboration_context(request, token_allocation["collaboration_context"])
            if collab_context["context"]:
                context_parts.append("=== COLLABORATION CONTEXT ===\n" + collab_context["context"])
                all_sources.extend(collab_context.get("sources", []))
                total_tokens += collab_context.get("tokens_used", 0)
        
        # 4. Get code context
        if request.code_context and token_allocation["code_context"] > 0:
            code_context = await self._get_code_context(request, token_allocation["code_context"])
            if code_context["context"]:
                context_parts.append("=== CODE CONTEXT ===\n" + code_context["context"])
                all_sources.extend(code_context.get("sources", []))
                total_tokens += code_context.get("tokens_used", 0)
        
        # 5. Get system context
        if token_allocation["system_context"] > 0:
            system_context = await self._get_system_context(request, token_allocation["system_context"])
            if system_context["context"]:
                context_parts.append("=== SYSTEM STATUS ===\n" + system_context["context"])
                all_sources.extend(system_context.get("sources", []))
                total_tokens += system_context.get("tokens_used", 0)
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": all_sources,
            "total_tokens": total_tokens,
            "strategy": "comprehensive",
            "query": request.query,
            "context_types": ["rag", "task", "collaboration", "code", "system"]
        }
    
    async def _task_focused_context_strategy(self, request: ContextRequest) -> Dict[str, Any]:
        """Context focused on current and related tasks"""
        context_parts = []
        all_sources = []
        total_tokens = 0
        
        # Get agent's current tasks
        agent_tasks = await task_hierarchy_manager.get_agent_tasks(
            request.agent_id,
            request.project_id,
            [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
        )
        
        if agent_tasks:
            task_context = "=== YOUR CURRENT TASKS ===\n"
            
            for task in agent_tasks[:5]:  # Limit to 5 most important tasks
                task_info = f"""
Task: {task.title}
Status: {task.status.value}
Priority: {task.priority.value}
Progress: {task.progress_percentage}%
Description: {task.description}
Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set'}
Files: {', '.join(task.file_paths) if task.file_paths else 'None'}
"""
                task_context += task_info
                
                # Get task hierarchy
                hierarchy = await task_hierarchy_manager.get_task_hierarchy(task.id)
                if hierarchy.get("parent_chain"):
                    task_context += f"Parent Tasks: {' -> '.join([p['title'] for p in hierarchy['parent_chain']])}\n"
                
                if hierarchy.get("children"):
                    task_context += f"Subtasks: {len(hierarchy['children'])} total, {hierarchy.get('completed_subtasks', 0)} completed\n"
                
                task_context += "---\n"
            
            context_parts.append(task_context)
            total_tokens += len(task_context) // 4  # Rough token estimation
        
        # Get RAG context related to tasks
        remaining_tokens = request.max_tokens - total_tokens
        if remaining_tokens > 1000:
            task_queries = []
            for task in agent_tasks[:3]:
                task_queries.append(f"{task.title} {task.description}")
            
            combined_query = f"{request.query} " + " ".join(task_queries)
            
            rag_context = await stateless_rag_manager.get_unlimited_context(
                project_id=request.project_id,
                agent_id=request.agent_id,
                query=combined_query,
                max_tokens=remaining_tokens,
                strategy="task_focused",
                include_history=True
            )
            
            if rag_context.get("context"):
                context_parts.append("=== TASK-RELATED CONTEXT ===\n" + rag_context["context"])
                all_sources.extend(rag_context.get("sources", []))
                total_tokens += rag_context.get("total_tokens", 0)
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": all_sources,
            "total_tokens": total_tokens,
            "strategy": "task_focused",
            "query": request.query,
            "active_tasks": len(agent_tasks)
        }
    
    async def _collaboration_focused_strategy(self, request: ContextRequest) -> Dict[str, Any]:
        """Context focused on team collaboration and communication"""
        context_parts = []
        all_sources = []
        total_tokens = 0
        
        # Get recent interactions
        recent_interactions = await interaction_logger.get_project_timeline(
            project_id=request.project_id,
            start_time=datetime.now() - timedelta(days=7),
            interaction_types=[InteractionType.COMMUNICATION, InteractionType.COLLABORATION]
        )
        
        if recent_interactions:
            collab_context = "=== RECENT TEAM INTERACTIONS ===\n"
            
            for interaction in recent_interactions[-10:]:  # Last 10 interactions
                collab_info = f"""
{interaction.timestamp.strftime('%Y-%m-%d %H:%M')} - {interaction.agent_id}
Action: {interaction.action}
Content: {interaction.content[:200]}...
"""
                if interaction.context.get("to_agent"):
                    collab_info += f"To: {interaction.context['to_agent']}\n"
                
                collab_context += collab_info + "---\n"
            
            context_parts.append(collab_context)
            total_tokens += len(collab_context) // 4
        
        # Get file lock status
        lock_manager = get_lock_manager(request.project_id)
        active_locks = await lock_manager.get_active_locks()
        
        if active_locks:
            lock_context = "=== CURRENT FILE LOCKS ===\n"
            for lock in active_locks[:5]:
                lock_info = f"""
File: {lock.file_path}
Locked by: {lock.agent_id}
Type: {lock.lock_type.value}
Since: {lock.created_at.strftime('%Y-%m-%d %H:%M')}
"""
                lock_context += lock_info + "---\n"
            
            context_parts.append(lock_context)
            total_tokens += len(lock_context) // 4
        
        # Get RAG context for collaboration
        remaining_tokens = request.max_tokens - total_tokens
        if remaining_tokens > 1000:
            rag_context = await stateless_rag_manager.get_unlimited_context(
                project_id=request.project_id,
                agent_id=request.agent_id,
                query=f"{request.query} collaboration communication team",
                max_tokens=remaining_tokens,
                strategy="semantic_clustering",
                include_history=True,
                time_filter=datetime.now() - timedelta(days=7)
            )
            
            if rag_context.get("context"):
                context_parts.append("=== COLLABORATION HISTORY ===\n" + rag_context["context"])
                all_sources.extend(rag_context.get("sources", []))
                total_tokens += rag_context.get("total_tokens", 0)
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": all_sources,
            "total_tokens": total_tokens,
            "strategy": "collaboration_focused",
            "query": request.query,
            "active_locks": len(active_locks),
            "recent_interactions": len(recent_interactions)
        }
    
    async def _debugging_focused_strategy(self, request: ContextRequest) -> Dict[str, Any]:
        """Context focused on debugging and error resolution"""
        context_parts = []
        all_sources = []
        total_tokens = 0
        
        # Get recent errors
        recent_errors = await interaction_logger.get_project_timeline(
            project_id=request.project_id,
            start_time=datetime.now() - timedelta(days=3),
            interaction_types=[InteractionType.DEBUGGING]
        )
        
        if recent_errors:
            error_context = "=== RECENT ERRORS ===\n"
            
            for error in recent_errors[-5:]:  # Last 5 errors
                error_info = f"""
{error.timestamp.strftime('%Y-%m-%d %H:%M')} - {error.agent_id}
Action: {error.action}
Error: {error.content[:300]}...
File: {error.context.get('file_path', 'Unknown')}
"""
                error_context += error_info + "---\n"
            
            context_parts.append(error_context)
            total_tokens += len(error_context) // 4
        
        # Get error-related RAG context
        remaining_tokens = request.max_tokens - total_tokens
        if remaining_tokens > 1000:
            error_query = f"{request.query} error debug exception fix solution"
            
            rag_context = await stateless_rag_manager.get_unlimited_context(
                project_id=request.project_id,
                agent_id=request.agent_id,
                query=error_query,
                max_tokens=remaining_tokens,
                strategy="temporal_priority",  # Recent errors are most relevant
                include_history=True,
                time_filter=datetime.now() - timedelta(days=30)
            )
            
            if rag_context.get("context"):
                context_parts.append("=== ERROR RESOLUTION CONTEXT ===\n" + rag_context["context"])
                all_sources.extend(rag_context.get("sources", []))
                total_tokens += rag_context.get("total_tokens", 0)
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": all_sources,
            "total_tokens": total_tokens,
            "strategy": "debugging_focused",
            "query": request.query,
            "recent_errors": len(recent_errors)
        }
    
    async def _code_review_focused_strategy(self, request: ContextRequest) -> Dict[str, Any]:
        """Context focused on code review and quality"""
        context_parts = []
        all_sources = []
        total_tokens = 0
        
        # Get recent code changes
        recent_changes = await interaction_logger.get_project_timeline(
            project_id=request.project_id,
            start_time=datetime.now() - timedelta(days=1),
            interaction_types=[InteractionType.CODE_EDIT]
        )
        
        if recent_changes:
            code_context = "=== RECENT CODE CHANGES ===\n"
            
            for change in recent_changes[-10:]:  # Last 10 changes
                change_info = f"""
{change.timestamp.strftime('%Y-%m-%d %H:%M')} - {change.agent_id}
Action: {change.action}
File: {change.context.get('file_path', 'Unknown')}
Changes: {change.content[:200]}...
"""
                code_context += change_info + "---\n"
            
            context_parts.append(code_context)
            total_tokens += len(code_context) // 4
        
        # Get code-related RAG context
        remaining_tokens = request.max_tokens - total_tokens
        if remaining_tokens > 1000:
            code_query = f"{request.query} code review quality best practices"
            
            rag_context = await stateless_rag_manager.get_unlimited_context(
                project_id=request.project_id,
                agent_id=request.agent_id,
                query=code_query,
                max_tokens=remaining_tokens,
                strategy="hierarchical",  # Good for code structure analysis
                include_history=True,
                time_filter=datetime.now() - timedelta(days=7)
            )
            
            if rag_context.get("context"):
                context_parts.append("=== CODE REVIEW CONTEXT ===\n" + rag_context["context"])
                all_sources.extend(rag_context.get("sources", []))
                total_tokens += rag_context.get("total_tokens", 0)
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": all_sources,
            "total_tokens": total_tokens,
            "strategy": "code_review_focused",
            "query": request.query,
            "recent_changes": len(recent_changes)
        }
    
    async def _get_task_context(self, request: ContextRequest, max_tokens: int) -> Dict[str, Any]:
        """Get task-specific context"""
        try:
            # Get agent's tasks
            agent_tasks = await task_hierarchy_manager.get_agent_tasks(
                request.agent_id, request.project_id
            )
            
            context_parts = []
            sources = []
            tokens_used = 0
            
            if agent_tasks:
                task_summary = f"You have {len(agent_tasks)} assigned tasks:\n"
                
                for i, task in enumerate(agent_tasks[:3]):  # Top 3 tasks
                    task_info = f"""
{i+1}. {task.title} ({task.status.value}, {task.progress_percentage}%)
   Priority: {task.priority.value}
   Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set'}
   Description: {task.description[:150]}...
"""
                    task_summary += task_info
                    sources.append({
                        "type": "task",
                        "task_id": task.id,
                        "title": task.title,
                        "status": task.status.value
                    })
                
                context_parts.append(task_summary)
                tokens_used = len(task_summary) // 4
            
            return {
                "context": "\n".join(context_parts),
                "sources": sources,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "get_task_context"})
            return {"context": "", "sources": [], "tokens_used": 0}
    
    async def _get_collaboration_context(self, request: ContextRequest, max_tokens: int) -> Dict[str, Any]:
        """Get collaboration-specific context"""
        try:
            # Get recent team communications
            recent_comms = await interaction_logger.get_project_timeline(
                project_id=request.project_id,
                start_time=datetime.now() - timedelta(hours=24),
                interaction_types=[InteractionType.COMMUNICATION]
            )
            
            context_parts = []
            sources = []
            tokens_used = 0
            
            if recent_comms:
                comm_summary = "Recent team communications:\n"
                
                for comm in recent_comms[-5:]:  # Last 5 communications
                    comm_info = f"- {comm.agent_id}: {comm.content[:100]}...\n"
                    comm_summary += comm_info
                    sources.append({
                        "type": "communication",
                        "agent_id": comm.agent_id,
                        "timestamp": comm.timestamp.isoformat()
                    })
                
                context_parts.append(comm_summary)
                tokens_used = len(comm_summary) // 4
            
            return {
                "context": "\n".join(context_parts),
                "sources": sources,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "get_collaboration_context"})
            return {"context": "", "sources": [], "tokens_used": 0}
    
    async def _get_code_context(self, request: ContextRequest, max_tokens: int) -> Dict[str, Any]:
        """Get code-specific context"""
        try:
            # Get recent code changes
            recent_code = await interaction_logger.get_project_timeline(
                project_id=request.project_id,
                start_time=datetime.now() - timedelta(hours=12),
                interaction_types=[InteractionType.CODE_EDIT]
            )
            
            context_parts = []
            sources = []
            tokens_used = 0
            
            if recent_code:
                code_summary = "Recent code changes:\n"
                
                for code_change in recent_code[-5:]:  # Last 5 changes
                    file_path = code_change.context.get('file_path', 'Unknown')
                    code_info = f"- {code_change.agent_id} modified {file_path}: {code_change.content[:100]}...\n"
                    code_summary += code_info
                    sources.append({
                        "type": "code_change",
                        "file_path": file_path,
                        "agent_id": code_change.agent_id,
                        "timestamp": code_change.timestamp.isoformat()
                    })
                
                context_parts.append(code_summary)
                tokens_used = len(code_summary) // 4
            
            return {
                "context": "\n".join(context_parts),
                "sources": sources,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "get_code_context"})
            return {"context": "", "sources": [], "tokens_used": 0}
    
    async def _get_system_context(self, request: ContextRequest, max_tokens: int) -> Dict[str, Any]:
        """Get system status context"""
        try:
            context_parts = []
            sources = []
            
            # Get project workspace status
            workspace = await project_workspace_manager.get_project(request.project_id)
            if workspace:
                status = await workspace.get_workspace_status()
                system_info = f"""
Project: {status.get('project_name', 'Unknown')}
Active Agents: {status.get('agents_count', 0)}
Active Tasks: {status.get('active_tasks', 0)}
Completed Tasks: {status.get('completed_tasks', 0)}
Active File Locks: {status.get('active_locks', 0)}
"""
                context_parts.append(system_info)
                sources.append({
                    "type": "system_status",
                    "project_id": request.project_id
                })
            
            tokens_used = sum(len(part) // 4 for part in context_parts)
            
            return {
                "context": "\n".join(context_parts),
                "sources": sources,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "get_system_context"})
            return {"context": "", "sources": [], "tokens_used": 0}
    
    def _generate_cache_key(self, request: ContextRequest, strategy: str) -> str:
        """Generate cache key for context request"""
        key_data = {
            "project_id": request.project_id,
            "agent_id": request.agent_id,
            "query": request.query,
            "strategy": strategy,
            "time_range": request.time_range,
            "content_types": sorted(request.content_types or []),
            "file_filter": request.file_filter
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def clear_cache(self, project_id: str = None, agent_id: str = None):
        """Clear context cache"""
        if not project_id and not agent_id:
            self.context_cache.clear()
        else:
            keys_to_remove = []
            for key in self.context_cache:
                if project_id and project_id not in key:
                    continue
                if agent_id and agent_id not in key:
                    continue
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.context_cache[key]
    
    async def get_context_summary(self, project_id: str) -> Dict[str, Any]:
        """Get summary of available context for a project"""
        try:
            # Get project workspace
            workspace = await project_workspace_manager.get_project(project_id)
            workspace_status = await workspace.get_workspace_status() if workspace else {}
            
            # Get task statistics
            project_tasks = await task_hierarchy_manager.get_project_tasks(project_id)
            task_stats = {
                "total": len(project_tasks),
                "by_status": {},
                "by_priority": {},
                "by_type": {}
            }
            
            for task in project_tasks:
                task_stats["by_status"][task.status.value] = task_stats["by_status"].get(task.status.value, 0) + 1
                task_stats["by_priority"][task.priority.value] = task_stats["by_priority"].get(task.priority.value, 0) + 1
                task_stats["by_type"][task.task_type.value] = task_stats["by_type"].get(task.task_type.value, 0) + 1
            
            # Get interaction statistics
            recent_interactions = await interaction_logger.get_project_timeline(
                project_id=project_id,
                start_time=datetime.now() - timedelta(days=7)
            )
            
            interaction_stats = {
                "total_week": len(recent_interactions),
                "by_type": {},
                "by_agent": {}
            }
            
            for interaction in recent_interactions:
                interaction_stats["by_type"][interaction.interaction_type.value] = interaction_stats["by_type"].get(interaction.interaction_type.value, 0) + 1
                interaction_stats["by_agent"][interaction.agent_id] = interaction_stats["by_agent"].get(interaction.agent_id, 0) + 1
            
            return {
                "project_id": project_id,
                "workspace_status": workspace_status,
                "task_statistics": task_stats,
                "interaction_statistics": interaction_stats,
                "context_availability": {
                    "rag_context": True,
                    "task_context": len(project_tasks) > 0,
                    "collaboration_context": len(recent_interactions) > 0,
                    "system_context": bool(workspace_status)
                },
                "cache_size": len(self.context_cache),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_context_summary",
                "project_id": project_id
            })
            return {"error": str(e)}


# Global instance
advanced_context_manager = AdvancedContextManager()