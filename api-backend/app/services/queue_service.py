"""
Redis-based processing queue service
"""

import json
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from ..core.redis_client import get_redis
from ..core.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class ProcessingJob:
    """Processing job data structure"""
    job_id: str
    document_id: int
    file_path: str
    document_type: str
    status: str = "queued"
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

class QueueService:
    """Redis-based queue service for document processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis = None
        
        # Queue names
        self.pending_queue = "mdus:jobs:pending"
        self.processing_queue = "mdus:jobs:processing" 
        self.completed_queue = "mdus:jobs:completed"
        self.failed_queue = "mdus:jobs:failed"
        
        # Job data key prefix
        self.job_data_prefix = "mdus:job:"
        
        # Metrics keys
        self.metrics_prefix = "mdus:metrics:"
    
    def _get_redis(self):
        """Get Redis client"""
        if not self.redis:
            self.redis = get_redis()
        return self.redis
    
    async def queue_document_processing(self, 
                                       document_id: int,
                                       file_path: str, 
                                       document_type: str,
                                       priority: int = 0) -> str:
        """Queue a document for processing"""
        
        redis = self._get_redis()
        job_id = str(uuid.uuid4())
        
        # Create job object
        job = ProcessingJob(
            job_id=job_id,
            document_id=document_id,
            file_path=file_path,
            document_type=document_type,
            priority=priority,
            max_retries=self.settings.retry_attempts
        )
        
        # Store job data
        job_key = f"{self.job_data_prefix}{job_id}"
        await redis.setex(
            job_key,
            timedelta(hours=24).total_seconds(),  # Expire after 24 hours
            json.dumps(asdict(job))
        )
        
        # Add to pending queue with priority
        await redis.zadd(self.pending_queue, {job_id: -priority})  # Negative for descending order
        
        # Update metrics
        await self._update_metrics("jobs_queued", 1)
        
        logger.info(f"Job queued: {job_id} for document {document_id}")
        return job_id
    
    async def get_next_job(self) -> Optional[ProcessingJob]:
        """Get next job from pending queue"""
        
        redis = self._get_redis()
        
        # Get highest priority job
        jobs = await redis.zrange(self.pending_queue, 0, 0, withscores=True)
        if not jobs:
            return None
        
        job_id, priority = jobs[0]
        
        # Remove from pending queue
        await redis.zrem(self.pending_queue, job_id)
        
        # Add to processing queue
        await redis.zadd(self.processing_queue, {job_id: datetime.utcnow().timestamp()})
        
        # Get job data
        job_data = await self._get_job_data(job_id)
        if not job_data:
            logger.error(f"Job data not found: {job_id}")
            return None
        
        # Update job status
        job_data.status = "processing"
        job_data.started_at = datetime.utcnow().isoformat()
        await self._save_job_data(job_data)
        
        logger.info(f"Job started: {job_id}")
        return job_data
    
    async def complete_job(self, 
                          job_id: str, 
                          result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        
        redis = self._get_redis()
        
        # Remove from processing queue
        await redis.zrem(self.processing_queue, job_id)
        
        # Add to completed queue
        await redis.zadd(self.completed_queue, {job_id: datetime.utcnow().timestamp()})
        
        # Update job data
        job_data = await self._get_job_data(job_id)
        if job_data:
            job_data.status = "completed"
            job_data.completed_at = datetime.utcnow().isoformat()
            job_data.result = result
            await self._save_job_data(job_data)
        
        # Update metrics
        await self._update_metrics("jobs_completed", 1)
        
        logger.info(f"Job completed: {job_id}")
    
    async def fail_job(self, 
                      job_id: str, 
                      error_message: str,
                      retry: bool = True):
        """Mark job as failed and optionally retry"""
        
        redis = self._get_redis()
        
        # Remove from processing queue
        await redis.zrem(self.processing_queue, job_id)
        
        # Get job data
        job_data = await self._get_job_data(job_id)
        if not job_data:
            logger.error(f"Job data not found for failure: {job_id}")
            return
        
        job_data.retry_count += 1
        job_data.error_message = error_message
        job_data.completed_at = datetime.utcnow().isoformat()
        
        # Check if we should retry
        if retry and job_data.retry_count < job_data.max_retries:
            # Reset for retry
            job_data.status = "queued"
            job_data.started_at = None
            job_data.completed_at = None
            
            # Add back to pending queue with lower priority
            await redis.zadd(self.pending_queue, {job_id: -(job_data.priority - 1)})
            
            logger.info(f"Job queued for retry: {job_id} (attempt {job_data.retry_count})")
        else:
            # Mark as failed
            job_data.status = "failed"
            await redis.zadd(self.failed_queue, {job_id: datetime.utcnow().timestamp()})
            
            # Update metrics
            await self._update_metrics("jobs_failed", 1)
            
            logger.error(f"Job failed: {job_id} - {error_message}")
        
        await self._save_job_data(job_data)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        
        job_data = await self._get_job_data(job_id)
        if not job_data:
            return None
        
        return asdict(job_data)
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        
        redis = self._get_redis()
        
        return {
            "pending": await redis.zcard(self.pending_queue),
            "processing": await redis.zcard(self.processing_queue),
            "completed": await redis.zcard(self.completed_queue),
            "failed": await redis.zcard(self.failed_queue)
        }
    
    async def cleanup_stuck_jobs(self, timeout_minutes: int = None):
        """Clean up jobs that have been processing too long"""
        
        timeout = timeout_minutes or self.settings.job_timeout_minutes
        redis = self._get_redis()
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout)
        cutoff_timestamp = cutoff_time.timestamp()
        
        # Get stuck jobs
        stuck_jobs = await redis.zrangebyscore(
            self.processing_queue, 
            0, 
            cutoff_timestamp,
            withscores=True
        )
        
        cleanup_count = 0
        for job_id, started_time in stuck_jobs:
            await self.fail_job(
                job_id, 
                f"Job timeout after {timeout} minutes",
                retry=True
            )
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} stuck jobs")
        return cleanup_count
    
    async def cleanup_old_jobs(self, days_old: int = 7):
        """Clean up old completed and failed jobs"""
        
        redis = self._get_redis()
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        cutoff_timestamp = cutoff_time.timestamp()
        
        # Clean completed jobs
        old_completed = await redis.zrangebyscore(
            self.completed_queue,
            0,
            cutoff_timestamp
        )
        
        # Clean failed jobs  
        old_failed = await redis.zrangebyscore(
            self.failed_queue,
            0, 
            cutoff_timestamp
        )
        
        # Remove job data and queue entries
        cleanup_count = 0
        for job_id in old_completed + old_failed:
            # Remove job data
            await redis.delete(f"{self.job_data_prefix}{job_id}")
            # Remove from queues
            await redis.zrem(self.completed_queue, job_id)
            await redis.zrem(self.failed_queue, job_id)
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} old jobs")
        return cleanup_count
    
    async def _get_job_data(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job data from Redis"""
        
        redis = self._get_redis()
        job_key = f"{self.job_data_prefix}{job_id}"
        
        data = await redis.get(job_key)
        if not data:
            return None
        
        try:
            job_dict = json.loads(data)
            return ProcessingJob(**job_dict)
        except Exception as e:
            logger.error(f"Failed to deserialize job data {job_id}: {e}")
            return None
    
    async def _save_job_data(self, job: ProcessingJob):
        """Save job data to Redis"""
        
        redis = self._get_redis()
        job_key = f"{self.job_data_prefix}{job.job_id}"
        
        await redis.setex(
            job_key,
            timedelta(hours=24).total_seconds(),
            json.dumps(asdict(job))
        )
    
    async def _update_metrics(self, metric_name: str, value: int):
        """Update processing metrics"""
        
        redis = self._get_redis()
        metric_key = f"{self.metrics_prefix}{metric_name}"
        
        await redis.incrby(metric_key, value)
        
        # Set expiry for daily metrics
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_key = f"{metric_key}:{today}"
        await redis.incrby(daily_key, value)
        await redis.expire(daily_key, timedelta(days=30).total_seconds())

# Global queue service instance
queue_service = QueueService()