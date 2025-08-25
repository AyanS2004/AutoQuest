import asyncio
import time
import logging
import structlog
from datetime import datetime
from typing import List, Optional, Dict
import psutil
import os
import json

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from pathlib import Path
import uuid
import shutil
import time

from config import settings
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from jose import jwt, JWTError
import secrets
from autoquest.api.schemas.core import (
    QuestionRequest, AnswerResponse, ChatRequest, ChatResponse,
    HealthResponse, ErrorResponse, BatchQuestionRequest, BatchAnswerResponse,
    SearchRequest, SearchResponse, DocumentInfo
)
from advanced_rag import AdvancedRAG
from ai_engine import AIEngine
from document_processor import DocumentProcessor
from autoquest.api.schemas.core import DocumentType
from pydantic import BaseModel
from gcc_copilot import FinalPerfectGCCExtractor

# Configure structured logging
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize components
rag_system = AdvancedRAG()
ai_engine = AIEngine()
document_processor = DocumentProcessor()

# GCC extractor session registry (in-memory)
GCC_SESSIONS: Dict[str, Dict] = {}


class GCCStartRequest(BaseModel):
    input_file: Optional[str] = "solutions.xlsx"
    output_file: Optional[str] = "solutions.xlsx"
    template_file: Optional[str] = "template.xlsx"
    debug_port: Optional[int] = 9222


class GCCStartResponse(BaseModel):
    session_id: str
    status: str
    input_file: str
    output_file: str
    template_file: str


def _run_gcc_extractor(session_id: str):
    session = GCC_SESSIONS.get(session_id)
    if not session:
        return
    try:
        session["status"] = "running"
        session["updated_at"] = time.time()

        extractor = FinalPerfectGCCExtractor(
            input_file=session["input_file"],
            output_file=session["output_file"],
            template_file=session["template_file"],
        )
        extractor.debug_port = session.get("debug_port", 9222)
        session["extractor"] = extractor
        session["log_file"] = str(Path("storage") / "logs" / extractor.log_file)
        session["db_file"] = extractor.db_file

        success = extractor.run_final_perfect_gcc_extraction()
        session["status"] = "completed" if success else "failed"
        session["updated_at"] = time.time()
    except Exception as e:
        session["status"] = "failed"
        session["error"] = str(e)
        session["updated_at"] = time.time()


