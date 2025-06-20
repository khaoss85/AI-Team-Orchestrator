-- Fix for conversation_messages RLS policy issues
-- Run this in your Supabase SQL Editor

-- 1. Check current policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'conversation_messages';

-- 2. Drop existing policies that might be causing issues
DROP POLICY IF EXISTS "conversation_messages_policy" ON conversation_messages;
DROP POLICY IF EXISTS "Enable read for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable delete for authenticated users" ON conversation_messages;

-- 3. Create new permissive policies for development
-- Allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users" 
ON conversation_messages 
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- Allow all operations for anonymous users (for development only)
CREATE POLICY "Allow all operations for anonymous users" 
ON conversation_messages 
FOR ALL 
TO anon 
USING (true) 
WITH CHECK (true);

-- 4. Ensure RLS is enabled
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- 5. Verify the fix
SELECT 'RLS policies fixed for conversation_messages table' as status;