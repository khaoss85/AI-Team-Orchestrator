-- Complete fix for all conversation-related RLS policies
-- Run this in your Supabase SQL Editor

-- ============================================
-- 1. FIX CONVERSATIONS TABLE
-- ============================================

-- Drop existing policies for conversations
DROP POLICY IF EXISTS "conversations_policy" ON conversations;
DROP POLICY IF EXISTS "Enable read for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON conversations;
DROP POLICY IF EXISTS "Enable delete for authenticated users" ON conversations;

-- Create permissive policies for conversations
CREATE POLICY "Allow all operations for authenticated users on conversations" 
ON conversations 
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow all operations for anonymous users on conversations" 
ON conversations 
FOR ALL 
TO anon 
USING (true) 
WITH CHECK (true);

-- Enable RLS on conversations
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 2. FIX CONVERSATION_MESSAGES TABLE
-- ============================================

-- Drop existing policies for conversation_messages
DROP POLICY IF EXISTS "conversation_messages_policy" ON conversation_messages;
DROP POLICY IF EXISTS "Enable read for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON conversation_messages;
DROP POLICY IF EXISTS "Enable delete for authenticated users" ON conversation_messages;

-- Create permissive policies for conversation_messages
CREATE POLICY "Allow all operations for authenticated users on conversation_messages" 
ON conversation_messages 
FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow all operations for anonymous users on conversation_messages" 
ON conversation_messages 
FOR ALL 
TO anon 
USING (true) 
WITH CHECK (true);

-- Enable RLS on conversation_messages
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 3. VERIFICATION
-- ============================================

-- Check all policies are in place
SELECT 
  schemaname, 
  tablename, 
  policyname, 
  permissive, 
  roles, 
  cmd 
FROM pg_policies 
WHERE tablename IN ('conversations', 'conversation_messages')
ORDER BY tablename, policyname;

-- Return success message
SELECT 'RLS policies fixed for ALL conversation tables' as status;