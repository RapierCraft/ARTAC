"""
Whisper Speech-to-Text Service
Local speech recognition using OpenAI Whisper
"""

import whisper
import tempfile
import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)


class WhisperService:
    """Service for speech-to-text using Whisper"""
    
    def __init__(self):
        self.model = None
        self.initialized = False
        self.model_name = "base"  # base model for speed, can upgrade to "large" for accuracy
    
    async def initialize(self) -> bool:
        """Initialize Whisper model"""
        try:
            logger.log_system_event("whisper_initializing", {"model": self.model_name})
            
            # Load Whisper model (this runs in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                whisper.load_model, 
                self.model_name
            )
            
            self.initialized = True
            logger.log_system_event("whisper_initialized", {
                "model": self.model_name,
                "status": "ready"
            })
            return True
            
        except Exception as e:
            logger.log_error(e, {"action": "initialize_whisper"})
            return False
    
    async def transcribe_audio(self, audio_file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., "en", "es", "fr")
            
        Returns:
            Dict with transcription results
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "Whisper not initialized",
                "text": ""
            }
        
        try:
            logger.log_system_event("whisper_transcribing", {
                "file_path": audio_file_path,
                "language": language
            })
            
            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_file_path,
                language
            )
            
            # Extract text and confidence
            text = result["text"].strip()
            
            logger.log_system_event("whisper_transcribed", {
                "text_length": len(text),
                "language": result.get("language", language),
                "success": True
            })
            
            return {
                "success": True,
                "text": text,
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "confidence": self._calculate_average_confidence(result.get("segments", []))
            }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "transcribe_audio",
                "file_path": audio_file_path
            })
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def _transcribe_sync(self, audio_file_path: str, language: str) -> Dict[str, Any]:
        """Synchronous transcription for executor"""
        return self.model.transcribe(
            audio_file_path,
            language=language,
            task="transcribe",
            verbose=False
        )
    
    def _calculate_average_confidence(self, segments: list) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        # Whisper doesn't always provide confidence scores
        # This is a placeholder for when they're available
        confidences = []
        for segment in segments:
            if "confidence" in segment:
                confidences.append(segment["confidence"])
        
        return sum(confidences) / len(confidences) if confidences else 0.8  # Default confidence
    
    async def transcribe_audio_bytes(self, audio_bytes: bytes, format: str = "wav") -> Dict[str, Any]:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Dict with transcription results
        """
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the temporary file
            result = await self.transcribe_audio(temp_file_path)
            return result
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.log_error(e, {"action": "cleanup_temp_file", "file": temp_file_path})
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "initialized": self.initialized,
            "model": self.model_name,
            "available": self.model is not None
        }


# Global Whisper service instance
whisper_service = WhisperService()