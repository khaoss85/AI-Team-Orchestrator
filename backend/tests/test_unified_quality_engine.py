# backend/tests/test_unified_quality_engine.py
import pytest
import json
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ai_quality_assurance.unified_quality_engine import (
    unified_quality_engine,
    GoalValidationResult,
    ValidationSeverity,
    WorkspaceGoal
)

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock external dependencies for every test."""
    unified_quality_engine.client = AsyncMock()
    yield

@pytest.mark.asyncio
async def test_validate_workspace_goal_achievement():
    """Test the goal validation functionality."""
    workspace_id = str(uuid4())
    goal_id = uuid4()
    
    sample_goal = WorkspaceGoal(
        id=goal_id,
        workspace_id=workspace_id,
        metric_type="conversion_rate",
        target_value=10.0,
        current_value=5.0,
        description="Increase conversion rate"
    )
    
    sample_tasks = [{"name": "Run new ad campaign", "result": "Campaign reached 2 million users."}]
    
    # Mock the AI client's response
    mock_ai_response_content = {
        "severity": "medium",
        "validation_message": "Progress made, but target not yet reached.",
        "gap_percentage": 50.0,
        "confidence": 0.85,
        "recommendations": ["Optimize ad spend", "A/B test landing page"]
    }
    
    unified_quality_engine.client.chat.completions.create.return_value = AsyncMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(mock_ai_response_content)))]
    )
    
    validation_results = await unified_quality_engine.validate_workspace_goal_achievement(
        workspace_id=workspace_id,
        completed_tasks=sample_tasks,
        workspace_goals=[sample_goal]
    )
    
    assert len(validation_results) == 1
    result = validation_results[0]
    assert isinstance(result, GoalValidationResult)
    assert result.goal_id == goal_id
    assert result.severity == ValidationSeverity.MEDIUM
    assert result.gap_percentage == 50.0
    assert "Optimize ad spend" in result.recommendations

@pytest.mark.asyncio
async def test_evaluate_phase_transition_readiness():
    """Test the quality gate functionality for phase transitions."""
    workspace_id = str(uuid4())
    
    # The current implementation is a placeholder, so we test that it returns a positive result.
    gate_result = await unified_quality_engine.evaluate_phase_transition_readiness(
        workspace_id=workspace_id,
        target_phase="development"
    )
    
    assert gate_result["gate_passed"] is True
    assert gate_result["confidence"] > 0
