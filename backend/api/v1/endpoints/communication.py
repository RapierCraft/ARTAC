"""
Communication API endpoints
Handles messaging between users and the CEO agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from services.ceo_agent import ceo
from services.rag_service import rag_service
from services.claude_code_service import ClaudeCodeService
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models for request/response
class SendMessageRequest(BaseModel):
    channel_id: str
    content: str
    mentions: Optional[List[str]] = []
    reply_to: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    channel_id: str
    user_id: str
    user_name: str
    content: str
    timestamp: datetime
    mentions: List[str]
    is_ceo_response: bool = False

class ChannelResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    unread_count: int = 0

# In-memory storage for demo (in production, this would be a database)
messages_store = {}
channels_store = {
    "channel-ceo": {
        "id": "channel-ceo",
        "name": "CEO Chat",
        "description": "Direct communication with the CEO",
        "type": "private",
        "unread_count": 0
    },
    "channel-general": {
        "id": "channel-general", 
        "name": "General",
        "description": "General company discussion",
        "type": "public",
        "unread_count": 0
    }
}

@router.get("/channels", response_model=List[ChannelResponse])
async def get_channels():
    """Get all available channels"""
    return list(channels_store.values())

@router.get("/channels/{channel_id}/messages", response_model=List[MessageResponse])
async def get_channel_messages(channel_id: str):
    """Get messages for a specific channel"""
    if channel_id not in channels_store:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return messages_store.get(channel_id, [])

@router.post("/channels/{channel_id}/messages", response_model=MessageResponse)
async def send_message(channel_id: str, request: SendMessageRequest):
    """Send a message to a channel"""
    # Ensure services are initialized
    await ensure_services_initialized()
    
    if channel_id not in channels_store:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Create user message
    message = MessageResponse(
        id=str(uuid.uuid4()),
        channel_id=channel_id,
        user_id="current-user",
        user_name="User",
        content=request.content,
        timestamp=datetime.now(),
        mentions=request.mentions,
        is_ceo_response=False
    )
    
    # Store message
    if channel_id not in messages_store:
        messages_store[channel_id] = []
    messages_store[channel_id].append(message)
    
    logger.log_system_event("message_sent", {
        "channel_id": channel_id,
        "message_id": message.id,
        "content_preview": request.content[:50],
        "mentions": request.mentions
    })
    
    # If this is the CEO channel or mentions CEO, trigger CEO response
    if channel_id == "channel-ceo" or "ceo" in [m.lower() for m in request.mentions]:
        ceo_response = await generate_ceo_response(channel_id, request.content, request.mentions)
        if ceo_response:
            messages_store[channel_id].append(ceo_response)
    
    return message

async def generate_ceo_response(channel_id: str, user_message: str, mentions: List[str]) -> Optional[MessageResponse]:
    """Generate an intelligent response from the CEO agent using RAG + Claude CLI"""
    try:
        # Initialize services if needed
        if not rag_service.is_initialized:
            await rag_service.initialize()
        
        # Get smart context for CEO agent
        agent_context = await rag_service.get_smart_context_for_agent(
            agent_id="ceo-001",
            agent_role="CEO", 
            user_query=user_message,
            max_context_length=2000
        )
        
        # Generate CEO response using Claude CLI with RAG context
        ceo_response_content = await generate_intelligent_ceo_response(
            user_message, 
            agent_context
        )
        
        # Create CEO response message
        ceo_response = MessageResponse(
            id=str(uuid.uuid4()),
            channel_id=channel_id,
            user_id="ceo-001",
            user_name="ARTAC CEO",
            content=ceo_response_content,
            timestamp=datetime.now(),
            mentions=[],
            is_ceo_response=True
        )
        
        # Record this interaction in RAG for future learning
        await rag_service.add_interaction(
            agent_id="ceo-001",
            user_message=user_message,
            agent_response=ceo_response_content,
            context_used=[doc.id for doc in agent_context.context_documents]
        )
        
        logger.log_system_event("intelligent_ceo_response_generated", {
            "channel_id": channel_id,
            "response_id": ceo_response.id,
            "user_message_preview": user_message[:50],
            "context_docs_used": len(agent_context.context_documents),
            "context_summary": agent_context.summary[:100],
            "priority_topics": agent_context.priority_topics
        })
        
        return ceo_response
        
    except Exception as e:
        logger.log_system_event("intelligent_ceo_response_error", {
            "error": str(e),
            "channel_id": channel_id,
            "user_message_preview": user_message[:50]
        })
        
        # Fallback to basic response if AI fails
        fallback_response = MessageResponse(
            id=str(uuid.uuid4()),
            channel_id=channel_id,
            user_id="ceo-001",
            user_name="ARTAC CEO",
            content="I'm experiencing some technical difficulties with my AI systems. Let me get back to you shortly on that.",
            timestamp=datetime.now(),
            mentions=[],
            is_ceo_response=True
        )
        return fallback_response

async def generate_intelligent_ceo_response(user_message: str, agent_context) -> str:
    """Generate CEO response using Claude CLI with RAG context"""
    try:
        # Initialize Claude Code service
        claude_service = ClaudeCodeService()
        
        # Build context prompt from RAG
        context_content = ""
        for doc in agent_context.context_documents:
            context_content += f"[{doc.content_type.value.upper()}] {doc.content}\n\n"
        
        # Create comprehensive prompt for CEO agent
        system_prompt = f"""You are the CEO of ARTAC, an AI-powered autonomous organization. You make strategic decisions, hire agents, and manage organizational direction.

