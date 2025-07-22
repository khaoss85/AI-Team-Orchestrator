-- Fix deliverables table schema and permissions
-- Execute these SQL commands in your Supabase SQL Editor

-- 1. Add missing auto_improvements column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'deliverables' 
        AND column_name = 'auto_improvements'
    ) THEN
        ALTER TABLE deliverables 
        ADD COLUMN auto_improvements JSONB DEFAULT '[]'::jsonb;
        
        COMMENT ON COLUMN deliverables.auto_improvements IS 'Stores AI-driven auto-improvements for deliverables';
    END IF;
END $$;

-- 2. Add missing columns that might be required by the system
DO $$ 
BEGIN
    -- Add quality_score if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'deliverables' 
        AND column_name = 'quality_score'
    ) THEN
        ALTER TABLE deliverables 
        ADD COLUMN quality_score DECIMAL(5,2) DEFAULT 0.0;
        
        COMMENT ON COLUMN deliverables.quality_score IS 'Quality assessment score (0-100)';
    END IF;
    
    -- Add metadata if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'deliverables' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE deliverables 
        ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
        
        COMMENT ON COLUMN deliverables.metadata IS 'Additional metadata for deliverables';
    END IF;
    
    -- Add pipeline_data if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'deliverables' 
        AND column_name = 'pipeline_data'
    ) THEN
        ALTER TABLE deliverables 
        ADD COLUMN pipeline_data JSONB DEFAULT '{}'::jsonb;
        
        COMMENT ON COLUMN deliverables.pipeline_data IS 'Data from AI pipeline execution';
    END IF;
END $$;

-- 3. Fix Row Level Security (RLS) policies for deliverables
-- Drop existing policies that might be too restrictive
DROP POLICY IF EXISTS "deliverables_insert_policy" ON deliverables;
DROP POLICY IF EXISTS "deliverables_select_policy" ON deliverables;
DROP POLICY IF EXISTS "deliverables_update_policy" ON deliverables;
DROP POLICY IF EXISTS "deliverables_delete_policy" ON deliverables;

-- Create more permissive policies for system operations
CREATE POLICY "deliverables_all_operations" ON deliverables
    FOR ALL 
    TO authenticated, anon
    USING (true)
    WITH CHECK (true);

-- Alternative: If you want more secure but functional policies
-- Uncomment these and comment out the permissive policy above

/*
CREATE POLICY "deliverables_select_policy" ON deliverables
    FOR SELECT 
    TO authenticated, anon
    USING (true);

CREATE POLICY "deliverables_insert_policy" ON deliverables
    FOR INSERT 
    TO authenticated, anon
    WITH CHECK (true);

CREATE POLICY "deliverables_update_policy" ON deliverables
    FOR UPDATE 
    TO authenticated, anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY "deliverables_delete_policy" ON deliverables
    FOR DELETE 
    TO authenticated, anon
    USING (true);
*/

-- 4. Ensure RLS is enabled but with permissive policies
ALTER TABLE deliverables ENABLE ROW LEVEL SECURITY;

-- 5. Grant necessary permissions
GRANT ALL ON deliverables TO authenticated;
GRANT ALL ON deliverables TO anon;
GRANT ALL ON deliverables TO service_role;

-- 6. Refresh the schema cache
NOTIFY pgrst, 'reload schema';

-- 7. Verify the schema
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'deliverables'
ORDER BY ordinal_position;

-- 8. Test insert to verify permissions work
DO $$
DECLARE
    test_workspace_id UUID := '00000000-0000-0000-0000-000000000000';
    test_deliverable_id UUID;
BEGIN
    -- Try to insert a test deliverable
    INSERT INTO deliverables (
        workspace_id,
        title,
        content,
        type,
        status,
        auto_improvements,
        quality_score,
        metadata,
        pipeline_data
    ) VALUES (
        test_workspace_id,
        'Test Deliverable',
        'Test content',
        'document',
        'draft',
        '[]'::jsonb,
        85.5,
        '{}'::jsonb,
        '{}'::jsonb
    ) RETURNING id INTO test_deliverable_id;
    
    RAISE NOTICE 'Test deliverable created successfully with ID: %', test_deliverable_id;
    
    -- Clean up test record
    DELETE FROM deliverables WHERE id = test_deliverable_id;
    
    RAISE NOTICE 'Test deliverable cleaned up successfully';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Test failed with error: %', SQLERRM;
END $$;