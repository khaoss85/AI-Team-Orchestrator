#!/usr/bin/env python3
import asyncio
import logging
import unittest
from uuid import uuid4
from datetime import datetime

from agents import Agent, Runner, SQLiteSession, RunContextWrapper, function_tool
from models import Agent as AgentModel, Task, TaskStatus, TaskExecutionOutput
from ai_agents.specialist_sdk_complete import SpecialistAgent, OrchestrationContext

logging.basicConfig(level=logging.INFO)

class TestSdkIntegration(unittest.TestCase):

    def test_session_memory(self):
        async def run_test():
            agent = Agent(name="TestAgent", instructions="Remember you are in San Francisco.")
            session = SQLiteSession(str(uuid4()))
            
            await Runner.run(agent, "Where am I?", session=session)
            result = await Runner.run(agent, "What is the weather like here?", session=session)
            
            self.assertIn("San Francisco", result.final_output)
        
        asyncio.run(run_test())

    def test_run_context_wrapper(self):
        @function_tool
        def get_workspace_id(ctx: RunContextWrapper[OrchestrationContext]) -> str:
            return ctx.context.workspace_id

        async def run_test():
            agent = Agent(name="TestAgent", tools=[get_workspace_id])
            context = OrchestrationContext(
                workspace_id="test_workspace",
                task_id="test_task",
                agent_id="test_agent",
                agent_role="tester",
                agent_seniority="senior",
                task_name="Test Task",
                task_description="Test Description"
            )
            
            with RunContextWrapper[OrchestrationContext](context) as ctx:
                result = await Runner.run(agent, "What is the workspace ID?", context=ctx.context)
            
            self.assertIn("test_workspace", result.final_output)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
