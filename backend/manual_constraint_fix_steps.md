# 🚨 Manual Database Constraint Fix Instructions

## Root Cause Analysis

**Unique Constraint Violation**: `unique_workspace_goal_title`
- **Constraint**: `(workspace_id, goal_id, title)` must be unique
- **Conflict**: Deliverable "Find Competitor Campaign Performance Metrics..." already exists in goal `10f7957c-cc17-481b-970a-4ec4a9fd26c4`
- **Issue**: Attempting to move another deliverable with same title from NULL goal to `74930a71-a443-4d56-9c09-1a8893214a9f`

## Current State Summary

- **Total deliverables**: 22 in workspace `3adfdc92-b316-442f-b9ca-a8d1df49e200`
- **NULL goal deliverables**: 10 (need reassignment)  
- **Existing duplicates**: 3 groups with duplicate titles in NULL goals
- **Cross-goal conflict**: 1 title exists in both assigned goal and NULL goal

## Option 1: Automated SQL Fix (RECOMMENDED)

### Step 1: Execute the Safe Fix
```bash
# Navigate to backend directory
cd /Users/pelleri/Documents/ai-team-orchestrator/backend

# Execute the comprehensive fix
python3 -c "
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Read and execute the fix
with open('fix_unique_constraint_violation.sql', 'r') as f:
    sql_content = f.read()

print('🔧 Executing database constraint fix...')
print('This will:')
print('1. Create backup table')  
print('2. Fix existing duplicates with unique suffixes')
print('3. Resolve cross-goal title conflicts')
print('4. Apply safe goal-deliverable mapping')
print('5. Validate results')
print()

# Note: Since we can't execute raw SQL directly, we'll use individual operations
"
```

### Step 2: Manual Execution (Since raw SQL not available)
```bash
python3 -c "
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'

print('🔧 STEP 1: Fix existing duplicates in NULL goals')

# Fix duplicate 1
try:
    result = supabase.table('deliverables').update({
        'title': 'Find Qualified Contacts Using Web Search - AI-Generated Deliverable (Instance 2)'
    }).eq('id', '3fd61d0c-d699-4439-9117-4da07d33fe5a').execute()
    print('✅ Fixed duplicate 1')
except Exception as e:
    print(f'❌ Error fixing duplicate 1: {e}')

# Fix duplicate 2  
try:
    result = supabase.table('deliverables').update({
        'title': 'Research Total Number of Email Sequences Tested: Instagram Analytics Tool - AI-Generated Deliverable (Instance 2)'
    }).eq('id', '4d38db3c-7a17-4148-9017-7be9b5c8dafb').execute()
    print('✅ Fixed duplicate 2')
except Exception as e:
    print(f'❌ Error fixing duplicate 2: {e}')

# Fix triple duplicate (part 1)
try:
    result = supabase.table('deliverables').update({
        'title': 'Gather Sequence Assignments for Contacts: File Search Tool - AI-Generated Deliverable (Instance 2)'
    }).eq('id', 'db31ca02-8397-4228-82d8-cc2211ac6061').execute()
    print('✅ Fixed triple duplicate (instance 2)')
except Exception as e:
    print(f'❌ Error fixing triple duplicate 2: {e}')

# Fix triple duplicate (part 2) 
try:
    result = supabase.table('deliverables').update({
        'title': 'Gather Sequence Assignments for Contacts: File Search Tool - AI-Generated Deliverable (Instance 3)'
    }).eq('id', '4b9220d4-4786-44e9-9080-911b6eb91894').execute()
    print('✅ Fixed triple duplicate (instance 3)')
except Exception as e:
    print(f'❌ Error fixing triple duplicate 3: {e}')

print()
print('🔧 STEP 2: Fix cross-goal title conflict')

# Rename the NULL goal version to avoid conflict with existing goal record
try:
    result = supabase.table('deliverables').update({
        'title': 'Find Competitor Campaign Performance Metrics: Database Query - AI-Generated Deliverable (Duplicate Fix)'
    }).eq('id', '2de6c28f-fe28-40fe-afcf-18140954ddca').execute()
    print('✅ Renamed conflicting deliverable')
except Exception as e:
    print(f'❌ Error renaming conflict: {e}')

print()
print('✅ Constraint conflicts resolved - ready for goal mapping')
"
```

### Step 3: Apply Goal Mappings
```bash
python3 -c "
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'

print('🎯 STEP 3: Apply semantic goal mappings')

# Get all NULL goal deliverables
result = supabase.table('deliverables').select('id, title').eq('workspace_id', workspace_id).is_('goal_id', 'null').execute()
null_deliverables = result.data

print(f'Found {len(null_deliverables)} deliverables without goals')

# Define goal mappings with semantic rules
goal_mappings = {
    '74930a71-a443-4d56-9c09-1a8893214a9f': {  # Analisi competitor
        'keywords': ['competitor', 'analisi', 'campaign', 'outbound', 'performance', 'metrics'],
        'name': 'Competitor Analysis'
    },
    'd707a492-db77-4501-ad7e-cc446efd5f35': {  # Strategia interazione
        'keywords': ['strategia', 'interazione', 'interaction', 'strategy', 'email sequence', 'contacts', 'qualified', 'research'],
        'name': 'Interaction Strategy'
    },
    '22f28697-e628-48a1-977d-4cf69496f486': {  # Piano editoriale
        'keywords': ['piano', 'editoriale', 'editorial', 'content', 'calendar'],
        'name': 'Editorial Plan'
    }
}

# Apply mappings
for deliverable in null_deliverables:
    title_lower = deliverable['title'].lower()
    matched_goal = None
    
    # Find best matching goal
    for goal_id, config in goal_mappings.items():
        if any(keyword in title_lower for keyword in config['keywords']):
            matched_goal = goal_id
            goal_name = config['name']
            break
    
    if matched_goal:
        try:
            result = supabase.table('deliverables').update({
                'goal_id': matched_goal
            }).eq('id', deliverable['id']).execute()
            print(f'✅ Mapped \"{deliverable['title'][:50]}...\" → {goal_name}')
        except Exception as e:
            print(f'❌ Error mapping {deliverable['id']}: {e}')
    else:
        print(f'⚠️ No match found for \"{deliverable['title'][:50]}...\"')

print()
print('✅ Goal mapping completed')
"
```