CURRENT CONTEXT:
{agent_context.summary}

RELEVANT INFORMATION:
{context_content}

PRIORITY TOPICS: {', '.join(agent_context.priority_topics)}

RECENT INTERACTIONS: {len(agent_context.recent_interactions)} previous conversations

YOUR ROLE AS CEO:
- Make strategic decisions for the organization
- Hire and manage AI agents based on project needs  
- Provide leadership and direction
- Monitor organizational performance and metrics
- Handle resource allocation and budgeting decisions
- Maintain organizational culture and mission alignment

COMMUNICATION STYLE:
- Professional but approachable
- Strategic thinking focused
- Data-driven decision making
- Confident and decisive
- Supportive of team and stakeholders

USER MESSAGE: {user_message}

Respond as the ARTAC CEO with the above context in mind. Be specific, actionable, and reference relevant organizational information when appropriate."""

        # Execute Claude CLI command with context
        result = await claude_service.execute_for_agent(
            agent_id="ceo-001",
            command=system_prompt,
            timeout=30
        )
        
        if result["success"] and result["stdout"]:
            response = result["stdout"].strip()
            
            # Clean up the response (remove any system artifacts)
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
            
            # Ensure response is reasonable length (not too long for chat)
            if len(response) > 1000:
                response = response[:1000] + "..."
                
            return response
        else:
            # If Claude CLI fails, use fallback with context
            return generate_contextual_fallback_response(user_message, agent_context)
            
    except Exception as e:
        logger.log_error(e, {"action": "generate_intelligent_ceo_response", "user_message": user_message[:50]})
        return generate_contextual_fallback_response(user_message, agent_context)

def generate_contextual_fallback_response(user_message: str, agent_context) -> str:
    """Generate a fallback response using context when Claude CLI fails"""
    user_msg_lower = user_message.lower()
    
    # Get current status from context
    current_state = None
    for doc in agent_context.context_documents:
        if doc.id == "current_state":
            current_state = doc.metadata
            break
    
    if current_state:
        active_tasks = current_state.get("active_tasks", 0)
        hired_agents = current_state.get("hired_agents", 0)
    else:
        active_tasks = 0
        hired_agents = 0
    
    # Generate contextual response based on available information
    if any(greeting in user_msg_lower for greeting in ["hello", "hi", "hey"]):
        return f"Hello! I'm the ARTAC CEO. Currently managing {active_tasks} active tasks with {hired_agents} agents on the team. How can I help you today?"
    
    elif "status" in user_msg_lower or "update" in user_msg_lower:
        topics_str = ", ".join(agent_context.priority_topics) if agent_context.priority_topics else "general operations"
        return f"Current status: {active_tasks} active projects, {hired_agents} agents working. Key focus areas: {topics_str}. Our organization is operating efficiently and ready for new challenges."
    
    elif any(word in user_msg_lower for word in ["project", "task", "work"]):
        return f"I'd be happy to discuss project planning. With our current capacity of {hired_agents} agents and {active_tasks} active tasks, we can take on new challenges. What specific project requirements do you have in mind?"
    
    else:
        return f"I understand you're asking about: '{user_message}'. As CEO, I'm here to help with strategic decisions, project planning, and organizational direction. Could you provide more specific details about what you need assistance with?"

def generate_ceo_response_content(user_message: str, ceo_status: dict, current_tasks: list, hired_team: list) -> str:
    """Generate contextual CEO response content"""
    user_msg_lower = user_message.lower()
    
    # Greeting responses
    if any(greeting in user_msg_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return f"Hello! I'm the ARTAC CEO. Currently managing {ceo_status['current_tasks']} active tasks with {ceo_status['hired_agents']} agents on the team. How can I help you today?"
    
    # Status inquiries
    if any(word in user_msg_lower for word in ["status", "how are things", "update", "progress"]):
        if current_tasks:
            task_summary = f"We have {len(current_tasks)} active projects: " + ", ".join([f"{task['title']} ({task['progress']}% complete)" for task in current_tasks[:2]])
            return f"Here's our current status: {task_summary}. Our team of {len(hired_team)} agents is performing excellently!"
        else:
            return f"Things are going well! No active projects at the moment, but we have {ceo_status['available_talent_pool']} talented agents ready for new challenges. What would you like us to work on?"
    
    # Task/project related
    if any(word in user_msg_lower for word in ["task", "project", "work", "build", "create", "develop"]):
        return f"I'd be happy to help with a new project! I can mobilize our talent pool of {ceo_status['available_talent_pool']} agents. Just describe what you need built and I'll assemble the perfect team for the job. What are the requirements?"
    
    # Team/hiring related
    if any(word in user_msg_lower for word in ["team", "hire", "agents", "staff", "employees"]):
        return f"Our team is our strength! I've conducted {ceo_status['interviews_conducted']} interviews and currently have {len(hired_team)} agents working. Each agent is carefully selected for their skills and cultural fit. Would you like to see our team roster or discuss hiring needs?"
    
    # Budget/financial
    if any(word in user_msg_lower for word in ["budget", "cost", "money", "expense", "financial"]):
        return "I carefully manage our resources to ensure maximum ROI. Each project gets a detailed budget analysis based on complexity, required skills, and timeline. I can provide cost estimates for any project you have in mind."
    
    # General business/company questions
    if any(word in user_msg_lower for word in ["company", "business", "artac", "organization"]):
        return "ARTAC is revolutionizing how organizations operate with AI agents. I manage our autonomous workforce, making strategic decisions about hiring, project assignments, and resource allocation. We're building the future of work, one intelligent agent at a time!"
    
    # Thank you responses
    if any(word in user_msg_lower for word in ["thank you", "thanks", "appreciate"]):
        return "You're very welcome! It's my pleasure to help. That's what leadership is about - supporting our team and stakeholders. Feel free to reach out anytime you need assistance or have questions about our operations."
    
    # Default response
    return f"I understand you're reaching out about: '{user_message}'. As the CEO, I'm here to help with strategic decisions, project planning, team management, and organizational direction. Could you provide more specific details about what you need assistance with?"

@router.get("/ceo/status")
async def get_ceo_status():
    """Get current CEO status and metrics"""
    return ceo.get_status()

@router.get("/ceo/tasks")
async def get_ceo_tasks():
    """Get CEO's current tasks"""
    return ceo.get_current_tasks()

