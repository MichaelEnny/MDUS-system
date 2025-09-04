# MDUS API Backend - File Storage & Processing Pipeline

The MDUS API Backend provides a comprehensive file storage and processing pipeline for medical document understanding. This system handles the complete workflow from file upload through processing to result storage.

## 🏗️ Architecture Overview

### Core Components

1. **File Upload & Storage Service**
   - Secure file upload with validation
   - Multiple storage directories (uploads, processed, temp, archive)
   - File lifecycle management

2. **Redis Processing Queue**
   - Asynchronous job processing
   - Priority-based queuing
   - Automatic retry logic
   - Job status tracking

3. **Background Processing Worker**
   - Document classification and processing
   - Integration with AI service
   - Quality assessment
   - Entity extraction

4. **File Lifecycle Management**
   - Automated cleanup of temporary files
   - Retention policy enforcement
   - Archive management
   - Storage optimization

5. **Monitoring & Health Checks**
   - System health monitoring
   - Performance metrics
   - Alert system
   - Storage statistics

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Start the complete system:
```bash
cd MDUS-system
docker-compose up -d
```

2. Check system health:
```bash
curl http://localhost:8000/api/v1/health
```

3. Access API documentation:
```
http://localhost:8000/api/docs
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run different components:
```bash
# API server only (development)
python run_system.py api

# Processing worker only
python run_system.py worker

# Lifecycle manager only
python run_system.py lifecycle

# Complete system
python run_system.py full
```

## 📁 Directory Structure

```
api-backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint definitions
│   ├── core/               # Core configuration and utilities
│   ├── services/           # Business logic services
│   └── models/            # Data models (if needed)
├── uploads/               # Docker volume mount point
├── processed/            # Docker volume mount point
├── temp/                 # Docker volume mount point
├── archive/              # Docker volume mount point
├── main.py               # FastAPI application entry point
├── run_system.py         # System orchestrator
├── test_workflow.py      # Complete workflow test
└── requirements.txt      # Python dependencies
```

## 🔄 Processing Workflow

1. **File Upload**
   - Client uploads file via `/api/v1/documents/upload`
   - File validation (size, type, security)
   - Secure storage in uploads directory
   - Database record creation
   - Job queuing for processing

2. **Queue Processing**
   - Redis-based job queue
   - Background worker picks up jobs
   - Priority-based processing
   - Automatic retry on failures

3. **Document Processing**
   - File classification
   - OCR/text extraction
   - Medical entity extraction
   - Quality assessment
   - Result storage

4. **File Lifecycle**
   - Move to processed directory
   - Retention policy application
   - Automatic cleanup
   - Archive management

## 🔍 API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document
- `POST /api/v1/documents/{id}/reprocess` - Reprocess document

### Processing Management
- `GET /api/v1/processing/jobs/{job_id}` - Get job status
- `GET /api/v1/processing/queue/stats` - Queue statistics
- `GET /api/v1/processing/jobs` - List processing jobs

### Monitoring
- `GET /api/v1/monitoring/health` - System health
- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/alerts` - System alerts
- `GET /api/v1/monitoring/storage` - Storage statistics
- `POST /api/v1/monitoring/cleanup` - Manual cleanup

### Health Checks
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health status

## 🧪 Testing

### Automated Workflow Test

Run the complete workflow test:

```bash
python test_workflow.py
```

This test covers:
- ✅ Health check endpoints
- ✅ File upload functionality
- ✅ Job status monitoring  
- ✅ Document retrieval
- ✅ Queue statistics
- ✅ Monitoring endpoints

### Manual Testing

1. **Upload a test file:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@test_document.pdf" \
  -F "document_type=medical_report" \
  -F "user_id=1"
```

2. **Check job status:**
```bash
curl "http://localhost:8000/api/v1/processing/jobs/{job_id}"
```

3. **Monitor system health:**
```bash
curl "http://localhost:8000/api/v1/monitoring/health"
```

## 📊 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
POSTGRES_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://:password@host:6379/0

# File Storage
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=/app/uploads
PROCESSED_DIR=/app/processed

# Processing
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_MINUTES=30

# Cleanup
TEMP_FILE_RETENTION_HOURS=24
PROCESSED_FILE_RETENTION_DAYS=30
```

### Docker Volumes

The system uses persistent Docker volumes:

- `api_uploads` - Uploaded files
- `processed_files` - Processed documents
- `temp_uploads` - Temporary files
- `archive_storage` - Archived documents

## 🔒 Security Features

- File type validation
- Size limits enforcement
- Secure file storage
- Non-root container user
- Input sanitization
- Error handling
- Audit logging (configurable)

## 📈 Monitoring & Maintenance

### Automatic Cleanup

The system automatically:
- Cleans temporary files (configurable interval)
- Removes stuck processing jobs
- Enforces retention policies
- Archives old documents

### Manual Maintenance

Use the monitoring endpoints for manual operations:

```bash
# Trigger cleanup
curl -X POST "http://localhost:8000/api/v1/monitoring/cleanup?admin_token=admin123"

# Check storage usage
curl "http://localhost:8000/api/v1/monitoring/storage"
```

## 🚨 Troubleshooting

### Common Issues

1. **Upload fails with 415 error**
   - Check file type is in `ALLOWED_FILE_TYPES`
   - Verify file isn't corrupted

2. **Jobs stuck in processing**
   - Check AI service connectivity
   - Review job timeout settings
   - Use cleanup endpoint

3. **Storage full**
   - Run manual cleanup
   - Check retention policies
   - Monitor storage statistics

### Logs

Check container logs:
```bash
docker logs mdus_api_backend
```

## 🔄 Development

### Running in Development Mode

```bash
# API server with reload
python run_system.py api

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality

```bash
# Format code
black .
isort .

# Run tests
pytest
```

## 📝 Task Implementation Summary

### ✅ Completed Features

1. **Docker Volume Configuration** 
   - ✅ Persistent storage volumes
   - ✅ Organized directory structure
   - ✅ Proper permissions

2. **File Upload & Storage**
   - ✅ Secure file upload endpoints
   - ✅ File validation and storage
   - ✅ Multiple storage directories

3. **Redis Processing Queue**
   - ✅ Priority-based job queue
   - ✅ Retry logic and error handling
   - ✅ Job status tracking

4. **Background Processing**
   - ✅ Asynchronous worker system
   - ✅ Document processing pipeline
   - ✅ AI service integration

5. **File Lifecycle Management**
   - ✅ Automated cleanup
   - ✅ Retention policies
   - ✅ Archive management

6. **Monitoring & Health Checks**
   - ✅ Comprehensive health endpoints
   - ✅ System metrics collection
   - ✅ Alert system

7. **Complete Workflow Testing**
   - ✅ Automated test suite
   - ✅ End-to-end workflow validation
   - ✅ Performance monitoring

This implementation provides a production-ready file storage and processing pipeline that handles the complete workflow from upload to processing to storage, with comprehensive monitoring and maintenance capabilities.