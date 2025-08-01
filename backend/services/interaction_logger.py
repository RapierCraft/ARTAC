"""
ARTAC Interaction Logger
Comprehensive logging and tracing system for multi-agent interactions
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from core.config import settings
from core.logging import get_logger
from core.database_postgres import db

logger = get_logger(__name__)


class InteractionType(Enum):
    """Types of agent interactions"""
    CODE_EDIT = "code_edit"
    COMMAND_EXEC = "command_exec"
    COMMUNICATION = "communication"
    DEBUGGING = "debugging"
    TASK_ASSIGNMENT = "task_assignment"
    MERGE_REQUEST = "merge_request"
    REVIEW = "review"
    COLLABORATION = "collaboration"
    SYSTEM_EVENT = "system_event"


class LogLevel(Enum):
    """Log levels for filtering"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class InteractionLog:
    """Structured interaction log entry"""
    id: str
    timestamp: datetime
    project_id: str
    agent_id: str
    interaction_type: InteractionType
    action: str
    content: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    level: LogLevel = LogLevel.INFO
    parent_interaction_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['interaction_type'] = self.interaction_type.value
        data['level'] = self.level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionLog':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['interaction_type'] = InteractionType(data['interaction_type'])
        data['level'] = LogLevel(data['level'])
        return cls(**data)


