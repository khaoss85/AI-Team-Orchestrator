# Legacy Learning System Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the legacy task-based learning system to the new Content-Aware Learning System. The migration transforms generic project statistics into domain-specific business intelligence while maintaining backward compatibility.

## Migration Overview

### Legacy System (Before)
- **Focus**: Task execution metadata and generic statistics
- **Insights**: "11 of 11 deliverables completed (100% completion rate)"
- **Analysis**: Task success/failure patterns, agent performance, timing patterns
- **Storage**: Generic `workspace_insights` table entries
- **Application**: Limited task context enhancement

### New System (After)  
- **Focus**: Deliverable content analysis and business intelligence
- **Insights**: "Carousel posts get 25% higher engagement than single images"
- **Analysis**: Domain-specific patterns, quantifiable business metrics
- **Storage**: Enhanced insights with business value scoring and domain categorization
- **Application**: Memory-enhanced task execution with domain expertise

## Migration Strategy

### Phase 1: Parallel Operation (Recommended)

Run both systems simultaneously to ensure data integrity and smooth transition:

```python
# Environment configuration for parallel operation
ENABLE_LEGACY_LEARNING=true                    # Keep legacy system active
ENABLE_CONTENT_AWARE_LEARNING=true            # Enable new system
MIGRATION_MODE=parallel                       # Run both systems
COMPARE_LEARNING_SYSTEMS=true                 # Generate comparison reports
```

### Phase 2: Gradual Transition  

Gradually shift from legacy to new system over a defined period:

```python
# Transition configuration
LEGACY_LEARNING_WEIGHT=0.3                   # 30% legacy, 70% new
CONTENT_LEARNING_WEIGHT=0.7
MIGRATION_TRANSITION_DAYS=30                 # 30-day transition period
```

### Phase 3: Full Migration

Complete transition to Content-Aware Learning System:

```python
# Full migration configuration
ENABLE_LEGACY_LEARNING=false                 # Disable legacy system
ENABLE_CONTENT_AWARE_LEARNING=true          # Full new system
MIGRATE_LEGACY_INSIGHTS=true                # Convert existing insights
```

## Data Migration Process

### Step 1: Analyze Existing Insights

First, analyze your current insight database to understand migration scope:

```python
# Migration analysis script
async def analyze_legacy_insights(workspace_id: str) -> Dict[str, Any]:
    """Analyze existing insights for migration planning"""
    
    # Get all existing insights
    legacy_insights = await get_memory_insights(workspace_id, limit=1000)
    
    analysis = {
        "total_insights": len(legacy_insights),
        "insight_types": defaultdict(int),
        "migration_candidates": [],
        "non_migratable": [],
        "business_value_potential": 0
    }
    
    for insight in legacy_insights:
        insight_type = insight.get('insight_type', 'unknown')
        analysis["insight_types"][insight_type] += 1
        
        # Identify insights with business value potential
        content = insight.get('content', '')
        if any(keyword in content.lower() for keyword in 
               ['rate', '%', 'performance', 'improvement', 'increase', 'decrease']):
            analysis["migration_candidates"].append(insight)
            analysis["business_value_potential"] += 1
        else:
            analysis["non_migratable"].append(insight)
    
    return analysis
```

### Step 2: Legacy Insight Conversion

Convert existing insights to new format where possible:

