"""
ARTAC Logging Configuration
Structured logging with multiple outputs
"""

import logging
import sys
from typing import Dict, Any
import structlog
from core.config import settings


def setup_logging():
    """Configure structured logging for the application"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG 
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class ARTACLogger:
    """Custom logger for ARTAC with agent context"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def log_agent_action(self, agent_id: str, action: str, details: Dict[str, Any] = None):
        """Log agent actions with context"""
        self.logger.info(
            "Agent action",
            agent_id=agent_id,
            action=action,
            details=details or {}
        )
    
    def log_user_interaction(self, user_id: str, command: str, response_time: float):
        """Log user interactions"""
        self.logger.info(
            "User interaction",
            user_id=user_id,
            command=command,
            response_time_ms=response_time * 1000
        )
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """Log system-level events"""
        self.logger.info(
            "System event",
            event_type=event_type,
            details=details
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with context"""
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {},
            exc_info=True
        )


def get_logger(name: str) -> ARTACLogger:
    """Get a ARTAC logger instance"""
    return ARTACLogger(name)