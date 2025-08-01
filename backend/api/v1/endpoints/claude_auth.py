"""
ARTAC Claude Authentication API
Handles Claude CLI authentication setup
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

from services.claude_code_service import ClaudeCodeService
from core.logging import get_logger
from core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/claude-auth", tags=["claude-auth"])

# Initialize Claude service
claude_service = ClaudeCodeService()

class AuthTokenRequest(BaseModel):
    token: str

class ApiKeyRequest(BaseModel):
    api_key: str

@router.get("/url")
async def get_authentication_url() -> Dict[str, Any]:
    """Get Claude CLI authentication URL"""
    try:
        result = claude_service.get_authentication_url()
        
        if result["success"]:
            logger.log_system_event("auth_url_requested", {
                "auth_url": result["auth_url"]
            })
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.log_error(e, {"action": "get_authentication_url"})
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token")
async def setup_authentication_token(request: AuthTokenRequest) -> Dict[str, Any]:
    """Setup Claude CLI authentication with provided token"""
    try:
        result = await claude_service.setup_authentication_token(request.token)
        
        if result["success"]:
            logger.log_system_event("auth_token_success", {
                "message": "Claude CLI authenticated successfully"
            })
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.log_error(e, {"action": "setup_authentication_token"})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_authentication_status() -> Dict[str, Any]:
    """Check Claude CLI authentication status"""
    try:
        # Check if API key is configured
        if os.environ.get('ANTHROPIC_API_KEY') or settings.ANTHROPIC_API_KEY:
            return {
                "success": True,
                "auth_method": "api_key",
                "message": "Claude CLI authenticated with API key"
            }
        
        # This will trigger the authentication check
        claude_service._check_claude_availability()
        
        return {
            "success": True,
            "auth_method": "oauth",
            "message": "Check logs for OAuth authentication status"
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "get_authentication_status"})
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api-key")
async def setup_api_key(request: ApiKeyRequest) -> Dict[str, Any]:
    """Setup Claude CLI authentication with API key"""
    try:
        # Set the API key as an environment variable
        os.environ['ANTHROPIC_API_KEY'] = request.api_key
        
        # Test the API key by checking Claude availability
        claude_service._check_claude_availability()
        
        logger.log_system_event("api_key_configured", {
            "message": "Claude CLI configured with API key"
        })
        
        return {
            "success": True,
            "message": "API key configured successfully"
        }
        
    except Exception as e:
        # Remove the API key if configuration failed
        os.environ.pop('ANTHROPIC_API_KEY', None)
        logger.log_error(e, {"action": "setup_api_key"})
        raise HTTPException(status_code=500, detail=str(e))