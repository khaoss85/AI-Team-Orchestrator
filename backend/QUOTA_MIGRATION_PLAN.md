# OpenAI Quota Tracking Migration Plan
**Created**: 2025-09-05  
**Priority**: CRITICAL - System Currently Non-Functional

## Migration Overview

We need to migrate **124 files** with direct OpenAI instantiations to use our quota-tracked factory. Additionally, we must extend tracking to cover **43 untracked API methods**.

## Phase 1: Critical Path Files (29 files - Day 1-2)

### Batch 1: Core AI Agents (EMERGENCY - Day 1 Morning)
These files are preventing ALL AI operations from working:

```bash
# Migration commands for each file:
python3 migrate_openai_client.py ai_agents/director.py
python3 migrate_openai_client.py ai_agents/specialist.py
python3 migrate_openai_client.py ai_agents/conversational.py
python3 migrate_openai_client.py ai_agents/specialist_sdk_complete.py
```

**Changes required**:
```python
# OLD (in director.py line 590)
from openai import AsyncOpenAI
openai_client = AsyncOpenAI()

# NEW
from utils.openai_client_factory import get_async_openai_client
openai_client = get_async_openai_client(workspace_id=workspace_id)
```

### Batch 2: Task Execution (Day 1 Afternoon)
Critical for task processing:

```bash
python3 migrate_openai_client.py executor.py
python3 migrate_openai_client.py task_analyzer.py
python3 migrate_openai_client.py real_task_executor.py
python3 migrate_openai_client.py goal_driven_task_planner.py
python3 migrate_openai_client.py auto_agent_provisioner.py
python3 migrate_openai_client.py AISemanticMapper.py
python3 migrate_openai_client.py ai_driven_task_intent_analyzer.py
```

### Batch 3: Core Services (Day 2 Morning)
Essential service layer:

```bash
python3 migrate_openai_client.py services/enhanced_goal_driven_planner.py
python3 migrate_openai_client.py services/recovery_analysis_engine.py
python3 migrate_openai_client.py services/recovery_explanation_engine.py
python3 migrate_openai_client.py services/constraint_violation_preventer.py
python3 migrate_openai_client.py services/universal_ai_pipeline_engine.py
python3 migrate_openai_client.py services/unified_memory_engine.py
python3 migrate_openai_client.py services/ai_content_display_transformer.py
python3 migrate_openai_client.py services/ai_goal_matcher.py
```

### Batch 4: Support Services (Day 2 Afternoon)
Supporting AI services:

```bash
python3 migrate_openai_client.py services/workspace_cleanup_service.py
python3 migrate_openai_client.py services/document_manager.py
python3 migrate_openai_client.py services/semantic_domain_memory.py
python3 migrate_openai_client.py services/ai_domain_classifier.py
python3 migrate_openai_client.py services/pure_ai_domain_classifier.py
python3 migrate_openai_client.py services/ai_resilient_similarity_engine.py
python3 migrate_openai_client.py services/ai_driven_director_enhancer.py
python3 migrate_openai_client.py services/universal_ai_content_extractor.py
python3 migrate_openai_client.py services/unified_progress_manager.py
python3 migrate_openai_client.py services/ai_task_execution_classifier.py
python3 migrate_openai_client.py services/pdf_content_extractor.py
```

## Migration Script

Create `migrate_openai_client.py`:

```python
#!/usr/bin/env python3
"""
Automated OpenAI client migration script
Replaces direct OpenAI instantiations with quota-tracked factory calls
"""

import sys
import re
from pathlib import Path

def migrate_file(filepath: str) -> bool:
    """Migrate a single file to use quota-tracked clients"""
    file_path = Path(filepath)
    if not file_path.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    content = file_path.read_text()
    original_content = content
    
    # Pattern replacements
    replacements = [
        # Import replacements
        (r'from openai import OpenAI\b', 
         'from utils.openai_client_factory import get_openai_client'),
        (r'from openai import AsyncOpenAI\b',
         'from utils.openai_client_factory import get_async_openai_client'),
        (r'from openai import OpenAI, AsyncOpenAI',
         'from utils.openai_client_factory import get_openai_client, get_async_openai_client'),
        
        # Direct instantiation replacements
        (r'OpenAI\s*\([^)]*\)',
         'get_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        (r'AsyncOpenAI\s*\([^)]*\)',
         'get_async_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        (r'openai\.OpenAI\s*\([^)]*\)',
         'get_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        (r'openai\.AsyncOpenAI\s*\([^)]*\)',
         'get_async_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        
        # Assignment replacements
        (r'(\w+)\s*=\s*OpenAI\s*\([^)]*\)',
         r'\1 = get_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        (r'(\w+)\s*=\s*AsyncOpenAI\s*\([^)]*\)',
         r'\1 = get_async_openai_client(workspace_id=workspace_id if "workspace_id" in locals() else None)'),
        
        # Class attribute replacements
        (r'self\.(\w+)\s*=\s*OpenAI\s*\([^)]*\)',
         r'self.\1 = get_openai_client(workspace_id=getattr(self, "workspace_id", None))'),
        (r'self\.(\w+)\s*=\s*AsyncOpenAI\s*\([^)]*\)',
         r'self.\1 = get_async_openai_client(workspace_id=getattr(self, "workspace_id", None))'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Add import if OpenAI is used but factory isn't imported
    if 'get_openai_client' in content and 'from utils.openai_client_factory import' not in content:
        # Add import after other imports
        import_lines = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(i)
        
        if import_lines:
            last_import_idx = max(import_lines)
            lines.insert(last_import_idx + 1, 'from utils.openai_client_factory import get_openai_client, get_async_openai_client')
            content = '\n'.join(lines)
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Migrated: {filepath}")
        return True
    else:
        print(f"ℹ️ No changes needed: {filepath}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 migrate_openai_client.py <file_path>")
        sys.exit(1)
    
    success = migrate_file(sys.argv[1])
    sys.exit(0 if success else 1)
```

