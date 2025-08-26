#!/usr/bin/env python3
"""
🧠 RECOVERY ANALYSIS API ROUTES
===============================

FastAPI routes for accessing the RecoveryAnalysisEngine functionality.
Provides real-time recovery analysis, statistics, and health monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import the recovery analysis engine
try:
    from services.recovery_analysis_engine import (
        recovery_analysis_engine,
        analyze_task_recovery,
        should_attempt_recovery,
        get_recovery_analysis_stats,
        RecoveryStrategy,
        RecoveryDecision
    )
    RECOVERY_ANALYSIS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"RecoveryAnalysisEngine not available: {e}")
    RECOVERY_ANALYSIS_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recovery-analysis", tags=["Recovery Analysis"])

# Pydantic models for API requests/responses
class RecoveryAnalysisRequest(BaseModel):
    """Request model for manual recovery analysis"""
    task_id: str = Field(..., description="Task ID to analyze")
    workspace_id: str = Field(..., description="Workspace ID")
    error_message: str = Field(..., description="Error message from failed task")
    error_type: str = Field(..., description="Type of error (e.g., ValidationError)")
    agent_id: Optional[str] = Field(None, description="Agent ID if known")
    task_name: Optional[str] = Field(None, description="Task name")
    task_description: Optional[str] = Field("", description="Task description")
    execution_stage: Optional[str] = Field(None, description="Execution stage where failure occurred")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class RecoveryAnalysisResponse(BaseModel):
    """Response model for recovery analysis"""
    success: bool = Field(..., description="Whether analysis was successful")
    
    # Core decision
    recovery_decision: Optional[str] = Field(None, description="Recovery decision (retry, skip, escalate, circuit_break)")
    recovery_strategy: Optional[str] = Field(None, description="Specific recovery strategy")
    confidence_score: Optional[float] = Field(None, description="Confidence in the decision (0.0-1.0)")
    
    # Timing and retry information
    recommended_delay_seconds: Optional[float] = Field(None, description="Recommended delay before retry")
    max_retry_attempts: Optional[int] = Field(None, description="Maximum number of retry attempts")
    
    # Analysis details
    analysis_reasoning: Optional[str] = Field(None, description="Detailed reasoning for the decision")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    success_indicators: List[str] = Field(default_factory=list, description="Indicators of potential success")
    
    # Context
    requires_different_agent: Optional[bool] = Field(None, description="Whether a different agent is needed")
    requires_enhanced_context: Optional[bool] = Field(None, description="Whether enhanced context is needed")
    estimated_success_probability: Optional[float] = Field(None, description="Estimated success probability")
    
    # Metadata
    failure_pattern_matched: Optional[str] = Field(None, description="Matched failure pattern ID")
    historical_success_rate: Optional[float] = Field(None, description="Historical success rate for this pattern")
    analysis_time_ms: Optional[float] = Field(None, description="Time taken for analysis in milliseconds")
    ai_analysis_used: Optional[bool] = Field(None, description="Whether AI analysis was used")
    
    # Error information
    error: Optional[str] = Field(None, description="Error message if analysis failed")

class RecoveryDecisionRequest(BaseModel):
    """Request model for quick recovery decision"""
    task_id: str = Field(..., description="Task ID")
    workspace_id: str = Field(..., description="Workspace ID")
    error_message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type")

class RecoveryDecisionResponse(BaseModel):
    """Response model for recovery decision"""
    should_attempt_recovery: bool = Field(..., description="Whether recovery should be attempted")
    analysis: Optional[RecoveryAnalysisResponse] = Field(None, description="Full analysis if recovery recommended")

class RecoveryStatsResponse(BaseModel):
    """Response model for recovery statistics"""
    total_analyses: int = Field(..., description="Total number of analyses performed")
    average_analysis_time_ms: float = Field(..., description="Average analysis time")
    component_reuse_percentage: float = Field(..., description="Component reuse percentage")
    
    strategy_distribution: Dict[str, int] = Field(..., description="Distribution of recovery strategies")
    confidence_distribution: Dict[str, int] = Field(..., description="Distribution of confidence levels")
    recovery_decision_distribution: Dict[str, int] = Field(..., description="Distribution of recovery decisions")
    
    ai_analysis_usage_percentage: float = Field(..., description="Percentage of analyses using AI")
    component_reuse_stats: Dict[str, int] = Field(..., description="Component reuse statistics")

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    healthy: bool = Field(..., description="Overall health status")
    enabled: bool = Field(..., description="Whether recovery analysis is enabled")
    ai_decisions_enabled: bool = Field(..., description="Whether AI decisions are enabled")
    confidence_threshold: float = Field(..., description="Confidence threshold for decisions")
    max_attempts_per_task: int = Field(..., description="Maximum recovery attempts per task")
    
    component_availability: Dict[str, bool] = Field(..., description="Component availability status")
    analysis_count: int = Field(..., description="Total analyses performed")
    average_analysis_time_ms: float = Field(..., description="Average analysis time")
    reuse_target_percentage: float = Field(..., description="Target component reuse percentage")

@router.post("/analyze", response_model=RecoveryAnalysisResponse)
async def analyze_recovery(request: RecoveryAnalysisRequest):
    """
    Perform comprehensive recovery analysis for a failed task
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery Analysis Engine not available"
        )
    
    try:
        logger.info(f"🧠 API: Analyzing recovery for task {request.task_id}")
        
        # Perform recovery analysis
        analysis_result = await analyze_task_recovery(
            task_id=request.task_id,
            workspace_id=request.workspace_id,
            error_message=request.error_message,
            error_type=request.error_type,
            agent_id=request.agent_id,
            task_name=request.task_name,
            task_description=request.task_description,
            execution_stage=request.execution_stage,
            metadata=request.metadata
        )
        
        # Convert result to API response
        return RecoveryAnalysisResponse(
            success=True,
            recovery_decision=analysis_result.recovery_decision.value,
            recovery_strategy=analysis_result.recovery_strategy.value,
            confidence_score=analysis_result.confidence_score,
            recommended_delay_seconds=analysis_result.recommended_delay_seconds,
            max_retry_attempts=analysis_result.max_retry_attempts,
            analysis_reasoning=analysis_result.analysis_reasoning,
            risk_factors=analysis_result.risk_factors,
            success_indicators=analysis_result.success_indicators,
            requires_different_agent=analysis_result.requires_different_agent,
            requires_enhanced_context=analysis_result.requires_enhanced_context,
            estimated_success_probability=analysis_result.estimated_success_probability,
            failure_pattern_matched=analysis_result.failure_pattern_matched,
            historical_success_rate=analysis_result.historical_success_rate,
            analysis_time_ms=analysis_result.analysis_time_ms,
            ai_analysis_used=analysis_result.ai_analysis_used
        )
        
    except Exception as e:
        logger.error(f"Recovery analysis API error for task {request.task_id}: {e}")
        return RecoveryAnalysisResponse(
            success=False,
            error=str(e)
        )

