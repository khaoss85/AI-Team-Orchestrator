-- Fix RLS policies for testing
-- Run this in Supabase SQL editor to allow backend testing

-- Temporarily disable RLS for testing (BE CAREFUL IN PRODUCTION!)
ALTER TABLE workspace_goals DISABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_insights DISABLE ROW LEVEL SECURITY;

-- Alternative: Create permissive policies for service role
-- DROP POLICY IF EXISTS "Service role can do everything on workspace_goals" ON workspace_goals;
-- CREATE POLICY "Service role can do everything on workspace_goals" ON workspace_goals
--     FOR ALL 
--     TO service_role
--     USING (true)
--     WITH CHECK (true);

-- DROP POLICY IF EXISTS "Service role can do everything on workspace_insights" ON workspace_insights;
-- CREATE POLICY "Service role can do everything on workspace_insights" ON workspace_insights
--     FOR ALL
--     TO service_role
--     USING (true)
--     WITH CHECK (true);

-- Check current RLS status
SELECT 
    tablename,
    rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('workspace_goals', 'workspace_insights');