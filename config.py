from pydantic import BaseSettings, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import os


class ModelType(str, Enum):
    QA = "qa"
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"


class EmbeddingModel(str, Enum):
    MINILM = "all-MiniLM-L6-v2"
    MPNET = "all-mpnet-base-v2"
    E5 = "intfloat/e5-large-v2"
    BGE = "BAAI/bge-large-en-v1.5"


class VectorDBType(str, Enum):
    FAISS = "faiss"
    CHROMA = "chroma"
    QDRANT = "qdrant"


class Settings(BaseSettings):
    # Application
    app_name: str = "RAG-Enhanced Enterprise AI Platform"
    version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Models
    embedding_model: EmbeddingModel = EmbeddingModel.BGE
    qa_model: str = "deepset/roberta-base-squad2"
    generation_model: str = "microsoft/DialoGPT-medium"
    chat_model: str = "microsoft/DialoGPT-large"
    
    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    max_context_length: int = 4000
    enable_hybrid: bool = Field(default=True, env="ENABLE_HYBRID")
    hybrid_alpha: float = Field(default=0.6, env="HYBRID_ALPHA")  # weight for vector vs lexical
    
    # Vector Database
    vector_db_type: VectorDBType = VectorDBType.CHROMA
    vector_db_path: str = "./vector_db"
    
    # Caching
    cache_ttl: int = 3600  # 1 hour
    enable_cache: bool = True
    
    # Monitoring
    enable_metrics: bool = True
    enable_sentry: bool = False
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    enforce_roles: bool = Field(default=False, env="ENFORCE_ROLES")
    
    # File Processing
    supported_formats: List[str] = [".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv"]
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    enable_redis_rate_limit: bool = Field(default=False, env="ENABLE_REDIS_RATE_LIMIT")
    
    # Background tasks
    use_celery: bool = Field(default=False, env="USE_CELERY")
    celery_broker_url: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 