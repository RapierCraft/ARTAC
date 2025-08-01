"""
ARTAC RAG Context Manager
Advanced context management system with vector embeddings for multi-agent collaboration
"""

import asyncio
import json
import os
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
import numpy as np
import sqlite3
import aiosqlite
from pathlib import Path
import hashlib
import re

# Vector embeddings and similarity
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers and faiss not available. Using fallback text similarity.")

from core.config import settings
from core.logging import get_logger
from services.interaction_logger import interaction_logger, InteractionType

logger = get_logger(__name__)


@dataclass
class ContextEntry:
    """Context entry with metadata"""
    id: str
    project_id: str
    agent_id: str
    content: str
    content_type: str  # code, docs, conversation, task, error, etc.
    file_path: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEntry':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'embedding' in data and data['embedding']:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)


class FallbackEmbedder:
    """Fallback embedder when sentence-transformers is not available"""
    
    def __init__(self):
        self.dimension = 384  # Typical dimension for sentence transformers
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate simple hash-based embeddings"""
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to fixed-size embedding
            embedding = np.zeros(self.dimension)
            for i, byte in enumerate(hash_bytes[:min(len(hash_bytes), self.dimension)]):
                embedding[i] = byte / 255.0
            
            # Add some text-based features
            words = text.lower().split()
            if words:
                embedding[0] = min(len(words) / 100.0, 1.0)  # Normalized word count
                embedding[1] = min(len(text) / 1000.0, 1.0)  # Normalized char count
                
                # Simple word frequency features
                word_counts = {}
                for word in words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                
                # Use top words to influence embedding
                for i, (word, count) in enumerate(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]):
                    if i + 2 < self.dimension:
                        embedding[i + 2] = min(count / len(words), 1.0)
            
            embeddings.append(embedding)
        
        return np.array(embeddings)


class VectorStore:
    """Vector storage and similarity search"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.context_entries: Dict[str, ContextEntry] = {}
        
        if EMBEDDINGS_AVAILABLE:
            # Initialize FAISS index
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        else:
            # Fallback to simple storage
            self.vectors: Dict[str, np.ndarray] = {}
    
    def add_vector(self, entry_id: str, vector: np.ndarray, context_entry: ContextEntry):
        """Add a vector to the store"""
        if EMBEDDINGS_AVAILABLE and self.index is not None:
            # Normalize vector for cosine similarity
            normalized_vector = vector / np.linalg.norm(vector)
            
            # Add to FAISS index
            current_index = self.index.ntotal
            self.index.add(normalized_vector.reshape(1, -1))
            
            # Update mappings
            self.id_to_index[entry_id] = current_index
            self.index_to_id[current_index] = entry_id
        else:
            # Fallback storage
            self.vectors[entry_id] = vector
        
        self.context_entries[entry_id] = context_entry
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors"""
        if EMBEDDINGS_AVAILABLE and self.index is not None:
            # Normalize query vector
            normalized_query = query_vector / np.linalg.norm(query_vector)
            
            # Search FAISS index
            scores, indices = self.index.search(normalized_query.reshape(1, -1), k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx in self.index_to_id:
                    entry_id = self.index_to_id[idx]
                    results.append((entry_id, float(score)))
            
            return results
        else:
            # Fallback similarity search
            results = []
            
            for entry_id, vector in self.vectors.items():
                # Simple cosine similarity
                similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
                results.append((entry_id, float(similarity)))
            
            # Sort by similarity
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:k]
    
    def get_entry(self, entry_id: str) -> Optional[ContextEntry]:
        """Get context entry by ID"""
        return self.context_entries.get(entry_id)
    
    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry from the store"""
        if entry_id in self.context_entries:
            del self.context_entries[entry_id]
            
            if entry_id in self.vectors:
                del self.vectors[entry_id]
            
            # Note: FAISS doesn't support efficient removal, so we'd need to rebuild for production
            return True
        
        return False


