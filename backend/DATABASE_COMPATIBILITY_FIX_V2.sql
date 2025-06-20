-- =============================================
-- DATABASE COMPATIBILITY FIX V2
-- Fixed version that handles existing UUID columns
-- =============================================

-- 1. Check and handle action_id column in pending_confirmations
-- The existing column is UUID, but our code expects TEXT
-- We'll add a new text column for compatibility

-- Add text-based action_id for conversational AI compatibility
ALTER TABLE pending_confirmations ADD COLUMN IF NOT EXISTS action_id_text TEXT;

-- Populate the text version from existing UUID if empty
UPDATE pending_confirmations 
SET action_id_text = action_id::text 
WHERE action_id_text IS NULL AND action_id IS NOT NULL;

-- For new records, we'll use the UUID column as is and convert when needed

-- 2. Add conversation_identifier to conversation_messages
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS conversation_identifier TEXT;

-- Create function to generate conversation identifiers (if not exists)
CREATE OR REPLACE FUNCTION generate_conversation_identifier(workspace_uuid UUID, chat_id_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN workspace_uuid::text || '_' || chat_id_text;
END;
$$ LANGUAGE plpgsql;

-- Update conversation_identifier for existing messages
UPDATE conversation_messages 
SET conversation_identifier = generate_conversation_identifier(
    (SELECT workspace_id FROM conversations WHERE conversations.id = conversation_messages.conversation_id),
    (SELECT chat_id FROM conversations WHERE conversations.id = conversation_messages.conversation_id)
)
WHERE conversation_identifier IS NULL;

-- 3. Add conversation_identifier to pending_confirmations
ALTER TABLE pending_confirmations ADD COLUMN IF NOT EXISTS conversation_identifier TEXT;

-- Update conversation_identifier for existing confirmations
UPDATE pending_confirmations 
SET conversation_identifier = generate_conversation_identifier(
    (SELECT workspace_id FROM conversations WHERE conversations.id = pending_confirmations.conversation_id),
    (SELECT chat_id FROM conversations WHERE conversations.id = pending_confirmations.conversation_id)
)
WHERE conversation_identifier IS NULL AND conversation_id IS NOT NULL;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_messages_identifier ON conversation_messages(conversation_identifier);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_identifier ON pending_confirmations(conversation_identifier);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_action_id_text ON pending_confirmations(action_id_text);

-- 5. Create compatibility views that match expected structure

-- Conversations view with conversation_id as text
CREATE OR REPLACE VIEW conversations_v2 AS
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

-- Messages view with text-based conversation_id
CREATE OR REPLACE VIEW conversation_messages_v2 AS
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
FROM conversation_messages cm
WHERE cm.conversation_identifier IS NOT NULL;

-- Confirmations view with text-based IDs
CREATE OR REPLACE VIEW pending_confirmations_v2 AS
SELECT 
    COALESCE(pc.action_id_text, pc.action_id::text) as action_id,
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

-- 6. Helper functions for conversational AI

-- Function to find or create conversation (improved)
CREATE OR REPLACE FUNCTION find_or_create_conversation_v2(
    p_workspace_id UUID,
    p_chat_id TEXT,
    p_title TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS TABLE (
    conversation_id TEXT,
    workspace_id UUID,
    chat_id TEXT,
    created BOOLEAN
) AS $$
DECLARE
    conversation_uuid UUID;
    conv_id TEXT;
    was_created BOOLEAN := FALSE;
BEGIN
    -- Generate the conversation identifier
    conv_id := p_workspace_id::text || '_' || p_chat_id;
    
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
        was_created := TRUE;
    END IF;
    
    RETURN QUERY SELECT conv_id, p_workspace_id, p_chat_id, was_created;
END;
$$ LANGUAGE plpgsql;

-- Function to insert message with text-based conversation_id
CREATE OR REPLACE FUNCTION insert_conversation_message_v2(
    p_conversation_id TEXT,
    p_message_id TEXT,
    p_role TEXT,
    p_content TEXT,
    p_content_type TEXT DEFAULT 'text',
    p_tools_used JSONB DEFAULT '[]',
    p_actions_performed JSONB DEFAULT '[]',
    p_context_snapshot JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    message_uuid UUID;
    conv_uuid UUID;
    parts TEXT[];
    ws_id UUID;
    c_id TEXT;
BEGIN
    -- Parse conversation_id to get workspace_id and chat_id
    parts := string_to_array(p_conversation_id, '_');
    
    IF array_length(parts, 1) >= 2 THEN
        ws_id := parts[1]::UUID;
        c_id := array_to_string(parts[2:], '_');
        
        -- Find the actual conversation UUID
        SELECT id INTO conv_uuid
        FROM conversations
        WHERE workspace_id = ws_id AND chat_id = c_id;
        
        IF conv_uuid IS NOT NULL THEN
            -- Insert the message
            INSERT INTO conversation_messages (
                conversation_id,
                conversation_identifier,
                message_id,
                role,
                content,
                content_type,
                tools_used,
                actions_performed,
                context_snapshot
            ) VALUES (
                conv_uuid,
                p_conversation_id,
                p_message_id,
                p_role,
                p_content,
                p_content_type,
                p_tools_used,
                p_actions_performed,
                p_context_snapshot
            ) RETURNING id INTO message_uuid;
        END IF;
    END IF;
    
    RETURN message_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to insert confirmation with text-based IDs
CREATE OR REPLACE FUNCTION insert_pending_confirmation_v2(
    p_action_id TEXT,
    p_conversation_id TEXT,
    p_action_type TEXT,
    p_action_description TEXT,
    p_parameters JSONB,
    p_risk_level TEXT,
    p_expires_at TIMESTAMP WITH TIME ZONE,
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    confirmation_uuid UUID;
    conv_uuid UUID;
    parts TEXT[];
    ws_id UUID;
    c_id TEXT;
BEGIN
    -- Parse conversation_id
    parts := string_to_array(p_conversation_id, '_');
    
    IF array_length(parts, 1) >= 2 THEN
        ws_id := parts[1]::UUID;
        c_id := array_to_string(parts[2:], '_');
        
        -- Find the conversation UUID
        SELECT id INTO conv_uuid
        FROM conversations
        WHERE workspace_id = ws_id AND chat_id = c_id;
        
        IF conv_uuid IS NOT NULL THEN
            -- Insert the confirmation
            INSERT INTO pending_confirmations (
                action_id_text,
                conversation_id,
                conversation_identifier,
                action_type,
                action_description,
                parameters,
                risk_level,
                expires_at,
                metadata
            ) VALUES (
                p_action_id,
                conv_uuid,
                p_conversation_id,
                p_action_type,
                p_action_description,
                p_parameters,
                p_risk_level,
                p_expires_at,
                p_metadata
            ) RETURNING id INTO confirmation_uuid;
        END IF;
    END IF;
    
    RETURN confirmation_uuid;
END;
$$ LANGUAGE plpgsql;

-- 7. Grant permissions on new functions and views
GRANT EXECUTE ON FUNCTION find_or_create_conversation_v2(UUID, TEXT, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION insert_conversation_message_v2(TEXT, TEXT, TEXT, TEXT, TEXT, JSONB, JSONB, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION insert_pending_confirmation_v2(TEXT, TEXT, TEXT, TEXT, JSONB, TEXT, TIMESTAMP WITH TIME ZONE, JSONB) TO authenticated;

GRANT SELECT ON conversations_v2 TO authenticated;
GRANT SELECT ON conversation_messages_v2 TO authenticated;
GRANT SELECT ON pending_confirmations_v2 TO authenticated;

-- 8. Create triggers to auto-populate conversation_identifier for new records

-- Trigger for conversation_messages
CREATE OR REPLACE FUNCTION auto_populate_conversation_identifier()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.conversation_identifier IS NULL AND NEW.conversation_id IS NOT NULL THEN
        SELECT generate_conversation_identifier(c.workspace_id, c.chat_id)
        INTO NEW.conversation_identifier
        FROM conversations c
        WHERE c.id = NEW.conversation_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_populate_message_identifier
    BEFORE INSERT OR UPDATE ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION auto_populate_conversation_identifier();

-- Trigger for pending_confirmations
CREATE TRIGGER trigger_auto_populate_confirmation_identifier
    BEFORE INSERT OR UPDATE ON pending_confirmations
    FOR EACH ROW
    EXECUTE FUNCTION auto_populate_conversation_identifier();

-- Success message
SELECT 'Database compatibility fix V2 applied successfully! Conversational AI should now work with existing structure.' as status;