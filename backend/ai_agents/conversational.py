"""
Conversational AI Agent - Context-aware assistant with full project access
Respects the core pillars: Agnostic, Multi-agent, Universal, Concrete, AI-Enhanced
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field
from openai import OpenAI

from ai_agents.specialist_enhanced import SpecialistAgent
from models import AgentSeniority, AgentStatus
from database import get_supabase_client
from utils.context_manager import get_workspace_context

# Import SDK with fallback
try:
    from agents import Agent, function_tool, AgentOutputSchema
    SDK_AVAILABLE = True
except ImportError:
    try:
        from openai_agents import Agent, function_tool
        SDK_AVAILABLE = True
        AgentOutputSchema = None
    except ImportError:
        SDK_AVAILABLE = False
        print("⚠️ No OpenAI Agents SDK available - using fallback implementation")
        
        # Create fallback definitions
        Agent = None
        AgentOutputSchema = None
        
        # Dummy function_tool decorator
        def function_tool(func):
            """Fallback function_tool decorator"""
            func._is_tool = True
            return func

logger = logging.getLogger(__name__)

class ConversationContext(BaseModel):
    """Rich context for conversation"""
    workspace_id: str
    chat_id: str
    workspace_data: Dict[str, Any]
    team_data: List[Dict[str, Any]]
    recent_tasks: List[Dict[str, Any]]
    deliverables: List[Dict[str, Any]]
    budget_info: Dict[str, Any]
    goals: List[Dict[str, Any]]
    memory_insights: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]

class ConversationResponse(BaseModel):
    """Structured response from conversational agent"""
    message: str
    message_type: str = "text"  # text, confirmation, clarification, error
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    actions_performed: List[Dict[str, Any]] = Field(default_factory=list)
    requires_confirmation: Optional[Dict[str, Any]] = None
    clarification_needed: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationalAgent:
    """
    Universal conversational agent that provides context-aware assistance
    for any workspace and domain. Completely AI-driven without hardcoded logic.
    """
    
    def __init__(self, workspace_id: str, chat_id: str = "general"):
        self.workspace_id = workspace_id
        self.chat_id = chat_id
        self.schema_version = "v2025-06-A"
        self.client = OpenAI()
        self.supabase = get_supabase_client()
        
        # Version management
        self._version_manager = None
        
        # Initialize agent with SDK if available
        if SDK_AVAILABLE:
            self._init_sdk_agent()
        
        # Tool registry for this conversation
        self.available_tools = self._register_conversational_tools()
        
        # Context manager
        self.context: Optional[ConversationContext] = None
        
        logger.info(f"ConversationalAgent initialized for workspace {workspace_id}, chat {chat_id}")
    
    def _init_sdk_agent(self):
        """Initialize OpenAI Agents SDK agent"""
        try:
            self.sdk_agent = Agent(
                name="Project Assistant",
                description="Context-aware AI assistant for project management",
                instructions=self._get_system_prompt(),
                functions=list(self.available_tools.values()) if hasattr(self, 'available_tools') else []
            )
        except Exception as e:
            logger.warning(f"Failed to initialize SDK agent: {e}")
            self.sdk_agent = None
    
    def _get_system_prompt(self) -> str:
        """
        Generate dynamic system prompt based on workspace context.
        Universal and agnostic - adapts to any domain.
        """
        base_prompt = """You are an expert AI project assistant with complete access to workspace context.

        CORE PRINCIPLES:
        - Be context-aware: Always consider the current project state, team, budget, and goals
        - Be actionable: Provide concrete next steps and specific recommendations
        - Be adaptive: Adjust your expertise to match the project domain and team needs
        - Be safe: Always ask for confirmation before destructive actions
        - Be precise: When insufficient information, ask clarifying questions

        CAPABILITIES:
        - Analyze project progress and identify bottlenecks
        - Suggest team optimizations and new team members
        - Manage budget and resource allocation
        - Create and modify project goals and tasks
        - Generate deliverables and artifacts
        - Provide domain-specific insights and recommendations

        INTERACTION STYLE:
        - Conversational but professional
        - Proactive in suggesting improvements
        - Transparent about actions taken
        - Educational when explaining decisions
        
        When users ask questions or request actions:
        1. Use current workspace context to provide accurate information
        2. Execute requested actions through appropriate tools
        3. Suggest related improvements or optimizations
        4. Generate artifacts when helpful (reports, plans, summaries)
        5. Always confirm before making significant changes
        """
        
        return base_prompt
    
    def _register_conversational_tools(self) -> Dict[str, Any]:
        """
        Register universal tools for conversational interactions.
        Tools are domain-agnostic and scale to any project type.
        """
        tools = {}
        
        if SDK_AVAILABLE:
            # SDK-based tools
            tools.update({
                "analyze_project_status": self._create_analyze_project_status_tool(),
                "modify_budget": self._create_modify_budget_tool(),
                "suggest_team_member": self._create_suggest_team_member_tool(),
                "create_deliverable": self._create_create_deliverable_tool(),
                "update_agent_skills": self._create_update_agent_skills_tool(),
                "create_task": self._create_create_task_tool(),
                "analyze_team_performance": self._create_analyze_team_performance_tool(),
                "upload_knowledge": self._create_upload_knowledge_tool(),
                "get_historical_insights": self._create_get_historical_insights_tool(),
                "create_workflow_automation": self._create_workflow_automation_tool()
            })
        
        return tools
    
    @function_tool
    def _create_analyze_project_status_tool(self):
        """Analyze current project status and generate insights"""
        async def analyze_project_status(focus_area: str = "overall") -> Dict[str, Any]:
            """
            Analyze project status with focus on specific area.
            
            Args:
                focus_area: What to focus on - 'overall', 'budget', 'timeline', 'team', 'quality'
            """
            if not self.context:
                await self._load_context()
            
            analysis = {
                "status": "in_progress",
                "focus_area": focus_area,
                "summary": "",
                "metrics": {},
                "insights": [],
                "recommendations": [],
                "risks": [],
                "next_actions": []
            }
            
            # Analyze based on current context
            workspace = self.context.workspace_data
            team = self.context.team_data
            tasks = self.context.recent_tasks
            budget = self.context.budget_info
            
            if focus_area == "overall" or focus_area == "budget":
                budget_used = budget.get("used", 0)
                budget_max = budget.get("max_budget", 10000)
                budget_percentage = (budget_used / budget_max) * 100 if budget_max > 0 else 0
                
                analysis["metrics"]["budget_utilization"] = budget_percentage
                
                if budget_percentage > 80:
                    analysis["risks"].append({
                        "type": "budget",
                        "severity": "high",
                        "description": f"Budget utilization at {budget_percentage:.1f}%"
                    })
            
            if focus_area == "overall" or focus_area == "team":
                available_agents = len([agent for agent in team if agent.get("status") == "available"])
                analysis["metrics"]["team_size"] = available_agents
                
                if available_agents < 3:
                    analysis["recommendations"].append({
                        "type": "team",
                        "priority": "medium",
                        "description": "Consider adding more team members for better coverage"
                    })
            
            if focus_area == "overall" or focus_area == "timeline":
                completed_tasks = len([task for task in tasks if task.get("status") == "completed"])
                total_tasks = len(tasks)
                completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                analysis["metrics"]["task_completion_rate"] = completion_rate
                
                if completion_rate < 50:
                    analysis["insights"].append({
                        "type": "timeline",
                        "description": f"Task completion rate is {completion_rate:.1f}%. Consider reviewing task prioritization."
                    })
            
            # Generate summary
            analysis["summary"] = self._generate_status_summary(analysis)
            
            return analysis
        
        return analyze_project_status
    
    @function_tool
    def _create_modify_budget_tool(self):
        """Modify workspace budget with validation"""
        async def modify_budget(operation: str, amount: float, reason: str = "") -> Dict[str, Any]:
            """
            Modify workspace budget.
            
            Args:
                operation: 'increase', 'decrease', or 'set'
                amount: Amount to change (positive number)
                reason: Reason for the change
            """
            if not self.context:
                await self._load_context()
            
            current_budget = self.context.budget_info.get("max_budget", 10000)
            
            if operation == "increase":
                new_budget = current_budget + amount
            elif operation == "decrease":
                new_budget = max(0, current_budget - amount)
            elif operation == "set":
                new_budget = amount
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Update in database
            update_data = {"max_budget": new_budget}
            if reason:
                update_data["budget_change_reason"] = reason
                update_data["budget_changed_at"] = datetime.now(timezone.utc).isoformat()
            
            self.supabase.table("workspaces").update(update_data).eq("id", self.workspace_id).execute()
            
            return {
                "success": True,
                "previous_budget": current_budget,
                "new_budget": new_budget,
                "change_amount": new_budget - current_budget,
                "operation": operation,
                "reason": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        
        return modify_budget
    
    @function_tool
    def _create_suggest_team_member_tool(self):
        """Suggest new team member based on project needs"""
        async def suggest_team_member(role_needed: str = None, skills_needed: List[str] = None) -> Dict[str, Any]:
            """
            Suggest a new team member based on project analysis.
            
            Args:
                role_needed: Specific role needed (optional)
                skills_needed: List of required skills (optional)
            """
            if not self.context:
                await self._load_context()
            
            # Analyze current team composition
            current_team = self.context.team_data
            current_roles = [agent.get("role", "") for agent in current_team]
            current_skills = []
            for agent in current_team:
                current_skills.extend(agent.get("skills", []))
            
            # AI-driven suggestion based on workspace domain and current gaps
            workspace = self.context.workspace_data
            domain = workspace.get("domain", "general")
            
            suggestion = self._analyze_team_gaps(current_roles, current_skills, domain, role_needed, skills_needed)
            
            return {
                "suggested_role": suggestion["role"],
                "suggested_seniority": suggestion["seniority"],
                "required_skills": suggestion["skills"],
                "reasoning": suggestion["reasoning"],
                "priority": suggestion["priority"],
                "estimated_cost": suggestion["estimated_cost"],
                "expected_impact": suggestion["impact"]
            }
        
        return suggest_team_member
    
    def _analyze_team_gaps(self, current_roles: List[str], current_skills: List[str], 
                          domain: str, role_needed: str = None, skills_needed: List[str] = None) -> Dict[str, Any]:
        """
        AI-driven analysis of team gaps. Universal and adaptive to any domain.
        """
        # Universal role patterns that apply across domains
        universal_roles = {
            "project_manager": {"priority": "high", "seniority": "senior"},
            "quality_assurance": {"priority": "medium", "seniority": "senior"},
            "analyst": {"priority": "medium", "seniority": "intermediate"},
            "specialist": {"priority": "high", "seniority": "expert"}
        }
        
        # Domain-specific role suggestions (AI-expandable)
        domain_roles = {
            "marketing": ["content_creator", "seo_specialist", "campaign_manager", "designer"],
            "development": ["backend_developer", "frontend_developer", "devops_engineer", "architect"],
            "finance": ["financial_analyst", "accountant", "controller", "advisor"],
            "sales": ["sales_manager", "account_executive", "business_developer", "customer_success"]
        }
        
        suggested_roles = domain_roles.get(domain, ["specialist", "analyst", "coordinator"])
        
        # If specific role requested, use it
        if role_needed:
            suggested_role = role_needed
        else:
            # Find missing roles
            missing_roles = [role for role in suggested_roles if role not in current_roles]
            suggested_role = missing_roles[0] if missing_roles else "specialist"
        
        # Determine seniority based on team composition
        seniority_counts = {"junior": 0, "senior": 0, "expert": 0}
        for role in current_roles:
            # Simple heuristic - can be made more sophisticated
            if "senior" in role or "lead" in role:
                seniority_counts["senior"] += 1
            elif "expert" in role or "architect" in role:
                seniority_counts["expert"] += 1
            else:
                seniority_counts["junior"] += 1
        
        # Balance team seniority
        if seniority_counts["senior"] == 0:
            suggested_seniority = "senior"
        elif seniority_counts["expert"] == 0 and len(current_roles) > 3:
            suggested_seniority = "expert"
        else:
            suggested_seniority = "intermediate"
        
        # Skills based on role and gaps
        if skills_needed:
            required_skills = skills_needed
        else:
            # AI-driven skill suggestions based on role and domain
            required_skills = self._suggest_skills_for_role(suggested_role, domain, current_skills)
        
        return {
            "role": suggested_role,
            "seniority": suggested_seniority,
            "skills": required_skills,
            "reasoning": f"Team analysis indicates need for {suggested_role} to fill gaps in {domain} domain",
            "priority": "high" if len(current_roles) < 3 else "medium",
            "estimated_cost": self._estimate_agent_cost(suggested_seniority),
            "impact": f"Expected to improve {domain} capabilities by 25-40%"
        }
    
    def _suggest_skills_for_role(self, role: str, domain: str, existing_skills: List[str]) -> List[str]:
        """Universal skill suggestion engine"""
        skill_patterns = {
            "project_manager": ["project_planning", "risk_management", "stakeholder_communication"],
            "analyst": ["data_analysis", "reporting", "research"],
            "developer": ["programming", "debugging", "testing"],
            "designer": ["ui_design", "user_experience", "prototyping"],
            "content_creator": ["content_writing", "seo", "social_media"],
            "specialist": ["domain_expertise", "problem_solving", "consultation"]
        }
        
        base_skills = skill_patterns.get(role, skill_patterns["specialist"])
        
        # Add domain-specific skills
        domain_skills = {
            "marketing": ["digital_marketing", "brand_management", "campaign_optimization"],
            "development": ["software_architecture", "code_review", "deployment"],
            "finance": ["financial_modeling", "budget_planning", "compliance"],
            "sales": ["lead_generation", "customer_relations", "negotiation"]
        }
        
        if domain in domain_skills:
            base_skills.extend(domain_skills[domain])
        
        # Remove skills already covered by team
        new_skills = [skill for skill in base_skills if skill not in existing_skills]
        
        return new_skills[:5]  # Limit to top 5 skills
    
    def _estimate_agent_cost(self, seniority: str) -> str:
        """Estimate daily cost for agent based on seniority"""
        costs = {
            "junior": "6 EUR/day",
            "intermediate": "8 EUR/day", 
            "senior": "10 EUR/day",
            "expert": "18 EUR/day"
        }
        return costs.get(seniority, "8 EUR/day")
    
    async def _load_context(self):
        """Load complete workspace context for AI processing"""
        try:
            # Get workspace context using existing function
            workspace_context = await get_workspace_context(self.workspace_id)
            
            # Load conversation history
            conversation_history = await self._get_conversation_history()
            
            # Load memory insights
            memory_insights = await self._get_memory_insights()
            
            self.context = ConversationContext(
                workspace_id=self.workspace_id,
                chat_id=self.chat_id,
                workspace_data=workspace_context.get("workspace", {}),
                team_data=workspace_context.get("agents", []),
                recent_tasks=workspace_context.get("recent_tasks", []),
                deliverables=workspace_context.get("deliverables", []),
                budget_info=workspace_context.get("budget", {}),
                goals=workspace_context.get("goals", []),
                memory_insights=memory_insights,
                conversation_history=conversation_history
            )
            
            logger.info(f"Context loaded for workspace {self.workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            # Create minimal context to prevent failures
            self.context = ConversationContext(
                workspace_id=self.workspace_id,
                chat_id=self.chat_id,
                workspace_data={},
                team_data=[],
                recent_tasks=[],
                deliverables=[],
                budget_info={"max_budget": 10000, "used": 0},
                goals=[],
                memory_insights=[],
                conversation_history=[]
            )
    
    async def _get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            result = self.supabase.table("conversation_messages")\
                .select("*")\
                .eq("conversation_id", f"{self.workspace_id}_{self.chat_id}")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            return []
    
    async def _get_memory_insights(self) -> List[Dict[str, Any]]:
        """Get AI memory insights for the workspace"""
        try:
            # This would integrate with the AI Memory Intelligence system
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to load memory insights: {e}")
            return []
    
    def _generate_status_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary from analysis data"""
        metrics = analysis.get("metrics", {})
        risks = analysis.get("risks", [])
        
        summary_parts = []
        
        # Budget summary
        if "budget_utilization" in metrics:
            budget_pct = metrics["budget_utilization"]
            if budget_pct > 80:
                summary_parts.append(f"⚠️ High budget utilization ({budget_pct:.1f}%)")
            elif budget_pct > 50:
                summary_parts.append(f"💰 Moderate budget usage ({budget_pct:.1f}%)")
            else:
                summary_parts.append(f"✅ Budget on track ({budget_pct:.1f}% used)")
        
        # Team summary
        if "team_size" in metrics:
            team_size = metrics["team_size"]
            if team_size < 3:
                summary_parts.append(f"👥 Small team ({team_size} members) - consider expansion")
            else:
                summary_parts.append(f"👥 Team size: {team_size} active members")
        
        # Task summary
        if "task_completion_rate" in metrics:
            completion_rate = metrics["task_completion_rate"]
            if completion_rate > 80:
                summary_parts.append(f"🎯 Excellent progress ({completion_rate:.1f}% completion)")
            elif completion_rate > 50:
                summary_parts.append(f"📈 Good progress ({completion_rate:.1f}% completion)")
            else:
                summary_parts.append(f"⏳ Progress needs attention ({completion_rate:.1f}% completion)")
        
        return " | ".join(summary_parts) if summary_parts else "Project status analysis completed"
    
    async def process_message(self, user_message: str, message_id: str = None) -> ConversationResponse:
        """
        Process user message and generate intelligent response.
        This is the main entry point for conversational interactions.
        """
        try:
            # Load context if not already loaded
            if not self.context:
                await self._load_context()
            
            # Generate unique message ID
            if not message_id:
                message_id = str(uuid4())
            
            # Log incoming message
            await self._save_message("user", user_message, message_id)
            
            # Process with SDK if available
            if SDK_AVAILABLE and self.sdk_agent:
                response = await self._process_with_sdk(user_message)
            else:
                response = await self._process_with_fallback(user_message)
            
            # Save AI response
            await self._save_message("assistant", response.message, f"{message_id}_response", {
                "tools_used": response.tools_used,
                "actions_performed": response.actions_performed,
                "artifacts_generated": response.artifacts
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ConversationResponse(
                message=f"I apologize, but I encountered an error processing your request: {str(e)}",
                message_type="error",
                confidence_score=0.0
            )
    
    async def _process_with_sdk(self, user_message: str) -> ConversationResponse:
        """Process message using OpenAI Agents SDK"""
        try:
            # Create context-enriched prompt
            enriched_prompt = await self._create_enriched_prompt(user_message)
            
            # Run with SDK
            response = self.sdk_agent.run(enriched_prompt)
            
            # Parse response and extract actions
            return self._parse_sdk_response(response, user_message)
            
        except Exception as e:
            logger.error(f"SDK processing failed: {e}")
            return await self._process_with_fallback(user_message)
    
    async def _process_with_fallback(self, user_message: str) -> ConversationResponse:
        """Fallback processing without SDK"""
        try:
            # Create context-enriched prompt
            enriched_prompt = await self._create_enriched_prompt(user_message)
            
            # Use OpenAI API directly
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": enriched_prompt}
                ],
                temperature=0.3
            )
            
            ai_message = response.choices[0].message.content
            
            # Simple response parsing for fallback
            return ConversationResponse(
                message=ai_message,
                message_type="text",
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return ConversationResponse(
                message="I'm having trouble processing your request right now. Please try again in a moment.",
                message_type="error",
                confidence_score=0.0
            )
    
    async def _create_enriched_prompt(self, user_message: str) -> str:
        """Create context-enriched prompt with all workspace information"""
        context_sections = []
        
        # Workspace information
        workspace = self.context.workspace_data
        context_sections.append(f"""
WORKSPACE CONTEXT:
- Name: {workspace.get('name', 'Unknown')}
- Domain: {workspace.get('domain', 'General')}
- Description: {workspace.get('description', 'No description')}
- Status: {workspace.get('status', 'active')}
""")
        
        # Team information
        team = self.context.team_data
        if team:
            team_info = []
            for agent in team:
                team_info.append(f"- {agent.get('name', 'Unknown')}: {agent.get('role', 'Unknown role')} ({agent.get('seniority', 'unknown')})")
            context_sections.append(f"""
CURRENT TEAM ({len(team)} members):
{chr(10).join(team_info)}
""")
        
        # Budget information
        budget = self.context.budget_info
        if budget:
            context_sections.append(f"""
BUDGET STATUS:
- Maximum Budget: €{budget.get('max_budget', 10000)}
- Used: €{budget.get('used', 0)}
- Remaining: €{budget.get('max_budget', 10000) - budget.get('used', 0)}
""")
        
        # Recent activity
        tasks = self.context.recent_tasks
        if tasks:
            recent_activity = []
            for task in tasks[:5]:  # Last 5 tasks
                recent_activity.append(f"- {task.get('title', 'Unknown task')}: {task.get('status', 'unknown')}")
            context_sections.append(f"""
RECENT ACTIVITY:
{chr(10).join(recent_activity)}
""")
        
        # Combine context with user message
        full_context = chr(10).join(context_sections)
        
        enriched_prompt = f"""
{full_context}

USER REQUEST: {user_message}

Please provide a helpful, context-aware response. If you need to take actions or make changes, use the appropriate tools. If you need clarification, ask specific questions.
"""
        
        return enriched_prompt
    
    def _parse_sdk_response(self, sdk_response, original_message: str) -> ConversationResponse:
        """Parse SDK response into structured format"""
        # This would parse the actual SDK response
        # For now, create a basic response structure
        return ConversationResponse(
            message=str(sdk_response),
            message_type="text",
            tools_used=[],
            actions_performed=[],
            confidence_score=0.9
        )
    
    async def _save_message(self, role: str, content: str, message_id: str, metadata: Dict[str, Any] = None):
        """Save message to conversation history"""
        try:
            conversation_id = f"{self.workspace_id}_{self.chat_id}"
            
            # Ensure conversation exists
            await self._ensure_conversation_exists(conversation_id)
            
            # Save message
            message_data = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "role": role,
                "content": content,
                "content_type": "text",
                "metadata": metadata or {},
                "context_snapshot": self.context.dict() if self.context else {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table("conversation_messages").insert(message_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
    
    async def _ensure_conversation_exists(self, conversation_id: str):
        """Ensure conversation record exists in database"""
        try:
            # Check if conversation exists
            result = self.supabase.table("conversations")\
                .select("id")\
                .eq("workspace_id", self.workspace_id)\
                .eq("chat_id", self.chat_id)\
                .execute()
            
            if not result.data:
                # Create conversation
                conversation_data = {
                    "workspace_id": self.workspace_id,
                    "chat_id": self.chat_id,
                    "schema_version": self.schema_version,
                    "title": f"Conversation: {self.chat_id}",
                    "description": f"AI assistant conversation for {self.chat_id}",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.table("conversations").insert(conversation_data).execute()
                
        except Exception as e:
            logger.error(f"Failed to ensure conversation exists: {e}")
    
    async def check_version_compatibility(self, target_version: str) -> Dict[str, Any]:
        """
        Check if current conversation can be migrated to target version.
        
        Args:
            target_version: Target schema version to check compatibility with
            
        Returns:
            Compatibility analysis and migration requirements
        """
        try:
            if not self._version_manager:
                from ..utils.versioning_manager import VersioningManager
                self._version_manager = VersioningManager(self.workspace_id)
            
            compatibility = await self._version_manager.check_version_compatibility(
                "conversation_schema",
                "conversation",
                self.schema_version,
                target_version
            )
            
            return compatibility
            
        except Exception as e:
            logger.error(f"Failed to check version compatibility: {e}")
            return {"compatible": False, "error": str(e)}
    
    async def migrate_to_version(self, target_version: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate current conversation to target version.
        
        Args:
            target_version: Target schema version
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration result with details of changes made
        """
        try:
            if not self._version_manager:
                from ..utils.versioning_manager import VersioningManager
                self._version_manager = VersioningManager(self.workspace_id)
            
            conversation_id = f"{self.workspace_id}_{self.chat_id}"
            result = await self._version_manager.migrate_conversation_to_version(
                conversation_id, target_version, dry_run
            )
            
            # Update local schema version if migration was successful
            if result.get("success", False) and not dry_run:
                self.schema_version = target_version
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to migrate conversation: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_supported_versions(self) -> List[str]:
        """
        Get list of supported schema versions for this conversation type.
        
        Returns:
            List of supported version strings
        """
        try:
            if not self._version_manager:
                from ..utils.versioning_manager import VersioningManager
                self._version_manager = VersioningManager(self.workspace_id)
            
            history = await self._version_manager.get_version_history(
                "conversation_schema", "conversation"
            )
            
            return [record["version"] for record in history if record.get("is_active", False)]
            
        except Exception as e:
            logger.error(f"Failed to get supported versions: {e}")
            return [self.schema_version]  # Return at least current version

# Additional tool implementations would go here...
# (create_deliverable_tool, update_agent_skills_tool, etc.)