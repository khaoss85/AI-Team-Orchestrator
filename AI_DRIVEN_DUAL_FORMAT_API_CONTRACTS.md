# 🚀 AI-Driven Dual-Format Architecture API Contracts

**Date:** 2025-08-28  
**Version:** 1.0  
**Author:** Claude Code AI Assistant  

## Overview

This document defines comprehensive API contracts for the AI-Driven Dual-Format Architecture that supports both execution (JSON) and display (user-friendly) formats for deliverables.

## 🎯 Architecture Goals

1. **Dual-Format Support**: Separate execution content (structured JSON) from display content (user-friendly HTML/Markdown)
2. **AI-Powered Transformation**: Automatic conversion from structured data to user-friendly formats
3. **Backward Compatibility**: Existing code continues to work without modifications
4. **Progressive Enhancement**: Enhanced features available when dual-format is supported
5. **Graceful Degradation**: System works even when AI transformation fails

## 📊 Core Models & Contracts

### 1. Enhanced AssetArtifact Model

**Location:** `/backend/models.py`

#### New Fields Added:
```python
# Display format fields
display_content: Optional[str] = None              # AI-transformed display content  
display_format: str = "html"                       # html, markdown, text
display_summary: Optional[str] = None              # Brief summary for UI cards
display_metadata: Dict[str, Any] = {}              # Display-specific metadata

# Transformation tracking
content_transformation_status: str = "pending"     # pending, success, failed
content_transformation_error: Optional[str] = None # Error message if failed
transformation_timestamp: Optional[datetime] = None # When transformation performed
transformation_method: str = "ai"                  # ai, manual, fallback

# Quality metrics
display_quality_score: float = 0.0                # Quality score for display content
user_friendliness_score: float = 0.0              # How user-friendly the display is
readability_score: float = 0.0                    # Text readability score
```

#### Backward Compatibility:
- Existing `content` field remains unchanged
- New fields are optional and default to safe values
- Legacy applications continue to work without modifications

### 2. AIContentDisplayTransformer Service Interface

**Location:** `/backend/models.py`

#### Service Capabilities:
```python
supported_input_formats: ["json", "dict", "text"]
supported_output_formats: ["html", "markdown", "text"]
transformation_capabilities: [
    "structured_data_to_html",
    "json_to_markdown", 
    "content_summarization",
    "user_friendly_formatting",
    "quality_enhancement"
]
```

#### Configuration:
```python
transformation_timeout: 30          # seconds
max_content_length: 50000          # characters
fallback_enabled: True
quality_threshold: 0.6
```

### 3. Enhanced API Response Models

#### EnhancedDeliverableResponse
```python
class EnhancedDeliverableResponse(BaseModel):
    # Core fields
    id: str
    title: str
    type: str
    status: str
    created_at: str
    updated_at: str
    
    # Execution content (for system processing)
    execution_content: Dict[str, Any] = {}
    execution_format: str = "json"
    
    # Display content (for user presentation)
    display_content: Optional[str] = None
    display_format: str = "html"
    display_summary: Optional[str] = None
    display_preview: Optional[str] = None  # First 200 chars for cards
    
    # Quality and transformation metadata
    display_quality_score: float = 0.0
    user_friendliness_score: float = 0.0
    content_transformation_status: str = "pending"
    transformation_error: Optional[str] = None
    
    # User actions
    can_retry_transformation: bool = False
    available_formats: List[str] = ["html"]
    
    # Backward compatibility
    content: Optional[Union[str, Dict[str, Any]]] = None  # DEPRECATED
```

#### DeliverableListResponse
```python
class DeliverableListResponse(BaseModel):
    deliverables: List[EnhancedDeliverableResponse]
    total_count: int
    transformation_status: Dict[str, int]    # pending: 2, success: 5, failed: 1
    quality_overview: Dict[str, float]       # avg_display_quality: 0.8
    
    # Pagination
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False
    
    # System capabilities
    supports_dual_format: bool = True
    available_transformations: List[str] = ["html", "markdown", "text"]
```

