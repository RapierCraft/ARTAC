"""
ARTAC Claude Authentication API
Handles Claude CLI authentication setup
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from services.claude_code_service import ClaudeCodeService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/claude-auth", tags=["claude-auth"])

# Initialize Claude service
claude_service = ClaudeCodeService()

class AuthTokenRequest(BaseModel):
    token: str

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
        # This will trigger the authentication check
        claude_service._check_claude_availability()
        
        return {
            "success": True,
            "message": "Check logs for authentication status"
        }
        
    except Exception as e:
        logger.log_error(e, {"action": "get_authentication_status"})
        raise HTTPException(status_code=500, detail=str(e))