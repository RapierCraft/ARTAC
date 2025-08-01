"""
ARTAC Stateless RAG Manager
Ultra-scalable RAG system that can handle unlimited context through stateless optimization
"""

import asyncio
import json
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict
import heapq

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from core.config import settings
from core.logging import get_logger
from core.database_postgres import db
from services.interaction_logger import interaction_logger, InteractionType

logger = get_logger(__name__)


class ChunkType(Enum):
    """Types of content chunks"""
    CODE_FUNCTION = "code_function"
    CODE_CLASS = "code_class" 
    CODE_FILE = "code_file"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    TASK_DESCRIPTION = "task_description"
    ERROR_LOG = "error_log"
    COMMIT_MESSAGE = "commit_message"
    SUMMARY = "summary"
    META_SUMMARY = "meta_summary"


class RelevanceScore(Enum):
    """Relevance scoring levels"""
    CRITICAL = 1.0      # Must include
    HIGH = 0.8          # Very relevant
    MEDIUM = 0.6        # Somewhat relevant
    LOW = 0.4           # Marginally relevant
    MINIMAL = 0.2       # Background context


@dataclass
class ContentChunk:
    """Optimized content chunk for stateless RAG"""
    id: str
    project_id: str
    agent_id: str
    content: str
    chunk_type: ChunkType
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray]
    timestamp: datetime
    parent_chunk_id: Optional[str]
    child_chunk_ids: List[str]
    summary: str
    keywords: List[str]
    relationships: Dict[str, List[str]]  # Related chunk IDs by relationship type
    access_count: int
    last_accessed: datetime
    relevance_scores: Dict[str, float]  # Context-specific relevance scores
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['chunk_type'] = self.chunk_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data
    
    def get_token_count(self) -> int:
        """Estimate token count for this chunk"""
        return max(len(self.content) // 4, len(self.summary) // 4)


@dataclass
class ContextSummary:
    """Hierarchical context summary for compression"""
    id: str
    level: int  # 0=leaf, 1=branch, 2=root
    content: str
    chunk_ids: List[str]
    children_summary_ids: List[str]
    token_count: int
    relevance_score: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


class StatelessContextOptimizer:
    """Optimizes context selection using stateless algorithms"""
    
    def __init__(self):
        self.max_context_tokens = 180000  # Reserve 20k for response
        self.summary_compression_ratio = 0.3  # Summaries are 30% of original
        self.relevance_threshold = 0.4
    
    async def optimize_context_selection(
        self,
        query: str,
        candidate_chunks: List[ContentChunk],
        max_tokens: int,
        context_strategy: str = "hierarchical"
    ) -> Tuple[List[ContentChunk], List[ContextSummary], Dict[str, Any]]:
        """
        Optimize context selection to maximize relevance within token limits
        """
        try:
            if context_strategy == "hierarchical":
                return await self._hierarchical_optimization(query, candidate_chunks, max_tokens)
            elif context_strategy == "semantic_clustering":
                return await self._semantic_clustering_optimization(query, candidate_chunks, max_tokens)
            elif context_strategy == "temporal_priority":
                return await self._temporal_priority_optimization(query, candidate_chunks, max_tokens)
            else:
                return await self._hybrid_optimization(query, candidate_chunks, max_tokens)
                
        except Exception as e:
            logger.log_error(e, {"action": "optimize_context_selection"})
            return [], [], {"error": str(e)}
    
    async def _hierarchical_optimization(
        self,
        query: str,
        chunks: List[ContentChunk],
        max_tokens: int
    ) -> Tuple[List[ContentChunk], List[ContextSummary], Dict[str, Any]]:
        """Hierarchical context optimization with multi-level summarization"""
        
        # Step 1: Score all chunks for relevance
        scored_chunks = await self._score_chunk_relevance(query, chunks)
        
        # Step 2: Create hierarchical clusters
        clusters = await self._create_hierarchical_clusters(scored_chunks)
        
        # Step 3: Generate summaries at different levels
        summaries = await self._generate_hierarchical_summaries(clusters)
        
        # Step 4: Optimal selection using dynamic programming
        selected_chunks, selected_summaries = await self._optimal_selection_dp(
            scored_chunks, summaries, max_tokens
        )
        
        optimization_stats = {
            "strategy": "hierarchical",
            "total_candidates": len(chunks),
            "selected_chunks": len(selected_chunks),
            "selected_summaries": len(selected_summaries),
            "token_utilization": sum(c.get_token_count() for c in selected_chunks) / max_tokens,
            "avg_relevance": np.mean([c.relevance_scores.get("query", 0.5) for c in selected_chunks]) if selected_chunks else 0
        }
        
        return selected_chunks, selected_summaries, optimization_stats
    
    async def _semantic_clustering_optimization(
        self,
        query: str,
        chunks: List[ContentChunk],
        max_tokens: int
    ) -> Tuple[List[ContentChunk], List[ContextSummary], Dict[str, Any]]:
        """Semantic clustering with representative selection"""
        
        if not EMBEDDINGS_AVAILABLE or not chunks:
            return chunks[:10], [], {"strategy": "semantic_clustering", "fallback": True}
        
        # Extract embeddings
        embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if chunk.embedding is not None:
                embeddings.append(chunk.embedding)
                valid_chunks.append(chunk)
        
        if not embeddings:
            return chunks[:10], [], {"strategy": "semantic_clustering", "no_embeddings": True}
        
        embeddings_matrix = np.array(embeddings)
        
        # Perform clustering
        from sklearn.cluster import KMeans
        n_clusters = min(20, len(valid_chunks) // 5 + 1)
        
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_matrix)
        except:
            # Fallback if sklearn not available
            cluster_labels = np.arange(len(valid_chunks)) % n_clusters
        
        # Select representative chunks from each cluster
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append(valid_chunks[i])
        
        selected_chunks = []
        summaries = []
        current_tokens = 0
        
        # Sort clusters by relevance to query
        query_embedding = await self._get_query_embedding(query)
        cluster_relevance = []
        
        for cluster_id, cluster_chunks in clusters.items():
            if query_embedding is not None:
                cluster_center = np.mean([c.embedding for c in cluster_chunks], axis=0)
                relevance = np.dot(query_embedding, cluster_center) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(cluster_center)
                )
            else:
                relevance = np.random.random()  # Fallback
            
            cluster_relevance.append((relevance, cluster_id, cluster_chunks))
        
        cluster_relevance.sort(reverse=True)
        
        # Select best chunks from each cluster
        for relevance, cluster_id, cluster_chunks in cluster_relevance:
            if current_tokens >= max_tokens:
                break
            
            # Sort chunks in cluster by individual relevance
            cluster_chunks.sort(key=lambda x: x.relevance_scores.get("query", 0.5), reverse=True)
            
            # Take best chunks from cluster until token limit
            for chunk in cluster_chunks:
                chunk_tokens = chunk.get_token_count()
                if current_tokens + chunk_tokens <= max_tokens:
                    selected_chunks.append(chunk)
                    current_tokens += chunk_tokens
                else:
                    # Create summary for remaining chunks
                    remaining_chunks = cluster_chunks[len([c for c in cluster_chunks if c in selected_chunks]):]
                    if remaining_chunks:
                        summary = await self._create_cluster_summary(remaining_chunks, cluster_id)
                        summaries.append(summary)
                    break
        
        optimization_stats = {
            "strategy": "semantic_clustering",
            "clusters_created": n_clusters,
            "selected_chunks": len(selected_chunks),
            "cluster_summaries": len(summaries),
            "token_utilization": current_tokens / max_tokens
        }
        
        return selected_chunks, summaries, optimization_stats
    
    async def _temporal_priority_optimization(
        self,
        query: str,
        chunks: List[ContentChunk],
        max_tokens: int
    ) -> Tuple[List[ContentChunk], List[ContextSummary], Dict[str, Any]]:
        """Time-based priority with exponential decay"""
        
        current_time = datetime.now()
        
        # Calculate temporal scores with exponential decay
        for chunk in chunks:
            days_old = (current_time - chunk.timestamp).days
            temporal_score = np.exp(-days_old / 30)  # 30-day half-life
            
            # Boost recent activity
            days_since_access = (current_time - chunk.last_accessed).days
            recency_boost = np.exp(-days_since_access / 7)  # 7-day half-life
            
            chunk.relevance_scores["temporal"] = temporal_score * recency_boost
        
        # Sort by combined relevance and temporal score
        chunks.sort(key=lambda x: (
            x.relevance_scores.get("query", 0.5) * 0.7 + 
            x.relevance_scores.get("temporal", 0.3) * 0.3
        ), reverse=True)
        
        # Select chunks within token limit
        selected_chunks = []
        current_tokens = 0
        
        for chunk in chunks:
            chunk_tokens = chunk.get_token_count()
            if current_tokens + chunk_tokens <= max_tokens:
                selected_chunks.append(chunk)
                current_tokens += chunk_tokens
            else:
                break
        
        optimization_stats = {
            "strategy": "temporal_priority",
            "selected_chunks": len(selected_chunks),
            "token_utilization": current_tokens / max_tokens,
            "avg_temporal_score": np.mean([c.relevance_scores.get("temporal", 0) for c in selected_chunks]) if selected_chunks else 0
        }
        
        return selected_chunks, [], optimization_stats
    
    async def _hybrid_optimization(
        self,
        query: str,
        chunks: List[ContentChunk],
        max_tokens: int
    ) -> Tuple[List[ContentChunk], List[ContextSummary], Dict[str, Any]]:
        """Hybrid approach combining multiple strategies"""
        
        # Multi-criteria scoring
        current_time = datetime.now()
        
        for chunk in chunks:
            # Relevance score (from semantic similarity or keyword matching)
            relevance = chunk.relevance_scores.get("query", 0.5)
            
            # Temporal score
            days_old = (current_time - chunk.timestamp).days
            temporal = np.exp(-days_old / 14)  # 14-day half-life
            
            # Popularity score (access frequency)
            popularity = min(1.0, chunk.access_count / 10)
            
            # Content type importance
            type_weights = {
                ChunkType.CODE_FUNCTION: 1.0,
                ChunkType.CODE_CLASS: 0.9,
                ChunkType.TASK_DESCRIPTION: 0.8,
                ChunkType.ERROR_LOG: 0.8,
                ChunkType.DOCUMENTATION: 0.7,
                ChunkType.CONVERSATION: 0.6,
                ChunkType.SUMMARY: 0.5,
                ChunkType.CODE_FILE: 0.4,
                ChunkType.COMMIT_MESSAGE: 0.3,
                ChunkType.META_SUMMARY: 0.2
            }
            type_importance = type_weights.get(chunk.chunk_type, 0.5)
            
            # Relationship boost (connected to other relevant chunks)
            relationship_boost = len(chunk.relationships.get("related", [])) * 0.1
            
            # Combined score
            combined_score = (
                relevance * 0.4 +
                temporal * 0.2 +
                popularity * 0.1 +
                type_importance * 0.2 +
                relationship_boost * 0.1
            )
            
            chunk.relevance_scores["combined"] = combined_score
        
        # Sort by combined score
        chunks.sort(key=lambda x: x.relevance_scores.get("combined", 0), reverse=True)
        
        # Smart selection with diversity
        selected_chunks = []
        selected_types = set()
        current_tokens = 0
        
        # First pass: high-priority diverse content
        for chunk in chunks:
            if current_tokens >= max_tokens * 0.8:  # Reserve 20% for summaries
                break
                
            chunk_tokens = chunk.get_token_count()
            if current_tokens + chunk_tokens <= max_tokens * 0.8:
                # Encourage diversity
                if chunk.chunk_type not in selected_types or len(selected_chunks) < 5:
                    selected_chunks.append(chunk)
                    selected_types.add(chunk.chunk_type)
                    current_tokens += chunk_tokens
        
        # Second pass: create summaries for remaining high-value content
        summaries = []
        remaining_chunks = [c for c in chunks if c not in selected_chunks and c.relevance_scores.get("combined", 0) > 0.6]
        
        if remaining_chunks:
            # Group by type and create summaries
            type_groups = defaultdict(list)
            for chunk in remaining_chunks:
                type_groups[chunk.chunk_type].append(chunk)
            
            for chunk_type, type_chunks in type_groups.items():
                if len(type_chunks) >= 3:  # Only summarize if enough chunks
                    summary = await self._create_type_summary(type_chunks, chunk_type)
                    summaries.append(summary)
        
        optimization_stats = {
            "strategy": "hybrid",
            "selected_chunks": len(selected_chunks),
            "type_summaries": len(summaries),
            "content_diversity": len(selected_types),
            "token_utilization": current_tokens / max_tokens,
            "avg_combined_score": np.mean([c.relevance_scores.get("combined", 0) for c in selected_chunks]) if selected_chunks else 0
        }
        
        return selected_chunks, summaries, optimization_stats
    
    async def _score_chunk_relevance(self, query: str, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """Score chunks for relevance to query"""
        query_embedding = await self._get_query_embedding(query)
        query_keywords = query.lower().split()
        
        for chunk in chunks:
            scores = {}
            
            # Semantic similarity score
            if query_embedding is not None and chunk.embedding is not None:
                similarity = np.dot(query_embedding, chunk.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk.embedding)
                )
                scores["semantic"] = max(0, similarity)
            
            # Keyword matching score
            chunk_text = (chunk.content + " " + chunk.summary).lower()
            keyword_matches = sum(1 for keyword in query_keywords if keyword in chunk_text)
            scores["keyword"] = keyword_matches / len(query_keywords) if query_keywords else 0
            
            # Metadata relevance
            metadata_text = " ".join(str(v) for v in chunk.metadata.values()).lower()
            metadata_matches = sum(1 for keyword in query_keywords if keyword in metadata_text)
            scores["metadata"] = metadata_matches / len(query_keywords) if query_keywords else 0
            
            # Combined query relevance
            chunk.relevance_scores["query"] = (
                scores.get("semantic", 0) * 0.6 +
                scores.get("keyword", 0) * 0.3 +
                scores.get("metadata", 0) * 0.1
            )
        
        return chunks
    
    async def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get embedding for query"""
        if not EMBEDDINGS_AVAILABLE:
            return None
        
        try:
            # This would use the same embedder as the chunk embeddings
            # For now, return None to trigger fallback
            return None
        except Exception:
            return None
    
    async def _create_hierarchical_clusters(self, chunks: List[ContentChunk]) -> Dict[str, List[ContentChunk]]:
        """Create hierarchical clusters of related chunks"""
        # Simple clustering by content type and relationships
        clusters = defaultdict(list)
        
        for chunk in chunks:
            cluster_key = f"{chunk.chunk_type.value}_{chunk.project_id}"
            clusters[cluster_key].append(chunk)
        
        return dict(clusters)
    
    async def _generate_hierarchical_summaries(self, clusters: Dict[str, List[ContentChunk]]) -> List[ContextSummary]:
        """Generate hierarchical summaries"""
        summaries = []
        
        for cluster_name, cluster_chunks in clusters.items():
            if len(cluster_chunks) >= 3:  # Only summarize meaningful clusters
                summary = ContextSummary(
                    id=f"summary_{uuid.uuid4().hex[:8]}",
                    level=1,
                    content=f"Summary of {len(cluster_chunks)} {cluster_name} items",
                    chunk_ids=[c.id for c in cluster_chunks],
                    children_summary_ids=[],
                    token_count=100,  # Estimated
                    relevance_score=np.mean([c.relevance_scores.get("query", 0.5) for c in cluster_chunks]),
                    created_at=datetime.now()
                )
                summaries.append(summary)
        
        return summaries
    
    async def _optimal_selection_dp(
        self,
        chunks: List[ContentChunk],
        summaries: List[ContextSummary],
        max_tokens: int
    ) -> Tuple[List[ContentChunk], List[ContextSummary]]:
        """Dynamic programming approach for optimal selection"""
        
        # Sort items by value/weight ratio
        items = []
        
        for chunk in chunks:
            value = chunk.relevance_scores.get("query", 0.5) * 100
            weight = chunk.get_token_count()
            items.append(("chunk", chunk, value, weight))
        
        for summary in summaries:
            value = summary.relevance_score * 80  # Summaries worth slightly less
            weight = summary.token_count
            items.append(("summary", summary, value, weight))
        
        items.sort(key=lambda x: x[2] / max(x[3], 1), reverse=True)
        
        # Greedy selection (simplified DP)
        selected_chunks = []
        selected_summaries = []
        current_weight = 0
        
        for item_type, item, value, weight in items:
            if current_weight + weight <= max_tokens:
                if item_type == "chunk":
                    selected_chunks.append(item)
                else:
                    selected_summaries.append(item)
                current_weight += weight
        
        return selected_chunks, selected_summaries
    
    async def _create_cluster_summary(self, chunks: List[ContentChunk], cluster_id: int) -> ContextSummary:
        """Create summary for a cluster of chunks"""
        chunk_types = set(c.chunk_type for c in chunks)
        avg_relevance = np.mean([c.relevance_scores.get("query", 0.5) for c in chunks])
        
        content = f"Summary of {len(chunks)} items of types: {', '.join(t.value for t in chunk_types)}"
        
        return ContextSummary(
            id=f"cluster_summary_{cluster_id}_{uuid.uuid4().hex[:8]}",
            level=1,
            content=content,
            chunk_ids=[c.id for c in chunks],
            children_summary_ids=[],
            token_count=len(content) // 4,
            relevance_score=avg_relevance,
            created_at=datetime.now()
        )
    
    async def _create_type_summary(self, chunks: List[ContentChunk], chunk_type: ChunkType) -> ContextSummary:
        """Create summary for chunks of the same type"""
        avg_relevance = np.mean([c.relevance_scores.get("combined", 0.5) for c in chunks])
        
        # Create more detailed summary based on type
        if chunk_type == ChunkType.CODE_FUNCTION:
            content = f"Summary of {len(chunks)} code functions including key functionality and signatures"
        elif chunk_type == ChunkType.ERROR_LOG:
            content = f"Summary of {len(chunks)} error logs with common patterns and solutions"
        elif chunk_type == ChunkType.CONVERSATION:
            content = f"Summary of {len(chunks)} conversations covering key decisions and discussions"
        else:
            content = f"Summary of {len(chunks)} {chunk_type.value} items"
        
        return ContextSummary(
            id=f"type_summary_{chunk_type.value}_{uuid.uuid4().hex[:8]}",
            level=1,
            content=content,
            chunk_ids=[c.id for c in chunks],
            children_summary_ids=[],
            token_count=len(content) // 4,
            relevance_score=avg_relevance,
            created_at=datetime.now()
        )


class StatelessRAGManager:
    """
    Ultra-scalable RAG manager that can handle unlimited context through stateless optimization.
    
    Key features:
    - Hierarchical chunking and summarization
    - Stateless context reconstruction
    - Multi-strategy optimization
    - Dynamic token allocation
    - Semantic clustering and relationship mapping
    """
    
    def __init__(self):
        self.optimizer = StatelessContextOptimizer()
        self.chunk_cache = {}  # In-memory cache for recently accessed chunks
        self.summary_cache = {}
        
        # Configuration
        self.max_chunk_size = 2000  # tokens
        self.optimal_chunk_size = 1000  # tokens
        self.cache_size = 1000  # number of chunks to keep in memory
        
        # Initialize database tables after startup
        self._db_initialized = False
        self._initialization_lock = None
    
    async def _ensure_initialized(self):
        """Ensure the RAG manager is properly initialized with async components"""
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
        """Initialize PostgreSQL database schema for stateless RAG"""
        try:
            table_definitions = {
                "content_chunks": """
                    CREATE TABLE IF NOT EXISTS content_chunks (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        chunk_type TEXT NOT NULL,
                        metadata JSONB,
                        embedding vector(384),
                        timestamp TIMESTAMPTZ NOT NULL,
                        parent_chunk_id TEXT,
                        child_chunk_ids TEXT[],
                        summary TEXT,
                        keywords TEXT[],
                        relationships JSONB,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMPTZ,
                        relevance_scores JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "context_summaries": """
                    CREATE TABLE IF NOT EXISTS context_summaries (
                        id TEXT PRIMARY KEY,
                        level INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        chunk_ids TEXT[] NOT NULL,
                        children_summary_ids TEXT[],
                        token_count INTEGER NOT NULL,
                        relevance_score REAL NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                """
            }
            
            # Create tables
            await db.create_tables_if_not_exist(table_definitions)
            
            # Create optimized indexes for performance
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_chunks_project_type ON content_chunks(project_id, chunk_type)",
                "CREATE INDEX IF NOT EXISTS idx_chunks_timestamp ON content_chunks(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_chunks_access ON content_chunks(last_accessed, access_count)",
                "CREATE INDEX IF NOT EXISTS idx_chunks_agent ON content_chunks(agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_summaries_level ON context_summaries(level, relevance_score)",
                # Vector similarity index for embeddings (if pgvector is available)
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON content_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            ]
            
            for index_query in index_queries:
                try:
                    await db.execute(index_query)
                except Exception as e:
                    logger.warning(f"Could not create index (may not have pgvector): {e}")
                
        except Exception as e:
            logger.log_error(e, {"action": "initialize_stateless_rag_database"})
    
    async def get_unlimited_context(
        self,
        project_id: str,
        agent_id: str,
        query: str,
        max_tokens: int = 180000,
        strategy: str = "hybrid",
        include_history: bool = True,
        time_filter: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get context that can theoretically handle unlimited amounts of data
        through intelligent optimization and summarization
        """
        try:
            await self._ensure_initialized()
            # Step 1: Retrieve all potentially relevant chunks
            candidate_chunks = await self._get_candidate_chunks(
                project_id, agent_id, query, include_history, time_filter
            )
            
            if not candidate_chunks:
                return {
                    "context": f"Query: {query}\n\nNo relevant context found.",
                    "optimization_stats": {"total_candidates": 0},
                    "sources": []
                }
            
            # Step 2: Optimize context selection
            selected_chunks, selected_summaries, optimization_stats = await self.optimizer.optimize_context_selection(
                query, candidate_chunks, max_tokens, strategy
            )
            
            # Step 3: Build optimized context
            context_response = await self._build_optimized_context(
                query, selected_chunks, selected_summaries, optimization_stats
            )
            
            # Step 4: Update access patterns
            await self._update_access_patterns(selected_chunks)
            
            # Log context generation
            await interaction_logger.log_interaction(
                project_id=project_id,
                agent_id=agent_id,
                interaction_type=InteractionType.SYSTEM_EVENT,
                action="unlimited_context_generated",
                content=f"Generated optimized context for: {query[:100]}...",
                context={
                    "strategy": strategy,
                    "total_candidates": len(candidate_chunks),
                    "selected_chunks": len(selected_chunks),
                    "selected_summaries": len(selected_summaries),
                    "token_utilization": optimization_stats.get("token_utilization", 0)
                }
            )
            
            return context_response
            
        except Exception as e:
            logger.log_error(e, {
                "action": "get_unlimited_context",
                "project_id": project_id,
                "query": query[:100]
            })
            return {"error": str(e), "context": "", "sources": []}
    
    async def add_optimized_content(
        self,
        project_id: str,
        agent_id: str,
        content: str,
        content_type: str,
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """Add content with automatic chunking and optimization"""
        try:
            await self._ensure_initialized()
            chunk_type = ChunkType(content_type) if content_type in [t.value for t in ChunkType] else ChunkType.DOCUMENTATION
            
            # Smart chunking based on content type
            chunks = await self._smart_chunk_content(
                content, chunk_type, project_id, agent_id, metadata or {}
            )
            
            # Store chunks
            chunk_ids = []
            for chunk in chunks:
                chunk_id = await self._store_chunk(chunk)
                if chunk_id:
                    chunk_ids.append(chunk_id)
            
            # Update relationships
            await self._update_chunk_relationships(chunks)
            
            # Trigger summarization if needed
            await self._trigger_adaptive_summarization(project_id, chunk_type)
            
            return chunk_ids
            
        except Exception as e:
            logger.log_error(e, {"action": "add_optimized_content"})
            return []
    
    async def _get_candidate_chunks(
        self,
        project_id: str,
        agent_id: str,
        query: str,
        include_history: bool,
        time_filter: Optional[datetime]
    ) -> List[ContentChunk]:
        """Get all potentially relevant chunks using multiple retrieval strategies"""
        try:
            candidates = []
            
            # Strategy 1: Semantic search (if embeddings available)
            if EMBEDDINGS_AVAILABLE:
                semantic_candidates = await self._semantic_search(project_id, query, limit=100)
                candidates.extend(semantic_candidates)
            
            # Strategy 2: Keyword search
            keyword_candidates = await self._keyword_search(project_id, query, limit=100)
            candidates.extend(keyword_candidates)
            
            # Strategy 3: Recent activity
            if include_history:
                recent_candidates = await self._get_recent_chunks(project_id, agent_id, limit=50)
                candidates.extend(recent_candidates)
            
            # Strategy 4: Relationship traversal
            relationship_candidates = await self._get_related_chunks(candidates[:20], limit=50)
            candidates.extend(relationship_candidates)
            
            # Deduplicate
            seen_ids = set()
            unique_candidates = []
            for chunk in candidates:
                if chunk.id not in seen_ids:
                    seen_ids.add(chunk.id)
                    unique_candidates.append(chunk)
            
            # Apply time filter
            if time_filter:
                unique_candidates = [c for c in unique_candidates if c.timestamp >= time_filter]
            
            return unique_candidates
            
        except Exception as e:
            logger.log_error(e, {"action": "get_candidate_chunks"})
            return []
    
    async def _semantic_search(self, project_id: str, query: str, limit: int) -> List[ContentChunk]:
        """Semantic search using vector similarity"""
        # Placeholder for semantic search
        # Would use FAISS or similar for actual implementation
        return []
    
    async def _keyword_search(self, project_id: str, query: str, limit: int) -> List[ContentChunk]:
        """Keyword-based search"""
        try:
            keywords = query.lower().split()
            
            # Use simple keyword search with PostgreSQL
            # For now, return empty list as this method needs full implementation
            return []
                
        except Exception as e:
            logger.log_error(e, {"action": "keyword_search"})
            return []
    
    async def _get_recent_chunks(self, project_id: str, agent_id: str, limit: int) -> List[ContentChunk]:
        """Get recently accessed or created chunks"""
        try:
            # PostgreSQL implementation needed
            return []
                
        except Exception as e:
            logger.log_error(e, {"action": "get_recent_chunks"})
            return []
    
    async def _get_related_chunks(self, seed_chunks: List[ContentChunk], limit: int) -> List[ContentChunk]:
        """Get chunks related to seed chunks through relationships"""
        related_ids = set()
        
        for chunk in seed_chunks:
            for relationship_list in chunk.relationships.values():
                related_ids.update(relationship_list)
        
        if not related_ids:
            return []
        
        try:
# PostgreSQL connection handled by global db instance
                placeholders = ",".join("?" * len(related_ids))
                cursor = await db.execute(f"""
                    SELECT * FROM content_chunks 
                    WHERE id IN ({placeholders})
                    ORDER BY access_count DESC
                    LIMIT ?
                """, list(related_ids) + [limit])
                
                rows = await cursor.fetchall()
                return [self._row_to_chunk(row) for row in rows]
                
        except Exception as e:
            logger.log_error(e, {"action": "get_related_chunks"})
            return []
    
    async def _build_optimized_context(
        self,
        query: str,
        chunks: List[ContentChunk],
        summaries: List[ContextSummary],
        optimization_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the final optimized context response"""
        
        context_parts = []
        sources = []
        total_tokens = 0
        
        # Add query context
        query_section = f"Query: {query}\n\nOptimized Context (Strategy: {optimization_stats.get('strategy', 'unknown')}):\n\n"
        context_parts.append(query_section)
        total_tokens += len(query_section) // 4
        
        # Add summaries first (compressed information)
        if summaries:
            context_parts.append("=== CONTEXT SUMMARIES ===\n")
            for summary in summaries:
                summary_text = f"[SUMMARY L{summary.level}] {summary.content}\n"
                context_parts.append(summary_text)
                total_tokens += summary.token_count
                
                sources.append({
                    "type": "summary",
                    "id": summary.id,
                    "level": summary.level,
                    "chunk_count": len(summary.chunk_ids),
                    "relevance": summary.relevance_score
                })
            context_parts.append("\n")
        
        # Add selected chunks (detailed information)
        if chunks:
            context_parts.append("=== DETAILED CONTEXT ===\n")
            
            # Group chunks by type for better organization
            type_groups = defaultdict(list)
            for chunk in chunks:
                type_groups[chunk.chunk_type].append(chunk)
            
            for chunk_type, type_chunks in type_groups.items():
                context_parts.append(f"\n--- {chunk_type.value.upper().replace('_', ' ')} ---\n")
                
                for chunk in type_chunks:
                    chunk_header = f"[{chunk.chunk_type.value}] {chunk.metadata.get('title', 'Untitled')}"
                    if chunk.metadata.get('file_path'):
                        chunk_header += f" ({chunk.metadata['file_path']})"
                    chunk_header += f" | Relevance: {chunk.relevance_scores.get('query', 0):.2f}\n"
                    
                    chunk_content = f"{chunk_header}{chunk.content}\n\n"
                    context_parts.append(chunk_content)
                    total_tokens += chunk.get_token_count()
                    
                    sources.append({
                        "type": "chunk",
                        "id": chunk.id,
                        "chunk_type": chunk.chunk_type.value,
                        "agent_id": chunk.agent_id,
                        "timestamp": chunk.timestamp.isoformat(),
                        "relevance": chunk.relevance_scores.get("query", 0),
                        "metadata": chunk.metadata
                    })
        
        # Add optimization statistics
        stats_section = f"\n=== OPTIMIZATION STATS ===\n"
        stats_section += f"Strategy: {optimization_stats.get('strategy', 'unknown')}\n"
        stats_section += f"Candidates Evaluated: {optimization_stats.get('total_candidates', 0)}\n"
        stats_section += f"Chunks Selected: {len(chunks)}\n"
        stats_section += f"Summaries Created: {len(summaries)}\n"
        stats_section += f"Token Utilization: {optimization_stats.get('token_utilization', 0):.1%}\n"
        
        if optimization_stats.get('content_diversity'):
            stats_section += f"Content Diversity: {optimization_stats['content_diversity']} types\n"
        
        context_parts.append(stats_section)
        total_tokens += len(stats_section) // 4
        
        return {
            "context": "".join(context_parts),
            "sources": sources,
            "total_tokens": total_tokens,
            "optimization_stats": optimization_stats,
            "query": query,
            "chunks_count": len(chunks),
            "summaries_count": len(summaries)
        }
    
    async def _smart_chunk_content(
        self,
        content: str,
        chunk_type: ChunkType,
        project_id: str,
        agent_id: str,
        metadata: Dict[str, Any]
    ) -> List[ContentChunk]:
        """Smart content chunking based on content type"""
        
        chunks = []
        
        if chunk_type == ChunkType.CODE_FILE:
            # Split by functions/classes
            chunks = await self._chunk_code_file(content, project_id, agent_id, metadata)
        elif chunk_type == ChunkType.DOCUMENTATION:
            # Split by sections/headers
            chunks = await self._chunk_documentation(content, project_id, agent_id, metadata)
        elif chunk_type == ChunkType.CONVERSATION:
            # Split by messages or topics
            chunks = await self._chunk_conversation(content, project_id, agent_id, metadata)
        else:
            # Generic chunking
            chunks = await self._chunk_generic_content(content, chunk_type, project_id, agent_id, metadata)
        
        return chunks
    
    async def _chunk_code_file(self, content: str, project_id: str, agent_id: str, metadata: Dict[str, Any]) -> List[ContentChunk]:
        """Chunk code file by functions and classes"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_function = None
        
        for line in lines:
            stripped = line.strip()
            
            # Detect function/class definitions
            if stripped.startswith(('def ', 'class ', 'function ', 'const ', 'let ', 'var ')):
                # Save previous chunk
                if current_chunk:
                    chunk = await self._create_chunk(
                        '\n'.join(current_chunk),
                        ChunkType.CODE_FUNCTION if current_function else ChunkType.CODE_CLASS,
                        project_id,
                        agent_id,
                        {**metadata, "function_name": current_function}
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [line]
                current_function = stripped.split('(')[0].split(' ')[-1] if '(' in stripped else stripped.split(' ')[-1]
            else:
                current_chunk.append(line)
                
                # Split large chunks
                if len('\n'.join(current_chunk)) > self.max_chunk_size * 4:  # Rough token estimate
                    chunk = await self._create_chunk(
                        '\n'.join(current_chunk),
                        ChunkType.CODE_FUNCTION,
                        project_id,
                        agent_id,
                        {**metadata, "function_name": current_function}
                    )
                    chunks.append(chunk)
                    current_chunk = []
                    current_function = None
        
        # Save final chunk
        if current_chunk:
            chunk = await self._create_chunk(
                '\n'.join(current_chunk),
                ChunkType.CODE_FUNCTION if current_function else ChunkType.CODE_FILE,
                project_id,
                agent_id,
                {**metadata, "function_name": current_function}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_documentation(self, content: str, project_id: str, agent_id: str, metadata: Dict[str, Any]) -> List[ContentChunk]:
        """Chunk documentation by sections"""
        chunks = []
        sections = content.split('\n#')  # Split by markdown headers
        
        for i, section in enumerate(sections):
            if i > 0:
                section = '#' + section  # Restore header
            
            if len(section.strip()) > 100:  # Only create chunks for substantial content
                chunk = await self._create_chunk(
                    section.strip(),
                    ChunkType.DOCUMENTATION,
                    project_id,
                    agent_id,
                    metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _chunk_conversation(self, content: str, project_id: str, agent_id: str, metadata: Dict[str, Any]) -> List[ContentChunk]:
        """Chunk conversation by messages or topics"""
        chunks = []
        
        # Simple chunking by double newlines (message separators)
        messages = content.split('\n\n')
        current_chunk = []
        
        for message in messages:
            current_chunk.append(message)
            
            # Create chunk when reaching optimal size
            chunk_content = '\n\n'.join(current_chunk)
            if len(chunk_content) > self.optimal_chunk_size * 4:
                chunk = await self._create_chunk(
                    chunk_content,
                    ChunkType.CONVERSATION,
                    project_id,
                    agent_id,
                    metadata
                )
                chunks.append(chunk)
                current_chunk = []
        
        # Save final chunk
        if current_chunk:
            chunk = await self._create_chunk(
                '\n\n'.join(current_chunk),
                ChunkType.CONVERSATION,
                project_id,
                agent_id,
                metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_generic_content(self, content: str, chunk_type: ChunkType, project_id: str, agent_id: str, metadata: Dict[str, Any]) -> List[ContentChunk]:
        """Generic content chunking"""
        chunks = []
        
        # Split by paragraphs or sentences
        paragraphs = content.split('\n\n')
        current_chunk = []
        
        for paragraph in paragraphs:
            current_chunk.append(paragraph)
            
            chunk_content = '\n\n'.join(current_chunk)
            if len(chunk_content) > self.optimal_chunk_size * 4:
                chunk = await self._create_chunk(
                    chunk_content,
                    chunk_type,
                    project_id,
                    agent_id,
                    metadata
                )
                chunks.append(chunk)
                current_chunk = []
        
        if current_chunk:
            chunk = await self._create_chunk(
                '\n\n'.join(current_chunk),
                chunk_type,
                project_id,
                agent_id,
                metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _create_chunk(
        self,
        content: str,
        chunk_type: ChunkType,
        project_id: str,
        agent_id: str,
        metadata: Dict[str, Any]
    ) -> ContentChunk:
        """Create a content chunk with all metadata"""
        
        chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
        
        # Generate summary
        summary = content[:200] + "..." if len(content) > 200 else content
        
        # Extract keywords
        keywords = await self._extract_keywords(content)
        
        # Create chunk
        chunk = ContentChunk(
            id=chunk_id,
            project_id=project_id,
            agent_id=agent_id,
            content=content,
            chunk_type=chunk_type,
            metadata=metadata,
            embedding=None,  # Will be generated later if needed
            timestamp=datetime.now(),
            parent_chunk_id=None,
            child_chunk_ids=[],
            summary=summary,
            keywords=keywords,
            relationships=defaultdict(list),
            access_count=0,
            last_accessed=datetime.now(),
            relevance_scores={}
        )
        
        return chunk
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction
        words = content.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        keywords = []
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        # Return most frequent keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    async def _store_chunk(self, chunk: ContentChunk) -> str:
        """Store chunk in database"""
        try:
# PostgreSQL connection handled by global db instance
                await db.execute("""
                    INSERT INTO content_chunks 
                    (id, project_id, agent_id, content, chunk_type, metadata, embedding,
                     timestamp, parent_chunk_id, child_chunk_ids, summary, keywords,
                     relationships, access_count, last_accessed, relevance_scores)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.id, chunk.project_id, chunk.agent_id, chunk.content,
                    chunk.chunk_type.value, json.dumps(chunk.metadata),
                    None,  # embedding will be added later
                    chunk.timestamp.isoformat(), chunk.parent_chunk_id,
                    json.dumps(chunk.child_chunk_ids), chunk.summary,
                    json.dumps(chunk.keywords), json.dumps(dict(chunk.relationships)),
                    chunk.access_count, chunk.last_accessed.isoformat(),
                    json.dumps(chunk.relevance_scores)
                ))
                await db.commit()
                return chunk.id
                
        except Exception as e:
            logger.log_error(e, {"action": "store_chunk"})
            return ""
    
    async def _update_chunk_relationships(self, chunks: List[ContentChunk]):
        """Update relationships between chunks"""
        # Simple relationship detection based on keywords and metadata
        for i, chunk1 in enumerate(chunks):
            for j, chunk2 in enumerate(chunks):
                if i != j:
                    # Check for keyword overlap
                    overlap = set(chunk1.keywords) & set(chunk2.keywords)
                    if len(overlap) >= 2:  # At least 2 common keywords
                        chunk1.relationships["related"].append(chunk2.id)
                    
                    # Check for metadata relationships
                    if chunk1.metadata.get("file_path") == chunk2.metadata.get("file_path"):
                        chunk1.relationships["same_file"].append(chunk2.id)
    
    async def _update_access_patterns(self, chunks: List[ContentChunk]):
        """Update access patterns for chunks"""
        try:
            # PostgreSQL implementation needed - simplified for now
            pass
                
        except Exception as e:
            logger.log_error(e, {"action": "update_access_patterns"})
    
    async def _trigger_adaptive_summarization(self, project_id: str, chunk_type: ChunkType):
        """Trigger summarization when there are too many chunks of a type"""
        try:
            # Count chunks of this type