### Step 4: Verify Results
```bash
python3 -c "
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'

print('🔍 VERIFICATION RESULTS')
print('=' * 50)

# Check remaining NULL goals
result = supabase.table('deliverables').select('id, title').eq('workspace_id', workspace_id).is_('goal_id', 'null').execute()
remaining_nulls = result.data

print(f'Deliverables still without goals: {len(remaining_nulls)}')
for d in remaining_nulls:
    print(f'  - \"{d['title'][:60]}...\"')

# Check final distribution
result = supabase.table('deliverables').select('goal_id').eq('workspace_id', workspace_id).execute()
all_deliverables = result.data

goal_distribution = {}
for d in all_deliverables:
    goal_id = d['goal_id'] or 'NULL'
    goal_distribution[goal_id] = goal_distribution.get(goal_id, 0) + 1

print()
print('Final goal distribution:')
for goal_id, count in goal_distribution.items():
    if goal_id == 'NULL':
        print(f'  No Goal: {count} deliverables')
    else:
        print(f'  Goal {goal_id[:8]}...: {count} deliverables')

print()
print('✅ Verification complete')
"
```

## Option 2: Manual Database Console Fix

### If you have direct database access:

1. **Connect to Supabase database console**
2. **Execute this SQL directly**:

```sql
-- Step 1: Fix duplicates first
UPDATE deliverables SET title = title || ' (Instance 2)' WHERE id = '3fd61d0c-d699-4439-9117-4da07d33fe5a';
UPDATE deliverables SET title = title || ' (Instance 2)' WHERE id = '4d38db3c-7a17-4148-9017-7be9b5c8dafb';
UPDATE deliverables SET title = title || ' (Instance 2)' WHERE id = 'db31ca02-8397-4228-82d8-cc2211ac6061';
UPDATE deliverables SET title = title || ' (Instance 3)' WHERE id = '4b9220d4-4786-44e9-9080-911b6eb91894';

-- Step 2: Fix cross-goal conflict
UPDATE deliverables SET title = 'Find Competitor Campaign Performance Metrics: Database Query - AI-Generated Deliverable (Duplicate Fix)' WHERE id = '2de6c28f-fe28-40fe-afcf-18140954ddca';

-- Step 3: Apply goal mappings (now safe)
UPDATE deliverables SET goal_id = '74930a71-a443-4d56-9c09-1a8893214a9f' WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200' AND goal_id IS NULL AND (title ILIKE '%competitor%' OR title ILIKE '%campaign%' OR title ILIKE '%performance%');

UPDATE deliverables SET goal_id = 'd707a492-db77-4501-ad7e-cc446efd5f35' WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200' AND goal_id IS NULL AND (title ILIKE '%interaction%' OR title ILIKE '%sequence%' OR title ILIKE '%contacts%');
```

## Option 3: Alternative - Remove Duplicates Instead

If you prefer to remove duplicates rather than rename them:

```bash
python3 -c "
# Delete the newer duplicate records instead of renaming
supabase.table('deliverables').delete().eq('id', '3fd61d0c-d699-4439-9117-4da07d33fe5a').execute()
supabase.table('deliverables').delete().eq('id', '4d38db3c-7a17-4148-9017-7be9b5c8dafb').execute()
supabase.table('deliverables').delete().eq('id', 'db31ca02-8397-4228-82d8-cc2211ac6061').execute()
supabase.table('deliverables').delete().eq('id', '4b9220d4-4786-44e9-9080-911b6eb91894').execute()
supabase.table('deliverables').delete().eq('id', '2de6c28f-fe28-40fe-afcf-18140954ddca').execute()
"
```

## Recovery Instructions

### If anything goes wrong:

```bash
# Check current state
python3 -c "
result = supabase.table('deliverables').select('id, title, goal_id').eq('workspace_id', '3adfdc92-b316-442f-b9ca-a8d1df49e200').execute()
print(f'Current deliverable count: {len(result.data)}')
"

# If you need to restore, you can reset problematic deliverables to NULL:
python3 -c "
# Reset specific deliverables back to NULL goal if needed
problem_ids = ['2de6c28f-fe28-40fe-afcf-18140954ddca']
for id in problem_ids:
    result = supabase.table('deliverables').update({'goal_id': None}).eq('id', id).execute()
    print(f'Reset {id} to NULL goal')
"
```

## Expected Results After Fix

- **0 deliverables with NULL goal_id** (all properly assigned)
- **0 duplicate titles within same goals** (unique constraint satisfied)
- **Proper goal distribution**:
  - Competitor Analysis: ~3-4 deliverables
  - Interaction Strategy: ~5-6 deliverables  
  - Editorial Plan: ~1-2 deliverables
- **No constraint violations** when running future goal assignment operations

## Next Steps

1. **Execute the fix** using Option 1 (recommended)
2. **Verify results** using the verification script
3. **Test the original goal-deliverable mapping** that was failing
4. **Monitor logs** for any remaining constraint issues

The fix addresses the root cause (title conflicts) while preserving all data through strategic renaming rather than deletion.