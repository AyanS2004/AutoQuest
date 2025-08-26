"""
Core domain models for AutoQuest
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    XLSX = "xlsx"
    CSV = "csv"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueryType(str, Enum):
    """Query types"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    SUMMARIZATION = "summarization"


class BaseModel(BaseModel):
    """Base model with common functionality"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True
        arbitrary_types_allowed = True


class Document(BaseModel):
    """Document model"""
    id: str = Field(..., description="Unique document identifier")
    file_name: str = Field(..., description="Original file name")
    file_type: DocumentType = Field(..., description="Document type")
    file_size: int = Field(ge=1, description="File size in bytes")
    upload_date: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    chunk_count: int = Field(default=0, ge=0, description="Number of chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")
    
    @validator('file_name')
    def validate_file_name(cls, v):
        if not v.strip():
            raise ValueError('File name cannot be empty')
        return v.strip()
    
    @property
    def is_processed(self) -> bool:
        """Check if document is fully processed"""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if document processing failed"""
        return self.processing_status == ProcessingStatus.FAILED


class DocumentChunk(BaseModel):
    """Document chunk model"""
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., ge=0, description="Chunk index in document")
    start_char: int = Field(..., ge=0, description="Start character position")
    end_char: int = Field(..., ge=0, description="End character position")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    
    @validator('end_char')
    def validate_end_char(cls, v, values):
        if 'start_char' in values and v <= values['start_char']:
            raise ValueError('end_char must be greater than start_char')
        return v
    
    @property
    def length(self) -> int:
        """Get chunk length"""
        return len(self.content)


class Query(BaseModel):
    """Query model"""
    id: str = Field(..., description="Unique query identifier")
    text: str = Field(..., min_length=1, max_length=1000, description="Query text")
    query_type: QueryType = Field(default=QueryType.FACTUAL, description="Query type")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Query creation timestamp")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Query text cannot be empty')
        return v.strip()


class Source(BaseModel):
    """Source model for answers"""
    document_id: str = Field(..., description="Source document ID")
    chunk_id: str = Field(..., description="Source chunk ID")
    file_name: str = Field(..., description="Source file name")
    content: str = Field(..., description="Source content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    page_number: Optional[int] = Field(None, ge=1, description="Page number (if applicable)")
    chunk_index: int = Field(..., ge=0, description="Chunk index")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")


class Response(BaseModel):
    """Response model"""
    id: str = Field(..., description="Unique response identifier")
    query_id: str = Field(..., description="Associated query ID")
    answer: str = Field(..., description="Generated answer")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[Source] = Field(default_factory=list, description="Source documents")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens used")
    model_used: str = Field(..., description="Model used for generation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response creation timestamp")
    
    @property
    def source_count(self) -> int:
        """Get number of sources"""
        return len(self.sources)
    
    @property
    def has_sources(self) -> bool:
        """Check if response has sources"""
        return len(self.sources) > 0


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str = Field(..., description="Unique message identifier")
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")


class ChatSession(BaseModel):
    """Chat session model"""
    id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Session messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Session last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    
    @property
    def message_count(self) -> int:
        """Get number of messages"""
        return len(self.messages)
    
    @property
    def is_empty(self) -> bool:
        """Check if session is empty"""
        return len(self.messages) == 0


class ProcessingJob(BaseModel):
    """Processing job model"""
    id: str = Field(..., description="Unique job identifier")
    document_id: str = Field(..., description="Document to process")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Job status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Processing progress")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    
    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]


class GCCSession(BaseModel):
    """GCC extraction session model"""
    id: str = Field(..., description="Unique session identifier")
    input_file: str = Field(..., description="Input Excel file path")
    output_file: str = Field(..., description="Output Excel file path")
    template_file: str = Field(..., description="Template Excel file path")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Session status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Processing progress")
    current_field: Optional[str] = Field(None, description="Currently processing field")
    processed_companies: int = Field(default=0, ge=0, description="Number of processed companies")
    total_companies: int = Field(default=0, ge=0, description="Total number of companies")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    debug_port: int = Field(default=9222, description="Chrome debug port")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Session start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Session completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    
    @property
    def duration(self) -> Optional[float]:
        """Get session duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage"""
        if self.total_companies == 0:
            return 0.0
        return (self.processed_companies / self.total_companies) * 100.0