@app.post("/gcc/start", response_model=GCCStartResponse)
async def start_gcc_extraction(
    request: GCCStartRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Start the GCC extractor in the background.

    Ensure Chrome is running with remote debugging: --remote-debugging-port=9222
    """
    try:
        # Ensure input/template files exist or bootstrap from template
        input_path = Path(request.input_file)
        template_path = Path(request.template_file)

        if not input_path.exists():
            if template_path.exists():
                shutil.copy2(template_path, input_path)
            else:
                raise HTTPException(status_code=400, detail="Neither input_file nor template_file exists")

        session_id = f"gcc_{uuid.uuid4().hex[:12]}"
        GCC_SESSIONS[session_id] = {
            "status": "starting",
            "created_at": time.time(),
            "updated_at": time.time(),
            "input_file": str(input_path),
            "output_file": str(request.output_file or request.input_file),
            "template_file": str(template_path),
            "debug_port": request.debug_port or 9222,
        }

        background_tasks.add_task(_run_gcc_extractor, session_id)

        return GCCStartResponse(
            session_id=session_id,
            status="starting",
            input_file=str(input_path),
            output_file=str(request.output_file or request.input_file),
            template_file=str(template_path),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start GCC extractor", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start GCC extraction")


@app.get("/gcc/status/{session_id}")
async def gcc_status(session_id: str, token: str = Depends(verify_token)):
    session = GCC_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Do not expose extractor object
    return {k: v for k, v in session.items() if k != "extractor"}


@app.post("/gcc/stop/{session_id}")
async def gcc_stop(session_id: str, token: str = Depends(verify_token)):
    session = GCC_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    extractor = session.get("extractor")
    if extractor and hasattr(extractor, "shutdown_event"):
        extractor.shutdown_event.set()
        session["status"] = "stopping"
        session["updated_at"] = time.time()
        return {"status": "stopping"}
    return {"status": session.get("status", "unknown")}


@app.get("/gcc/download/{filename}")
async def gcc_download(filename: str, token: str = Depends(verify_token)):
    # Whitelist only .xlsx and .db and .log under project root
    allowed_suffixes = {".xlsx", ".db", ".log"}
    file_path = Path(filename)
    if not file_path.suffix.lower() in allowed_suffixes:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if not file_path.exists():
        # Also check under storage/logs/
        alt = Path("storage") / "logs" / filename
        if alt.exists():
            file_path = alt
        else:
            raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=file_path.name)

# Prometheus metrics
REQUEST_COUNT = Counter('ragbot_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('ragbot_request_duration_seconds', 'Request latency', ['method', 'endpoint'])
ERROR_COUNT = Counter('ragbot_errors_total', 'Total errors', ['method', 'endpoint', 'error_type'])

# Security
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "A Retrieval-Augmented Generation (RAG) system built with modern architecture, "
        "advanced AI models, and enterprise-grade engineering. Designed for high-performance "
        "data ingestion, intelligent automation, and resilient operations."
    ),
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Record request
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            ERROR_COUNT.labels(
                method=request.method, 
                endpoint=request.url.path, 
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)


app.add_middleware(MetricsMiddleware)
# Simple in-memory rate limiter (per token, per minute)
RATE_LIMIT_BUCKETS: Dict[str, Dict[str, float]] = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/metrics") or request.url.path.startswith("/health"):
            return await call_next(request)
        try:
            auth = request.headers.get("Authorization", "")
            token = auth.split(" ")[-1] if auth else "anonymous"
            limit = settings.rate_limit_per_minute
            if limit <= 0:
                return await call_next(request)
            bucket = RATE_LIMIT_BUCKETS.get(token)
            now = time.time()
            window = int(now // 60)
            if not bucket or bucket.get("window") != window:
                RATE_LIMIT_BUCKETS[token] = {"window": window, "count": 1}
            else:
                RATE_LIMIT_BUCKETS[token]["count"] += 1
            if RATE_LIMIT_BUCKETS[token]["count"] > limit:
                return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
        except Exception:
            pass
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

# Optional Sentry
if settings.enable_sentry and settings.sentry_dsn:
    try:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.2)
        app.add_middleware(SentryAsgiMiddleware)
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning("Failed to initialize Sentry", error=str(e))


# Dependency for authentication (optional JWT implementation)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    token = credentials.credentials
    # If SECRET_KEY is set and token seems like JWT, validate; else accept token as opaque string
    try:
        if token.count('.') == 2 and settings.secret_key:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            # Optional role enforcement
            if request is not None:
                request.state.user_role = payload.get("role")
            if settings.enforce_roles:
                path = request.url.path if request is not None else ""
                required_role = "admin" if path.startswith("/gcc") else "user"
                user_role = (payload.get("role") or "user").lower()
                if required_role == "admin" and user_role != "admin":
                    raise HTTPException(status_code=403, detail="Insufficient role")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


# Token issuance (demo only; not a full user system)
class TokenRequest(BaseModel):
    role: Optional[str] = "user"
    ttl_minutes: Optional[int] = 30


@app.post("/auth/token")
async def issue_token(req: TokenRequest):
    """Issue a signed JWT for testing. In production, back with real users and secrets."""
    payload = {
        "role": (req.role or "user").lower(),
        "exp": int(time.time()) + (req.ttl_minutes or settings.access_token_expire_minutes) * 60,
        "jti": secrets.token_hex(8),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return {"access_token": token, "token_type": "bearer"}


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health status"""
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        
        # Get model status
        model_status = ai_engine.get_model_status()
        
        # Get RAG system stats
        rag_stats = rag_system.get_stats()
        
        # Get cache stats
        cache_stats = ai_engine.get_cache_stats()
        
        return HealthResponse(
            status="healthy",
            version=settings.version,
            uptime=time.time() - app.start_time if hasattr(app, 'start_time') else 0,
            model_status=model_status,
            vector_db_status=rag_stats.get("vector_db_type", "unknown"),
            cache_status="enabled" if cache_stats["cache_enabled"] else "disabled",
            memory_usage={
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent_used": memory.percent
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Get Prometheus metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Question answering endpoint
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Ask a question and get an answer based on the knowledge base"""
    try:
        start_time = time.time()
        
        # Retrieve relevant documents
        sources = await rag_system.retrieve(
            query=request.question,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        if not sources:
            return AnswerResponse(
                answer="I couldn't find any relevant information to answer your question.",
                confidence_score=0.0,
                sources=[],
                processing_time=time.time() - start_time,
                model_used="no_sources",
                question_type=request.question_type
            )
        
        # Generate answer
        response = await ai_engine.generate_answer(request, sources)
        
        # Add background task for logging
        background_tasks.add_task(log_interaction, request, response, token)
        
        return response
        
    except Exception as e:
        logger.error("Error processing question", error=str(e), question=request.question)
        ERROR_COUNT.labels(method="POST", endpoint="/ask", error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail="Failed to process question")


# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """Chat with the AI system"""
    try:
        # Retrieve relevant documents if context is requested
        sources = []
        if request.include_context and request.messages:
            last_message = request.messages[-1].content
            sources = await rag_system.retrieve(
                query=last_message,
                top_k=request.top_k
            )
        
        # Generate chat response
        response = await ai_engine.generate_chat_response(request, sources)
        
        return response
        
    except Exception as e:
        logger.error("Error in chat", error=str(e))
        ERROR_COUNT.labels(method="POST", endpoint="/chat", error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail="Failed to generate chat response")


# Batch processing endpoint
@app.post("/batch", response_model=BatchAnswerResponse)
async def batch_questions(
    request: BatchQuestionRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Process multiple questions in batch"""
    try:
        start_time = time.time()
        batch_id = request.batch_id or f"batch_{int(time.time())}"
        
        answers = []
        errors = []
        
        # Process questions concurrently
        tasks = []
        for question_request in request.questions:
            task = asyncio.create_task(process_single_question(question_request))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(ErrorResponse(
                    error=str(result),
                    error_code=type(result).__name__,
                    details=f"Failed to process question {i+1}"
                ))
            else:
                answers.append(result)
        
        # Add background task for logging
        background_tasks.add_task(log_batch_interaction, request, answers, errors, token)
        
        return BatchAnswerResponse(
            batch_id=batch_id,
            answers=answers,
            total_processing_time=time.time() - start_time,
            success_count=len(answers),
            error_count=len(errors),
            errors=errors
        )
        
    except Exception as e:
        logger.error("Error in batch processing", error=str(e))
        ERROR_COUNT.labels(method="POST", endpoint="/batch", error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail="Failed to process batch questions")


async def process_single_question(question_request: QuestionRequest) -> AnswerResponse:
    """Process a single question (for batch processing)"""
    sources = await rag_system.retrieve(
        query=question_request.question,
        top_k=question_request.top_k,
        similarity_threshold=question_request.similarity_threshold
    )
    
    if not sources:
        return AnswerResponse(
            answer="I couldn't find any relevant information to answer your question.",
            confidence_score=0.0,
            sources=[],
            processing_time=0.0,
            model_used="no_sources",
            question_type=question_request.question_type
        )
    
    return await ai_engine.generate_answer(question_request, sources)


# Document upload endpoint
@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    token: str = Depends(verify_token)
):
    """Upload a document to the knowledge base"""
    try:
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: {settings.supported_formats}"
            )
        
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size / (1024*1024)}MB"
            )
        
        # Determine document type
        doc_type_map = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.txt': DocumentType.TXT,
            '.md': DocumentType.MD,
            '.xlsx': DocumentType.XLSX,
            '.csv': DocumentType.CSV
        }
        doc_type = doc_type_map.get(file_extension)
        
        # Save file temporarily
        temp_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse metadata
        doc_metadata = {}
        if metadata:
            try:
                doc_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning("Invalid metadata JSON", metadata=metadata)
        
        # Add document to RAG system
        document_id = await rag_system.add_document(temp_path, doc_type, doc_metadata)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "document_id": document_id,
            "file_name": file.filename,
            "file_type": doc_type.value,
            "status": "uploaded"
        }
        
    except Exception as e:
        logger.error("Error uploading document", error=str(e), filename=file.filename)
        ERROR_COUNT.labels(method="POST", endpoint="/upload", error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail="Failed to upload document")


