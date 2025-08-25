import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from models import QuestionRequest, QuestionType, DocumentType, ChatRequest, ChatMessage
from advanced_rag import AdvancedRAG
from ai_engine import AIEngine
from document_processor import DocumentProcessor


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_token():
    """Mock authentication token"""
    return "test-token-123"


@pytest.fixture
def sample_question_request():
    """Sample question request"""
    return QuestionRequest(
        question="What is artificial intelligence?",
        question_type=QuestionType.FACTUAL,
        top_k=3,
        similarity_threshold=0.7,
        include_sources=True,
        max_answer_length=200,
        temperature=0.7
    )


@pytest.fixture
def sample_chat_request():
    """Sample chat request"""
    return ChatRequest(
        messages=[
            ChatMessage(role="user", content="Hello, how can you help me?")
        ],
        conversation_id="test-conv-123",
        top_k=3,
        include_context=True
    )


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime" in data
        assert "model_status" in data


class TestAuthentication:
    """Test authentication middleware"""
    
    def test_ask_without_token(self, client):
        """Test asking question without authentication"""
        response = client.post("/ask", json={"question": "test"})
        assert response.status_code == 403
    
    def test_ask_with_invalid_token(self, client):
        """Test asking question with invalid token"""
        response = client.post(
            "/ask", 
            json={"question": "test"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


class TestQuestionEndpoint:
    """Test question answering endpoint"""
    
    @patch('main.rag_system')
    @patch('main.ai_engine')
    def test_ask_question_success(self, mock_ai_engine, mock_rag_system, client, mock_token, sample_question_request):
        """Test successful question answering"""
        # Mock RAG system
        mock_rag_system.retrieve = AsyncMock(return_value=[
            Mock(
                document_id="doc1",
                file_name="test.pdf",
                chunk_text="AI is a branch of computer science.",
                similarity_score=0.9,
                chunk_index=0
            )
        ])
        
        # Mock AI engine
        mock_ai_engine.generate_answer = AsyncMock(return_value=Mock(
            answer="Artificial intelligence is a branch of computer science.",
            confidence_score=0.85,
            sources=[],
            processing_time=0.5,
            model_used="qa_model",
            question_type=QuestionType.FACTUAL,
            metadata={}
        ))
        
        response = client.post(
            "/ask",
            json=sample_question_request.dict(),
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "confidence_score" in data
        assert "processing_time" in data
    
    @patch('main.rag_system')
    def test_ask_question_no_sources(self, mock_rag_system, client, mock_token, sample_question_request):
        """Test question answering when no sources are found"""
        mock_rag_system.retrieve = AsyncMock(return_value=[])
        
        response = client.post(
            "/ask",
            json=sample_question_request.dict(),
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "I couldn't find any relevant information" in data["answer"]
        assert data["confidence_score"] == 0.0


class TestChatEndpoint:
    """Test chat endpoint"""
    
    @patch('main.rag_system')
    @patch('main.ai_engine')
    def test_chat_success(self, mock_ai_engine, mock_rag_system, client, mock_token, sample_chat_request):
        """Test successful chat interaction"""
        # Mock RAG system
        mock_rag_system.retrieve = AsyncMock(return_value=[])
        
        # Mock AI engine
        mock_ai_engine.generate_chat_response = AsyncMock(return_value=Mock(
            message=Mock(role="assistant", content="Hello! I can help you with questions."),
            conversation_id="test-conv-123",
            sources=[],
            processing_time=0.3
        ))
        
        response = client.post(
            "/chat",
            json=sample_chat_request.dict(),
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"]["role"] == "assistant"


class TestDocumentUpload:
    """Test document upload endpoint"""
    
    def test_upload_unsupported_file_type(self, client, mock_token):
        """Test uploading unsupported file type"""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            with open(f.name, "rb") as file:
                response = client.post(
                    "/upload",
                    files={"file": ("test.xyz", file, "application/octet-stream")},
                    headers={"Authorization": f"Bearer {mock_token}"}
                )
        
        os.unlink(f.name)
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @patch('main.rag_system')
    def test_upload_success(self, mock_rag_system, client, mock_token):
        """Test successful document upload"""
        mock_rag_system.add_document = AsyncMock(return_value="doc-123")
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            with open(f.name, "rb") as file:
                response = client.post(
                    "/upload",
                    files={"file": ("test.txt", file, "text/plain")},
                    data={"metadata": '{"category": "test"}'},
                    headers={"Authorization": f"Bearer {mock_token}"}
                )
        
        os.unlink(f.name)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-123"
        assert data["file_name"] == "test.txt"


class TestDocumentManagement:
    """Test document management endpoints"""
    
    @patch('main.rag_system')
    def test_list_documents(self, mock_rag_system, client, mock_token):
        """Test listing documents"""
        mock_rag_system.list_documents.return_value = [
            Mock(
                id="doc1",
                file_name="test.pdf",
                file_type=DocumentType.PDF,
                upload_date=datetime.utcnow(),
                chunk_count=10,
                metadata={}
            )
        ]
        
        response = client.get(
            "/documents",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "doc1"
    
    @patch('main.rag_system')
    def test_delete_document(self, mock_rag_system, client, mock_token):
        """Test deleting document"""
        mock_rag_system.delete_document = AsyncMock(return_value=True)
        
        response = client.delete(
            "/documents/doc-123",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"


class TestSearchEndpoint:
    """Test search endpoint"""
    
    @patch('main.rag_system')
    def test_search_documents(self, mock_rag_system, client, mock_token):
        """Test searching documents"""
        mock_rag_system.retrieve = AsyncMock(return_value=[
            Mock(
                document_id="doc1",
                file_name="test.pdf",
                chunk_text="search result",
                similarity_score=0.8,
                chunk_index=0
            )
        ])
        
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "top_k": 5,
                "filters": {"category": "test"}
            },
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_found" in data
        assert "processing_time" in data


class TestBatchProcessing:
    """Test batch processing endpoint"""
    
    @patch('main.rag_system')
    @patch('main.ai_engine')
    def test_batch_questions(self, mock_ai_engine, mock_rag_system, client, mock_token):
        """Test batch question processing"""
        # Mock RAG system
        mock_rag_system.retrieve = AsyncMock(return_value=[
            Mock(
                document_id="doc1",
                file_name="test.pdf",
                chunk_text="test content",
                similarity_score=0.8,
                chunk_index=0
            )
        ])
        
        # Mock AI engine
        mock_ai_engine.generate_answer = AsyncMock(return_value=Mock(
            answer="Test answer",
            confidence_score=0.8,
            sources=[],
            processing_time=0.5,
            model_used="qa_model",
            question_type=QuestionType.FACTUAL,
            metadata={}
        ))
        
        response = client.post(
            "/batch",
            json={
                "questions": [
                    {"question": "What is AI?", "question_type": "factual"},
                    {"question": "What is ML?", "question_type": "factual"}
                ],
                "batch_id": "batch-123"
            },
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "answers" in data
        assert "total_processing_time" in data
        assert data["success_count"] == 2


class TestSystemManagement:
    """Test system management endpoints"""
    
    @patch('main.rag_system')
    @patch('main.ai_engine')
    def test_get_stats(self, mock_ai_engine, mock_rag_system, client, mock_token):
        """Test getting system statistics"""
        mock_rag_system.get_stats.return_value = {
            "total_documents": 10,
            "total_chunks": 100,
            "vector_db_type": "chroma"
        }
        
        mock_ai_engine.get_cache_stats.return_value = {
            "cache_size": 50,
            "cache_enabled": True
        }
        
        mock_ai_engine.get_model_status.return_value = {
            "qa": "loaded",
            "text_generation": "loaded"
        }
        
        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "rag_system" in data
        assert "cache" in data
        assert "models" in data
    
    @patch('main.ai_engine')
    def test_clear_cache(self, mock_ai_engine, client, mock_token):
        """Test clearing cache"""
        mock_ai_engine.clear_cache = Mock()
        
        response = client.post(
            "/cache/clear",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cache_cleared"
        mock_ai_engine.clear_cache.assert_called_once()


class TestAdvancedRAG:
    """Test AdvancedRAG class"""
    
    @pytest.fixture
    def rag_system(self):
        """Create AdvancedRAG instance for testing"""
        return AdvancedRAG()
    
    @pytest.mark.asyncio
    async def test_add_document(self, rag_system):
        """Test adding document to RAG system"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test document content")
            f.flush()
            
            doc_id = await rag_system.add_document(f.name, DocumentType.TXT)
            os.unlink(f.name)
            
            assert doc_id is not None
            assert isinstance(doc_id, str)
    
    @pytest.mark.asyncio
    async def test_retrieve_documents(self, rag_system):
        """Test document retrieval"""
        # First add a document
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"artificial intelligence machine learning")
            f.flush()
            
            await rag_system.add_document(f.name, DocumentType.TXT)
            os.unlink(f.name)
        
        # Then retrieve
        sources = await rag_system.retrieve("What is AI?", top_k=3)
        assert isinstance(sources, list)


class TestAIEngine:
    """Test AIEngine class"""
    
    @pytest.fixture
    def ai_engine(self):
        """Create AIEngine instance for testing"""
        return AIEngine()
    
    @pytest.mark.asyncio
    async def test_generate_answer(self, ai_engine, sample_question_request):
        """Test answer generation"""
        sources = [
            Mock(
                document_id="doc1",
                file_name="test.pdf",
                chunk_text="AI is artificial intelligence.",
                similarity_score=0.9,
                chunk_index=0
            )
        ]
        
        response = await ai_engine.generate_answer(sample_question_request, sources)
        assert response is not None
        assert hasattr(response, 'answer')
        assert hasattr(response, 'confidence_score')
    
    def test_get_model_status(self, ai_engine):
        """Test getting model status"""
        status = ai_engine.get_model_status()
        assert isinstance(status, dict)
        assert "qa" in status
        assert "text_generation" in status


class TestDocumentProcessor:
    """Test DocumentProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance for testing"""
        return DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_process_text_document(self, processor):
        """Test processing text document"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"This is a test document with some content.")
            f.flush()
            
            chunks = await processor.process_document(f.name, DocumentType.TXT)
            os.unlink(f.name)
            
            assert isinstance(chunks, list)
            assert len(chunks) > 0
    
    def test_clean_text(self, processor):
        """Test text cleaning"""
        dirty_text = "  This   has   extra   spaces  \n\nand\n\nline\nbreaks  "
        clean_text = processor._clean_text(dirty_text)
        assert "  " not in clean_text
        assert clean_text.strip() == clean_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 