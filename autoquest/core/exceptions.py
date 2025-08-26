"""
Custom exceptions for AutoQuest
"""

from typing import Optional, Dict, Any


class AutoQuestException(Exception):
    """Base exception for AutoQuest application"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(AutoQuestException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(message, "VALIDATION_ERROR", details)


class ProcessingError(AutoQuestException):
    """Raised when document processing fails"""
    
    def __init__(self, message: str, document_id: Optional[str] = None, step: Optional[str] = None):
        details = {}
        if document_id:
            details["document_id"] = document_id
        if step:
            details["step"] = step
        
        super().__init__(message, "PROCESSING_ERROR", details)


class ModelError(AutoQuestException):
    """Raised when AI model operations fail"""
    
    def __init__(self, message: str, model: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if model:
            details["model"] = model
        if operation:
            details["operation"] = operation
        
        super().__init__(message, "MODEL_ERROR", details)


class DatabaseError(AutoQuestException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(message, "DATABASE_ERROR", details)


class AuthenticationError(AutoQuestException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", token_type: Optional[str] = None):
        details = {}
        if token_type:
            details["token_type"] = token_type
        
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(AutoQuestException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions", required_role: Optional[str] = None):
        details = {}
        if required_role:
            details["required_role"] = required_role
        
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class RateLimitError(AutoQuestException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", limit: Optional[int] = None, window: Optional[str] = None):
        details = {}
        if limit:
            details["limit"] = limit
        if window:
            details["window"] = window
        
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class FileError(AutoQuestException):
    """Raised when file operations fail"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        
        super().__init__(message, "FILE_ERROR", details)


class ConfigurationError(AutoQuestException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, setting: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if setting:
            details["setting"] = setting
        if value is not None:
            details["value"] = value
        
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ExternalServiceError(AutoQuestException):
    """Raised when external service calls fail"""
    
    def __init__(self, message: str, service: Optional[str] = None, status_code: Optional[int] = None):
        details = {}
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class CacheError(AutoQuestException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None, key: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key
        
        super().__init__(message, "CACHE_ERROR", details)


class GCCError(AutoQuestException):
    """Raised when GCC extraction operations fail"""
    
    def __init__(self, message: str, session_id: Optional[str] = None, step: Optional[str] = None):
        details = {}
        if session_id:
            details["session_id"] = session_id
        if step:
            details["step"] = step
        
        super().__init__(message, "GCC_ERROR", details)


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """Convert any exception to a standardized error response"""
    if isinstance(exc, AutoQuestException):
        return exc.to_dict()
    else:
        return {
            "error": str(exc),
            "error_code": "UNKNOWN_ERROR",
            "details": {
                "exception_type": type(exc).__name__,
                "exception_module": type(exc).__module__
            }
        }


def is_retryable_error(exc: Exception) -> bool:
    """Check if an exception is retryable"""
    if isinstance(exc, (ValidationError, AuthenticationError, AuthorizationError, ConfigurationError)):
        return False
    
    if isinstance(exc, (ProcessingError, ModelError, DatabaseError, FileError, ExternalServiceError, CacheError, GCCError)):
        return True
    
    # Default to retryable for unknown exceptions
    return True
