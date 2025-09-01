#!/usr/bin/env python3
"""
🎯 Theme Extraction API Routes
Endpoint for AI-driven goal theme extraction and macro-deliverable grouping
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Any, Optional
from uuid import UUID
import logging
import json
from datetime import datetime

from middleware.trace_middleware import get_trace_id, create_traced_logger
from services.ai_theme_extractor import AIThemeExtractor, ThemeExtractionResult
from database import get_supabase_client, get_workspace_goals

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/theme", tags=["theme-extraction"])

# Initialize AI Theme Extractor
theme_extractor = AIThemeExtractor()

@router.get("/{workspace_id}/extract", response_model=Dict[str, Any])
async def extract_workspace_themes(
    workspace_id: UUID, 
    request: Request,
    min_confidence: Optional[float] = 70.0,
    user_locale: Optional[str] = "en"
):
    """
    🎯 Extract AI-driven themes from workspace goals for macro-deliverable grouping
    
    Args:
        workspace_id: Workspace UUID
        min_confidence: Minimum confidence threshold for theme creation (0-100)
        user_locale: User language for theme naming (en, it, es, fr, de, etc.)
        
    Returns:
        ThemeExtractionResult with AI-generated macro-themes and grouped goals
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"🎯 Theme extraction requested for workspace {workspace_id}")
    
    try:
        # Get workspace goals
        supabase = get_supabase_client()
        goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", str(workspace_id)).eq("status", "active").execute()
        
        if not goals_response.data:
            logger.warning(f"No active goals found for workspace {workspace_id}")
            return {
                "workspace_id": str(workspace_id),
                "themes": [],
                "ungrouped_goals": [],
                "extraction_confidence": 0.0,
                "extraction_time": 0.0,
                "fallback_used": False,
                "user_locale": user_locale,
                "extraction_reasoning": "No active goals found in workspace",
                "message": "No active goals available for theme extraction"
            }
        
        goals = goals_response.data
        logger.info(f"✅ Found {len(goals)} active goals for theme extraction")
        
        # Get workspace context for better theme extraction
        workspace_response = supabase.table("workspaces").select("*").eq("id", str(workspace_id)).execute()
        workspace_context = {}
        if workspace_response.data:
            workspace_context = {
                "name": workspace_response.data[0].get("name", ""),
                "goal": workspace_response.data[0].get("goal", ""),
                "status": workspace_response.data[0].get("status", ""),
                "created_at": workspace_response.data[0].get("created_at", "")
            }
        
        # Extract themes using AI
        result = await theme_extractor.extract_themes(
            goals=goals,
            workspace_context=workspace_context,
            user_locale=user_locale,
            min_confidence=min_confidence
        )
        
        logger.info(f"✅ Theme extraction completed: {len(result.themes)} themes, confidence {result.extraction_confidence}%")
        
        # Convert to API response format
        return {
            "workspace_id": str(workspace_id),
            "themes": [
                {
                    "theme_id": theme.theme_id,
                    "name": theme.name,
                    "description": theme.description,
                    "goal_ids": theme.goal_ids,
                    "deliverable_counts": theme.deliverable_counts,
                    "confidence_score": theme.confidence_score,
                    "reasoning": theme.reasoning,
                    "business_value": theme.business_value,
                    "suggested_icon": theme.suggested_icon,
                    "extracted_at": theme.extracted_at,
                    "total_goals": len(theme.goal_ids),
                    "total_deliverables": sum(theme.deliverable_counts.values())
                }
                for theme in result.themes
            ],
            "ungrouped_goals": result.ungrouped_goals,
            "extraction_confidence": result.extraction_confidence,
            "extraction_time": result.extraction_time,
            "fallback_used": result.fallback_used,
            "user_locale": result.user_locale,
            "extraction_reasoning": result.extraction_reasoning,
            "summary": {
                "total_goals": len(goals),
                "total_themes": len(result.themes),
                "goals_grouped": sum(len(theme.goal_ids) for theme in result.themes),
                "goals_ungrouped": len(result.ungrouped_goals),
                "grouping_efficiency": round((sum(len(theme.goal_ids) for theme in result.themes) / len(goals)) * 100, 1) if goals else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Theme extraction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Theme extraction failed: {str(e)}"
        )

@router.get("/{workspace_id}/macro-deliverables", response_model=Dict[str, Any])
async def get_macro_deliverables_view(
    workspace_id: UUID,
    request: Request,
    include_deliverables: Optional[bool] = True,
    user_locale: Optional[str] = "en"
):
    """
    📦 Get macro-deliverables view with themed goal groupings
    
    Args:
        workspace_id: Workspace UUID
        include_deliverables: Include actual deliverable data for each goal
        user_locale: User language preference
        
    Returns:
        Structured macro-deliverables with themed goal groups
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"📦 Macro-deliverables view requested for workspace {workspace_id}")
    
    try:
        # Get theme extraction
        theme_result = await extract_workspace_themes(workspace_id, request, user_locale=user_locale)
        
        if not theme_result["themes"]:
            logger.info("No themes found, returning simple goal list")
            return {
                "workspace_id": str(workspace_id),
                "macro_deliverables": [],
                "view_type": "simple_goals",
                "message": "No themes detected, showing individual goals"
            }
        
        # If deliverables are requested, fetch them
        deliverables_by_goal = {}
        if include_deliverables:
            supabase = get_supabase_client()
            deliverables_response = supabase.table("deliverables").select("*").eq("workspace_id", str(workspace_id)).execute()
            
            for deliverable in deliverables_response.data or []:
                goal_id = deliverable.get("goal_id")
                if goal_id:
                    if goal_id not in deliverables_by_goal:
                        deliverables_by_goal[goal_id] = []
                    deliverables_by_goal[goal_id].append({
                        "id": deliverable["id"],
                        "title": deliverable.get("title", ""),
                        "status": deliverable.get("status", "pending"),
                        "progress": deliverable.get("progress", 0),
                        "created_at": deliverable.get("created_at", "")
                    })
        
        # Build macro-deliverables structure
        macro_deliverables = []
        for theme in theme_result["themes"]:
            theme_deliverables = []
            theme_progress = 0
            
            for goal_id in theme["goal_ids"]:
                goal_deliverables = deliverables_by_goal.get(goal_id, [])
                theme_deliverables.extend(goal_deliverables)
                
                # Calculate theme progress
                if goal_deliverables:
                    goal_progress = sum(d.get("progress", 0) for d in goal_deliverables) / len(goal_deliverables)
                    theme_progress += goal_progress
            
            if theme["goal_ids"]:
                theme_progress /= len(theme["goal_ids"])
            
            macro_deliverables.append({
                "theme_id": theme["theme_id"],
                "name": theme["name"],
                "description": theme["description"],
                "icon": theme["suggested_icon"],
                "business_value": theme["business_value"],
                "confidence_score": theme["confidence_score"],
                "goals": theme["goal_ids"],
                "deliverables": theme_deliverables if include_deliverables else [],
                "statistics": {
                    "total_goals": theme["total_goals"],
                    "total_deliverables": theme["total_deliverables"],
                    "average_progress": round(theme_progress, 1),
                    "completed_deliverables": sum(1 for d in theme_deliverables if d.get("status") == "completed")
                },
                "reasoning": theme["reasoning"]
            })
        
        return {
            "workspace_id": str(workspace_id),
            "macro_deliverables": macro_deliverables,
            "view_type": "themed_groups",
            "ungrouped_goals": theme_result["ungrouped_goals"],
            "extraction_summary": theme_result["summary"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Macro-deliverables view failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate macro-deliverables view: {str(e)}"
        )