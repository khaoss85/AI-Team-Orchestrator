-- =============================================
-- DATABASE COMPATIBILITY FIX
-- Aligns existing database structure with conversational AI code
-- =============================================

-- 1. Add missing columns to pending_confirmations to match code expectations
ALTER TABLE pending_confirmations ADD COLUMN IF NOT EXISTS action_id TEXT;

-- Update action_id to match the existing id if it's null
UPDATE pending_confirmations 
SET action_id = id::text 
WHERE action_id IS NULL;

-- 2. Ensure conversation_messages references conversations correctly
-- The code expects conversation_id as TEXT (workspace_id_chat_id format)
-- but the table has UUID reference. We'll add a computed column.

-- Add conversation_identifier column for text-based lookups
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS conversation_identifier TEXT;

-- Create a function to generate conversation identifiers
CREATE OR REPLACE FUNCTION generate_conversation_identifier(workspace_uuid UUID, chat_id_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN workspace_uuid::text || '_' || chat_id_text;
END;
$$ LANGUAGE plpgsql;

-- Update existing conversation_messages to have conversation_identifier
UPDATE conversation_messages 
SET conversation_identifier = generate_conversation_identifier(
    (SELECT workspace_id FROM conversations WHERE conversations.id = conversation_messages.conversation_id),
    (SELECT chat_id FROM conversations WHERE conversations.id = conversation_messages.conversation_id)
)
WHERE conversation_identifier IS NULL;

-- 3. Update pending_confirmations to use conversation_identifier
ALTER TABLE pending_confirmations ADD COLUMN IF NOT EXISTS conversation_identifier TEXT;

UPDATE pending_confirmations 
SET conversation_identifier = generate_conversation_identifier(
    (SELECT workspace_id FROM conversations WHERE conversations.id = pending_confirmations.conversation_id),
    (SELECT chat_id FROM conversations WHERE conversations.id = pending_confirmations.conversation_id)
)
WHERE conversation_identifier IS NULL;

-- 4. Create indexes for the new identifier columns
CREATE INDEX IF NOT EXISTS idx_conversation_messages_identifier ON conversation_messages(conversation_identifier);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_identifier ON pending_confirmations(conversation_identifier);

-- 5. Create a view that matches the expected structure for conversations
CREATE OR REPLACE VIEW conversations_compatible AS
SELECT 
    workspace_id,
    chat_id,
    workspace_id::text || '_' || chat_id as conversation_id,
    schema_version,
    title,
    description,
    active_messages,
    archived_summaries,
    conversational_features,
    context_snapshot as metadata,
    last_summarization,
    created_at,
    updated_at
FROM conversations;

-- 6. Create helper functions for the conversational AI system

-- Function to find or create conversation
CREATE OR REPLACE FUNCTION find_or_create_conversation(
    p_workspace_id UUID,
    p_chat_id TEXT,
    p_title TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    conversation_uuid UUID;
BEGIN
    -- Try to find existing conversation
    SELECT id INTO conversation_uuid
    FROM conversations
    WHERE workspace_id = p_workspace_id AND chat_id = p_chat_id;
    
    -- If not found, create it
    IF conversation_uuid IS NULL THEN
        INSERT INTO conversations (workspace_id, chat_id, title, description, schema_version)
        VALUES (p_workspace_id, p_chat_id, 
                COALESCE(p_title, 'Conversation: ' || p_chat_id),
                COALESCE(p_description, 'AI assistant conversation for ' || p_chat_id),
                'v2025-06-A')
        RETURNING id INTO conversation_uuid;
    END IF;
    
    RETURN conversation_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to get conversation by identifier
CREATE OR REPLACE FUNCTION get_conversation_by_identifier(conversation_identifier TEXT)
RETURNS TABLE (
    id UUID,
    workspace_id UUID,
    chat_id TEXT,
    schema_version TEXT,
    title TEXT,
    description TEXT,
    active_messages JSONB[],
    archived_summaries JSONB[],
    conversational_features JSONB,
    metadata JSONB,
    last_summarization TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    parts TEXT[];
    ws_id UUID;
    c_id TEXT;
BEGIN
    -- Split the identifier
    parts := string_to_array(conversation_identifier, '_');
    
    IF array_length(parts, 1) >= 2 THEN
        ws_id := parts[1]::UUID;
        c_id := array_to_string(parts[2:], '_'); -- Rejoin in case chat_id contains underscores
        
        RETURN QUERY
        SELECT 
            c.id,
            c.workspace_id,
            c.chat_id,
            c.schema_version,
            c.title,
            c.description,
            c.active_messages,
            c.archived_summaries,
            c.conversational_features,
            c.context_snapshot,
            c.last_summarization,
            c.created_at,
            c.updated_at
        FROM conversations c
        WHERE c.workspace_id = ws_id AND c.chat_id = c_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 7. Update RLS policies to work with the new structure
-- (Policies should already work, but let's ensure compatibility)

-- 8. Create a compatibility layer for the conversational AI code
CREATE OR REPLACE VIEW conversation_messages_compatible AS
SELECT 
    cm.id,
    cm.conversation_identifier as conversation_id,
    cm.message_id,
    cm.role,
    cm.content,
    cm.content_type,
    cm.tools_used,
    cm.actions_performed,
    cm.artifacts_generated,
    cm.context_snapshot,
    cm.metadata,
    cm.created_at
FROM conversation_messages cm;

CREATE OR REPLACE VIEW pending_confirmations_compatible AS
SELECT 
    pc.action_id,
    pc.conversation_identifier as conversation_id,
    pc.message_id,
    pc.action_type,
    pc.action_description,
    pc.parameters,
    pc.risk_level,
    pc.status,
    pc.expires_at,
    pc.confirmed_at,
    pc.metadata,
    pc.created_at
FROM pending_confirmations pc;

-- 9. Grant permissions on new functions and views
GRANT EXECUTE ON FUNCTION find_or_create_conversation(UUID, TEXT, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_conversation_by_identifier(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION generate_conversation_identifier(UUID, TEXT) TO authenticated;

GRANT SELECT ON conversations_compatible TO authenticated;
GRANT SELECT ON conversation_messages_compatible TO authenticated;
GRANT SELECT ON pending_confirmations_compatible TO authenticated;

-- Success message
SELECT 'Database compatibility fix applied successfully! Conversational AI code should now work with existing database structure.' as status;