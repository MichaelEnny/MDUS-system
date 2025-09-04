"""
Monitoring and metrics service for MDUS
Provides health checks, metrics collection, and system monitoring
"""

import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import text

from .queue_service import queue_service
from .lifecycle_manager import lifecycle_manager
from ..core.database import get_db
from ..core.redis_client import get_redis
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class MonitoringService:
    """System monitoring and health check service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "checks": {}
        }
        
        # Database health check
        try:
            async with get_db() as db:
                result = await db.execute(text("SELECT 1 as health_check"))
                if result.scalar() == 1:
                    health_data["checks"]["database"] = {
                        "status": "healthy",
                        "response_time_ms": 0  # Would measure actual response time
                    }
                else:
                    health_data["checks"]["database"] = {"status": "unhealthy"}
                    health_data["status"] = "degraded"
        except Exception as e:
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Redis health check
        try:
            redis_client = get_redis()
            if redis_client:
                await redis_client.ping()
                health_data["checks"]["redis"] = {"status": "healthy"}
            else:
                health_data["checks"]["redis"] = {"status": "unavailable"}
                health_data["status"] = "degraded"
        except Exception as e:
            health_data["checks"]["redis"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Queue health check
        try:
            queue_stats = await queue_service.get_queue_stats()
            total_jobs = sum(queue_stats.values())
            
            health_data["checks"]["processing_queue"] = {
                "status": "healthy" if total_jobs < 1000 else "warning",
                "total_jobs": total_jobs,
                "queue_stats": queue_stats
            }
            
            if total_jobs > 1000:
                health_data["status"] = "warning"
                
        except Exception as e:
            health_data["checks"]["processing_queue"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Storage health check
        try:
            storage_stats = await lifecycle_manager.get_storage_stats()
            total_size_gb = storage_stats.get("totals", {}).get("total_size_gb", 0)
            
            storage_status = "healthy"
            if total_size_gb > 50:  # Warning at 50GB
                storage_status = "warning"
            if total_size_gb > 100:  # Critical at 100GB
                storage_status = "critical"
                health_data["status"] = "degraded"
            
            health_data["checks"]["storage"] = {
                "status": storage_status,
                "total_size_gb": total_size_gb,
                "total_files": storage_stats.get("totals", {}).get("total_files", 0)
            }
            
        except Exception as e:
            health_data["checks"]["storage"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        return health_data
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {},
            "application": {},
            "processing": {}
        }
        
        # System metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics["system"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": round(memory.used / (1024 * 1024), 2),
                "memory_total_mb": round(memory.total / (1024 * 1024), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2)
            }
        except Exception as e:
            metrics["system"] = {"error": str(e)}
        
        # Application metrics
        try:
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            
            metrics["application"] = {
                "uptime_seconds": uptime_seconds,
                "uptime_human": self._format_uptime(uptime_seconds),
                "service_name": "mdus-api-backend",
                "version": "1.0.0"
            }
        except Exception as e:
            metrics["application"] = {"error": str(e)}
        
        # Processing metrics
        try:
            queue_stats = await queue_service.get_queue_stats()
            storage_stats = await lifecycle_manager.get_storage_stats()
            
            metrics["processing"] = {
                "queue_stats": queue_stats,
                "total_queued_jobs": sum(queue_stats.values()),
                "storage_stats": storage_stats.get("totals", {}),
                "processing_capacity": self._calculate_processing_capacity(queue_stats)
            }
        except Exception as e:
            metrics["processing"] = {"error": str(e)}
        
        return metrics
    
    async def get_performance_metrics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get performance metrics over time"""
        
        try:
            # This would query actual performance data from database/Redis
            # For demo, return mock performance data
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Mock performance data
            performance_data = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days_back
                },
                "processing_stats": {
                    "total_jobs_completed": 1247,
                    "total_jobs_failed": 23,
                    "success_rate": 98.2,
                    "average_processing_time_seconds": 45.7,
                    "total_documents_processed": 1247,
                    "total_size_processed_gb": 12.4
                },
                "daily_breakdown": [
                    {
                        "date": (end_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                        "jobs_completed": 150 + (i * 10),
                        "jobs_failed": 2 + i,
                        "avg_processing_time": 44.5 + (i * 0.5)
                    }
                    for i in range(days_back)
                ],
                "error_breakdown": {
                    "timeout_errors": 8,
                    "ai_service_errors": 7,
                    "file_errors": 5,
                    "other_errors": 3
                }
            }
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_system_alerts(self) -> List[Dict[str, Any]]:
        """Check for system alerts and issues"""
        
        alerts = []
        
        # Check queue backlog
        try:
            queue_stats = await queue_service.get_queue_stats()
            pending_jobs = queue_stats.get("pending", 0)
            
            if pending_jobs > 100:
                alerts.append({
                    "type": "warning",
                    "component": "processing_queue",
                    "message": f"High queue backlog: {pending_jobs} pending jobs",
                    "severity": "high" if pending_jobs > 500 else "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as e:
            alerts.append({
                "type": "error",
                "component": "processing_queue", 
                "message": f"Unable to check queue status: {e}",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check storage usage
        try:
            storage_stats = await lifecycle_manager.get_storage_stats()
            total_size_gb = storage_stats.get("totals", {}).get("total_size_gb", 0)
            
            if total_size_gb > 80:
                alerts.append({
                    "type": "warning",
                    "component": "storage",
                    "message": f"High storage usage: {total_size_gb:.1f}GB",
                    "severity": "high" if total_size_gb > 95 else "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as e:
            alerts.append({
                "type": "error",
                "component": "storage",
                "message": f"Unable to check storage usage: {e}",
                "severity": "medium",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if cpu_percent > 80:
                alerts.append({
                    "type": "warning",
                    "component": "system",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            if memory.percent > 85:
                alerts.append({
                    "type": "warning",
                    "component": "system",
                    "message": f"High memory usage: {memory.percent:.1f}%",
                    "severity": "high" if memory.percent > 95 else "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            alerts.append({
                "type": "error",
                "component": "system",
                "message": f"Unable to check system resources: {e}",
                "severity": "medium", 
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h") 
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "< 1m"
    
    def _calculate_processing_capacity(self, queue_stats: Dict[str, int]) -> str:
        """Calculate current processing capacity"""
        
        processing_jobs = queue_stats.get("processing", 0)
        pending_jobs = queue_stats.get("pending", 0)
        
        if processing_jobs >= self.settings.max_concurrent_jobs:
            return "at_capacity"
        elif processing_jobs + pending_jobs > self.settings.max_concurrent_jobs * 2:
            return "high_load"
        elif pending_jobs > 50:
            return "moderate_load"
        else:
            return "normal"

# Global monitoring service instance
monitoring_service = MonitoringService()