```python
async def convert_legacy_insight(legacy_insight: Dict[str, Any]) -> Optional[BusinessInsight]:
    """Convert legacy insight to BusinessInsight format"""
    
    try:
        content = legacy_insight.get('content', '')
        
        # Parse content for business metrics
        if isinstance(content, str):
            content_data = json.loads(content) if content.startswith('{') else {'text': content}
        else:
            content_data = content
        
        # Extract quantifiable metrics using AI
        prompt = f"""Analyze this legacy learning insight and extract business metrics if present:

{json.dumps(content_data, indent=2)}

If this contains quantifiable business metrics, extract:
1. The metric name and value
2. Business domain (instagram_marketing, email_marketing, etc.)
3. Actionable recommendation
4. Confidence level (0.1-1.0)

Return JSON format or null if no business metrics found:
{{
    "has_business_value": true/false,
    "domain": "domain_name",
    "metric_name": "metric_name", 
    "metric_value": numeric_value,
    "recommendation": "actionable_text",
    "confidence": 0.0-1.0
}}"""

        agent = {
            "name": "LegacyInsightAnalyzer",
            "model": "gpt-4o-mini",
            "instructions": "Extract business value from legacy learning insights."
        }
        
        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=agent,
            prompt=prompt,
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        if response and response.get('has_business_value'):
            # Create BusinessInsight from legacy data
            domain = DomainType(response.get('domain', 'general'))
            
            business_insight = BusinessInsight(
                insight_type="migrated_legacy_insight",
                domain=domain,
                metric_name=response.get('metric_name'),
                metric_value=response.get('metric_value'),
                actionable_recommendation=response.get('recommendation', ''),
                confidence_score=response.get('confidence', 0.5),
                evidence_sources=[legacy_insight.get('id', '')],
                extraction_method="legacy_migration"
            )
            
            return business_insight
        
        return None
        
    except Exception as e:
        logger.error(f"Error converting legacy insight: {e}")
        return None
```

### Step 3: Database Migration

Migrate insights while preserving data integrity:

```python
async def migrate_workspace_insights(workspace_id: str) -> Dict[str, Any]:
    """Migrate legacy insights to new content-aware format"""
    
    migration_result = {
        "workspace_id": workspace_id,
        "legacy_insights_processed": 0,
        "successfully_migrated": 0,
        "migration_failures": 0,
        "new_insights_generated": 0,
        "migration_timestamp": datetime.now().isoformat()
    }
    
    try:
        # Get legacy insights
        legacy_insights = await get_memory_insights(workspace_id, limit=1000)
        migration_result["legacy_insights_processed"] = len(legacy_insights)
        
        # Convert each legacy insight
        for legacy_insight in legacy_insights:
            try:
                business_insight = await convert_legacy_insight(legacy_insight)
                
                if business_insight:
                    # Store in new format
                    success = await content_aware_learning_engine._store_insight(
                        workspace_id, business_insight
                    )
                    
                    if success:
                        migration_result["successfully_migrated"] += 1
                        
                        # Mark original as migrated (don't delete, preserve for rollback)
                        await mark_insight_migrated(legacy_insight.get('id'))
                    else:
                        migration_result["migration_failures"] += 1
                else:
                    # Legacy insight has no business value, keep as-is
                    continue
                    
            except Exception as e:
                logger.error(f"Error migrating insight {legacy_insight.get('id')}: {e}")
                migration_result["migration_failures"] += 1
        
        # Run new content analysis to generate additional insights
        if migration_result["successfully_migrated"] > 0:
            content_analysis = await content_aware_learning_engine.analyze_workspace_content(workspace_id)
            migration_result["new_insights_generated"] = content_analysis.get("insights_generated", 0)
        
        logger.info(f"✅ Migration completed for workspace {workspace_id}: "
                   f"{migration_result['successfully_migrated']} migrated, "
                   f"{migration_result['new_insights_generated']} new insights")
        
        return migration_result
        
    except Exception as e:
        logger.error(f"Error during workspace migration: {e}")
        migration_result["error"] = str(e)
        return migration_result

async def mark_insight_migrated(insight_id: str) -> bool:
    """Mark legacy insight as migrated without deleting"""
    try:
        supabase = get_supabase_client()
        
        # Update metadata to mark as migrated
        result = supabase.table('workspace_insights').update({
            'metadata': supabase.rpc('jsonb_set', {
                'target': supabase.table('workspace_insights').select('metadata').eq('id', insight_id),
                'path': '{migrated}',
                'new_value': 'true'
            }),
            'updated_at': datetime.now().isoformat()
        }).eq('id', insight_id).execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        logger.error(f"Error marking insight as migrated: {e}")
        return False
```

### Step 4: API Integration Migration

