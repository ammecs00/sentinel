-- Initial database setup
-- This file is automatically executed when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions (tables will be created by Alembic migrations)
-- GRANT ALL PRIVILEGES ON DATABASE sentinel_db TO sentinel_user;