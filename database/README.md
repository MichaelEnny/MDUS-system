# MDUS Database System

A production-ready PostgreSQL database setup for the Medical Document Understanding System (MDUS) with comprehensive schema design, migration management, monitoring, and performance optimization.

## Overview

This database system provides:

- **Enhanced PostgreSQL Schema**: Optimized for medical document processing with proper relationships, indexing, and data types
- **Migration System**: Version-controlled database migrations with rollback capabilities
- **Connection Pooling**: Optimized connection management for high-concurrency document processing
- **Comprehensive Monitoring**: Real-time performance monitoring, alerting, and trend analysis
- **Data Access Layer**: SQLAlchemy models with business logic and validation
- **Production Configuration**: Tuned PostgreSQL settings for document processing workloads

## Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory:

```bash
# Database Configuration
POSTGRES_DB=mdus_db
POSTGRES_USER=mdus_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Security
JWT_SECRET=your_jwt_secret_key_here
```

### 2. Start Database with Docker

```bash
# Start PostgreSQL with optimized configuration
docker-compose up postgres -d

# Check database health
docker-compose logs postgres
```

### 3. Run Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Check migration status
python database/migrate.py status

# Apply all migrations
python database/migrate.py migrate

# Target specific migration
python database/migrate.py migrate --target 002_add_enhanced_features
```

### 4. Verify Setup

```python
from database.database import init_database, get_db_session
from database.monitoring import get_database_monitor

# Initialize database connection
db_manager = init_database()

# Test connection
if db_manager.test_connection():
    print("Database connection successful!")

# Check database health
monitor = get_database_monitor()
health = monitor.collect_performance_metrics()
print(f"Database health: {health}")
```

## Database Schema

### Core Tables

#### Documents
- **documents**: Main document storage with metadata
- **document_versions**: Version control for document changes
- **document_relationships**: Links between related documents

#### Analysis
- **document_analysis**: AI/ML analysis results
- **extracted_entities**: Individual entities found in documents
- **quality_checks**: Document quality assessment results

#### Processing
- **processing_jobs**: Asynchronous job queue management
- **processing_metrics**: Performance and processing metrics

#### System
- **users**: User authentication and authorization
- **model_configurations**: ML model settings and versions
- **audit_logs**: Comprehensive audit trail

### Key Features

#### 1. Document Types
```sql
-- Supported document types
CREATE TYPE document_type_enum AS ENUM (
    'medical_report', 'laboratory_result', 'prescription',
    'insurance_claim', 'patient_form', 'discharge_summary',
    'pathology_report', 'radiology_report', 'invoice',
    'contract', 'form', 'receipt', 'statement', 'other'
);
```

#### 2. Processing Status Tracking
```sql
-- Processing pipeline status
CREATE TYPE processing_status_enum AS ENUM (
    'uploaded', 'queued', 'processing', 
    'completed', 'failed', 'archived'
);
```

#### 3. Advanced Indexing
- GIN indexes for JSONB fields (metadata, structured_data)
- Full-text search indexes for document content
- Composite indexes for common query patterns
- Partial indexes for frequently filtered data

## Data Access Layer

### Using SQLAlchemy Models

```python
from database.models import Document, DocumentAnalysis, User
from database.database import get_db_session

# Create a new document
with get_db_session() as session:
    document = Document(
        user_id=user_id,
        filename="medical_report.pdf",
        original_filename="patient_report_2025.pdf",
        file_path="/uploads/documents/doc_123.pdf",
        file_size=2048576,
        mime_type="application/pdf",
        document_type=DocumentType.MEDICAL_REPORT
    )
    session.add(document)
    session.commit()

# Query documents with relationships
with get_db_session() as session:
    documents = session.query(Document)\
        .filter(Document.status == ProcessingStatus.COMPLETED)\
        .join(DocumentAnalysis)\
        .all()

# Get document analysis results
analysis = DocumentAnalysis.get_by_document(session, document.id)
for result in analysis:
    confidence = result.get_overall_confidence()
    entities = result.extracted_entities
```

### Business Logic Examples

```python
# Mark document as processed with quality score
document.mark_as_processed(quality_score=0.95)

# Check if user can access document
if user.can_access_document(document.id):
    # User has permission
    content = document.get_latest_analysis()

# Get high-confidence extractions
high_conf_entities = ExtractedEntity.get_high_confidence_entities(
    session, min_confidence=0.9
)

# Record processing metrics
ProcessingMetrics.record_metric(
    session, 
    document_id=doc.id,
    metric_type="processing_time_seconds",
    value=15.2,
    unit="seconds"
)
```

## Migration Management

### Creating New Migrations

```bash
# Create migration files in database/migrations/
# Format: XXX_description.sql

# Example: 003_add_user_preferences.sql
BEGIN;

ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);

INSERT INTO schema_migrations (version) VALUES ('003_add_user_preferences');

COMMIT;
```

### Migration Commands

```bash
# Check current status
python database/migrate.py status

# Apply all pending migrations
python database/migrate.py migrate

# Apply migrations up to specific version
python database/migrate.py migrate --target 003_add_user_preferences

# Rollback to specific version (removes migration records)
python database/migrate.py rollback --target 002_add_enhanced_features

# Verbose output
python database/migrate.py status --verbose
```

## Performance Monitoring

### Real-time Monitoring

```python
from database.monitoring import get_database_monitor

monitor = get_database_monitor()

# Collect comprehensive metrics
metrics = monitor.collect_performance_metrics()

# Check for alerts
alerts = monitor.check_alerts(metrics)
if alerts:
    for alert in alerts:
        print(f"ALERT [{alert['severity']}]: {alert['message']}")

