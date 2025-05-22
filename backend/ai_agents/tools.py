import logging
import json
from typing import List, Dict, Any, Optional, Literal
from uuid import UUID

# Import corretto per function_tool
try:
    from agents import function_tool
except ImportError:
    # Fallback se il package si chiama diversamente
    from openai_agents import function_tool

# Import del Field da Pydantic, NON dall'SDK
from pydantic import Field

from models import TaskStatus
from database import create_task as db_create_task, list_agents as db_list_agents

logger = logging.getLogger(__name__)

class PMOrchestrationTools:
    @staticmethod
    @function_tool(name_override="create_and_assign_sub_task")
    async def create_and_assign_sub_task_tool(
        workspace_id: str = Field(..., description="ID of the current workspace."),
        task_name: str = Field(..., description="Clear, concise, and unique name for the new sub-task."),
        task_description: str = Field(..., description="Detailed description of what needs to be done for the sub-task, including all necessary context, inputs, and expected deliverables."),
        target_agent_role: str = Field(..., description="The role of the agent specialist best suited to perform this sub-task (e.g., 'Data Analyst', 'Copywriter', 'Social Media Marketer'). Match the role exactly as defined in the team structure."),
        priority: str = Field(default="medium", description="Priority of the sub-task: low, medium, or high"),
        parent_task_id: Optional[str] = Field(None, description="ID of the parent task from which this sub-task is derived."),
        context_data: Optional[str] = Field(None, description="Optional JSON string containing specific context or inputs for the task.")
    ) -> str:
        """
        Creates a new sub-task based on the project plan and assigns it to an agent with the specified role.
        Use this to break down a larger plan into actionable steps for the team.
        The task description must be comprehensive.
        """
        logger.info(f"PM Tool 'create_and_assign_sub_task': Creating sub-task '{task_name}' for role '{target_agent_role}' in workspace '{workspace_id}'.")
        try:
            # 1. Trova un agente attivo con il ruolo target
            agents_in_db = await db_list_agents(workspace_id=workspace_id)
            
            compatible_agents = [
                agent for agent in agents_in_db
                if agent.get("role", "").lower() == target_agent_role.lower()
                and agent.get("status") == "active"
            ]

            if not compatible_agents:
                error_msg = f"No active agent found for role '{target_agent_role}' in workspace {workspace_id}."
                logger.warning(error_msg)
                return json.dumps({
                    "success": False, 
                    "task_id": None, 
                    "error": error_msg,
                    "suggestion": "Verify the target_agent_role or ensure an agent with this role is active."
                })

            # Scegli un agente (per ora il primo)
            target_agent_id_str = str(compatible_agents[0]["id"])
            assigned_agent_name = compatible_agents[0]["name"]
            
            # Parse context_data se fornito
            context_dict = None
            if context_data:
                try:
                    context_dict = json.loads(context_data)
                except json.JSONDecodeError as je:
                    logger.warning(f"Invalid JSON in context_data: {je}. Using as plain text in description.")
                    # Se non è JSON valido, aggiungilo alla descrizione del task
                    task_description += f"\n\nAdditional Context: {context_data}"

            # 2. Crea il task nel database
            created_task_data = await db_create_task(
                workspace_id=workspace_id,
                agent_id=target_agent_id_str,
                assigned_to_role=target_agent_role,
                name=task_name,
                description=task_description,
                status=TaskStatus.PENDING.value,
                priority=priority,
                parent_task_id=parent_task_id,

                # TRACKING AUTOMATICO
                created_by_task_id=parent_task_id,  # Questo subtask è creato da un task padre
                created_by_agent_id=None,  # Sarà riempito automaticamente dall'agent_id del parent task
                creation_type="pm_delegation",  # Delega da parte del Project Manager

                # CONTEXT DATA SPECIFICO
                context_data={
                    **(context_dict or {}),  # Mantieni i dati originali se forniti
                    "pm_tool_created": True,
                    "tool_call_timestamp": datetime.now().isoformat(),
                    "delegated_via": "pm_orchestration_tool"
                }
            )

            if created_task_data and created_task_data.get("id"):
                task_created_id = created_task_data['id']
                msg = f"Sub-task '{task_name}' (ID: {task_created_id}) created successfully and assigned to agent {assigned_agent_name} (Role: {target_agent_role})."
                logger.info(msg)
                return json.dumps({
                    "success": True,
                    "task_id": task_created_id,
                    "assigned_agent_id": target_agent_id_str,
                    "assigned_agent_name": assigned_agent_name,
                    "message": msg
                })
            else:
                error_msg = f"Database error: Failed to create sub-task '{task_name}'."
                logger.error(f"{error_msg} DB response: {created_task_data}")
                return json.dumps({"success": False, "task_id": None, "error": error_msg})

        except Exception as e:
            logger.error(f"Critical error in create_and_assign_sub_task_tool: {e}", exc_info=True)
            return json.dumps({"success": False, "task_id": None, "error": f"An unexpected error occurred: {str(e)}"})

    @staticmethod
    @function_tool(name_override="get_team_roles_and_status")
    async def get_team_roles_and_status_tool(
        workspace_id: str = Field(..., description="ID of the workspace to check")
    ) -> str:
        """
        Get information about available team roles and their current status.
        Useful for the PM to understand what specialist roles are available for task assignment.
        """
        try:
            agents_in_db = await db_list_agents(workspace_id=workspace_id)
            
            team_info = []
            for agent in agents_in_db:
                team_info.append({
                    "name": agent.get("name"),
                    "role": agent.get("role"),
                    "status": agent.get("status"),
                    "seniority": agent.get("seniority"),
                    "description": agent.get("description", "")[:100] + "..." if agent.get("description", "") else "No description"
                })
            
            result = {
                "workspace_id": workspace_id,
                "team_members": team_info,
                "total_agents": len(team_info),
                "active_agents": len([a for a in team_info if a["status"] == "active"])
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error in get_team_roles_and_status_tool: {e}", exc_info=True)
            return json.dumps({"error": str(e), "team_members": []})

class CommonTools:
    """Common tools that can be used by any agent"""
    
    @staticmethod
    @function_tool
    async def store_data(key: str, value: str) -> bool:
        """
        Store data in the agent's memory.
        
        Args:
            key: The key to store the data under
            value: The data to store (as JSON string)
            
        Returns:
            Boolean indicating success
        """
        try:
            # In a real implementation, this would store data in a database
            # For now, we'll just log it
            logger.info(f"Storing data under key '{key}': {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False
    
    @staticmethod
    @function_tool
    async def retrieve_data(key: str) -> str:
        """
        Retrieve data from the agent's memory.
        
        Args:
            key: The key to retrieve data from
            
        Returns:
            The stored data as JSON string, or empty string if not found
        """
        try:
            # In a real implementation, this would retrieve data from a database
            # For now, we'll just return a placeholder
            logger.info(f"Retrieving data for key '{key}'")
            return json.dumps({"placeholder": "This is placeholder data"})
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return ""
    
    @staticmethod
    @function_tool
    async def search_web(query: str) -> str:
        """
        Search the web for information.
        
        Args:
            query: The search query
            
        Returns:
            Search results as JSON string
        """
        try:
            # In a real implementation, this would use a real search API
            # For now, we'll just return placeholder results
            logger.info(f"Searching web for: {query}")
            time.sleep(1)  # Simulate network delay
            
            results = {
                "results": [
                    {
                        "title": f"Search result 1 for '{query}'",
                        "url": "https://example.com/1",
                        "snippet": "This is a snippet of the first search result."
                    },
                    {
                        "title": f"Search result 2 for '{query}'",
                        "url": "https://example.com/2",
                        "snippet": "This is a snippet of the second search result."
                    },
                ],
                "total": 2
            }
            return json.dumps(results)
        except Exception as e:
            logger.error(f"Failed to search web: {e}")
            return json.dumps({"results": [], "total": 0, "error": str(e)})
    
    @staticmethod
    @function_tool
    async def fetch_url(url: str) -> str:
        """
        Fetch content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            The content of the URL as JSON string
        """
        try:
            # In a real implementation, this would use requests or aiohttp
            # For now, we'll just return placeholder content
            logger.info(f"Fetching URL: {url}")
            time.sleep(1)  # Simulate network delay
            
            result = {
                "url": url,
                "content": f"This is placeholder content for {url}",
                "status": 200
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to fetch URL: {e}")
            return json.dumps({"url": url, "content": None, "status": 500, "error": str(e)})

class ContentTools:
    """Tools specific to content creation and analysis"""
    
    @staticmethod
    @function_tool
    async def analyze_text(text: str) -> str:
        """
        Analyze text for sentiment, entities, etc.
        
        Args:
            text: The text to analyze
            
        Returns:
            Analysis results as JSON string
        """
        try:
            # In a real implementation, this would use a NLP service
            # For now, we'll just return placeholder results
            logger.info(f"Analyzing text: {text[:100]}...")
            time.sleep(0.5)  # Simulate processing delay
            
            # Simple sentiment analysis based on keywords
            sentiment = "neutral"
            if any(word in text.lower() for word in ["great", "good", "excellent", "happy", "love"]):
                sentiment = "positive"
            elif any(word in text.lower() for word in ["bad", "terrible", "awful", "sad", "hate"]):
                sentiment = "negative"
                
            # Simple entity extraction using regex
            emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
            urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
            
            result = {
                "sentiment": sentiment,
                "entities": {
                    "emails": emails,
                    "urls": urls
                },
                "length": len(text),
                "word_count": len(text.split())
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to analyze text: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def generate_headlines(topic: str, count: int = 5) -> str:
        """
        Generate headline ideas for a topic.
        
        Args:
            topic: The topic to generate headlines for
            count: Number of headlines to generate
            
        Returns:
            List of headline ideas as JSON string
        """
        try:
            # In a real implementation, this would use a creative AI service
            # For now, we'll just return placeholder headlines
            logger.info(f"Generating {count} headlines for topic: {topic}")
            
            prefixes = [
                "The Ultimate Guide to",
                "10 Ways to Improve Your",
                "Why You Should Care About",
                "The Future of",
                "How to Master",
                "Understanding",
                "The Secret to",
                "What Nobody Tells You About",
                "The Rise of",
                "Exploring"
            ]
            
            headlines = [f"{prefixes[i % len(prefixes)]} {topic}" for i in range(count)]
            return json.dumps(headlines)
        except Exception as e:
            logger.error(f"Failed to generate headlines: {e}")
            return json.dumps([])

class DataTools:
    """Tools specific to data analysis and visualization"""
    
    @staticmethod
    @function_tool
    async def analyze_data(data: str, metric_column: str) -> str:
        """
        Analyze data for basic statistics.
        
        Args:
            data: List of data points as JSON string
            metric_column: The column to analyze
            
        Returns:
            Statistical analysis as JSON string
        """
        try:
            # Parse the JSON data
            data_list = json.loads(data)
            
            # Extract values for the given column
            values = [item.get(metric_column, 0) for item in data_list if metric_column in item]
            
            if not values:
                return json.dumps({"error": f"No data found for column '{metric_column}'"})
                
            count = len(values)
            total = sum(values)
            avg = total / count if count > 0 else 0
            minimum = min(values) if values else 0
            maximum = max(values) if values else 0
            
            result = {
                "count": count,
                "sum": total,
                "average": avg,
                "min": minimum,
                "max": maximum
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def find_correlation(data: str, column1: str, column2: str) -> str:
        """
        Find correlation between two columns in the data.
        
        Args:
            data: List of data points as JSON string
            column1: First column name
            column2: Second column name
            
        Returns:
            Correlation information as JSON string
        """
        try:
            # Parse the JSON data
            data_list = json.loads(data)
            
            # Extract paired values
            pairs = [(item.get(column1), item.get(column2)) for item in data_list 
                     if column1 in item and column2 in item]
            
            if not pairs:
                return json.dumps({"error": f"No paired data found for columns '{column1}' and '{column2}'"})
                
            # In a real implementation, we would calculate actual correlation
            # For now, just return a placeholder
            result = {
                "correlation": 0.7,  # Placeholder value
                "interpretation": "Strong positive correlation",
                "sample_size": len(pairs)
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to find correlation: {e}")
            return json.dumps({"error": str(e)})
    
    @staticmethod
    @function_tool
    async def generate_chart_data(data: str, x_column: str, y_column: str) -> str:
        """
        Generate data for charts.
        
        Args:
            data: List of data points as JSON string
            x_column: Column for x-axis
            y_column: Column for y-axis
            
        Returns:
            Chart data as JSON string
        """
        try:
            # Parse the JSON data
            data_list = json.loads(data)
            
            # Extract data points
            chart_data = [
                {"x": item.get(x_column), "y": item.get(y_column)}
                for item in data_list if x_column in item and y_column in item
            ]
            
            if not chart_data:
                return json.dumps({"error": f"No data found for columns '{x_column}' and '{y_column}'"})
                
            result = {
                "chart_type": "line",  # Default recommendation
                "data": chart_data,
                "x_label": x_column,
                "y_label": y_column
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to generate chart data: {e}")
            return json.dumps({"error": str(e)})

class AgentTools:
    """Tools for agent-to-agent communication and management"""
    
    @staticmethod
    @function_tool
    async def update_health(agent_id: str, status: str, details: str = None) -> bool:
        """
        Update the health status of an agent.
        
        Args:
            agent_id: The ID of the agent
            status: Health status (healthy, degraded, unhealthy)
            details: Optional details about the health status as JSON string
            
        Returns:
            Boolean indicating success
        """
        try:
            details_dict = json.loads(details) if details else {}
            health = {
                "status": status,
                "last_update": datetime.now().isoformat(),
                "details": details_dict
            }
            
            await update_agent_status(
                agent_id=agent_id,
                status=None,  # Don't update agent status, just health
                health=health
            )
            
            logger.info(f"Updated health status for agent {agent_id} to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent health: {e}")
            return False
    
    @staticmethod
    @function_tool
    async def get_available_handoffs(agent_id: str) -> str:
        """
        Get available handoff options for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List of available handoff options as JSON string
        """
        try:
            # In a real implementation, this would query the database for handoffs
            # For now, we'll just return placeholder data
            handoffs = [
                {
                    "target_agent_id": "00000000-0000-0000-0000-000000000001",
                    "target_agent_name": "Content Specialist",
                    "description": "Handoff for content creation"
                },
                {
                    "target_agent_id": "00000000-0000-0000-0000-000000000002",
                    "target_agent_name": "Data Analyst",
                    "description": "Handoff for data analysis"
                }
            ]
            return json.dumps(handoffs)
        except Exception as e:
            logger.error(f"Failed to get available handoffs: {e}")
            return json.dumps([])