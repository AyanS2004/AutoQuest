from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    SUMMARIZATION = "summarization"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    XLSX = "xlsx"
    CSV = "csv"


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    question_type: Optional[QuestionType] = QuestionType.FACTUAL
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata: Optional[bool] = True
    include_sources: Optional[bool] = True
    max_answer_length: Optional[int] = Field(default=500, ge=50, le=2000)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()


class DocumentUpload(BaseModel):
    file_name: str = Field(..., description="Name of the uploaded file")
    file_type: 'DocumentType'
    file_size: int = Field(..., ge=1, le=50 * 1024 * 1024)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentInfo(BaseModel):
    id: str
    file_name: str
    file_type: 'DocumentType'
    upload_date: datetime
    chunk_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Source(BaseModel):
    document_id: str
    file_name: str
    chunk_text: str
    similarity_score: float
    page_number: Optional[int] = None
    chunk_index: int


class AnswerResponse(BaseModel):
    answer: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    sources: List['Source'] = Field(default_factory=list)
    processing_time: float
    tokens_used: Optional[int] = None
    model_used: str
    question_type: 'QuestionType'
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    messages: List['ChatMessage'] = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    include_context: Optional[bool] = True


class ChatResponse(BaseModel):
    message: 'ChatMessage'
    conversation_id: str
    sources: List['Source'] = Field(default_factory=list)
    processing_time: float
    tokens_used: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    model_status: Dict[str, str]
    vector_db_status: str
    cache_status: str
    memory_usage: Dict[str, float]


class ErrorResponse(BaseModel):
    error: str
    error_code: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchQuestionRequest(BaseModel):
    questions: List['QuestionRequest'] = Field(..., min_length=1, max_length=100)
    batch_id: Optional[str] = None


class BatchAnswerResponse(BaseModel):
    batch_id: str
    answers: List['AnswerResponse']
    total_processing_time: float
    success_count: int
    error_count: int
    errors: List['ErrorResponse'] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=10, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: List['Source']
    total_found: int
    processing_time: float


# Resolve forward refs
DocumentUpload.update_forward_refs()
DocumentInfo.update_forward_refs()
AnswerResponse.update_forward_refs()
ChatRequest.update_forward_refs()
ChatResponse.update_forward_refs()
BatchQuestionRequest.update_forward_refs()
BatchAnswerResponse.update_forward_refs()
SearchResponse.update_forward_refs()







