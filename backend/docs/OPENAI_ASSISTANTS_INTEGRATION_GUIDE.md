# OpenAI Assistants API Integration Guide

## Quick Start

### 1. Apply Database Migration
```bash
# Run the migration to create workspace_assistants table
psql -U your_user -d your_database -f migrations/018_add_openai_assistants_support.sql
```

### 2. Enable OpenAI Assistants
Add to your `.env` file:
```bash
# Enable OpenAI Assistants API for RAG
USE_OPENAI_ASSISTANTS=true

# Optional configuration
OPENAI_ASSISTANT_MODEL=gpt-4-turbo-preview
OPENAI_ASSISTANT_TEMPERATURE=0.7
OPENAI_ASSISTANT_MAX_TOKENS=4096
OPENAI_FILE_SEARCH_MAX_RESULTS=10
```

### 3. Update Routes Integration

#### Option A: Minimal Change (Recommended for Testing)

In `backend/routes/conversational.py`, update the import and agent creation:

```python
# Old import
from ai_agents.conversational_simple import SimpleConversationalAgent

# New import
from ai_agents.conversational_factory import create_and_initialize_agent

# Old agent creation
@app.post("/api/conversational/message")
async def process_message(request: ConversationRequest):
    agent = SimpleConversationalAgent(request.workspace_id, request.chat_id)
    
# New agent creation
@app.post("/api/conversational/message")
async def process_message(request: ConversationRequest):
    agent = await create_and_initialize_agent(request.workspace_id, request.chat_id)
```

#### Option B: Full Integration

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_agents.conversational_factory import create_and_initialize_agent

router = APIRouter(prefix="/api/conversational", tags=["conversational"])

class ConversationRequest(BaseModel):
    workspace_id: str
    chat_id: str = "general"
    message: str
    message_id: str = None

