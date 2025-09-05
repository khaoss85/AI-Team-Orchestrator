"""
Real-time OpenAI Usage API endpoints for cost tracking and budget management
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import traceback

import logging
from services.openai_usage_api_client import get_usage_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/usage", tags=["Usage"])

@router.get("/current-month")
async def get_current_month_usage():
    """Get current month's OpenAI usage data"""
    try:
        client = get_usage_client()
        usage_data = await client.get_current_month_usage()
        
        return {
            "total_cost": usage_data.total_cost,
            "total_tokens": usage_data.total_tokens,
            "total_requests": usage_data.total_requests,
            "model_breakdown": [
                {
                    "model": model_name,
                    "input_cost_per_1k": stats.get('input_cost', 0) / max(stats.get('input_tokens', 1) / 1000, 0.001),
                    "output_cost_per_1k": stats.get('output_cost', 0) / max(stats.get('output_tokens', 1) / 1000, 0.001),
                    "total_input_tokens": stats.get('input_tokens', 0),
                    "total_output_tokens": stats.get('output_tokens', 0),
                    "total_cost": stats.get('total_cost', 0),
                    "request_count": stats.get('requests_count', 0),
                    "error_count": 0  # We don't track errors currently
                } for model_name, stats in usage_data.model_breakdown.items()
            ],
            "daily_breakdown": [
                {
                    "date": day.date.isoformat(),
                    "total_cost": day.total_cost,
                    "total_tokens": day.total_tokens,
                    "total_requests": day.total_requests
                } for day in usage_data.daily_breakdown
            ] if usage_data.daily_breakdown else [],
            "period_start": getattr(usage_data, 'period_start', None),
            "period_end": getattr(usage_data, 'period_end', None)
        }
    except Exception as e:
        logger.error(f"Failed to fetch current month usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today")
async def get_today_usage():
    """Get today's OpenAI usage data with hourly breakdown"""
    try:
        client = get_usage_client()
        usage_data = await client.get_today_usage()
        
        return {
            "total_cost": usage_data.total_cost,
            "total_tokens": usage_data.total_tokens,
            "total_requests": usage_data.total_requests,
            "model_breakdown": [
                {
                    "model": model_name,
                    "input_cost_per_1k": stats.get('input_cost', 0) / max(stats.get('input_tokens', 1) / 1000, 0.001),
                    "output_cost_per_1k": stats.get('output_cost', 0) / max(stats.get('output_tokens', 1) / 1000, 0.001),
                    "total_input_tokens": stats.get('input_tokens', 0),
                    "total_output_tokens": stats.get('output_tokens', 0),
                    "total_cost": stats.get('total_cost', 0),
                    "request_count": stats.get('requests_count', 0),
                    "error_count": 0  # We don't track errors currently
                } for model_name, stats in usage_data.model_breakdown.items()
            ],
            "hourly_breakdown": [
                {
                    "hour": int(hour_key.split()[1].split(':')[0]) if ' ' in hour_key and ':' in hour_key else idx,
                    "cost": hour_data.get('total_cost', hour_data.get('cost', 0)),
                    "tokens": hour_data.get('total_tokens', hour_data.get('tokens', 0)),
                    "requests": hour_data.get('requests_count', hour_data.get('requests', 0))
                } for idx, (hour_key, hour_data) in enumerate(usage_data.hourly_breakdown.items() if usage_data.hourly_breakdown else {})
            ] if usage_data.hourly_breakdown else [],
            "period_start": getattr(usage_data, 'period_start', None),
            "period_end": getattr(usage_data, 'period_end', None)
        }
    except Exception as e:
        logger.error(f"Failed to fetch today's usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budget-status")
async def get_budget_status():
    """Get budget status and recommendations"""
    try:
        client = get_usage_client()
        # Use check_budget_status instead of get_budget_status
        budget_data = await client.check_budget_status()
        
        # The method returns a dict, so we'll use it directly
        return budget_data
    except Exception as e:
        logger.error(f"Failed to fetch budget status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-comparison")
async def get_model_comparison():
    """Get model cost comparison and recommendations"""
    try:
        client = get_usage_client()
        usage_data = await client.get_current_month_usage()
        
        # Simple model comparison based on usage data
        models = []
        for model_data in usage_data.model_breakdown:
            avg_cost_per_1k = (model_data.total_cost / max((model_data.total_input_tokens + model_data.total_output_tokens) / 1000, 1))
            models.append({
                "model": model_data.model,
                "daily_cost": model_data.total_cost / max(len(usage_data.daily_breakdown), 1) if usage_data.daily_breakdown else model_data.total_cost,
                "projected_monthly": model_data.total_cost * (30 / max(len(usage_data.daily_breakdown), 1)) if usage_data.daily_breakdown else model_data.total_cost * 30,
                "cost_per_1k_tokens": avg_cost_per_1k,
                "efficiency_score": 10 - min(avg_cost_per_1k * 10, 10),  # Simple efficiency score
                "pros": ["Fast response time"] if "gpt-4" in model_data.model.lower() else ["Cost effective"],
                "cons": ["Higher cost"] if "gpt-4" in model_data.model.lower() else ["Less capable"]
            })
        
        # Simple recommendation
        recommended = min(models, key=lambda x: x["cost_per_1k_tokens"]) if models else None
        
        return {
            "models": models,
            "recommended_model": recommended["model"] if recommended else None,
            "estimated_savings": 0  # Placeholder
        }
    except Exception as e:
        logger.error(f"Failed to get model comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-intelligence/{workspace_id}")
