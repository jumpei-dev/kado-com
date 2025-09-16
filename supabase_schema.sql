-- Supabase Database Schema Definition
-- Generated for kado-com project

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and authorization
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    can_see_contents BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Businesses table for store information
CREATE TABLE IF NOT EXISTS businesses (
    business_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    area VARCHAR(100) NOT NULL,
    prefecture VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    open_hour TIME NOT NULL,
    close_hour TIME NOT NULL,
    schedule_url TEXT NOT NULL,
    in_scope BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Casts table for cast information
CREATE TABLE IF NOT EXISTS casts (
    cast_id VARCHAR(50) PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    profile_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status table for current cast status
CREATE TABLE IF NOT EXISTS status (
    id SERIAL PRIMARY KEY,
    cast_id VARCHAR(50) NOT NULL REFERENCES casts(cast_id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    is_working BOOLEAN NOT NULL,
    is_on_shift BOOLEAN NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cast_id, recorded_at)
);

-- Status history table for working rate calculations
CREATE TABLE IF NOT EXISTS status_history (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    biz_date DATE NOT NULL,
    working_rate DECIMAL(5,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, biz_date)
);

-- Batch job results table for monitoring
CREATE TABLE IF NOT EXISTS batch_job_results (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    success BOOLEAN DEFAULT FALSE,
    processed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    errors TEXT[],
    duration_seconds DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_casts_business_id ON casts(business_id);
CREATE INDEX IF NOT EXISTS idx_status_cast_id ON status(cast_id);
CREATE INDEX IF NOT EXISTS idx_status_business_id ON status(business_id);
CREATE INDEX IF NOT EXISTS idx_status_recorded_at ON status(recorded_at);
CREATE INDEX IF NOT EXISTS idx_status_history_business_id ON status_history(business_id);
CREATE INDEX IF NOT EXISTS idx_status_history_biz_date ON status_history(biz_date);
CREATE INDEX IF NOT EXISTS idx_batch_job_results_job_name ON batch_job_results(job_name);
CREATE INDEX IF NOT EXISTS idx_batch_job_results_started_at ON batch_job_results(started_at);

-- Additional indexes for store list performance
CREATE INDEX IF NOT EXISTS idx_businesses_area_type ON businesses(area, type);
CREATE INDEX IF NOT EXISTS idx_businesses_in_scope ON businesses(in_scope) WHERE in_scope = true;
CREATE INDEX IF NOT EXISTS idx_status_history_biz_date_business_id ON status_history(biz_date, business_id);
CREATE INDEX IF NOT EXISTS idx_status_business_recorded ON status(business_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_casts_business_active ON casts(business_id, is_active) WHERE is_active = true;

-- RLS (Row Level Security) policies can be added here if needed
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE casts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE status ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE status_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE batch_job_results ENABLE ROW LEVEL SECURITY;

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_casts_updated_at BEFORE UPDATE ON casts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_status_history_updated_at BEFORE UPDATE ON status_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE users IS 'User authentication and authorization table';
COMMENT ON TABLE businesses IS 'Store/business information table';
COMMENT ON TABLE casts IS 'Cast member information table';
COMMENT ON TABLE status IS 'Current status records for casts';
COMMENT ON TABLE status_history IS 'Historical working rate data by business and date';
COMMENT ON TABLE batch_job_results IS 'Batch job execution results and monitoring';

COMMENT ON COLUMN users.can_see_contents IS 'Permission to view sensitive content';
COMMENT ON COLUMN businesses.in_scope IS 'Whether this business is included in processing';
COMMENT ON COLUMN casts.is_active IS 'Whether this cast is currently active';
COMMENT ON COLUMN status.is_working IS 'Whether the cast is currently working';
COMMENT ON COLUMN status.is_on_shift IS 'Whether the cast is on shift';
COMMENT ON COLUMN status_history.working_rate IS 'Calculated working rate (0.0000 to 1.0000)';