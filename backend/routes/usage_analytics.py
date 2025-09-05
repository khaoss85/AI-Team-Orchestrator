#!/usr/bin/env python3
"""
Usage Analytics API Routes
Provides endpoints for real-time OpenAI usage data, cost analytics, and budget monitoring
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from services.openai_usage_api_client import get_usage_client, AggregationLevel
from services.ai_cost_intelligence import get_cost_intelligence
from services.openai_quota_tracker import quota_manager
# from auth import get_current_user  # Auth module not available

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage_analytics"])

@router.get("/current-month")
async def get_current_month_usage(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current month's OpenAI usage data with real costs
    
    Returns:
        Current month usage summary with model breakdown
    """
    try:
        client = get_usage_client()
        usage = await client.get_current_month_usage()
        
        return {
            "success": True,
            "data": {
                "total_cost": usage.total_cost,
                "total_tokens": usage.total_tokens,
                "total_requests": usage.total_requests,
                "start_date": usage.start_date.isoformat(),
                "end_date": usage.end_date.isoformat(),
                "model_breakdown": usage.model_breakdown,
                "daily_breakdown": usage.daily_breakdown
            }
        }
    except Exception as e:
        logger.error(f"Error fetching current month usage: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/today")
async def get_today_usage(
    current_user: dict = Depends(get_current_user)
):
    """
    Get today's OpenAI usage data with hourly breakdown
    
    Returns:
        Today's usage with hourly breakdown
    """
    try:
        client = get_usage_client()
        usage = await client.get_today_usage()
        
        return {
            "success": True,
            "data": {
                "total_cost": usage.total_cost,
                "total_tokens": usage.total_tokens,
                "total_requests": usage.total_requests,
                "hourly_breakdown": usage.hourly_breakdown,
                "model_breakdown": usage.model_breakdown
            }
        }
    except Exception as e:
        logger.error(f"Error fetching today's usage: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/budget-status")
