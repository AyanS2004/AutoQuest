import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from transformers import pipeline, set_seed
import re
import json
from datetime import datetime
import uuid

from config import settings, VectorDBType
from autoquest.api.schemas.core import DocumentType, Source, DocumentInfo
from document_processor import DocumentProcessor
from pathlib import Path

logger = logging.getLogger(__name__)

class AdvancedRAG:
    """Enhanced RAG system with multiple retrieval strategies and response generation models.

    Now includes a document registry and pluggable vector database backends (FAISS, Chroma, Qdrant).
    """
    
    def __init__(self, 
                 embedding_model: str = settings.embedding_model.value,
                 chunk_size: int = settings.chunk_size,
                 chunk_overlap: int = settings.chunk_overlap):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Document registry
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []
        self.doc_index_to_id: Dict[int, str] = {}
        self.id_to_info: Dict[str, DocumentInfo] = {}
        
        # Initialize vector index
        self.index = None
        self.doc_embeddings = None
        self.vector_db_type = settings.vector_db_type
        self.vector_db_path = settings.vector_db_path
        self._backend_client = None  # for chroma/qdrant
        self._backend_collection = None
        self._init_backend()
        
        # Initialize response generation models
        self.qa_pipeline = None
        self.text_gen_pipeline = None
        self._initialize_models()
        
        # Processors
        self.processor = DocumentProcessor(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        
        set_seed(42)
    
    def _initialize_models(self):
        """Initialize different types of response generation models."""
        try:
            # Try to load QA model
            self.qa_pipeline = pipeline(
                "question-answering", 
                model="distilbert-base-cased-distilled-squad",
                device=-1  # Use CPU for now
            )
            logger.info("QA model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load QA model: {e}")
            self.qa_pipeline = None
        
        try:
            # Load text generation model as fallback
            self.text_gen_pipeline = pipeline(
                "text-generation",
                model="gpt2",
                device=-1
            )
            logger.info("Text generation model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load text generation model: {e}")
            self.text_gen_pipeline = None
    
    async def add_document(self, file_path: str, file_type: DocumentType, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a single file into the RAG system, process into chunks, and index."""
        metadata = metadata or {}
        chunks = await self.processor.process_document(file_path, file_type)
        if not chunks:
            raise ValueError("No content extracted from document")
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        # Register document info
        info = DocumentInfo(
            id=document_id,
            file_name=Path(file_path).name,
            file_type=file_type,
            upload_date=now,
            chunk_count=len(chunks),
            metadata=metadata
        )
        self.id_to_info[document_id] = info
        # Add chunks into in-memory registry (used by FAISS and for Source response)
        start_idx = len(self.documents)
        for chunk in chunks:
            self.documents.append(chunk["text"])
            self.metadata.append({"document_id": document_id, **chunk.get("metadata", {}), **metadata})
        # Map new indices to this doc_id
        for local_idx in range(start_idx, start_idx + len(chunks)):
            self.doc_index_to_id[local_idx] = document_id
        # Index
        self._build_index()
        logger.info(f"Added document {document_id} with {len(chunks)} chunks")
        return document_id
    
    def _build_index(self):
        """Build vector index depending on configured backend.
        For now, implement FAISS fully; placeholders for Chroma/Qdrant to be filled later.
        """
        if not self.documents:
            logger.warning("No documents to index")
            return
        # Create embeddings
        self.doc_embeddings = self.embedder.encode(
            self.documents,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        if self.vector_db_type == VectorDBType.FAISS:
            dimension = self.doc_embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.doc_embeddings)
            logger.info(f"Built FAISS index with {len(self.documents)} chunks")
        elif self.vector_db_type == VectorDBType.CHROMA:
            try:
                if self._backend_collection is None:
                    self._init_backend()
                # Clear and re-add
                self._backend_collection.delete(where={})
                ids = [f"chunk_{i}" for i in range(len(self.documents))]
                self._backend_collection.add(
                    ids=ids,
                    documents=self.documents,
                    embeddings=self.doc_embeddings.tolist(),
                    metadatas=self.metadata
                )
                self.index = None
                logger.info(f"Rebuilt Chroma collection with {len(ids)} chunks")
            except Exception as e:
                logger.error(f"Chroma indexing failed: {e}")
                # Fallback to FAISS
                self.vector_db_type = VectorDBType.FAISS
                self._build_index()
        elif self.vector_db_type == VectorDBType.QDRANT:
            try:
                dim = int(self.doc_embeddings.shape[1])
                self._ensure_qdrant_collection(dim)
                from qdrant_client.models import PointStruct
                points = []
                for i, vector in enumerate(self.doc_embeddings):
                    points.append(PointStruct(id=i, vector=vector.tolist(), payload=self.metadata[i]))
                self._backend_client.upsert(collection_name="documents", points=points)
                self.index = None
                logger.info(f"Rebuilt Qdrant collection with {len(points)} chunks")
            except Exception as e:
                logger.error(f"Qdrant indexing failed: {e}")
                # Fallback to FAISS
                self.vector_db_type = VectorDBType.FAISS
                self._build_index()
    
    async def retrieve(self, query: str, top_k: int = None, similarity_threshold: float = None, filters: Optional[Dict[str, Any]] = None) -> List[Source]:
        """Retrieve relevant chunks as Source models using hybrid (lexical + vector) if enabled.
        Supports simple metadata filters on in-memory metadata (document_id equality and file_type).
        """
        if not self.documents:
            return []
        top_k = top_k or settings.top_k
        similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.similarity_threshold
        # Lexical scoring (simple frequency overlap)
        def lexical_score(text: str, q: str) -> float:
            q_tokens = set(re.findall(r"\b\w+\b", q.lower()))
            t_tokens = set(re.findall(r"\b\w+\b", text.lower()))
            if not q_tokens or not t_tokens:
                return 0.0
            overlap = len(q_tokens.intersection(t_tokens))
            return overlap / max(1, len(q_tokens))

        # Filter indices by metadata
        candidate_indices = list(range(len(self.documents)))
        if filters:
            filtered = []
            for idx in candidate_indices:
                meta = self.metadata[idx] if idx < len(self.metadata) else {}
                ok = True
                if "document_id" in filters and meta.get("document_id") != filters["document_id"]:
                    ok = False
                if "file_type" in filters and meta.get("file_type") != filters["file_type"]:
                    ok = False
                if ok:
                    filtered.append(idx)
            candidate_indices = filtered
            if not candidate_indices:
                return []

        # Query embedding
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        sources: List[Source] = []
        if self.vector_db_type == VectorDBType.FAISS:
            if self.index is None:
                self._build_index()
            if self.index is None:
                return []
            # Vector search over candidate indices: emulate by searching all and post-filter
            distances, indices = self.index.search(query_embedding, min(len(self.documents), max(top_k * 5, 50)))
            ranked = []
            for distance, idx in zip(distances[0], indices[0]):
                if int(idx) not in candidate_indices:
                    continue
                vec_sim = float(1 / (1 + distance))
                lex_sim = lexical_score(self.documents[idx], query)
                if settings.enable_hybrid:
                    alpha = settings.hybrid_alpha
                    score = alpha * vec_sim + (1 - alpha) * lex_sim
                else:
                    score = vec_sim
                ranked.append((score, vec_sim, int(idx)))
            ranked.sort(key=lambda x: x[0], reverse=True)
            results = []
            for score, vec_sim, idx in ranked[:top_k]:
                if vec_sim < similarity_threshold and not settings.enable_hybrid:
                    continue
                meta = self.metadata[idx] if idx < len(self.metadata) else {}
                doc_id = meta.get("document_id", self.doc_index_to_id.get(int(idx), ""))
                file_name = meta.get("file_path", "")
                results.append(Source(
                    document_id=doc_id or str(idx),
                    file_name=Path(file_name).name if file_name else (self.id_to_info.get(doc_id).file_name if doc_id in self.id_to_info else "unknown"),
                    chunk_text=self.documents[idx],
                    similarity_score=float(score),
                    chunk_index=int(idx)
                ))
            return results
        elif self.vector_db_type == VectorDBType.CHROMA:
            try:
                if self._backend_collection is None:
                    self._init_backend()
                res = self._backend_collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=top_k
                )
                ids = res.get("ids", [[]])[0]
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                dists = res.get("distances", [[]])[0]
                for i, _ in enumerate(ids):
                    distance = float(dists[i]) if i < len(dists) else 0.0
                    similarity = float(1 / (1 + distance))
                    if similarity < similarity_threshold:
                        continue
                    meta = metas[i] if i < len(metas) else {}
                    doc_id = meta.get("document_id", "")
                    file_name = meta.get("file_path", "")
                    sources.append(Source(
                        document_id=doc_id or str(i),
                        file_name=Path(file_name).name if file_name else (self.id_to_info.get(doc_id).file_name if doc_id in self.id_to_info else "unknown"),
                        chunk_text=docs[i] if i < len(docs) else "",
                        similarity_score=similarity,
                        chunk_index=int(i)
                    ))
            except Exception as e:
                logger.error(f"Chroma query failed: {e}")
                # Fallback to FAISS search
                self.vector_db_type = VectorDBType.FAISS
                return await self.retrieve(query, top_k=top_k, similarity_threshold=similarity_threshold, filters=filters)
            return sources
        elif self.vector_db_type == VectorDBType.QDRANT:
            try:
                self._ensure_qdrant_collection(int(query_embedding.shape[1]))
                res = self._backend_client.search(
                    collection_name="documents",
                    query_vector=query_embedding[0].tolist(),
                    limit=top_k
                )
                for hit in res:
                    similarity = float(hit.score)
                    if similarity < similarity_threshold:
                        continue
                    meta = hit.payload or {}
                    idx = int(hit.id) if isinstance(hit.id, int) else 0
                    doc_id = meta.get("document_id", self.doc_index_to_id.get(idx, ""))
                    file_name = meta.get("file_path", "")
                    text = self.documents[idx] if idx < len(self.documents) else ""
                    sources.append(Source(
                        document_id=doc_id or str(idx),
                        file_name=Path(file_name).name if file_name else (self.id_to_info.get(doc_id).file_name if doc_id in self.id_to_info else "unknown"),
                        chunk_text=text,
                        similarity_score=similarity,
                        chunk_index=int(idx)
                    ))
            except Exception as e:
                logger.error(f"Qdrant query failed: {e}")
                # Fallback to FAISS search
                self.vector_db_type = VectorDBType.FAISS
                return await self.retrieve(query, top_k=top_k, similarity_threshold=similarity_threshold, filters=filters)
            return sources
        return sources
    
    def classify_question_type(self, question: str) -> str:
        """Classify the type of question being asked."""
        question_lower = question.lower()
        
        # Define question type patterns
        patterns = {
            'factual': [
                r'\b(what|who|when|where|which)\b',
                r'\b(is|are|was|were)\b',
                r'\b(how many|how much)\b'
            ],
            'analytical': [
                r'\b(why|how)\b',
                r'\b(explain|describe|analyze)\b',
                r'\b(compare|contrast)\b'
            ],
            'comparative': [
                r'\b(compare|versus|vs|difference|similar)\b',
                r'\b(better|worse|best|worst)\b'
            ],
            'summarization': [
                r'\b(summarize|summary|overview)\b',
                r'\b(main points|key points)\b'
            ]
        }
        
        for qtype, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, question_lower):
                    return qtype
        
        return 'factual'  # Default to factual
    
    def generate_response(self, 
                         question: str, 
                         context_docs: List[Dict[str, Any]], 
                         response_type: str = 'auto') -> Dict[str, Any]:
        """Generate a response using the retrieved context."""
        if not context_docs:
            return {
                'answer': 'I could not find relevant information to answer your question.',
                'confidence': 0.0,
                'sources': [],
                'response_type': 'no_context'
            }
        
        # Determine response type
        if response_type == 'auto':
            response_type = self.classify_question_type(question)
        
        # Prepare context
        context_text = "\n\n".join([doc['text'] for doc in context_docs])
        
        # Generate response based on type
        if response_type == 'factual' and self.qa_pipeline:
            return self._generate_qa_response(question, context_text, context_docs)
        elif response_type == 'summarization':
            return self._generate_summary_response(question, context_text, context_docs)
        else:
            return self._generate_text_response(question, context_text, context_docs, response_type)
    
    def _generate_qa_response(self, question: str, context: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using question-answering model."""
        try:
            response = self.qa_pipeline(
                question=question,
                context=context,
                max_answer_len=150,
                handle_impossible_answer=True
            )
            
            return {
                'answer': response['answer'],
                'confidence': float(response.get('score', 0.5)),
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'qa',
                'start': response.get('start', 0),
                'end': response.get('end', 0)
            }
        except Exception as e:
            logger.error(f"Error in QA response generation: {e}")
            return self._generate_text_response(question, context, context_docs, 'factual')
    
    def _generate_text_response(self, question: str, context: str, context_docs: List[Dict[str, Any]], response_type: str) -> Dict[str, Any]:
        """Generate response using text generation model."""
        if not self.text_gen_pipeline:
            return {
                'answer': 'I am unable to generate a response at this time.',
                'confidence': 0.0,
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'text_gen',
                'error': 'No text generation model available'
            }
        
        try:
            # Create a structured prompt based on question type
            if response_type == 'analytical':
                prompt = f"""Context: {context}

Question: {question}

Analysis: Based on the provided context, """
            elif response_type == 'comparative':
                prompt = f"""Context: {context}

Question: {question}

Comparison: """
            else:
                prompt = f"""Context: {context}

Question: {question}

Answer: Based on the context provided, """
            
            response = self.text_gen_pipeline(
                prompt,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.text_gen_pipeline.tokenizer.eos_token_id
            )
            
            generated_text = response[0]["generated_text"]
            
            # Extract the answer part
            answer = self._extract_answer_from_generated(generated_text, prompt)
            
            return {
                'answer': answer,
                'confidence': 0.6,  # Default confidence for text generation
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'text_gen',
                'full_response': generated_text
            }
            
        except Exception as e:
            logger.error(f"Error in text generation: {e}")
            return {
                'answer': 'I encountered an error while generating a response.',
                'confidence': 0.0,
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'text_gen',
                'error': str(e)
            }
    
    def _generate_summary_response(self, question: str, context: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary response."""
        try:
            # Extract key information from context
            sentences = re.split(r'[.!?]+', context)
            key_sentences = []
            
            # Simple keyword-based sentence selection
            question_words = set(re.findall(r'\b\w+\b', question.lower()))
            
            for sentence in sentences:
                sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
                overlap = len(question_words.intersection(sentence_words))
                if overlap > 0:
                    key_sentences.append(sentence)
            
            if key_sentences:
                summary = ". ".join(key_sentences[:3]) + "."
            else:
                summary = context[:500] + "..." if len(context) > 500 else context
            
            return {
                'answer': summary,
                'confidence': 0.7,
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'summary'
            }
            
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            return {
                'answer': 'I could not generate a summary at this time.',
                'confidence': 0.0,
                'sources': [doc['metadata'] for doc in context_docs],
                'response_type': 'summary',
                'error': str(e)
            }
    
    def _extract_answer_from_generated(self, generated_text: str, prompt: str) -> str:
        """Extract the answer part from generated text."""
        # Remove the prompt from the generated text
        if generated_text.startswith(prompt):
            answer_part = generated_text[len(prompt):]
        else:
            answer_part = generated_text
        
        # Clean up the answer
        answer_part = answer_part.strip()
        
        # Try to find answer patterns
        patterns = [
            r'Answer:\s*(.*?)(?:\n|$)',
            r'Analysis:\s*(.*?)(?:\n|$)',
            r'Comparison:\s*(.*?)(?:\n|$)',
            r'Summary:\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, answer_part, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no pattern found, return the first sentence or first 200 characters
        sentences = re.split(r'[.!?]+', answer_part)
        if sentences:
            return sentences[0].strip()
        
        return answer_part[:200].strip()
    
    def ask(self, question: str, k: int = 5, response_type: str = 'auto') -> Dict[str, Any]:
        """Main method to ask a question and get a response."""
        start_time = datetime.now()
        
        try:
            # Retrieve relevant documents
            context_docs = self.retrieve(question, k=k)
            
            # Generate response
            response = self.generate_response(question, context_docs, response_type)
            
            # Add metadata
            response['question'] = question
            response['processing_time'] = (datetime.now() - start_time).total_seconds()
            response['context_count'] = len(context_docs)
            response['timestamp'] = datetime.now().isoformat()
            
            return response
            
        except Exception as e:
            logger.error(f"Error in ask method: {e}")
            return {
                'answer': 'I encountered an error while processing your question.',
                'confidence': 0.0,
                'sources': [],
                'response_type': 'error',
                'error': str(e),
                'question': question,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the RAG system."""
        return {
            'embedding_model': self.embedding_model,
            'document_count': len(self.documents),
            'index_built': self.index is not None,
            'qa_model_available': self.qa_pipeline is not None,
            'text_gen_model_available': self.text_gen_pipeline is not None,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        } 

    # New management APIs expected by FastAPI layer
    def list_documents(self) -> List[DocumentInfo]:
        return list(self.id_to_info.values())

    def get_document_info(self, document_id: str) -> Optional[DocumentInfo]:
        return self.id_to_info.get(document_id)

    async def delete_document(self, document_id: str) -> bool:
        if document_id not in self.id_to_info:
            return False
        # Remove all chunks belonging to doc_id
        indices_to_keep: List[int] = []
        new_documents: List[str] = []
        new_metadata: List[Dict[str, Any]] = []
        new_index_to_id: Dict[int, str] = {}
        for idx, text in enumerate(self.documents):
            if self.doc_index_to_id.get(idx) != document_id:
                new_index_to_id[len(new_documents)] = self.doc_index_to_id.get(idx)
                new_documents.append(text)
                new_metadata.append(self.metadata[idx])
        self.documents = new_documents
        self.metadata = new_metadata
        self.doc_index_to_id = new_index_to_id
        # Remove registry entry and rebuild index
        del self.id_to_info[document_id]
        self._build_index()
        return True

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.id_to_info),
            "total_chunks": len(self.documents),
            "vector_db_type": self.vector_db_type.value if hasattr(self.vector_db_type, 'value') else str(self.vector_db_type)
        }

    # Backend initialization helpers
    def _init_backend(self):
        try:
            if self.vector_db_type == VectorDBType.CHROMA:
                import chromadb
                self._backend_client = chromadb.PersistentClient(path=self.vector_db_path)
                self._backend_collection = self._backend_client.get_or_create_collection(name="documents")
                logger.info("Chroma backend initialized")
            elif self.vector_db_type == VectorDBType.QDRANT:
                from qdrant_client import QdrantClient
                import os
                host = os.environ.get("QDRANT_HOST", "localhost")
                port = int(os.environ.get("QDRANT_PORT", "6333"))
                self._backend_client = QdrantClient(host=host, port=port)
                logger.info("Qdrant backend initialized")
        except Exception as e:
            logger.error(f"Backend init failed: {e}")
            # Fallback to FAISS if backend not available
            self.vector_db_type = VectorDBType.FAISS

    def _ensure_qdrant_collection(self, dim: int):
        if self.vector_db_type != VectorDBType.QDRANT or self._backend_client is None:
            return
        from qdrant_client.models import Distance, VectorParams
        try:
            self._backend_client.get_collection("documents")
        except Exception:
            self._backend_client.recreate_collection(
                collection_name="documents",
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )