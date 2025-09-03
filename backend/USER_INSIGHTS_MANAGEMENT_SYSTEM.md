# User Insights Management System Documentation

## Overview

The User Insights Management System extends the existing AI-driven knowledge categorization system with comprehensive user management capabilities. This hybrid system allows users to manually create, edit, delete, and manage knowledge insights while maintaining seamless integration with AI-generated insights.

## Architecture Components

### 1. Database Layer

#### Schema Extensions (Migration 017)
- **User Management Fields**: Added to `workspace_insights` table
  - `created_by`: User identifier who created the insight
  - `last_modified_by`: Last user to modify the insight
  - `is_user_created`: Boolean flag for user-created insights
  - `is_user_modified`: Boolean flag for modified insights
  - `is_deleted`: Soft delete flag
  - `deleted_at`, `deleted_by`: Deletion tracking
  - `user_flags`: JSONB for verified/important/etc flags
  - `version_number`: Incremented on each modification
  - `parent_insight_id`: Links to previous versions

#### Audit Trail Table
- `insight_audit_trail`: Complete history of all changes
  - Tracks CREATE, UPDATE, DELETE, FLAG, CATEGORIZE actions
  - Stores old and new values for rollback capability
  - Automatic logging via database triggers

#### User Categories Table
- `user_insight_categories`: Custom categories per workspace
  - Hierarchical category support
  - Custom colors and icons
  - Sort ordering

### 2. Backend Services

#### UserInsightManager (`services/user_insight_manager.py`)
Core service managing all user insight operations:

**Key Methods:**
- `create_user_insight()`: Create new user-generated insights
- `update_insight()`: Modify existing insights with versioning
- `delete_insight()`: Soft/hard delete capabilities
- `restore_insight()`: Recover soft-deleted insights
- `flag_insight()`: Mark as verified/important/outdated
- `bulk_operation()`: Batch operations on multiple insights
- `list_insights()`: Advanced filtering and search
- `get_insight_history()`: Full audit trail access
- `undo_last_change()`: Rollback to previous state

**Features:**
- Automatic versioning on modifications
- Comprehensive audit trail logging
- Support for bulk operations
- Soft delete with restoration capability
- Flag management with history tracking

### 3. API Layer

#### RESTful Endpoints (`routes/user_insights.py`)

**CRUD Operations:**
```
POST   /user-insights/{workspace_id}/insights         - Create insight
GET    /user-insights/{workspace_id}/insights         - List insights
GET    /user-insights/insights/{insight_id}          - Get single insight  
PUT    /user-insights/insights/{insight_id}          - Update insight
DELETE /user-insights/insights/{insight_id}          - Delete insight
```

**Special Operations:**
```
POST   /user-insights/insights/{insight_id}/restore  - Restore deleted
PATCH  /user-insights/insights/{insight_id}/category - Re-categorize
POST   /user-insights/insights/{insight_id}/flags    - Add/remove flags
POST   /user-insights/{workspace_id}/insights/bulk   - Bulk operations
GET    /user-insights/insights/{insight_id}/history  - Audit trail
POST   /user-insights/insights/{insight_id}/undo     - Undo last change
```

**Query Parameters:**
- `include_ai`: Include AI-generated insights (default: true)
- `include_user`: Include user-created insights (default: true)
- `include_deleted`: Show soft-deleted insights (default: false)
- `category`: Filter by category
- `flags`: Filter by specific flags
- `search`: Search in title and content
- `limit`, `offset`: Pagination

### 4. Security & Permissions

#### Permission Checks
- **Create**: User must be workspace member
- **Edit**: User must be creator or workspace admin
- **Delete**: User must be creator or workspace admin
- **Flag**: Any workspace member can flag
- **Restore**: Admin or original deleter only

#### Validation
- Input sanitization for all text fields
- Category validation against allowed values
- Metric data structure validation
- Flag type validation

### 5. Frontend Components (Design)

#### Knowledge Base Manager Component
```typescript
interface KnowledgeBaseManagerProps {
  workspaceId: string;
  currentUserId: string;
}
```

**Features:**
- Three-tab interface: All / AI-Generated / User-Created
- Grid/list view toggle
- Bulk selection for operations
- Search and filter controls
- Sort by date/category/flags

#### Insight Card Component
```typescript
interface InsightCardProps {
  insight: UserManagedInsight;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onFlag: (id: string, flag: string) => void;
}
```

**Visual Indicators:**
- Blue border for user-created
- Green background for verified
- Star icon for important
- Badge showing source (AI/User)
- Version number for modified

#### Insight Editor Modal
```typescript
interface InsightEditorModalProps {
  insight?: UserManagedInsight; // Optional for create
  open: boolean;
  onClose: () => void;
  onSave: (data: InsightFormData) => void;
}
```

**Form Fields:**
- Title (required)
- Content (rich text editor)
- Category dropdown
- Domain type selector
- Metrics editor (key-value pairs)
- Recommendations list
- Tags input

### 6. Integration Points

#### With AI System
- **Hybrid Processing**: Merge AI and user insights with deduplication
- **AI Enhancement**: Use AI to add metrics to user insights
- **AI Validation**: Validate user insights for quality
- **Categorization Assistance**: AI suggests categories

#### With Existing Features
- **Workspace Memory**: User insights become part of memory
- **Task Execution**: User insights influence task generation
- **Deliverables**: User insights reflected in outputs
- **Reporting**: Combined AI+User insights in reports

## Usage Examples

### Creating a User Insight

```python
# Backend
insight = await user_insight_manager.create_user_insight(
    workspace_id="workspace-uuid",
    title="Optimal Posting Times for B2B",
    content="B2B audiences show highest engagement 7-9 AM weekdays",
    category="best_practice",
    created_by="user_123",
    domain_type="social_media",
    metrics={
        "engagement_increase": "35%",
        "sample_size": 500
    },
    recommendations=[
        "Schedule posts for 7-9 AM",
        "Focus on Tuesday-Thursday"
    ],
    tags=["b2b", "timing", "engagement"]
)
```

```typescript
// Frontend
const createInsight = async () => {
  const response = await api.post(`/user-insights/${workspaceId}/insights`, {
    title: "Optimal Posting Times for B2B",
    content: "B2B audiences show highest engagement 7-9 AM weekdays",
    category: "best_practice",
    domain_type: "social_media",
    metrics: {
      engagement_increase: "35%",
      sample_size: 500
    },
    recommendations: [
      "Schedule posts for 7-9 AM",
      "Focus on Tuesday-Thursday"
    ],
    tags: ["b2b", "timing", "engagement"]
  });
  return response.data;
};
```

### Updating and Flagging

```python
# Update insight
updated = await user_insight_manager.update_insight(
    insight_id="insight-uuid",
    updates={
        "content": "Updated content with new findings",
        "metrics": {"engagement_increase": "42%"}
    },
    modified_by="user_123"
)

# Flag as verified
flagged = await user_insight_manager.flag_insight(
    insight_id="insight-uuid",
    flag_type="verified",
    flag_value=True,
    flagged_by="user_123"
)
```

### Bulk Operations

```python
# Bulk delete outdated insights
result = await user_insight_manager.bulk_operation(
    insight_ids=["id1", "id2", "id3"],
    operation=BulkOperation.DELETE,
    performed_by="user_123"
)
# Returns: {'succeeded': 3, 'failed': 0, 'total': 3}

# Bulk categorize
result = await user_insight_manager.bulk_operation(
    insight_ids=["id4", "id5"],
    operation=BulkOperation.CATEGORIZE,
    performed_by="user_123",
    operation_data={'category': 'best_practice'}
)
```

### Searching and Filtering

```python
# Find verified best practices
insights, total = await user_insight_manager.list_insights(
    workspace_id="workspace-uuid",
    include_ai=True,
    include_user=True,
    category="best_practice",
    flags=["verified"],
    search_query="engagement",
    limit=20
)
```

## Database Queries

### Useful SQL Queries

```sql
-- Find all user-created insights in a workspace
SELECT * FROM workspace_insights 
WHERE workspace_id = 'workspace-uuid' 
  AND is_user_created = TRUE 
  AND is_deleted = FALSE;

-- Get insights with specific flags
SELECT * FROM workspace_insights 
WHERE workspace_id = 'workspace-uuid'
  AND user_flags->>'verified' = 'true'
  AND user_flags->>'important' = 'true';

-- Track user activity
SELECT 
  performed_by,
  COUNT(*) as action_count,
  array_agg(DISTINCT action) as actions
FROM insight_audit_trail
WHERE workspace_id = 'workspace-uuid'
  AND performed_at > NOW() - INTERVAL '7 days'
GROUP BY performed_by;

-- Find modified insights with original content
SELECT 
  id,
  title,
  created_by,
  last_modified_by,
  version_number,
  original_content IS NOT NULL as has_original
FROM workspace_insights
WHERE is_user_modified = TRUE
  AND is_deleted = FALSE;
```

## Testing

### API Testing with cURL

