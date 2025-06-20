"""
Simplified Conversational Agent - AI-driven responses without complex SDK dependencies
Maintains AI-enhanced principles while providing reliable functionality
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from openai import OpenAI
from pydantic import BaseModel

from database import get_supabase_client
from utils.context_manager import get_workspace_context
from tools.openai_sdk_tools import openai_tools_manager
from tools.workspace_service import get_workspace_service

logger = logging.getLogger(__name__)

class ConversationResponse(BaseModel):
    """Structured response from conversational agent"""
    message: str
    message_type: str = "text"
    artifacts: Optional[List[Dict[str, Any]]] = None
    actions_performed: Optional[List[Dict[str, Any]]] = None
    needs_confirmation: bool = False
    confirmation_id: Optional[str] = None

class SimpleConversationalAgent:
    """
    Simplified AI-driven conversational agent.
    Uses OpenAI directly for intelligent responses while maintaining our core principles.
    """
    
    def __init__(self, workspace_id: str, chat_id: str = "general"):
        self.workspace_id = workspace_id
        self.chat_id = chat_id
        self.openai_client = OpenAI()
        self.context = None
        self.tools_available = self._initialize_tools()
        
    async def process_message(self, user_message: str, message_id: str = None) -> ConversationResponse:
        """
        Process user message with AI-driven analysis and response generation.
        Maintains context awareness and generates intelligent responses.
        """
        try:
            # Load workspace context
            await self._load_context()
            
            # Generate AI-driven response
            ai_response = await self._generate_intelligent_response(user_message)
            
            # Store conversation in database
            await self._store_conversation(user_message, ai_response, message_id)
            
            return ConversationResponse(
                message=ai_response,
                message_type="ai_response",
                artifacts=None,
                actions_performed=None,
                needs_confirmation=False
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ConversationResponse(
                message=f"I encountered an error processing your request: {str(e)}. Please try again.",
                message_type="error"
            )
    
    async def _load_context(self):
        """Load comprehensive workspace context for AI processing"""
        try:
            self.context = await get_workspace_context(self.workspace_id)
            logger.info(f"✅ Context loaded for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            self.context = {"workspace_id": self.workspace_id, "error": "context_unavailable"}
    
    async def _generate_intelligent_response(self, user_message: str) -> str:
        """
        Generate AI-driven response based on context and user message.
        Uses OpenAI to provide intelligent, context-aware responses.
        """
        try:
            # Prepare context for AI
            context_summary = self._prepare_context_for_ai()
            
            # Create intelligent prompt with tool awareness
            tools_description = self._get_tools_description()
            
            system_prompt = f"""You are a direct, execution-focused AI project manager with the ability to perform actions.

WORKSPACE CONTEXT:
{context_summary}

CHAT CONTEXT: {self.chat_id}

AVAILABLE TOOLS:
{tools_description}

When the user asks you to DO something (add team member, start/pause team, etc.), you should:
1. Identify which tool to use
2. Extract the necessary parameters
3. Respond with: "EXECUTE_TOOL: tool_name {{parameters}}"

For questions or status requests, provide direct answers without tool execution.

RESPONSE STYLE:
- Be direct and concise (max 3-4 sentences)
- Execute actions when requested instead of explaining how
- Focus on results, not instructions"""

            user_prompt = f"""User request: "{user_message}"

Provide a direct, actionable response. Focus on:
- Immediate next steps (be specific)
- Concrete actions the user can take now
- Reference actual workspace data/context
- Keep it brief and execution-focused

Respond with specific actions, not general advice."""

            # Call OpenAI for intelligent response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"✅ AI response generated successfully")
            
            # Check if the AI wants to execute a tool
            if ai_response.startswith("EXECUTE_TOOL:"):
                tool_response = await self._parse_and_execute_tool(ai_response)
                return tool_response
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return f"I'm having trouble generating a response right now. Here's what I can tell you about your workspace based on the available information: {self._get_basic_workspace_info()}"
    
    def _prepare_context_for_ai(self) -> str:
        """Prepare workspace context in a format suitable for AI processing"""
        if not self.context:
            return "Context unavailable"
        
        try:
            workspace_info = self.context.get('workspace', {})
            agents_info = self.context.get('agents', [])
            goals_info = self.context.get('goals', [])
            tasks_info = self.context.get('tasks', [])
            
            # Get specific team details
            team_details = []
            for agent in agents_info[:4]:  # Limit to first 4 agents
                role = agent.get('role', 'Unknown')
                seniority = agent.get('seniority', 'Unknown')
                skills = agent.get('skills', [])
                team_details.append(f"- {role} ({seniority}): {', '.join(skills[:3])}")
            
            # Get active goals
            active_goals = [goal.get('title', 'Untitled') for goal in goals_info if goal.get('status') == 'active']
            
            # Get task status
            pending_tasks = len([t for t in tasks_info if t.get('status') == 'pending'])
            completed_tasks = len([t for t in tasks_info if t.get('status') == 'completed'])
            
            summary = f"""
