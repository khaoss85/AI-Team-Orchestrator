# Content-Aware Learning API Reference

## Overview

The Content-Aware Learning API provides endpoints for extracting business-valuable insights from deliverable content, managing domain-specific learning, and integrating with the quality feedback loop. These APIs replace generic learning statistics with actionable business intelligence.

## Base URL

All API endpoints are mounted under the `/api/content-learning` prefix:

```
Base URL: http://localhost:8000/api/content-learning
Production: https://your-domain.com/api/content-learning
```

## Authentication

All endpoints require workspace-level authentication. Include the workspace context in your requests.

## Endpoints

### POST `/analyze/{workspace_id}`

Analyze deliverable content to extract business-valuable insights.

**Parameters:**
- `workspace_id` (path, UUID, required): Workspace ID to analyze
- `include_legacy` (query, boolean, optional): Include legacy task-based analysis (default: false)

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/content-learning/analyze/550e8400-e29b-41d4-a716-446655440000?include_legacy=true" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "content_analysis": {
        "status": "completed",
        "insights_generated": 12,
        "domains_analyzed": ["instagram_marketing", "email_marketing", "lead_generation"],
        "deliverables_analyzed": 8,
        "analysis_timestamp": "2025-01-15T10:30:00Z"
    },
    "insights_generated": 12,
    "domains_analyzed": ["instagram_marketing", "email_marketing", "lead_generation"],
    "deliverables_analyzed": 8,
    "status": "completed",
    "legacy_analysis": {
        "insights_generated": 3,
        "analysis_timestamp": "2025-01-15T10:30:00Z"
    },
    "total_insights": 15
}
```

**Response Codes:**
- `200`: Analysis completed successfully
- `400`: Invalid workspace ID
- `500`: Analysis failed

---

### GET `/insights/{workspace_id}`

Get actionable business insights for a workspace.

**Parameters:**
- `workspace_id` (path, UUID, required): Workspace ID
- `domain` (query, string, optional): Filter by business domain
- `limit` (query, integer, optional): Maximum insights to return (1-100, default: 20)

**Request Example:**
```bash
curl "http://localhost:8000/api/content-learning/insights/550e8400-e29b-41d4-a716-446655440000?domain=instagram_marketing&limit=10"
```

**Response:**
```json
{
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "domain_filter": "instagram_marketing",
    "insights_count": 8,
    "actionable_insights": [
        "✅ HIGH CONFIDENCE: Carousel posts get 25% higher engagement than single images",
        "✅ HIGH CONFIDENCE: Optimal posting time: 6:00 PM based on engagement data",
        "📊 MODERATE CONFIDENCE: Use 8 hashtags per post for optimal reach",
        "📊 MODERATE CONFIDENCE: Stories with polls increase engagement by 40%",
        "🔍 EXPLORATORY: User-generated content shows 15% higher reach"
    ],
    "insight_categories": {
        "high_confidence": 2,
        "moderate_confidence": 3,
        "exploratory": 3
    }
}
```

**Available Domains:**
- `instagram_marketing`
- `email_marketing`
- `content_strategy`
- `lead_generation`
- `data_analysis`
- `business_strategy`
- `technical_documentation`
- `product_development`
- `general`

**Response Codes:**
- `200`: Insights retrieved successfully
- `400`: Invalid parameters
- `404`: Workspace not found
- `500`: Retrieval failed

---

### POST `/deliverable/{deliverable_id}/extract`

Extract insights from a specific deliverable with quality validation.

**Parameters:**
- `deliverable_id` (path, UUID, required): Deliverable ID to analyze
- `workspace_id` (query, UUID, required): Workspace ID

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/content-learning/deliverable/750e8400-e29b-41d4-a716-446655440000/extract?workspace_id=550e8400-e29b-41d4-a716-446655440000"
```

**Response (Success):**
```json
{
    "deliverable_id": "750e8400-e29b-41d4-a716-446655440000",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "domain": "email_marketing",
    "insights_extracted": 3,
    "insights_stored": 2,
    "quality_score": 0.87
}
```

**Response (Quality Too Low):**
```json
{
    "deliverable_id": "750e8400-e29b-41d4-a716-446655440000",
    "status": "skipped",
    "reason": "below_quality_threshold",
    "quality_score": 0.45,
    "message": "Deliverable quality too low for reliable insight extraction"
}
```

**Response Codes:**
- `200`: Extraction completed or skipped
- `400`: Invalid parameters
- `404`: Deliverable not found
- `500`: Extraction failed

---

### GET `/domains`

Get list of available business domains for filtering.

**Request Example:**
```bash
curl "http://localhost:8000/api/content-learning/domains"
```

