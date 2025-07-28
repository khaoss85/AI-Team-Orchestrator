
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.ai_agents.specialist_enhanced import SpecialistAgent

@pytest.fixture
def specialist_agent():
    """Fixture to create a SpecialistAgent instance with mocked dependencies."""
    from backend.models import Agent as AgentModel
    from uuid import uuid4
    from datetime import datetime
    
    with patch('backend.ai_agents.specialist_enhanced.SDK_AVAILABLE', True):
        # Create a proper AgentModel instance
        agent_data = AgentModel(
            id=uuid4(),
            name='TestAgent',
            role='tester',
            seniority='senior',
            workspace_id=uuid4(),
            status='idle',
            skills=['testing', 'validation'],
            personality_traits=['analytical', 'methodical'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create SpecialistAgent with correct constructor
        agent = SpecialistAgent(
            agent_data=agent_data,
            all_workspace_agents_data=[]
        )
    return agent

@pytest.mark.asyncio
@patch('backend.sdk_native_guardrails.validate_task_input_ai', new_callable=AsyncMock)
async def test_specialist_agent_input_guardrail_integration(mock_validate_input, specialist_agent):
    """
    Tests that the SpecialistAgent correctly calls the AI-driven input guardrail.
    """
    # Configure the guardrail mock to return a "pass" result
    mock_validate_input.return_value = MagicMock(tripwire_triggered=False)
    
    # Mock the AI provider call
    with patch('services.ai_provider_abstraction.ai_provider_manager.call_ai', new_callable=AsyncMock) as mock_call_ai:
        mock_call_ai.return_value = {"response": "Test output"}
        
        # Create a test task for the agent's execute method
        from backend.models import Task, TaskStatus
        from uuid import uuid4
        from datetime import datetime
        
        test_task = Task(
            id=uuid4(),
            workspace_id=specialist_agent.agent_data.workspace_id,
            name="Test Task",
            description="This is a valid test input.",
            status=TaskStatus.PENDING,
            priority="high",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute the task (which should trigger guardrails)
        with patch('backend.ai_agents.specialist_enhanced.Runner') as mock_runner:
            mock_runner.run = AsyncMock(return_value=MagicMock(final_output="Test output"))
            with patch('backend.database.update_agent_status', new_callable=AsyncMock):
                result = await specialist_agent.execute(test_task)
        
        # Verify that the agent processed the task
        assert result.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
@patch('backend.sdk_native_guardrails.validate_asset_output_ai', new_callable=AsyncMock)
async def test_specialist_agent_output_guardrail_integration(mock_validate_output, specialist_agent):
    """
    Tests that the SpecialistAgent correctly calls the AI-driven output guardrail.
    """
    # Configure the guardrail mock to return a "pass" result
    mock_validate_output.return_value = MagicMock(tripwire_triggered=False)
    
    # Mock the AI provider call to produce a specific output
    test_output = "This is the generated asset."
    with patch('services.ai_provider_abstraction.ai_provider_manager.call_ai', new_callable=AsyncMock) as mock_call_ai:
        # Mock the structure that the specialist agent expects
        mock_run_result = MagicMock()
        mock_run_result.final_output = test_output
        mock_call_ai.return_value = mock_run_result

        # Create a test task for asset generation
        from backend.models import Task, TaskStatus
        from uuid import uuid4
        from datetime import datetime
        
        test_task = Task(
            id=uuid4(),
            workspace_id=specialist_agent.agent_data.workspace_id,
            name="Generate Asset",
            description="Generate an asset.",
            status=TaskStatus.PENDING,
            priority="high",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute the task
        with patch('backend.ai_agents.specialist_enhanced.Runner') as mock_runner:
            mock_runner.run = AsyncMock(return_value=mock_run_result)
            with patch('backend.database.update_agent_status', new_callable=AsyncMock):
                result = await specialist_agent.execute(test_task)
        
        # Verify that the agent processed the task
        assert result.status == TaskStatus.COMPLETED
        assert test_output in result.result