# Document management endpoints
@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents(token: str = Depends(verify_token)):
    """List all documents in the knowledge base"""
    try:
        return rag_system.list_documents()
    except Exception as e:
        logger.error("Error listing documents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list documents")


@app.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str, token: str = Depends(verify_token)):
    """Get information about a specific document"""
    try:
        doc_info = rag_system.get_document_info(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting document", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail="Failed to get document")


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, token: str = Depends(verify_token)):
    """Delete a document from the knowledge base"""
    try:
        success = await rag_system.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "deleted", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document", error=str(e), document_id=document_id)
        raise HTTPException(status_code=500, detail="Failed to delete document")


# Search endpoint
@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    """Search documents in the knowledge base"""
    try:
        start_time = time.time()
        
        sources = await rag_system.retrieve(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        
        return SearchResponse(
            results=sources,
            total_found=len(sources),
            processing_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error("Error searching documents", error=str(e))
        ERROR_COUNT.labels(method="POST", endpoint="/search", error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail="Failed to search documents")


# System management endpoints
@app.get("/stats")
async def get_system_stats(token: str = Depends(verify_token)):
    """Get system statistics"""
    try:
        rag_stats = rag_system.get_stats()
        cache_stats = ai_engine.get_cache_stats()
        model_status = ai_engine.get_model_status()
        
        return {
            "rag_system": rag_stats,
            "cache": cache_stats,
            "models": model_status,
            "settings": {
                "embedding_model": settings.embedding_model.value,
                "vector_db_type": settings.vector_db_type.value,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap
            }
        }
    except Exception as e:
        logger.error("Error getting system stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system stats")


@app.post("/cache/clear")
async def clear_cache(token: str = Depends(verify_token)):
    """Clear the response cache"""
    try:
        ai_engine.clear_cache()
        return {"status": "cache_cleared"}
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# Background tasks
async def log_interaction(request: QuestionRequest, response: AnswerResponse, token: str):
    """Log interaction for analytics"""
    logger.info(
        "Question answered",
        question=request.question,
        answer_length=len(response.answer),
        confidence=response.confidence_score,
        processing_time=response.processing_time,
        model_used=response.model_used,
        sources_count=len(response.sources)
    )


async def log_batch_interaction(
    request: BatchQuestionRequest, 
    answers: List[AnswerResponse], 
    errors: List[ErrorResponse], 
    token: str
):
    """Log batch interaction for analytics"""
    logger.info(
        "Batch questions processed",
        batch_id=request.batch_id,
        total_questions=len(request.questions),
        successful_answers=len(answers),
        errors=len(errors)
    )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )
    
    ERROR_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        error_type=type(exc).__name__
    ).inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    app.start_time = time.time()
    logger.info("RAGbot Pro starting up", version=settings.version)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("RAGbot Pro shutting down")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 