Update API calls to use new endpoints:

```python
# Legacy API calls (deprecated)
# GET /api/learning/insights/{workspace_id}
# POST /api/learning/analyze/{workspace_id}

# New API calls (recommended)  
# GET /api/content-learning/insights/{workspace_id}
# POST /api/content-learning/analyze/{workspace_id}
# GET /api/content-learning/comparison/{workspace_id}  # Compare systems
```

**Frontend Migration Example:**
```typescript
// Legacy frontend integration
const legacyInsights = await api.get(`/learning/insights/${workspaceId}`);

// New frontend integration  
const contentInsights = await api.get(`/content-learning/insights/${workspaceId}`);

// Parallel operation during migration
const [legacyData, newData] = await Promise.all([
    api.get(`/learning/insights/${workspaceId}`),
    api.get(`/content-learning/insights/${workspaceId}`)
]);

// Combine insights during transition
const combinedInsights = [
    ...legacyData.insights.map(i => ({...i, source: 'legacy'})),
    ...newData.actionable_insights.map(i => ({...i, source: 'content_aware'}))
];
```

## Migration Configuration

### Environment Variables

```bash
# Migration Control
MIGRATION_MODE=parallel                       # parallel, transition, complete
ENABLE_LEGACY_LEARNING=true                  # Keep legacy during migration
ENABLE_CONTENT_AWARE_LEARNING=true          # Enable new system
MIGRATE_LEGACY_INSIGHTS=true                # Auto-convert existing insights

# Migration Parameters
MIGRATION_BATCH_SIZE=50                      # Insights per migration batch
MIGRATION_DELAY_SECONDS=1                    # Delay between batches
LEGACY_INSIGHT_RETENTION_DAYS=90            # Keep legacy insights for rollback

# Quality Filters
MIGRATION_MIN_CONFIDENCE=0.5                # Minimum confidence for migration
MIGRATION_BUSINESS_VALUE_THRESHOLD=0.3      # Minimum business value score
SKIP_GENERIC_INSIGHTS=true                  # Skip purely generic insights

# Performance Settings
MIGRATION_PARALLEL_WORKERS=3                # Concurrent migration workers
MIGRATION_TIMEOUT_SECONDS=300               # Timeout per workspace migration
MIGRATION_RETRY_ATTEMPTS=3                  # Retry failed migrations
```

### Migration Modes

```python
class MigrationMode(str, Enum):
    PARALLEL = "parallel"        # Run both systems simultaneously
    TRANSITION = "transition"    # Gradual weight shift
    COMPLETE = "complete"        # Full migration to new system
    ROLLBACK = "rollback"        # Revert to legacy system
```

## Migration Tools and Scripts

### Migration Command Line Tool

```python
# migration_tool.py
import asyncio
import click

@click.group()
def migration():
    """Content-Aware Learning Migration Tool"""
    pass

@migration.command()
@click.option('--workspace-id', required=True, help='Workspace ID to migrate')
@click.option('--dry-run', is_flag=True, help='Preview migration without changes')
def migrate_workspace(workspace_id: str, dry_run: bool):
    """Migrate a single workspace to content-aware learning"""
    asyncio.run(migrate_single_workspace(workspace_id, dry_run))

@migration.command() 
def migrate_all():
    """Migrate all workspaces to content-aware learning"""
    asyncio.run(migrate_all_workspaces())

@migration.command()
@click.option('--workspace-id', required=True, help='Workspace ID to analyze')
def analyze_migration(workspace_id: str):
    """Analyze migration potential for a workspace"""
    asyncio.run(analyze_workspace_migration(workspace_id))

@migration.command()
@click.option('--workspace-id', required=True, help='Workspace ID to compare')
def compare_systems(workspace_id: str):
    """Compare legacy vs content-aware insights"""
    asyncio.run(compare_learning_systems(workspace_id))

if __name__ == '__main__':
    migration()
```

### Migration Status Dashboard

