"""
Core configuration for MDUS API Backend
"""

import os
from typing import List
from pydantic import BaseSettings, Field, validator
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database settings
    postgres_url: str = Field(..., env="POSTGRES_URL")
    
    # Redis settings
    redis_url: str = Field(..., env="REDIS_URL")
    
    # AI Service settings
    ai_service_url: str = Field("http://ai_service:8000", env="AI_SERVICE_URL")
    
    # Security settings
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    # CORS settings
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # File storage settings
    upload_dir: str = Field("/app/uploads", env="UPLOAD_DIR")
    processed_dir: str = Field("/app/processed", env="PROCESSED_DIR")
    temp_dir: str = Field("/app/temp", env="TEMP_DIR")
    archive_dir: str = Field("/app/archive", env="ARCHIVE_DIR")
    
    max_file_size: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_file_types: List[str] = Field([
        "application/pdf",
        "image/jpeg", 
        "image/png",
        "image/tiff",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ], env="ALLOWED_FILE_TYPES")
    
    # Processing settings
    max_concurrent_jobs: int = Field(5, env="MAX_CONCURRENT_JOBS")
    job_timeout_minutes: int = Field(30, env="JOB_TIMEOUT_MINUTES")
    retry_attempts: int = Field(3, env="RETRY_ATTEMPTS")
    
    # Cleanup settings
    temp_file_retention_hours: int = Field(24, env="TEMP_FILE_RETENTION_HOURS")
    processed_file_retention_days: int = Field(30, env="PROCESSED_FILE_RETENTION_DAYS")
    
    # Security and compliance
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    require_authentication: bool = Field(True, env="REQUIRE_AUTHENTICATION")
    
    # Monitoring settings
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and "," in v:
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            return [v]
        return v
    
    @validator("allowed_file_types", pre=True)
    def assemble_file_types(cls, v):
        if isinstance(v, str) and "," in v:
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            return [v]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()