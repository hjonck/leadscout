-- LeadScout Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Description: Create core tables for name classifications, CIPC data, and lead enrichment cache

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Name classifications table (shared with Developer B)
-- This table stores all name ethnicity classifications from multiple sources
CREATE TABLE name_classifications (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phonetic_key TEXT NOT NULL,  -- Metaphone/Soundex key for similarity matching
    ethnicity VARCHAR(20) NOT NULL CHECK (ethnicity IN ('african', 'indian', 'coloured', 'white', 'mixed', 'unknown')),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    method VARCHAR(20) NOT NULL CHECK (method IN ('rule_based', 'phonetic', 'llm', 'manual')),
    sources TEXT[], -- JSON array of source systems that contributed to classification
    embedding VECTOR(1536), -- OpenAI text-embedding-3-small dimensions for similarity search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Allow multiple ethnicities per name with different confidences
    UNIQUE(name, ethnicity)
);

-- CIPC company registry data
-- Stores South African company registration information from monthly CSV downloads
CREATE TABLE cipc_companies (
    id SERIAL PRIMARY KEY,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    company_type VARCHAR(50),
    company_status VARCHAR(20),
    extracted_names TEXT[], -- JSON array of personal names extracted from company name
    province VARCHAR(50), -- Inferred from address patterns
    industry_keywords TEXT[], -- Keywords for industry classification
    download_batch DATE NOT NULL, -- Which monthly batch this data came from
    file_source VARCHAR(10) NOT NULL, -- Which letter file (A-Z) this came from
    name_slug TEXT NOT NULL, -- Normalized name for fuzzy matching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lead enrichment cache
-- Stores cached enrichment results for processed leads
CREATE TABLE lead_enrichments (
    id SERIAL PRIMARY KEY,
    lead_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 hash of original lead data
    original_data JSONB NOT NULL, -- Original lead data for reference
    enrichment_data JSONB NOT NULL, -- All enrichment results
    processing_status VARCHAR(20) DEFAULT 'completed' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT, -- Error details if processing failed
    processing_time_ms INTEGER, -- Total processing time in milliseconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE -- TTL for cache expiration
);

-- Cache statistics tracking
-- Tracks cache performance metrics and usage patterns
CREATE TABLE cache_statistics (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('hit', 'miss', 'write', 'delete')),
    count INTEGER DEFAULT 1,
    response_time_ms INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes for name classifications
CREATE INDEX idx_name_classifications_name ON name_classifications(name);
CREATE INDEX idx_name_classifications_phonetic ON name_classifications(phonetic_key);
CREATE INDEX idx_name_classifications_ethnicity ON name_classifications(ethnicity);
CREATE INDEX idx_name_classifications_method ON name_classifications(method);
CREATE INDEX idx_name_classifications_confidence ON name_classifications(confidence DESC);
-- GIN index for array operations on sources
CREATE INDEX idx_name_classifications_sources ON name_classifications USING GIN(sources);
-- Index for similarity search using pg_trgm
CREATE INDEX idx_name_classifications_name_trgm ON name_classifications USING GIN(name gin_trgm_ops);

-- Performance indexes for CIPC companies
CREATE INDEX idx_cipc_companies_registration ON cipc_companies(registration_number);
CREATE INDEX idx_cipc_companies_name ON cipc_companies(company_name);
CREATE INDEX idx_cipc_companies_slug ON cipc_companies(name_slug);
CREATE INDEX idx_cipc_companies_type ON cipc_companies(company_type);
CREATE INDEX idx_cipc_companies_status ON cipc_companies(company_status);
CREATE INDEX idx_cipc_companies_batch ON cipc_companies(download_batch);
CREATE INDEX idx_cipc_companies_province ON cipc_companies(province);
-- Full-text search index for company names
CREATE INDEX idx_cipc_companies_name_fts ON cipc_companies USING GIN(to_tsvector('english', company_name));
-- GIN index for extracted names array
CREATE INDEX idx_cipc_companies_extracted_names ON cipc_companies USING GIN(extracted_names);
-- Trigram index for fuzzy matching
CREATE INDEX idx_cipc_companies_name_trgm ON cipc_companies USING GIN(company_name gin_trgm_ops);

-- Performance indexes for lead enrichments
CREATE INDEX idx_lead_enrichments_hash ON lead_enrichments(lead_hash);
CREATE INDEX idx_lead_enrichments_status ON lead_enrichments(processing_status);
CREATE INDEX idx_lead_enrichments_created ON lead_enrichments(created_at);
CREATE INDEX idx_lead_enrichments_expires ON lead_enrichments(expires_at);
-- GIN indexes for JSONB data
CREATE INDEX idx_lead_enrichments_original_data ON lead_enrichments USING GIN(original_data);
CREATE INDEX idx_lead_enrichments_enrichment_data ON lead_enrichments USING GIN(enrichment_data);

-- Performance indexes for cache statistics
CREATE INDEX idx_cache_statistics_table ON cache_statistics(table_name);
CREATE INDEX idx_cache_statistics_operation ON cache_statistics(operation_type);
CREATE INDEX idx_cache_statistics_recorded ON cache_statistics(recorded_at);

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_name_classifications_updated_at 
    BEFORE UPDATE ON name_classifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cipc_companies_updated_at 
    BEFORE UPDATE ON cipc_companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lead_enrichments_updated_at 
    BEFORE UPDATE ON lead_enrichments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- View for active companies only
CREATE VIEW active_cipc_companies AS
SELECT *
FROM cipc_companies 
WHERE company_status IN ('Active', 'In Business');

-- View for recent name classifications with high confidence
CREATE VIEW reliable_name_classifications AS
SELECT *
FROM name_classifications 
WHERE confidence >= 0.8 
  AND created_at >= NOW() - INTERVAL '1 year';

-- View for cache performance summary
CREATE VIEW cache_performance_summary AS
SELECT 
    table_name,
    operation_type,
    COUNT(*) as total_operations,
    AVG(response_time_ms) as avg_response_time_ms,
    MAX(recorded_at) as last_recorded
FROM cache_statistics 
WHERE recorded_at >= NOW() - INTERVAL '24 hours'
GROUP BY table_name, operation_type
ORDER BY table_name, operation_type;

-- Function to calculate cache hit rate
CREATE OR REPLACE FUNCTION get_cache_hit_rate(
    p_table_name VARCHAR(50), 
    p_hours INTEGER DEFAULT 24
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    hit_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO hit_count
    FROM cache_statistics 
    WHERE table_name = p_table_name 
      AND operation_type = 'hit'
      AND recorded_at >= NOW() - INTERVAL '1 hour' * p_hours;
    
    SELECT COUNT(*) INTO total_count
    FROM cache_statistics 
    WHERE table_name = p_table_name 
      AND operation_type IN ('hit', 'miss')
      AND recorded_at >= NOW() - INTERVAL '1 hour' * p_hours;
    
    IF total_count = 0 THEN
        RETURN 0.00;
    END IF;
    
    RETURN ROUND((hit_count::DECIMAL / total_count::DECIMAL) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM lead_enrichments 
    WHERE expires_at IS NOT NULL 
      AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup operation
    INSERT INTO cache_statistics (table_name, operation_type, count)
    VALUES ('lead_enrichments', 'delete', deleted_count);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cache cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-cache', '0 2 * * *', 'SELECT cleanup_expired_cache();');

COMMENT ON TABLE name_classifications IS 'Stores ethnicity classifications for names using multiple methods (rule-based, phonetic, LLM)';
COMMENT ON TABLE cipc_companies IS 'South African company registry data from CIPC monthly CSV downloads';
COMMENT ON TABLE lead_enrichments IS 'Cached enrichment results for processed leads with TTL support';
COMMENT ON TABLE cache_statistics IS 'Performance metrics and usage tracking for cache operations';

COMMENT ON COLUMN name_classifications.embedding IS 'OpenAI text-embedding-3-small vector for similarity search';
COMMENT ON COLUMN cipc_companies.name_slug IS 'Normalized company name for fuzzy matching (lowercase, no special chars)';
COMMENT ON COLUMN lead_enrichments.lead_hash IS 'SHA-256 hash of normalized original lead data for deduplication';