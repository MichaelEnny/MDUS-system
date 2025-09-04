"""
Processing and job management endpoints
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/processing/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get processing job status"""
    
    job_data = await queue_service.get_job_status(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "document_id": job_data["document_id"],
        "document_type": job_data["document_type"],
        "created_at": job_data["created_at"],
        "started_at": job_data.get("started_at"),
        "completed_at": job_data.get("completed_at"),
        "retry_count": job_data["retry_count"],
        "error_message": job_data.get("error_message"),
        "result": job_data.get("result")
    }

@router.get("/processing/queue/stats")
async def get_queue_statistics():
    """Get processing queue statistics"""
    
    stats = await queue_service.get_queue_stats()
    
    return {
        "queue_stats": stats,
        "total_jobs": sum(stats.values()),
        "processing_capacity": "normal"  # Could be calculated based on load
    }

@router.post("/processing/maintenance/cleanup-stuck")
async def cleanup_stuck_jobs(
    timeout_minutes: Optional[int] = Query(None),
    admin_token: str = Query(...)  # Simple admin authentication
):
    """Clean up stuck processing jobs (admin only)"""
    
    # Simple admin check - in production use proper authentication
    if admin_token != "admin123":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cleanup_count = await queue_service.cleanup_stuck_jobs(timeout_minutes)
    
    return {
        "message": f"Cleaned up {cleanup_count} stuck jobs",
        "cleanup_count": cleanup_count
    }

@router.post("/processing/maintenance/cleanup-old")
async def cleanup_old_jobs(
    days_old: Optional[int] = Query(7),
    admin_token: str = Query(...)  # Simple admin authentication
):
    """Clean up old completed/failed jobs (admin only)"""
    
    # Simple admin check - in production use proper authentication  
    if admin_token != "admin123":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cleanup_count = await queue_service.cleanup_old_jobs(days_old)
    
    return {
        "message": f"Cleaned up {cleanup_count} old jobs",
        "cleanup_count": cleanup_count
    }

@router.get("/processing/jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    document_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """List processing jobs with filters"""
    
    # In real implementation, would query job data from Redis or database
    # For demo, return mock data
    jobs = [
        {
            "job_id": "123e4567-e89b-12d3-a456-426614174000",
            "document_id": 1,
            "status": "completed",
            "document_type": "medical_report",
            "created_at": "2024-01-01T10:00:00Z",
            "completed_at": "2024-01-01T10:05:00Z",
            "processing_time": 45.2
        },
        {
            "job_id": "456e7890-e12b-34d5-b789-567890123456", 
            "document_id": 2,
            "status": "processing",
            "document_type": "prescription",
            "created_at": "2024-01-01T11:00:00Z",
            "started_at": "2024-01-01T11:01:00Z"
        }
    ]
    
    # Apply filters
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    if document_id:
        jobs = [j for j in jobs if j["document_id"] == document_id]
    
    return {
        "jobs": jobs[offset:offset+limit],
        "total": len(jobs),
        "limit": limit,
        "offset": offset
    }