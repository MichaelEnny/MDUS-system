"""
Monitoring and metrics endpoints
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ...services.monitoring_service import monitoring_service
from ...services.lifecycle_manager import lifecycle_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/monitoring/health")
async def get_system_health():
    """Get comprehensive system health status"""
    
    try:
        health_data = await monitoring_service.get_system_health()
        return health_data
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "error"
        }

@router.get("/monitoring/metrics")
async def get_system_metrics():
    """Get detailed system metrics"""
    
    try:
        metrics = await monitoring_service.get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {e}")

@router.get("/monitoring/performance")
async def get_performance_metrics(days_back: int = Query(7, ge=1, le=30)):
    """Get performance metrics over specified time period"""
    
    try:
        performance_data = await monitoring_service.get_performance_metrics(days_back)
        return performance_data
    except Exception as e:
        logger.error(f"Performance metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {e}")

@router.get("/monitoring/alerts")
async def get_system_alerts():
    """Get current system alerts and warnings"""
    
    try:
        alerts = await monitoring_service.check_system_alerts()
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "high_severity_alerts": len([a for a in alerts if a.get("severity") == "high"]),
            "medium_severity_alerts": len([a for a in alerts if a.get("severity") == "medium"])
        }
    except Exception as e:
        logger.error(f"Alert check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Alert check failed: {e}")

@router.get("/monitoring/storage")
async def get_storage_statistics():
    """Get storage utilization statistics"""
    
    try:
        storage_stats = await lifecycle_manager.get_storage_stats()
        return storage_stats
    except Exception as e:
        logger.error(f"Storage stats collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Storage stats failed: {e}")

@router.post("/monitoring/cleanup")
async def trigger_manual_cleanup(
    cleanup_temp: bool = Query(True),
    cleanup_stuck_jobs: bool = Query(True), 
    cleanup_old_jobs: bool = Query(True),
    enforce_retention: bool = Query(False),
    admin_token: str = Query(...)
):
    """Trigger manual cleanup operations (admin only)"""
    
    # Simple admin check - in production use proper authentication
    if admin_token != "admin123":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        cleanup_result = await lifecycle_manager.manual_cleanup(
            cleanup_temp=cleanup_temp,
            cleanup_stuck_jobs=cleanup_stuck_jobs,
            cleanup_old_jobs=cleanup_old_jobs,
            enforce_retention=enforce_retention
        )
        
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Manual cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")