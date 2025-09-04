"""
Document management endpoints with file upload support
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.file_storage import file_storage
from ...services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    user_id: int = Form(1),  # Simplified - would come from JWT token
    is_sensitive: bool = Form(False),
    metadata: Optional[str] = Form(None),  # JSON string
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document file for processing
    
    - **file**: The file to upload
    - **document_type**: Type of document (medical_report, prescription, etc.)
    - **user_id**: User ID (from authentication)
    - **is_sensitive**: Whether document contains sensitive data
    - **metadata**: Additional metadata as JSON string
    """
    
    try:
        # Save uploaded file
        file_path, checksum, file_size, mime_type = await file_storage.save_upload(
            file, user_id, document_type
        )
        
        # Create document record in database
        # Note: This would use the actual database models
        document_data = {
            "user_id": user_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "document_type": document_type or "other",
            "status": "uploaded",
            "is_sensitive": is_sensitive,
            "checksum": checksum
        }
        
        # In real implementation, would create Document model instance
        document_id = 123  # Mock document ID
        
        # Queue document for processing
        job_id = await queue_service.queue_document_processing(
            document_id=document_id,
            file_path=file_path,
            document_type=document_type or "other"
        )
        
        logger.info(f"Document uploaded: {file.filename} -> {file_path}")
        
        return {
            "document_id": document_id,
            "job_id": job_id,
            "filename": file.filename,
            "size": file_size,
            "type": document_type,
            "status": "uploaded",
            "message": "Document uploaded successfully and queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents")
async def list_documents(
    user_id: int = Query(1),  # Would come from JWT token
    status: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """List user documents with filtering options"""
    
    # In real implementation, would query Document model
    # For demo, return mock data
    documents = [
        {
            "id": 1,
            "filename": "medical_report_1.pdf",
            "document_type": "medical_report", 
            "status": "completed",
            "uploaded_at": "2024-01-01T10:00:00Z",
            "size": 1024576
        },
        {
            "id": 2,
            "filename": "prescription_scan.jpg",
            "document_type": "prescription",
            "status": "processing", 
            "uploaded_at": "2024-01-01T11:00:00Z",
            "size": 2048192
        }
    ]
    
    # Apply filters
    if status:
        documents = [d for d in documents if d["status"] == status]
    if document_type:
        documents = [d for d in documents if d["document_type"] == document_type]
    
    return {
        "documents": documents[offset:offset+limit],
        "total": len(documents),
        "limit": limit,
        "offset": offset
    }

@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    user_id: int = Query(1),  # Would come from JWT token  
    db: AsyncSession = Depends(get_db)
):
    """Get document details"""
    
    # In real implementation, would query Document model
    # For demo, return mock data
    if document_id == 1:
        return {
            "id": 1,
            "filename": "medical_report_1.pdf",
            "original_filename": "Medical Report - John Doe.pdf",
            "document_type": "medical_report",
            "status": "completed", 
            "uploaded_at": "2024-01-01T10:00:00Z",
            "processed_at": "2024-01-01T10:05:00Z",
            "size": 1024576,
            "mime_type": "application/pdf",
            "quality_score": 0.95,
            "is_sensitive": True,
            "page_count": 3,
            "processing_results": {
                "entities_extracted": 25,
                "confidence_score": 0.92,
                "processing_time": 45.2
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    user_id: int = Query(1),  # Would come from JWT token
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and its files"""
    
    # In real implementation, would:
    # 1. Check user permissions
    # 2. Get document from database
    # 3. Delete file from storage
    # 4. Update database record
    
    logger.info(f"Document deletion requested: {document_id}")
    
    return {
        "document_id": document_id,
        "message": "Document deleted successfully"
    }

@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    user_id: int = Query(1),  # Would come from JWT token
    db: AsyncSession = Depends(get_db)
):
    """Queue document for reprocessing"""
    
    # In real implementation, would:
    # 1. Check user permissions
    # 2. Get document from database
    # 3. Queue for reprocessing
    
    job_id = await queue_service.queue_document_processing(
        document_id=document_id,
        file_path=f"/app/uploads/mock_path_{document_id}.pdf",
        document_type="medical_report",
        priority=1  # Higher priority for reprocessing
    )
    
    return {
        "document_id": document_id,
        "job_id": job_id,
        "message": "Document queued for reprocessing"
    }