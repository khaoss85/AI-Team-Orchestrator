# backend/ai_agents/tools.py
import logging
import json
from typing import List, Dict, Any, Optional, Literal, Union, Annotated
from uuid import UUID
from datetime import datetime
from pydantic import Field

try:
    from agents import function_tool
except ImportError:
    from openai_agents import function_tool # type: ignore

from models import TaskStatus, ProjectPhase # Assicurati che ProjectPhase sia importato
from database import (
    create_task as db_create_task,
    list_agents as db_list_agents,
    list_tasks as db_list_tasks,
    get_agent # Assicurati che get_agent sia importato
)

logger = logging.getLogger(__name__)

class PMOrchestrationTools:
    # Definisci i nomi dei tool come attributi di CLASSE
    TOOL_NAME_CREATE_SUB_TASK = "create_and_assign_sub_task"
    TOOL_NAME_GET_TEAM_STATUS = "get_team_roles_and_status"

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        logger.info(f"PMOrchestrationTools initialized for workspace: {workspace_id}")
        # Non è più necessario impostare self._create_task_tool_name qui se usi gli attributi di classe

    def get_team_roles_and_status_tool(self):
        """Creates tool to get team roles and status, with embedded workspace_id."""
        workspace_id_str = self.workspace_id
        
        # Usa l'attributo di classe per name_override
        @function_tool(name_override=PMOrchestrationTools.TOOL_NAME_GET_TEAM_STATUS)
        async def impl() -> str:
            """
            Get detailed information about available team members, their EXACT names, roles, and current status.
            CRITICAL: Call this tool BEFORE using 'create_and_assign_sub_task' to ensure you use the precise 'agent_name' for assignments.
            This helps in assigning tasks to the correct and active agents.
            """
            try:
                logger.info(f"Tool '{PMOrchestrationTools.TOOL_NAME_GET_TEAM_STATUS}': Getting team roles for workspace: {workspace_id_str}")
                agents_in_db = await db_list_agents(workspace_id=workspace_id_str)
                
                active_agents_info = []
                inactive_agents_info = []

                for agent_data_dict in agents_in_db:
                    agent_info = {
                        "agent_name": agent_data_dict.get("name"),
                        "exact_role": agent_data_dict.get("role"),  
                        "seniority": agent_data_dict.get("seniority"),
                        "status": agent_data_dict.get("status"),
                        "description_summary": (agent_data_dict.get("description", "")[:100] + "..." 
                                               if agent_data_dict.get("description", "") else "No description")
                    }
                    if agent_data_dict.get("status") == "active":
                        active_agents_info.append(agent_info)
                    else:
                        inactive_agents_info.append(agent_info)
                
                team_info_response = {
                    "workspace_id": workspace_id_str,
                    "team_summary": {
                        "total_agents": len(agents_in_db),
                        "active_agents_count": len(active_agents_info),
                        "inactive_agents_count": len(inactive_agents_info)
                    },
                    "active_team_members": active_agents_info,
                    "usage_instructions": {
                        "for_task_assignment": "When using 'create_and_assign_sub_task', you MUST provide the 'agent_name' from the 'active_team_members' list for the 'target_agent_role' parameter. Do NOT use the 'exact_role' for assignment.",
                        "example_assignment": "If an active agent is listed as agent_name: 'ContentWriterBot', then for 'create_and_assign_sub_task', set target_agent_role='ContentWriterBot'."
                    }
                }
                if inactive_agents_info:
                    team_info_response["inactive_team_members_summary"] = [
                        {"agent_name": ag["agent_name"], "status": ag["status"]} for ag in inactive_agents_info
                    ]
                
                return json.dumps(team_info_response, indent=2)
                
            except Exception as e:
                logger.error(f"Error in {PMOrchestrationTools.TOOL_NAME_GET_TEAM_STATUS} tool for workspace {workspace_id_str}: {e}", exc_info=True)
                return json.dumps({"error": str(e), "workspace_id": workspace_id_str, "active_team_members": []})
        return impl

    def create_and_assign_sub_task_tool(self):
        """Creates sub-task tool with embedded workspace_id and duplicate check."""
        workspace_id_str = self.workspace_id 
        
        # Usa l'attributo di classe per name_override
        @function_tool(name_override=PMOrchestrationTools.TOOL_NAME_CREATE_SUB_TASK)
        async def impl(
            task_name: Annotated[str, Field(description="Clear, concise, and unique name for the new sub-task (max 100 chars).")],
            task_description: Annotated[str, Field(description="Detailed description (min 50 chars) of what needs to be done, including all necessary context, inputs, expected deliverables, and acceptance criteria.")],
            target_agent_role: Annotated[str, Field(description="The EXACT 'agent_name' of the ACTIVE agent to assign this task to (e.g., 'ContentSpecialist', 'AnalysisLead'). Obtain this from 'get_team_roles_and_status' tool.")],
            project_phase: Annotated[str, Field(description="The project phase this sub-task belongs to (e.g., ANALYSIS, IMPLEMENTATION, FINALIZATION). Must be one of the official project phases.")],
            priority: Annotated[Literal["low", "medium", "high"], Field(description="Priority of the sub-task: low, medium, or high.")] = "medium",
            parent_task_id: Annotated[Optional[str], Field(description="ID of the parent task (the PM's current task ID) from which this sub-task is derived. This is CRITICAL for tracking.")] = None
        ) -> str:
            logger.info(f"Tool '{PMOrchestrationTools.TOOL_NAME_CREATE_SUB_TASK}': Attempting to create sub-task '{task_name}' for agent NAME '{target_agent_role}' in workspace '{workspace_id_str}' for phase '{project_phase}'. Parent Task ID: {parent_task_id}")
            
            if not parent_task_id:
                logger.error(f"Tool '{PMOrchestrationTools.TOOL_NAME_CREATE_SUB_TASK}': 'parent_task_id' is missing. This is required for proper task hierarchy and tracking.")
                return json.dumps({
                    "success": False, 
                    "error": "Missing required parameter: 'parent_task_id'. Provide the ID of the current Project Manager task."
                })

            try:
                valid_phases = [p.value for p in ProjectPhase]
                normalized_project_phase = project_phase.upper().strip()
                if normalized_project_phase not in valid_phases:
                    return json.dumps({
                        "success": False, 
                        "error": f"Invalid project_phase '{project_phase}'. Must be one of {', '.join(valid_phases)}."
                    })

                all_current_tasks = await db_list_tasks(workspace_id=workspace_id_str)
                agents_in_db = await db_list_agents(workspace_id=workspace_id_str)
                target_agent = next(
                    (
                        agent
                        for agent in agents_in_db
                        if agent.get("name", "").lower() == target_agent_role.lower()
                        and agent.get("status") == "active"
                    ),
                    None,
                )
                task_name_lower = task_name.lower().strip()
                
                for existing_task_dict in all_current_tasks:
                    if existing_task_dict.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]:
                        existing_name_lower = existing_task_dict.get("name", "").lower().strip()
                        existing_phase = (existing_task_dict.get("context_data", {}).get("project_phase", "")).upper()
                        
                        is_same_target_agent = False
                        existing_agent_id_in_task = existing_task_dict.get("agent_id")
                        existing_assigned_role_in_task = existing_task_dict.get("assigned_to_role", "") 
                        
                        target_agent_object_for_new_task = target_agent

                        if target_agent_object_for_new_task:
                            if existing_agent_id_in_task == target_agent_object_for_new_task.get("id"):
                                is_same_target_agent = True
                            # Se il task esistente non ha agent_id ma ha un assigned_to_role che matcha il nome del target agent
                            elif not existing_agent_id_in_task and existing_assigned_role_in_task.lower() == target_agent_role.lower():
                                is_same_target_agent = True
                        # Se non troviamo un target_agent_object per nome (improbabile se il PM usa get_team_roles_and_status),
                        # e il task esistente ha un assigned_to_role che matcha, consideralo come stesso target
                        elif not target_agent_object_for_new_task and existing_assigned_role_in_task.lower() == target_agent_role.lower():
                             is_same_target_agent = True

                        if task_name_lower == existing_name_lower and \
                           existing_phase == normalized_project_phase and \
                           is_same_target_agent:
                            msg = f"Potential duplicate: A task named '{existing_task_dict.get('name')}' (ID: {existing_task_dict.get('id')}) is already '{existing_task_dict.get('status')}' targeting '{target_agent_role}' for phase '{normalized_project_phase}'. Not creating a new task."
                            logger.warning(msg)
                            return json.dumps({
                                "success": False, 
                                "task_id": existing_task_dict.get('id'), 
                                "message": msg,
                                "error": "Likely duplicate task detected (similar name, target agent/role, and phase)."
                            })
                
                if not target_agent:
                    available_agents_summary = [
                        {"name": a.get("name"), "role": a.get("role"), "status": a.get("status")}
                        for a in agents_in_db
                    ]
                    error_msg = f"Agent Assignment Error: No ACTIVE agent found with the EXACT name '{target_agent_role}'. Ensure the name matches an active agent from 'get_team_roles_and_status'."
                    logger.warning(f"{error_msg}. Workspace: {workspace_id_str}. Available agents for reference: {available_agents_summary}")
                    return json.dumps({
                        "success": False, "task_id": None, "error": error_msg,
                        "suggestion": "Call 'get_team_roles_and_status' again to verify the exact 'agent_name' of an ACTIVE agent.",
                        "available_agents_summary": available_agents_summary
                    })
                
                pm_agent_id = None
                if parent_task_id:
                    pm_task_obj_list = [t for t in all_current_tasks if t.get("id") == parent_task_id]
                    if pm_task_obj_list:
                        pm_agent_id = pm_task_obj_list[0].get("agent_id")
                        if not pm_agent_id: # Se il task genitore non ha un agent_id (improbabile per un task PM)
                            logger.warning(f"Parent task {parent_task_id} has no agent_id. Cannot reliably determine PM delegator ID.")
                    else:
                        logger.warning(f"Could not find parent PM task {parent_task_id} to retrieve PM agent ID.")
                
                # Recupera il nome del PM se l'ID è disponibile
                pm_name_delegator = "Unknown PM"
                if pm_agent_id:
                    pm_agent_obj = await get_agent(pm_agent_id) # Usa la funzione get_agent
                    if pm_agent_obj:
                        pm_name_delegator = pm_agent_obj.get("name", "Unknown PM")


                final_context_data = {
                    "project_phase": normalized_project_phase,
                    "delegated_by_pm_tool": True,
                    "tool_call_timestamp": datetime.now().isoformat(),
                    "source_pm_task_id": parent_task_id, 
                    "pm_name_who_delegated": pm_name_delegator,
                    "target_agent_name_at_creation": target_agent.get("name"),
                    "target_agent_role_at_creation": target_agent.get("role")
                }
                
                created_task_data = await db_create_task(
                    workspace_id=workspace_id_str,
                    agent_id=str(target_agent["id"]), 
                    assigned_to_role=target_agent.get("role"), 
                    name=task_name,
                    description=task_description,
                    status=TaskStatus.PENDING.value,
                    priority=priority,
                    parent_task_id=parent_task_id, 
                    context_data=final_context_data,
                    created_by_task_id=parent_task_id, 
                    created_by_agent_id=pm_agent_id, 
                    creation_type="pm_tool_delegation" 
                )
                
                if created_task_data and created_task_data.get("id"):
                    task_created_id = created_task_data['id']
                    msg = f"Sub-task '{task_name}' (ID: {task_created_id}) created successfully and assigned to agent '{target_agent['name']}' (Role: '{target_agent.get('role', 'N/A')}') for project phase '{normalized_project_phase}'."
                    logger.info(msg)
                    response_payload = {
                        "success": True, "task_id": task_created_id,
                        "assigned_agent_name": target_agent["name"],
                        "task_name_created": task_name, 
                        "message": msg
                    }
                    return json.dumps(response_payload)
                else:
                    error_msg = f"Database error: Failed to create sub-task '{task_name}' for phase '{normalized_project_phase}'."
                    logger.error(f"{error_msg} DB response: {created_task_data}")
                    return json.dumps({"success": False, "task_id": None, "error": error_msg})
                    
            except Exception as e:
                logger.error(f"Critical error in {PMOrchestrationTools.TOOL_NAME_CREATE_SUB_TASK} tool: {e}", exc_info=True)
                return json.dumps({"success": False, "task_id": None, "error": f"An unexpected error occurred: {str(e)}"})
        
        return impl

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