class ConversationTracker:
    """Tracks agent conversations and interactions"""
    
    def __init__(self):
        self.active_conversations: Dict[str, List[InteractionLog]] = {}
        self.conversation_metadata: Dict[str, Dict[str, Any]] = {}
    
    def start_conversation(self, participants: List[str], topic: str, project_id: str) -> str:
        """Start a new conversation thread"""
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        self.active_conversations[conversation_id] = []
        self.conversation_metadata[conversation_id] = {
            "participants": participants,
            "topic": topic,
            "project_id": project_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        logger.log_system_event("conversation_started", {
            "conversation_id": conversation_id,
            "participants": participants,
            "topic": topic,
            "project_id": project_id
        })
        
        return conversation_id
    
    def add_message(self, conversation_id: str, log_entry: InteractionLog):
        """Add a message to conversation"""
        if conversation_id in self.active_conversations:
            self.active_conversations[conversation_id].append(log_entry)
    
    def get_conversation(self, conversation_id: str) -> Optional[List[InteractionLog]]:
        """Get conversation history"""
        return self.active_conversations.get(conversation_id)
    
    def end_conversation(self, conversation_id: str, summary: str = ""):
        """End a conversation"""
        if conversation_id in self.conversation_metadata:
            self.conversation_metadata[conversation_id]["status"] = "ended"
            self.conversation_metadata[conversation_id]["ended_at"] = datetime.utcnow().isoformat()
            self.conversation_metadata[conversation_id]["summary"] = summary


class InteractionLogger:
    """Advanced interaction logging system"""
    
    def __init__(self):
        self.conversation_tracker = ConversationTracker()
        self.session_logs: Dict[str, List[InteractionLog]] = {}
        
        # Initialize database tables after startup
        self._db_initialized = False
    
    async def _initialize_database(self):
        """Initialize PostgreSQL database for interaction logs"""
        try:
            table_definitions = {
                "interactions": """
                    CREATE TABLE IF NOT EXISTS interactions (
                        id TEXT PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        project_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        action TEXT NOT NULL,
                        content TEXT,
                        context JSONB,
                        metadata JSONB,
                        level TEXT NOT NULL,
                        parent_interaction_id TEXT,
                        session_id TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "conversations": """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        participants TEXT[] NOT NULL,
                        topic TEXT,
                        project_id TEXT NOT NULL,
                        started_at TIMESTAMPTZ NOT NULL,
                        ended_at TIMESTAMPTZ,
                        status TEXT DEFAULT 'active',
                        summary TEXT,
                        metadata JSONB
                    )
                """,
                "file_changes": """
                    CREATE TABLE IF NOT EXISTS file_changes (
                        id TEXT PRIMARY KEY,
                        interaction_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        change_type TEXT NOT NULL,
                        line_start INTEGER,
                        line_end INTEGER,
                        old_content TEXT,
                        new_content TEXT,
                        diff TEXT,
                        commit_hash TEXT,
                        timestamp TIMESTAMPTZ NOT NULL,
                        FOREIGN KEY (interaction_id) REFERENCES interactions (id)
                    )
                """
            }
            
            # Create tables
            await db.create_tables_if_not_exist(table_definitions)
            
            # Create indexes for performance
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_project_agent ON interactions(project_id, agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_file_changes_interaction ON file_changes(interaction_id)"
            ]
            
            for index_query in index_queries:
                try:
                    await db.execute(index_query)
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            logger.log_system_event("interaction_logger_initialized", {
                "database": "PostgreSQL"
            })
            
            self._db_initialized = True
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_interaction_database"})
    
    async def _ensure_database_initialized(self):
        """Ensure database is initialized before use"""
        if not self._db_initialized and db.is_connected:
            await self._initialize_database()
    
    async def log_interaction(
        self,
        project_id: str,
        agent_id: str,
        interaction_type: InteractionType,
        action: str,
        content: str = "",
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        level: LogLevel = LogLevel.INFO,
        parent_interaction_id: str = None,
        session_id: str = None
    ) -> str:
        """Log an agent interaction"""
        try:
            await self._ensure_database_initialized()
            interaction_id = f"int_{uuid.uuid4().hex[:12]}"
            
            log_entry = InteractionLog(
                id=interaction_id,
                timestamp=datetime.utcnow(),
                project_id=project_id,
                agent_id=agent_id,
                interaction_type=interaction_type,
                action=action,
                content=content,
                context=context or {},
                metadata=metadata or {},
                level=level,
                parent_interaction_id=parent_interaction_id,
                session_id=session_id
            )
            
            # Store in database
            await self._store_interaction(log_entry)
            
            # Add to session logs
            if session_id:
                if session_id not in self.session_logs:
                    self.session_logs[session_id] = []
                self.session_logs[session_id].append(log_entry)
            
            # Log system event for critical interactions
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                logger.log_system_event("critical_interaction", {
                    "interaction_id": interaction_id,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "action": action,
                    "level": level.value
                })
            
            return interaction_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "log_interaction",
                "project_id": project_id,
                "agent_id": agent_id
            })
            return ""
    
    async def log_code_change(
        self,
        interaction_id: str,
        file_path: str,
        change_type: str,
        old_content: str = "",
        new_content: str = "",
        line_start: int = None,
        line_end: int = None,
        commit_hash: str = ""
    ):
        """Log a code change with detailed diff information"""
        try:
            change_id = f"change_{uuid.uuid4().hex[:8]}"
            
            # Generate diff
            diff = self._generate_diff(old_content, new_content)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO file_changes 
                    (id, interaction_id, file_path, change_type, line_start, line_end, 
                     old_content, new_content, diff, commit_hash, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change_id, interaction_id, file_path, change_type,
                    line_start, line_end, old_content, new_content,
                    diff, commit_hash, datetime.utcnow().isoformat()
                ))
                await db.commit()
            
            logger.log_system_event("code_change_logged", {
                "change_id": change_id,
                "interaction_id": interaction_id,
                "file_path": file_path,
                "change_type": change_type
            })
            
        except Exception as e:
            logger.log_error(e, {
                "action": "log_code_change",
                "interaction_id": interaction_id,
                "file_path": file_path
            })
    
    async def log_communication(
        self,
        project_id: str,
        from_agent: str,
        to_agent: str,
        message: str,
        communication_type: str = "direct",
        conversation_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Log inter-agent communication"""
        context = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "communication_type": communication_type,
            "conversation_id": conversation_id
        }
        
        interaction_id = await self.log_interaction(
            project_id=project_id,
            agent_id=from_agent,
            interaction_type=InteractionType.COMMUNICATION,
            action="send_message",
            content=message,
            context=context,
            metadata=metadata or {}
        )
        
        # Add to conversation if specified
        if conversation_id:
            log_entry = await self.get_interaction(interaction_id)
            if log_entry:
                self.conversation_tracker.add_message(conversation_id, log_entry)
        
        return interaction_id
    
    async def log_task_progress(
        self,
        project_id: str,
        agent_id: str,
        task_id: str,
        action: str,
        progress_data: Dict[str, Any],
        session_id: str = None
    ) -> str:
        """Log task progress and updates"""
        context = {
            "task_id": task_id,
            "progress_percentage": progress_data.get("progress_percentage", 0),
            "status": progress_data.get("status", "in_progress")
        }
        
        return await self.log_interaction(
            project_id=project_id,
            agent_id=agent_id,
            interaction_type=InteractionType.TASK_ASSIGNMENT,
            action=action,
            content=progress_data.get("description", ""),
            context=context,
            metadata=progress_data,
            session_id=session_id
        )
    
    async def get_interaction(self, interaction_id: str) -> Optional[InteractionLog]:
        """Get a specific interaction by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT * FROM interactions WHERE id = ?
                """, (interaction_id,))
                
                row = await cursor.fetchone()
                if row:
                    return self._row_to_interaction(row)
                
                return None
                
        except Exception as e:
            logger.log_error(e, {"action": "get_interaction", "interaction_id": interaction_id})
            return None
    
    async def get_agent_interactions(
        self,
        agent_id: str,
        project_id: str = None,
        interaction_type: InteractionType = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[InteractionLog]:
        """Get interactions for a specific agent"""
        try:
            query = "SELECT * FROM interactions WHERE agent_id = ?"
            params = [agent_id]
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            if interaction_type:
                query += " AND interaction_type = ?"
                params.append(interaction_type.value)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [self._row_to_interaction(row) for row in rows]
                
        except Exception as e:
            logger.log_error(e, {
                "action": "get_agent_interactions",
                "agent_id": agent_id
            })
            return []
    
    async def get_project_timeline(
        self,
        project_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
        agent_filter: List[str] = None,
        interaction_types: List[InteractionType] = None
    ) -> List[InteractionLog]:
        """Get project timeline with all interactions"""
        try:
            query = "SELECT * FROM interactions WHERE project_id = $1"
            params = [project_id]
            param_count = 1
            
            if start_time:
                param_count += 1
                query += f" AND timestamp >= ${param_count}"
                params.append(start_time)
            
            if end_time:
                param_count += 1
                query += f" AND timestamp <= ${param_count}"
                params.append(end_time)
            
            if agent_filter:
                param_count += 1
                query += f" AND agent_id = ANY(${param_count})"
                params.append(agent_filter)
            
            if interaction_types:
                param_count += 1
                query += f" AND interaction_type = ANY(${param_count})"
                params.append([t.value for t in interaction_types])
            
            query += " ORDER BY timestamp ASC"
            
            rows = await db.fetch_all(query, *params)
            return [self._row_to_interaction(row) for row in rows]
                
        except Exception as e:
            logger.log_error(e, {
                "action": "get_project_timeline",
                "project_id": project_id
            })
            return []
    
    async def get_session_logs(self, session_id: str) -> List[InteractionLog]:
        """Get all logs for a specific session"""
        if session_id in self.session_logs:
            return self.session_logs[session_id]
        
        # Fallback to database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT * FROM interactions WHERE session_id = ? ORDER BY timestamp ASC
                """, (session_id,))
                
                rows = await cursor.fetchall()
                return [self._row_to_interaction(row) for row in rows]
                
        except Exception as e:
            logger.log_error(e, {"action": "get_session_logs", "session_id": session_id})
            return []
    
    async def get_file_change_history(self, file_path: str, project_id: str = None) -> List[Dict[str, Any]]:
        """Get change history for a specific file"""
        try:
            query = """
                SELECT fc.*, i.agent_id, i.timestamp, i.action 
                FROM file_changes fc
                JOIN interactions i ON fc.interaction_id = i.id
                WHERE fc.file_path = ?
            """
            params = [file_path]
            
            if project_id:
                query += " AND i.project_id = ?"
                params.append(project_id)
            
            query += " ORDER BY fc.timestamp DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                changes = []
                for row in rows:
                    changes.append({
                        "id": row[0],
                        "interaction_id": row[1],
                        "file_path": row[2],
                        "change_type": row[3],
                        "line_start": row[4],
                        "line_end": row[5],
                        "old_content": row[6],
                        "new_content": row[7],
                        "diff": row[8],
                        "commit_hash": row[9],
                        "timestamp": row[10],
                        "agent_id": row[11],
                        "action": row[13]
                    })
                
                return changes
                
        except Exception as e:
            logger.log_error(e, {
                "action": "get_file_change_history",
                "file_path": file_path
            })
            return []
    
    async def search_interactions(
        self,
        query: str,
        project_id: str = None,
        agent_id: str = None,
        limit: int = 50
    ) -> List[InteractionLog]:
        """Search interactions by content"""
        try:
            sql_query = """
                SELECT * FROM interactions 
                WHERE (content LIKE ? OR action LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if project_id:
                sql_query += " AND project_id = ?"
                params.append(project_id)
            
            if agent_id:
                sql_query += " AND agent_id = ?"
                params.append(agent_id)
            
            sql_query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(sql_query, params)
                rows = await cursor.fetchall()
                
                return [self._row_to_interaction(row) for row in rows]
                
        except Exception as e:
            logger.log_error(e, {
                "action": "search_interactions",
                "query": query
            })
            return []
    
    async def _store_interaction(self, log_entry: InteractionLog):
        """Store interaction in PostgreSQL database"""
        try:
            await db.execute("""
                INSERT INTO interactions 
                (id, timestamp, project_id, agent_id, interaction_type, action, 
                 content, context, metadata, level, parent_interaction_id, session_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, 
                log_entry.id,
                log_entry.timestamp,
                log_entry.project_id,
                log_entry.agent_id,
                log_entry.interaction_type.value,
                log_entry.action,
                log_entry.content,
                json.dumps(log_entry.context) if log_entry.context else "{}",
                json.dumps(log_entry.metadata) if log_entry.metadata else "{}",
                log_entry.level.value,
                log_entry.parent_interaction_id,
                log_entry.session_id
            )
                
        except Exception as e:
            logger.log_error(e, {"action": "store_interaction"})
    
    def _row_to_interaction(self, row) -> InteractionLog:
        """Convert PostgreSQL row to InteractionLog"""
        return InteractionLog(
            id=row['id'],
            timestamp=row['timestamp'],
            project_id=row['project_id'],
            agent_id=row['agent_id'],
            interaction_type=InteractionType(row['interaction_type']),
            action=row['action'],
            content=row['content'] or "",
            context=row['context'] if row['context'] else {},  # PostgreSQL handles JSON directly
            metadata=row['metadata'] if row['metadata'] else {},  # PostgreSQL handles JSON directly
            level=LogLevel(row['level']),
            parent_interaction_id=row['parent_interaction_id'],
            session_id=row['session_id']
        )
    
    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """Generate simple diff between old and new content"""
        try:
            import difflib
            
            old_lines = old_content.splitlines() if old_content else []
            new_lines = new_content.splitlines() if new_content else []
            
            diff = list(difflib.unified_diff(
                old_lines,
                new_lines,
                lineterm='',
                n=3
            ))
            
            return '\n'.join(diff)
            
        except Exception:
            return f"Old: {len(old_content)} chars, New: {len(new_content)} chars"


# Global instance
interaction_logger = InteractionLogger()