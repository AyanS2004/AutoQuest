"""
Logging configuration for AutoQuest
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Setup structured logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format (json, text)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create handlers
    handlers = []
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        handlers=handlers,
        force=True
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str = "autoquest") -> structlog.BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")


def log_function_call(func):
    """Decorator to log function calls with parameters and timing"""
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        
        # Log function call
        logger.info(
            "Function called",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            start_time = datetime.utcnow()
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            
            # Log successful completion
            logger.info(
                "Function completed",
                function=func.__name__,
                duration_ms=(end_time - start_time).total_seconds() * 1000
            )
            
            return result
            
        except Exception as e:
            # Log error
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    return wrapper


def log_async_function_call(func):
    """Decorator to log async function calls with parameters and timing"""
    async def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        
        # Log function call
        logger.info(
            "Async function called",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            start_time = datetime.utcnow()
            result = await func(*args, **kwargs)
            end_time = datetime.utcnow()
            
            # Log successful completion
            logger.info(
                "Async function completed",
                function=func.__name__,
                duration_ms=(end_time - start_time).total_seconds() * 1000
            )
            
            return result
            
        except Exception as e:
            # Log error
            logger.error(
                "Async function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    return wrapper


class PerformanceLogger:
    """Context manager for logging performance metrics"""
    
    def __init__(self, operation: str, logger: Optional[structlog.BoundLogger] = None):
        self.operation = operation
        self.logger = logger or get_logger("performance")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info("Operation started", operation=self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration_ms = (end_time - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(
                "Operation completed",
                operation=self.operation,
                duration_ms=duration_ms
            )
        else:
            self.logger.error(
                "Operation failed",
                operation=self.operation,
                duration_ms=duration_ms,
                error=str(exc_val),
                error_type=exc_type.__name__
            )


def log_request(request_data: Dict[str, Any], logger: Optional[structlog.BoundLogger] = None):
    """Log incoming request data"""
    logger = logger or get_logger("requests")
    logger.info("Request received", **request_data)


def log_response(response_data: Dict[str, Any], logger: Optional[structlog.BoundLogger] = None):
    """Log outgoing response data"""
    logger = logger or get_logger("requests")
    logger.info("Response sent", **response_data)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, logger: Optional[structlog.BoundLogger] = None):
    """Log error with context"""
    logger = logger or get_logger("errors")
    
    error_data = {
        "error": str(error),
        "error_type": type(error).__name__,
        "error_module": type(error).__module__
    }
    
    if context:
        error_data.update(context)
    
    logger.error("Error occurred", **error_data)
