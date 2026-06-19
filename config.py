from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "AI应用通用框架"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_framework"
    REDIS_URL: str = "redis://localhost:6379"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_framework"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    MODEL_CACHE_DIR: str = "./models"
    DEFAULT_LLM_MODEL: str = "deepseek-chat"
    DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    API_V1_PREFIX: str = "/api/v1"
    
    SECRET_KEY: str = "dev-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    PROMETHEUS_ENABLED: bool = False
    
    model_config = {"env_file": ".env", "case_sensitive": True}

settings = Settings()

os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE) or "./logs", exist_ok=True)
