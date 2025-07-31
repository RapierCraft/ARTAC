"""
Voice Service - ElevenLabs integration for CEO and agent voice interactions
"""

import io
import asyncio
import tempfile
import uuid
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime

try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    # Create stub classes for when ElevenLabs is not available
    class VoiceSettings:
        def __init__(self, stability=0.8, similarity_boost=0.8, style=0.3, use_speaker_boost=True):
            pass
    class ElevenLabs:
        pass
    class Voice:
        pass

from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class VoiceProfile:
    """Voice profile for an agent"""
    
    def __init__(self, agent_id: str, agent_name: str, role: str, voice_id: str, voice_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.role = role
        self.voice_id = voice_id
        self.voice_name = voice_name
        self.personality_traits = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "voice_id": self.voice_id,
            "voice_name": self.voice_name
        }


class VoiceService:
    """Service for voice synthesis and agent voice interactions"""
    
    def __init__(self):
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self.initialized = False
        self.available_voices = []
        self.client = None
        
        # Voice assignments by role
        self.role_voice_map = {
            "ceo": {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"},  # Professional female
            "developer": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella"},  # Friendly female
            "devops": {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni"},  # Professional male
            "security": {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold"},  # Authoritative male
            "designer": {"voice_id": "ThT5KcBeYPX3keUQqHPh", "name": "Dorothy"},  # Creative female
            "architect": {"voice_id": "29vD33N1CtxCmqQRPOHJ", "name": "Drew"},  # Thoughtful male
            "analyst": {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlotte"},  # Analytical female
            "tester": {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam"},  # Detail-oriented male
            "project_manager": {"voice_id": "oWAxZDx7w5VEj9dCyTzz", "name": "Grace"},  # Leadership female
            "data_scientist": {"voice_id": "N2lVS1w4EtoT3dr4eOWO", "name": "Callum"}  # Analytical male
        }
    
    async def initialize(self) -> bool:
        """Initialize ElevenLabs voice service"""
        
        if not ELEVENLABS_AVAILABLE:
            logger.log_error(Exception("ElevenLabs not installed"), {"action": "initialize_voice_service"})
            return False
        
        if not settings.ELEVENLABS_API_KEY:
            logger.log_system_event("voice_service_no_api_key", {
                "message": "ElevenLabs API key not provided, voice features disabled"
            })
            return False
        
        try:
            # Initialize ElevenLabs client
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            
            # Try to get available voices (skip if permission is missing)
            try:
                self.available_voices = self.client.voices.get_all()
                voice_count = len(self.available_voices.voices) if hasattr(self.available_voices, 'voices') else 0
            except Exception as voice_error:
                logger.log_system_event("voice_permission_limited", {
                    "message": "Limited API key permissions - continuing with predefined voices",
                    "error": str(voice_error)
                })
                voice_count = len(self.role_voice_map)
                self.available_voices = []
            
            logger.log_system_event("voice_service_initialized", {
                "available_voices": voice_count,
                "status": "ready"
            })
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_voice_service"})
            return False
    
    def assign_voice_to_agent(self, agent_id: str, agent_name: str, role: str) -> Optional[VoiceProfile]:
        """Assign appropriate voice to an agent based on their role"""
        
        if not self.initialized:
            return None
        
        # Get voice for role, fallback to CEO voice
        voice_config = self.role_voice_map.get(role, self.role_voice_map["ceo"])
        
        voice_profile = VoiceProfile(
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            voice_id=voice_config["voice_id"],
            voice_name=voice_config["name"]
        )
        
        self.voice_profiles[agent_id] = voice_profile
        
        logger.log_agent_action(
            agent_id=agent_id,
            action="voice_assigned",
            details={
                "voice_name": voice_config["name"],
                "role": role
            }
        )
        
        return voice_profile
    
    async def generate_speech(self, agent_id: str, text: str, emotion: str = "neutral") -> Optional[bytes]:
        """Generate speech for an agent"""
        
        if not self.initialized:
            logger.log_error(Exception("Voice service not initialized"), {"agent_id": agent_id})
            return None
        
        voice_profile = self.voice_profiles.get(agent_id)
        if not voice_profile:
            logger.log_error(Exception("No voice profile found"), {"agent_id": agent_id})
            return None
        
        try:
            # Adjust voice settings based on emotion and role
            voice_settings = self._get_voice_settings(voice_profile.role, emotion)
            
            # Generate audio using the new client API
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_profile.voice_id,
                text=text,
                model_id="eleven_monolingual_v1",
                voice_settings=voice_settings
            )
            
            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            
            logger.log_agent_action(
                agent_id=agent_id,
                action="speech_generated",
                details={
                    "text_length": len(text),
                    "emotion": emotion,
                    "voice_name": voice_profile.voice_name
                }
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.log_error(e, {
                "action": "generate_speech",
                "agent_id": agent_id,
                "text": text[:50]
            })
            return None
    
    def _get_voice_settings(self, role: str, emotion: str) -> VoiceSettings:
        """Get voice settings based on role and emotion"""
        
        # Base settings by role
        role_settings = {
            "ceo": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.3},
            "developer": {"stability": 0.7, "similarity_boost": 0.7, "style": 0.4},
            "security": {"stability": 0.9, "similarity_boost": 0.8, "style": 0.2},  # More serious
            "designer": {"stability": 0.6, "similarity_boost": 0.7, "style": 0.6},  # More expressive
            "project_manager": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.4}
        }
        
        settings_config = role_settings.get(role, role_settings["ceo"])
        
        # Adjust for emotion
        if emotion == "excited":
            settings_config["style"] += 0.2
            settings_config["stability"] -= 0.1
        elif emotion == "concerned":
            settings_config["stability"] += 0.1
            settings_config["style"] -= 0.1
        elif emotion == "confident":
            settings_config["stability"] += 0.1
            settings_config["similarity_boost"] += 0.1
        
        # Clamp values
        for key in settings_config:
            settings_config[key] = max(0.0, min(1.0, settings_config[key]))
        
        return VoiceSettings(
            stability=settings_config["stability"],
            similarity_boost=settings_config["similarity_boost"],
            style=settings_config["style"],
            use_speaker_boost=True
        )
    
    async def ceo_respond(self, message: str, context: str = "") -> Dict[str, Any]:
        """Generate CEO voice response to a message"""
        
        # Get or create CEO voice profile
        ceo_id = "ceo-001"
        if ceo_id not in self.voice_profiles:
            self.assign_voice_to_agent(ceo_id, "ARTAC CEO", "ceo")
        
        # Generate CEO response text (this would integrate with Claude CLI)
        response_text = await self._generate_ceo_response_text(message, context)
        
        # Generate speech
        audio_data = await self.generate_speech(ceo_id, response_text, "confident")
        
        # Save to temporary file
        audio_file = None
        if audio_data:
            audio_file = await self._save_audio_temp(audio_data, f"ceo_response_{uuid.uuid4().hex[:8]}")
        
        return {
            "agent_id": ceo_id,
            "agent_name": "ARTAC CEO",
            "response_text": response_text,
            "audio_file": audio_file,
            "voice_profile": self.voice_profiles[ceo_id].to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def agent_respond(self, agent_id: str, agent_name: str, role: str, message: str, context: str = "") -> Dict[str, Any]:
        """Generate agent voice response to a message"""
        
        # Get or create agent voice profile
        if agent_id not in self.voice_profiles:
            self.assign_voice_to_agent(agent_id, agent_name, role)
        
        # Generate agent response text (this would integrate with Claude CLI + agent persona)
        response_text = await self._generate_agent_response_text(agent_id, agent_name, role, message, context)
        
        # Determine emotion based on role and context
        emotion = self._determine_emotion(role, message, context)
        
        # Generate speech
        audio_data = await self.generate_speech(agent_id, response_text, emotion)
        
        # Save to temporary file
        audio_file = None
        if audio_data:
            audio_file = await self._save_audio_temp(audio_data, f"agent_{agent_id}_{uuid.uuid4().hex[:8]}")
        
        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "role": role,
            "response_text": response_text,
            "audio_file": audio_file,
            "voice_profile": self.voice_profiles[agent_id].to_dict(),
            "emotion": emotion,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_ceo_response_text(self, message: str, context: str) -> str:
        """Generate CEO response text (placeholder - would integrate with Claude CLI)"""
        
        # This is a simplified version - in reality, this would:
        # 1. Use Ollama to create a CEO persona prompt
        # 2. Send to Claude CLI for high-quality response
        # 3. Return the response
        
        ceo_responses = {
            "task": "Excellent! I'll analyze this task and begin the hiring process immediately. Let me review our talent pool and identify the right candidates for interviews.",
            "status": "Our organization is performing well. We have strong talent across all departments and are ready to take on challenging projects.",
            "meeting": "Absolutely! I'll schedule a team meeting to discuss this. Let me gather the relevant stakeholders.",
            "goal": "That's a great strategic goal. I'll work with the team to break this down into actionable items and assign the right people.",
            "default": "Thank you for bringing this to my attention. I'll give this the consideration it deserves and get back to you with a comprehensive plan."
        }
        
        # Simple keyword matching (would be much more sophisticated with Claude CLI)
        message_lower = message.lower()
        if "task" in message_lower or "project" in message_lower:
            return ceo_responses["task"]
        elif "status" in message_lower or "how" in message_lower:
            return ceo_responses["status"]
        elif "meeting" in message_lower or "call" in message_lower:
            return ceo_responses["meeting"]
        elif "goal" in message_lower or "objective" in message_lower:
            return ceo_responses["goal"]
        else:
            return ceo_responses["default"]
    
    async def _generate_agent_response_text(self, agent_id: str, agent_name: str, role: str, message: str, context: str) -> str:
        """Generate agent response text based on their role and personality"""
        
        role_responses = {
            "developer": f"Hi! I'm {agent_name}, a developer on the team. I'd be happy to discuss the technical aspects of this project and share my thoughts on implementation.",
            "security": f"Hello, I'm {agent_name} from the security team. I want to make sure we address all security considerations in this initiative.",
            "devops": f"Hey there! {agent_name} here from DevOps. I can help with the infrastructure and deployment aspects of what you're planning.",
            "designer": f"Hi! I'm {agent_name}, the designer. I'm excited to contribute to the user experience and visual design of this project.",
            "project_manager": f"Hello! I'm {agent_name}, project manager. I'll help coordinate the team and ensure we meet our objectives on time."
        }
        
        return role_responses.get(role, f"Hello! I'm {agent_name}. I'm here to help with whatever you need.")
    
    def _determine_emotion(self, role: str, message: str, context: str) -> str:
        """Determine appropriate emotion based on role and context"""
        
        message_lower = message.lower()
        
        if "urgent" in message_lower or "critical" in message_lower:
            return "concerned"
        elif "great" in message_lower or "excellent" in message_lower:
            return "excited"
        elif role == "ceo":
            return "confident"
        elif role == "security" and ("security" in message_lower or "risk" in message_lower):
            return "concerned"
        else:
            return "neutral"
    
    async def _save_audio_temp(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to temporary file and return path"""
        
        try:
            temp_dir = tempfile.gettempdir()
            file_path = f"{temp_dir}/{filename}.mp3"
            
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            logger.log_system_event("audio_file_saved", {
                "file_path": file_path,
                "file_size": len(audio_data)
            })
            
            return file_path
            
        except Exception as e:
            logger.log_error(e, {"action": "save_audio_temp", "filename": filename})
            return None
    
    def get_voice_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all voice profiles"""
        return {
            agent_id: profile.to_dict() 
            for agent_id, profile in self.voice_profiles.items()
        }
    
    async def test_voice_generation(self) -> Dict[str, Any]:
        """Test voice generation with CEO"""
        
        if not self.initialized:
            return {"status": "error", "message": "Voice service not initialized"}
        
        try:
            # Test CEO voice
            test_response = await self.ceo_respond("Hello, this is a test of the voice system.")
            
            return {
                "status": "success",
                "message": "Voice generation test completed",
                "test_response": test_response
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "test_voice_generation"})
            return {"status": "error", "message": str(e)}


# Global voice service instance
voice_service = VoiceService()