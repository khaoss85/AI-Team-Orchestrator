import logging
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

# Update this import - use Handoff instead of HandoffConfig
from agents import Agent as OpenAIAgent
from agents import Runner, Handoff

from database import (
    list_agents,
    get_workspace,
    create_task,
    list_tasks
)

from models import (
    Agent as AgentModel,
    AgentStatus,
    Task,
    TaskStatus,
    WorkspaceStatus
)

from ai_agents.specialist import SpecialistAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages a team of specialist agents within a workspace"""

    def __init__(self, workspace_id: UUID):
        """
        Initialize agent manager for a workspace.

        Args:
            workspace_id: The workspace ID
        """
        self.workspace_id = workspace_id
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.agents: Dict[UUID, SpecialistAgent] = {}
        self.handoffs: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize the agent manager and load agents from database"""
        try:
            # Get workspace to verify it exists
            workspace = await get_workspace(str(self.workspace_id))
            if not workspace:
                logger.error(f"Workspace {self.workspace_id} not found in database")
                raise ValueError(f"Workspace {self.workspace_id} not found")

            logger.info(f"Initializing agent manager for workspace {self.workspace_id}")

            # Get agents for this workspace
            agents = await list_agents(str(self.workspace_id))
            
            # Check if agents is None or empty
            if not agents:
                logger.warning(f"No agents found for workspace {self.workspace_id}")
                # This isn't necessarily an error - workspace might not have agents yet
                return True
            
            logger.info(f"Found {len(agents)} agents for workspace {self.workspace_id}")

            # Initialize specialist agents with better error handling
            successful_agents = 0
            for i, agent_data in enumerate(agents):
                try:
                    # Validate agent_data is not None
                    if not agent_data:
                        logger.error(f"Agent data at index {i} is None, skipping")
                        continue
                    
                    # Check required fields
                    required_fields = ['id', 'name', 'role', 'seniority']
                    missing_fields = [field for field in required_fields if not agent_data.get(field)]
                    if missing_fields:
                        logger.error(f"Agent {agent_data.get('id', 'unknown')} missing required fields: {missing_fields}")
                        continue
                    
                    # Log agent details before creation
                    logger.info(f"Creating SpecialistAgent for: ID={agent_data['id']}, Name={agent_data.get('name')}, Role={agent_data.get('role')}")
                    
                    # Validate with Pydantic
                    try:
                        agent_model = AgentModel.model_validate(agent_data)
                    except Exception as validation_error:
                        logger.error(f"Validation failed for agent {agent_data.get('id')}: {validation_error}")
                        logger.error(f"Agent data: {agent_data}")
                        continue
                    
                    # Create SpecialistAgent
                    agent = SpecialistAgent(agent_model)
                    self.agents[UUID(agent_data["id"])] = agent
                    successful_agents += 1
                    
                    logger.info(f"Successfully created SpecialistAgent {agent_data['id']} ({agent_data['name']})")
                    
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_data.get('id', 'unknown')}: {e}")
                    logger.error(f"Agent data that caused error: {agent_data}")
                    # Continue with other agents instead of failing completely
                    continue

            # Initialize handoffs (would need to implement this)
            # self.handoffs = await list_handoffs(str(self.workspace_id))

            logger.info(f"Successfully initialized {successful_agents}/{len(agents)} agents for workspace {self.workspace_id}")
            
            # Return True if we have at least one successful agent, or if no agents were found
            return successful_agents > 0 or len(agents) == 0
            
        except Exception as e:
            logger.error(f"Failed to initialize agent manager for workspace {self.workspace_id}: {e}")
            # Log more details about the error
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    async def verify_all_agents(self):
        """Verify all agents have required capabilities"""
        verification_results = {}
        for agent_id, agent in self.agents.items():
            logger.info(f"Verifying capabilities for agent {agent_id}")
            try:
                result = await agent.verify_capabilities()
                verification_results[agent_id] = result
            except Exception as e:
                logger.error(f"Error verifying agent {agent_id}: {e}")
                verification_results[agent_id] = False
        return verification_results

    async def execute_task(self, task_id: UUID):
        """Execute a specific task"""
        try:
            # Get tasks from database
            tasks = await list_tasks(str(self.workspace_id))
            task = next((t for t in tasks if UUID(t["id"]) == task_id), None)
            if not task:
                raise ValueError(f"Task {task_id} not found")
                
            # Get agent for this task
            agent_id = UUID(task["agent_id"]) if task["agent_id"] else None
            if not agent_id or agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found for task {task_id}")
                
            # Execute task
            agent = self.agents[agent_id]
            result = await agent.execute_task(Task.model_validate(task))
            return result
        except Exception as e:
            logger.error(f"Failed to execute task {task_id}: {e}")
            raise

    async def handle_handoff(self, source_agent_id: UUID, target_agent_id: UUID, handoff_data: Dict[str, Any]):
        """Handle a handoff between agents"""
        try:
            # Verify agents exist
            if source_agent_id not in self.agents:
                raise ValueError(f"Source agent {source_agent_id} not found")
            if target_agent_id not in self.agents:
                raise ValueError(f"Target agent {target_agent_id} not found")
                
            # Get agents
            source_agent = self.agents[source_agent_id]
            target_agent = self.agents[target_agent_id]
            
            # Create a task for the target agent
            task_data = await create_task(
                workspace_id=str(self.workspace_id),
                agent_id=str(target_agent_id),
                name=f"Handoff from {source_agent.agent_data.name}",
                description=handoff_data.get("description", ""),
                status=TaskStatus.PENDING.value
            )
            
            # Execute the task
            task = Task.model_validate(task_data)
            result = await target_agent.execute_task(task)
            return result
        except Exception as e:
            logger.error(f"Failed to handle handoff: {e}")
            raise