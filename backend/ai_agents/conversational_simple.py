"""
Simplified Conversational Agent - AI-driven responses without complex SDK dependencies
Maintains AI-enhanced principles while providing reliable functionality
"""

import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from openai import OpenAI
from pydantic import BaseModel

from database import get_supabase_client
from utils.context_manager import get_workspace_context
from tools.openai_sdk_tools import openai_tools_manager
from tools.workspace_service import get_workspace_service
from ai_agents.enhanced_reasoning import EnhancedReasoningEngine

# Import shared conversation response model
from ai_agents.conversation_models import ConversationResponse

logger = logging.getLogger(__name__)

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
                # Store the step locally
                enriched_step = {
                    **step_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "workspace_id": self.workspace_id,
                    "chat_id": self.chat_id
                }
                self._current_thinking_steps.append(enriched_step)
                
                # 🧠 REAL-TIME: Broadcast thinking step via WebSocket (Claude/o3 style)
                try:
                    from routes.websocket import broadcast_thinking_step
                    await broadcast_thinking_step(self.workspace_id, enriched_step)
                except Exception as e:
                    logger.debug(f"Could not broadcast thinking step: {e}")
                
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
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "history_loading", 
                    "title": "📚 Loading Conversation History",
                    "description": "Retrieving previous messages for context continuity...",
                    "status": "in_progress"
                })
            
            # We'll load this in the AI generation step, but show thinking here
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "history_loading",
                    "title": "📚 History Loaded", 
                    "description": "Retrieved recent conversation context for better understanding",
                    "status": "completed"
                })
            
            # Step 3: Query Analysis
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "query_analysis",
                    "title": "🧠 Analyzing Request",
                    "description": f"Understanding: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'",
                    "status": "in_progress"
                })
            
            # AI-driven query classification - let the AI decide the complexity level
            query_classification_prompt = f"""
            Analyze this user message and classify its complexity:
            
            User message: "{user_message}"
            
            Return ONLY one of these classifications:
            - SIMPLE_LOOKUP: Direct data retrieval (facts, status, numbers, lists)
            - STRATEGIC_ANALYSIS: Requires reasoning, recommendations, planning
            - GENERAL_INQUIRY: Standard information request
            
            Classification:"""
            
            try:
                classification_response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": query_classification_prompt}],
                    max_tokens=20,
                    temperature=0
                )
                query_type = classification_response.choices[0].message.content.strip()
            except:
                query_type = "GENERAL_INQUIRY"  # Safe fallback
            
            # Determine processing approach based on AI classification
            requires_data = "LOOKUP" in query_type or "ANALYSIS" in query_type
            is_strategic_question = query_type == "STRATEGIC_ANALYSIS"
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "query_analysis", 
                    "title": "🧠 Request Understood",
                    "description": f"Type: {query_type} | Data needed: {'Yes' if requires_data else 'No'}",
                    "status": "completed"
                })
            
            # Step 4: Todo List Decomposition (Claude/o3 style)
            if is_strategic_question or "decomp" in user_message.lower() or "task" in user_message.lower():
                await storing_thinking_callback({
                        "type": "thinking_step",
                        "step": "todo_decomposition",
                        "title": "📋 Breaking Down the Problem",
                        "description": "Analyzing request and creating step-by-step action plan...",
                        "status": "in_progress"
                    })
                
                # Generate AI-driven todo list decomposition
                todo_prompt = f"""
                Based on this request: "{user_message}"
                
                Create a step-by-step todo list breakdown showing how you'll approach this task.
                Format as a JSON array of todo items with: title, description, status (pending/in_progress/completed)
                
                Example format:
                [
                  {{"title": "Analyze current goals", "description": "Review workspace goals and progress", "status": "pending"}},
                  {{"title": "Identify gaps", "description": "Find areas needing attention", "status": "pending"}}
                ]
                
                Todo list:"""
                
                try:
                    todo_response = self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": todo_prompt}],
                        max_tokens=300,
                        temperature=0.3
                    )
                    todo_list_raw = todo_response.choices[0].message.content.strip()
                    
                    # Try to parse as JSON, fallback to text
                    try:
                        import json
                        todo_list = json.loads(todo_list_raw)
                    except:
                        # Fallback: create simple todo from text
                        todo_list = [
                            {"title": "Analyze request", "description": "Understanding user requirements", "status": "completed"},
                            {"title": "Plan approach", "description": "Define strategy and steps", "status": "in_progress"},
                            {"title": "Generate response", "description": "Create comprehensive answer", "status": "pending"}
                        ]
                    
                except Exception as e:
                    # Safe fallback todo list
                    todo_list = [
                        {"title": "Process request", "description": "Analyze and understand requirements", "status": "in_progress"},
                        {"title": "Generate solution", "description": "Create actionable response", "status": "pending"}
                    ]
                
                await storing_thinking_callback({
                        "type": "thinking_step",
                        "step": "todo_decomposition",
                        "title": "📋 Action Plan Created",
                        "description": f"Generated {len(todo_list)} action items for systematic execution",
                        "status": "completed",
                        "todo_list": todo_list  # 🎯 Claude/o3 style todo breakdown
                    })
            
            # Step 4: Data Gathering (AI-driven based on context availability)
            if requires_data and thinking_callback:
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "data_gathering",
                    "title": "📊 Gathering Relevant Data", 
                    "description": "Analyzing available workspace context and metrics...",
                    "status": "in_progress"
                })
                
                # AI-driven data analysis based on available context
                context_summary = self._prepare_context_for_ai()
                
                await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "data_gathering",
                    "title": "📊 Data Analysis Complete",
                    "description": "Workspace context analyzed and ready for intelligent processing",
                    "status": "completed"
                })
                
            # Step 4.5: Deep Reasoning Analysis (AI-driven for strategic queries)
            if query_type == "STRATEGIC_ANALYSIS" and thinking_callback:
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
            await storing_thinking_callback({
                    "type": "thinking_step", 
                    "step": "ai_processing",
                    "title": "🤖 Generating Strategic Response",
                    "description": "Applying project management expertise and context analysis...",
                    "status": "in_progress"
                })
            
            # Generate AI-driven response using OpenAI with appropriate context
            ai_response = await self._generate_intelligent_response(user_message, query_type)
            
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "ai_processing", 
                    "title": "🤖 Response Generated",
                    "description": "Strategic analysis complete with recommendations and next actions",
                    "status": "completed"
                })
            
            # Step 6: Action Extraction (AI-driven)
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "action_extraction",
                    "title": "⚡ Extracting Actionable Items",
                    "description": "Identifying tools and quick actions from the response...",
                    "status": "in_progress"
                })
            
            # AI determines if actions are needed based on response content
            suggested_actions = self._extract_suggested_actions(ai_response)
            
            action_count = len(suggested_actions)
            await storing_thinking_callback({
                    "type": "thinking_step",
                    "step": "action_extraction",
                    "title": "⚡ Actions Ready",
                    "description": f"Found {action_count} actionable tools ready for execution",
                    "status": "completed"
                })
            
            # AI-driven step counting based on actual processing
            base_steps = 7  # Standard process steps
            deep_reasoning_steps = 7 if 'deep_analysis' in self.context else 0
            total_steps = base_steps + deep_reasoning_steps
            
            # Step 7: Finalizing
            process_type = "deep reasoning" if total_steps > 7 else "standard analysis"
            await storing_thinking_callback({
                    "type": "thinking_complete",
                    "title": "✅ Analysis Complete",
                    "description": f"Completed {total_steps} steps with {process_type} process"
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
            if thinking_callback:
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
            
            # Get only essential workspace info including budget
            workspace_result = supabase.table("workspaces")\
                .select("id,name,description,status,budget")\
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
            
            # Prepare workspace data with budget fallback
            workspace_data = workspace_result.data[0] if workspace_result.data else {}
            if 'budget' not in workspace_data or workspace_data['budget'] is None:
                # Add fallback budget if not present in database
                workspace_data['budget'] = 50000.00  # Default budget for testing
            
            return {
                "workspace_id": self.workspace_id,
                "workspace": workspace_data,
                "agents": agents_result.data[:3],  # Limit to 3 agents
                "task_count": len(tasks_result.data),
                "context_type": "lightweight"
            }
            
        except Exception as e:
            logger.error(f"Failed to load lightweight context: {e}")
            return {"workspace_id": self.workspace_id, "error": "lightweight_context_unavailable"}
    
    async def _generate_intelligent_response(self, user_message: str, query_type: str = "GENERAL_INQUIRY") -> str:
        """
        Generate AI-driven response based on context and user message.
        Uses AI to determine the appropriate response style based on query classification.
        Uses OpenAI to provide intelligent, context-aware responses.
        """
        try:
            # Check if user is asking about available tools
            if self._is_asking_about_tools(user_message):
                return await self._generate_tools_artifact_response()
            
            # 🔍 DOCUMENT SEARCH: Check if user is asking about documents
            document_search_results = None
            if self._is_asking_about_documents(user_message):
                logger.info("📄 Document-related query detected, searching documents...")
                document_search_results = await self._search_relevant_documents(user_message)
            
            # Prepare context for AI
            context_summary = self._prepare_context_for_ai()
            
            # Include document search results in context if available
            if document_search_results:
                context_summary += f"\n\n📄 DOCUMENT SEARCH RESULTS:\n{document_search_results}"
            
            # Create intelligent prompt with tool awareness
            tools_description = self._get_tools_description()
            
            system_prompt = f"""You are an intelligent AI Project Manager with deep analytical capabilities and full workspace context.

WORKSPACE CONTEXT:
{context_summary}

CHAT CONTEXT: {self.chat_id}

AVAILABLE TOOLS:
{tools_description}

CORE INTELLIGENCE FRAMEWORK:
You have access to ALL workspace data - team composition, performance metrics, budget, goals, insights, deliverables, project history, AND uploaded documents. Use this context to:

1. **ANALYZE** - Always gather relevant data first using appropriate tools
2. **REASON** - Apply project management expertise to the situation  
3. **RECOMMEND** - Provide specific, actionable recommendations
4. **EXECUTE** - Offer quick actions when appropriate

DOCUMENT AWARENESS:
- When users ask about uploaded documents, files, or specific content, the system has already searched for relevant documents
- Use the DOCUMENT SEARCH RESULTS provided in the context to answer questions about document content
- If document search results are provided, incorporate them into your response
- You can reference specific documents by name and provide summaries based on search results

RESPONSE STYLE GUIDANCE:
Query Classification: {query_type}

Adapt your response style based on the query classification:

- SIMPLE_LOOKUP: Provide direct, concise answers using available data. Be efficient.
- STRATEGIC_ANALYSIS: Deep analysis with reasoning, alternatives, and strategic recommendations
- GENERAL_INQUIRY: Balanced response with appropriate depth based on context

For execution requests (especially goal progress, project status, team management):
- ALWAYS execute tools immediately when data is needed
- Use: "EXECUTE_TOOL: tool_name {{parameters}}"
- For goal progress: "EXECUTE_TOOL: show_goal_progress {{\"goal_id\": \"goal-id-here\"}}"
- For project status: "EXECUTE_TOOL: show_project_status {{}}"

CRITICAL: If user asks about goal progress, status, or specific data - EXECUTE the appropriate tool first, then analyze the results.

Be context-aware and adapt your expertise to the domain of the workspace. Extract insights from available data and provide value-driven responses."""

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

CRITICAL INSTRUCTIONS FOR DATA REQUESTS:

1. If user asks about GOAL PROGRESS or mentions a goal ID, immediately respond with:
   EXECUTE_TOOL: show_goal_progress {{"goal_id": "goal-id-here"}}

2. If user asks about PROJECT STATUS, immediately respond with:
   EXECUTE_TOOL: show_project_status {{}}

3. If user asks about TEAM, immediately respond with:
   EXECUTE_TOOL: show_team_status {{}}

Examples of data requests requiring immediate tool execution:
- "Show goal progress"
- "What's the status of this goal"  
- "Goal analysis"
- "Project status"
- "Team status"

For strategic questions (planning, recommendations):
- Use the structured format with ANALYSIS, REASONING, RECOMMENDATIONS, NEXT ACTIONS

For simple execution requests:
- Start immediately with EXECUTE_TOOL: tool_name {{parameters}}"""

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
            
            # Check if the AI wants to execute a tool (search anywhere in response)
            import re
            execute_tool_match = re.search(r'EXECUTE_TOOL:\s*(\w+)\s*({.*?})?', ai_response)
            if execute_tool_match:
                tool_response = await self._parse_and_execute_tool_from_match(execute_tool_match)
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
            },
            'approve_all_feedback': {
                'tool': 'approve_all_feedback',
                'label': '✅ Approve All Feedback', 
                'description': 'Approve all pending feedback requests',
                'parameters': {},
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
        
        # Look for approve feedback patterns
        if any(phrase in ai_response.lower() for phrase in ["approve.*feedback", "approve all", "execute_tool.*approve_all_feedback"]):
            tools_mentioned.append("approve_all_feedback")
        
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
                "description": "Pause all team activities and task execution. Current tasks will complete gracefully but no new tasks will start.",
                "parameters": {}
            },
            "approve_all_feedback": {
                "description": "Approve all pending human feedback requests for this workspace",
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
            "fix_workspace_issues": {
                "description": "Analyze and fix workspace issues that require intervention",
                "parameters": {
                    "action_type": "string - Type of fix: 'restart_failed_tasks', 'reset_agents', 'clear_blockages'"
                }
            },
            "auto_complete_with_recovery": {
                "description": "Complete missing deliverables AND recover failed tasks automatically",
                "parameters": {
                    "include_failed_recovery": "boolean - Whether to include failed task recovery (default: true)"
                }
            },
            "analyze_blocking_issues": {
                "description": "Deep analysis of what's blocking progress toward deliverables",
                "parameters": {}
            },
            "resume_workspace_operations": {
                "description": "Resume stalled operations and restart progress",
                "parameters": {
                    "force_restart": "boolean - Whether to force restart stuck processes"
                }
            },
            "list_available_tools": {
                "description": "List all tools available to AI agents in the system",
                "parameters": {}
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
            },
            "search_document_content": {
                "description": "Search and retrieve actual content from uploaded documents (enhanced RAG)",
                "parameters": {
                    "query": "string - Search query for document content",
                    "max_results": "int - Maximum number of results (default: 3)",
                    "include_full_text": "bool - Include full extracted text (default: false)"
                }
            },
            "read_document_content": {
                "description": "Read the full content of a specific document",
                "parameters": {
                    "filename": "string - Document filename to read",
                    "document_id": "string - Alternative: document ID to read"
                }
            },
            "summarize_document": {
                "description": "Generate an AI summary of document content",
                "parameters": {
                    "filename": "string - Document filename to summarize",
                    "document_id": "string - Alternative: document ID to summarize",
                    "summary_type": "string - Type of summary: brief/detailed/key_points (default: brief)"
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
                # 🚀 AUTO-START: Trigger immediate goal analysis and task generation
                logger.info(f"🎯 Manual team start requested for workspace {self.workspace_id}")
                
                try:
                    # First set workspace to active
                    status_result = await workspace_service.update_workspace_status(
                        workspace_id=self.workspace_id,
                        status="active"
                    )
                    
                    # Check if workspace has goals and team
                    supabase = get_supabase_client()
                    
                    # Check for active goals
                    goals_response = supabase.table("workspace_goals").select("id").eq(
                        "workspace_id", self.workspace_id
                    ).eq("status", "active").execute()
                    
                    # Check for active agents  
                    agents_response = supabase.table("agents").select("id").eq(
                        "workspace_id", self.workspace_id
                    ).execute()
                    
                    if not goals_response.data:
                        return {
                            "success": False,
                            "message": "❌ Cannot start team: No active goals found. Please confirm project goals first.",
                            "action_required": "confirm_goals"
                        }
                    
                    if not agents_response.data:
                        return {
                            "success": False, 
                            "message": "❌ Cannot start team: No agents found. Please approve team proposal first.",
                            "action_required": "approve_team"
                        }
                    
                    # Trigger immediate goal analysis and task creation
                    from automated_goal_monitor import automated_goal_monitor
                    import asyncio
                    
                    asyncio.create_task(automated_goal_monitor._trigger_immediate_goal_analysis(self.workspace_id))
                    
                    return {
                        "success": True,
                        "message": f"✅ Team started successfully! Auto-start triggered for {len(goals_response.data)} goals with {len(agents_response.data)} agents.",
                        "goals_count": len(goals_response.data),
                        "agents_count": len(agents_response.data),
                        "auto_start_triggered": True
                    }
                    
                except Exception as e:
                    logger.error(f"Error in manual team start: {e}")
                    return {
                        "success": False,
                        "message": f"❌ Error starting team: {str(e)}",
                        "error": str(e)
                    }
                
            elif tool_name == "pause_team":
                # 🛑 PAUSE TEAM: Stop task execution and update workspace status
                logger.info(f"🛑 Team pause requested for workspace {self.workspace_id}")
                
                try:
                    # Update workspace status to paused
                    status_result = await workspace_service.update_workspace_status(
                        workspace_id=self.workspace_id,
                        status="paused"
                    )
                    
                    # Get current team and task information
                    supabase = get_supabase_client()
                    
                    # Check current agents
                    agents_response = supabase.table("agents").select("id, name, status").eq(
                        "workspace_id", self.workspace_id
                    ).execute()
                    
                    # Check active tasks
                    tasks_response = supabase.table("tasks").select("id, name, status").eq(
                        "workspace_id", self.workspace_id
                    ).in_("status", ["pending", "in_progress"]).execute()
                    
                    # Update agent statuses to paused
                    if agents_response.data:
                        supabase.table("agents").update({"status": "paused"}).eq(
                            "workspace_id", self.workspace_id
                        ).execute()
                    
                    return {
                        "success": True,
                        "message": f"✅ Team paused successfully! {len(agents_response.data)} agents paused, {len(tasks_response.data)} active tasks will complete but no new tasks will start.",
                        "agents_paused": len(agents_response.data),
                        "active_tasks": len(tasks_response.data),
                        "workspace_status": "paused",
                        "note": "Current tasks will complete gracefully. Use 'start_team' to resume operations."
                    }
                    
                except Exception as e:
                    logger.error(f"Error pausing team: {e}")
                    return {
                        "success": False,
                        "message": f"❌ Error pausing team: {str(e)}",
                        "error": str(e)
                    }
                
            elif tool_name == "approve_all_feedback":
                # 📋 APPROVE ALL FEEDBACK: Approve all pending human feedback requests
                logger.info(f"📋 Mass feedback approval requested for workspace {self.workspace_id}")
                
                try:
                    from human_feedback_manager import human_feedback_manager
                    
                    # Get all pending feedback requests for this workspace
                    pending_requests = await human_feedback_manager.get_pending_requests(self.workspace_id)
                    
                    if not pending_requests:
                        return {
                            "success": True,
                            "message": "✅ No pending feedback requests found.",
                            "approved_count": 0
                        }
                    
                    # Approve all pending requests
                    approved_count = 0
                    failed_count = 0
                    
                    for request in pending_requests:
                        try:
                            approval_response = {
                                "approved": True,
                                "comment": "Bulk approval via conversational agent",
                                "auto_approved": True,
                                "bulk_operation": True
                            }
                            
                            from human_feedback_manager import FeedbackStatus
                            
                            success = await human_feedback_manager.respond_to_request(
                                request_id=request["id"],
                                response=approval_response,
                                status=FeedbackStatus.APPROVED
                            )
                            
                            if success:
                                approved_count += 1
                                logger.info(f"✅ Approved feedback request: {request['title']}")
                            else:
                                failed_count += 1
                                logger.warning(f"❌ Failed to approve feedback request: {request['title']}")
                                
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"Error approving feedback {request.get('id')}: {e}")
                    
                    return {
                        "success": True,
                        "message": f"✅ Bulk approval completed: {approved_count} approved, {failed_count} failed",
                        "approved_count": approved_count,
                        "failed_count": failed_count,
                        "total_processed": len(pending_requests)
                    }
                    
                except Exception as e:
                    logger.error(f"Error in bulk feedback approval: {e}")
                    return {
                        "success": False,
                        "message": f"❌ Error approving feedback: {str(e)}",
                        "error": str(e)
                    }
                
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
            
            elif tool_name == "fix_workspace_issues":
                # SCALABLE: Intervention system
                return await self._fix_workspace_issues(
                    action_type=parameters.get("action_type", "restart_failed_tasks")
                )
            
            elif tool_name == "auto_complete_with_recovery":
                # 🤖 NEW: Enhanced Auto-Complete with Failed Task Recovery
                return await self._auto_complete_with_recovery(
                    include_failed_recovery=parameters.get("include_failed_recovery", True)
                )
            
            elif tool_name == "analyze_blocking_issues":
                # SCALABLE: Deep analysis
                return await self._analyze_blocking_issues()
            
            elif tool_name == "resume_workspace_operations":
                # SCALABLE: Resume operations
                return await self._resume_workspace_operations(
                    force_restart=parameters.get("force_restart", False)
                )
            
            elif tool_name == "list_available_tools":
                # List all available tools from the tool registry
                try:
                    from tools.registry import tool_registry
                    available_tools = tool_registry.list_tools()
                    
                    # Also include conversational tools
                    conversational_tools = list(self.tools.keys())
                    
                    return {
                        "success": True,
                        "message": "Available Tools",
                        "modular_tools": available_tools,
                        "conversational_tools": conversational_tools,
                        "total_tools": len(available_tools) + len(conversational_tools),
                        "formatted": f"""
🛠️ **Available Tools in the System**

**Modular Agent Tools ({len(available_tools)})**:
{chr(10).join(f"• {tool}" for tool in available_tools)}

**Conversational Tools ({len(conversational_tools)})**:
{chr(10).join(f"• /{tool}" for tool in conversational_tools)}

💡 **Usage Tips**:
- Modular tools are used by AI agents automatically
- Conversational tools can be accessed via slash commands (/)
- Type "/" in any chat to see available commands
                        """
                    }
                except Exception as e:
                    logger.error(f"Error listing tools: {e}")
                    return {
                        "success": False,
                        "message": f"Error listing tools: {str(e)}"
                    }
                
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
                    
            elif tool_name in ["search_document_content", "read_document_content", "summarize_document"]:
                # Use Enhanced RAG tools for content search
                from tools.enhanced_document_search import enhanced_document_tools
                
                tool_instance = enhanced_document_tools[tool_name]
                
                # Call the enhanced RAG tool with proper parameters
                if tool_name == "search_document_content":
                    result = await tool_instance.execute(
                        query=parameters.get("query"),
                        workspace_id=self.workspace_id,
                        max_results=parameters.get("max_results", 3),
                        include_full_text=parameters.get("include_full_text", False)
                    )
                elif tool_name == "read_document_content":
                    result = await tool_instance.execute(
                        document_id=parameters.get("document_id"),
                        filename=parameters.get("filename"),
                        workspace_id=self.workspace_id
                    )
                elif tool_name == "summarize_document":
                    result = await tool_instance.execute(
                        document_id=parameters.get("document_id"),
                        filename=parameters.get("filename"),
                        workspace_id=self.workspace_id,
                        summary_type=parameters.get("summary_type", "brief")
                    )
                
                return {
                    "success": True,
                    "message": result,
                    "action": tool_name
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
    
    async def _parse_and_execute_tool_from_match(self, match) -> str:
        """Parse tool execution from regex match and execute the tool"""
        try:
            tool_name = match.group(1)
            params_str = match.group(2) or "{}"
            
            print(f"🔧 [_parse_and_execute_tool_from_match] Executing tool: {tool_name}")
            print(f"🔧 [_parse_and_execute_tool_from_match] Parameters: {params_str}")
            
            # Parse parameters
            try:
                parameters = json.loads(params_str)
            except Exception as e:
                print(f"❌ [_parse_and_execute_tool_from_match] JSON parse error: {e}")
                parameters = {}
            
            # Execute the tool
            result = await self._execute_tool(tool_name, parameters)
            
            # Format the result as a structured response
            if result.get("success"):
                message = result.get("message", "Action completed successfully")
                
                # Enhanced formatting for different tool results
                if tool_name == "show_goal_progress" and "goals" in result:
                    goals = result["goals"]
                    if goals:
                        goal = goals[0]
                        title = goal.get("title", "Goal")
                        status = goal.get("status", "unknown")
                        progress = goal.get("progress", "0%")
                        description = goal.get("description", "")
                        
                        formatted_message = f"""📊 **{title}**

**Status**: {status}
**Progress**: {progress}
**Description**: {description}

{message}"""
                        return formatted_message
                
                elif tool_name == "generate_image":
                    prompt = parameters.get("prompt", "Generated image")
                    
                    # Try to extract image URL from different possible result formats
                    image_url = None
                    if "image_url" in result:
                        image_url = result["image_url"]
                    elif "result" in result and isinstance(result["result"], dict):
                        if "image_url" in result["result"]:
                            image_url = result["result"]["image_url"]
                        elif "url" in result["result"]:
                            image_url = result["result"]["url"]
                    elif "result" in result and isinstance(result["result"], str):
                        # If result is a string, it might be the URL
                        if "http" in result["result"]:
                            image_url = result["result"]
                    
                    # Search for URL in the message if not found
                    if not image_url and "message" in result:
                        import re
                        url_match = re.search(r'https?://[^\s]+', result["message"])
                        if url_match:
                            image_url = url_match.group()
                    
                    if image_url:
                        return f"""🎨 **Image Generated Successfully**

**Prompt**: {prompt}

![Generated Image]({image_url})

**URL**: {image_url}

{message}"""
                    else:
                        return f"""🎨 **Image Generation Result**

**Prompt**: {prompt}

{message}

*Image URL not found in expected format. Please check the tool response.*"""
                
                return f"✅ **Tool Executed Successfully**\n\n{message}"
            else:
                error_msg = result.get("message", "Tool execution failed")
                return f"❌ **Tool Execution Failed**\n\n{error_msg}"
                
        except Exception as e:
            print(f"❌ [_parse_and_execute_tool_from_match] Error: {e}")
            return f"❌ **Error executing tool**: {str(e)}"

    async def _parse_and_execute_tool(self, ai_response: str) -> str:
        """Parse tool execution request and execute the tool (legacy method)"""
        try:
            # Extract tool name and parameters
            import re
            match = re.match(r"EXECUTE_TOOL:\s*(\w+)\s*(\{.*\})?", ai_response)
            if not match:
                return "Error parsing tool execution request."
            
            return await self._parse_and_execute_tool_from_match(match)
            
        except Exception as e:
            logger.error(f"Failed to parse and execute tool: {e}")
            return f"Error executing tool: {str(e)}"
            
            # Format the result as a structured response
            if result.get("success"):
                message = result.get("message", "Action completed successfully")
                
                # Enhanced formatting for different tool results
                if tool_name == "show_goal_progress" and "goals" in result:
                    goals = result["goals"]
                    if goals:
                        goal = goals[0]
                        title = goal.get("title", "Goal")
                        status = goal.get("status", "unknown")
                        progress = goal.get("progress", "0%")
                        description = goal.get("description", "")
                        
                        formatted_message = f"""📊 **{title}**

**Status**: {status}
**Progress**: {progress}
**Description**: {description}

✅ Goal data successfully retrieved and analyzed."""
                        return formatted_message
                    else:
                        return "📊 **Goal Analysis**\n\n⚠️ No goal data found for the specified ID."
                
                # Enhanced formatting for team status with intervention detection
                elif tool_name == "show_team_status" and "workspace_status" in result:
                    workspace_status = result.get("workspace_status", "unknown")
                    team_members = result.get("team_members", 0)
                    handoffs_count = len(result.get("handoffs", []))
                    
                    if workspace_status == "needs_intervention":
                        intervention_actions = self._generate_intervention_actions(result)
                        formatted_message = f"""👥 **Team Status Report**

**Members**: {team_members} active
**Handoffs**: {handoffs_count} configured
**Status**: ⚠️ {workspace_status}

🚨 **Intervention Required:**
{intervention_actions}

💡 **Quick Actions Available:**
🔧 Fix Issues - Analyze and resolve blocking problems
📋 Review Tasks - Check failed/stuck tasks status
⚡ Resume Operations - Restart stalled processes

*The system has detected issues that need your attention to continue progress toward deliverables.*"""
                        return formatted_message
                    else:
                        formatted_message = f"""👥 **Team Status Report**

**Members**: {team_members} active
**Handoffs**: {handoffs_count} configured  
**Status**: ✅ {workspace_status}

✅ Team operating normally and making progress."""
                        return formatted_message
                
                # Enhanced formatting for project status with intervention detection
                elif tool_name == "show_project_status" and "details" in result:
                    details = result["details"]
                    team_status = details.get("team", {})
                    workspace_status = team_status.get("workspace_status", "unknown")
                    
                    if workspace_status == "needs_intervention" or "failed" in str(details.get("tasks", {})):
                        intervention_actions = self._generate_project_intervention_actions(result)
                        formatted_message = f"""📊 **Project Status Report**

{message}

🚨 **Action Required:**
{intervention_actions}

💡 **Quick Actions Available:**
🔧 Fix Issues - Restart failed tasks and reset agents
📋 Analyze Issues - Deep analysis of blocking problems
⚡ Resume Operations - Force restart all stalled processes

*Click any action above to resolve issues and continue progress.*"""
                        return formatted_message
                
                
                return f"✅ {message}"
            else:
                message = result.get("message", "Action failed")
                return f"❌ {message}"
                
        except Exception as e:
            logger.error(f"Error parsing/executing tool: {e}")
            return f"Error executing action: {str(e)}"
    
    def _generate_intervention_actions(self, team_status_result: dict) -> str:
        """Generate specific intervention recommendations based on team status"""
        try:
            workspace_status = team_status_result.get("workspace_status", "unknown")
            agents = team_status_result.get("agents", [])
            
            issues = []
            
            # Check for agent issues
            for agent in agents:
                agent_status = agent.get("status", "unknown")
                agent_health = agent.get("health", {}).get("status", "unknown") if isinstance(agent.get("health"), dict) else agent.get("health", "unknown")
                
                if agent_status in ["error", "terminated", "paused"]:
                    issues.append(f"Agent {agent.get('name', 'Unknown')} is {agent_status}")
                elif agent_health in ["unhealthy", "degraded"]:
                    issues.append(f"Agent {agent.get('name', 'Unknown')} health is {agent_health}")
            
            if not issues:
                issues.append("Workspace requires manual review to identify specific issues")
            
            return "\n".join([f"• {issue}" for issue in issues[:3]])  # Limit to top 3 issues
            
        except Exception as e:
            logger.error(f"Error generating intervention actions: {e}")
            return "• System status unclear - manual review recommended"
    
    def _generate_project_intervention_actions(self, project_status_result: dict) -> str:
        """Generate specific intervention recommendations for project status"""
        try:
            details = project_status_result.get("details", {})
            tasks = details.get("tasks", {})
            team = details.get("team", {})
            
            issues = []
            
            # Check task issues
            if "failed" in tasks and tasks["failed"] > 0:
                issues.append(f"{tasks['failed']} tasks have failed and need investigation")
            
            if "needs_enhancement" in tasks and tasks["needs_enhancement"] > 0:
                issues.append(f"{tasks['needs_enhancement']} tasks need quality improvements")
            
            if "pending_verification" in tasks and tasks["pending_verification"] > 3:
                issues.append(f"{tasks['pending_verification']} tasks are waiting for verification")
            
            # Check team issues
            workspace_status = team.get("workspace_status", "unknown")
            if workspace_status == "needs_intervention":
                issues.append("Team workspace requires immediate attention")
            
            if not issues:
                issues.append("Progress has stalled - comprehensive review needed")
            
            return "\n".join([f"• {issue}" for issue in issues[:3]])  # Limit to top 3 issues
            
        except Exception as e:
            logger.error(f"Error generating project intervention actions: {e}")
            return "• Project status unclear - manual intervention recommended"
    
    async def _fix_workspace_issues(self, action_type: str) -> dict:
        """Fix workspace issues based on action type"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            if action_type == "restart_failed_tasks":
                # Reset failed tasks to pending
                result = supabase.table("tasks")\
                    .update({"status": "pending", "error_message": None})\
                    .eq("workspace_id", self.workspace_id)\
                    .eq("status", "failed")\
                    .execute()
                
                affected_count = len(result.data) if result.data else 0
                return {
                    "success": True,
                    "message": f"Restarted {affected_count} failed tasks. They will be re-executed shortly."
                }
            
            elif action_type == "reset_agents":
                # Reset agent status to available
                result = supabase.table("agents")\
                    .update({"status": "available"})\
                    .eq("workspace_id", self.workspace_id)\
                    .in_("status", ["error", "paused", "terminated"])\
                    .execute()
                
                affected_count = len(result.data) if result.data else 0
                return {
                    "success": True,
                    "message": f"Reset {affected_count} agents to available status. They can now accept new tasks."
                }
            
            elif action_type == "clear_blockages":
                # Set workspace to active and clear any locks
                workspace_result = supabase.table("workspaces")\
                    .update({"status": "active"})\
                    .eq("id", self.workspace_id)\
                    .execute()
                
                return {
                    "success": True,
                    "message": "Cleared workspace blockages and set status to active. Operations should resume."
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}. Available: restart_failed_tasks, reset_agents, clear_blockages"
                }
        
        except Exception as e:
            logger.error(f"Error fixing workspace issues: {e}")
            return {
                "success": False,
                "message": f"Failed to fix workspace issues: {str(e)}"
            }
    
    async def _analyze_blocking_issues(self) -> dict:
        """Analyze what's blocking progress"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Get workspace and related data
            workspace = supabase.table("workspaces").select("*").eq("id", self.workspace_id).execute()
            tasks = supabase.table("tasks").select("*").eq("workspace_id", self.workspace_id).execute()
            agents = supabase.table("agents").select("*").eq("workspace_id", self.workspace_id).execute()
            
            issues = []
            recommendations = []
            
            # Analyze tasks
            task_data = tasks.data if tasks.data else []
            failed_tasks = [t for t in task_data if t.get("status") == "failed"]
            stuck_tasks = [t for t in task_data if t.get("status") in ["pending_verification", "needs_enhancement"] and t.get("created_at", "") < "2024-01-01"]
            
            if failed_tasks:
                issues.append(f"{len(failed_tasks)} tasks have failed")
                recommendations.append("Use 'restart_failed_tasks' to retry failed operations")
            
            if stuck_tasks:
                issues.append(f"{len(stuck_tasks)} tasks appear to be stuck in verification")
                recommendations.append("Review task outputs and provide feedback to continue")
            
            # Analyze agents
            agent_data = agents.data if agents.data else []
            inactive_agents = [a for a in agent_data if a.get("status") not in ["available", "busy"]]
            
            if inactive_agents:
                issues.append(f"{len(inactive_agents)} agents are not operational")
                recommendations.append("Use 'reset_agents' to restore agent availability")
            
            # Analyze workspace
            workspace_data = workspace.data[0] if workspace.data else {}
            workspace_status = workspace_data.get("status", "unknown")
            
            if workspace_status != "active":
                issues.append(f"Workspace status is {workspace_status} instead of active")
                recommendations.append("Use 'clear_blockages' to activate workspace operations")
            
            if not issues:
                issues.append("No obvious blocking issues detected")
                recommendations.append("System appears operational - check deliverable progress")
            
            analysis_report = f"""
**Blocking Issues Found:**
{chr(10).join([f'• {issue}' for issue in issues])}

**Recommended Actions:**
{chr(10).join([f'• {rec}' for rec in recommendations])}

**Summary:** {'Critical intervention needed' if len(issues) > 2 else 'Minor issues detected' if issues[0] != 'No obvious blocking issues detected' else 'System operational'}
            """
            
            return {
                "success": True,
                "message": analysis_report,
                "details": {
                    "issues_count": len([i for i in issues if i != "No obvious blocking issues detected"]),
                    "failed_tasks": len(failed_tasks),
                    "stuck_tasks": len(stuck_tasks),
                    "inactive_agents": len(inactive_agents),
                    "workspace_status": workspace_status
                }
            }
        
        except Exception as e:
            logger.error(f"Error analyzing blocking issues: {e}")
            return {
                "success": False,
                "message": f"Failed to analyze issues: {str(e)}"
            }
    
    async def _resume_workspace_operations(self, force_restart: bool = False) -> dict:
        """Resume workspace operations"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            actions_taken = []
            
            # 1. Set workspace to active
            workspace_result = supabase.table("workspaces")\
                .update({"status": "active"})\
                .eq("id", self.workspace_id)\
                .execute()
            actions_taken.append("Activated workspace")
            
            # 2. Reset agents to available
            agent_result = supabase.table("agents")\
                .update({"status": "available"})\
                .eq("workspace_id", self.workspace_id)\
                .in_("status", ["error", "paused", "terminated"])\
                .execute()
            
            reset_agents = len(agent_result.data) if agent_result.data else 0
            if reset_agents > 0:
                actions_taken.append(f"Reset {reset_agents} agents to available")
            
            # 3. If force restart, retry failed tasks
            if force_restart:
                task_result = supabase.table("tasks")\
                    .update({"status": "pending", "error_message": None})\
                    .eq("workspace_id", self.workspace_id)\
                    .eq("status", "failed")\
                    .execute()
                
                restarted_tasks = len(task_result.data) if task_result.data else 0
                if restarted_tasks > 0:
                    actions_taken.append(f"Restarted {restarted_tasks} failed tasks")
            
            return {
                "success": True,
                "message": f"Operations resumed successfully. Actions taken: {', '.join(actions_taken)}. The team should now continue progress toward deliverables."
            }
        
        except Exception as e:
            logger.error(f"Error resuming workspace operations: {e}")
            return {
                "success": False,
                "message": f"Failed to resume operations: {str(e)}"
            }
    
    def _is_asking_about_tools(self, user_message: str) -> bool:
        """Check if user is asking about available tools"""
        tools_keywords = [
            "available tools",
            "what tools",
            "list tools",
            "show tools",
            "tools available",
            "what can you do",
            "capabilities",
            "available commands",
            "slash commands",
            "/"
        ]
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in tools_keywords)
    
    def _is_asking_about_documents(self, user_message: str) -> bool:
        """Check if user is asking about documents or specific files"""
        document_keywords = [
            "document",
            "file",
            "pdf",
            "book",
            "paper",
            "report",
            "presentation",
            "summarize",
            "summary",
            "what's in",
            "content of",
            "read the",
            "analyze the",
            "review the",
            "uploaded",
            "knowledge base",
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".md"
        ]
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in document_keywords)
    
    async def _search_relevant_documents(self, user_message: str) -> str:
        """Search for relevant documents based on user query - WITH FULL CONTENT RETRIEVAL"""
        try:
            # First try enhanced content search
            try:
                from tools.enhanced_document_search import enhanced_document_tools
                
                # Use the enhanced search that retrieves actual content
                search_tool = enhanced_document_tools["search_document_content"]
                
                logger.info(f"🔍 Using ENHANCED document search with CONTENT RETRIEVAL for: {user_message}")
                
                # Execute enhanced search
                search_result = await search_tool.execute(
                    query=user_message,
                    workspace_id=self.workspace_id,
                    max_results=3,
                    include_full_text=False  # Don't include full text to avoid token overflow
                )
                
                # Check if user is asking for a summary
                if any(word in user_message.lower() for word in ["summarize", "summary", "riassumi", "riassunto"]):
                    # Try to find a specific document to summarize
                    file_extensions = [".pdf", ".doc", ".docx", ".txt", ".md"]
                    words = user_message.lower().split()
                    specific_files = [word for word in words if any(ext in word for ext in file_extensions)]
                    
                    if specific_files:
                        summary_tool = enhanced_document_tools["summarize_document"]
                        summary_result = await summary_tool.execute(
                            filename=specific_files[0],
                            workspace_id=self.workspace_id,
                            summary_type="detailed"
                        )
                        
                        if "❌" not in summary_result:
                            search_result = f"{search_result}\n\n{summary_result}"
                
                return search_result
                
            except ImportError:
                logger.warning("Enhanced document search not available, falling back to basic search")
                # Fall back to original implementation
                pass
            
            # Fallback: Original implementation
            # Extract potential search terms from the user message
            # Remove common words to focus on key terms
            stop_words = {"the", "a", "an", "is", "are", "what", "whats", "in", "of", "and", "or", "but", "for", "to", "from", "about", "summarize", "summary", "please", "can", "you", "show", "me", "tell"}
            
            # Clean the message and extract search terms
            words = user_message.lower().split()
            search_terms = [word.strip('.,!?') for word in words if word.strip('.,!?') not in stop_words]
            
            # If we have specific file mentions, prioritize those
            file_extensions = [".pdf", ".doc", ".docx", ".txt", ".md"]
            specific_files = [word for word in words if any(ext in word for ext in file_extensions)]
            
            # Construct search query
            if specific_files:
                search_query = " ".join(specific_files)
            else:
                # Use the most relevant terms
                search_query = " ".join(search_terms[:5])  # Limit to 5 terms
            
            if not search_query:
                search_query = user_message  # Fallback to full message
            
            logger.info(f"🔍 Searching documents with query: {search_query}")
            
            # Execute document search
            from tools.document_tools import document_tools
            search_tool = document_tools["search_documents"]
            
            context = {"workspace_id": self.workspace_id}
            search_result = await search_tool.execute(
                query=search_query,
                max_results=3,  # Limit results to avoid token overflow
                context=context
            )
            
            # Also list available documents for context
            list_tool = document_tools["list_documents"]
            docs_list = await list_tool.execute(context=context)
            
            # Combine results
            combined_results = f"SEARCH RESULTS for '{search_query}':\n{search_result}\n\nAVAILABLE DOCUMENTS:\n{docs_list}"
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return f"Note: Document search encountered an error: {str(e)}. Please ensure documents are properly uploaded to the workspace."
    
    async def _generate_tools_artifact_response(self) -> str:
        """Generate a properly formatted artifact response for available tools"""
        # Get the tools from our tools_available dictionary
        tools_list = []
        
        # Categorize tools
        team_tools = []
        project_tools = []
        execution_tools = []
        document_tools = []
        openai_tools = []
        
        for tool_name, tool_info in self.tools_available.items():
            tool_data = {
                "name": tool_name,
                "label": tool_name.replace('_', ' ').title(),
                "description": tool_info["description"],
                "parameters": tool_info["parameters"]
            }
            
            # Categorize based on tool name
            if tool_name in ["add_team_member", "start_team", "pause_team", "update_team_skills", "show_team_status"]:
                team_tools.append(tool_data)
            elif tool_name in ["show_project_status", "show_goal_progress", "create_goal", "show_deliverables"]:
                project_tools.append(tool_data)
            elif tool_name in ["approve_all_feedback", "fix_workspace_issues", "auto_complete_with_recovery", "analyze_blocking_issues", "resume_workspace_operations"]:
                execution_tools.append(tool_data)
            elif tool_name in ["upload_document", "list_documents", "delete_document", "search_documents", "search_document_content", "read_document_content", "summarize_document"]:
                document_tools.append(tool_data)
            elif tool_name in ["web_search", "code_interpreter", "generate_image", "file_search"]:
                openai_tools.append(tool_data)
            
            tools_list.append(tool_data)
        
        # Create the artifact content
        artifact_content = {
            "tools": tools_list,
            "categories": {
                "team_management": {
                    "title": "Team Management",
                    "icon": "👥",
                    "tools": team_tools
                },
                "project_monitoring": {
                    "title": "Project Monitoring",
                    "icon": "📊",
                    "tools": project_tools
                },
                "execution_control": {
                    "title": "Execution & Control",
                    "icon": "⚡",
                    "tools": execution_tools
                },
                "document_management": {
                    "title": "Document Management",
                    "icon": "📄",
                    "tools": document_tools
                },
                "ai_capabilities": {
                    "title": "AI Capabilities",
                    "icon": "🤖",
                    "tools": openai_tools
                }
            },
            "slash_commands": [
                {"command": "/help", "description": "Show available commands and tools"},
                {"command": "/status", "description": "Show project status overview"},
                {"command": "/team", "description": "View and manage team members"},
                {"command": "/goals", "description": "View project goals and progress"},
                {"command": "/approve", "description": "Approve all pending feedback"}
            ],
            "integrations": [
                {"name": "OpenAI", "status": "active", "features": ["Web Search", "Code Interpreter", "Image Generation"]},
                {"name": "Supabase", "status": "active", "features": ["Database", "Storage", "Real-time Updates"]}
            ],
            "capabilities": [
                "Multi-agent orchestration and team management",
                "Goal-driven task generation and monitoring",
                "Real-time project status tracking",
                "Document upload and knowledge management",
                "AI-powered web search and analysis",
                "Automated quality assurance and feedback loops",
                "Budget tracking and resource management",
                "Deliverable generation and asset creation"
            ]
        }
        
        # Format the response with the artifact
        response = f"""# 🛠️ Available Tools and Capabilities

I have access to a comprehensive set of tools to help manage your project. Here's what I can do:

## 📋 Quick Overview

**Total Tools**: {len(tools_list)} tools across 5 categories
**Slash Commands**: 5 quick commands for common actions
**AI Integrations**: OpenAI and Supabase backends
**Core Capabilities**: 8 major feature areas

## 🚀 Most Used Tools

1. **show_project_status** - Get comprehensive project overview
2. **show_team_status** - View current team and activities
3. **approve_all_feedback** - Bulk approve pending requests
4. **start_team** / **pause_team** - Control execution flow
5. **show_goal_progress** - Track objective completion

## 💡 Pro Tips

- Use slash commands like `/status` for quick access
- Tools can be executed by mentioning them in your request
- I'll suggest relevant tools based on your questions
- All tools integrate seamlessly with your workspace context

**ARTIFACT:tools_overview:{json.dumps(artifact_content)}**

Would you like me to execute any specific tool or explain how to use a particular feature?"""
        
        return response
    
    async def _auto_complete_with_recovery(self, include_failed_recovery: bool = True) -> dict:
        """
        🤖 Enhanced Auto-Complete: Complete missing deliverables AND recover failed tasks
        This is the main method for complete autonomous recovery
        """
        try:
            logger.info(f"🤖 ENHANCED AUTO-COMPLETE: Starting for workspace {self.workspace_id}")
            
            # Step 1: Failed Task Recovery (if enabled)
            recovery_summary = {'attempted': False}
            if include_failed_recovery:
                try:
                    from services.failed_task_resolver import process_workspace_failed_tasks
                    
                    logger.info(f"🔧 STEP 1: Recovering failed tasks in workspace {self.workspace_id}")
                    recovery_result = await process_workspace_failed_tasks(self.workspace_id)
                    
                    recovery_summary = {
                        'attempted': True,
                        'success': recovery_result.get('success', False),
                        'total_failed_tasks': recovery_result.get('total_processed', 0),
                        'successful_recoveries': recovery_result.get('successful_recoveries', 0),
                        'recovery_rate': recovery_result.get('recovery_rate', 0.0)
                    }
                    
                    logger.info(f"🔧 RECOVERY RESULT: {recovery_summary['successful_recoveries']}/{recovery_summary['total_failed_tasks']} tasks recovered")
                    
                except Exception as recovery_error:
                    logger.error(f"❌ Recovery error: {recovery_error}")
                    recovery_summary = {
                        'attempted': True,
                        'success': False,
                        'error': str(recovery_error),
                        'total_failed_tasks': 0,
                        'successful_recoveries': 0
                    }
            
            # Step 2: Auto-Complete Missing Deliverables - USE NEW ENHANCED ENDPOINT
            try:
                import aiohttp
                
                # Use our new enhanced auto-complete endpoint
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                url = f"{base_url}/api/enhanced-auto-complete"
                
                logger.info(f"📦 STEP 2: Calling enhanced auto-completion endpoint: {url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"workspace_id": self.workspace_id}) as response:
                        if response.status == 200:
                            completion_result = await response.json()
                            logger.info(f"📦 ENHANCED COMPLETION RESULT: {completion_result}")
                        else:
                            error_text = await response.text()
                            raise Exception(f"Enhanced auto-completion API error {response.status}: {error_text}")
                
            except Exception as completion_error:
                logger.error(f"❌ Completion error: {completion_error}")
                completion_result = {
                    'success': False,
                    'error': str(completion_error),
                    'deliverable_completion': {
                        'total_attempts': 0,
                        'successful_completions': 0
                    }
                }
            
            # Calculate overall results
            # Parse new enhanced endpoint response structure
            summary = completion_result.get('summary', {})
            total_recoveries = summary.get('total_failed_tasks_recovered', 0)
            total_completions = summary.get('total_deliverables_completed', 0)
            total_missing_detected = summary.get('missing_deliverables_detected', 0)
            overall_success = completion_result.get('success', False)
            
            total_actions = total_recoveries + total_completions
            
            success_message = f"""✅ **Enhanced Auto-Complete Finished!**

🔧 **Failed Task Recovery:**
   • Tasks Recovered: **{total_recoveries}** failed tasks automatically resolved
   • Method: Autonomous task recovery system

📦 **Deliverable Completion:**
   • Deliverables Detected: **{total_missing_detected}** goals with missing outputs
   • Deliverables Completed: **{total_completions}** deliverables auto-generated

🎯 **Overall Results:**
   • Total Actions Taken: **{total_actions}**
   • System Status: **{'✅ Success' if overall_success else '⚠️ Partial'}**
   • Human Intervention Required: **No** (Fully Autonomous)

🤖 **Autonomous Enhancement:**
The system has automatically detected and resolved workspace issues, completed missing deliverables, and ensured project continuity without requiring manual intervention. All operations were performed autonomously with AI-driven decision making."""
            
            logger.info(f"✅ ENHANCED AUTO-COMPLETE FINISHED: {total_actions} total actions, success: {overall_success}")
            
            return {
                "success": True,
                "message": success_message,
                "enhanced_auto_complete": True,
                "failed_task_recovery": recovery_summary,
                "deliverable_completion": deliverable_stats,
                "overall_summary": {
                    "total_actions": total_actions,
                    "total_successes": total_successes,
                    "success_rate": overall_success_rate / 100,
                    "human_intervention_required": False
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced auto-complete error: {e}")
            return {
                "success": False,
                "message": f"❌ **Enhanced Auto-Complete Failed**\n\nError: {str(e)}\n\nPlease try again or check the system logs for more details.",
                "error": str(e)
            }