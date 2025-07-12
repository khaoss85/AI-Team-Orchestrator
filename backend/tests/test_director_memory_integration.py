# backend/tests/test_director_memory_integration.py
import pytest
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ai_agents.director import DirectorAgent
from backend.models import DirectorTeamProposal, AgentSeniority

@pytest.fixture
def director_agent():
    """Fixture to provide a DirectorAgent instance."""
    return DirectorAgent()

@pytest.fixture
def base_proposal_request():
    """Fixture for a base DirectorTeamProposal request."""
    return DirectorTeamProposal(
        workspace_id=uuid4(),
        requirements="Develop a new marketing campaign.",
        budget_limit=3000.0
    )

@pytest.mark.asyncio
@patch('backend.ai_agents.director.DirectorAgent._group_skills_for_design')
@patch('backend.ai_agents.director.unified_memory_engine.get_best_performing_agents')
async def test_director_uses_performance_memory_to_boost_seniority(
    mock_get_performers, mock_group_skills, director_agent, base_proposal_request
):
    """
    Verifies that the DirectorAgent promotes an agent to a higher seniority
    if memory indicates a history of high-quality performance for that role.
    """
    # 1. SETUP:
    # Mock skill grouping to return a single, high-importance group
    mock_group_skills.return_value = [{
        "domain": "marketing_strategy",
        "skills": ["market_analysis", "campaign_planning"],
        "importance": "high"
    }]
    
    # Mock the memory engine to return a high-performing agent for this role
    mock_get_performers.return_value = [{
        "agent_id": str(uuid4()),
        "avg_quality_score": 0.9,  # High score, should trigger a boost
        "agents": {"name": "TopPerformer", "role": "Marketing Specialist", "seniority": "senior"}
    }]

    # Mock the LLM call within the director to return a basic structure
    with patch('backend.ai_agents.director.Runner.run') as mock_runner_run:
        mock_runner_run.return_value = AsyncMock(
            final_output=json.dumps({
                "agents": [],
                "handoffs": [],
                "estimated_cost": {},
                "rationale": "Test"
            })
        )

        # 2. EXECUTION:
        # The budget (3000) would normally result in a SENIOR agent at most.
        # The performance boost should push this to EXPERT.
        proposal = await director_agent.create_team_proposal(base_proposal_request)

        # 3. VERIFICATION:
        assert len(proposal.agents) > 0, "No agents were created in the proposal."
        
        # Find the specialist created for our skill group
        specialist_agent = next((agent for agent in proposal.agents if "Specialist" in agent.role), None)
        assert specialist_agent is not None, "Specialist agent not found in the team."
        
        # The key assertion: The agent should be promoted to EXPERT due to the memory boost
        assert specialist_agent.seniority == AgentSeniority.EXPERT, \
            f"Agent seniority was {specialist_agent.seniority}, but EXPERT was expected due to performance boost."
            
        mock_get_performers.assert_called_once_with(
            workspace_id=base_proposal_request.workspace_id,
            role="marketing_strategy",
            limit=1
        )
        logging.info("✅ Test passed: Director correctly used performance memory to upgrade agent seniority.")




