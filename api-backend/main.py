"""
MDUS API Backend - Main Application
FastAPI application for Medical Data Understanding System
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Import modules
from app.core.config import get_settings
from app.core.database import init_db
from app.core.redis_client import init_redis, get_redis
from app.api.routes import documents, processing, health, auth, monitoring
from app.core.middleware import setup_middleware
from app.services.file_storage import ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MDUS API Backend...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    # Ensure storage directories exist
    ensure_directories()
    logger.info("Storage directories initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MDUS API Backend...")
    
    # Close Redis connection
    redis_client = get_redis()
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

# Create FastAPI app
app = FastAPI(
    title="MDUS API Backend",
    description="Medical Data Understanding System - API Backend Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Get settings
settings = get_settings()

# Setup middleware
setup_middleware(app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(processing.router, prefix="/api/v1", tags=["Processing"])
app.include_router(monitoring.router, prefix="/api/v1", tags=["Monitoring"])

# Mount static files for uploaded documents (with security)
if os.path.exists("/app/uploads"):
    app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MDUS API Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "mdus-api-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )