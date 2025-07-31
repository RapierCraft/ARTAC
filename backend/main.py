"""
RAISC - RAG-Enabled AI Software Company
Main FastAPI application entry point
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import settings
from core.database import database
from core.logging import setup_logging
from api.v1.router import api_router
from services.agent_manager import AgentManager
from services.rag_service import RAGService
from services.process_manager import process_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    logger.info("🚀 Starting RAISC application...")
    
    # Initialize database
    await database.connect()
    logger.info("✅ Database connected")
    
    # Initialize services
    app.state.agent_manager = AgentManager()
    app.state.rag_service = RAGService()
    
    await app.state.rag_service.initialize()
    logger.info("✅ RAG service initialized")
    
    await app.state.agent_manager.initialize()
    logger.info("✅ Agent manager initialized")
    
    # Start process monitoring
    monitor_task = asyncio.create_task(process_manager.monitor_processes())
    app.state.monitor_task = monitor_task
    logger.info("✅ Process monitoring started")
    
    logger.info("🎯 RAISC application ready - All Claude CLI sessions will run in headless mode!")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down RAISC application...")
    
    # Cancel monitoring task
    if hasattr(app.state, 'monitor_task'):
        app.state.monitor_task.cancel()
        try:
            await app.state.monitor_task
        except asyncio.CancelledError:
            pass
    
    # Shutdown all Claude CLI processes (unless configured to persist)
    if not settings.PERSIST_CLAUDE_SESSIONS:
        await process_manager.shutdown_all_processes()
        logger.info("✅ Clean shutdown completed - All headless processes terminated")
    else:
        logger.info("✅ Clean shutdown completed - Claude sessions persisted")
    
    # Shutdown other services
    await app.state.agent_manager.shutdown()
    await database.disconnect()


# Create FastAPI application
app = FastAPI(
    title="RAISC - RAG-Enabled AI Software Company",
    description="A fully autonomous, hierarchical AI development organization",
    version="0.1.0-alpha",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAISC - RAG-Enabled AI Software Company",
        "version": "0.1.0-alpha",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        await database.execute("SELECT 1")
        
        # Check core services
        agent_status = app.state.agent_manager.get_status()
        rag_status = app.state.rag_service.get_status()
        
        return {
            "status": "healthy",
            "database": "connected",
            "agents": agent_status,
            "rag": rag_status,
            "timestamp": "2024-01-01T00:00:00Z"  # This would be dynamic
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


def setup_signal_handlers():
    """Setup signal handlers to prevent terminal issues"""
    if sys.platform != 'win32':
        # Ignore SIGHUP to prevent terminal disconnect issues
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        # Prevent signal propagation to child processes
        signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        signal.signal(signal.SIGTTIN, signal.SIG_IGN)


if __name__ == "__main__":
    # Setup signal handlers before running
    setup_signal_handlers()
    
    # Determine reload setting based on SAFE_RELOAD_MODE
    reload_enabled = settings.DEBUG and not settings.SAFE_RELOAD_MODE
    
    if settings.SAFE_RELOAD_MODE and settings.DEBUG:
        logger.info("Safe reload mode: Auto-reload disabled to prevent Claude session conflicts")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=reload_enabled,
        reload_excludes=['/tmp/raisc-agent-*', '**/venv/**', '**/__pycache__/**'] if reload_enabled else None,
        log_level=settings.LOG_LEVEL.lower()
    )