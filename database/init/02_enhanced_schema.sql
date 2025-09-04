-- Enhanced MDUS Database Schema for Production-Ready System
-- This schema extends the basic schema with advanced features for medical document processing

-- Create additional extensions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- Text similarity
CREATE EXTENSION IF NOT EXISTS "btree_gin";   -- Better indexing for JSON/arrays
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance tracking

-- Enhanced document types enumeration
CREATE TYPE document_type_enum AS ENUM (
    'medical_report',
    'laboratory_result', 
    'prescription',
    'insurance_claim',
    'patient_form',
    'discharge_summary',
    'pathology_report',
    'radiology_report',
    'invoice',
    'contract',
    'form',
    'receipt',
    'statement',
    'other'
);

-- Processing status enumeration
CREATE TYPE processing_status_enum AS ENUM (
    'uploaded',
    'queued',
    'processing',
    'completed',
    'failed',
    'archived'
);

-- Analysis type enumeration  
CREATE TYPE analysis_type_enum AS ENUM (
    'ocr_extraction',
    'layout_analysis',
    'entity_recognition', 
    'classification',
    'key_value_extraction',
    'table_extraction',
    'signature_detection',
    'quality_assessment'
);

-- Enhanced documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_type document_type_enum DEFAULT 'other',
ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS language_code VARCHAR(10) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS quality_score DECIMAL(5,4),
ADD COLUMN IF NOT EXISTS is_sensitive BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS retention_date DATE,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS checksum VARCHAR(64),
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE;

-- Update status column to use enum
ALTER TABLE documents ALTER COLUMN status TYPE processing_status_enum USING status::processing_status_enum;

-- Create document_versions table for version control
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    changes_description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, version_number)
);

-- Enhanced document_analysis table
ALTER TABLE document_analysis 
ADD COLUMN IF NOT EXISTS model_version VARCHAR(50),
ADD COLUMN IF NOT EXISTS accuracy_metrics JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS validated_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS validation_notes TEXT;

-- Update analysis_type and status columns to use enums
ALTER TABLE document_analysis 
ALTER COLUMN analysis_type TYPE analysis_type_enum USING analysis_type::analysis_type_enum,
ALTER COLUMN status TYPE processing_status_enum USING status::processing_status_enum;

-- Create extracted_entities table for structured entity storage
CREATE TABLE IF NOT EXISTS extracted_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES document_analysis(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    entity_value TEXT NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    bounding_box JSONB, -- {x, y, width, height}
    page_number INTEGER DEFAULT 1,
    context_text TEXT,
    validation_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_relationships table
CREATE TABLE IF NOT EXISTS document_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    target_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'related', 'duplicate', 'amendment', 'followup'
    confidence_score DECIMAL(5,4),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_document_id, target_document_id, relationship_type)
);

-- Create audit_logs table for compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create model_configurations table
CREATE TABLE IF NOT EXISTS model_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    performance_metrics JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create processing_metrics table for monitoring
CREATE TABLE IF NOT EXISTS processing_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(50),
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create quality_checks table
CREATE TABLE IF NOT EXISTS quality_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    check_type VARCHAR(100) NOT NULL,
    check_result VARCHAR(50) NOT NULL, -- 'pass', 'fail', 'warning'
    score DECIMAL(5,4),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_quality_score ON documents(quality_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN(metadata);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_checksum ON documents(checksum);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_model_name ON document_analysis(model_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_created_at ON document_analysis(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_structured_data_gin ON document_analysis USING GIN(structured_data);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_validation_status ON document_analysis(validation_status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_entities_entity_type ON extracted_entities(entity_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_entities_analysis_id ON extracted_entities(analysis_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_extracted_entities_confidence ON extracted_entities(confidence_score);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processing_jobs_priority ON processing_jobs(priority);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processing_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processing_jobs_retry_count ON processing_jobs(retry_count);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_filename_gin ON documents USING GIN(to_tsvector('english', filename));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_text_gin ON document_analysis USING GIN(to_tsvector('english', extracted_text));

-- Apply triggers to new tables
CREATE TRIGGER update_document_versions_updated_at BEFORE UPDATE ON document_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_configurations_updated_at BEFORE UPDATE ON model_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_values, new_values, created_at)
    VALUES (
        current_setting('app.current_user_id', true)::UUID,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW) ELSE NULL END,
        NOW()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_documents_trigger
    AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_document_analysis_trigger
    AFTER INSERT OR UPDATE OR DELETE ON document_analysis
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Create views for common queries
CREATE OR REPLACE VIEW document_summary AS
SELECT 
    d.id,
    d.filename,
    d.document_type,
    d.status,
    d.quality_score,
    d.created_at,
    u.full_name as uploaded_by,
    COUNT(da.id) as analysis_count,
    MAX(da.created_at) as last_analyzed,
    AVG(da.confidence_scores->>'overall') as avg_confidence
FROM documents d
LEFT JOIN users u ON d.user_id = u.id
LEFT JOIN document_analysis da ON d.id = da.document_id
GROUP BY d.id, d.filename, d.document_type, d.status, d.quality_score, d.created_at, u.full_name;

CREATE OR REPLACE VIEW processing_status_summary AS
SELECT 
    status,
    COUNT(*) as document_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(completed_at, NOW()) - created_at))) as avg_processing_time_seconds
FROM processing_jobs 
GROUP BY status;

-- Insert default model configurations
INSERT INTO model_configurations (model_name, model_version, model_type, configuration, performance_metrics) VALUES
    ('layoutlmv3', '1.0.0', 'layout_analysis', '{"max_sequence_length": 512, "image_size": [224, 224]}', '{"accuracy": 0.985, "f1_score": 0.978}'),
    ('donut', '1.0.0', 'ocr_free', '{"max_length": 1024, "ignore_id": -100}', '{"accuracy": 0.972, "bleu_score": 0.891}'),
    ('bert_large', '1.0.0', 'ner', '{"max_length": 512, "num_labels": 20}', '{"precision": 0.954, "recall": 0.948, "f1_score": 0.951}')
ON CONFLICT (model_name) DO NOTHING;

-- Create functions for data analysis
CREATE OR REPLACE FUNCTION get_document_processing_stats(days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    total_documents BIGINT,
    processed_documents BIGINT,
    avg_processing_time_seconds NUMERIC,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_documents,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::BIGINT as processed_documents,
        AVG(EXTRACT(EPOCH FROM (processed_at - created_at)))::NUMERIC as avg_processing_time_seconds,
        (COUNT(CASE WHEN status = 'completed' THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100)::NUMERIC as success_rate
    FROM documents 
    WHERE created_at >= NOW() - INTERVAL '1 day' * days_back;
END;
$$ LANGUAGE plpgsql;

-- Create function for entity extraction summary
CREATE OR REPLACE FUNCTION get_entity_extraction_summary(document_uuid UUID)
RETURNS TABLE(
    entity_type VARCHAR,
    entity_count BIGINT,
    avg_confidence NUMERIC,
    high_confidence_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ee.entity_type,
        COUNT(*)::BIGINT as entity_count,
        AVG(ee.confidence_score)::NUMERIC as avg_confidence,
        COUNT(CASE WHEN ee.confidence_score >= 0.90 THEN 1 END)::BIGINT as high_confidence_count
    FROM extracted_entities ee
    JOIN document_analysis da ON ee.analysis_id = da.id
    WHERE da.document_id = document_uuid
    GROUP BY ee.entity_type
    ORDER BY entity_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO mdus_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mdus_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mdus_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mdus_user;