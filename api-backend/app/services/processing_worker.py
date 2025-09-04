"""
Background processing worker for document processing jobs
"""

import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from .queue_service import queue_service, ProcessingJob
from .file_storage import file_storage
from ..core.config import get_settings
from ..core.redis_client import init_redis

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Document processing worker"""
    
    def __init__(self):
        self.settings = get_settings()
        self.is_running = False
        self.max_concurrent_jobs = self.settings.max_concurrent_jobs
        self.processing_jobs = set()
        self.ai_service_client = None
    
    async def start(self):
        """Start the processing worker"""
        
        logger.info("Starting document processing worker...")
        
        # Initialize Redis connection
        await init_redis()
        
        # Initialize HTTP client for AI service
        self.ai_service_client = httpx.AsyncClient(
            base_url=self.settings.ai_service_url,
            timeout=httpx.Timeout(timeout=300.0)  # 5 minute timeout
        )
        
        self.is_running = True
        
        # Start processing loop
        await self._processing_loop()
    
    async def stop(self):
        """Stop the processing worker"""
        
        logger.info("Stopping document processing worker...")
        
        self.is_running = False
        
        # Wait for current jobs to complete
        if self.processing_jobs:
            logger.info(f"Waiting for {len(self.processing_jobs)} jobs to complete...")
            await asyncio.gather(*self.processing_jobs, return_exceptions=True)
        
        # Close HTTP client
        if self.ai_service_client:
            await self.ai_service_client.aclose()
        
        logger.info("Document processing worker stopped")
    
    async def _processing_loop(self):
        """Main processing loop"""
        
        while self.is_running:
            try:
                # Check if we can take more jobs
                if len(self.processing_jobs) < self.max_concurrent_jobs:
                    # Get next job from queue
                    job = await queue_service.get_next_job()
                    if job:
                        # Start processing job
                        task = asyncio.create_task(self._process_job(job))
                        self.processing_jobs.add(task)
                        
                        # Clean up completed tasks
                        self.processing_jobs = {t for t in self.processing_jobs if not t.done()}
                
                # Wait before checking for more jobs
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _process_job(self, job: ProcessingJob):
        """Process a single job"""
        
        logger.info(f"Processing job: {job.job_id} for document {job.document_id}")
        
        try:
            # Process based on document type
            result = await self._process_document(job)
            
            # Mark job as completed
            await queue_service.complete_job(job.job_id, result)
            
            # Move file to processed directory
            processed_path = await file_storage.move_to_processed(
                job.file_path, 
                job.document_id
            )
            
            logger.info(f"Job completed: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Job failed: {job.job_id} - {e}")
            
            # Mark job as failed
            await queue_service.fail_job(job.job_id, str(e))
    
    async def _process_document(self, job: ProcessingJob) -> Dict[str, Any]:
        """Process document based on its type"""
        
        start_time = datetime.utcnow()
        
        # Get file info
        file_info = await file_storage.get_file_info(job.file_path)
        
        processing_result = {
            "job_id": job.job_id,
            "document_id": job.document_id,
            "document_type": job.document_type,
            "file_info": file_info,
            "processing_started": start_time.isoformat(),
            "steps_completed": []
        }
        
        # Step 1: Basic file validation
        processing_result["steps_completed"].append("file_validation")
        
        # Step 2: Document classification (if type is unknown)
        if job.document_type in ["other", "unknown"]:
            classification_result = await self._classify_document(job.file_path)
            processing_result["classification"] = classification_result
            processing_result["steps_completed"].append("document_classification")
        
        # Step 3: OCR/Text extraction
        extraction_result = await self._extract_text(job.file_path, job.document_type)
        processing_result["text_extraction"] = extraction_result
        processing_result["steps_completed"].append("text_extraction")
        
        # Step 4: Entity extraction (medical entities for medical documents)
        if job.document_type in ["medical_report", "prescription", "laboratory_result"]:
            entity_result = await self._extract_medical_entities(
                extraction_result.get("text", ""),
                job.document_type
            )
            processing_result["entity_extraction"] = entity_result
            processing_result["steps_completed"].append("entity_extraction")
        
        # Step 5: Quality assessment
        quality_result = await self._assess_quality(job.file_path, extraction_result)
        processing_result["quality_assessment"] = quality_result
        processing_result["steps_completed"].append("quality_assessment")
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_result["processing_completed"] = end_time.isoformat()
        processing_result["processing_time_seconds"] = (end_time - start_time).total_seconds()
        
        # Calculate overall confidence score
        processing_result["confidence_score"] = self._calculate_confidence_score(processing_result)
        
        logger.info(
            f"Document processing completed for {job.document_id} "
            f"in {processing_result['processing_time_seconds']:.2f}s"
        )
        
        return processing_result
    
    async def _classify_document(self, file_path: str) -> Dict[str, Any]:
        """Classify document type using AI service"""
        
        try:
            # Call AI service for document classification
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = await self.ai_service_client.post(
                    '/classify',
                    files=files
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.warning(f"Document classification failed: {e}")
            return {
                "document_type": "other",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _extract_text(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract text from document using AI service"""
        
        try:
            # Call AI service for OCR/text extraction
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'document_type': document_type}
                
                response = await self.ai_service_client.post(
                    '/extract-text',
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "page_count": 1,
                "error": str(e)
            }
    
    async def _extract_medical_entities(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract medical entities using AI service"""
        
        try:
            # Call AI service for entity extraction
            payload = {
                "text": text,
                "document_type": document_type
            }
            
            response = await self.ai_service_client.post(
                '/extract-entities',
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return {
                "entities": [],
                "entity_count": 0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _assess_quality(self, file_path: str, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess document quality"""
        
        try:
            # Simple quality assessment based on text extraction results
            text_length = len(extraction_result.get("text", ""))
            extraction_confidence = extraction_result.get("confidence", 0.0)
            
            # Calculate quality score (0-1)
            quality_score = min(1.0, (text_length / 1000) * 0.5 + extraction_confidence * 0.5)
            
            quality_issues = []
            if text_length < 100:
                quality_issues.append("Low text content")
            if extraction_confidence < 0.7:
                quality_issues.append("Low extraction confidence")
            
            return {
                "quality_score": round(quality_score, 4),
                "text_length": text_length,
                "extraction_confidence": extraction_confidence,
                "quality_issues": quality_issues,
                "assessment": "good" if quality_score >= 0.7 else "fair" if quality_score >= 0.5 else "poor"
            }
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return {
                "quality_score": 0.0,
                "assessment": "unknown",
                "error": str(e)
            }
    
    def _calculate_confidence_score(self, result: Dict[str, Any]) -> float:
        """Calculate overall confidence score for processing result"""
        
        scores = []
        
        # Include classification confidence if available
        if "classification" in result:
            scores.append(result["classification"].get("confidence", 0.0))
        
        # Include extraction confidence
        if "text_extraction" in result:
            scores.append(result["text_extraction"].get("confidence", 0.0))
        
        # Include entity extraction confidence
        if "entity_extraction" in result:
            scores.append(result["entity_extraction"].get("confidence", 0.0))
        
        # Include quality score
        if "quality_assessment" in result:
            scores.append(result["quality_assessment"].get("quality_score", 0.0))
        
        # Calculate weighted average
        return sum(scores) / len(scores) if scores else 0.0

# Global processor instance
processor = DocumentProcessor()

async def start_worker():
    """Start the processing worker"""
    await processor.start()

async def stop_worker():
    """Stop the processing worker"""
    await processor.stop()

if __name__ == "__main__":
    # Run worker standalone
    asyncio.run(start_worker())