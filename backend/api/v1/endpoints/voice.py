"""
Voice Interface Endpoints - Talk to CEO and agents
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from services.voice_service import voice_service
from services.whisper_service import whisper_service
from services.ceo_agent import ceo
from services.talent_pool import talent_pool
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class VoiceMessage(BaseModel):
    message: str
    context: Optional[str] = ""
    emotion: Optional[str] = "neutral"


class TaskAssignment(BaseModel):
    message: str
    title: str
    description: str
    required_skills: Optional[list] = []
    priority: str = "medium"
    estimated_hours: int = 8


@router.get("/voice/status")
async def get_voice_status() -> Dict[str, Any]:
    """Get voice service status and available voices"""
    
    return {
        "voice_service_initialized": voice_service.initialized,
        "available_voices": len(voice_service.voice_profiles),
        "voice_profiles": voice_service.get_voice_profiles(),
        "supported_emotions": ["neutral", "excited", "concerned", "confident"],
        "message": "Voice service ready" if voice_service.initialized else "Voice service not available"
    }


@router.post("/voice/talk-to-ceo")
async def talk_to_ceo(message: VoiceMessage) -> Dict[str, Any]:
    """Have a voice conversation with the CEO"""
    
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    logger.log_system_event("voice_conversation_ceo", {
        "message_length": len(message.message),
        "context": message.context
    })
    
    try:
        # Generate CEO voice response
        response = await voice_service.ceo_respond(message.message, message.context)
        
        return {
            "status": "success",
            "conversation_type": "ceo_voice_call",
            "ceo_response": response,
            "instructions": {
                "audio_file": "Download the audio file to hear the CEO's response",
                "text_response": "Text version also provided for reference"
            }
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "talk_to_ceo"})
        raise HTTPException(status_code=500, detail=f"Failed to generate CEO response: {str(e)}")


@router.post("/voice/assign-task-to-ceo")
async def assign_task_to_ceo(task: TaskAssignment) -> Dict[str, Any]:
    """Assign a task to the CEO via voice interface"""
    
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    logger.log_system_event("voice_task_assignment", {
        "title": task.title,
        "message": task.message
    })
    
    try:
        # 1. Assign the task to CEO (triggers hiring process)
        ceo_task = ceo.receive_task(
            title=task.title,
            description=task.description,
            required_skills=task.required_skills,
            priority=task.priority,
            estimated_hours=task.estimated_hours
        )
        
        # 2. Generate CEO voice response about receiving the task
        ceo_context = f"Task assigned: {task.title}. CEO is now analyzing requirements and beginning hiring process."
        ceo_response = await voice_service.ceo_respond(task.message, ceo_context)
        
        return {
            "status": "task_assigned_with_voice",
            "task_id": ceo_task.id,
            "ceo_voice_response": ceo_response,
            "task_details": {
                "title": task.title,
                "status": "received",
                "ceo_action": "analyzing_and_hiring"
            },
            "next_steps": [
                "CEO will analyze task requirements",
                "Interview candidates from talent pool", 
                "Hire best candidates",
                "Assign task to hired team"
            ]
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "assign_task_to_ceo"})
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.post("/voice/talk-to-agent/{agent_id}")
async def talk_to_agent(agent_id: str, message: VoiceMessage) -> Dict[str, Any]:
    """Have a voice conversation with a specific agent"""
    
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    # Get agent details
    agent = talent_pool.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    logger.log_agent_action(
        agent_id=agent_id,
        action="voice_conversation",
        details={"message_length": len(message.message)}
    )
    
    try:
        # Generate agent voice response
        response = await voice_service.agent_respond(
            agent_id=agent.id,
            agent_name=agent.name,
            role=agent.role.value,
            message=message.message,
            context=message.context
        )
        
        return {
            "status": "success",
            "conversation_type": "agent_voice_call",
            "agent_info": {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role.value,
                "status": agent.status.value
            },
            "agent_response": response
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "talk_to_agent", "agent_id": agent_id})
        raise HTTPException(status_code=500, detail=f"Failed to generate agent response: {str(e)}")


@router.post("/voice/team-meeting")
async def start_team_meeting(message: VoiceMessage) -> Dict[str, Any]:
    """Start a voice-enabled team meeting with CEO and available agents"""
    
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    logger.log_system_event("voice_team_meeting", {
        "message": message.message,
        "context": message.context
    })
    
    try:
        # Get CEO and some available agents for the meeting
        available_agents = talent_pool.get_available_agents()[:5]  # Max 5 for demo
        
        meeting_participants = []
        
        # CEO opens the meeting
        ceo_context = f"Team meeting started. Topic: {message.message}. Participants: {len(available_agents)} team members."
        ceo_response = await voice_service.ceo_respond(
            f"Team, I've called this meeting to discuss: {message.message}",
            ceo_context
        )
        
        meeting_participants.append({
            "role": "meeting_host",
            "participant": "ARTAC CEO",
            "response": ceo_response
        })
        
        # Each agent responds briefly
        for agent in available_agents[:3]:  # Limit to 3 for demo
            agent_response = await voice_service.agent_respond(
                agent_id=agent.id,
                agent_name=agent.name,
                role=agent.role.value,
                message=f"Meeting topic: {message.message}",
                context="team_meeting"
            )
            
            meeting_participants.append({
                "role": "team_member",
                "participant": f"{agent.name} ({agent.role.value})",
                "response": agent_response
            })
        
        return {
            "status": "meeting_started",
            "meeting_type": "voice_team_meeting",
            "topic": message.message,
            "participants_count": len(meeting_participants),
            "meeting_responses": meeting_participants,
            "instructions": {
                "message": "Download each audio file to hear the meeting participants",
                "order": "CEO speaks first, then team members respond"
            }
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "start_team_meeting"})
        raise HTTPException(status_code=500, detail=f"Failed to start meeting: {str(e)}")


@router.get("/voice/download-audio/{filename}")
async def download_audio(filename: str):
    """Download generated audio file"""
    
    # Security: Only allow downloading from temp directory with specific pattern
    if not filename.endswith('.mp3') or '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    import tempfile
    file_path = f"{tempfile.gettempdir()}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@router.post("/voice/test-generation")
async def test_voice_generation() -> Dict[str, Any]:
    """Test voice generation system"""
    
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available - check ElevenLabs API key")
    
    try:
        test_result = await voice_service.test_voice_generation()
        return test_result
        
    except Exception as e:
        logger.log_error(e, {"action": "test_voice_generation"})
        raise HTTPException(status_code=500, detail=f"Voice test failed: {str(e)}")


@router.get("/voice/call-log")
async def get_call_log() -> Dict[str, Any]:
    """Get history of voice interactions"""
    
    # This would normally be stored in database
    # For now, return current voice profiles as call log
    
    return {
        "total_voice_interactions": len(voice_service.voice_profiles),
        "active_voice_profiles": voice_service.get_voice_profiles(),
        "supported_roles": list(voice_service.role_voice_map.keys()),
        "voice_features": [
            "CEO conversations",
            "Agent conversations", 
            "Team meetings",
            "Task assignments via voice",
            "Multiple emotions and personalities"
        ]
    }


# === WHISPER STT ENDPOINTS ===

@router.get("/whisper/status")
async def get_whisper_status() -> Dict[str, Any]:
    """Get Whisper STT service status"""
    
    status = whisper_service.get_status()
    
    return {
        "whisper_service_initialized": status["initialized"],
        "model": status["model"],
        "available": status["available"],
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        "supported_formats": ["wav", "mp3", "m4a", "flac", "ogg"],
        "message": "Whisper STT ready" if status["available"] else "Whisper STT not available"
    }


@router.post("/whisper/transcribe-file")
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    language: str = Form("en")
) -> Dict[str, Any]:
    """Transcribe uploaded audio file using Whisper STT"""
    
    if not whisper_service.initialized:
        raise HTTPException(status_code=503, detail="Whisper service not available")
    
    # Validate file type
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/flac", "audio/ogg"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format. Allowed: {allowed_types}")
    
    logger.log_system_event("whisper_transcription", {
        "filename": audio_file.filename,
        "content_type": audio_file.content_type,
        "language": language
    })
    
    try:
        # Read audio file bytes
        audio_bytes = await audio_file.read()
        
        # Determine format from content type
        format_map = {
            "audio/wav": "wav",
            "audio/mpeg": "mp3", 
            "audio/mp3": "mp3",
            "audio/m4a": "m4a",
            "audio/flac": "flac",
            "audio/ogg": "ogg"
        }
        audio_format = format_map.get(audio_file.content_type, "wav")
        
        # Transcribe audio
        result = await whisper_service.transcribe_audio_bytes(audio_bytes, audio_format)
        
        if result["success"]:
            return {
                "status": "transcribed",
                "text": result["text"],
                "language": result.get("language", language),
                "confidence": result.get("confidence", 0.0),
                "segments": result.get("segments", []),
                "file_info": {
                    "filename": audio_file.filename,
                    "format": audio_format,
                    "size_bytes": len(audio_bytes)
                }
            }
        else:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error(e, {"action": "transcribe_audio_file"})
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/whisper/transcribe-and-respond")
async def transcribe_and_respond(
    audio_file: UploadFile = File(...),
    conversation_mode: str = Form("ceo"),
    language: str = Form("en")
) -> Dict[str, Any]:
    """Complete STT->Claude->TTS pipeline: Transcribe audio, get intelligent response, generate speech"""
    
    if not whisper_service.initialized:
        raise HTTPException(status_code=503, detail="Whisper service not available") 
        
    if not voice_service.initialized:
        raise HTTPException(status_code=503, detail="Voice service not available")
    
    logger.log_system_event("full_voice_pipeline", {
        "filename": audio_file.filename,
        "conversation_mode": conversation_mode,
        "language": language
    })
    
    try:
        # Step 1: Transcribe audio using Whisper STT
        audio_bytes = await audio_file.read()
        format_map = {
            "audio/wav": "wav",
            "audio/mpeg": "mp3", 
            "audio/mp3": "mp3",
            "audio/m4a": "m4a",
            "audio/flac": "flac",
            "audio/ogg": "ogg"
        }
        audio_format = format_map.get(audio_file.content_type, "wav")
        
        transcription_result = await whisper_service.transcribe_audio_bytes(audio_bytes, audio_format)
        
        if not transcription_result["success"]:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcription_result.get('error')}")
        
        transcribed_text = transcription_result["text"]
        
        # Step 2: Generate intelligent response (this will integrate with Claude CLI later)
        response_data = None
        
        if conversation_mode == "task-assignment":
            # Create task assignment payload
            task_data = TaskAssignment(
                message=transcribed_text,
                title=f"Voice Task: {transcribed_text[:50]}...",
                description=transcribed_text,
                required_skills=["general"],
                priority="medium",
                estimated_hours=8
            )
            
            # Process as task assignment
            ceo_task = ceo.receive_task(
                title=task_data.title,
                description=task_data.description,
                required_skills=task_data.required_skills,
                priority=task_data.priority,
                estimated_hours=task_data.estimated_hours
            )
            
            ceo_context = f"Task assigned via voice: {task_data.title}. CEO analyzing requirements and beginning hiring process."
            response_data = await voice_service.ceo_respond(transcribed_text, ceo_context)
            
        elif conversation_mode == "team-meeting":
            # Start team meeting
            available_agents = talent_pool.get_available_agents()[:3]
            ceo_context = f"Team meeting started via voice. Topic: {transcribed_text}. Participants: {len(available_agents)} team members."
            response_data = await voice_service.ceo_respond(
                f"Team, I've called this meeting to discuss: {transcribed_text}",
                ceo_context
            )
            
        else:
            # Default to CEO conversation
            response_data = await voice_service.ceo_respond(transcribed_text, conversation_mode)
        
        # Step 3: Return complete pipeline result
        return {
            "status": "pipeline_complete",
            "pipeline_steps": ["whisper_stt", "intelligent_response", "elevenlabs_tts"],
            "transcription": {
                "text": transcribed_text,
                "language": transcription_result.get("language", language),
                "confidence": transcription_result.get("confidence", 0.0)
            },
            "response": response_data,
            "conversation_mode": conversation_mode,
            "instructions": {
                "message": "Complete voice pipeline executed successfully",
                "audio_download": "Use the audio_file path in the response to download the TTS audio"
            }
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "transcribe_and_respond"})
        raise HTTPException(status_code=500, detail=f"Voice pipeline failed: {str(e)}")


@router.post("/whisper/test-transcription")
async def test_whisper_transcription() -> Dict[str, Any]:
    """Test Whisper transcription system"""
    
    if not whisper_service.initialized:
        raise HTTPException(status_code=503, detail="Whisper service not available")
    
    try:
        # Create a simple test audio (silence) to test the system
        import tempfile
        import wave
        import numpy as np
        
        # Generate 2 seconds of silence as test audio
        sample_rate = 16000
        duration = 2
        samples = np.zeros(sample_rate * duration, dtype=np.int16)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            
            # Test transcription
            result = await whisper_service.transcribe_audio(temp_file.name)
            
            return {
                "status": "test_complete",
                "whisper_available": result["success"],
                "test_result": result,
                "message": "Whisper STT test completed successfully" if result["success"] else "Whisper STT test failed"
            }
            
    except Exception as e:
        logger.log_error(e, {"action": "test_whisper_transcription"})
        raise HTTPException(status_code=500, detail=f"Whisper test failed: {str(e)}")