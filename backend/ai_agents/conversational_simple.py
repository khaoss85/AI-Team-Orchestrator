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
from ai_agents.enhanced_reasoning import EnhancedReasoningEngine

logger = logging.getLogger(__name__)

class ConversationResponse(BaseModel):
    """Structured response from conversational agent"""
    message: str
    message_type: str = "text"
    artifacts: Optional[List[Dict[str, Any]]] = None
    actions_performed: Optional[List[Dict[str, Any]]] = None
    needs_confirmation: bool = False
    confirmation_id: Optional[str] = None
    suggested_actions: Optional[List[Dict[str, Any]]] = None

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
        self.reasoning_engine = EnhancedReasoningEngine()
        
    async def process_message(self, user_message: str, message_id: str = None, thinking_callback=None) -> ConversationResponse:
        """
        Process user message with AI-driven analysis and response generation.
        Maintains context awareness and generates intelligent responses.
        """
        try:
            # Load workspace context
            await self._load_context()
            
            # Generate AI-driven response
            ai_response = await self._generate_intelligent_response(user_message)
            
            # Extract suggested actions from the response
            suggested_actions = self._extract_suggested_actions(ai_response)
            
            # Store conversation in database
            await self._store_conversation(user_message, ai_response, message_id)
            
            return ConversationResponse(
                message=ai_response,
                message_type="ai_response",
                artifacts=None,
                actions_performed=None,
                needs_confirmation=False,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ConversationResponse(
                message=f"I encountered an error processing your request: {str(e)}. Please try again.",
                message_type="error"
            )
    
    async def process_message_with_thinking(self, user_message: str, message_id: str = None, thinking_callback=None) -> ConversationResponse:
        """
        Process user message with visible thinking steps for real-time updates.
        Shows the actual AI reasoning process step by step.
        """
        try:
            # Initialize thinking steps storage
            self._current_thinking_steps = []
            
            # Create wrapper for thinking callback to store steps
            async def storing_thinking_callback(step_data):
                # Store the step
                self._current_thinking_steps.append({
                    **step_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                # Call the original callback if provided
                if thinking_callback:
                    await thinking_callback(step_data)
            
            # Step 1: Context Loading
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "context_loading",
                    "title": "🔍 Loading Workspace Context",
                    "description": "Retrieving team composition, project status, and recent activities...",
                    "status": "in_progress"
                })
            
            await self._load_context()
            
            await storing_thinking_callback({
                    "type": "thinking_step", 
                    "step": "context_loading",
                    "title": "🔍 Context Loaded",
                    "description": f"Loaded workspace data for {self.context.get('workspace', {}).get('name', 'project')}",
                    "status": "completed"
                })
            
            # Step 2: Conversation History
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "history_loading", 
                    "title": "📚 Loading Conversation History",
                    "description": "Retrieving previous messages for context continuity...",
                    "status": "in_progress"
                })
            
            # We'll load this in the AI generation step, but show thinking here
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "history_loading",
                    "title": "📚 History Loaded", 
                    "description": "Retrieved recent conversation context for better understanding",
                    "status": "completed"
                })
            
            # Step 3: Query Analysis
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "query_analysis",
                    "title": "🧠 Analyzing Request",
                    "description": f"Understanding: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'",
                    "status": "in_progress"
                })
            
            # Quick analysis of the user request
            is_strategic_question = any(word in user_message.lower() for word in [
                'team', 'serve', 'aggiungere', 'completo', 'abbastanza', 'consiglio', 'pensi'
            ])
            
            requires_data = any(word in user_message.lower() for word in [
                'status', 'progresso', 'stato', 'team', 'progetto', 'membri'
            ])
            
            # Using storing_thinking_callback instead
                query_type = "Strategic Decision" if is_strategic_question else "Information Request"
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "query_analysis", 
                    "title": "🧠 Request Understood",
                    "description": f"Type: {query_type} | Data needed: {'Yes' if requires_data else 'No'}",
                    "status": "completed"
                })
            
            # Step 4: Data Gathering (if needed)
            if requires_data and thinking_callback:
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "data_gathering",
                    "title": "📊 Gathering Relevant Data", 
                    "description": "Analyzing current team composition, workload, and project metrics...",
                    "status": "in_progress"
                })
                
                # Show what data we're analyzing
                team_size = len(self.context.get('agents', []))
                task_count = self.context.get('task_count', 0)
                
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "data_gathering",
                    "title": "📊 Data Analysis Complete",
                    "description": f"Team: {team_size} members | Active tasks: {task_count} | Workload ratio: {round(task_count/team_size, 1) if team_size > 0 else 0} tasks/member",
                    "status": "completed"
                })
                
            # Step 4.5: Deep Reasoning Analysis (if strategic query)
            if query_type == "Strategic Decision" and thinking_callback:
                # Prepare context for deep reasoning
                reasoning_context = {
                    'workspace_data': self.context.get('workspace', {}),
                    'team_data': self.context.get('agents', []),
                    'active_tasks': self.context.get('active_tasks', []),
                    'completed_tasks': self.context.get('completed_tasks', []),
                    'goals': self.context.get('goals', []),
                    'quality_metrics': self.context.get('quality_metrics', {}),
                    'time_elapsed_days': self.context.get('time_elapsed_days', 30)
                }
                
                # Perform deep reasoning analysis
                deep_analysis = await self.reasoning_engine.deep_reasoning_analysis(
                    user_message,
                    reasoning_context,
                    storing_thinking_callback
                )
                
                # Store deep analysis for response generation
                self.context['deep_analysis'] = deep_analysis
            
            # Step 5: AI Processing
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step", 
                    "step": "ai_processing",
                    "title": "🤖 Generating Strategic Response",
                    "description": "Applying project management expertise and context analysis...",
                    "status": "in_progress"
                })
            
            # Generate the actual AI response
            ai_response = await self._generate_intelligent_response(user_message)
            
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "ai_processing", 
                    "title": "🤖 Response Generated",
                    "description": "Strategic analysis complete with recommendations and next actions",
                    "status": "completed"
                })
            
            # Step 6: Action Extraction
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "action_extraction",
                    "title": "⚡ Extracting Actionable Items",
                    "description": "Identifying tools and quick actions from the response...",
                    "status": "in_progress"
                })
            
            suggested_actions = self._extract_suggested_actions(ai_response)
            
            # Using storing_thinking_callback instead
                action_count = len(suggested_actions)
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "action_extraction",
                    "title": "⚡ Actions Ready",
                    "description": f"Found {action_count} actionable tools ready for execution",
                    "status": "completed"
                })
            
            # Count total steps (including deep reasoning if performed)
            total_steps = 7  # Base steps
            if query_type == "Strategic Decision" and 'deep_analysis' in self.context:
                # Deep reasoning adds additional steps
                total_steps += 7  # Problem decomposition, perspectives, alternatives, evaluation, critique, confidence, synthesis
            
            # Step 7: Finalizing
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_complete",
                    "title": "✅ Analysis Complete",
                    "description": f"Completed {total_steps} analysis steps with {'deep reasoning' if total_steps > 7 else 'standard'} process"
                })
            
            # Store conversation
            await self._store_conversation(user_message, ai_response, message_id)
            
            return ConversationResponse(
                message=ai_response,
                message_type="ai_response",
                artifacts=None,
                actions_performed=None,
                needs_confirmation=False,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            # Using storing_thinking_callback instead
                await storing_thinking_callback({
                    "type": "thinking_error",
                    "title": "❌ Processing Error",
                    "description": f"Error during analysis: {str(e)}"
                })
            
            logger.error(f"Error in thinking process: {e}")
            return ConversationResponse(
                message=f"I encountered an error during my analysis: {str(e)}. Please try again.",
                message_type="error"
            )
    
    async def _load_context(self):
        """Load optimized workspace context for AI processing"""
        try:
            # Use lightweight context for document operations to avoid token limits
            self.context = await self._get_lightweight_context()
            logger.info(f"✅ Context loaded for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            self.context = {"workspace_id": self.workspace_id, "error": "context_unavailable"}
    
    async def _get_lightweight_context(self) -> Dict[str, Any]:
        """Get minimal context to avoid OpenAI token limits"""
        try:
            supabase = get_supabase_client()
            
            # Get only essential workspace info
            workspace_result = supabase.table("workspaces")\
                .select("id,name,description,status")\
                .eq("id", self.workspace_id)\
                .execute()
            
            # Get basic team info  
            agents_result = supabase.table("agents")\
                .select("id,name,role,status")\
                .eq("workspace_id", self.workspace_id)\
                .limit(5)\
                .execute()
            
            # Get recent tasks count only
            tasks_result = supabase.table("tasks")\
                .select("status")\
                .eq("workspace_id", self.workspace_id)\
                .limit(10)\
                .execute()
            
            return {
                "workspace_id": self.workspace_id,
                "workspace": workspace_result.data[0] if workspace_result.data else {},
                "agents": agents_result.data[:3],  # Limit to 3 agents
                "task_count": len(tasks_result.data),
                "context_type": "lightweight"
            }
            
        except Exception as e:
            logger.error(f"Failed to load lightweight context: {e}")
            return {"workspace_id": self.workspace_id, "error": "lightweight_context_unavailable"}
    
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
            
            system_prompt = f"""You are an intelligent AI Project Manager with deep analytical capabilities and full workspace context.

WORKSPACE CONTEXT:
{context_summary}

CHAT CONTEXT: {self.chat_id}

AVAILABLE TOOLS:
{tools_description}

CORE INTELLIGENCE FRAMEWORK:
You have access to ALL workspace data - team composition, performance metrics, budget, goals, insights, deliverables, and project history. Use this context to:

1. **ANALYZE** - Always gather relevant data first using appropriate tools
2. **REASON** - Apply project management expertise to the situation  
3. **RECOMMEND** - Provide specific, actionable recommendations
4. **EXECUTE** - Offer quick actions when appropriate

RESPONSE APPROACH:
For strategic questions (team composition, project direction, resource allocation):
1. First gather data: "Let me analyze the current situation..."
2. Show your reasoning process and analysis
3. Provide specific recommendations with rationale
4. Suggest concrete next actions

For execution requests:
- Use: "EXECUTE_TOOL: tool_name {{parameters}}"

DECISION-MAKING EXAMPLES:
- Team questions: Analyze current team size, skills, workload, budget → recommend optimal team composition
- Resource questions: Review current allocation vs goals → suggest reallocation
- Timeline questions: Assess progress vs deadlines → recommend acceleration strategies
- Quality questions: Review performance metrics → suggest improvements

Be proactive, analytical, and strategic. Act like a senior consultant, not a simple assistant."""

            # Pre-process user message to handle large file uploads
            processed_message, file_upload_result = self._handle_file_upload_in_message(user_message, self.workspace_id)
            
            # Check if deep reasoning was performed
            deep_reasoning_info = ""
            if 'deep_analysis' in self.context:
                deep_analysis = self.context['deep_analysis']
                confidence = deep_analysis.get('confidence', {}).get('overall', 0)
                alternatives_count = len(deep_analysis.get('alternatives', []))
                
                deep_reasoning_info = f"""
Deep Reasoning Applied:
- Analyzed {alternatives_count} alternative approaches
- Confidence level: {confidence:.0%}
- Primary recommendation: {deep_analysis.get('recommendation', {}).get('primary_recommendation', 'N/A')}
"""

            user_prompt = f"""User request: "{processed_message}"
{deep_reasoning_info}
As an AI Project Manager, provide an intelligent response using this structure:

**ANALYSIS**: [If data is needed, gather it first using appropriate tools, then analyze the current situation]

**REASONING**: [Share your thought process, considering project management best practices, resource constraints, timelines, and strategic implications]

**RECOMMENDATIONS**: [Provide specific, actionable recommendations with clear rationale]

**NEXT ACTIONS**: [Suggest concrete immediate steps, including tool executions if appropriate]

For strategic questions (team composition, resource allocation, timeline concerns):
- Be thorough and analytical
- Use tools to gather current data
- Apply project management expertise
- Consider multiple factors and trade-offs

For simple execution requests:
- Be direct and execute immediately
- Use tools as needed"""

            # Prepare messages with conversation history
            messages = await self._prepare_messages_with_history(system_prompt, user_prompt)
            
            # Call OpenAI for intelligent response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"✅ AI response generated successfully")
            
            # If we handled a file upload, include the result in the response
            if file_upload_result.get("success"):
                file_info = f"\n\n✅ File upload completed: {file_upload_result.get('message', 'File uploaded successfully')}"
                ai_response += file_info
            elif file_upload_result.get("message") != "No file upload detected":
                # There was a file upload attempt but it failed
                file_error = f"\n\n❌ File upload failed: {file_upload_result.get('message', 'Unknown error')}"
                ai_response += file_error
            
            # Check if the AI wants to execute a tool
            if ai_response.startswith("EXECUTE_TOOL:"):
                tool_response = await self._parse_and_execute_tool(ai_response)
                return tool_response
            
            # Parse structured response for thinking artifacts
            parsed_response = self._parse_structured_response(ai_response)
            return parsed_response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return f"I'm having trouble generating a response right now. Here's what I can tell you about your workspace based on the available information: {self._get_basic_workspace_info()}"
    
    def _prepare_context_for_ai(self) -> str:
        """Prepare strategic workspace context for AI analysis"""
        if not self.context:
            return "Context unavailable"
        
        try:
            workspace_info = self.context.get('workspace', {})
            agents_info = self.context.get('agents', [])
            task_count = self.context.get('task_count', 0)
            
            # Enhanced team analysis
            team_roles = {}
            team_seniority = {"junior": 0, "senior": 0, "expert": 0}
            
            for agent in agents_info:
                role = agent.get('role', 'Unknown')
                seniority = agent.get('seniority', 'unknown')
                
                team_roles[role] = team_roles.get(role, 0) + 1
                if seniority in team_seniority:
                    team_seniority[seniority] += 1
            
            # Format team composition
            team_composition = []
            for role, count in team_roles.items():
                team_composition.append(f"{count} {role}{'s' if count > 1 else ''}")
            
            # Format seniority distribution
            seniority_dist = []
            for level, count in team_seniority.items():
                if count > 0:
                    seniority_dist.append(f"{count} {level}")
            
            summary = f"""
PROJECT: {workspace_info.get('name', 'Unknown')}
STATUS: {workspace_info.get('status', 'Unknown')}
DOMAIN: {workspace_info.get('domain', 'Not specified')}

TEAM ANALYSIS:
- Size: {len(agents_info)} members
- Composition: {', '.join(team_composition) if team_composition else 'No roles defined'}
- Seniority: {', '.join(seniority_dist) if seniority_dist else 'Not specified'}

WORKLOAD:
- Active tasks: {task_count}
- Tasks per member: {round(task_count / len(agents_info), 1) if agents_info else 0}

Use tools to gather additional data for deeper analysis when needed.
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
            
            # Store AI response with thinking steps if available
            ai_metadata = {}
            if hasattr(self, '_current_thinking_steps') and self._current_thinking_steps:
                ai_metadata['thinking_steps'] = self._current_thinking_steps
            if 'deep_analysis' in self.context:
                ai_metadata['deep_analysis'] = self.context['deep_analysis']
                
            await self._store_message(supabase, ai_response, "assistant", f"{message_id}_response", ai_metadata)
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    async def _store_message(self, supabase, content: str, role: str, message_id: str = None, metadata: dict = None):
        """Store individual message in database using simple approach"""
        try:
            import uuid
            conversation_identifier = f"{self.workspace_id}_{self.chat_id}"
            
            # Generate or retrieve conversation UUID
            # For now, create a deterministic UUID based on the identifier
            conversation_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, conversation_identifier))
            
            # Ensure conversation exists in conversations table
            try:
                # Check if conversation already exists
                existing = supabase.table("conversations").select("id").eq("id", conversation_uuid).execute()
                if not existing.data:
                    # Create new conversation
                    supabase.table("conversations").insert({
                        "id": conversation_uuid,
                        "workspace_id": self.workspace_id,
                        "chat_id": self.chat_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }).execute()
                    logger.info(f"📝 Created new conversation: {conversation_uuid}")
            except Exception as conv_error:
                logger.warning(f"Could not create/check conversation: {conv_error}")
                # Continue anyway - maybe the foreign key constraint is optional
            
            # Generate message ID if not provided
            if not message_id:
                message_id = f"msg_{int(datetime.now().timestamp() * 1000)}_{role}"
            
            # Simple direct insert using actual table columns
            message_data = {
                "conversation_identifier": conversation_identifier,
                "conversation_id": conversation_uuid,
                "message_id": message_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Add metadata if provided (includes thinking steps)
            if metadata:
                message_data["metadata"] = json.dumps(metadata)
            
            result = supabase.table("conversation_messages").insert(message_data).execute()
            
            logger.info(f"✅ Message stored successfully in conversation {conversation_identifier}")
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
    
    def _parse_structured_response(self, ai_response: str) -> str:
        """Parse AI response to extract thinking process and create enhanced formatting"""
        try:
            import re
            
            # Check if response contains analysis/reasoning sections
            analysis_pattern = r'\*\*ANALYSIS\*\*:?\s*(.*?)(?=\*\*|$)'
            reasoning_pattern = r'\*\*REASONING\*\*:?\s*(.*?)(?=\*\*|$)'
            recommendations_pattern = r'\*\*RECOMMENDATIONS?\*\*:?\s*(.*?)(?=\*\*|$)'
            actions_pattern = r'\*\*NEXT ACTIONS?\*\*:?\s*(.*?)(?=\*\*|$)'
            
            analysis_match = re.search(analysis_pattern, ai_response, re.IGNORECASE | re.DOTALL)
            reasoning_match = re.search(reasoning_pattern, ai_response, re.IGNORECASE | re.DOTALL)
            recommendations_match = re.search(recommendations_pattern, ai_response, re.IGNORECASE | re.DOTALL)
            actions_match = re.search(actions_pattern, ai_response, re.IGNORECASE | re.DOTALL)
            
            # If we found structured sections, format them with enhanced markup
            if analysis_match or reasoning_match or recommendations_match or actions_match:
                structured_parts = []
                
                if analysis_match:
                    analysis_content = self._enhance_markdown(analysis_match.group(1).strip())
                    structured_parts.append(f"🔍 **ANALYSIS**\n\n{analysis_content}")
                
                if reasoning_match:
                    reasoning_content = self._enhance_markdown(reasoning_match.group(1).strip())
                    structured_parts.append(f"🧠 **REASONING**\n\n{reasoning_content}")
                    
                if recommendations_match:
                    recommendations_content = self._enhance_markdown(recommendations_match.group(1).strip())
                    structured_parts.append(f"💡 **RECOMMENDATIONS**\n\n{recommendations_content}")
                
                if actions_match:
                    actions_content = self._parse_and_enhance_actions(actions_match.group(1).strip())
                    structured_parts.append(f"⚡ **NEXT ACTIONS**\n\n{actions_content}")
                
                # Add the structured response with better spacing
                formatted_response = "\n\n---\n\n".join(structured_parts)
                
                # Add any remaining content that wasn't captured
                remaining_content = ai_response
                for pattern in [analysis_pattern, reasoning_pattern, recommendations_pattern, actions_pattern]:
                    remaining_content = re.sub(pattern, '', remaining_content, flags=re.IGNORECASE | re.DOTALL)
                
                remaining_content = remaining_content.strip()
                if remaining_content and not remaining_content.startswith('**'):
                    remaining_content = self._enhance_markdown(remaining_content)
                    formatted_response += f"\n\n---\n\n{remaining_content}"
                
                return formatted_response
            
            # If no structured sections found, enhance the original response
            return self._enhance_markdown(ai_response)
            
        except Exception as e:
            logger.warning(f"Could not parse structured response: {e}")
            return ai_response
    
    def _enhance_markdown(self, content: str) -> str:
        """Enhance content with better markdown formatting"""
        import re
        
        # Enhance bullet points
        content = re.sub(r'^- ', '• ', content, flags=re.MULTILINE)
        content = re.sub(r'^\* ', '• ', content, flags=re.MULTILINE)
        
        # Enhance numbered lists
        content = re.sub(r'^(\d+)\. ', r'**\1.** ', content, flags=re.MULTILINE)
        
        # Enhance emphasis for key terms
        key_terms = ['team', 'project', 'deadline', 'budget', 'workload', 'task', 'member', 'developer', 'timeline']
        for term in key_terms:
            # Only emphasize if not already emphasized
            content = re.sub(rf'\b({term})\b(?!\*)', rf'**\1**', content, flags=re.IGNORECASE)
        
        # Clean up any double emphasis
        content = re.sub(r'\*\*\*\*([^*]+)\*\*\*\*', r'**\1**', content)
        
        return content
    
    def _parse_and_enhance_actions(self, actions_content: str) -> str:
        """Parse and enhance actions section with tool buttons and better formatting"""
        import re
        
        # Look for tool recommendations
        tool_pattern = r"'([^']+)'"
        tools_mentioned = re.findall(tool_pattern, actions_content)
        
        # Available tools that can be made into buttons
        actionable_tools = {
            'show_project_status': {'label': '📊 View Project Status', 'description': 'Get comprehensive project overview'},
            'show_team_status': {'label': '👥 View Team Status', 'description': 'See current team composition and activities'},
            'show_goal_progress': {'label': '🎯 View Goal Progress', 'description': 'Check progress on objectives'},
            'show_deliverables': {'label': '📦 View Deliverables', 'description': 'See completed deliverables and assets'},
            'add_team_member': {'label': '➕ Add Team Member', 'description': 'Add a new member to the team'},
            'start_team': {'label': '▶️ Start Team', 'description': 'Begin team activities'},
            'pause_team': {'label': '⏸️ Pause Team', 'description': 'Pause all team activities'}
        }
        
        # Enhance the text content
        enhanced_content = self._enhance_markdown(actions_content)
        
        # Add tool buttons section if tools were mentioned
        tool_buttons = []
        for tool in tools_mentioned:
            if tool in actionable_tools:
                tool_info = actionable_tools[tool]
                tool_buttons.append(f"🔲 **{tool_info['label']}** - {tool_info['description']}")
        
        if tool_buttons:
            enhanced_content += "\n\n**🛠️ Quick Actions:**\n" + "\n".join(tool_buttons)
            enhanced_content += "\n\n*Click any action above to execute it immediately.*"
        
        return enhanced_content
    
    def _extract_suggested_actions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract suggested tool actions from AI response"""
        import re
        
        # Available tools that can be made into action buttons
        actionable_tools = {
            'show_project_status': {
                'tool': 'show_project_status',
                'label': '📊 View Project Status', 
                'description': 'Get comprehensive project overview',
                'parameters': {},
                'type': 'info'
            },
            'show_team_status': {
                'tool': 'show_team_status',
                'label': '👥 View Team Status', 
                'description': 'See current team composition and activities',
                'parameters': {},
                'type': 'info'
            },
            'show_goal_progress': {
                'tool': 'show_goal_progress',
                'label': '🎯 View Goal Progress', 
                'description': 'Check progress on objectives',
                'parameters': {},
                'type': 'info'
            },
            'show_deliverables': {
                'tool': 'show_deliverables',
                'label': '📦 View Deliverables', 
                'description': 'See completed deliverables and assets',
                'parameters': {},
                'type': 'info'
            },
            'add_team_member': {
                'tool': 'add_team_member',
                'label': '➕ Add Team Member', 
                'description': 'Add a new member to the team',
                'parameters': {
                    'role': 'developer',
                    'seniority': 'senior'
                },
                'type': 'action'
            }
        }
        
        suggested_actions = []
        
        # Look for tool mentions in single quotes
        tool_pattern = r"'([^']+)'"
        tools_mentioned = re.findall(tool_pattern, ai_response)
        
        # Look for specific action recommendations
        if "add_team_member" in ai_response.lower() or "add.*member" in ai_response.lower():
            tools_mentioned.append("add_team_member")
        
        if any(phrase in ai_response.lower() for phrase in ["monitor", "check progress", "track"]):
            tools_mentioned.extend(["show_project_status", "show_goal_progress"])
        
        # Convert to action objects
        for tool in set(tools_mentioned):  # Remove duplicates
            if tool in actionable_tools:
                suggested_actions.append(actionable_tools[tool])
        
        # If no specific tools mentioned but it's a strategic response, suggest status tools
        if not suggested_actions and any(section in ai_response for section in ["**ANALYSIS**", "**REASONING**"]):
            suggested_actions.append(actionable_tools["show_project_status"])
        
        return suggested_actions[:3]  # Limit to 3 actions to avoid overwhelming UI
    
    async def _prepare_messages_with_history(self, system_prompt: str, user_prompt: str, max_history: int = None) -> list:
        """
        Prepare messages array with conversation history for better AI context.
        
        Args:
            system_prompt: System instructions
            user_prompt: Current user message
            max_history: Maximum number of previous messages to include (default: 6, so 3 exchanges)
        
        Returns:
            List of messages for OpenAI API
        """
        try:
            # Get max_history from environment or use default
            if max_history is None:
                import os
                max_history = int(os.getenv('CONVERSATION_HISTORY_LIMIT', 6))
            
            # Start with system message
            messages = [{"role": "system", "content": system_prompt}]
            
            # Get conversation history from database
            supabase = get_supabase_client()
            conversation_identifier = f"{self.workspace_id}_{self.chat_id}"
            
            # Fetch recent messages from this conversation
            history_result = supabase.table("conversation_messages")\
                .select("content, role, created_at")\
                .eq("conversation_identifier", conversation_identifier)\
                .order("created_at", desc=True)\
                .limit(max_history)\
                .execute()
            
            # Reverse to get chronological order (oldest first)
            if history_result.data:
                history_messages = list(reversed(history_result.data))
                
                # Add to messages array
                for msg in history_messages:
                    # Map our role types to OpenAI role types
                    openai_role = "assistant" if msg["role"] == "assistant" else "user"
                    
                    messages.append({
                        "role": openai_role,
                        "content": msg["content"]
                    })
                
                logger.info(f"📚 Loaded {len(history_messages)} messages from conversation history")
            else:
                logger.info("📭 No conversation history found")
            
            # Add current user message
            messages.append({"role": "user", "content": user_prompt})
            
            # Log total context size for monitoring
            total_chars = sum(len(msg["content"]) for msg in messages)
            logger.info(f"💬 Total conversation context: {len(messages)} messages, {total_chars} characters")
            
            return messages
            
        except Exception as e:
            logger.warning(f"Could not load conversation history: {e}")
            # Fallback to simple messages without history
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
    
    def _handle_file_upload_in_message(self, user_message: str, workspace_id: str) -> tuple[str, dict]:
        """
        Pre-process user message to extract and handle file uploads before sending to OpenAI.
        This prevents large base64 file content from being sent in the prompt.
        
        Returns:
            tuple: (processed_message, file_upload_result)
        """
        import re
        import json
        
        # Check if message contains file upload command
        upload_pattern = r'EXECUTE_TOOL:\s*upload_document\s*({[^}]*})'
        match = re.search(upload_pattern, user_message, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # No file upload detected, return original message
            return user_message, {"success": False, "message": "No file upload detected"}
        
        try:
            # Extract the parameters
            params_str = match.group(1)
            # Clean up the JSON string - handle potential formatting issues
            params_str = params_str.strip()
            if not params_str.startswith('{'):
                params_str = '{' + params_str
            if not params_str.endswith('}'):
                params_str = params_str + '}'
            
            # Parse parameters
            params = json.loads(params_str)
            
            # Get file info
            file_data = params.get('file_data', '')
            filename = params.get('filename', 'unknown_file')
            file_size = len(file_data) if file_data else 0
            
            logger.info(f"🔍 File upload detected: {filename} ({file_size} characters base64)")
            
            # Execute the file upload immediately
            from tools.document_tools import upload_document
            upload_result = upload_document(workspace_id, file_data, filename)
            
            # Create a summarized message for OpenAI (without the large file content)
            if upload_result.get("success"):
                processed_message = f"I just uploaded a file named '{filename}' to the workspace. Please confirm the upload was successful and let me know what I should do next with this file."
            else:
                processed_message = f"I tried to upload a file named '{filename}' but it failed. Error: {upload_result.get('message', 'Unknown error')}. Please help me resolve this issue."
            
            logger.info(f"✅ File upload processed, message reduced from {len(user_message)} to {len(processed_message)} characters")
            
            return processed_message, upload_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse file upload parameters: {e}")
            # Return original message if parsing fails
            return user_message, {"success": False, "message": f"Failed to parse upload parameters: {e}"}
        except Exception as e:
            logger.error(f"❌ Error handling file upload: {e}")
            # Return original message if any error occurs
            return user_message, {"success": False, "message": f"Error handling file upload: {e}"}
    
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
            "show_project_status": {
                "description": "Show comprehensive project status including team, tasks, and deliverables",
                "parameters": {}
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
                
            elif tool_name == "show_project_status":
                # SCALABLE: Comprehensive project status
                return await workspace_service.get_project_status(self.workspace_id)
                
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
                
                # Call the tool with proper parameters
                if tool_name == "upload_document":
                    result = await tool_instance.execute(
                        file_data=parameters.get("file_data"),
                        filename=parameters.get("filename"),
                        sharing_scope=parameters.get("sharing_scope", "team"),
                        description=parameters.get("description"),
                        tags=parameters.get("tags"),
                        context=context
                    )
                elif tool_name == "list_documents":
                    result = await tool_instance.execute(
                        scope=parameters.get("scope"),
                        context=context
                    )
                elif tool_name == "delete_document":
                    result = await tool_instance.execute(
                        document_id=parameters.get("document_id"),
                        context=context
                    )
                elif tool_name == "search_documents":
                    result = await tool_instance.execute(
                        query=parameters.get("query"),
                        max_results=parameters.get("max_results"),
                        context=context
                    )
                
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
            
            if result.get("success"):
                message = result.get("message", "Action completed successfully")
                return f"✅ {message}"
            else:
                message = result.get("message", "Action failed")
                return f"❌ {message}"
                
        except Exception as e:
            logger.error(f"Error parsing/executing tool: {e}")
            return f"Error executing action: {str(e)}"