### 4. Content Transformation API Contracts

#### Request Model
```python
class ContentTransformationRequest(BaseModel):
    asset_id: UUID
    execution_content: Dict[str, Any]
    content_type: str
    target_format: str = "html"                    # html, markdown, text
    transformation_context: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}
    quality_requirements: Dict[str, str] = {}
```

#### Response Model
```python
class ContentTransformationResponse(BaseModel):
    success: bool
    asset_id: UUID
    display_content: Optional[str] = None
    display_format: str
    display_summary: Optional[str] = None
    display_metadata: Dict[str, Any] = {}
    
    # Quality metrics
    display_quality_score: float = 0.0
    user_friendliness_score: float = 0.0
    readability_score: float = 0.0
    
    # Transformation details
    transformation_method: str = "ai"
    transformation_timestamp: datetime
    ai_confidence: float = 0.0
    
    # Error handling
    error_message: Optional[str] = None
    fallback_used: bool = False
    retry_suggestions: List[str] = []
```

### 5. Batch Processing Contracts

#### Batch Request
```python
class TransformationBatchRequest(BaseModel):
    asset_ids: List[UUID]
    target_format: str = "html"
    priority: str = "normal"                       # low, normal, high
    transformation_context: Dict[str, Any] = {}
```

#### Batch Response
```python
class TransformationBatchResponse(BaseModel):
    batch_id: str
    total_assets: int
    successful_transformations: int
    failed_transformations: int
    pending_transformations: int
    
    results: List[ContentTransformationResponse]
    
    started_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
```

## 🎨 Frontend TypeScript Interfaces

**Location:** `/frontend/src/types/goal-progress.ts`

### Enhanced DeliverableItem Interface
```typescript
export interface DeliverableItem {
  id: string
  title: string
  status: 'completed' | 'failed' | 'pending' | 'in_progress' | 'unknown'
  
  // 🚀 AI-DRIVEN DUAL-FORMAT SUPPORT
  // Execution content (structured data for processing)
  execution_content?: Record<string, any>
  execution_format?: string
  
  // Display content (user-friendly format for presentation)
  display_content?: string
  display_format?: 'html' | 'markdown' | 'text'
  display_summary?: string
  display_preview?: string
  
  // Quality and transformation metadata
  display_quality_score?: number
  user_friendliness_score?: number
  readability_score?: number
  content_transformation_status?: 'pending' | 'success' | 'failed'
  transformation_error?: string
  
  // User actions for dual-format
  can_retry_transformation?: boolean
  available_formats?: string[]
  
  // Legacy support (deprecated)
  content?: string | Record<string, any>
}
```

### New Display Configuration Constants
```typescript
export const DISPLAY_FORMAT_CONFIG = {
  html: {
    label: 'HTML',
    icon: '🌐',
    color: 'text-blue-600',
    description: 'Rich HTML format with styling'
  },
  markdown: {
    label: 'Markdown', 
    icon: '📝',
    color: 'text-green-600',
    description: 'Markdown format for documentation'
  },
  text: {
    label: 'Plain Text',
    icon: '📄', 
    color: 'text-gray-600',
    description: 'Simple text format'
  }
}

export const TRANSFORMATION_STATUS_CONFIG = {
  pending: { label: 'Pending', icon: '⏳', color: 'text-yellow-600' },
  success: { label: 'Success', icon: '✅', color: 'text-green-600' },
  failed: { label: 'Failed', icon: '❌', color: 'text-red-600' }
}
```

## 🗃️ Database Schema Extensions

**Location:** `/backend/ai_driven_dual_format_migration_plan.py`