```bash
# Create insight
curl -X POST "http://localhost:8000/api/user-insights/${WORKSPACE_ID}/insights" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "title": "Test Insight",
    "content": "This is a test insight",
    "category": "general"
  }'

# List insights with filters
curl "http://localhost:8000/api/user-insights/${WORKSPACE_ID}/insights?\
include_ai=false&\
include_user=true&\
category=best_practice&\
limit=10"

# Flag insight as verified
curl -X POST "http://localhost:8000/api/user-insights/insights/${INSIGHT_ID}/flags" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "flag_type": "verified",
    "flag_value": true
  }'

# Bulk delete
curl -X POST "http://localhost:8000/api/user-insights/${WORKSPACE_ID}/insights/bulk" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "insight_ids": ["id1", "id2"],
    "operation": "delete"
  }'
```

### Python Testing

```python
import asyncio
from services.user_insight_manager import user_insight_manager

async def test_crud_operations():
    # Create
    insight = await user_insight_manager.create_user_insight(
        workspace_id="test-workspace",
        title="Test Insight",
        content="Test content",
        category="general",
        created_by="test_user"
    )
    print(f"Created: {insight.id}")
    
    # Update
    updated = await user_insight_manager.update_insight(
        insight_id=insight.id,
        updates={"content": "Updated content"},
        modified_by="test_user"
    )
    print(f"Updated: {updated.version_number}")
    
    # Flag
    flagged = await user_insight_manager.flag_insight(
        insight_id=insight.id,
        flag_type="important",
        flag_value=True,
        flagged_by="test_user"
    )
    print(f"Flagged: {flagged.user_flags}")
    
    # History
    history = await user_insight_manager.get_insight_history(insight.id)
    print(f"History entries: {len(history)}")
    
    # Delete
    deleted = await user_insight_manager.delete_insight(
        insight_id=insight.id,
        deleted_by="test_user"
    )
    print(f"Deleted: {deleted}")

asyncio.run(test_crud_operations())
```

## Maintenance

### Regular Tasks

1. **Clean up old soft-deleted insights** (monthly)
```sql
DELETE FROM workspace_insights 
WHERE is_deleted = TRUE 
  AND deleted_at < NOW() - INTERVAL '90 days';
```

2. **Archive old audit trail entries** (quarterly)
```sql
-- Move to archive table
INSERT INTO insight_audit_trail_archive 
SELECT * FROM insight_audit_trail 
WHERE performed_at < NOW() - INTERVAL '1 year';

-- Delete from main table
DELETE FROM insight_audit_trail 
WHERE performed_at < NOW() - INTERVAL '1 year';
```

3. **Analyze usage patterns** (monthly)
```sql
-- Most active users
SELECT 
  created_by,
  COUNT(*) as insights_created,
  AVG(business_value_score) as avg_value
FROM workspace_insights
WHERE is_user_created = TRUE
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY created_by
ORDER BY insights_created DESC;

-- Most flagged insights
SELECT 
  id,
  title,
  user_flags
FROM workspace_insights
WHERE (user_flags->>'verified')::boolean = TRUE
   OR (user_flags->>'important')::boolean = TRUE
ORDER BY created_at DESC
LIMIT 20;
```

## Performance Considerations

### Indices
The system includes optimized indices for:
- User-created insights filtering
- Flag-based queries (GIN index on JSONB)
- Title search (trigram index)
- Audit trail lookups

### Caching Strategy
- Cache frequently accessed insights in Redis
- Invalidate on updates
- Cache search results for 5 minutes

### Scalability
- Soft delete reduces database writes
- Versioning via parent_insight_id keeps main table clean
- Audit trail in separate table avoids bloat
- Bulk operations reduce API calls

## Compliance with 15 Pillars

✅ **Goal-first**: User insights tied to workspace goals  
✅ **Workspace Memory**: Insights become permanent memory  
✅ **Autonomous Pipeline**: AI can use user insights  
✅ **QA AI-first**: AI validates user-created content  
✅ **Production-ready**: Full CRUD with audit trail  
✅ **No Placeholders**: Real user data, no mocks  
✅ **Course Correction**: User can fix AI mistakes  
✅ **Explainability**: Full history and audit trail  
✅ **Modular Services**: Clean separation of concerns  
✅ **Context-aware**: Insights influence task generation

## Future Enhancements

1. **AI-Assisted Creation**: AI suggests insights from deliverables
2. **Collaboration**: Multiple users can edit with conflict resolution
3. **Export/Import**: Bulk import from CSV/JSON
4. **Templates**: Pre-defined insight templates by domain
5. **Analytics Dashboard**: Insights usage and impact metrics
6. **ML Classification**: Auto-categorize user insights
7. **Version Diff Viewer**: Visual comparison of changes
8. **Approval Workflow**: Review process for critical insights

## Support

For issues or questions:
1. Check audit trail for debugging
2. Review error logs in `/backend/logs/`
3. Use SQL queries to verify data integrity
4. Test with cURL before frontend integration