class RAGContextManager:
    """Advanced RAG-based context management system"""
    
    def __init__(self):
        self.db_path = os.path.join(settings.DATA_ROOT, "rag", "context.db")
        self.vector_stores: Dict[str, VectorStore] = {}  # project_id -> VectorStore
        
        # Initialize embedder
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = self.embedder.get_sentence_embedding_dimension()
            except Exception as e:
                logger.log_error(e, {"action": "initialize_sentence_transformer"})
                self.embedder = FallbackEmbedder()
                self.dimension = self.embedder.dimension
        else:
            self.embedder = FallbackEmbedder()
            self.dimension = self.embedder.dimension
        
        # Ensure RAG directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database - delay async initialization
        self._db_initialized = False
        self._initialization_lock = None
    
    async def _ensure_initialized(self):
        """Ensure the RAG context manager is properly initialized with async components"""
        if self._db_initialized:
            return
            
        if self._initialization_lock is None:
            import asyncio
            self._initialization_lock = asyncio.Lock()
            
        async with self._initialization_lock:
            if not self._db_initialized:
                await self._initialize_database()
                self._db_initialized = True
    
    async def _initialize_database(self):
        """Initialize SQLite database for context storage"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create context entries table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS context_entries (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        file_path TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        embedding BLOB,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                await db.execute("CREATE INDEX IF NOT EXISTS idx_project_agent ON context_entries(project_id, agent_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON context_entries(content_type)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON context_entries(timestamp)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON context_entries(file_path)")
                
                # Create agent memory table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_memory (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        key_name TEXT NOT NULL,
                        value_data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires_at TEXT,
                        metadata TEXT,
                        UNIQUE(project_id, agent_id, memory_type, key_name)
                    )
                """)
                
                await db.commit()
                
            logger.log_system_event("rag_context_manager_initialized", {
                "db_path": self.db_path,
                "embedder_type": type(self.embedder).__name__,
                "dimension": self.dimension
            })
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_rag_database"})
    
    def _get_vector_store(self, project_id: str) -> VectorStore:
        """Get or create vector store for project"""
        if project_id not in self.vector_stores:
            self.vector_stores[project_id] = VectorStore(self.dimension)
        return self.vector_stores[project_id]
    
    async def add_context(
        self,
        project_id: str,
        agent_id: str,
        content: str,
        content_type: str,
        file_path: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add context entry with automatic embedding"""
        try:
            await self._ensure_initialized()
            entry_id = f"ctx_{uuid.uuid4().hex[:12]}"
            
            # Generate embedding
            embedding = self.embedder.encode([content])[0]
            
            # Create context entry
            context_entry = ContextEntry(
                id=entry_id,
                project_id=project_id,
                agent_id=agent_id,
                content=content,
                content_type=content_type,
                file_path=file_path,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                embedding=embedding
            )
            
            # Store in vector store
            vector_store = self._get_vector_store(project_id)
            vector_store.add_vector(entry_id, embedding, context_entry)
            
            # Store in database
            await self._store_context_entry(context_entry)
            
            # Log context addition
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="context_added",
                content=f"Added {content_type} context",
                context={
                    "context_id": entry_id,
                    "content_type": content_type,
                    "file_path": file_path,
                    "content_length": len(content)
                },
                metadata=metadata or {}
            )
            
            return entry_id
            
        except Exception as e:
            logger.log_error(e, {
                "action": "add_context",
                "project_id": project_id,
                "agent_id": agent_id,
                "content_type": content_type
            })
            return ""
    
    async def get_context(
        self,
        project_id: str,
        agent_id: str,
        query: str,
        max_tokens: int = 180000,
        include_history: bool = True,
        time_range: str = "all",
        content_types: List[str] = None,
        file_filter: str = None
    ) -> Dict[str, Any]:
        """Get relevant context for an agent query"""
        try:
            await self._ensure_initialized()
            # Generate query embedding
            query_embedding = self.embedder.encode([query])[0]
            
            # Search vector store
            vector_store = self._get_vector_store(project_id)
            similar_entries = vector_store.search(query_embedding, k=50)
            
            # Filter and rank results
            filtered_results = await self._filter_context_results(
                similar_entries,
                agent_id,
                time_range,
                content_types,
                file_filter,
                include_history
            )
            
            # Build context within token limit
            context_data = await self._build_context_response(
                filtered_results,
                max_tokens,
                query
            )
            
            # Log context retrieval
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="context_retrieved",
                content=f"Retrieved context for query: {query[:100]}...",
                context={
                    "query": query,
                    "results_count": len(filtered_results),
                    "tokens_used": context_data.get("tokens_used", 0),
                    "time_range": time_range
                },
                metadata={
                    "content_types": content_types,
                    "file_filter": file_filter,
                    "include_history": include_history
                }
            )
            
            return context_data
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_context",
                "project_id": project_id,
                "agent_id": agent_id,
                "query": query[:100]
            })
            return {"error": str(e), "context": "", "sources": []}
    
    async def add_code_context(
        self,
        project_id: str,
        agent_id: str,
        file_path: str,
        code_content: str,
        change_type: str = "modification",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add code-specific context with enhanced metadata"""
        try:
            # Extract code features
            code_metadata = self._extract_code_features(code_content, file_path)
            if metadata:
                code_metadata.update(metadata)
            
            code_metadata["change_type"] = change_type
            
            # Create enhanced content with context
            enhanced_content = f"""
File: {file_path}
Change Type: {change_type}
Code:
{code_content}
"""
            
            return await self.add_context(
                project_id=project_id,
                agent_id=agent_id,
                content=enhanced_content,
                content_type="code",
                file_path=file_path,
                metadata=code_metadata
            )
            
        except Exception as e:
            logger.log_error(e, {
                "action": "add_code_context",
                "project_id": project_id,
                "file_path": file_path
            })
            return ""
    
    async def add_conversation_context(
        self,
        project_id: str,
        from_agent: str,
        to_agent: str,
        message: str,
        conversation_type: str = "direct",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add conversation context"""
        conversation_metadata = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "conversation_type": conversation_type
        }
        if metadata:
            conversation_metadata.update(metadata)
        
        enhanced_content = f"""
Conversation between {from_agent} and {to_agent}
Type: {conversation_type}
Message: {message}
"""
        
        return await self.add_context(
            project_id=project_id,
            agent_id=from_agent,
            content=enhanced_content,
            content_type="conversation",
            metadata=conversation_metadata
        )
    
    async def add_error_context(
        self,
        project_id: str,
        agent_id: str,
        error_message: str,
        stack_trace: str = "",
        file_path: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add error context for debugging"""
        error_metadata = {
            "error_type": self._extract_error_type(error_message),
            "has_stack_trace": bool(stack_trace),
            "error_severity": self._classify_error_severity(error_message)
        }
        if metadata:
            error_metadata.update(metadata)
        
        enhanced_content = f"""
Error in {file_path or 'unknown file'}
Error: {error_message}
Stack Trace:
{stack_trace}
"""
        
        return await self.add_context(
            project_id=project_id,
            agent_id=agent_id,
            content=enhanced_content,
            content_type="error",
            file_path=file_path,
            metadata=error_metadata
        )
    
    async def store_agent_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_type: str,
        key: str,
        value: Any,
        expires_at: datetime = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store agent-specific memory"""
        try:
            memory_id = f"mem_{uuid.uuid4().hex[:8]}"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO agent_memory 
                    (id, project_id, agent_id, memory_type, key_name, value_data, timestamp, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_id,
                    project_id,
                    agent_id,
                    memory_type,
                    key,
                    json.dumps(value),
                    datetime.utcnow().isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    json.dumps(metadata or {})
                ))
                await db.commit()
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "store_agent_memory",
                "project_id": project_id,
                "agent_id": agent_id,
                "memory_type": memory_type
            })
            return False
    
    async def get_agent_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_type: str,
        key: str = None
    ) -> Dict[str, Any]:
        """Retrieve agent memory"""
        try:
            query = """
                SELECT key_name, value_data, timestamp, expires_at, metadata 
                FROM agent_memory 
                WHERE project_id = ? AND agent_id = ? AND memory_type = ?
            """
            params = [project_id, agent_id, memory_type]
            
            if key:
                query += " AND key_name = ?"
                params.append(key)
            
            query += " ORDER BY timestamp DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                memory_data = {}
                for row in rows:
                    key_name, value_data, timestamp, expires_at, metadata = row
                    
                    # Check expiration
                    if expires_at:
                        expiry_time = datetime.fromisoformat(expires_at)
                        if datetime.utcnow() > expiry_time:
                            continue
                    
                    memory_data[key_name] = {
                        "value": json.loads(value_data),
                        "timestamp": timestamp,
                        "expires_at": expires_at,
                        "metadata": json.loads(metadata) if metadata else {}
                    }
                
                return memory_data
                
        except Exception as e:
            logger.log_error(e, {
                "action": "get_agent_memory",
                "project_id": project_id,
                "agent_id": agent_id,
                "memory_type": memory_type
            })
            return {}
    
    async def search_context(
        self,
        project_id: str,
        query: str,
        agent_filter: List[str] = None,
        content_types: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search context entries"""
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query])[0]
            
            # Search vector store
            vector_store = self._get_vector_store(project_id)
            similar_entries = vector_store.search(query_embedding, k=limit * 2)
            
            # Filter results
            filtered_results = []
            for entry_id, similarity in similar_entries:
                entry = vector_store.get_entry(entry_id)
                if entry:
                    # Apply filters
                    if agent_filter and entry.agent_id not in agent_filter:
                        continue
                    if content_types and entry.content_type not in content_types:
                        continue
                    
                    filtered_results.append({
                        "id": entry.id,
                        "content": entry.content,
                        "content_type": entry.content_type,
                        "agent_id": entry.agent_id,
                        "file_path": entry.file_path,
                        "timestamp": entry.timestamp.isoformat(),
                        "similarity": similarity,
                        "metadata": entry.metadata
                    })
                
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results
            
        except Exception as e:
            logger.log_error(e, {
                "action": "search_context",
                "project_id": project_id,
                "query": query[:100]
            })
            return []
    
    async def _store_context_entry(self, context_entry: ContextEntry):
        """Store context entry in database"""
        try:
            # Serialize embedding
            embedding_blob = pickle.dumps(context_entry.embedding) if context_entry.embedding is not None else None
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO context_entries 
                    (id, project_id, agent_id, content, content_type, file_path, timestamp, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    context_entry.id,
                    context_entry.project_id,
                    context_entry.agent_id,
                    context_entry.content,
                    context_entry.content_type,
                    context_entry.file_path,
                    context_entry.timestamp.isoformat(),
                    json.dumps(context_entry.metadata),
                    embedding_blob
                ))
                await db.commit()
                
        except Exception as e:
            logger.log_error(e, {"action": "store_context_entry"})
    
    async def _filter_context_results(
        self,
        similar_entries: List[Tuple[str, float]],
        agent_id: str,
        time_range: str,
        content_types: List[str],
        file_filter: str,
        include_history: bool
    ) -> List[Tuple[ContextEntry, float]]:
        """Filter context search results"""
        filtered_results = []
        
        # Calculate time bounds
        now = datetime.utcnow()
        time_bounds = {
            "last_hour": now - timedelta(hours=1),
            "last_day": now - timedelta(days=1),
            "last_week": now - timedelta(weeks=1),
            "last_month": now - timedelta(days=30),
            "all": None
        }
        time_bound = time_bounds.get(time_range)
        
        vector_store = self._get_vector_store(similar_entries[0][0] if similar_entries else "")
        
        for entry_id, similarity in similar_entries:
            entry = vector_store.get_entry(entry_id)
            if not entry:
                continue
            
            # Time filter
            if time_bound and entry.timestamp < time_bound:
                continue
            
            # Content type filter
            if content_types and entry.content_type not in content_types:
                continue
            
            # File filter
            if file_filter and entry.file_path and file_filter not in entry.file_path:
                continue
            
            # Agent history filter
            if not include_history and entry.agent_id != agent_id:
                continue
            
            filtered_results.append((entry, similarity))
        
        return filtered_results
    
    async def _build_context_response(
        self,
        filtered_results: List[Tuple[ContextEntry, float]],
        max_tokens: int,
        query: str
    ) -> Dict[str, Any]:
        """Build context response within token limits"""
        context_parts = []
        sources = []
        total_tokens = 0
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        def estimate_tokens(text: str) -> int:
            return len(text) // 4
        
        # Add query context
        query_context = f"Query: {query}\n\nRelevant Context:\n\n"
        context_parts.append(query_context)
        total_tokens += estimate_tokens(query_context)
        
        # Add most relevant entries
        for entry, similarity in filtered_results:
            entry_text = f"[{entry.content_type.upper()}] {entry.file_path or 'Unknown'}\n"
            entry_text += f"Agent: {entry.agent_id} | Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            entry_text += f"Similarity: {similarity:.3f}\n"
            entry_text += f"Content:\n{entry.content}\n\n---\n\n"
            
            entry_tokens = estimate_tokens(entry_text)
            
            if total_tokens + entry_tokens > max_tokens:
                break
            
            context_parts.append(entry_text)
            total_tokens += entry_tokens
            
            sources.append({
                "id": entry.id,
                "content_type": entry.content_type,
                "file_path": entry.file_path,
                "agent_id": entry.agent_id,
                "timestamp": entry.timestamp.isoformat(),
                "similarity": similarity,
                "metadata": entry.metadata
            })
        
        return {
            "context": "".join(context_parts),
            "sources": sources,
            "tokens_used": total_tokens,
            "query": query,
            "results_count": len(sources)
        }
    
    def _extract_code_features(self, code_content: str, file_path: str) -> Dict[str, Any]:
        """Extract features from code content"""
        features = {
            "language": self._detect_language(file_path),
            "lines_count": len(code_content.split('\n')),
            "chars_count": len(code_content),
            "has_functions": bool(re.search(r'\b(def|function|func)\s+\w+', code_content)),
            "has_classes": bool(re.search(r'\b(class|interface)\s+\w+', code_content)),
            "has_imports": bool(re.search(r'\b(import|from|require|include)\s+', code_content)),
            "has_comments": bool(re.search(r'(//|#|/\*|\*|<!--)', code_content))
        }
        
        # Extract keywords
        keywords = re.findall(r'\b(if|else|for|while|try|catch|async|await|return)\b', code_content.lower())
        features["keywords"] = list(set(keywords))
        
        return features
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        return language_map.get(ext, 'unknown')
    
    def _extract_error_type(self, error_message: str) -> str:
        """Extract error type from error message"""
        error_patterns = {
            'syntax': r'(syntax|parse|unexpected token)',
            'type': r'(type|attribute|undefined)',
            'runtime': r'(runtime|execution|null|reference)',
            'import': r'(import|module|not found)',
            'permission': r'(permission|access|denied|unauthorized)'
        }
        
        error_message_lower = error_message.lower()
        for error_type, pattern in error_patterns.items():
            if re.search(pattern, error_message_lower):
                return error_type
        
        return 'unknown'
    
    def _classify_error_severity(self, error_message: str) -> str:
        """Classify error severity"""
        error_message_lower = error_message.lower()
        
        if any(word in error_message_lower for word in ['critical', 'fatal', 'crash', 'abort']):
            return 'critical'
        elif any(word in error_message_lower for word in ['error', 'exception', 'fail']):
            return 'error'
        elif any(word in error_message_lower for word in ['warning', 'warn', 'deprecated']):
            return 'warning'
        else:
            return 'info'


# Global instance
rag_context_manager = RAGContextManager()