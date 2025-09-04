"""
File storage and management service
"""

import os
import uuid
import hashlib
import mimetypes
import aiofiles
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class FileStorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self.processed_dir = Path(self.settings.processed_dir)
        self.temp_dir = Path(self.settings.temp_dir)
        self.archive_dir = Path(self.settings.archive_dir)
    
    async def save_upload(self, 
                         file: UploadFile, 
                         user_id: int,
                         document_type: Optional[str] = None) -> Tuple[str, str, int, str]:
        """
        Save uploaded file and return file info
        Returns: (file_path, checksum, file_size, mime_type)
        """
        
        # Validate file
        await self._validate_file(file)
        
        # Generate unique filename
        file_ext = self._get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create user directory
        user_dir = self.upload_dir / str(user_id) / datetime.now().strftime("%Y/%m/%d")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_dir / unique_filename
        
        # Save file and calculate checksum
        checksum = hashlib.sha256()
        file_size = 0
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):
                    await f.write(chunk)
                    checksum.update(chunk)
                    file_size += len(chunk)
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = file.content_type or 'application/octet-stream'
            
            logger.info(f"File saved: {file_path} ({file_size} bytes)")
            
            return str(file_path), checksum.hexdigest(), file_size, mime_type
            
        except Exception as e:
            # Cleanup on error
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")
    
    async def move_to_processed(self, 
                               source_path: str, 
                               document_id: int) -> str:
        """Move file from uploads to processed directory"""
        
        source = Path(source_path)
        if not source.exists():
            raise HTTPException(status_code=404, detail="Source file not found")
        
        # Create processed directory structure
        processed_dir = self.processed_dir / str(document_id)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = processed_dir / source.name
        
        try:
            shutil.move(str(source), str(dest_path))
            logger.info(f"File moved to processed: {dest_path}")
            return str(dest_path)
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise HTTPException(status_code=500, detail="Failed to move file")
    
    async def archive_file(self, 
                          source_path: str, 
                          document_id: int) -> str:
        """Archive processed file"""
        
        source = Path(source_path)
        if not source.exists():
            raise HTTPException(status_code=404, detail="Source file not found")
        
        # Create archive directory structure  
        archive_dir = self.archive_dir / str(document_id)
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = archive_dir / f"{datetime.now().isoformat()}_{source.name}"
        
        try:
            shutil.move(str(source), str(dest_path))
            logger.info(f"File archived: {dest_path}")
            return str(dest_path)
        except Exception as e:
            logger.error(f"Failed to archive file: {e}")
            raise HTTPException(status_code=500, detail="Failed to archive file")
    
    async def cleanup_temp_files(self, hours_old: int = None):
        """Clean up temporary files older than specified hours"""
        
        hours = hours_old or self.settings.temp_file_retention_hours
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cleaned_count = 0
        for file_path in self.temp_dir.rglob('*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete temp file {file_path}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} temporary files")
        return cleaned_count
    
    async def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            "filename": path.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "mime_type": mime_type
        }
    
    async def delete_file(self, file_path: str):
        """Safely delete a file"""
        
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"File deleted: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete file")
    
    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""
        
        # Check file size
        if hasattr(file, 'size') and file.size > self.settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.settings.max_file_size} bytes"
            )
        
        # Check MIME type
        if file.content_type not in self.settings.allowed_file_types:
            raise HTTPException(
                status_code=415,
                detail=f"File type not allowed: {file.content_type}"
            )
        
        # Reset file pointer
        await file.seek(0)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if not filename:
            return ''
        return Path(filename).suffix.lower()

def ensure_directories():
    """Ensure all required directories exist"""
    settings = get_settings()
    
    directories = [
        settings.upload_dir,
        settings.processed_dir, 
        settings.temp_dir,
        settings.archive_dir
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")

# Global file storage service instance
file_storage = FileStorageService()