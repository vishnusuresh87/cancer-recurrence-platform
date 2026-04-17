-- Run this to create the model_versions table
-- psql -h localhost -p 55432 -U cancer_user -d cancer_db -f scripts/create_model_versions_table.sql

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model_status') THEN
        CREATE TYPE model_status AS ENUM ('staging', 'production', 'archived', 'failed');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS model_versions (
    version VARCHAR(50) PRIMARY KEY,
    storage_path VARCHAR(500) NOT NULL,
    status model_status DEFAULT 'staging' NOT NULL,
    metrics JSONB,
    training_date TIMESTAMP,
    training_samples INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    promoted_at TIMESTAMP,
    archived_at TIMESTAMP
);

-- Migrate legacy schema: rename gcs_path -> storage_path if needed.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'model_versions' AND column_name = 'gcs_path'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'model_versions' AND column_name = 'storage_path'
    ) THEN
        ALTER TABLE model_versions RENAME COLUMN gcs_path TO storage_path;
    END IF;
END $$;

ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500);
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS promoted_at TIMESTAMP;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;

-- Convert legacy varchar status column to model_status enum when needed.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'model_versions'
          AND column_name = 'status'
          AND udt_name IN ('varchar', 'text')
    ) THEN
        ALTER TABLE model_versions
            ALTER COLUMN status DROP DEFAULT;

        ALTER TABLE model_versions
            ALTER COLUMN status TYPE model_status
            USING status::model_status;
    END IF;
END $$;

UPDATE model_versions
SET status = 'staging'
WHERE status IS NULL;

ALTER TABLE model_versions
    ALTER COLUMN status SET DEFAULT 'staging';

ALTER TABLE model_versions
    ALTER COLUMN status SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_model_status ON model_versions(status);
CREATE INDEX IF NOT EXISTS idx_model_created ON model_versions(created_at DESC);

-- Insert current model
INSERT INTO model_versions (
    version,
    storage_path,
    status,
    metrics,
    training_date,
    training_samples
) VALUES (
    'rsf_seer_v1.0.0',
    '../../ml-pipeline/models/rsf_seer_v1.pkl',
    'production',
    '{"c_index_train": 0.7823, "c_index_test": 0.7654}'::jsonb,
    NOW(),
    160000
) ON CONFLICT (version) DO NOTHING;