# Get performance trends
trends = monitor.get_performance_trends(hours_back=24)
```

### Key Metrics Tracked

- **Connection Statistics**: Pool utilization, active connections, wait times
- **Query Performance**: Slow queries, execution times, query patterns  
- **Table Statistics**: Row counts, table sizes, scan patterns
- **Index Usage**: Index hit ratios, unused indexes, scan patterns
- **Cache Performance**: Buffer cache hit ratios, memory usage
- **Lock Statistics**: Lock waits, blocking queries, deadlocks
- **Disk Usage**: Database size, table sizes, growth trends
- **Replication**: WAL streaming, lag times, slot usage

### Monitoring Alerts

Configurable thresholds for:
- Connection pool usage > 80%
- Queries running > 5 minutes
- Lock waits > 1 minute
- Cache hit ratio < 95%
- Disk usage > 85%

## Configuration

### PostgreSQL Optimization

The system includes production-optimized PostgreSQL configuration:

```conf
# Key optimizations for document processing
shared_buffers = 1GB                     # 25% of RAM
effective_cache_size = 3GB               # Expected system cache
work_mem = 64MB                          # Increased for JSONB operations
max_connections = 200                    # High concurrency support
random_page_cost = 1.1                   # SSD-optimized
checkpoint_completion_target = 0.9       # Spread checkpoint I/O
```

### Connection Pooling

```python
# Pool settings optimized for document processing
pool_settings = {
    'pool_size': 20,           # Base connections
    'max_overflow': 30,        # Additional connections
    'pool_timeout': 30,        # Connection timeout
    'pool_recycle': 3600,      # Recycle after 1 hour
    'pool_pre_ping': True,     # Validate connections
}
```

## Security Features

### Authentication & Authorization

- SCRAM-SHA-256 password encryption
- Role-based access control (RBAC)
- Row-level security for multi-tenant data
- Comprehensive audit logging

### Data Protection

- SSL/TLS encryption in transit
- Sensitive data flagging and retention policies
- Automatic PII detection and masking capabilities
- Compliance with HIPAA, GDPR requirements

### Audit Trail

```python
# Automatic audit logging for all table changes
from database.models import AuditLog

# Query audit history
user_actions = AuditLog.get_by_user(session, user_id)
document_history = AuditLog.get_by_resource(session, 'documents', doc_id)
```

## Backup and Recovery

### Automated Backups

```bash
# Database backup (configure in production)
pg_dump -h localhost -U mdus_user -d mdus_db -f backup_$(date +%Y%m%d).sql

# Point-in-time recovery setup
# Configure WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'cp %p /backup/wal_archive/%f'
```

### Disaster Recovery

- Continuous WAL archiving
- Point-in-time recovery capability
- Cross-region backup replication
- Automated backup validation

## Scaling and Performance

### Read Replicas

```yaml
# docker-compose.replica.yml
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_MASTER_SERVICE: postgres
    POSTGRES_REPLICA_USER: replicator
  command: |
    postgres -c hot_standby=on -c primary_conninfo='host=postgres port=5432 user=replicator'
```

### Partitioning Strategy

```sql
-- Partition large tables by date
CREATE TABLE documents_2025 PARTITION OF documents 
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Automatic partition creation
CREATE EXTENSION pg_partman;
SELECT partman.create_parent('public.documents', 'created_at', 'range', 'monthly');
```

### Query Optimization

```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM documents 
WHERE document_type = 'medical_report' AND created_at > '2025-01-01';

-- Index recommendations
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   ```python
   # Check pool status
   pool_status = db_manager.get_pool_status()
   print(f"Pool utilization: {pool_status}")
   ```

2. **Slow Queries**
   ```sql
   -- Find slow queries
   SELECT query, total_exec_time, calls, mean_exec_time 
   FROM pg_stat_statements 
   ORDER BY total_exec_time DESC LIMIT 10;
   ```

3. **Lock Contention**
   ```sql
   -- Check for blocking queries
   SELECT blocked_locks.pid AS blocked_pid,
          blocking_locks.pid AS blocking_pid,
          blocked_activity.query as blocked_query
   FROM pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_locks blocking_locks ON ...;
   ```

### Health Checks

```python
from database.database import DatabaseHealthCheck

# Comprehensive health check
health = DatabaseHealthCheck.check_database_health()
if health['status'] == 'healthy':
    print("Database is healthy")
else:
    print(f"Database issues: {health['message']}")

# Performance statistics
stats = DatabaseHealthCheck.get_database_stats()
```

## Development Workflow

### Local Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up postgres

# Run tests
pytest tests/database/

# Load test data
python scripts/load_test_data.py
```

### Code Quality

```python
# Model validation example
from database.models import Document

# Validate business rules
document = Document(filename="test.pdf")
if not document.filename.endswith('.pdf'):
    raise ValueError("Invalid file type")

# Test database operations
def test_document_creation():
    with get_db_session() as session:
        doc = Document.create(session, **test_data)
        assert doc.id is not None
        assert doc.status == ProcessingStatus.UPLOADED
```

## Production Deployment

### Prerequisites

- PostgreSQL 15+
- Python 3.9+
- Docker and Docker Compose
- Sufficient RAM (4GB+ recommended)
- SSD storage for optimal performance

### Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Resource limits set
- [ ] Performance baseline established

---

## Contributing

When contributing to the database system:

1. Create migrations for schema changes
2. Update model classes accordingly
3. Add appropriate indexes and constraints
4. Include tests for new functionality
5. Update documentation

## License

This database system is part of the MDUS project. See LICENSE file for details.

---

For questions or issues, please refer to the project documentation or create an issue in the project repository.