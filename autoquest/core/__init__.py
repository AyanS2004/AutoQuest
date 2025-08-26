"""
Core domain logic for AutoQuest
Contains shared utilities, configuration, and base classes
"""

from .config import Settings, get_settings
from .logging import setup_logging, get_logger
from .exceptions import AutoQuestException, ValidationError, ProcessingError
from .models import BaseModel, Document, Query, Response
from .utils import (
    validate_file_type,
    sanitize_filename,
    generate_id,
    format_timestamp,
    calculate_similarity
)

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    
    # Logging
    "setup_logging", 
    "get_logger",
    
    # Exceptions
    "AutoQuestException",
    "ValidationError", 
    "ProcessingError",
    
    # Models
    "BaseModel",
    "Document",
    "Query", 
    "Response",
    
    # Utilities
    "validate_file_type",
    "sanitize_filename",
    "generate_id",
    "format_timestamp",
    "calculate_similarity"
]







