-- Migration: Add secrets_config column to settings table
-- Date: 2025-08-18
-- Description: Add missing secrets_config JSON column that was added to the Setting model

-- Check if column exists before adding it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'settings' 
        AND column_name = 'secrets_config'
    ) THEN
        ALTER TABLE settings ADD COLUMN secrets_config JSON;
        RAISE NOTICE 'Added secrets_config column to settings table';
    ELSE
        RAISE NOTICE 'secrets_config column already exists';
    END IF;
END $$;