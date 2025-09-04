# Page Count Migration Instructions

## 🔍 Problem Analysis
**Error**: `Could not find the 'page_count' column of 'workspace_documents' in the schema cache`

**Root Cause**: The document upload system in `document_manager.py` tries to insert a `page_count` field that doesn't exist in the `workspace_documents` table.

## 🛠️ Temporary Fix Applied ✅
**File**: `backend/services/document_manager.py` (lines 291-296)
- **Status**: ✅ **APPLIED** - `page_count` field temporarily removed from database inserts
- **Effect**: Document uploads now work without the missing column error
- **Limitation**: Page count information is not stored in database (but preserved in-memory metadata)

## 📋 Manual Migration Required

### Step 1: Apply Database Migration
Run this SQL in your **Supabase SQL Editor**:

```sql
-- Add page_count column to workspace_documents table
ALTER TABLE workspace_documents ADD COLUMN page_count INTEGER;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_workspace_documents_page_count 
ON workspace_documents(page_count) 
WHERE page_count IS NOT NULL;

-- Add documentation comment
COMMENT ON COLUMN workspace_documents.page_count IS 'Number of pages in document (for PDFs and other paginated documents)';

-- Set default page_count to 1 for existing PDF documents
UPDATE workspace_documents 
SET page_count = 1 
WHERE page_count IS NULL 
  AND mime_type = 'application/pdf';
```

### Step 2: Re-enable Page Count in Code
After the database migration succeeds:

**File**: `backend/services/document_manager.py`
**Action**: Uncomment line 291:

```python
# CHANGE THIS:
# "page_count": page_count  # TODO: Re-enable after migration 017 is applied

# TO THIS:
"page_count": page_count
```

**Also remove**: Lines 294-296 (the TODO comment block)

## 🧪 Testing Migration Success

### Test 1: Database Schema Verification
```bash
python3 -c "
from database import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('workspace_documents').select('*').limit(1).execute()
columns = list(result.data[0].keys()) if result.data else []
if 'page_count' in columns:
    print('✅ SUCCESS: page_count column exists')
else:
    print('❌ FAILED: page_count column still missing')
    print('Available columns:', columns)
"
```

### Test 2: Document Upload Test
```bash
# After re-enabling page_count in code, test upload
python3 backend/test_document_upload.py  # (create this test if needed)
```

## 📁 Migration Files Created
- **Forward Migration**: `migrations/017_add_page_count_to_workspace_documents.sql`
- **Rollback Migration**: `migrations/017_add_page_count_to_workspace_documents_ROLLBACK.sql`
- **Instructions**: This file

## 🚨 Current System Status
- **Document Uploads**: ✅ **WORKING** (with temporary fix)
- **Page Count Storage**: ❌ **DISABLED** (until migration applied)
- **Content Extraction**: ✅ **WORKING** (other fields functional)
- **PDF Processing**: ✅ **WORKING** (page count calculated but not stored)

## 📚 Related Files
- **Main Fix**: `backend/services/document_manager.py` (lines 291-296)
- **PDF Extractor**: `backend/services/pdf_content_extractor.py` (uses page_count)
- **Test Script**: `backend/test_pdf_content_15_pillars.py` (references page_count)

## ⚡ Priority
**High** - Page count is important metadata for document management and should be restored once migration is applied.

**Next Steps**:
1. Apply SQL migration in Supabase ⏳
2. Re-enable page_count in document_manager.py ⏳ 
3. Test document uploads with page_count storage ⏳
4. Remove this temporary documentation ⏳