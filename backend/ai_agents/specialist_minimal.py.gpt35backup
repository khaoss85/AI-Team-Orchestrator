import logging
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# CRITICAL: Load environment variables for OpenAI API access
from dotenv import load_dotenv
load_dotenv()

try:
    from agents import Agent as OpenAIAgent, Runner
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from models import Agent as AgentModel, Task, TaskStatus, TaskExecutionOutput, AgentStatus
from typing import Any
from database import update_agent_status

logger = logging.getLogger(__name__)

class SpecialistAgent:
    """Minimal SpecialistAgent for testing task execution fix"""
    
    def __init__(self, agent_data: AgentModel):
        self.agent_data = agent_data
        
    async def execute(self, task: Task, session: Optional[Any] = None) -> TaskExecutionOutput:
        """Simplified task execution with OpenAI API key fix"""
        logger.info(f"🚀 Executing task {task.id} with minimal agent")
        
        try:
            await update_agent_status(str(self.agent_data.id), AgentStatus.BUSY.value)
            
            if not SDK_AVAILABLE:
                raise Exception("OpenAI Agents SDK not available")
                
            # Create minimal agent
            agent = OpenAIAgent(
                name=self.agent_data.name,
                instructions=f"""
You are a {self.agent_data.seniority} {self.agent_data.role}.
Complete the assigned task efficiently and respond with this JSON format:
{{"task_id": "{task.id}", "status": "completed", "summary": "Brief description of what you accomplished", "result": "Your concrete output"}}
""".strip(),
                model="gpt-3.5-turbo"
            )
            
            # Execute with Runner
            start_time = time.time()
            run_result = await Runner.run(agent, str(task.model_dump()), max_turns=3)
            execution_time = time.time() - start_time
            
            if not run_result.final_output:
                raise ValueError("No output from agent")
                
            # Parse result
            try:
                result_data = json.loads(str(run_result.final_output))
            except:
                # Fallback if not valid JSON
                result_data = {
                    "task_id": str(task.id),
                    "status": "completed", 
                    "summary": f"Task completed by {self.agent_data.role}",
                    "result": str(run_result.final_output)
                }
            
            output = TaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                summary=result_data.get("summary", "Task completed"),
                result=result_data.get("result", ""),
                execution_time=execution_time
            )
            
            logger.info(f"✅ Task {task.id} completed successfully in {execution_time:.2f}s")
            return output
            
        except Exception as e:
            logger.error(f"❌ Task {task.id} failed: {e}")
            return TaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.FAILED,
                summary=f"Task failed: {str(e)}",
                execution_time=0
            )
        finally:
            try:
                await update_agent_status(str(self.agent_data.id), AgentStatus.AVAILABLE.value)
            except:
                pass