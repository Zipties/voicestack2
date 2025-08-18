-- Migration: Add speaker visibility and identification fields
-- Date: 2025-08-18
-- Description: Add original_speaker_label to segments and original_label/match_confidence to speakers

-- Add original_speaker_label to segments table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'segments' 
        AND column_name = 'original_speaker_label'
    ) THEN
        ALTER TABLE segments ADD COLUMN original_speaker_label VARCHAR;
        RAISE NOTICE 'Added original_speaker_label column to segments table';
    ELSE
        RAISE NOTICE 'original_speaker_label column already exists in segments table';
    END IF;
END $$;

-- Add original_label to speakers table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'speakers' 
        AND column_name = 'original_label'
    ) THEN
        ALTER TABLE speakers ADD COLUMN original_label VARCHAR;
        RAISE NOTICE 'Added original_label column to speakers table';
    ELSE
        RAISE NOTICE 'original_label column already exists in speakers table';
    END IF;
END $$;

-- Add match_confidence to speakers table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'speakers' 
        AND column_name = 'match_confidence'
    ) THEN
        ALTER TABLE speakers ADD COLUMN match_confidence FLOAT;
        RAISE NOTICE 'Added match_confidence column to speakers table';
    ELSE
        RAISE NOTICE 'match_confidence column already exists in speakers table';
    END IF;
END $$;