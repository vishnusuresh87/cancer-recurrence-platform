-- scripts/init_db.sql
-- This runs automatically when PostgreSQL container starts

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'patient',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- User profiles
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    date_of_birth DATE,
    cancer_type VARCHAR(100),
    diagnosis_date DATE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Prediction history
CREATE TABLE prediction_history (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    feature_vector JSONB,
    probability FLOAT,
    risk_level VARCHAR(20),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Model versions
CREATE TABLE model_versions (
    version VARCHAR(50) PRIMARY KEY,
    gcs_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'staging',
    metrics JSONB,
    training_date TIMESTAMP,
    training_samples INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OAuth tokens
CREATE TABLE oauth_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    provider VARCHAR(50),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_prediction_history_user_created ON prediction_history(user_id, created_at DESC);
CREATE INDEX idx_model_versions_status ON model_versions(status);