async def get_cost_intelligence(workspace_id: str):
    """Get AI-powered cost optimization insights"""
    try:
        client = get_usage_client()
        usage_data = await client.get_current_month_usage()
        
        # Generate simple cost intelligence alerts
        alerts = []
        
        # Check for high GPT-4 usage
        for model in usage_data.model_breakdown:
            if "gpt-4" in model.model.lower() and model.total_cost > 10:
                alerts.append({
                    "id": f"alert_{model.model}_cost",
                    "severity": "medium",
                    "category": "model_optimization",
                    "title": f"High {model.model} usage detected",
                    "description": f"You've spent ${model.total_cost:.2f} on {model.model} this month",
                    "recommendation": "Consider using GPT-4o-mini for simpler tasks to reduce costs",
                    "potential_savings": model.total_cost * 0.3,  # Estimate 30% savings
                    "confidence": 0.75,
                    "created_at": datetime.utcnow().isoformat()
                })
        
        # Check for duplicate patterns (simplified)
        if usage_data.total_requests > 100:
            alerts.append({
                "id": "alert_duplicate_calls",
                "severity": "low",
                "category": "efficiency",
                "title": "Potential duplicate API calls",
                "description": "High request volume detected that might include duplicates",
                "recommendation": "Implement caching for frequently repeated queries",
                "potential_savings": usage_data.total_cost * 0.1,  # Estimate 10% savings
                "confidence": 0.6,
                "created_at": datetime.utcnow().isoformat()
            })
        
        total_savings = sum(alert["potential_savings"] for alert in alerts)
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "potential_monthly_savings": total_savings
        }
    except Exception as e:
        logger.error(f"Failed to generate cost intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/{workspace_id}")
async def get_usage_dashboard(workspace_id: str):
    """Get comprehensive usage dashboard with all metrics"""
    try:
        client = get_usage_client()
        
        # Fetch all data
        current_month = await client.get_current_month_usage()
        today = await client.get_today_usage()
        budget = await client.check_budget_status()
        
        # Get model comparison (simplified)
        models = []
        for model_data in current_month.model_breakdown:
            avg_cost_per_1k = (model_data.total_cost / max((model_data.total_input_tokens + model_data.total_output_tokens) / 1000, 1))
            models.append({
                "model": model_data.model,
                "daily_cost": model_data.total_cost / max(len(current_month.daily_breakdown), 1) if current_month.daily_breakdown else model_data.total_cost,
                "projected_monthly": model_data.total_cost * (30 / max(len(current_month.daily_breakdown), 1)) if current_month.daily_breakdown else model_data.total_cost * 30,
                "cost_per_1k_tokens": avg_cost_per_1k,
                "efficiency_score": 10 - min(avg_cost_per_1k * 10, 10),
                "pros": ["Fast response time"] if "gpt-4" in model_data.model.lower() else ["Cost effective"],
                "cons": ["Higher cost"] if "gpt-4" in model_data.model.lower() else ["Less capable"]
            })
        
        recommended = min(models, key=lambda x: x["cost_per_1k_tokens"]) if models else None
        model_comparison = {
            "models": models,
            "recommended_model": recommended["model"] if recommended else None,
            "estimated_savings": 0
        }
        
        # Get cost intelligence (simplified)
        alerts = []
        for model in current_month.model_breakdown:
            if "gpt-4" in model.model.lower() and model.total_cost > 10:
                alerts.append({
                    "id": f"alert_{model.model}_cost",
                    "severity": "medium",
                    "category": "model_optimization",
                    "title": f"High {model.model} usage detected",
                    "description": f"You've spent ${model.total_cost:.2f} on {model.model} this month",
                    "recommendation": "Consider using GPT-4o-mini for simpler tasks",
                    "potential_savings": model.total_cost * 0.3,
                    "confidence": 0.75,
                    "created_at": datetime.utcnow().isoformat()
                })
        
        return {
            "current_month": {
                "total_cost": current_month.total_cost,
                "total_tokens": current_month.total_tokens,
                "total_requests": current_month.total_requests,
                "model_breakdown": [
                    {
                        "model": model.model,
                        "total_cost": model.total_cost,
                        "request_count": model.request_count,
                        "total_tokens": model.total_input_tokens + model.total_output_tokens
                    } for model in current_month.model_breakdown
                ],
                "period_start": current_month.period_start.isoformat() if current_month.period_start else None,
                "period_end": current_month.period_end.isoformat() if current_month.period_end else None
            },
            "today": {
                "total_cost": today.total_cost,
                "total_tokens": today.total_tokens,
                "total_requests": today.total_requests,
                "hourly_breakdown": [
                    {
                        "hour": int(hour_key.split()[1].split(':')[0]) if ' ' in hour_key and ':' in hour_key else idx,
                        "cost": hour_data.get('total_cost', hour_data.get('cost', 0)),
                        "tokens": hour_data.get('total_tokens', hour_data.get('tokens', 0)),
                        "requests": hour_data.get('requests_count', hour_data.get('requests', 0))
                    } for idx, (hour_key, hour_data) in enumerate(today.hourly_breakdown.items() if today.hourly_breakdown else {})
                ] if today.hourly_breakdown else [],
            },
            "budget": budget,  # Use the budget dict directly
            "model_comparison": model_comparison,
            "cost_intelligence": {
                "alerts": [
                    {
                        "id": alert.get("id"),
                        "severity": alert.get("severity"),
                        "category": alert.get("category"),
                        "title": alert.get("title"),
                        "description": alert.get("description"),
                        "recommendation": alert.get("recommendation"),
                        "potential_savings": alert.get("potential_savings", 0),
                        "confidence": alert.get("confidence", 0),
                        "created_at": alert.get("created_at", datetime.utcnow().isoformat())
                    } for alert in alerts
                ],
                "total_alerts": len(alerts),
                "potential_monthly_savings": sum(alert.get("potential_savings", 0) for alert in alerts)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to generate usage dashboard: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))