### New Columns Added to asset_artifacts
```sql
-- Display content fields
ALTER TABLE asset_artifacts 
ADD COLUMN IF NOT EXISTS display_content TEXT,
ADD COLUMN IF NOT EXISTS display_format VARCHAR(20) DEFAULT 'html',
ADD COLUMN IF NOT EXISTS display_summary TEXT,
ADD COLUMN IF NOT EXISTS display_metadata JSONB DEFAULT '{}';

-- Transformation tracking fields
ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS content_transformation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS content_transformation_error TEXT,
ADD COLUMN IF NOT EXISTS transformation_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS transformation_method VARCHAR(50) DEFAULT 'ai';

-- Quality metrics for display content
ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS display_quality_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS user_friendliness_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS readability_score FLOAT DEFAULT 0.0;
```

### New Audit Table
```sql
CREATE TABLE IF NOT EXISTS content_transformations_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES asset_artifacts(id),
    transformation_type VARCHAR(50) NOT NULL,
    input_format VARCHAR(20) NOT NULL,
    output_format VARCHAR(20) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    quality_score FLOAT,
    transformation_duration_ms INTEGER,
    ai_model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔄 Migration Strategy

### 5-Phase Migration Plan

#### Phase 1: Schema Extension
- Add new columns to existing tables
- Create indexes for performance
- Create audit/logging tables
- **Impact:** Zero downtime, backward compatible

#### Phase 2: Data Migration  
- Incremental batch processing (100 assets per batch)
- AI transformation of existing content
- Quality validation and scoring
- **Timeline:** ~7 minutes for 1000 assets

#### Phase 3: Service Deployment
- Deploy AIContentDisplayTransformer service
- Update API endpoints with dual-format support
- Implement batch transformation APIs
- Deploy monitoring and alerting

#### Phase 4: Frontend Updates
- Update components to use display_content
- Add transformation status indicators
- Implement format switching UI
- Add quality metrics visualization

#### Phase 5: Validation & Cleanup
- Data integrity validation
- Performance testing
- User acceptance testing
- Cleanup temporary migration data

### Rollback Strategy
- Immediate rollback: Disable AI service, revert APIs
- Data rollback: Restore from pre-migration backups  
- Partial rollback: Selective component rollback
- Recovery validation: Test all critical functionality

## 📋 API Endpoint Changes

### Enhanced Deliverables Endpoints

#### GET /api/workspaces/{workspace_id}/deliverables
**Enhanced Response:**
```json
{
  "deliverables": [...], // EnhancedDeliverableResponse[]
  "total_count": 10,
  "transformation_status": {
    "pending": 2,
    "success": 7,
    "failed": 1
  },
  "quality_overview": {
    "avg_display_quality": 0.82,
    "avg_user_friendliness": 0.78
  },
  "supports_dual_format": true,
  "available_transformations": ["html", "markdown", "text"]
}
```

#### POST /api/content/transform
**New Endpoint for Content Transformation:**
```json
{
  "asset_id": "uuid",
  "execution_content": {...},
  "content_type": "business_analysis", 
  "target_format": "html",
  "transformation_context": {...},
  "user_preferences": {...}
}
```

#### POST /api/content/transform/batch
**Batch Transformation Endpoint:**
```json
{
  "asset_ids": ["uuid1", "uuid2", "uuid3"],
  "target_format": "html",
  "priority": "normal"
}
```

### Migration Endpoints

#### GET /api/migration/status
**Migration Status Check:**
```json
{
  "migration_id": "uuid",
  "status": "running", 
  "progress_percentage": 65.5,
  "processed_count": 655,
  "successful_count": 620,
  "failed_count": 35,
  "estimated_remaining_minutes": 15
}
```

## ⚠️ Error Handling Specifications

### Transformation Error Model
```python
class ContentTransformationError(BaseModel):
    error_code: str                    # SM001, DM001, etc.
    error_message: str                 # Human-readable message
    asset_id: UUID                     # Failed asset ID
    retry_count: int = 0               # Current retry attempt
    max_retries: int = 3               # Maximum retry attempts
    last_attempt: datetime             # Last retry timestamp
    suggested_actions: List[str] = []  # Recommended user actions
    fallback_content: Optional[str]    # Safe fallback content
    technical_details: Dict[str, Any]  # Debug information