## Phase 2: Extended Method Coverage (Day 3-4)

### Extend Factory for Untracked Methods

Update `openai_client_factory.py` to track:

```python
class QuotaTrackedOpenAI:
    """Extended to track ALL OpenAI API methods"""
    
    def __init__(self, client, workspace_id=None):
        self._client = client
        self._workspace_id = workspace_id
        self._quota_tracker = OpenAIQuotaTracker.get_tracker(workspace_id)
        
        # Wrap all API namespaces
        self.chat = QuotaTrackedChat(client.chat, self._quota_tracker)
        self.embeddings = QuotaTrackedEmbeddings(client.embeddings, self._quota_tracker)
        self.images = QuotaTrackedImages(client.images, self._quota_tracker)
        self.audio = QuotaTrackedAudio(client.audio, self._quota_tracker)
        self.files = QuotaTrackedFiles(client.files, self._quota_tracker)
        self.assistants = QuotaTrackedAssistants(client.assistants, self._quota_tracker)
        self.threads = QuotaTrackedThreads(client.threads, self._quota_tracker)
        self.vector_stores = QuotaTrackedVectorStores(client.vector_stores, self._quota_tracker)
        self.moderations = QuotaTrackedModerations(client.moderations, self._quota_tracker)

class QuotaTrackedEmbeddings:
    """Track embeddings API usage"""
    
    def __init__(self, embeddings_client, tracker):
        self._client = embeddings_client
        self._tracker = tracker
    
    async def create(self, **kwargs):
        model = kwargs.get('model', 'text-embedding-ada-002')
        input_text = kwargs.get('input', '')
        
        # Estimate tokens
        if isinstance(input_text, str):
            estimated_tokens = len(input_text) // 4
        elif isinstance(input_text, list):
            estimated_tokens = sum(len(str(text)) // 4 for text in input_text)
        else:
            estimated_tokens = 100  # Default estimate
        
        try:
            response = await self._client.create(**kwargs)
            
            # Track successful embedding
            await self._tracker.track_request(
                model=model,
                endpoint='embeddings',
                prompt_tokens=estimated_tokens,
                completion_tokens=0,
                total_tokens=estimated_tokens,
                estimated_cost=estimated_tokens * 0.0001 / 1000  # Ada pricing
            )
            
            return response
            
        except Exception as e:
            await self._tracker.track_error(str(e))
            raise

# Similar wrappers for Images, Audio, Files, Assistants, Threads, VectorStores, Moderations
```

## Phase 3: Quality Assurance (Day 5)

### Integration Tests

Create `test_quota_coverage.py`:

```python
import pytest
import asyncio
from unittest.mock import patch, MagicMock

class TestQuotaCoverage:
    """Verify 100% quota tracking coverage"""
    
    @pytest.mark.asyncio
    async def test_all_openai_calls_tracked(self):
        """Ensure no OpenAI calls bypass tracking"""
        
        # Mock OpenAI to detect direct usage
        with patch('openai.OpenAI') as mock_openai:
            with patch('openai.AsyncOpenAI') as mock_async_openai:
                # These should never be called directly
                mock_openai.side_effect = Exception("Direct OpenAI usage detected!")
                mock_async_openai.side_effect = Exception("Direct AsyncOpenAI usage detected!")
                
                # Import all modules to trigger any direct instantiation
                import ai_agents.director
                import ai_agents.specialist
                import services.enhanced_goal_driven_planner
                # ... import all migrated modules
                
                # If we get here, all modules use factory
                assert True
    
    @pytest.mark.asyncio
    async def test_all_api_methods_tracked(self):
        """Verify all API methods are tracked"""
        
        from utils.openai_client_factory import get_async_openai_client
        
        client = get_async_openai_client()
        tracker = client._quota_tracker
        
        # Test all API endpoints
        methods_to_test = [
            ('chat.completions.create', {'model': 'gpt-3.5-turbo', 'messages': []}),
            ('embeddings.create', {'model': 'text-embedding-ada-002', 'input': 'test'}),
            ('images.generate', {'prompt': 'test', 'n': 1}),
            ('audio.transcriptions.create', {'file': b'', 'model': 'whisper-1'}),
            ('files.create', {'file': b'', 'purpose': 'assistants'}),
            # ... all methods
        ]
        
        for method_path, kwargs in methods_to_test:
            # Verify method exists and is wrapped
            method = client
            for part in method_path.split('.'):
                method = getattr(method, part)
            
            assert hasattr(method, '__wrapped__'), f"{method_path} not wrapped for tracking"
```