@router.post("/should-recover", response_model=RecoveryDecisionResponse)
async def check_recovery_decision(request: RecoveryDecisionRequest):
    """
    Quick decision on whether recovery should be attempted for a failed task
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery Analysis Engine not available"
        )
    
    try:
        logger.info(f"🤔 API: Checking recovery decision for task {request.task_id}")
        
        # Get recovery decision
        should_recover, analysis_result = await should_attempt_recovery(
            task_id=request.task_id,
            workspace_id=request.workspace_id,
            error_message=request.error_message,
            error_type=request.error_type
        )
        
        # Convert analysis result if available
        analysis_response = None
        if analysis_result:
            analysis_response = RecoveryAnalysisResponse(
                success=True,
                recovery_decision=analysis_result.recovery_decision.value,
                recovery_strategy=analysis_result.recovery_strategy.value,
                confidence_score=analysis_result.confidence_score,
                recommended_delay_seconds=analysis_result.recommended_delay_seconds,
                max_retry_attempts=analysis_result.max_retry_attempts,
                analysis_reasoning=analysis_result.analysis_reasoning,
                risk_factors=analysis_result.risk_factors,
                success_indicators=analysis_result.success_indicators,
                requires_different_agent=analysis_result.requires_different_agent,
                requires_enhanced_context=analysis_result.requires_enhanced_context,
                estimated_success_probability=analysis_result.estimated_success_probability,
                failure_pattern_matched=analysis_result.failure_pattern_matched,
                historical_success_rate=analysis_result.historical_success_rate,
                analysis_time_ms=analysis_result.analysis_time_ms,
                ai_analysis_used=analysis_result.ai_analysis_used
            )
        
        return RecoveryDecisionResponse(
            should_attempt_recovery=should_recover,
            analysis=analysis_response
        )
        
    except Exception as e:
        logger.error(f"Recovery decision API error for task {request.task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recovery decision failed: {str(e)}"
        )

@router.get("/stats", response_model=RecoveryStatsResponse)
async def get_recovery_stats(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID")
):
    """
    Get recovery analysis statistics
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery Analysis Engine not available"
        )
    
    try:
        logger.debug(f"📊 API: Getting recovery stats" + (f" for workspace {workspace_id}" if workspace_id else ""))
        
        # Get statistics
        stats = await get_recovery_analysis_stats(workspace_id)
        
        return RecoveryStatsResponse(
            total_analyses=stats['total_analyses'],
            average_analysis_time_ms=stats['average_analysis_time_ms'],
            component_reuse_percentage=stats['component_reuse_percentage'],
            strategy_distribution=stats['strategy_distribution'],
            confidence_distribution=stats['confidence_distribution'],
            recovery_decision_distribution=stats['recovery_decision_distribution'],
            ai_analysis_usage_percentage=stats['ai_analysis_usage_percentage'],
            component_reuse_stats=stats['component_reuse_stats']
        )
        
    except Exception as e:
        logger.error(f"Recovery stats API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recovery stats: {str(e)}"
        )

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check for the Recovery Analysis Engine
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        return HealthCheckResponse(
            healthy=False,
            enabled=False,
            ai_decisions_enabled=False,
            confidence_threshold=0.0,
            max_attempts_per_task=0,
            component_availability={},
            analysis_count=0,
            average_analysis_time_ms=0.0,
            reuse_target_percentage=0.0
        )
    
    try:
        # Get health information
        health_info = await recovery_analysis_engine.health_check()
        
        return HealthCheckResponse(
            healthy=True,
            enabled=health_info['enabled'],
            ai_decisions_enabled=health_info['ai_decisions_enabled'],
            confidence_threshold=health_info['confidence_threshold'],
            max_attempts_per_task=health_info['max_attempts_per_task'],
            component_availability=health_info['component_availability'],
            analysis_count=health_info['analysis_count'],
            average_analysis_time_ms=health_info['average_analysis_time_ms'],
            reuse_target_percentage=health_info['reuse_target_percentage']
        )
        
    except Exception as e:
        logger.error(f"Recovery health check API error: {e}")
        return HealthCheckResponse(
            healthy=False,
            enabled=False,
            ai_decisions_enabled=False,
            confidence_threshold=0.0,
            max_attempts_per_task=0,
            component_availability={'error': str(e)},
            analysis_count=0,
            average_analysis_time_ms=0.0,
            reuse_target_percentage=90.0
        )

@router.get("/patterns")
async def get_recovery_patterns():
    """
    Get available recovery patterns and their configurations
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery Analysis Engine not available"
        )
    
    try:
        patterns = recovery_analysis_engine.pattern_matcher.recovery_patterns
        return {
            'success': True,
            'patterns': patterns,
            'pattern_count': len(patterns)
        }
        
    except Exception as e:
        logger.error(f"Get patterns API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recovery patterns: {str(e)}"
        )

# Quality Gate Test Endpoint
@router.post("/test/orchestration-context")
async def test_orchestration_context_recovery():
    """
    🎯 QUALITY GATE TEST: Test OrchestrationContext field missing recovery decision
    """
    if not RECOVERY_ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery Analysis Engine not available"
        )
    
    try:
        # Import the test function
        from services.recovery_analysis_engine import test_orchestration_context_recovery_decision
        
        # Run the quality gate test
        success = await test_orchestration_context_recovery_decision()
        
        return {
            'success': True,
            'quality_gate_passed': success,
            'test_description': 'OrchestrationContext field missing recovery decision test',
            'expected_result': 'IMMEDIATE_RETRY with >90% confidence'
        }
        
    except Exception as e:
        logger.error(f"Quality gate test API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quality gate test failed: {str(e)}"
        )