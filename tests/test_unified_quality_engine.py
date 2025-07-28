
import pytest
from unittest.mock import AsyncMock, patch
from backend.ai_quality_assurance.unified_quality_engine import UnifiedQualityEngine

@pytest.fixture
def quality_engine():
    """Fixture to create a UnifiedQualityEngine instance."""
    return UnifiedQualityEngine()

@pytest.mark.asyncio
async def test_evaluate_asset_quality_ai_driven_pass(quality_engine):
    """
    Tests that the AI-driven asset quality evaluation passes when the quality score is above the dynamic threshold.
    """
    with patch('backend.ai_quality_assurance.unified_quality_engine.unified_quality_engine.validate_asset_quality', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {'quality_score': 0.9, 'reason': 'High quality'}
        
        result = await quality_engine.evaluate_asset_quality(
            content="This is a high-quality asset.",
            task_context={'agent_name': 'senior_developer'},
            workspace_id='test_workspace'
        )
        
        assert result['quality_score'] == 90
        assert result['dynamic_threshold'] == 80
        assert result['validation_passed'] is True
        assert result['ai_driven'] is True

@pytest.mark.asyncio
async def test_evaluate_asset_quality_ai_driven_fail(quality_engine):
    """
    Tests that the AI-driven asset quality evaluation fails when the quality score is below the dynamic threshold.
    """
    with patch('backend.ai_quality_assurance.unified_quality_engine.unified_quality_engine.validate_asset_quality', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {'quality_score': 0.6, 'reason': 'Low quality'}
        
        result = await quality_engine.evaluate_asset_quality(
            content="This is a low-quality asset.",
            task_context={'agent_name': 'junior_developer'},
            workspace_id='test_workspace'
        )
        
        assert result['quality_score'] == 60
        assert result['dynamic_threshold'] == 70
        assert result['validation_passed'] is False
        assert result['ai_driven'] is True

@pytest.mark.asyncio
async def test_validate_task_input_ai_driven_valid(quality_engine):
    """
    Tests that the AI-driven task input validation passes for a valid input.
    """
    with patch('backend.ai_quality_assurance.unified_quality_engine.unified_quality_engine.evaluate_with_ai', new_callable=AsyncMock) as mock_evaluate:
        mock_evaluate.return_value = {
            'response': '{"is_valid": true, "confidence": 0.9, "validation_reason": "Input is clear and actionable."}'
        }
        
        result = await quality_engine.validate_task_input(
            content="Create a detailed report on Q3 sales figures.",
            agent_context={'agent_name': 'Data Analyst', 'agent_role': 'analyst'},
            workspace_id='test_workspace'
        )
        
        assert result['is_valid'] is True
        assert result['validation_reason'] == "Input is clear and actionable."
        assert result['ai_driven'] is True

@pytest.mark.asyncio
async def test_validate_task_input_ai_driven_invalid(quality_engine):
    """
    Tests that the AI-driven task input validation fails for an invalid input.
    """
    with patch('backend.ai_quality_assurance.unified_quality_engine.unified_quality_engine.evaluate_with_ai', new_callable=AsyncMock) as mock_evaluate:
        mock_evaluate.return_value = {
            'response': '{"is_valid": false, "confidence": 0.95, "validation_reason": "Input is too vague."}'
        }
        
        result = await quality_engine.validate_task_input(
            content="Analyze data.",
            agent_context={'agent_name': 'Data Analyst', 'agent_role': 'analyst'},
            workspace_id='test_workspace'
        )
        
        assert result['is_valid'] is False
        assert result['validation_reason'] == "Input is too vague."
        assert result['ai_driven'] is True

@pytest.mark.asyncio
async def test_validate_task_input_fallback_short(quality_engine):
    """
    Tests the fallback mechanism for task input validation when the input is too short.
    """
    with patch('backend.ai_quality_assurance.unified_quality_engine.unified_quality_engine.evaluate_with_ai', new_callable=AsyncMock) as mock_evaluate:
        mock_evaluate.side_effect = Exception("AI service unavailable")
        
        result = await quality_engine.validate_task_input(
            content="Report.",
            agent_context={'agent_name': 'Data Analyst', 'agent_role': 'analyst'},
            workspace_id='test_workspace'
        )
        
        assert result['is_valid'] is False
        assert "too short" in result['validation_reason']
        assert result['ai_driven'] is False