## Phase 4: Validation & Monitoring (Day 6)

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Prevent direct OpenAI usage from being committed

echo "🔍 Checking for direct OpenAI usage..."

# Check for direct imports
if git diff --cached --name-only | xargs grep -l "from openai import.*OpenAI" | grep -v openai_client_factory; then
    echo "❌ Direct OpenAI imports detected! Use openai_client_factory instead."
    exit 1
fi

# Check for direct instantiation
if git diff --cached --name-only | xargs grep -l "OpenAI()" | grep -v openai_client_factory; then
    echo "❌ Direct OpenAI() instantiation detected! Use get_openai_client() instead."
    exit 1
fi

echo "✅ No direct OpenAI usage detected"
```

### Monitoring Dashboard

Create `monitor_quota_migration.py`:

```python
#!/usr/bin/env python3
"""Real-time migration progress monitor"""

import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live

def check_migration_status():
    """Check current migration status"""
    violations = []
    migrated = []
    
    backend_dir = Path(__file__).parent
    for py_file in backend_dir.rglob("*.py"):
        if py_file.name in ["migrate_openai_client.py", "openai_client_factory.py"]:
            continue
            
        content = py_file.read_text()
        if "from openai import" in content and "openai_client_factory" not in content:
            violations.append(str(py_file))
        elif "openai_client_factory" in content:
            migrated.append(str(py_file))
    
    return violations, migrated

def display_status():
    """Display migration status dashboard"""
    console = Console()
    
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            violations, migrated = check_migration_status()
            
            table = Table(title="OpenAI Migration Status")
            table.add_column("Status", style="cyan")
            table.add_column("Count", style="magenta")
            table.add_column("Progress", style="green")
            
            total = len(violations) + len(migrated)
            progress = len(migrated) / total * 100 if total > 0 else 0
            
            table.add_row("✅ Migrated", str(len(migrated)), f"{progress:.1f}%")
            table.add_row("❌ Pending", str(len(violations)), f"{100-progress:.1f}%")
            table.add_row("📊 Total", str(total), "100%")
            
            if violations:
                table.add_row("", "", "")
                table.add_row("Next Files to Migrate:", "", "")
                for file in violations[:5]:
                    table.add_row("", file, "")
            
            live.update(table)
            time.sleep(5)

if __name__ == "__main__":
    display_status()
```

## Success Criteria

### Day 1 Success:
- [ ] Core AI agents migrated
- [ ] Basic AI operations restored
- [ ] Quota tracking shows activity

### Day 2 Success:
- [ ] All 29 critical files migrated
- [ ] Integration tests passing
- [ ] WebSocket updates working

### Week 1 Success:
- [ ] 100% of files migrated
- [ ] All API methods tracked
- [ ] Real-time monitoring active
- [ ] Alerts configured

### Production Ready:
- [ ] Zero untracked API calls
- [ ] <10ms tracking overhead
- [ ] 99.9% tracking reliability
- [ ] Full cost visibility
- [ ] Predictive quota alerts

## Emergency Fallback Plan

If migration fails or causes issues:

1. **Immediate Rollback**: Git revert to pre-migration state
2. **Quota Override**: Set `DISABLE_QUOTA_TRACKING=true` in .env
3. **Manual Tracking**: Use OpenAI dashboard for cost monitoring
4. **Gradual Migration**: Migrate one service at a time with feature flags

## Timeline

- **Day 1**: Emergency migration of core AI agents
- **Day 2**: Complete Phase 1 (29 files)
- **Day 3-4**: Extend tracking methods
- **Day 5**: Quality assurance & testing
- **Day 6**: Monitoring & validation
- **Week 2**: Phase 2 migration (remaining files)
- **Week 3**: Performance optimization
- **Week 4**: Production deployment

## Resources Required

- 2 engineers full-time for first week
- 1 engineer for weeks 2-4
- Access to OpenAI dashboard for verification
- Test budget for quota testing (~$50)
- Monitoring infrastructure (Grafana/Datadog)

---

**Note**: This migration is CRITICAL. The system is currently non-functional due to quota exhaustion that went undetected. Every day of delay costs money in untracked API usage and degrades user experience.