# PostgreSQL connection handled by global db instance
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM content_chunks 
                    WHERE project_id = ? AND chunk_type = ?
                """, (project_id, chunk_type.value))
                
                count = (await cursor.fetchone())[0]
                
                # If we have too many chunks, create summaries
                if count > 100:  # Threshold for summarization
                    await self._create_adaptive_summaries(project_id, chunk_type)
                    
        except Exception as e:
            logger.log_error(e, {"action": "trigger_adaptive_summarization"})
    
    async def _create_adaptive_summaries(self, project_id: str, chunk_type: ChunkType):
        """Create adaptive summaries for chunk type"""
        # This would implement more sophisticated summarization logic
        # For now, just log that it would happen
        logger.log_system_event("adaptive_summarization_triggered", {
            "project_id": project_id,
            "chunk_type": chunk_type.value
        })
    
    def _row_to_chunk(self, row) -> ContentChunk:
        """Convert database row to ContentChunk"""
        return ContentChunk(
            id=row[0],
            project_id=row[1],
            agent_id=row[2],
            content=row[3],
            chunk_type=ChunkType(row[4]),
            metadata=json.loads(row[5]) if row[5] else {},
            embedding=None,  # Would deserialize from BLOB
            timestamp=datetime.fromisoformat(row[7]),
            parent_chunk_id=row[8],
            child_chunk_ids=json.loads(row[9]) if row[9] else [],
            summary=row[10] or "",
            keywords=json.loads(row[11]) if row[11] else [],
            relationships=defaultdict(list, json.loads(row[12]) if row[12] else {}),
            access_count=row[13] or 0,
            last_accessed=datetime.fromisoformat(row[14]) if row[14] else datetime.now(),
            relevance_scores=json.loads(row[15]) if row[15] else {}
        )


# Global instance
stateless_rag_manager = StatelessRAGManager()