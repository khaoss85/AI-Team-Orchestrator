# Claude Sub-Agent Development Guide

## Overview
This guide provides comprehensive instructions for future Claude Code sub-agent development on the AI Team Orchestrator codebase, specifically focusing on document access systems and RAG implementations.

## 🎯 Core Architectural Principles

### The 15 Pillars Framework
When developing or enhancing this codebase, always verify compliance with our 15 Pillars:

1. **SDK Native Compliance**: Use official SDKs, never custom HTTP calls
2. **No Hard-Coding**: Externalize all configuration via environment variables
3. **Domain Agnostic**: Design works for any business domain
4. **Memory & Explainability**: Comprehensive logging and fallback systems
5. **Production Ready**: Proper error handling and graceful degradation
6. **Real Tool Usage**: Agents use actual tools, not mock implementations
7. **Goal-Driven**: All features support goal achievement and tracking
8. **User Visibility**: Clear feedback and transparent operations
9. **No Placeholders**: Zero TODO, FIXME, lorem ipsum, or mock content
10. **Shared Resources**: Efficient resource usage, avoid duplication
11. **Multi-Tenant**: Support multiple workspaces and users
12. **Multi-Language**: Support international deployment
13. **Quality Assurance**: AI-driven quality enhancement
14. **Autonomous Recovery**: Self-healing systems without human intervention
15. **Cost Efficiency**: Optimize API costs and resource usage

### Document Access Architecture Pattern

#### **Level 1: Conversational Document Access**
- **Purpose**: Chat interface with document RAG capabilities
- **Implementation**: OpenAI Assistants API with vector stores
- **Files**: `backend/ai_agents/conversational_assistant.py`

#### **Level 2: Specialist Agent Document Access**
- **Purpose**: Task-executing agents access workspace documents
- **Implementation**: Shared assistant pattern for cost efficiency
- **Files**: `backend/services/shared_document_manager.py`, `backend/ai_agents/specialist.py`

## 🔧 Development Best Practices

### Sub-Agent Quality Gates Pattern
When implementing major features, use this orchestration pattern:

```python
# Use director to orchestrate quality verification
def verify_implementation():
    director_task = {
        "description": "Verify implementation quality",
        "subagent_sequence": [
            "principles-guardian",  # 15 Pillars compliance
            "placeholder-police",   # No development artifacts
            "system-architect",     # Architecture consistency
            "db-steward",          # Database integrity
            "api-contract-guardian", # API compatibility
        ]
    }
    return orchestrate_sub_agents(director_task)
```

### Code Quality Checklist
Before any major deployment, verify:

- [ ] ✅ **SDK Native**: No `requests`, `urllib`, `httpx`, `aiohttp` for API calls
- [ ] ✅ **Configuration**: All settings in environment variables or config files
- [ ] ✅ **Error Handling**: Comprehensive try-catch blocks with fallbacks
- [ ] ✅ **Logging**: Clear status indicators (✅, ⚠️, ❌) for all operations
- [ ] ✅ **Testing**: Integration tests cover all critical paths
- [ ] ✅ **Documentation**: CLAUDE.md updated with new features
- [ ] ✅ **No Placeholders**: Grep search for TODO, FIXME, lorem ipsum returns empty

### Shared Resource Pattern
Always prefer shared resources over individual resources:

```python
# ✅ GOOD: Shared assistant per workspace
workspace_assistant = get_shared_assistant(workspace_id)

# ❌ BAD: Individual assistant per agent
agent_assistant = create_new_assistant(agent_id)
```

## 📁 Critical File Structure

### Backend Architecture
```
backend/
├── services/
│   ├── shared_document_manager.py      # Level 2 document access
│   ├── openai_assistant_manager.py     # OpenAI SDK wrapper
│   └── thinking_process.py             # Real-time thinking
├── ai_agents/
│   ├── specialist.py                   # Enhanced with document access
│   ├── conversational_assistant.py     # Level 1 document access
│   └── director.py                     # Team orchestration
├── migrations/
│   └── 019_add_specialist_assistants_support.sql
└── config/
    └── agent_system_config.py          # Centralized configuration
```

### Frontend Architecture
```
frontend/src/
├── components/
│   ├── conversational/
│   │   ├── ConversationalWorkspace.tsx # Main chat interface
│   │   ├── ArtifactsPanel.tsx          # Documents section
│   │   └── ThinkingProcessViewer.tsx   # Real-time thinking
│   └── assets/
│       └── AssetHistoryPanel.tsx       # Document history
├── hooks/
│   ├── useConversationalWorkspace.ts   # Progressive loading
│   └── useGoalThinking.ts              # Thinking integration
└── types/
    └── goal-progress.ts                # TypeScript definitions
```

## 🎨 Implementation Patterns

### OpenAI Assistants Integration
Always use the native SDK pattern:

```python
# ✅ CORRECT: Native SDK usage
from services.openai_assistant_manager import OpenAIAssistantManager

async def create_document_assistant(workspace_id: str, config: dict):
    assistant_manager = OpenAIAssistantManager()
    
    # Use native SDK methods
    assistant = await assistant_manager.client.beta.assistants.create(
        name=f"Workspace Assistant {workspace_id}",
        instructions=config.get("instructions"),
        model="gpt-4-1106-preview",
        tools=[{"type": "file_search"}]
    )
    
    return assistant.id
```

### Document Search Pattern
Implement document search with proper error handling:

```python
async def search_workspace_documents(self, workspace_id: str, agent_id: str, query: str):
    try:
        # Get shared assistant
        assistant_id = await self.get_specialist_assistant_id(workspace_id, agent_id)
        if not assistant_id:
            logger.warning("No assistant found for document search")
            return []
        
        # Create thread for search
        thread = await self.assistant_manager.client.beta.threads.create()
        
        # Add query message
        await self.assistant_manager.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Run assistant
        run = await self.assistant_manager.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Wait for completion and return results
        return await self._wait_for_completion(thread.id, run.id)
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return []  # Graceful degradation
```

### Memory Fallback Pattern
Always implement fallback storage for development:

```python
class SharedDocumentManager:
    def __init__(self):
        self._memory_storage = {}  # Fallback storage
        
    async def _store_specialist_assistant_mapping(self, workspace_id: str, agent_id: str, assistant_id: str):
        try:
            # Try database first
            await self.supabase.table("specialist_assistants").insert({
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "assistant_id": assistant_id
            }).execute()
        except Exception as e:
            # Fallback to memory storage
            key = f"{workspace_id}:{agent_id}"
            self._memory_storage[key] = assistant_id
            logger.info(f"✅ Using memory fallback for assistant mapping: {key}")
```

## 🧪 Testing Patterns

### Integration Testing Structure
Create comprehensive integration tests:

```python
# test_level2_integration.py
async def test_specialist_document_access():
    """Test complete document access workflow"""
    
    # 1. Setup test data
    workspace_id = "test-workspace"
    agent_id = "test-agent"
    agent_config = {
        "role": "business-analyst",
        "skills": ["analysis", "research"],
        "seniority": "senior"
    }
    
    # 2. Test assistant creation
    assistant_id = await shared_document_manager.create_specialist_assistant(
        workspace_id, agent_id, agent_config
    )
    assert assistant_id, "Assistant creation failed"
    
    # 3. Test document search
    results = await shared_document_manager.search_workspace_documents(
        workspace_id, agent_id, "business framework"
    )
    assert isinstance(results, list), "Document search should return list"
    
    # 4. Test specialist agent integration
    specialist = SpecialistAgent(create_test_agent_model())
    has_access = specialist.has_document_access()
    assert has_access, "Specialist should have document access"
```

### Verification Script Pattern
Create production verification scripts:

```python
#!/usr/bin/env python3
def verify_implementation():
    """Comprehensive verification of implementation"""
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Service Integration", test_service_integration),
        ("Production Readiness", test_production_readiness),
        ("Performance", test_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: PASS")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAIL - {e}")
    
    return all(result for _, result in results)
```

## 📊 Performance Optimization

### Progressive Loading Pattern
Implement staged loading for better UX:

```typescript
// Progressive loading hook pattern
const useProgressiveWorkspaceLoading = (workspaceId: string) => {
  const [phase1Loading, setPhase1Loading] = useState(true)
  const [phase2Loading, setPhase2Loading] = useState(false)
  const [phase3Loading, setPhase3Loading] = useState(false)
  
  useEffect(() => {
    // Phase 1: Essential data (workspace, team)
    loadEssentialData().then(() => {
      setPhase1Loading(false)
      
      // Phase 2: Enhanced data (goals, chats)
      setTimeout(() => {
        setPhase2Loading(true)
        loadEnhancedData().then(() => setPhase2Loading(false))
      }, 50)
    })
  }, [workspaceId])
  
  return { phase1Loading, phase2Loading, phase3Loading, loadPhase3 }
}
```

### API Optimization Pattern
Avoid blocking heavy operations:

```python
# ✅ GOOD: Background loading
@app.get("/api/workspace/{workspace_id}")
async def get_workspace(workspace_id: str):
    # Return essential data immediately
    essential_data = await get_essential_workspace_data(workspace_id)
    
    # Queue heavy operations for background
    background_tasks.add_task(load_full_assets, workspace_id)
    
    return essential_data

# ❌ BAD: Blocking operation
@app.get("/api/workspace/{workspace_id}")
async def get_workspace_blocking(workspace_id: str):
    # This blocks for 90+ seconds
    full_data = await get_all_workspace_data_including_heavy_assets(workspace_id)
    return full_data
```