@router.post("/message")
async def process_message(request: ConversationRequest):
    """Process a conversational message with OpenAI Assistants or fallback"""
    try:
        # Create and initialize the appropriate agent
        agent = await create_and_initialize_agent(
            request.workspace_id, 
            request.chat_id
        )
        
        # Process the message
        response = await agent.process_message(
            request.message,
            request.message_id
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message-with-thinking")
async def process_message_with_thinking(request: ConversationRequest):
    """Process with visible thinking steps"""
    try:
        agent = await create_and_initialize_agent(
            request.workspace_id,
            request.chat_id
        )
        
        # Process with thinking (both agents support this)
        response = await agent.process_message_with_thinking(
            request.message,
            request.message_id
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing the Integration

### 1. Test Document Upload and Search

```python
# test_assistant_rag.py
import asyncio
from ai_agents.conversational_factory import create_and_initialize_agent

async def test_document_search():
    # Create agent
    agent = await create_and_initialize_agent("test-workspace-id")
    
    # Test search query
    response = await agent.process_message(
        "Search for information about project requirements in the uploaded PDFs"
    )
    
    print("Response:", response.message)
    if response.citations:
        print("Citations found:", len(response.citations))
        for citation in response.citations:
            print(f"  - {citation.get('filename')}: {citation.get('quote')[:100]}...")

asyncio.run(test_document_search())
```

### 2. Test with cURL

```bash
# Test with OpenAI Assistants enabled
curl -X POST http://localhost:8000/api/conversational/message \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "your-workspace-id",
    "message": "Search for budget information in the uploaded documents"
  }'
```

### 3. Verify Assistant Creation

```python
# verify_assistant.py
from database import get_supabase_client

supabase = get_supabase_client()

# Check if assistant was created
result = supabase.table("workspace_assistants")\
    .select("*")\
    .eq("workspace_id", "your-workspace-id")\
    .execute()

if result.data:
    print("Assistant found:", result.data[0])
else:
    print("No assistant created yet")
```

## Migration Path

### Phase 1: Testing (Week 1)
1. Enable for specific test workspaces only
2. Monitor performance and accuracy
3. Collect user feedback

```python
# Selective enablement
def should_use_assistants(workspace_id: str) -> bool:
    """Enable for specific workspaces during testing"""
    TEST_WORKSPACES = ["workspace-1", "workspace-2"]
    return (
        os.getenv("USE_OPENAI_ASSISTANTS", "false").lower() == "true" 
        and workspace_id in TEST_WORKSPACES
    )
```

### Phase 2: Gradual Rollout (Week 2)
1. Enable for 10% of workspaces
2. Monitor error rates and performance
3. Increase to 50% if successful

### Phase 3: Full Migration (Week 3-4)
1. Enable for all workspaces
2. Keep fallback mechanism active
3. Deprecate SimpleConversationalAgent after stability confirmed

## Monitoring and Debugging

### Check Assistant Status
```python
from services.openai_assistant_manager import assistant_manager

# Get assistant info
assistant = await assistant_manager.get_or_create_assistant("workspace-id")
print(f"Assistant ID: {assistant['id']}")
print(f"Model: {assistant['model']}")
print(f"Tools: {assistant['tools']}")
```

### Monitor Vector Store Attachment
```python
from services.document_manager import document_manager

# Check vector stores
vector_stores = await document_manager.get_vector_store_ids_for_agent("workspace-id")
print(f"Vector stores attached: {vector_stores}")
```

### Debug Search Results
```python
# Enable debug logging
import logging
logging.getLogger("openai_assistant_manager").setLevel(logging.DEBUG)

# Process message with debugging
agent = await create_and_initialize_agent("workspace-id")
response = await agent.process_message("search for test document")

# Check citations
if response.citations:
    print("Documents found and cited!")
else:
    print("No documents cited - check vector store attachment")
```

## Troubleshooting

### Issue: "No documents found" despite uploads
**Solution**: Verify vector stores are attached
```python
# Re-sync vector stores
from services.openai_assistant_manager import assistant_manager

assistant = await assistant_manager.get_or_create_assistant("workspace-id")
vector_store_ids = await document_manager.get_vector_store_ids_for_agent("workspace-id")
await assistant_manager.update_assistant_vector_stores(assistant["id"], vector_store_ids)
```

### Issue: Assistant not created
**Solution**: Check database migration and permissions
```sql
-- Verify table exists
SELECT * FROM information_schema.tables WHERE table_name = 'workspace_assistants';

-- Check for creation errors
SELECT * FROM workspace_assistants WHERE workspace_id = 'your-workspace-id';
```

### Issue: Slow response times
**Solution**: Optimize assistant configuration
```python
# Use faster model for non-critical searches
config = AssistantConfig(
    model="gpt-3.5-turbo",  # Faster than gpt-4
    temperature=0.3,  # More deterministic
    max_tokens=2048  # Limit response length
)
```

## Performance Optimization

### 1. Thread Reuse
Threads are automatically reused per workspace to maintain context and reduce API calls.

### 2. Vector Store Caching
Vector stores are created once per workspace and reused across sessions.

### 3. Async Processing
All operations are async to prevent blocking:
```python
# Good - async all the way
response = await agent.process_message(message)

# Bad - blocks event loop
response = asyncio.run(agent.process_message(message))
```

### 4. Rate Limiting
The system respects OpenAI rate limits automatically through the SDK.

## Rollback Plan

If issues arise, disable OpenAI Assistants immediately:

```bash
# In .env
USE_OPENAI_ASSISTANTS=false
```

Or programmatically:
```python
# Emergency override in code
os.environ["USE_OPENAI_ASSISTANTS"] = "false"
```

The system will automatically fall back to SimpleConversationalAgent without any code changes.

## Success Metrics

Monitor these metrics to evaluate success:

1. **Search Accuracy**: Citations provided vs queries needing them
2. **Response Time**: Average time to process messages
3. **Error Rate**: Failed searches or timeout errors
4. **User Satisfaction**: Feedback on search quality
5. **Cost**: Monitor OpenAI API usage costs

## Next Steps

1. **Test in Development**: Verify basic functionality works
2. **Document Upload Test**: Upload PDFs and test search
3. **Performance Baseline**: Measure response times
4. **User Testing**: Get feedback from test users
5. **Production Rollout**: Follow phased migration plan