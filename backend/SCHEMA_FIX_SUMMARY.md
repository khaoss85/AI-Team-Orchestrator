# 🔧 DATABASE SCHEMA ANALYSIS & FIXES NEEDED

## FOUND ISSUES

### 1. ❌ workspace_goals table - Missing AI columns

**Current schema:**
```sql
CREATE TABLE public.workspace_goals (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL,
    metric_type text NOT NULL CHECK (...),
    target_value numeric NOT NULL CHECK (target_value > 0::numeric),
    current_value numeric DEFAULT 0,
    unit text DEFAULT ''::text,
    priority integer DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
    status text DEFAULT 'active'::text CHECK (...),
    success_criteria jsonb DEFAULT '{}'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    description text,
    source_goal_text text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    last_validation_at timestamp with time zone,
    validation_frequency_minutes integer DEFAULT 20
);
```

**Missing columns required by AI Goal Extractor:**
- `confidence` DECIMAL(3,2) - AI extraction confidence score
- `semantic_context` JSONB - AI semantic understanding data
- `goal_type` TEXT - Goal classification (deliverable, metric, quality, timeline, quantity)
- `is_percentage` BOOLEAN - Whether the goal is percentage-based
- `is_minimum` BOOLEAN - Whether the goal represents minimum threshold

**SQL Fix:**
```sql
-- Add AI-driven goal extraction columns
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2) DEFAULT 0.8 
CHECK (confidence >= 0.0 AND confidence <= 1.0);

ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS semantic_context JSONB DEFAULT '{}';

ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS goal_type TEXT DEFAULT 'deliverable'
CHECK (goal_type IN ('deliverable', 'metric', 'quality', 'timeline', 'quantity'));

ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS is_percentage BOOLEAN DEFAULT false;

ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS is_minimum BOOLEAN DEFAULT true;
```

### 2. ⚠️ workspace_insights table - Task ID constraint mismatch

**Current schema:**
```sql
task_id uuid NOT NULL,
```

**Model definition:**
```python
task_id: Optional[UUID] = PydanticField(default=None, description="ID del task sorgente (opzionale)")
```

**Problem:** Database requires task_id but model makes it optional. This causes insertion failures when storing workspace-level insights (not task-specific).

**SQL Fix:**
```sql
-- Make task_id optional to match model
ALTER TABLE workspace_insights 
ALTER COLUMN task_id DROP NOT NULL;
```

### 3. ✅ All other tables appear correctly aligned

**Checked tables:**
- ✅ `workspaces` - Schema matches usage
- ✅ `agents` - Schema matches usage  
- ✅ `tasks` - Schema matches usage
- ✅ `logs` - Schema matches usage
- ✅ `execution_logs` - Schema matches usage
- ✅ `human_feedback_requests` - Schema matches usage
- ✅ `documents` - Schema matches usage
- ✅ `custom_tools` - Schema matches usage
- ✅ `team_proposals` - Schema matches usage
- ✅ `agent_proposals` - Schema matches usage
- ✅ `agent_handoffs` - Schema matches usage

## PRIORITY FIXES NEEDED

### HIGH PRIORITY (Blocks AI Goal Extraction)
1. **Add missing columns to workspace_goals**
   - Without these, AI goal extraction fails with schema errors
   - Currently handled with temporary workaround that excludes AI data

### MEDIUM PRIORITY (Affects Memory System)  
2. **Fix workspace_insights task_id constraint**
   - Without this, workspace-level insights cannot be stored
   - Affects memory system functionality

## WORKAROUNDS CURRENTLY IN PLACE

### ✅ workspace_goals - Temporary fix applied
- `ai_goal_extractor.py` contains `safe_goal_data_for_db()` method
- Excludes AI-specific columns until schema is updated
- Logs warnings about missing columns

### ✅ workspace_insights - Temporary fix applied  
- `workspace_memory.py` handles None task_id correctly
- Converts None to NULL instead of string "None"

## VERIFICATION COMMANDS

After applying fixes, verify with:

```sql
-- Verify workspace_goals columns
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'workspace_goals' 
ORDER BY ordinal_position;

-- Verify workspace_insights task_id is nullable
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'workspace_insights' AND column_name = 'task_id';
```

## IMPACT

### Before fixes:
- ❌ AI Goal Extraction works but loses semantic data
- ❌ Workspace-level insights cannot be stored
- ⚠️ System falls back to pattern-based extraction

### After fixes:
- ✅ Full AI Goal Extraction with semantic understanding
- ✅ Complete workspace memory system functionality
- ✅ 100% AI-driven, scalable, universal system as designed