## 🔒 Security Guidelines

### Environment Variables
Always externalize sensitive configuration:

```python
# config/security_config.py
class SecurityConfig:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL") 
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Timeouts and limits
    ASSISTANT_OPERATION_TIMEOUT = int(os.getenv("ASSISTANT_OPERATION_TIMEOUT", "30"))
    MAX_DOCUMENT_SEARCH_RESULTS = int(os.getenv("MAX_DOCUMENT_SEARCH_RESULTS", "10"))
```

### Rate Limiting Pattern
Implement proper rate limiting:

```python
from services.rate_limiter import RateLimiter

async def search_documents(self, query: str):
    # Acquire rate limit permit
    async with RateLimiter("document_search", max_requests=10, window=60):
        return await self._perform_document_search(query)
```

## 🚀 Deployment Checklist

### Pre-Deployment Verification
Run this checklist before any deployment:

```bash
# 1. Quality gate verification
python3 verify_level2_implementation.py

# 2. Integration tests
python3 -m pytest test_specialist_document_access.py -v

# 3. Security scan
grep -r "TODO\|FIXME\|XXX\|password\|secret\|key.*=" backend/services/
grep -r "localhost\|127.0.0.1\|hardcoded" backend/services/

# 4. Performance tests
curl -w "@curl-format.txt" -s -o /dev/null "http://localhost:8000/api/workspaces/test"

# 5. Database migration
python3 run_migrations.py --dry-run
```

### Production Environment Setup
Ensure these variables are configured:

```bash
# Required
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Optional (with sensible defaults)
ENABLE_SPECIALIST_DOCUMENT_ACCESS=true
SHARED_ASSISTANT_TIMEOUT=30
MAX_DOCUMENT_SEARCH_RESULTS=10
ASSISTANT_OPERATION_TIMEOUT=30
```

## 📈 Monitoring and Observability

### Logging Standards
Use consistent logging patterns:

```python
import logging
logger = logging.getLogger(__name__)

# Success operations
logger.info("✅ Operation completed successfully: {details}")

# Warnings (non-blocking issues)
logger.warning("⚠️ Fallback mechanism used: {details}")

# Errors (but handled gracefully)
logger.error("❌ Operation failed, using fallback: {details}")

# Debug information
logger.debug("🔍 Debug info: {details}")
```

### Performance Monitoring
Track these key metrics:

```python
import time
from contextlib import contextmanager

@contextmanager
def performance_timer(operation_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"⏱️ {operation_name} completed in {duration:.2f}s")

# Usage
async def search_documents(self, query: str):
    with performance_timer("document_search"):
        return await self._perform_search(query)
```

## 🎯 Future Development Guidelines

### When Adding New Features
1. **Design Review**: Ensure alignment with 15 Pillars
2. **Architecture Consistency**: Follow shared resource patterns
3. **Error Handling**: Implement graceful degradation
4. **Testing**: Create integration tests and verification scripts
5. **Documentation**: Update CLAUDE.md and relevant guides
6. **Sub-Agent Review**: Use director-orchestrated quality gates

### When Debugging Issues
1. **Check Logs**: Look for ✅, ⚠️, ❌ indicators
2. **Verify Configuration**: Ensure environment variables are set
3. **Test Fallbacks**: Verify memory fallback systems work
4. **Run Verification Scripts**: Use existing diagnostic tools
5. **Progressive Loading**: Check if heavy operations are blocking UI

### When Optimizing Performance
1. **Identify Bottlenecks**: Use performance monitoring
2. **Progressive Enhancement**: Load essential data first
3. **Background Processing**: Move heavy operations off critical path
4. **Caching Strategy**: Leverage OpenAI's vector store caching
5. **Resource Sharing**: Use shared assistants and services

## 📚 Additional Resources

### Key Documentation Files
- **`CLAUDE.md`**: Main project documentation and configuration
- **`backend/LEVEL2_QUALITY_GATE_REPORT.md`**: Latest quality verification
- **`docs/GOAL_PROGRESS_TRANSPARENCY_SYSTEM.md`**: Goal tracking implementation
- **`backend/migrations/`**: Database schema evolution

### Critical Codebase Files
- **`backend/services/shared_document_manager.py`**: Level 2 document access
- **`backend/ai_agents/specialist.py`**: Enhanced specialist agents
- **`frontend/src/hooks/useConversationalWorkspace.ts`**: Progressive loading
- **`backend/verify_level2_implementation.py`**: Production verification

### Testing and Verification
- **`backend/test_specialist_document_access.py`**: Integration testing
- **`backend/config/agent_system_config.py`**: Configuration management
- **`.claude/agents/`**: Sub-agent configurations for quality gates

---

**Last Updated**: September 2025  
**Next Review**: When adding major architectural changes  
**Quality Standard**: All implementations must pass director-orchestrated quality gates