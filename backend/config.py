"""
Environment configuration for Code Documentation Assistant
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    api_title: str = "Code Documentation Assistant"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI Settings
    openai_api_key: str = ''
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Pinecone Settings
    pinecone_api_key: str = ''
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "code-docs"
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_documents: int = 5
    chunking_strategy: str = "auto"  # Options: 'auto', 'ast', 'lines'
    embedding_backend: str = "sentence-transformers"  # Options: 'openai', 'sentence-transformers'
    
    # LLM Backend
    llm_backend: str = "local-quantized"  # Options: 'openai', 'ollama'
    ollama_model: str = "llama2"  # Default Ollama model name
    local_quantized_model_path: str = "backend/models/llama-2-7b-chat.Q4_K_M.gguf"  # Path to local quantized model (e.g., GGML/GPTQ)
    
    # Observability
    enable_logging: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