```

### Error Scenarios & Handling

1. **AI Service Unavailable**
   - Fallback to basic HTML formatting
   - Queue for retry when service recovers
   - Display pending transformation status

2. **Content Too Large**
   - Truncate content intelligently
   - Process in smaller chunks
   - Provide summary instead of full content

3. **Transformation Quality Too Low**
   - Retry with different prompts
   - Use fallback formatting
   - Flag for manual review

4. **Database Constraint Violations**
   - Validate data before transformation
   - Use safe default values
   - Log violations for analysis

## 🔒 Backward Compatibility Guarantees

### Legacy API Support
- Original `content` field remains available
- Existing API endpoints return legacy format by default
- New fields are optional and default to safe values
- No breaking changes to existing functionality

### Migration Safety
- All changes are additive (new columns, new tables)
- Original data is never modified in-place
- Full backup and rollback procedures
- Zero-downtime deployment strategy

### Progressive Enhancement
- Enhanced features available when supported
- Graceful degradation for legacy clients
- Feature flags for controlled rollout
- A/B testing capabilities

## 📊 Quality Metrics & Monitoring

### Content Quality Scores
- **display_quality_score** (0.0 - 1.0): Overall display quality
- **user_friendliness_score** (0.0 - 1.0): How user-friendly the content is
- **readability_score** (0.0 - 1.0): Text readability (Flesch-Kincaid based)

### System Monitoring
- Transformation success rates
- Average transformation time
- Quality score distributions  
- Error rates by category
- User engagement metrics

### Performance Metrics
- API response time impact
- Database query performance
- Memory usage during transformations
- Concurrent transformation capacity

## ✅ Implementation Checklist

### Backend Implementation
- [x] Enhanced AssetArtifact model with dual-format fields
- [x] ContentTransformationRequest/Response models
- [x] AIContentDisplayTransformer service interface
- [x] Enhanced API response models
- [x] Batch processing contracts
- [x] Migration models and error handling
- [ ] Implement AI transformation service
- [ ] Update existing API endpoints
- [ ] Deploy batch processing endpoints
- [ ] Implement migration procedures

### Frontend Implementation  
- [x] Updated TypeScript interfaces
- [x] Enhanced DeliverableItem interface
- [x] Display format configurations
- [x] Transformation status configurations
- [ ] Update ObjectiveArtifact component
- [ ] Add transformation status indicators
- [ ] Implement format switching UI
- [ ] Add quality metrics display
- [ ] Create migration dashboard

### Database Implementation
- [x] Schema extension SQL statements
- [x] Migration batch processing SQL
- [x] Audit table creation
- [x] Performance indexes
- [ ] Execute schema extensions
- [ ] Run data migration
- [ ] Validate migration results
- [ ] Performance optimization

### Testing & Validation
- [ ] Unit tests for all new models
- [ ] Integration tests for API endpoints
- [ ] Frontend component testing
- [ ] Migration testing on staging
- [ ] Performance testing with large datasets
- [ ] User acceptance testing

## 🚀 Next Steps

1. **Execute Schema Extensions**: Run the SQL statements to extend the database
2. **Implement AI Service**: Create the content transformation service
3. **Update API Endpoints**: Modify existing endpoints to return enhanced responses
4. **Deploy Frontend Updates**: Update components to use dual-format content
5. **Run Migration**: Execute the data migration for existing assets
6. **Monitor & Optimize**: Track quality metrics and optimize transformations

---

**Status:** ✅ API Contracts Complete  
**Ready for Implementation:** Yes  
**Backward Compatibility:** Guaranteed  
**Migration Time Estimate:** ~7 minutes for 1000 assets