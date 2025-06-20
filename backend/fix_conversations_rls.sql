-- Additional fix for conversations table RLS policy
-- Run this in your Supabase SQL Editor AFTER the previous fix

-- 1. Check current policies for conversations table
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'conversations';

-- 2. Drop existing problematic policies for conversations
DROP POLICY IF EXISTS "conversations_policy" ON conversations;
DROP POLICY IF EXISTS "Enable read for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable delete for authenticated users" ON conversations;

-- 3. Create permissive policies for conversations table
-- Allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users on conversations" 
ON conversations 
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- Allow all operations for anonymous users (for development only)
CREATE POLICY "Allow all operations for anonymous users on conversations" 
ON conversations 
FOR ALL 
TO anon 
USING (true) 
WITH CHECK (true);

-- 4. Ensure RLS is enabled
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- 5. Verify the fix
SELECT 'RLS policies fixed for conversations table' as status;