```python
async def get_migration_status() -> Dict[str, Any]:
    """Get overall migration status across all workspaces"""
    
    try:
        supabase = get_supabase_client()
        
        # Get workspace statistics
        workspaces_result = supabase.table('workspaces').select('id, name').execute()
        total_workspaces = len(workspaces_result.data)
        
        # Check migration status for each workspace
        migration_stats = {
            "total_workspaces": total_workspaces,
            "fully_migrated": 0,
            "partially_migrated": 0,
            "not_migrated": 0,
            "migration_in_progress": 0,
            "migration_errors": 0,
            "business_insights_generated": 0,
            "legacy_insights_preserved": 0
        }
        
        for workspace in workspaces_result.data:
            workspace_id = workspace['id']
            
            # Check for content-aware insights
            content_insights = await get_memory_insights(
                workspace_id, 
                insight_type="business_learning",
                limit=1
            )
            
            # Check for legacy insights
            legacy_insights = await get_memory_insights(
                workspace_id,
                insight_type=["success_pattern", "failure_lesson", "agent_performance_insight"],
                limit=1
            )
            
            if content_insights and not legacy_insights:
                migration_stats["fully_migrated"] += 1
            elif content_insights and legacy_insights:
                migration_stats["partially_migrated"] += 1
            elif not content_insights and legacy_insights:
                migration_stats["not_migrated"] += 1
            else:
                migration_stats["migration_errors"] += 1
        
        # Get total insight counts
        all_content_insights = await supabase.table('workspace_insights')\
            .select('*')\
            .eq('insight_type', 'business_learning')\
            .execute()
        
        migration_stats["business_insights_generated"] = len(all_content_insights.data)
        
        return migration_stats
        
    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        return {"error": str(e)}
```

## Rollback Strategy

### Rollback Planning

```python
async def create_migration_rollback_point(workspace_id: str) -> str:
    """Create rollback point before migration"""
    
    try:
        rollback_id = str(uuid4())
        
        # Backup current insights
        current_insights = await get_memory_insights(workspace_id, limit=1000)
        
        # Store rollback data
        rollback_data = {
            "rollback_id": rollback_id,
            "workspace_id": workspace_id,
            "created_at": datetime.now().isoformat(),
            "insights_backup": current_insights,
            "migration_config": get_migration_config()
        }
        
        # Store rollback point
        supabase = get_supabase_client()
        supabase.table('migration_rollbacks').insert({
            "id": rollback_id,
            "workspace_id": workspace_id,
            "backup_data": json.dumps(rollback_data),
            "created_at": datetime.now().isoformat()
        }).execute()
        
        logger.info(f"✅ Created rollback point {rollback_id} for workspace {workspace_id}")
        return rollback_id
        
    except Exception as e:
        logger.error(f"Error creating rollback point: {e}")
        raise

async def execute_rollback(rollback_id: str) -> bool:
    """Execute rollback to previous state"""
    
    try:
        supabase = get_supabase_client()
        
        # Get rollback data
        rollback_result = supabase.table('migration_rollbacks')\
            .select('*')\
            .eq('id', rollback_id)\
            .single()\
            .execute()
        
        if not rollback_result.data:
            raise Exception(f"Rollback point {rollback_id} not found")
        
        rollback_data = json.loads(rollback_result.data['backup_data'])
        workspace_id = rollback_data['workspace_id']
        
        # Delete migrated insights
        await delete_content_insights(workspace_id)
        
        # Restore legacy insights
        for insight in rollback_data['insights_backup']:
            await restore_legacy_insight(insight)
        
        logger.info(f"✅ Successfully rolled back workspace {workspace_id} to rollback point {rollback_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error executing rollback: {e}")
        return False
```

## Validation and Testing

### Migration Validation Tests

