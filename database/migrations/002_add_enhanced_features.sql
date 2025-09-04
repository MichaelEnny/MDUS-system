-- Migration: 002_add_enhanced_features.sql
-- Description: Add enhanced features for production-ready system
-- Created: 2025-09-04
-- Author: MDUS Team

BEGIN;

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

-- Create extracted_entities table
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
    relationship_type VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,4),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_document_id, target_document_id, relationship_type)
);

-- Create audit_logs table
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

-- Create processing_metrics table
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
    check_result VARCHAR(50) NOT NULL,
    score DECIMAL(5,4),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create enhanced indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_quality_score ON documents(quality_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN(metadata);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_checksum ON documents(checksum);

-- Apply triggers to new tables
CREATE TRIGGER update_document_versions_updated_at BEFORE UPDATE ON document_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_configurations_updated_at BEFORE UPDATE ON model_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert migration record
INSERT INTO schema_migrations (version) VALUES ('002_add_enhanced_features');

COMMIT;