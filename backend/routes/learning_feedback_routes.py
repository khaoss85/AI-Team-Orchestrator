"""
API Routes for Learning-Quality Feedback Loop System
Exposes the performance-boosting feedback loop functionality
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from services.learning_quality_feedback_loop import learning_quality_feedback_loop
from services.universal_learning_engine import universal_learning_engine
# Note: DomainType enum removed as Universal Learning Engine is domain-agnostic
from database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning-feedback", tags=["Learning Feedback Loop"])

@router.post("/process/{workspace_id}/{deliverable_id}")
async def process_deliverable_feedback(
    workspace_id: str,
    deliverable_id: str,
    force_learning: bool = Query(False, description="Force learning extraction even from lower quality content")
) -> Dict[str, Any]:
    """
    Process a deliverable through the complete learning-quality feedback loop.
    
    This endpoint:
    1. Validates deliverable quality using learned insights
    2. Extracts new insights from high-quality content
    3. Updates quality criteria with new learnings
    4. Measures performance boost
    
    Returns comprehensive feedback loop metrics and performance data.
    """
    try:
        logger.info(f"📊 Processing deliverable {deliverable_id} through feedback loop")
        
        result = await learning_quality_feedback_loop.process_deliverable_with_feedback_loop(
            workspace_id=workspace_id,
            deliverable_id=deliverable_id,
            force_learning=force_learning
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Deliverable not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deliverable feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-task/{workspace_id}/{task_id}")
async def enhance_task_with_learnings(
    workspace_id: str,
    task_id: str,
    agent_role: str = Query(..., description="The role of the agent executing the task")
) -> Dict[str, Any]:
    """
    Enhance task execution by providing relevant learned insights to the agent.
    
    This enables agents to produce higher quality deliverables by:
    - Providing domain-specific best practices
    - Setting performance targets based on successful patterns
    - Sharing actionable recommendations from past successes
    
    The insights are added to the task metadata for the agent to use during execution.
    """
    try:
        logger.info(f"🚀 Enhancing task {task_id} with learned insights")
        
        result = await learning_quality_feedback_loop.enhance_task_execution_with_learnings(
            workspace_id=workspace_id,
            task_id=task_id,
            agent_role=agent_role
        )
        
        if not result.get("enhanced"):
            logger.warning(f"Task enhancement not applied: {result.get('reason', 'Unknown reason')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error enhancing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-report/{workspace_id}")
async def get_performance_report(workspace_id: str) -> Dict[str, Any]:
    """
    Get a comprehensive performance report showing feedback loop effectiveness.
    
    Returns:
    - Overall performance boost percentage
    - Domain-specific quality improvements
    - Top performing insights
    - Quality criteria evolution
    - Recommendations for further improvement
    """
    try:
        logger.info(f"📈 Generating performance report for workspace {workspace_id}")
        
        report = await learning_quality_feedback_loop.get_performance_report(workspace_id)
        
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-workspace/{workspace_id}")
async def analyze_workspace_for_learnings(
    workspace_id: str,
    min_quality_score: float = Query(0.7, description="Minimum quality score for learning extraction")
) -> Dict[str, Any]:
    """
    Analyze all deliverables in a workspace to extract business insights.
    
    Only processes deliverables that meet the quality threshold to ensure
    we learn from successful patterns rather than failures.
    """
    try:
        logger.info(f"🔍 Analyzing workspace {workspace_id} for business insights")
        
        # First run content analysis
        analysis_result = await universal_learning_engine.analyze_workspace_content(workspace_id)
        
        if analysis_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("error"))
        
        # Then process high-quality deliverables through feedback loop
        supabase = get_supabase_client()
        deliverables_response = supabase.table('deliverables')\
            .select('id')\
            .eq('workspace_id', workspace_id)\
            .execute()
        
        if deliverables_response.data:
            feedback_results = []
            for deliverable in deliverables_response.data[:10]:  # Process up to 10 deliverables
                try:
                    feedback_result = await learning_quality_feedback_loop.process_deliverable_with_feedback_loop(
                        workspace_id=workspace_id,
                        deliverable_id=deliverable['id'],
                        force_learning=False
                    )
                    feedback_results.append({
                        "deliverable_id": deliverable['id'],
                        "quality_score": feedback_result.get('quality_validation', {}).get('quality_score', 0),
                        "insights_stored": feedback_result.get('learning_extraction', {}).get('insights_stored', 0),
                        "performance_boost": feedback_result.get('performance_metrics', {}).get('boost_percentage', 0)
                    })
                except Exception as e:
                    logger.warning(f"Failed to process deliverable {deliverable['id']}: {e}")
                    continue
            
            analysis_result['feedback_loop_results'] = feedback_results
            analysis_result['total_processed'] = len(feedback_results)
            
            # Calculate average performance boost
            boosts = [r['performance_boost'] for r in feedback_results if r['performance_boost'] > 0]
            if boosts:
                analysis_result['average_performance_boost'] = sum(boosts) / len(boosts)
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domain-insights/{workspace_id}")
async def get_domain_specific_insights(
    workspace_id: str,
    domain: Optional[str] = Query(None, description="Filter by specific domain")
) -> Dict[str, Any]:
    """
    Get actionable business insights for a workspace, optionally filtered by domain.
    
    Returns learned best practices, performance patterns, and recommendations
    that can be applied to improve future task execution.
    """
    try:
        logger.info(f"📚 Retrieving domain insights for workspace {workspace_id}")
        
        # Convert domain string to enum if provided
        domain_type = None
        if domain:
            try:
                # Domain is now a string, no enum conversion needed
                domain_type = domain
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
        
        # Get actionable learnings
        learnings = await universal_learning_engine.get_actionable_learnings(
            workspace_id=workspace_id,
            domain=domain_type
        )
        
        # Get quality criteria for the domain if specified
        quality_criteria = {}
        if domain_type:
            criteria = learning_quality_feedback_loop.domain_quality_criteria.get(domain_type, {})
            quality_criteria = {
                "base_threshold": criteria.get('base_threshold', 0.7),
                "learned_criteria_count": len(criteria.get('learned_criteria', [])),
                "performance_multiplier": criteria.get('performance_multiplier', 1.0),
                "maturity": "advanced" if len(criteria.get('learned_criteria', [])) > 10 else "developing"
            }
        
        return {
            "workspace_id": workspace_id,
            "domain": domain,
            "actionable_learnings": learnings,
            "total_learnings": len(learnings),
            "quality_criteria": quality_criteria,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback-metrics/{workspace_id}")
async def get_feedback_loop_metrics(
    workspace_id: str,
    limit: int = Query(10, description="Number of recent metrics to return")
) -> Dict[str, Any]:
    """
    Get recent feedback loop metrics showing the bidirectional influence
    between learning and quality systems.
    """
    try:
        logger.info(f"📊 Retrieving feedback metrics for workspace {workspace_id}")
        
        # Get feedback metrics from memory insights
        from database import get_memory_insights
        insights = await get_memory_insights(workspace_id, limit=limit * 2)
        
        feedback_metrics = []
        for insight in insights:
            if insight.get('insight_type') == 'feedback_loop_metrics':
                try:
                    import json
                    content = json.loads(insight.get('content', '{}'))
                    feedback_metrics.append({
                        "feedback_type": content.get('feedback_type'),
                        "quality_impact": content.get('quality_impact'),
                        "performance_boost": content.get('performance_boost'),
                        "domain": content.get('domain'),
                        "confidence": content.get('confidence'),
                        "timestamp": content.get('timestamp')
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse feedback metric: {e}")
                    continue
        
        # Sort by timestamp
        feedback_metrics.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate summary statistics
        if feedback_metrics:
            quality_impacts = [m['quality_impact'] for m in feedback_metrics if m.get('quality_impact')]
            performance_boosts = [m['performance_boost'] for m in feedback_metrics if m.get('performance_boost')]
            
            summary = {
                "average_quality_impact": sum(quality_impacts) / len(quality_impacts) if quality_impacts else 0,
                "average_performance_boost": sum(performance_boosts) / len(performance_boosts) if performance_boosts else 0,
                "total_feedback_cycles": len(feedback_metrics),
                "domains_covered": list(set(m['domain'] for m in feedback_metrics if m.get('domain')))
            }
        else:
            summary = {
                "average_quality_impact": 0,
                "average_performance_boost": 0,
                "total_feedback_cycles": 0,
                "domains_covered": []
            }
        
        return {
            "workspace_id": workspace_id,
            "feedback_metrics": feedback_metrics[:limit],
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router for inclusion in main app
__all__ = ["router"]