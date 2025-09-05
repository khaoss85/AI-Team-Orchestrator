# OpenAI Quota Tracking Coverage Analysis

## Critical Finding: 24+ Files Bypassing Quota Tracking

### Summary
We have discovered that **24+ critical backend files** are directly instantiating OpenAI clients, completely bypassing our quota tracking system. Additionally, multiple OpenAI API methods (embeddings, assistants, threads, images) are being used but NOT tracked.

### Impact
- **0 tracking** for 24+ files worth of OpenAI API calls
- **Missing methods**: embeddings, assistants, threads, images, files, audio
- **Budget monitoring broken**: Users see incorrect usage data
- **Rate limiting ineffective**: System can hit OpenAI limits unexpectedly

### Files with Direct Instantiation (Partial List)
- backend/services/document_manager.py
- backend/services/ai_task_execution_classifier.py  
- backend/services/workspace_cleanup_service.py
- backend/ai_agents/conversational.py
- backend/ai_agents/director.py
- backend/utils/ai_utils.py
- backend/tools/openai_sdk_tools.py

### Untracked API Methods in Use
- embeddings.create (semantic_domain_memory.py)
- assistants.create (openai_assistant_manager.py)
- threads.create (specialist.py)
- images.generate (openai_sdk_tools.py)
- files.create (document_manager.py)

### Required Analysis
1. How did this violation of Pillar #15 (SDK compliance) occur?
2. What's the full architectural impact?
3. How do we fix ALL instances systematically?
4. How do we prevent future violations?
