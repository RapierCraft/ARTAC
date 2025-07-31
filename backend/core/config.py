"""
ARTAC Configuration Management
Centralized configuration using Pydantic settings
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    PROJECT_NAME: str = "ARTAC"
    VERSION: str = "0.1.0-alpha"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database (optional for basic functionality)
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis (optional for basic functionality)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security (optional for basic functionality)
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ENCRYPTION_KEY: Optional[str] = None
    
    # AI Services - Claude Code CLI Integration
    CLAUDE_CODE_PATH: str = "claude"  # Path to claude command
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Voice Interface Configuration
    DEFAULT_VOICE_EMOTION: str = "neutral"
    VOICE_GENERATION_TIMEOUT: int = 30
    
    # Agent Configuration
    MAX_AGENTS: int = 100
    AGENT_TIMEOUT: int = 300
    CLAUDE_CODE_TIMEOUT: int = 600  # 10 minutes for complex tasks
    DEFAULT_CLAUDE_MODEL: str = "claude-4-sonnet"
    CLAUDE_HEADLESS_MODE: bool = True  # Run Claude CLI in headless mode
    PERSIST_CLAUDE_SESSIONS: bool = False  # Keep Claude sessions alive after backend shutdown
    SAFE_RELOAD_MODE: bool = False  # Disable auto-reload to prevent Claude session conflicts
    
    # RAG Configuration
    VECTOR_DB_PATH: str = "./vector_db"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    MAX_CONTEXT_LENGTH: int = 128000
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Voice Interface
    STT_MODEL: str = "whisper-1"
    TTS_VOICE: str = "alloy"
    VOICE_TIMEOUT: int = 30
    
    # Git Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # External APIs
    STACKOVERFLOW_API_KEY: Optional[str] = None
    CVE_API_ENDPOINT: str = "https://cve.circl.lu/api/"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3001
    ENABLE_METRICS: bool = True
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v):
        if isinstance(v, str):
            return v
        return f"postgresql://{v}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()