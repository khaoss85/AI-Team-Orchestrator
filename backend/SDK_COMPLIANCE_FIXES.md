# SDK Compliance Fixes - Implementation Guide

## File: backend/services/document_manager.py

### Fix 1: Remove HTTP Client Setup (Lines 84-91)

**REMOVE THESE LINES:**
```python
# Lines 84-91 - DELETE ALL OF THIS
self.api_key = os.getenv("OPENAI_API_KEY")
self.base_url = "https://api.openai.com/v1"
self.headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2"
}
```

The OpenAI client already handles authentication internally.

### Fix 2: Replace Vector Store File Creation (Lines 210-241)

**CURRENT CODE (VIOLATION):**
```python
# Lines 210-241
payload = {"file_id": openai_file.id}

response = requests.post(
    f"{self.base_url}/vector_stores/{vector_store_id}/files",
    headers=self.headers,
    json=payload,
    timeout=30
)

if response.status_code == 200:
    logger.info(f"✅ File {openai_file.id} added to vector store {vector_store_id}")
    
    # Wait for processing to complete
    import time
    for _ in range(30):  # Max 30 seconds wait
        time.sleep(1)
        
        # Check status
        status_response = requests.get(
            f"{self.base_url}/vector_stores/{vector_store_id}/files/{openai_file.id}",
            headers=self.headers,
            timeout=10
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data.get("status") == "completed":
                logger.info(f"✅ File processing completed in vector store")
                break
```

**REPLACE WITH SDK VERSION:**
```python
# SDK COMPLIANT VERSION
try:
    # Create vector store file using SDK
    vector_store_file = self.openai_client.beta.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=openai_file.id
    )
    
    logger.info(f"✅ File {openai_file.id} added to vector store {vector_store_id}")
    
    # Wait for processing to complete
    import time
    for _ in range(30):  # Max 30 seconds wait
        time.sleep(1)
        
        # Check status using SDK
        file_status = self.openai_client.beta.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=openai_file.id
        )
        
        if file_status.status == "completed":
            logger.info(f"✅ File processing completed in vector store")
            break
            
except Exception as e:
    logger.error(f"Failed to add file to vector store: {e}")
    raise
```

### Fix 3: Replace Vector Store Creation (Lines 332-345)

**CURRENT CODE (VIOLATION):**
```python
# Lines 332-345
payload = {
    "name": f"Workspace {workspace_id} Documents",
    "file_ids": []
}

response = requests.post(
    f"{self.base_url}/vector_stores",
    headers=self.headers,
    json=payload,
    timeout=30
)

if response.status_code == 200:
    vector_store_data = response.json()
    vector_store_id = vector_store_data["id"]
```

**REPLACE WITH SDK VERSION:**
```python
# SDK COMPLIANT VERSION
try:
    # Create vector store using SDK
    vector_store = self.openai_client.beta.vector_stores.create(
        name=f"Workspace {workspace_id} Documents",
        file_ids=[]
    )
    
    vector_store_id = vector_store.id
    logger.info(f"✅ Created vector store {vector_store_id} for workspace")
    
except Exception as e:
    logger.error(f"Failed to create vector store: {e}")
    raise
```

### Fix 4: Replace Vector Store File Deletion (Lines 514-522)

**CURRENT CODE (VIOLATION):**
```python
# Lines 514-522
if doc_data.get("vector_store_id") and doc_data.get("openai_file_id"):
    response = requests.delete(
        f"{self.base_url}/vector_stores/{doc_data['vector_store_id']}/files/{doc_data['openai_file_id']}",
        headers=self.headers,
        timeout=30
    )
    
    if response.status_code in [200, 204]:
        logger.info(f"✅ Removed file from vector store")
```

**REPLACE WITH SDK VERSION:**
```python
# SDK COMPLIANT VERSION
if doc_data.get("vector_store_id") and doc_data.get("openai_file_id"):
    try:
        # Delete vector store file using SDK
        self.openai_client.beta.vector_stores.files.delete(
            vector_store_id=doc_data["vector_store_id"],
            file_id=doc_data["openai_file_id"]
        )
        logger.info(f"✅ Removed file from vector store")
        
    except Exception as e:
        # File might already be deleted, log but don't fail
        logger.warning(f"Could not remove file from vector store: {e}")
```

### Fix 5: Remove requests import

**At the top of the file, REMOVE:**
```python
import requests  # Remove this line if not used elsewhere
```

## File: backend/tools/openai_sdk_tools.py

### Fix: Remove Unused HTTP Setup in FileSearchTool (Lines 189-196)

**REMOVE THESE LINES:**
```python
# Lines 189-196 - DELETE ALL OF THIS
# Initialize for HTTP API access
self.api_key = os.getenv("OPENAI_API_KEY")
self.base_url = "https://api.openai.com/v1"
self.headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2"
}
```

Keep only the OpenAI client initialization (lines 199-204).

## Testing After Fixes

Run these tests to verify the fixes work:

```python
# Test 1: Upload a document
async def test_document_upload():
    from services.document_manager import document_manager
    
    with open("test.pdf", "rb") as f:
        result = await document_manager.upload_document(
            workspace_id="test-workspace",
            file_content=f.read(),
            filename="test.pdf",
            uploaded_by="test-user"
        )
    print(f"Upload result: {result}")

# Test 2: Create vector store
async def test_vector_store_creation():
    from services.document_manager import document_manager
    
    vector_store_id = await document_manager._get_or_create_vector_store(
        "test-workspace"
    )
    print(f"Vector store ID: {vector_store_id}")

# Test 3: Delete document
async def test_document_deletion():
    from services.document_manager import document_manager
    
    success = await document_manager.delete_document(
        document_id="test-doc-id"
    )
    print(f"Deletion success: {success}")
```

## Verification Commands

After implementing fixes, run:

```bash
# Check for any remaining HTTP calls to OpenAI
grep -r "requests.*openai" backend/
grep -r "api.openai.com" backend/ --exclude="*.md"

# Check all OpenAI SDK usage is correct
grep -r "openai_client.beta" backend/

# Verify no manual headers for OpenAI
grep -r "Authorization.*Bearer.*OPENAI" backend/
```

## Benefits After Implementation

1. **Automatic Retries**: SDK handles transient failures automatically
2. **Better Error Messages**: SDK provides structured error information
3. **Type Safety**: IDE can provide better autocompletion and type checking
4. **Future Compatibility**: SDK will handle API version changes
5. **Connection Pooling**: SDK manages HTTP connections efficiently
6. **Rate Limiting**: SDK respects rate limits automatically

## Migration Checklist

- [ ] Backup current document_manager.py
- [ ] Remove HTTP client setup (lines 84-91)
- [ ] Replace vector store file creation (lines 210-241)
- [ ] Replace vector store creation (lines 332-345)
- [ ] Replace vector store file deletion (lines 514-522)
- [ ] Remove unused requests import if applicable
- [ ] Fix openai_sdk_tools.py FileSearchTool
- [ ] Run all tests
- [ ] Verify no HTTP calls remain
- [ ] Deploy and monitor for issues