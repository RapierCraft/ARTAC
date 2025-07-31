"""
ARTAC Smart RAG Service
Advanced Retrieval Augmented Generation service for intelligent agent context
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class ContextType(Enum):
    """Types of context that can be retrieved"""
    ORGANIZATIONAL = "organizational"      # Company structure, policies, culture
    PROJECT = "project"                   # Current projects, tasks, deadlines
    TEAM = "team"                        # Team members, skills, performance
    FINANCIAL = "financial"              # Budget, costs, revenue
    TECHNICAL = "technical"              # Code, architecture, documentation
    COMMUNICATION = "communication"       # Previous conversations, decisions
    METRICS = "metrics"                  # Performance data, analytics
    EXTERNAL = "external"                # Market data, client info


@dataclass
class ContextDocument:
    """A document in the knowledge base"""
    id: str
    content: str
    content_type: ContextType
    metadata: Dict[str, Any]
    timestamp: datetime
    relevance_score: float = 0.0
    source: str = "unknown"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class AgentContext:
    """Context specifically tailored for an agent"""
    agent_id: str
    agent_role: str
    context_documents: List[ContextDocument]
    summary: str
    priority_topics: List[str]
    recent_interactions: List[Dict[str, Any]]
    generated_at: datetime


class SmartRAGService:
    """Advanced RAG service with intelligent context management"""
    
    def __init__(self):
        self.is_initialized = False
        self.knowledge_base: Dict[str, ContextDocument] = {}
        self.context_cache: Dict[str, AgentContext] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Smart context weights for different agent roles
        self.role_context_weights = {
            "CEO": {
                ContextType.ORGANIZATIONAL: 1.0,
                ContextType.PROJECT: 0.9,
                ContextType.FINANCIAL: 0.9,
                ContextType.TEAM: 0.8,
                ContextType.METRICS: 0.8,
                ContextType.COMMUNICATION: 0.7,
                ContextType.TECHNICAL: 0.3,
                ContextType.EXTERNAL: 0.6
            },
            "CTO": {
                ContextType.TECHNICAL: 1.0,
                ContextType.PROJECT: 0.9,
                ContextType.TEAM: 0.8,
                ContextType.ORGANIZATIONAL: 0.6,
                ContextType.FINANCIAL: 0.5,
                ContextType.METRICS: 0.8,
                ContextType.COMMUNICATION: 0.7,
                ContextType.EXTERNAL: 0.4
            },
            "Developer": {
                ContextType.TECHNICAL: 1.0,
                ContextType.PROJECT: 0.9,
                ContextType.TEAM: 0.6,
                ContextType.COMMUNICATION: 0.5,
                ContextType.ORGANIZATIONAL: 0.3,
                ContextType.FINANCIAL: 0.2,
                ContextType.METRICS: 0.4,
                ContextType.EXTERNAL: 0.2
            },
            "Security": {
                ContextType.TECHNICAL: 0.9,
                ContextType.ORGANIZATIONAL: 0.8,
                ContextType.PROJECT: 0.7,
                ContextType.TEAM: 0.6,
                ContextType.EXTERNAL: 0.7,
                ContextType.COMMUNICATION: 0.6,
                ContextType.FINANCIAL: 0.4,
                ContextType.METRICS: 0.6
            }
        }
        
    async def initialize(self):
        """Initialize the smart RAG service"""
        try:
            # Initialize with organizational knowledge
            await self._load_organizational_context()
            await self._load_current_state()
            
            self.is_initialized = True
            logger.log_system_event("smart_rag_initialized", {
                "knowledge_base_size": len(self.knowledge_base),
                "context_types": list(ContextType),
                "supported_roles": list(self.role_context_weights.keys())
            })
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_rag"})
            raise
    
    async def _load_organizational_context(self):
        """Load core organizational knowledge"""
        org_contexts = [
            ContextDocument(
                id="org_mission",
                content="ARTAC is an AI-powered autonomous organization that uses intelligent agents to handle complex tasks. Our mission is to revolutionize how work gets done by creating a fully autonomous workforce that can adapt, learn, and execute tasks with minimal human oversight.",
                content_type=ContextType.ORGANIZATIONAL,
                metadata={"importance": "critical", "category": "mission"},
                timestamp=datetime.now(),
                source="organizational_charter",
                tags=["mission", "vision", "ai", "autonomous"]
            ),
            ContextDocument(
                id="org_structure",
                content="ARTAC operates with a CEO agent that makes strategic decisions and hires specialized agents as needed. Each agent has specific skills and can work independently or as part of teams. The organization uses a dynamic hiring model where agents are recruited based on project requirements.",
                content_type=ContextType.ORGANIZATIONAL,
                metadata={"importance": "high", "category": "structure"},
                timestamp=datetime.now(),
                source="organizational_chart",
                tags=["structure", "hierarchy", "agents", "hiring"]
            ),
            ContextDocument(
                id="tech_stack",
                content="ARTAC is built on Python FastAPI backend with React/TypeScript frontend. Uses Claude AI for agent intelligence, Docker for containerization, and implements real-time communication systems. The architecture supports scalable agent deployment and management.",
                content_type=ContextType.TECHNICAL,
                metadata={"importance": "high", "category": "architecture"},
                timestamp=datetime.now(),
                source="technical_documentation",
                tags=["python", "fastapi", "react", "claude", "docker"]
            )
        ]
        
        for doc in org_contexts:
            self.knowledge_base[doc.id] = doc
    
    async def _load_current_state(self):
        """Load current organizational state"""
        # This would normally query your database for current state
        # For now, we'll simulate with dynamic content
        
        from services.ceo_agent import ceo
        
        ceo_status = ceo.get_status()
        current_tasks = ceo.get_current_tasks()
        hired_team = ceo.get_hired_team()
        
        current_state_doc = ContextDocument(
            id="current_state",
            content=f"Current organizational state: {ceo_status['current_tasks']} active tasks, {ceo_status['hired_agents']} agents hired, {ceo_status['interviews_conducted']} interviews conducted. Available talent pool: {ceo_status['available_talent_pool']} agents. Recent activity shows {'high productivity' if ceo_status['hired_agents'] > 0 else 'ready for new projects'}.",
            content_type=ContextType.METRICS,
            metadata={
                "importance": "critical",
                "category": "current_state",
                "active_tasks": ceo_status['current_tasks'],
                "hired_agents": ceo_status['hired_agents'],
                "last_updated": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            source="real_time_status",
            tags=["current", "status", "metrics", "live"]
        )
        
        self.knowledge_base["current_state"] = current_state_doc
    
    async def add_interaction(self, agent_id: str, user_message: str, agent_response: str, context_used: List[str] = None):
        """Record an interaction for learning"""
        interaction = {
            "id": hashlib.md5(f"{agent_id}_{datetime.now().isoformat()}".encode()).hexdigest(),
            "agent_id": agent_id,
            "user_message": user_message,
            "agent_response": agent_response,
            "context_used": context_used or [],
            "timestamp": datetime.now(),
            "metadata": {"response_length": len(agent_response), "context_count": len(context_used or [])}
        }
        
        self.interaction_history.append(interaction)
        
        # Store as knowledge for future context
        interaction_doc = ContextDocument(
            id=f"interaction_{interaction['id']}",
            content=f"Previous conversation - User: {user_message} | Agent Response: {agent_response}",
            content_type=ContextType.COMMUNICATION,
            metadata=interaction["metadata"],
            timestamp=interaction["timestamp"],
            source=f"agent_{agent_id}",
            tags=["conversation", "history", agent_id]
        )
        
        self.knowledge_base[interaction_doc.id] = interaction_doc
        
        # Keep only recent interactions (last 100)
        if len(self.interaction_history) > 100:
            self.interaction_history = self.interaction_history[-100:]
    
    async def get_smart_context_for_agent(
        self, 
        agent_id: str, 
        agent_role: str, 
        user_query: str,
        max_context_length: int = 2000
    ) -> AgentContext:
        """Get intelligent context tailored for specific agent and query"""
        
        try:
            # Update current state
            await self._load_current_state()
            
            # Get role-specific weights
            role_weights = self.role_context_weights.get(agent_role, self.role_context_weights["CEO"])
            
            # Score all documents for relevance
            scored_docs = []
            query_lower = user_query.lower()
            
            for doc in self.knowledge_base.values():
                # Base relevance score
                relevance = 0.0
                
                # Role-based weighting
                role_weight = role_weights.get(doc.content_type, 0.1)
                relevance += role_weight * 0.4
                
                # Query relevance (simple keyword matching - could be enhanced with embeddings)
                query_words = set(query_lower.split())
                doc_words = set(doc.content.lower().split())
                tag_words = set([tag.lower() for tag in doc.tags])
                
                keyword_overlap = len(query_words.intersection(doc_words.union(tag_words)))
                if keyword_overlap > 0:
                    relevance += (keyword_overlap / len(query_words)) * 0.4
                
                # Recency boost
                age_hours = (datetime.now() - doc.timestamp).total_seconds() / 3600
                if age_hours < 24:
                    relevance += 0.2 * (1 - age_hours / 24)
                
                # Importance boost
                importance = doc.metadata.get("importance", "medium")
                importance_boost = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.0}
                relevance += importance_boost.get(importance, 0.1)
                
                doc.relevance_score = relevance
                scored_docs.append(doc)
            
            # Sort by relevance and take top results
            scored_docs.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Select context within length limit
            selected_docs = []
            current_length = 0
            
            for doc in scored_docs:
                if current_length + len(doc.content) <= max_context_length:
                    selected_docs.append(doc)
                    current_length += len(doc.content)
                else:
                    break
            
            # Generate summary
            priority_topics = self._extract_priority_topics(selected_docs, user_query)
            summary = self._generate_context_summary(selected_docs, agent_role, user_query)
            
            # Get recent interactions with this agent
            recent_interactions = [
                interaction for interaction in self.interaction_history[-10:]
                if interaction["agent_id"] == agent_id
            ]
            
            context = AgentContext(
                agent_id=agent_id,
                agent_role=agent_role,
                context_documents=selected_docs,
                summary=summary,
                priority_topics=priority_topics,
                recent_interactions=recent_interactions,
                generated_at=datetime.now()
            )
            
            # Cache the context
            self.context_cache[f"{agent_id}_{hashlib.md5(user_query.encode()).hexdigest()[:8]}"] = context
            
            logger.log_system_event("smart_context_generated", {
                "agent_id": agent_id,
                "agent_role": agent_role,
                "query_preview": user_query[:50],
                "context_docs": len(selected_docs),
                "context_length": current_length,
                "priority_topics": len(priority_topics)
            })
            
            return context
            
        except Exception as e:
            logger.log_error(e, {"action": "get_smart_context", "agent_id": agent_id})
            # Return minimal context on error
            return AgentContext(
                agent_id=agent_id,
                agent_role=agent_role,
                context_documents=[],
                summary="Context generation failed - operating with minimal context",
                priority_topics=[],
                recent_interactions=[],
                generated_at=datetime.now()
            )
    
    def _extract_priority_topics(self, docs: List[ContextDocument], query: str) -> List[str]:
        """Extract priority topics from context documents"""
        topics = set()
        query_words = set(query.lower().split())
        
        for doc in docs:
            # Add tags as topics
            topics.update(doc.tags)
            
            # Add metadata categories
            if "category" in doc.metadata:
                topics.add(doc.metadata["category"])
        
        # Prioritize topics that match query
        prioritized = []
        for topic in topics:
            if any(word in topic.lower() for word in query_words):
                prioritized.append(topic)
        
        # Add remaining topics
        for topic in topics:
            if topic not in prioritized:
                prioritized.append(topic)
        
        return prioritized[:5]  # Top 5 topics
    
    def _generate_context_summary(self, docs: List[ContextDocument], agent_role: str, query: str) -> str:
        """Generate a concise summary of the context"""
        if not docs:
            return "No relevant context found."
        
        context_types = set(doc.content_type.value for doc in docs)
        doc_count = len(docs)
        
        summary = f"Context for {agent_role} agent: {doc_count} relevant documents covering {', '.join(context_types)}. "
        
        # Add specific insights based on role
        if agent_role == "CEO":
            summary += "Focus on strategic decision-making, organizational performance, and resource allocation. "
        elif agent_role == "CTO":
            summary += "Focus on technical architecture, development priorities, and team capabilities. "
        elif agent_role == "Developer":
            summary += "Focus on technical implementation, code quality, and project requirements. "
        elif agent_role == "Security":
            summary += "Focus on security protocols, risk assessment, and compliance requirements. "
        
        # Add query-specific context
        if "status" in query.lower():
            summary += "Query requires current status information. "
        elif any(word in query.lower() for word in ["project", "task", "work"]):
            summary += "Query relates to project/task management. "
        elif any(word in query.lower() for word in ["team", "hire", "agent"]):
            summary += "Query involves team/hiring decisions. "
        
        return summary
    
    async def add_knowledge(self, content: str, content_type: ContextType, metadata: Dict[str, Any] = None, source: str = "manual", tags: List[str] = None):
        """Add knowledge to the RAG system"""
        try:
            doc_id = hashlib.md5(f"{content}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            doc = ContextDocument(
                id=doc_id,
                content=content,
                content_type=content_type,
                metadata=metadata or {},
                timestamp=datetime.now(),
                source=source,
                tags=tags or []
            )
            
            self.knowledge_base[doc_id] = doc
            
            logger.log_system_event("knowledge_added", {
                "doc_id": doc_id,
                "content_type": content_type.value,
                "content_length": len(content),
                "source": source,
                "tags": tags or []
            })
            
        except Exception as e:
            logger.log_error(e, {"action": "add_knowledge", "content_type": content_type.value})
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive RAG service status"""
        context_type_counts = {}
        for doc in self.knowledge_base.values():
            doc_type = doc.content_type.value
            context_type_counts[doc_type] = context_type_counts.get(doc_type, 0) + 1
        
        return {
            "initialized": self.is_initialized,
            "knowledge_base_size": len(self.knowledge_base),
            "interaction_history_size": len(self.interaction_history),
            "cached_contexts": len(self.context_cache),
            "context_type_distribution": context_type_counts,
            "supported_agent_roles": list(self.role_context_weights.keys()),
            "last_updated": datetime.now().isoformat()
        }


# Global RAG service instance
rag_service = SmartRAGService()