**Response:**
```json
{
    "domains": [
        {
            "value": "instagram_marketing",
            "name": "Instagram Marketing",
            "description": "Instagram engagement, hashtags, posting times, content types"
        },
        {
            "value": "email_marketing", 
            "name": "Email Marketing",
            "description": "Email open rates, subject lines, send timing, sequences"
        },
        {
            "value": "lead_generation",
            "name": "Lead Generation", 
            "description": "Lead sources, qualification, conversion rates"
        },
        {
            "value": "content_strategy",
            "name": "Content Strategy",
            "description": "Content calendars, publishing frequency, content mix"
        },
        {
            "value": "data_analysis",
            "name": "Data Analysis",
            "description": "KPIs, metrics, performance indicators"
        },
        {
            "value": "business_strategy",
            "name": "Business Strategy", 
            "description": "Market opportunities, competitive advantages, growth"
        },
        {
            "value": "technical_documentation",
            "name": "Technical Documentation",
            "description": "Technical specifications, documentation, guides"
        },
        {
            "value": "product_development",
            "name": "Product Development",
            "description": "Product features, roadmaps, user feedback"
        },
        {
            "value": "general",
            "name": "General",
            "description": "General business insights across domains"
        }
    ]
}
```

**Response Codes:**
- `200`: Domains retrieved successfully

---

### GET `/comparison/{workspace_id}`

Compare traditional vs content-aware learning extraction.

**Parameters:**
- `workspace_id` (path, UUID, required): Workspace ID to analyze

**Request Example:**
```bash
curl "http://localhost:8000/api/content-learning/comparison/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "comparison": {
        "content_aware": {
            "insights_generated": 16,
            "sample_insights": [
                "✅ HIGH CONFIDENCE: Carousel posts get 25% higher engagement than single images",
                "📊 MODERATE CONFIDENCE: Email open rates peak at 9 AM on Tuesdays",
                "📊 MODERATE CONFIDENCE: LinkedIn generates 45% of qualified leads"
            ],
            "insight_type": "business_valuable",
            "example": "Carousel posts get 25% higher engagement than single images"
        },
        "traditional": {
            "insights_generated": 4,
            "insight_type": "task_statistics", 
            "example": "11 of 11 deliverables completed (100% completion rate)"
        }
    },
    "improvement_factor": 4.0,
    "recommendation": "Use content-aware analysis for actionable business insights"
}
```

**Response Codes:**
- `200`: Comparison completed successfully
- `400`: Invalid workspace ID
- `500`: Comparison failed

## Integration Examples

### JavaScript/TypeScript Integration

```typescript
// Content Learning API Client
class ContentLearningAPI {
    private baseURL = '/api/content-learning';
    
    async analyzeWorkspace(workspaceId: string, includeLegacy = false): Promise<AnalysisResult> {
        const response = await fetch(`${this.baseURL}/analyze/${workspaceId}?include_legacy=${includeLegacy}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return response.json();
    }
    
    async getInsights(workspaceId: string, domain?: string, limit = 20): Promise<InsightsResponse> {
        const params = new URLSearchParams();
        if (domain) params.append('domain', domain);
        params.append('limit', limit.toString());
        
        const response = await fetch(`${this.baseURL}/insights/${workspaceId}?${params}`);
        return response.json();
    }
    
    async extractDeliverableInsights(deliverableId: string, workspaceId: string): Promise<ExtractionResult> {
        const response = await fetch(`${this.baseURL}/deliverable/${deliverableId}/extract?workspace_id=${workspaceId}`, {
            method: 'POST'
        });
        return response.json();
    }
    
    async getDomains(): Promise<DomainsResponse> {
        const response = await fetch(`${this.baseURL}/domains`);
        return response.json();
    }
    
    async compareLearningSystems(workspaceId: string): Promise<ComparisonResponse> {
        const response = await fetch(`${this.baseURL}/comparison/${workspaceId}`);
        return response.json();
    }
}

// Usage example
const api = new ContentLearningAPI();

// Analyze workspace content
const analysis = await api.analyzeWorkspace(workspaceId);
console.log(`Generated ${analysis.insights_generated} insights across ${analysis.domains_analyzed.length} domains`);

// Get domain-specific insights
const instagramInsights = await api.getInsights(workspaceId, 'instagram_marketing');
instagramInsights.actionable_insights.forEach(insight => {
    console.log(`Instagram insight: ${insight}`);
});

// Compare learning systems
const comparison = await api.compareLearningSystems(workspaceId);
console.log(`Content-aware analysis generates ${comparison.improvement_factor}x more insights`);
```

### Python Integration

```python
import httpx
import asyncio
from typing import Optional, Dict, List, Any

class ContentLearningClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/content-learning"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def analyze_workspace(self, workspace_id: str, include_legacy: bool = False) -> Dict[str, Any]:
        """Analyze workspace content for business insights"""
        response = await self.client.post(
            f"{self.base_url}/analyze/{workspace_id}",
            params={"include_legacy": include_legacy}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_insights(self, workspace_id: str, domain: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Get actionable business insights"""
        params = {"limit": limit}
        if domain:
            params["domain"] = domain
        
        response = await self.client.get(
            f"{self.base_url}/insights/{workspace_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def extract_deliverable_insights(self, deliverable_id: str, workspace_id: str) -> Dict[str, Any]:
        """Extract insights from specific deliverable"""
        response = await self.client.post(
            f"{self.base_url}/deliverable/{deliverable_id}/extract",
            params={"workspace_id": workspace_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_domains(self) -> Dict[str, Any]:
        """Get available business domains"""
        response = await self.client.get(f"{self.base_url}/domains")
        response.raise_for_status()
        return response.json()
    
    async def compare_systems(self, workspace_id: str) -> Dict[str, Any]:
        """Compare traditional vs content-aware learning"""
        response = await self.client.get(f"{self.base_url}/comparison/{workspace_id}")
        response.raise_for_status()
        return response.json()

# Usage example
async def main():
    client = ContentLearningClient()
    workspace_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Analyze workspace
    analysis = await client.analyze_workspace(workspace_id, include_legacy=True)
    print(f"Analysis generated {analysis['insights_generated']} insights")
    
    # Get domain-specific insights
    email_insights = await client.get_insights(workspace_id, domain="email_marketing")
    for insight in email_insights['actionable_insights']:
        print(f"Email insight: {insight}")
    
    # Compare systems
    comparison = await client.compare_systems(workspace_id)
    print(f"Content-aware system is {comparison['improvement_factor']}x better")
    
    await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
    "detail": "Invalid workspace ID format",
    "error_code": "INVALID_WORKSPACE_ID",
    "timestamp": "2025-01-15T10:30:00Z"
}
```

**404 Not Found:**
```json
{
    "detail": "Workspace not found",
    "error_code": "WORKSPACE_NOT_FOUND",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Content analysis failed",
    "error_code": "ANALYSIS_FAILED",
    "error_message": "Domain detection timeout",
    "retry_after": 60
}
```

### Error Codes Reference

| Code | Description | Action |
|------|-------------|---------|
| `INVALID_WORKSPACE_ID` | Workspace ID format invalid | Check UUID format |
| `WORKSPACE_NOT_FOUND` | Workspace doesn't exist | Verify workspace exists |
| `DELIVERABLE_NOT_FOUND` | Deliverable doesn't exist | Check deliverable ID |
| `INSUFFICIENT_CONTENT` | Not enough content to analyze | Add more deliverables |
| `ANALYSIS_FAILED` | Content analysis error | Retry after delay |
| `QUALITY_TOO_LOW` | Content quality below threshold | Improve deliverable quality |
| `DOMAIN_DETECTION_FAILED` | Cannot detect business domain | Manual domain specification |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry |

## Rate Limiting

API endpoints are rate limited to ensure system stability:

- **Analysis endpoints**: 10 requests per minute per workspace
- **Insight retrieval**: 60 requests per minute per workspace  
- **Domain listing**: 100 requests per minute (global)

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642248000
```

## Monitoring and Analytics

### Performance Metrics

Track API performance with these built-in metrics:

```bash
# Check API health
curl "http://localhost:8000/health"

# Monitor analysis performance
curl "http://localhost:8000/api/content-learning/metrics" \
  -H "Authorization: Bearer admin_token"
```

**Metrics Response:**
```json
{
    "total_analyses": 1247,
    "successful_analyses": 1198,
    "failed_analyses": 49,
    "average_analysis_time": 2.3,
    "insights_generated_total": 18942,
    "domains_active": 8,
    "quality_score_average": 0.78
}
```

### Usage Analytics

```json
{
    "usage_by_domain": {
        "instagram_marketing": 324,
        "email_marketing": 287, 
        "lead_generation": 203,
        "content_strategy": 156
    },
    "insights_by_confidence": {
        "high_confidence": 7234,
        "moderate_confidence": 8901,
        "exploratory": 2807
    },
    "top_performing_workspaces": [
        {
            "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
            "insights_generated": 67,
            "quality_score_avg": 0.89
        }
    ]
}
```

## Webhooks (Future Feature)

Planned webhook support for real-time insight notifications:

```json
{
    "event": "insight.generated",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": {
        "insight_type": "business_learning",
        "domain": "instagram_marketing",
        "confidence": "high",
        "business_value": 0.85,
        "recommendation": "Carousel posts get 25% higher engagement than single images"
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

## SDK Development

Official SDKs are planned for:
- JavaScript/TypeScript (Web & Node.js)
- Python 
- Go
- Java

Community SDKs welcome for other languages.

## Migration from Legacy APIs

### Legacy Endpoint Mapping

| Legacy Endpoint | New Endpoint | Status |
|----------------|--------------|---------|
| `GET /api/learning/insights/{workspace_id}` | `GET /api/content-learning/insights/{workspace_id}` | ✅ Available |
| `POST /api/learning/analyze/{workspace_id}` | `POST /api/content-learning/analyze/{workspace_id}` | ✅ Available |
| `GET /api/learning/patterns/{workspace_id}` | `GET /api/content-learning/insights/{workspace_id}?domain=general` | 🔄 Deprecated |

### Migration Timeline

- **Phase 1**: Both APIs available (current)
- **Phase 2**: Legacy API deprecated warnings (Q2 2025)
- **Phase 3**: Legacy API removal (Q4 2025)

This API reference provides comprehensive documentation for integrating with the Content-Aware Learning System, enabling developers to extract maximum business value from their content analysis workflows.