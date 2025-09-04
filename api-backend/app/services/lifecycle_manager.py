"""
File lifecycle management service for MDUS
Handles file retention, archiving, and cleanup policies
"""

import asyncio
import logging
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import text

from .file_storage import file_storage
from .queue_service import queue_service
from ..core.config import get_settings
from ..core.database import get_db

logger = logging.getLogger(__name__)

class FileLifecycleManager:
    """Manages file lifecycle from upload to archival/deletion"""
    
    def __init__(self):
        self.settings = get_settings()
        self.is_running = False
    
    async def start_scheduler(self):
        """Start the lifecycle management scheduler"""
        
        logger.info("Starting file lifecycle manager...")
        self.is_running = True
        
        # Schedule cleanup tasks
        schedule.every(1).hours.do(self._schedule_temp_cleanup)
        schedule.every(6).hours.do(self._schedule_stuck_job_cleanup)
        schedule.every().day.at("02:00").do(self._schedule_file_retention_check)
        schedule.every().day.at("03:00").do(self._schedule_old_job_cleanup)
        schedule.every().week.do(self._schedule_archive_cleanup)
        
        # Run scheduler loop
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
        
        logger.info("File lifecycle manager stopped")
    
    def stop_scheduler(self):
        """Stop the lifecycle manager"""
        self.is_running = False
    
    def _schedule_temp_cleanup(self):
        """Schedule temporary file cleanup"""
        asyncio.create_task(self.cleanup_temp_files())
    
    def _schedule_stuck_job_cleanup(self):
        """Schedule stuck job cleanup"""
        asyncio.create_task(self.cleanup_stuck_jobs())
    
    def _schedule_file_retention_check(self):
        """Schedule file retention policy check"""
        asyncio.create_task(self.enforce_retention_policies())
    
    def _schedule_old_job_cleanup(self):
        """Schedule old job cleanup"""
        asyncio.create_task(self.cleanup_old_jobs())
    
    def _schedule_archive_cleanup(self):
        """Schedule archive cleanup"""
        asyncio.create_task(self.cleanup_archives())
    
    async def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files"""
        
        logger.info("Starting temporary file cleanup...")
        
        try:
            # Use file storage service to clean temp files
            cleaned_count = await file_storage.cleanup_temp_files(
                self.settings.temp_file_retention_hours
            )
            
            result = {
                "task": "temp_file_cleanup",
                "status": "completed",
                "files_cleaned": cleaned_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Temp file cleanup completed: {cleaned_count} files removed")
            return result
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            return {
                "task": "temp_file_cleanup", 
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_stuck_jobs(self) -> Dict[str, Any]:
        """Clean up stuck processing jobs"""
        
        logger.info("Starting stuck job cleanup...")
        
        try:
            # Use queue service to clean stuck jobs
            cleaned_count = await queue_service.cleanup_stuck_jobs(
                self.settings.job_timeout_minutes
            )
            
            result = {
                "task": "stuck_job_cleanup",
                "status": "completed", 
                "jobs_cleaned": cleaned_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Stuck job cleanup completed: {cleaned_count} jobs cleaned")
            return result
            
        except Exception as e:
            logger.error(f"Stuck job cleanup failed: {e}")
            return {
                "task": "stuck_job_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_old_jobs(self) -> Dict[str, Any]:
        """Clean up old completed/failed jobs"""
        
        logger.info("Starting old job cleanup...")
        
        try:
            # Clean jobs older than 7 days
            cleaned_count = await queue_service.cleanup_old_jobs(7)
            
            result = {
                "task": "old_job_cleanup",
                "status": "completed",
                "jobs_cleaned": cleaned_count, 
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Old job cleanup completed: {cleaned_count} jobs removed")
            return result
            
        except Exception as e:
            logger.error(f"Old job cleanup failed: {e}")
            return {
                "task": "old_job_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def enforce_retention_policies(self) -> Dict[str, Any]:
        """Enforce file retention policies"""
        
        logger.info("Starting retention policy enforcement...")
        
        try:
            # This would query the database for documents past their retention date
            # For demo purposes, we'll simulate this
            
            async with get_db() as db:
                # Query documents past retention date
                query = """
                SELECT id, file_path, retention_date 
                FROM documents 
                WHERE retention_date IS NOT NULL 
                AND retention_date < CURRENT_DATE
                AND status != 'archived'
                LIMIT 100
                """
                
                # This would be actual database query in production
                # result = await db.execute(text(query))
                # expired_documents = result.fetchall()
                
                # Mock expired documents for demo
                expired_documents = []
            
            archived_count = 0
            for doc in expired_documents:
                try:
                    # Archive the file
                    await file_storage.archive_file(doc.file_path, doc.id)
                    
                    # Update document status in database
                    # In production, would update the Document model
                    
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to archive document {doc.id}: {e}")
            
            result = {
                "task": "retention_policy_enforcement",
                "status": "completed",
                "documents_archived": archived_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Retention policy enforcement completed: {archived_count} documents archived")
            return result
            
        except Exception as e:
            logger.error(f"Retention policy enforcement failed: {e}")
            return {
                "task": "retention_policy_enforcement",
                "status": "failed", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_archives(self) -> Dict[str, Any]:
        """Clean up old archived files"""
        
        logger.info("Starting archive cleanup...")
        
        try:
            archive_dir = Path(self.settings.archive_dir)
            cutoff_date = datetime.now() - timedelta(days=365)  # Keep archives for 1 year
            
            cleaned_count = 0
            if archive_dir.exists():
                for file_path in archive_dir.rglob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            try:
                                file_path.unlink()
                                cleaned_count += 1
                            except Exception as e:
                                logger.error(f"Failed to delete archived file {file_path}: {e}")
            
            result = {
                "task": "archive_cleanup",
                "status": "completed",
                "files_cleaned": cleaned_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Archive cleanup completed: {cleaned_count} files removed")
            return result
            
        except Exception as e:
            logger.error(f"Archive cleanup failed: {e}")
            return {
                "task": "archive_cleanup",
                "status": "failed",
                "error": str(e), 
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage utilization statistics"""
        
        try:
            stats = {}
            
            # Check each storage directory
            directories = {
                "uploads": self.settings.upload_dir,
                "processed": self.settings.processed_dir,
                "temp": self.settings.temp_dir,
                "archive": self.settings.archive_dir
            }
            
            for name, directory in directories.items():
                path = Path(directory)
                if path.exists():
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    file_count = sum(1 for f in path.rglob('*') if f.is_file())
                    
                    stats[name] = {
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "file_count": file_count,
                        "path": str(path)
                    }
                else:
                    stats[name] = {
                        "total_size_bytes": 0,
                        "total_size_mb": 0,
                        "file_count": 0,
                        "path": str(path),
                        "note": "Directory does not exist"
                    }
            
            # Calculate totals
            total_size = sum(s["total_size_bytes"] for s in stats.values())
            total_files = sum(s["file_count"] for s in stats.values())
            
            return {
                "storage_stats": stats,
                "totals": {
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
                    "total_files": total_files
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def manual_cleanup(self, 
                           cleanup_temp: bool = True,
                           cleanup_stuck_jobs: bool = True,
                           cleanup_old_jobs: bool = True,
                           enforce_retention: bool = False) -> Dict[str, Any]:
        """Perform manual cleanup operations"""
        
        logger.info("Starting manual cleanup operations...")
        
        results = []
        
        if cleanup_temp:
            result = await self.cleanup_temp_files()
            results.append(result)
        
        if cleanup_stuck_jobs:
            result = await self.cleanup_stuck_jobs()
            results.append(result)
        
        if cleanup_old_jobs:
            result = await self.cleanup_old_jobs()
            results.append(result)
        
        if enforce_retention:
            result = await self.enforce_retention_policies()
            results.append(result)
        
        # Calculate summary
        total_files_cleaned = sum(r.get("files_cleaned", 0) for r in results)
        total_jobs_cleaned = sum(r.get("jobs_cleaned", 0) for r in results)
        failed_tasks = [r for r in results if r.get("status") == "failed"]
        
        return {
            "manual_cleanup": {
                "completed_tasks": len(results),
                "failed_tasks": len(failed_tasks),
                "total_files_cleaned": total_files_cleaned,
                "total_jobs_cleaned": total_jobs_cleaned,
                "task_results": results
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Global lifecycle manager instance
lifecycle_manager = FileLifecycleManager()

async def start_lifecycle_manager():
    """Start the lifecycle manager"""
    await lifecycle_manager.start_scheduler()

def stop_lifecycle_manager():
    """Stop the lifecycle manager"""
    lifecycle_manager.stop_scheduler()

if __name__ == "__main__":
    # Run lifecycle manager standalone
    asyncio.run(start_lifecycle_manager())