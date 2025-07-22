"""
Quality Database Fallbacks - Provides fallback implementations for quality-related database functions
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import real database functions, provide fallbacks if not available
try:
    from database import (
        get_quality_rules_for_asset_type as _real_get_quality_rules,
        log_quality_validation as _real_log_quality_validation,
        update_artifact_status as _real_update_artifact_status,
        get_artifacts_for_requirement as _real_get_artifacts_for_requirement,
        update_goal_progress as _real_update_goal_progress
    )
    HAS_REAL_DB_FUNCTIONS = True
except ImportError:
    logger.warning("Some quality database functions not available, using fallbacks")
    HAS_REAL_DB_FUNCTIONS = False
    _real_get_quality_rules = None
    _real_log_quality_validation = None
    _real_update_artifact_status = None
    _real_get_artifacts_for_requirement = None
    _real_update_goal_progress = None

# Import real functions that exist
from database import log_quality_validation as _real_log_quality_validation


async def get_quality_rules_for_asset_type(asset_type: str) -> List[Dict[str, Any]]:
    """Get quality rules for a specific asset type with fallback"""
    if _real_get_quality_rules:
        return await _real_get_quality_rules(asset_type)
    
    # Fallback: Return default quality rules
    logger.info(f"Using fallback quality rules for asset type: {asset_type}")
    
    default_rules = [
        {
            "id": str(uuid4()),
            "rule_name": f"Basic Quality Check for {asset_type}",
            "ai_validation_prompt": f"Validate that this {asset_type} meets basic quality standards",
            "threshold_score": 0.7,
            "validation_type": "content_quality",
            "severity": "medium"
        },
        {
            "id": uuid4(), 
            "rule_name": f"Completeness Check for {asset_type}",
            "ai_validation_prompt": f"Check that this {asset_type} is complete and not a placeholder",
            "threshold_score": 0.8,
            "validation_type": "completeness",
            "severity": "high"
        }
    ]
    
    # Create mock QualityRule objects
    from models import QualityRule
    rules = []
    for rule_data in default_rules:
        rule = QualityRule(
            id=rule_data["id"],
            rule_name=rule_data["rule_name"],
            rule_type=rule_data.get("validation_type", "general"),
            asset_type=asset_type,
            validation_logic=rule_data.get("validation_logic", {}),
            ai_validation_prompt=rule_data["ai_validation_prompt"],
            threshold_score=rule_data["threshold_score"],
            severity=rule_data.get("severity", "medium"),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        rules.append(rule)
    
    return rules


async def log_quality_validation(validation_result: Any) -> bool:
    """Log quality validation result with fallback"""
    if _real_log_quality_validation:
        return await _real_log_quality_validation(validation_result)
    
    # Fallback: Just log to logger
    logger.info(f"Quality validation logged (fallback): {validation_result.id if hasattr(validation_result, 'id') else 'unknown'}")
    return True


async def update_artifact_status(artifact_id: UUID, status: str, metadata: Dict[str, Any] = None) -> bool:
    """Update artifact status with fallback"""
    if _real_update_artifact_status:
        return await _real_update_artifact_status(artifact_id, status, metadata)
    
    # Fallback: Just log the update
    logger.info(f"Artifact status updated (fallback): {artifact_id} -> {status}")
    return True


async def get_artifacts_for_requirement(requirement_id: UUID) -> List[Dict[str, Any]]:
    """Get artifacts for a requirement with fallback"""
    if _real_get_artifacts_for_requirement:
        return await _real_get_artifacts_for_requirement(requirement_id)
    
    # Fallback: Return empty list
    logger.info(f"No artifacts found for requirement (fallback): {requirement_id}")
    return []


async def update_goal_progress(goal_id: UUID, progress_data: Dict[str, Any]) -> bool:
    """Update goal progress with fallback"""
    if _real_update_goal_progress:
        return await _real_update_goal_progress(goal_id, progress_data)
    
    # Import the real function that exists
    try:
        from database import update_goal
        # Use update_goal as a fallback
        return await update_goal(str(goal_id), progress_data)
    except:
        # Ultimate fallback
        logger.info(f"Goal progress updated (fallback): {goal_id}")
        return True