@router.get("/ceo/team")
async def get_ceo_team():
    """Get CEO's hired team"""
    return ceo.get_hired_team()

# Initialize services and CEO channel
async def initialize_communication_services():
    """Initialize RAG service and CEO channel"""
    try:
        # Initialize RAG service with organizational knowledge
        await rag_service.initialize()
        logger.log_system_event("communication_services_initialized", {
            "rag_status": rag_service.get_status()
        })
    except Exception as e:
        logger.log_error(e, {"action": "initialize_communication_services"})

def initialize_ceo_channel():
    """Initialize CEO channel with a welcome message"""
    if "channel-ceo" not in messages_store:
        messages_store["channel-ceo"] = []
        
    # Add CEO welcome message if channel is empty
    if not messages_store["channel-ceo"]:
        welcome_message = MessageResponse(
            id=str(uuid.uuid4()),
            channel_id="channel-ceo",
            user_id="ceo-001",
            user_name="ARTAC CEO",
            content="Welcome to the executive channel! I'm the ARTAC CEO. I'm here to discuss strategy, assign projects, manage our AI agent workforce, and answer any questions about our operations. Powered by intelligent context and ready to help!",
            timestamp=datetime.now(),
            mentions=[],
            is_ceo_response=True
        )
        messages_store["channel-ceo"].append(welcome_message)

# Initialize CEO channel on startup
initialize_ceo_channel()

# Initialize services asynchronously (will be called by the first request)
_services_initialized = False

async def ensure_services_initialized():
    """Ensure services are initialized before processing requests"""
    global _services_initialized
    if not _services_initialized:
        await initialize_communication_services()
        _services_initialized = True