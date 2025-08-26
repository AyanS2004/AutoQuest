"""
Configuration management for AutoQuest
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = Field(default="AutoQuest", env="APP_NAME")
    version: str = Field(default="1.0.0", env="VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    enforce_roles: bool = Field(default=False, env="ENFORCE_ROLES")
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    
    # AI Models
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Vector Database
    vector_db_type: str = Field(default="chroma", env="VECTOR_DB_TYPE")
    vector_db_path: str = Field(default="./vector_db", env="VECTOR_DB_PATH")
    chroma_host: Optional[str] = Field(default=None, env="CHROMA_HOST")
    chroma_port: Optional[int] = Field(default=None, env="CHROMA_PORT")
    
    # Document Processing
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    supported_formats: List[str] = Field(
        default=[".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv"],
        env="SUPPORTED_FORMATS"
    )
    
    # Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="./temp", env="TEMP_DIR")
    logs_dir: str = Field(default="./logs", env="LOGS_DIR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    enable_sentry: bool = Field(default=False, env="ENABLE_SENTRY")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    # GCC Specific
    gcc_debug_port: int = Field(default=9222, env="GCC_DEBUG_PORT")
    gcc_batch_size: int = Field(default=3, env="GCC_BATCH_SIZE")
    gcc_timeout: int = Field(default=120, env="GCC_TIMEOUT")
    
    # Cache
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    @validator('supported_formats', pre=True)
    def parse_supported_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(',')]
        return v
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_env_file_path() -> Path:
    """Get the path to the environment file"""
    return Path(".env")


def create_env_file_if_missing():
    """Create .env file from example if it doesn't exist"""
    env_path = get_env_file_path()
    example_path = Path("env.example")
    
    if not env_path.exists() and example_path.exists():
        import shutil
        shutil.copy(example_path, env_path)
        print(f"Created {env_path} from {example_path}")
        print("Please edit the .env file with your configuration.")


def validate_required_settings(settings: Settings) -> List[str]:
    """Validate required settings and return list of missing ones"""
    missing = []
    
    # Check for required API keys based on model selection
    if "openai" in settings.embedding_model.lower() or "openai" in settings.llm_model.lower():
        if not settings.openai_api_key:
            missing.append("OPENAI_API_KEY")
    
    if "anthropic" in settings.llm_model.lower():
        if not settings.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
    
    # Check for required directories
    required_dirs = [settings.upload_dir, settings.temp_dir, settings.logs_dir]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return missing


def get_model_config(settings: Settings) -> Dict[str, Any]:
    """Get model-specific configuration"""
    config = {
        "embedding_model": settings.embedding_model,
        "llm_model": settings.llm_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }
    
    if settings.openai_api_key:
        config["openai_api_key"] = settings.openai_api_key
    
    if settings.anthropic_api_key:
        config["anthropic_api_key"] = settings.anthropic_api_key
    
    return config


def get_vector_db_config(settings: Settings) -> Dict[str, Any]:
    """Get vector database configuration"""
    config = {
        "type": settings.vector_db_type,
        "path": settings.vector_db_path,
    }
    
    if settings.vector_db_type == "chroma":
        if settings.chroma_host:
            config["host"] = settings.chroma_host
        if settings.chroma_port:
            config["port"] = settings.chroma_port
    
    return config