```python
class TestMigrationValidation:
    
    async def test_data_integrity_preservation(self):
        """Ensure no data loss during migration"""
        workspace_id = "test-workspace"
        
        # Get original insight count
        original_insights = await get_memory_insights(workspace_id, limit=1000)
        original_count = len(original_insights)
        
        # Run migration
        migration_result = await migrate_workspace_insights(workspace_id)
        
        # Verify data preservation
        post_migration_insights = await get_memory_insights(workspace_id, limit=1000)
        
        # Should have at least same number of insights (migration + legacy preserved)
        assert len(post_migration_insights) >= original_count
        assert migration_result["migration_failures"] == 0
    
    async def test_business_value_improvement(self):
        """Verify migration improves business value of insights"""
        workspace_id = "test-workspace"
        
        # Analyze before migration
        pre_analysis = await analyze_legacy_insights(workspace_id)
        
        # Run migration
        await migrate_workspace_insights(workspace_id)
        
        # Analyze after migration  
        content_insights = await content_aware_learning_engine.get_actionable_learnings(workspace_id)
        
        # Should have more actionable, quantified insights
        actionable_count = len([i for i in content_insights if any(
            keyword in i.lower() for keyword in ['%', 'increase', 'improve', 'rate']
        )])
        
        assert actionable_count > pre_analysis["business_value_potential"]
    
    async def test_rollback_capability(self):
        """Verify rollback restores original state"""
        workspace_id = "test-workspace"
        
        # Create rollback point
        rollback_id = await create_migration_rollback_point(workspace_id)
        
        # Run migration
        await migrate_workspace_insights(workspace_id)
        
        # Execute rollback
        rollback_success = await execute_rollback(rollback_id)
        
        assert rollback_success
        
        # Verify restoration
        restored_insights = await get_memory_insights(workspace_id, limit=1000)
        # Should match pre-migration state
```

### Performance Impact Testing

```python
async def test_migration_performance_impact():
    """Test performance impact of migration"""
    
    import time
    
    # Test legacy system performance
    start_time = time.time()
    legacy_result = await learning_feedback_engine.analyze_workspace_performance("test-workspace")
    legacy_time = time.time() - start_time
    
    # Test new system performance  
    start_time = time.time()
    content_result = await content_aware_learning_engine.analyze_workspace_content("test-workspace")
    content_time = time.time() - start_time
    
    # Performance comparison
    print(f"Legacy analysis: {legacy_time:.2f}s")
    print(f"Content analysis: {content_time:.2f}s")
    print(f"Performance ratio: {content_time/legacy_time:.2f}x")
    
    # New system should provide more insights even if slower
    assert content_result.get("insights_generated", 0) >= legacy_result.get("insights_generated", 0)
```

## Migration Timeline

### Recommended Migration Schedule

**Week 1: Preparation**
- [ ] Enable parallel operation mode
- [ ] Create rollback points for all workspaces
- [ ] Run migration analysis for key workspaces
- [ ] Test migration on development environments

**Week 2: Pilot Migration**
- [ ] Migrate 5-10 pilot workspaces
- [ ] Monitor performance and quality
- [ ] Gather user feedback
- [ ] Refine migration scripts

**Week 3: Gradual Rollout**
- [ ] Migrate 25% of workspaces
- [ ] Compare system performance
- [ ] Address any issues identified
- [ ] Document lessons learned

**Week 4: Full Migration**
- [ ] Migrate remaining workspaces
- [ ] Disable legacy system
- [ ] Clean up migration infrastructure
- [ ] Archive rollback points (after 30 days)

## Success Criteria

### Migration Success Metrics

**Data Integrity:**
- [ ] Zero data loss during migration
- [ ] 100% workspace migration completion
- [ ] Successful rollback capability verified

**Business Value:**
- [ ] 3x increase in actionable insights per workspace
- [ ] 50%+ insights contain quantifiable metrics
- [ ] 80%+ insights provide specific recommendations

**Performance:**
- [ ] System response time within 2x of legacy
- [ ] No degradation in user experience
- [ ] Improved quality of insights generated

**User Adoption:**
- [ ] 90%+ positive feedback on new insights
- [ ] Increased engagement with learning recommendations
- [ ] Measurable improvement in task execution quality

This migration guide ensures a smooth transition from the legacy learning system to the advanced Content-Aware Learning System while preserving data integrity and maximizing business value.