async def get_budget_status(
    monthly_budget: Optional[float] = Query(None, description="Monthly budget in USD"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current budget status with projections
    
    Args:
        monthly_budget: Optional monthly budget override
        
    Returns:
        Budget status with spending projections
    """
    try:
        client = get_usage_client()
        status = await client.check_budget_status(monthly_budget)
        
        # Add intelligent alerts if needed
        alerts = []
        if status['status'] == 'critical':
            alerts.append({
                "severity": "critical",
                "message": f"Budget usage at {status['budget_used_percent']:.1f}% with {status['days_remaining']} days remaining",
                "action": "Consider increasing budget or reducing usage immediately"
            })
        elif status['status'] == 'warning':
            alerts.append({
                "severity": "warning",
                "message": f"Approaching budget limit: ${status['current_spend']:.2f} of ${status['monthly_budget']:.2f}",
                "action": f"Recommended daily limit: ${status['recommended_daily_limit']:.2f}"
            })
        
        return {
            "success": True,
            "data": status,
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error checking budget status: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/model-comparison")
async def get_model_comparison(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """
    Compare usage and costs across different models
    
    Args:
        days: Number of days to analyze (1-90)
        
    Returns:
        Model comparison with efficiency metrics
    """
    try:
        client = get_usage_client()
        comparison = await client.get_model_comparison(days)
        
        # Add recommendations based on comparison
        recommendations = []
        for model, data in comparison.items():
            if model == "gpt-4" and data['cost_percentage'] > 50:
                recommendations.append({
                    "model": model,
                    "suggestion": "Consider using gpt-4o-mini for simpler tasks",
                    "potential_savings": data['total_cost'] * 0.3  # Rough estimate
                })
        
        return {
            "success": True,
            "data": {
                "comparison": comparison,
                "period_days": days,
                "recommendations": recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/cost-trend")
async def get_cost_trend(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get cost trend over time with projections
    
    Args:
        days: Number of days to analyze (1-90)
        
    Returns:
        Daily and cumulative cost trends
    """
    try:
        client = get_usage_client()
        trend = await client.get_cost_trend(days)
        
        # Add trend analysis
        analysis = {
            "trend_direction": "increasing" if len(trend['daily']) > 1 and trend['daily'][-1]['cost'] > trend['daily'][0]['cost'] else "stable",
            "average_daily_cost": trend['avg_daily_cost'],
            "projected_monthly": trend['avg_daily_cost'] * 30
        }
        
        return {
            "success": True,
            "data": {
                **trend,
                "analysis": analysis
            }
        }
    except Exception as e:
        logger.error(f"Error fetching cost trend: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/real-vs-estimated/{workspace_id}")
async def get_real_vs_estimated_comparison(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare real usage data with system estimates
    
    Args:
        workspace_id: Workspace to analyze
        
    Returns:
        Comparison of real vs estimated costs
    """
    try:
        # Get cost intelligence for workspace
        cost_intel = get_cost_intelligence(workspace_id)
        
        # Update with real costs first
        await cost_intel.update_real_costs()
        
        # Get comparison
        comparison = await cost_intel.get_real_vs_estimated_comparison()
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "data": comparison
        }
    except Exception as e:
        logger.error(f"Error comparing real vs estimated: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/cost-intelligence/{workspace_id}")
async def get_cost_intelligence_summary(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI cost intelligence summary with optimization alerts
    
    Args:
        workspace_id: Workspace to analyze
        
    Returns:
        Cost intelligence summary with alerts and recommendations
    """
    try:
        # Get cost intelligence
        cost_intel = get_cost_intelligence(workspace_id)
        
        # Update with real data
        await cost_intel.update_real_costs()
        
        # Get summary
        summary = cost_intel.get_cost_summary()
        
        # Get recent alerts
        alerts = cost_intel.get_recent_alerts(limit=5)
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "severity": alert.severity.value,
                "type": alert.type,
                "title": alert.title,
                "description": alert.description,
                "potential_savings": alert.potential_savings,
                "recommendation": alert.recommendation,
                "confidence": alert.confidence,
                "created_at": alert.created_at.isoformat()
            })
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "summary": summary,
            "alerts": alert_data,
            "real_data_available": summary.get("real_data_calibrated", False)
        }
    except Exception as e:
        logger.error(f"Error getting cost intelligence: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.get("/quota-status/{workspace_id}")
async def get_quota_status_with_real_data(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get quota status enhanced with real usage data
    
    Args:
        workspace_id: Workspace to check
        
    Returns:
        Quota status with real usage integration
    """
    try:
        # Get quota tracker
        tracker = quota_manager.get_tracker(workspace_id)
        
        # Fetch real usage data
        real_data = await tracker.fetch_real_usage_data()
        
        # Get status data
        status = tracker.get_status_data()
        enhanced = tracker.get_enhanced_status_data()
        notifications = tracker.get_notification_data()
        
        # Combine all data
        return {
            "success": True,
            "workspace_id": workspace_id,
            "status": status,
            "enhanced": enhanced,
            "notifications": notifications,
            "real_usage_available": real_data is not None
        }
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@router.post("/clear-cache")
async def clear_usage_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear usage data cache to force fresh data fetch
    
    Returns:
        Cache clear status
    """
    try:
        client = get_usage_client()
        client.clear_cache()
        
        return {
            "success": True,
            "message": "Usage cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/dashboard/{workspace_id}")
async def get_usage_dashboard(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive usage dashboard data for frontend display
    
    Args:
        workspace_id: Workspace to analyze
        
    Returns:
        Complete dashboard data with all metrics
    """
    try:
        # Initialize clients
        usage_client = get_usage_client()
        cost_intel = get_cost_intelligence(workspace_id)
        tracker = quota_manager.get_tracker(workspace_id)
        
        # Fetch all data in parallel
        import asyncio
        (
            today_usage,
            month_usage,
            budget_status,
            model_comparison,
            cost_trend,
            real_vs_estimated,
            quota_status,
            real_quota_data
        ) = await asyncio.gather(
            usage_client.get_today_usage(),
            usage_client.get_current_month_usage(),
            usage_client.check_budget_status(),
            usage_client.get_model_comparison(days=7),
            usage_client.get_cost_trend(days=30),
            cost_intel.get_real_vs_estimated_comparison(),
            tracker.get_status_data(),
            tracker.fetch_real_usage_data()
        )
        
        # Get cost intelligence summary
        cost_summary = cost_intel.get_cost_summary()
        recent_alerts = cost_intel.get_recent_alerts(limit=3)
        
        # Build dashboard response
        dashboard = {
            "success": True,
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat(),
            "today": {
                "cost": today_usage.total_cost,
                "tokens": today_usage.total_tokens,
                "requests": today_usage.total_requests
            },
            "month": {
                "cost": month_usage.total_cost,
                "tokens": month_usage.total_tokens,
                "requests": month_usage.total_requests,
                "daily_average": month_usage.total_cost / datetime.now().day
            },
            "budget": {
                "status": budget_status['status'],
                "current_spend": budget_status['current_spend'],
                "monthly_budget": budget_status['monthly_budget'],
                "percentage_used": budget_status['budget_used_percent'],
                "projected_monthly": budget_status['projected_monthly'],
                "days_remaining": budget_status['days_remaining']
            },
            "models": model_comparison,
            "cost_trend": {
                "last_7_days": cost_trend['daily'][-7:] if len(cost_trend['daily']) > 7 else cost_trend['daily'],
                "total_30_days": cost_trend['total_cost']
            },
            "accuracy": {
                "real_vs_estimated": real_vs_estimated['accuracy_percent'],
                "calibration_ratio": real_vs_estimated.get('calibration_ratio', 1.0)
            },
            "quota": {
                "status": quota_status['status'],
                "requests_per_minute": quota_status['requests_per_minute'],
                "requests_per_day": quota_status['requests_per_day']
            },
            "intelligence": {
                "efficiency_score": cost_summary['efficiency_score'],
                "duplicate_rate": cost_summary['duplicate_rate_percent'],
                "potential_daily_savings": cost_summary['potential_daily_savings_usd'],
                "alerts": [
                    {
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "savings": alert.potential_savings
                    }
                    for alert in recent_alerts
                ]
            }
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error building usage dashboard: {e}")
        return {
            "success": False,
            "error": str(e),
            "workspace_id": workspace_id
        }