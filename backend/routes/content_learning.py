"""
API Routes for Content-Aware Learning Extraction
Provides endpoints for extracting business-valuable insights from deliverable content
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from services.content_aware_learning_engine import (
    content_aware_learning_engine,
    DomainType
)
from services.learning_feedback_engine import learning_feedback_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content-learning", tags=["content-learning"])

@router.post("/analyze/{workspace_id}")
async def analyze_workspace_content(
    workspace_id: UUID = Path(..., description="Workspace ID to analyze"),
    include_legacy: bool = Query(False, description="Include legacy task-based analysis")
) -> Dict[str, Any]:
    """
    Analyze deliverable content to extract business-valuable insights.
    
    This endpoint:
    - Analyzes deliverable content instead of task metadata
    - Extracts domain-specific insights (e.g., Instagram engagement rates)
    - Generates actionable recommendations with metrics
    - Integrates with quality validation for high-value insights
    """
    try:
        logger.info(f"📊 Starting content-aware analysis for workspace {workspace_id}")
        
        # Perform content-aware analysis
        content_results = await content_aware_learning_engine.analyze_workspace_content(str(workspace_id))
        
        # Optionally include legacy analysis
        legacy_results = {}
        if include_legacy:
            legacy_results = await learning_feedback_engine.analyze_workspace_performance(str(workspace_id))
        
        # Combine results
        response = {
            "workspace_id": str(workspace_id),
            "content_analysis": content_results,
            "insights_generated": content_results.get("insights_generated", 0),
            "domains_analyzed": content_results.get("domains_analyzed", []),
            "deliverables_analyzed": content_results.get("deliverables_analyzed", 0),
            "status": content_results.get("status", "completed")
        }
        
        if include_legacy:
            response["legacy_analysis"] = legacy_results
            response["total_insights"] = (
                content_results.get("insights_generated", 0) + 
                legacy_results.get("insights_generated", 0)
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing workspace content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{workspace_id}")
async def get_workspace_insights(
    workspace_id: UUID = Path(..., description="Workspace ID"),
    domain: Optional[str] = Query(None, description="Filter by business domain"),
    limit: int = Query(20, ge=1, le=100, description="Maximum insights to return")
) -> Dict[str, Any]:
    """
    Get actionable business insights for a workspace.
    
    Returns insights like:
    - "Carousel posts get 25% higher engagement than single images"
    - "Email open rates peak at 9 AM on Tuesdays"
    - "LinkedIn generates 45% of qualified leads"
    """
    try:
        # Convert domain string to enum if provided
        domain_filter = None
        if domain:
            try:
                domain_filter = DomainType(domain)
            except ValueError:
                logger.warning(f"Invalid domain filter: {domain}")
        
        # Get actionable learnings
        learnings = await content_aware_learning_engine.get_actionable_learnings(
            str(workspace_id),
            domain_filter
        )
        
        # Limit results
        learnings = learnings[:limit]
        
        return {
            "workspace_id": str(workspace_id),
            "domain_filter": domain,
            "insights_count": len(learnings),
            "actionable_insights": learnings,
            "insight_categories": {
                "high_confidence": len([l for l in learnings if "HIGH CONFIDENCE" in l]),
                "moderate_confidence": len([l for l in learnings if "MODERATE CONFIDENCE" in l]),
                "exploratory": len([l for l in learnings if "EXPLORATORY" in l])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting workspace insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deliverable/{deliverable_id}/extract")
async def extract_deliverable_insights(
    deliverable_id: UUID = Path(..., description="Deliverable ID to analyze"),
    workspace_id: UUID = Query(..., description="Workspace ID")
) -> Dict[str, Any]:
    """
    Extract insights from a specific deliverable.
    
    Integrates with quality validation to ensure only high-quality
    deliverables contribute to learning.
    """
    try:
        logger.info(f"🔍 Extracting insights from deliverable {deliverable_id}")
        
        # Use quality integration
        result = await content_aware_learning_engine.integrate_with_quality_validation(
            str(workspace_id),
            str(deliverable_id)
        )
        
        if result.get("status") == "below_quality_threshold":
            return {
                "deliverable_id": str(deliverable_id),
                "status": "skipped",
                "reason": "below_quality_threshold",
                "quality_score": result.get("quality_score", 0),
                "message": "Deliverable quality too low for reliable insight extraction"
            }
        
        return {
            "deliverable_id": str(deliverable_id),
            "workspace_id": str(workspace_id),
            "status": result.get("status", "completed"),
            "domain": result.get("domain", "general"),
            "insights_extracted": result.get("insights_extracted", 0),
            "insights_stored": result.get("insights_stored", 0),
            "quality_score": result.get("quality_score", 0)
        }
        
    except Exception as e:
        logger.error(f"Error extracting deliverable insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains")
async def get_available_domains() -> Dict[str, Any]:
    """
    Get list of available business domains for filtering.
    """
    return {
        "domains": [
            {
                "value": domain.value,
                "name": domain.value.replace("_", " ").title(),
                "description": get_domain_description(domain)
            }
            for domain in DomainType
        ]
    }

@router.get("/comparison/{workspace_id}")
async def compare_learning_methods(
    workspace_id: UUID = Path(..., description="Workspace ID to analyze")
) -> Dict[str, Any]:
    """
    Compare traditional vs content-aware learning extraction.
    
    Shows the difference between generic statistics and business insights.
    """
    try:
        # Get both types of analysis
        content_analysis = await content_aware_learning_engine.analyze_workspace_content(str(workspace_id))
        legacy_analysis = await learning_feedback_engine.analyze_workspace_performance(str(workspace_id))
        
        # Get sample insights from each
        content_learnings = await content_aware_learning_engine.get_actionable_learnings(str(workspace_id))
        
        return {
            "workspace_id": str(workspace_id),
            "comparison": {
                "content_aware": {
                    "insights_generated": content_analysis.get("insights_generated", 0),
                    "sample_insights": content_learnings[:3] if content_learnings else [],
                    "insight_type": "business_valuable",
                    "example": "Carousel posts get 25% higher engagement than single images"
                },
                "traditional": {
                    "insights_generated": legacy_analysis.get("insights_generated", 0),
                    "insight_type": "task_statistics",
                    "example": "11 of 11 deliverables completed (100% completion rate)"
                }
            },
            "improvement_factor": (
                content_analysis.get("insights_generated", 0) / 
                max(legacy_analysis.get("insights_generated", 1), 1)
            ),
            "recommendation": "Use content-aware analysis for actionable business insights"
        }
        
    except Exception as e:
        logger.error(f"Error comparing learning methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_domain_description(domain: DomainType) -> str:
    """Get human-readable description for a domain."""
    descriptions = {
        DomainType.INSTAGRAM_MARKETING: "Instagram engagement, hashtags, posting times, content types",
        DomainType.EMAIL_MARKETING: "Email open rates, subject lines, send timing, sequences",
        DomainType.CONTENT_STRATEGY: "Content calendars, publishing frequency, content mix",
        DomainType.LEAD_GENERATION: "Lead sources, qualification, conversion rates",
        DomainType.DATA_ANALYSIS: "KPIs, metrics, performance indicators",
        DomainType.BUSINESS_STRATEGY: "Market opportunities, competitive advantages, growth",
        DomainType.TECHNICAL_DOCUMENTATION: "Technical specifications, documentation, guides",
        DomainType.PRODUCT_DEVELOPMENT: "Product features, roadmaps, user feedback",
        DomainType.GENERAL: "General business insights across domains"
    }
    return descriptions.get(domain, "General business domain")

# Export router for main app
__all__ = ["router"]