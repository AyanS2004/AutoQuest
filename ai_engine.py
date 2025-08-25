import asyncio
from typing import List, Dict, Any, Optional, Tuple
import time
import logging
from datetime import datetime
import uuid
import json

from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering, AutoModelForCausalLM
import torch
from optimum.onnxruntime import ORTModelForQuestionAnswering, ORTModelForCausalLM
import numpy as np

from config import settings, ModelType
import redis
from autoquest.api.schemas.core import QuestionRequest, AnswerResponse, Source, QuestionType, ChatMessage, ChatRequest, ChatResponse


logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.cache = {}
        self.redis_client: Optional[redis.Redis] = None
        self.model_status = {}
        
        # Initialize models
        self._init_models()
        self._init_cache_backend()
        
    def _init_models(self):
        """Initialize all required models"""
        try:
            # Initialize QA model
            self._load_qa_model()
            self.model_status["qa"] = "loaded"
        except Exception as e:
            logger.error(f"Failed to load QA model: {str(e)}")
            self.model_status["qa"] = "failed"
        
        try:
            # Initialize text generation model
            self._load_generation_model()
            self.model_status["text_generation"] = "loaded"
        except Exception as e:
            logger.error(f"Failed to load text generation model: {str(e)}")
            self.model_status["text_generation"] = "failed"
        
        try:
            # Initialize chat model
            self._load_chat_model()
            self.model_status["chat"] = "loaded"
        except Exception as e:
            logger.error(f"Failed to load chat model: {str(e)}")
            self.model_status["chat"] = "failed"
    
    def _init_cache_backend(self):
        """Initialize optional Redis cache backend."""
        if not settings.enable_cache or not settings.redis_url:
            return
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            self.redis_client.ping()
            logger.info("Connected to Redis cache backend")
        except Exception as e:
            self.redis_client = None
            logger.warning(f"Redis cache unavailable: {str(e)}")
    
    def _load_qa_model(self):
        """Load question-answering model"""
        model_name = settings.qa_model
        
        # Try to load optimized model first
        try:
            self.models["qa"] = ORTModelForQuestionAnswering.from_pretrained(
                model_name, 
                export=True,
                provider="CPUExecutionProvider"
            )
            self.tokenizers["qa"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded optimized QA model: {model_name}")
        except:
            # Fallback to regular model
            self.models["qa"] = AutoModelForQuestionAnswering.from_pretrained(model_name)
            self.tokenizers["qa"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded regular QA model: {model_name}")
    
    def _load_generation_model(self):
        """Load text generation model"""
        model_name = settings.generation_model
        
        try:
            self.models["text_generation"] = ORTModelForCausalLM.from_pretrained(
                model_name,
                export=True,
                provider="CPUExecutionProvider"
            )
            self.tokenizers["text_generation"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded optimized generation model: {model_name}")
        except:
            self.models["text_generation"] = AutoModelForCausalLM.from_pretrained(model_name)
            self.tokenizers["text_generation"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded regular generation model: {model_name}")
    
    def _load_chat_model(self):
        """Load chat model"""
        model_name = settings.chat_model
        
        try:
            self.models["chat"] = ORTModelForCausalLM.from_pretrained(
                model_name,
                export=True,
                provider="CPUExecutionProvider"
            )
            self.tokenizers["chat"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded optimized chat model: {model_name}")
        except:
            self.models["chat"] = AutoModelForCausalLM.from_pretrained(model_name)
            self.tokenizers["chat"] = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded regular chat model: {model_name}")
    
    async def generate_answer(self, request: QuestionRequest, sources: List[Source]) -> AnswerResponse:
        """Generate an answer based on the question and retrieved sources"""
        start_time = time.time()
        
        # Create cache key
        cache_key = self._create_cache_key(request, sources)
        
        # Check cache
        if settings.enable_cache:
            if self.redis_client is not None:
                try:
                    cached_bytes = self.redis_client.get(cache_key)
                    if cached_bytes:
                        data = json.loads(cached_bytes)
                        resp = AnswerResponse(**data)
                        resp.processing_time = time.time() - start_time
                        return resp
                except Exception:
                    pass
            if cache_key in self.cache:
                cached_response = self.cache[cache_key]
                cached_response.processing_time = time.time() - start_time
                return cached_response
        
        # Prepare context
        context_text = self._prepare_context(sources)
        
        # Generate answer based on question type
        if request.question_type == QuestionType.FACTUAL:
            answer, confidence, model_used = await self._generate_factual_answer(request, context_text)
        elif request.question_type == QuestionType.ANALYTICAL:
            answer, confidence, model_used = await self._generate_analytical_answer(request, context_text)
        elif request.question_type == QuestionType.COMPARATIVE:
            answer, confidence, model_used = await self._generate_comparative_answer(request, context_text)
        elif request.question_type == QuestionType.SUMMARIZATION:
            answer, confidence, model_used = await self._generate_summary_answer(request, context_text)
        else:
            answer, confidence, model_used = await self._generate_factual_answer(request, context_text)
        
        # Create response
        response = AnswerResponse(
            answer=answer,
            confidence_score=confidence,
            sources=sources if request.include_sources else [],
            processing_time=time.time() - start_time,
            model_used=model_used,
            question_type=request.question_type,
            metadata={
                "context_length": len(context_text),
                "sources_count": len(sources),
                "temperature": request.temperature
            }
        )
        
        # Cache response
        if settings.enable_cache:
            try:
                if self.redis_client is not None:
                    payload = json.dumps(response.dict()).encode("utf-8")
                    self.redis_client.setex(cache_key, settings.cache_ttl, payload)
                else:
                    self.cache[cache_key] = response
            except Exception:
                self.cache[cache_key] = response
        
        return response
    
    async def _generate_factual_answer(self, request: QuestionRequest, context: str) -> Tuple[str, float, str]:
        """Generate factual answer using QA model"""
        if "qa" in self.models and self.model_status["qa"] == "loaded":
            try:
                # Use QA pipeline
                qa_pipeline = pipeline(
                    "question-answering",
                    model=self.models["qa"],
                    tokenizer=self.tokenizers["qa"]
                )
                
                result = qa_pipeline(
                    question=request.question,
                    context=context,
                    max_answer_len=request.max_answer_length,
                    handle_impossible_answer=True
                )
                
                answer = result['answer']
                confidence = result.get('score', 0.8)
                
                return answer, confidence, "qa_model"
                
            except Exception as e:
                logger.error(f"QA model failed: {str(e)}")
        
        # Fallback to text generation
        return await self._generate_text_answer(request, context, "factual")
    
    async def _generate_analytical_answer(self, request: QuestionRequest, context: str) -> Tuple[str, float, str]:
        """Generate analytical answer"""
        prompt = f"""Based on the following context, provide an analytical answer to the question.

Context: {context}

Question: {request.question}

Please analyze the information and provide insights:"""
        
        return await self._generate_text_answer(request, context, "analytical", prompt)
    
    async def _generate_comparative_answer(self, request: QuestionRequest, context: str) -> Tuple[str, float, str]:
        """Generate comparative answer"""
        prompt = f"""Based on the following context, provide a comparative analysis.

Context: {context}

Question: {request.question}

Please compare and contrast the relevant information:"""
        
        return await self._generate_text_answer(request, context, "comparative", prompt)
    
    async def _generate_summary_answer(self, request: QuestionRequest, context: str) -> Tuple[str, float, str]:
        """Generate summary answer"""
        prompt = f"""Based on the following context, provide a comprehensive summary.

Context: {context}

Question: {request.question}

Please provide a detailed summary:"""
        
        return await self._generate_text_answer(request, context, "summary", prompt)
    
    async def _generate_text_answer(self, request: QuestionRequest, context: str, 
                                  answer_type: str, custom_prompt: str = None) -> Tuple[str, float, str]:
        """Generate answer using text generation model"""
        if "text_generation" not in self.models or self.model_status["text_generation"] != "loaded":
            # Fallback response
            return "I apologize, but I'm unable to generate a response at the moment.", 0.5, "fallback"
        
        try:
            # Prepare prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = f"""Context: {context}

Question: {request.question}

Answer: Based on the context provided, """
            
            # Tokenize
            inputs = self.tokenizers["text_generation"](
                prompt,
                return_tensors="pt",
                max_length=settings.max_context_length,
                truncation=True
            )
            
            # Generate
            with torch.no_grad():
                outputs = self.models["text_generation"].generate(
                    **inputs,
                    max_new_tokens=request.max_answer_length,
                    do_sample=True,
                    temperature=request.temperature,
                    top_p=0.9,
                    pad_token_id=self.tokenizers["text_generation"].eos_token_id,
                    eos_token_id=self.tokenizers["text_generation"].eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizers["text_generation"].decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # Extract answer
            answer = self._extract_answer_from_generated(generated_text, prompt)
            
            # Calculate confidence based on length and source recall
            context_coverage = min(1.0, len(context) / max(1, settings.max_context_length)) if context else 0.0
            base = len(answer) / 150 + 0.25
            confidence = float(max(0.1, min(0.95, base * (0.7 + 0.3 * context_coverage))))
            
            return answer, confidence, "text_generation"
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            return "I apologize, but I encountered an error while generating the response.", 0.3, "error"
    
    async def generate_chat_response(self, request: ChatRequest, sources: List[Source]) -> ChatResponse:
        """Generate chat response"""
        start_time = time.time()
        
        if "chat" not in self.models or self.model_status["chat"] != "loaded":
            # Fallback response
            fallback_message = ChatMessage(
                role="assistant",
                content="I apologize, but I'm unable to generate a response at the moment."
            )
            return ChatResponse(
                message=fallback_message,
                conversation_id=request.conversation_id or "fallback",
                processing_time=time.time() - start_time
            )
        
        try:
            # Prepare conversation history
            conversation_text = self._prepare_conversation_history(request.messages)
            
            # Add context if requested
            if request.include_context and sources:
                context_text = self._prepare_context(sources)
                conversation_text += f"\n\nRelevant context: {context_text}\n\n"
            
            # Get last user message
            last_user_message = request.messages[-1].content
            
            # Generate response
            prompt = f"{conversation_text}User: {last_user_message}\nAssistant:"
            
            inputs = self.tokenizers["chat"](
                prompt,
                return_tensors="pt",
                max_length=settings.max_context_length,
                truncation=True
            )
            
            with torch.no_grad():
                outputs = self.models["chat"].generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizers["chat"].eos_token_id,
                    eos_token_id=self.tokenizers["chat"].eos_token_id
                )
            
            generated_text = self.tokenizers["chat"].decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # Extract assistant response
            response_text = self._extract_chat_response(generated_text, prompt)
            
            response_message = ChatMessage(
                role="assistant",
                content=response_text
            )
            
            return ChatResponse(
                message=response_message,
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                sources=sources if request.include_context else [],
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Chat generation failed: {str(e)}")
            fallback_message = ChatMessage(
                role="assistant",
                content="I apologize, but I encountered an error while generating the response."
            )
            return ChatResponse(
                message=fallback_message,
                conversation_id=request.conversation_id or "fallback",
                processing_time=time.time() - start_time
            )
    
    def _prepare_context(self, sources: List[Source]) -> str:
        """Prepare context from sources"""
        if not sources:
            return ""
        
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"Source {i} (from {source.file_name}): {source.chunk_text}")
        
        return "\n\n".join(context_parts)
    
    def _prepare_conversation_history(self, messages: List[ChatMessage]) -> str:
        """Prepare conversation history for chat model"""
        if not messages:
            return ""
        
        conversation_parts = []
        for message in messages[:-1]:  # Exclude last message as it will be added separately
            conversation_parts.append(f"{message.role.capitalize()}: {message.content}")
        
        return "\n".join(conversation_parts)
    
    def _extract_answer_from_generated(self, generated_text: str, prompt: str) -> str:
        """Extract answer from generated text"""
        # Remove the prompt from generated text
        if generated_text.startswith(prompt):
            answer = generated_text[len(prompt):].strip()
        else:
            answer = generated_text.strip()
        
        # Clean up the answer
        answer = answer.replace("Answer:", "").strip()
        
        # Limit length
        if len(answer) > 1000:
            answer = answer[:1000] + "..."
        
        return answer if answer else "I couldn't generate a specific answer based on the provided context."
    
    def _extract_chat_response(self, generated_text: str, prompt: str) -> str:
        """Extract chat response from generated text"""
        if generated_text.startswith(prompt):
            response = generated_text[len(prompt):].strip()
        else:
            response = generated_text.strip()
        
        # Clean up
        response = response.replace("Assistant:", "").strip()
        
        # Limit length
        if len(response) > 500:
            response = response[:500] + "..."
        
        return response if response else "I'm not sure how to respond to that."
    
    def _create_cache_key(self, request: QuestionRequest, sources: List[Source]) -> str:
        """Create cache key for request"""
        source_hashes = [hash(source.chunk_text) for source in sources]
        return f"{hash(request.question)}_{hash(tuple(source_hashes))}_{request.question_type.value}"
    
    def get_model_status(self) -> Dict[str, str]:
        """Get status of all models"""
        return self.model_status.copy()
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        try:
            if self.redis_client is not None:
                self.redis_client.flushdb()
        except Exception:
            pass
        logger.info("Response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_enabled": settings.enable_cache,
            "cache_ttl": settings.cache_ttl
        } 