PROJECT: {workspace_info.get('name', 'Unknown')}
GOAL: {workspace_info.get('goal', 'Not specified')}
STATUS: {workspace_info.get('status', 'Unknown')}

TEAM ({len(agents_info)} members):
{chr(10).join(team_details) if team_details else '- No team details available'}

ACTIVE OBJECTIVES: {', '.join(active_goals) if active_goals else 'None set'}
TASKS: {completed_tasks} completed, {pending_tasks} pending
"""
            return summary.strip()
            
        except Exception as e:
            return f"Context processing error: {e}"
    
    def _get_basic_workspace_info(self) -> str:
        """Get basic workspace information as fallback"""
        if self.context and 'workspace' in self.context:
            workspace = self.context['workspace']
            return f"Workspace '{workspace.get('name', 'Unknown')}' with {len(self.context.get('agents', []))} team members."
        return "Workspace information is being loaded."
    
    async def _store_conversation(self, user_message: str, ai_response: str, message_id: str = None):
        """Store conversation in database for history"""
        try:
            supabase = get_supabase_client()
            
            # Store user message
            await self._store_message(supabase, user_message, "user", message_id)
            
            # Store AI response  
            await self._store_message(supabase, ai_response, "assistant", f"{message_id}_response")
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    async def _store_message(self, supabase, content: str, role: str, message_id: str = None):
        """Store individual message in database using simple approach"""
        try:
            conversation_id = f"{self.workspace_id}_{self.chat_id}"
            
            # Simple direct insert - conversations will be created automatically if needed
            result = supabase.table("conversation_messages").insert({
                "conversation_identifier": conversation_id,
                "message_id": message_id or f"msg_{int(datetime.now().timestamp())}",
                "role": role,
                "content": content,
                "content_type": "text",
                "tools_used": [],
                "actions_performed": [],
                "context_snapshot": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            logger.info(f"✅ Message stored successfully in conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize available tools for the conversational agent"""
        tools = {
            "add_team_member": {
                "description": "Add a new team member to the workspace",
                "parameters": {
                    "role": "string - The role of the new member (e.g., 'developer', 'designer')",
                    "seniority": "string - Seniority level (junior, senior, expert)",
                    "skills": "list - List of skills for the member"
                }
            },
            "start_team": {
                "description": "Start the team and begin task execution",
                "parameters": {}
            },
            "pause_team": {
                "description": "Pause all team activities",
                "parameters": {}
            },
            "update_team_skills": {
                "description": "Update skills for existing team members",
                "parameters": {
                    "agent_id": "string - ID of the agent to update",
                    "skills": "list - New skills to add"
                }
            },
            "show_team_status": {
                "description": "Show current team status and activities",
                "parameters": {}
            },
            "show_goal_progress": {
                "description": "Show progress on workspace goals and objectives",
                "parameters": {
                    "goal_id": "string - Optional specific goal ID to view (shows all if not provided)"
                }
            },
            "show_deliverables": {
                "description": "Show completed deliverables and assets",
                "parameters": {
                    "type": "string - Optional filter: 'assets', 'deliverables', or 'all' (default: all)"
                }
            },
            "create_goal": {
                "description": "Create a new goal/objective for the workspace",
                "parameters": {
                    "title": "string - Title of the goal",
                    "description": "string - Detailed description of what needs to be achieved"
                }
            },
            # OpenAI SDK Tools
            "web_search": {
                "description": "Search the web for current information",
                "parameters": {
                    "query": "string - The search query"
                }
            },
            "code_interpreter": {
                "description": "Execute Python code for calculations and data processing",
                "parameters": {
                    "code": "string - Python code to execute"
                }
            },
            "generate_image": {
                "description": "Create images from text descriptions",
                "parameters": {
                    "prompt": "string - Description of the image to generate"
                }
            },
            "file_search": {
                "description": "Search through workspace documents and files",
                "parameters": {
                    "query": "string - What to search for in files"
                }
            },
            # Document Management Tools
            "upload_document": {
                "description": "Upload a document to the workspace for team access",
                "parameters": {
                    "file_data": "string - Base64 encoded file content",
                    "filename": "string - Name of the file",
                    "sharing_scope": "string - 'team' for all agents or 'agent-{id}' for specific agent",
                    "description": "string - Optional description of the document",
                    "tags": "list - Optional list of tags for categorization"
                }
            },
            "list_documents": {
                "description": "List all documents uploaded to the workspace",
                "parameters": {
                    "scope": "string - Optional filter by scope: 'team' or specific agent ID"
                }
            },
            "delete_document": {
                "description": "Delete a document from the workspace",
                "parameters": {
                    "document_id": "string - ID of the document to delete"
                }
            },
            "search_documents": {
                "description": "Search through uploaded documents using AI-powered search",
                "parameters": {
                    "query": "string - Search query for document content",
                    "max_results": "int - Maximum number of results (default: 5)"
                }
            }
        }
        return tools
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool action and return results - SCALABLE & AGNOSTIC"""
        try:
            # AGNOSTIC: Use service layer instead of direct database access
            supabase = get_supabase_client()
            workspace_service = get_workspace_service(supabase)
            
            if tool_name == "add_team_member":
                # SCALABLE: Use service layer
                return await workspace_service.add_team_member(
                    workspace_id=self.workspace_id,
                    role=parameters['role'],
                    seniority=parameters.get('seniority', 'senior'),
                    skills=parameters.get('skills', [])
                )
                
            elif tool_name == "start_team":
                # SCALABLE: Use service layer
                return await workspace_service.update_workspace_status(
                    workspace_id=self.workspace_id,
                    status="active"
                )
                
            elif tool_name == "pause_team":
                # SCALABLE: Use service layer
                return await workspace_service.update_workspace_status(
                    workspace_id=self.workspace_id,
                    status="paused"
                )
                
            elif tool_name == "show_team_status":
                # SCALABLE: Use service layer
                return await workspace_service.get_team_status(self.workspace_id)
                
            elif tool_name == "show_goal_progress":
                # SCALABLE: Use service layer
                return await workspace_service.get_goal_progress(
                    workspace_id=self.workspace_id,
                    goal_id=parameters.get("goal_id")
                )
                
            elif tool_name == "show_deliverables":
                # SCALABLE: Use service layer
                return await workspace_service.get_deliverables(
                    workspace_id=self.workspace_id,
                    filter_type=parameters.get("type", "all")
                )
                
            elif tool_name == "create_goal":
                # SCALABLE: Use service layer
                return await workspace_service.create_goal(
                    workspace_id=self.workspace_id,
                    title=parameters["title"],
                    description=parameters.get("description", "")
                )
                
            elif tool_name in ["web_search", "code_interpreter", "generate_image", "file_search"]:
                # Use OpenAI SDK tools with context
                context = {"workspace_id": self.workspace_id}
                result = await openai_tools_manager.execute_tool(tool_name, parameters, context)
                if result["success"]:
                    return {
                        "success": True,
                        "message": result["result"]
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Error: {result.get('error', 'Unknown error')}"
                    }
                    
            elif tool_name in ["upload_document", "list_documents", "delete_document", "search_documents"]:
                # Use Document Management tools with context
                from tools.document_tools import document_tools
                context = {"workspace_id": self.workspace_id}
                
                tool_instance = document_tools[tool_name]
                result = await tool_instance.execute(context=context, **parameters)
                
                return {
                    "success": True,
                    "message": result
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Tool '{tool_name}' not implemented yet"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "message": f"Error executing {tool_name}: {str(e)}"
            }
    
    def _get_tools_description(self) -> str:
        """Get formatted description of available tools"""
        descriptions = []
        for tool_name, tool_info in self.tools_available.items():
            params = tool_info["parameters"]
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items()]) if params else "no parameters"
            descriptions.append(f"- {tool_name}: {tool_info['description']} ({param_str})")
        return "\n".join(descriptions)
    
    async def _parse_and_execute_tool(self, ai_response: str) -> str:
        """Parse tool execution request and execute the tool"""
        try:
            # Extract tool name and parameters
            import re
            match = re.match(r"EXECUTE_TOOL:\s*(\w+)\s*(\{.*\})?", ai_response)
            if not match:
                return "Error parsing tool execution request."
            
            tool_name = match.group(1)
            params_str = match.group(2) or "{}"
            
            # Parse parameters
            try:
                parameters = json.loads(params_str)
            except:
                parameters = {}
            
            # Execute the tool
            result = await self._execute_tool(tool_name, parameters)
            
            if result["success"]:
                return f"✅ {result['message']}"
            else:
                return f"❌ {result['message']}"
                
        except Exception as e:
            logger.error(f"Error parsing/executing tool: {e}")
            return f"Error executing action: {str(e)}"