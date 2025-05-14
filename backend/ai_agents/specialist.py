import logging
import os
from typing import List, Dict, Any, Optional, Union, Literal, TypeVar, Generic, Type
from uuid import UUID
import json

# Importazione dal pacchetto installato
from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool
from agents import Handoff, handoff, WebSearchTool, FileSearchTool
from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput
from agents import TResponseInputItem, RunContextWrapper
from agents import trace, custom_span, gen_trace_id
from agents.exceptions import MaxTurnsExceeded, AgentsException, ModelBehaviorError
from agents.extensions import handoff_filters
from agents.extensions.handoff_filters import HandoffInputData
from pydantic import BaseModel, Field

# Context type variable for generic typing
T = TypeVar('T')

from models import (
    Agent as AgentModel,
    AgentStatus,
    AgentHealth,
    HealthStatus,
    Task,
    TaskStatus
)
from database import update_agent_status, update_task_status, create_task, list_agents

logger = logging.getLogger(__name__)

# ==============================================================================
# OUTPUT STRUTTURATI
# ==============================================================================

class TaskExecutionOutput(BaseModel):
    """Output strutturato per l'esecuzione di task"""
    task_id: str
    status: Literal["completed", "failed", "requires_handoff"]
    summary: str
    detailed_results: Dict[str, Any]
    next_steps: Optional[List[str]] = None
    suggested_handoff: Optional[str] = None
    resources_consumed: Optional[Dict[str, Union[int, float]]] = None

class CapabilityVerificationOutput(BaseModel):
    """Output strutturato per la verifica delle capacità"""
    verification_status: Literal["passed", "failed"]
    available_tools: List[str]
    missing_requirements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class ToolCreationOutput(BaseModel):
    """Output strutturato per la creazione di tool"""
    success: bool
    tool_name: str
    tool_id: Optional[str] = None
    error_message: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None

class TaskCreationOutput(BaseModel):
    """Output strutturato per la creazione di task"""
    success: bool
    task_id: Optional[str] = None
    task_name: str
    assigned_agent: Optional[str] = None
    error_message: Optional[str] = None

class HandoffRequest(BaseModel):
    """Richiesta di handoff strutturata"""
    target_agent_role: str
    context: str
    priority: Literal["low", "medium", "high"] = "medium"
    expected_output: Optional[str] = None

class ConversationSummary(BaseModel):
    """Structured summary for conversation optimization"""
    key_points: List[str]
    user_requests: List[str]
    current_status: str
    relevant_context: Dict[str, Any]

# ==============================================================================
# HANDOFF DATA MODELS
# ==============================================================================

class EscalationData(BaseModel):
    reason: str = Field(..., description="Why escalation is needed")
    context: str = Field(..., description="Context and work done so far")
    priority: str = Field(..., description="Priority level: low, medium, high") 
    task_id: Optional[str] = Field(None, description="Current task ID")

class CompletionReport(BaseModel):
    task_summary: str = Field(..., description="Summary of completed work")
    next_steps: Optional[List[str]] = Field(None, description="Recommended next steps")
    recommendations: Optional[str] = Field(None, description="Additional recommendations")
    requires_followup: bool = Field(..., description="Whether follow-up is needed")
    handoff_target: Optional[str] = Field(None, description="Specific role to hand off to")

class DelegationData(BaseModel):
    target_role: str = Field(..., description="Role of the target specialist")
    task_description: str = Field(..., description="Description of work to delegate")
    context: str = Field(..., description="Context and background information")
    priority: str = Field(..., description="Priority level") 
    deadline: Optional[str] = Field(None, description="Deadline if any")
    expected_output: Optional[str] = Field(None, description="What kind of output is expected")
    
# ==============================================================================
# GUARDRAIL
# ==============================================================================

class BudgetMonitoringData(BaseModel):
    """Dati per il monitoraggio del budget"""
    estimated_cost: float
    budget_warning_threshold: float

@input_guardrail
async def budget_monitoring_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Guardrail per monitorare l'uso del budget"""
    try:
        # Stima il costo basato sulla lunghezza dell'input
        input_text = input if isinstance(input, str) else str(input)
        estimated_tokens = len(input_text.split()) * 1.3  # Stima approssimativa
        estimated_cost = estimated_tokens * 0.00003  # Costo per token (esempio)
        
        # Controlla se supera la soglia
        budget_limit = 10.0  # EUR - dovrebbe essere configurabile
        warning_threshold = budget_limit * 0.8
        
        return GuardrailFunctionOutput(
            output_info={
                "estimated_cost": estimated_cost,
                "budget_usage": (estimated_cost / budget_limit) * 100
            },
            tripwire_triggered=estimated_cost > warning_threshold
        )
    except Exception as e:
        logger.error(f"Error in budget guardrail: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False
        )

@output_guardrail
async def quality_assurance_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: Any
) -> GuardrailFunctionOutput:
    """Guardrail per verifica qualità output"""
    try:
        # Verifica la qualità dell'output
        quality_score = 1.0
        issues = []
        
        if hasattr(output, 'status') and output.status == "failed":
            quality_score -= 0.5
            issues.append("Task marked as failed")
        
        if hasattr(output, 'summary') and len(output.summary) < 20:
            quality_score -= 0.2
            issues.append("Summary too short")
        
        return GuardrailFunctionOutput(
            output_info={
                "quality_score": quality_score,
                "issues_found": issues
            },
            tripwire_triggered=quality_score < 0.6
        )
    except Exception as e:
        logger.error(f"Error in quality guardrail: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False
        )

# ==============================================================================
# CONVERSATION HISTORY OPTIMIZATION WITH AI
# ==============================================================================

class ConversationOptimizer:
    """Optimize conversation history using AI for better handoff performance"""
    
    def __init__(self):
        self.summarizer_agent = None
        
    async def _get_summarizer_agent(self):
        """Get or create the conversation summarizer agent"""
        if self.summarizer_agent is None:
            self.summarizer_agent = OpenAIAgent(
                name="ConversationSummarizer",
                instructions="""You are an expert at summarizing conversations for AI handoffs.
                Extract key points, user requests, current status, and relevant context.
                Focus on information needed for the next agent to continue effectively.""",
                model="gpt-4.1-nano",  # Use fast, cheap model for summaries
                output_type=ConversationSummary
            )
        return self.summarizer_agent
        
    async def optimize_with_ai_summary(self, conversation_history):
        """Use AI to create optimized conversation summary"""
        if len(conversation_history) <= 3:
            return conversation_history
            
        try:
            # Convert conversation to text
            text_history = self._history_to_text(conversation_history)
            
            # Get summary
            summarizer = await self._get_summarizer_agent()
            result = await Runner.run(
                summarizer,
                f"Summarize this conversation for handoff:\n\n{text_history}",
                max_turns=1
            )
            
            summary = result.final_output
            
            # Create optimized history with summary
            optimized_history = [
                {"role": "system", "content": f"""Previous conversation summary:
Key points: {'; '.join(summary.key_points)}
User requests: {'; '.join(summary.user_requests)}
Current status: {summary.current_status}
Relevant context: {summary.relevant_context}
"""},
                # Keep the last 2 messages for immediate context
                *conversation_history[-2:]
            ]
            
            return optimized_history
            
        except Exception as e:
            logger.warning(f"AI summarization failed, using basic optimization: {e}")
            # Fallback to basic optimization
            return conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    
    def _history_to_text(self, history):
        """Convert conversation history to text for summarization"""
        text_parts = []
        for msg in history:
            if isinstance(msg, dict):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                text_parts.append(f"{role.upper()}: {content}")
            else:
                text_parts.append(str(msg))
        return "\n".join(text_parts)

# ==============================================================================
# SPECIALIST AGENT
# ==============================================================================

class SpecialistAgent(Generic[T]):
    """Advanced Specialist Agent with native handoffs, context management and tracing"""
    
    def __init__(self, agent_data: AgentModel, context_type: Optional[Type[T]] = None):
        """
        Initialize a specialist agent with its configuration.
        
        Args:
            agent_data: The agent configuration from the database
            context_type: Optional type for context management
        """
        self.agent_data = agent_data
        self.context_type = context_type or dict
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize conversation optimizer
        self.conversation_optimizer = ConversationOptimizer()
        
        # Updated mapping with latest 4.1 models (officially released)
        self.seniority_model_map = {
            "junior": "gpt-4.1-nano",     # Fastest and cheapest: $0.10 input, $0.40 output
            "senior": "gpt-4.1-mini",     # Bilanciato: $0.40 input, $1.60 output  
            "expert": "gpt-4.1"           # Migliore: $2.00 input, $8.00 output
        }
        
        # Initialize tools based on agent configuration
        self.tools = self._initialize_tools()
        
        # Initialize handoffs BEFORE creating the agent
        self.handoffs = self._initialize_handoffs()
        
        # Create OpenAI Agent
        self.agent = self._create_agent()
    
def _initialize_tools(self) -> List[Any]:
    """Initialize tools based on agent configuration"""
    tools = [
        # automation di base
        self._create_auto_task_tool(),
        self._create_request_handoff_tool(),
        self._create_log_execution_tool(),
        self._create_update_health_status_tool(),
        self._create_report_progress_tool(),
    ]

    # tool "nativi" in base a self.agent_data.tools (impostati dal Director)
    if self.agent_data.tools:
        for cfg in self.agent_data.tools:
            if not isinstance(cfg, dict):
                continue
            t = cfg.get("type", "")
            if t == "web_search":
                tools.append(WebSearchTool(search_context_size="medium"))
            elif t == "file_search":
                # FIX: Non passare vector_store_ids se è None o vuoto
                vector_store_ids = getattr(self.agent_data, "vector_store_ids", None)
                tool_params = {
                    "max_num_results": 5,
                    "include_search_results": True,
                }
                # Solo aggiungere vector_store_ids se non è None e non è vuoto
                if vector_store_ids and len(vector_store_ids) > 0:
                    tool_params["vector_store_ids"] = vector_store_ids
                
                tools.append(FileSearchTool(**tool_params))

    # fallback: se l'agente ha vector_store_ids validi ma manca file_search
    vector_store_ids = getattr(self.agent_data, "vector_store_ids", None)
    if (vector_store_ids and len(vector_store_ids) > 0 and 
        not any(isinstance(x, FileSearchTool) for x in tools)):
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=vector_store_ids,
            )
        )

    # strumenti Instagram per ruoli social
    if any(k in self.agent_data.role.lower() for k in ("social media", "instagram", "content")):
        tools.extend(self._get_instagram_function_tools())

    # permesso di creare nuovi tool
    if self.agent_data.can_create_tools:
        tools.append(self._create_custom_tool_tool())

    return tools
    
    def _get_instagram_function_tools(self) -> List[Any]:
        """Get Instagram-specific function tools"""
        # Import Instagram tools from social_media module
        try:
            from tools.social_media import InstagramTools
            return [
                InstagramTools.analyze_hashtags,
                InstagramTools.analyze_account,
                InstagramTools.generate_content_ideas,
                InstagramTools.analyze_competitors
            ]
        except ImportError:
            logger.warning("Instagram tools not available")
            return []
    
    # ==============================================================================
    # HANDOFF INPUT FILTERS - CONVERSATION HISTORY OPTIMIZATION
    # ==============================================================================
    
    async def _optimize_conversation_history_with_ai(self, handoff_input_data):
        """Optimize conversation history using AI summarization for complex handoffs"""
        # Remove tool calls first
        filtered_data = handoff_filters.remove_all_tools(handoff_input_data)
        
        # For complex conversations, use AI summarization
        if len(filtered_data.input_history) > 5:
            optimized_history = await self.conversation_optimizer.optimize_with_ai_summary(
                list(filtered_data.input_history)
            )
        else:
            # Use basic optimization for shorter conversations
            optimized_history = list(filtered_data.input_history)
        
        return HandoffInputData(
            input_history=tuple(optimized_history),
            pre_handoff_items=filtered_data.pre_handoff_items,
            new_items=filtered_data.new_items,
        )
    
    def _optimize_conversation_history(self, handoff_input_data):
        """Optimize conversation history for better handoff performance"""
        # Remove tool calls for cleaner history
        filtered_data = handoff_filters.remove_all_tools(handoff_input_data)
        
        # Advanced conversation compression
        history = list(filtered_data.input_history)
        optimized_history = []
        
        # Keep first message (usually contains important context)
        if history:
            optimized_history.append(history[0])
            
        # Keep last 5 messages for recent context
        if len(history) > 6:
            optimized_history.extend(history[-5:])
        else:
            optimized_history.extend(history[1:])
        
        # Remove duplicate or very similar consecutive messages
        final_history = []
        prev_content = None
        
        for msg in optimized_history:
            content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
            # Simple similarity check (can be enhanced with embeddings)
            if prev_content is None or abs(len(content) - len(prev_content)) > 50 or content[:100] != prev_content[:100]:
                final_history.append(msg)
                prev_content = content
        
        return HandoffInputData(
            input_history=tuple(final_history),
            pre_handoff_items=filtered_data.pre_handoff_items,
            new_items=filtered_data.new_items,
        )
    
    def _escalation_input_filter(self, handoff_input_data):
        """Enhanced input filter for escalation handoffs"""
        # More aggressive cleaning for escalations, keep essential context
        filtered_data = handoff_filters.remove_all_tools(handoff_input_data)
        
        # For escalations, keep the original request and the last few messages
        history = list(filtered_data.input_history)
        if len(history) > 4:
            # Keep first message (original request) and last 3 messages
            optimized_history = [history[0]] + history[-3:]
        else:
            optimized_history = history
            
        return HandoffInputData(
            input_history=tuple(optimized_history),
            pre_handoff_items=filtered_data.pre_handoff_items, 
            new_items=filtered_data.new_items,
        )
        
    def _delegation_input_filter(self, handoff_input_data):
        """Enhanced input filter for delegation handoffs"""
        # For delegation, we want to be more comprehensive but still clean
        return self._optimize_conversation_history(handoff_input_data)
    
    def _coordinator_input_filter(self, handoff_input_data):
        """Enhanced input filter for coordinator handoffs with conversation optimization"""
        return self._optimize_conversation_history(handoff_input_data)
    
    # ==============================================================================
    # HANDOFFS IMPLEMENTATION
    # ==============================================================================
    
    def _initialize_handoffs(self) -> List[Handoff]:
        """Initialize handoffs for this agent based on role and seniority with input filters"""
        handoffs = []

        placeholder_agent = OpenAIAgent(
            name="DynamicHandoffTarget",
            instructions="Placeholder for dynamic handoff resolution"
        )

        # Handoff per escalation (tutti tranne expert possono escalare)
        if self.agent_data.seniority != "expert":
            escalation_handoff = handoff(
                agent=placeholder_agent,
                tool_name_override="escalate_to_senior",
                tool_description_override="Escalate complex issues requiring higher expertise. Use when current task exceeds your capabilities.",
                on_handoff=self._on_escalation_handoff,
                input_type=EscalationData,
                input_filter=self._escalation_input_filter
            )
            handoffs.append(escalation_handoff)

        # Handoff al coordinatore (tutti gli agenti tranne i coordinatori stessi)
        if not any(keyword in self.agent_data.role.lower() for keyword in ["coordinator", "manager", "director"]):
            coordinator_handoff = handoff(
                agent=placeholder_agent, 
                tool_name_override="report_to_coordinator",
                tool_description_override="Report task completion and coordinate next steps with project manager.",
                on_handoff=self._on_coordinator_handoff,
                input_type=CompletionReport,
                input_filter=self._coordinator_input_filter
            )
            handoffs.append(coordinator_handoff)

        # Handoff specifico per coordinatori (delegazione)
        if any(keyword in self.agent_data.role.lower() for keyword in ["coordinator", "manager", "director"]):
            delegation_handoff = handoff(
                agent=placeholder_agent,  
                tool_name_override="delegate_to_specialist",
                tool_description_override="Delegate specific work to appropriate specialist agents.",
                on_handoff=self._on_delegation_handoff,
                input_type=DelegationData,
                input_filter=self._delegation_input_filter
            )
            handoffs.append(delegation_handoff)

        logger.info(f"Initialized {len(handoffs)} handoffs for agent {self.agent_data.name}")
        return handoffs
    
    async def _on_escalation_handoff(
        self,
        ctx: RunContextWrapper[T],
        input_data: EscalationData
    ):
        """Callback per gestire l'escalation handoff with context support"""
        try:
            logger.info(f"Agent {self.agent_data.id} ({self.agent_data.name}) escalating: {input_data.reason}")
            
            # Trova agenti senior dello stesso role/domain
            agents = await list_agents(str(self.agent_data.workspace_id))
            
            # Logica di selezione dell'agente target
            target_agent = None
            
            # Prima prova: cerca expert nello stesso role
            expert_agents = [
                a for a in agents 
                if a["seniority"] == "expert" and 
                   self._is_same_domain(a["role"], self.agent_data.role) and
                   a["id"] != str(self.agent_data.id)
            ]
            
            # Seconda prova: cerca senior nello stesso role
            if not expert_agents:
                senior_agents = [
                    a for a in agents 
                    if a["seniority"] == "senior" and 
                       self._is_same_domain(a["role"], self.agent_data.role) and
                       a["id"] != str(self.agent_data.id)
                ]
                target_agent = senior_agents[0] if senior_agents else None
            else:
                target_agent = expert_agents[0]
            
            if target_agent:
                # Log dell'escalation con dettagli
                await self._log_execution_internal("escalation_handoff", 
                    json.dumps({
                        "target_agent_id": target_agent["id"],
                        "target_agent_name": target_agent["name"],
                        "escalation_reason": input_data.reason,
                        "context": input_data.context,
                        "priority": input_data.priority
                    }))
                
                # Crea il target agent e mantiene il context
                target_specialist = self._create_agent_from_data(target_agent)
                ctx.set_agent(target_specialist)
            else:
                logger.warning(f"No suitable agent found for escalation from {self.agent_data.name}")
                # Fallback: escalate to coordinator
                coordinator = await self._find_coordinator()
                if coordinator:
                    coordinator_specialist = self._create_agent_from_data(coordinator)
                    ctx.set_agent(coordinator_specialist)
                    
        except Exception as e:
            logger.error(f"Error in escalation handoff: {e}")
            raise

    async def _on_coordinator_handoff(
        self,
        ctx: RunContextWrapper[T], 
        input_data: CompletionReport
    ):
        """Callback per handoff al coordinatore with context support"""
        try:
            logger.info(f"Agent {self.agent_data.id} ({self.agent_data.name}) reporting to coordinator")
            
            # Trova il coordinatore/project manager
            coordinator = await self._find_coordinator()
            
            if coordinator:
                await self._log_execution_internal("coordinator_handoff",
                    json.dumps({
                        "target_agent_id": coordinator["id"],
                        "target_agent_name": coordinator["name"],
                        "task_summary": input_data.task_summary,
                        "next_steps": input_data.next_steps,
                        "requires_followup": input_data.requires_followup
                    }))
                
                # Set the coordinator as the next agent with context preservation
                coordinator_specialist = self._create_agent_from_data(coordinator)
                ctx.set_agent(coordinator_specialist)
            else:
                logger.warning(f"No coordinator found for handoff from {self.agent_data.name}")
                
        except Exception as e:
            logger.error(f"Error in coordinator handoff: {e}")
            raise

    async def _on_delegation_handoff(
        self,
        ctx: RunContextWrapper[T],
        input_data: DelegationData
    ):
        """Callback per la delegazione da coordinator a specialist with context support"""
        try:
            logger.info(f"Coordinator {self.agent_data.name} delegating to {input_data.target_role}")
            
            # Trova l'agente appropriato per il role richiesto
            agents = await list_agents(str(self.agent_data.workspace_id))
            
            # Cerca il miglior match per role
            target_candidates = []
            for agent in agents:
                if self._matches_role(agent["role"], input_data.target_role):
                    target_candidates.append((agent, self._calculate_agent_score(agent, input_data)))
            
            if target_candidates:
                # Ordina per score e prendi il migliore
                target_candidates.sort(key=lambda x: x[1], reverse=True)
                target_agent = target_candidates[0][0]
                
                await self._log_execution_internal("delegation_handoff",
                    json.dumps({
                        "target_agent_id": target_agent["id"],
                        "target_agent_name": target_agent["name"],
                        "target_role": input_data.target_role,
                        "task_description": input_data.task_description,
                        "priority": input_data.priority
                    }))
                
                # Create and set target agent with context preservation
                target_specialist = self._create_agent_from_data(target_agent)
                ctx.set_agent(target_specialist)
            else:
                logger.warning(f"No suitable agent found for role {input_data.target_role}")
                
        except Exception as e:
            logger.error(f"Error in delegation handoff: {e}")
            raise
    
    # ==============================================================================
    # HELPER METHODS FOR HANDOFFS
    # ==============================================================================
    
    def _is_same_domain(self, role1: str, role2: str) -> bool:
        """Check if two roles are in the same domain"""
        # Semplifica i role per il confronto
        role1_clean = role1.lower().replace("specialist", "").replace("agent", "").strip()
        role2_clean = role2.lower().replace("specialist", "").replace("agent", "").strip()
        
        # Dominio keywords
        domains = {
            "content": ["content", "writing", "copywriting", "editorial"],
            "data": ["data", "analytics", "analysis", "insights"],
            "social": ["social", "instagram", "media", "marketing"],
            "technical": ["technical", "development", "engineering", "system"],
            "design": ["design", "creative", "visual", "graphics"]
        }
        
        for domain, keywords in domains.items():
            if any(kw in role1_clean for kw in keywords) and any(kw in role2_clean for kw in keywords):
                return True
        
        return False

    def _matches_role(self, agent_role: str, target_role: str) -> bool:
        """Check if an agent's role matches the target role"""
        agent_role_clean = agent_role.lower().strip()
        target_role_clean = target_role.lower().strip()
        
        # Exact match
        if target_role_clean in agent_role_clean:
            return True
        
        # Fuzzy matching per ruoli simili
        synonyms = {
            "content": ["content", "writing", "copywriting"],
            "data": ["data", "analytics", "analysis"],
            "social media": ["social", "instagram", "media"],
            "technical": ["technical", "development", "tech"]
        }
        
        for key, values in synonyms.items():
            if any(v in target_role_clean for v in values) and any(v in agent_role_clean for v in values):
                return True
        
        return False

    def _calculate_agent_score(self, agent: Dict, delegation_data: DelegationData) -> float:
        """Calculate a score for agent selection"""
        score = 0.0
        
        # Seniority bonus
        seniority_scores = {"expert": 3.0, "senior": 2.0, "junior": 1.0}
        score += seniority_scores.get(agent.get("seniority"), 0)
        
        # Status bonus (prefer active agents)
        if agent.get("status") == "active":
            score += 1.0
        
        # Health bonus
        health = agent.get("health", {})
        if health.get("status") == "healthy":
            score += 0.5
        
        # Role match precision bonus
        if delegation_data.target_role.lower() in agent["role"].lower():
            score += 2.0
        
        return score

    async def _find_coordinator(self) -> Optional[Dict]:
        """Find the workspace coordinator/project manager"""
        agents = await list_agents(str(self.agent_data.workspace_id))
        
        # Cerca per keywords specifiche
        coordinator_keywords = ["manager", "coordinator", "director", "lead"]
        
        for agent in agents:
            if any(keyword in agent["role"].lower() for keyword in coordinator_keywords):
                return agent
        
        # Se non trovi nessuno, prendi il primo expert
        experts = [a for a in agents if a.get("seniority") == "expert"]
        if experts:
            return experts[0]
        
        return None

    def _create_agent_from_data(self, agent_data: Dict) -> OpenAIAgent:
        """Create a temporary agent instance from database data"""
        # Converte i dati del database in un AgentModel
        agent_model = AgentModel.model_validate(agent_data)
        
        # Crea una nuova istanza di SpecialistAgent
        temp_specialist = SpecialistAgent(agent_model)
        return temp_specialist.agent
    
    # ==============================================================================
    # AGENT CREATION
    # ==============================================================================
    
    def _create_agent(self) -> OpenAIAgent:
        """Create the OpenAI Agent with the appropriate configuration"""
        # Determine model based on seniority
        model = self.agent_data.llm_config.get("model") if self.agent_data.llm_config else None
        if not model:
            model = self.seniority_model_map.get(self.agent_data.seniority, "gpt-4.1-mini")
        
        # Get other model settings
        temperature = self.agent_data.llm_config.get("temperature", 0.7) if self.agent_data.llm_config else 0.7
        
        # Create enhanced system prompt
        system_prompt = self._create_system_prompt()
        
        # Configure guardrails
        input_guardrails = [budget_monitoring_guardrail]
        output_guardrails = [quality_assurance_guardrail]
        
        # Determine output type based on role
        output_type = None
        if "coordinator" in self.agent_data.role.lower() or "manager" in self.agent_data.role.lower():
            output_type = TaskExecutionOutput
        
        # Create the agent with handoffs and structured outputs
        return OpenAIAgent(
            name=self.agent_data.name,
            instructions=system_prompt,
            model=model,
            model_settings=ModelSettings(
                temperature=temperature,
                top_p=self.agent_data.llm_config.get("top_p", 1.0) if self.agent_data.llm_config else 1.0,
                max_tokens=self.agent_data.llm_config.get("max_tokens", 32768) if self.agent_data.llm_config else 32768  # Increased for GPT-4.1
            ),
            tools=self.tools,
            handoffs=self.handoffs,  # Include handoffs
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails,
            output_type=output_type,  # Add structured output support
        )
    
    def _create_system_prompt(self) -> str:
        """Create an optimized system prompt focused on native handoffs"""
        # Import per handoff prompt recommendations
        try:
            from agents.extensions.handoff_prompt import prompt_with_handoff_instructions, RECOMMENDED_PROMPT_PREFIX
            handoff_prefix = RECOMMENDED_PROMPT_PREFIX
            use_enhanced_handoff_prompt = True
        except ImportError:
            # Fallback se l'extension non è disponibile
            handoff_prefix = """
You have access to handoff tools. Use them when:
- You need specialized expertise outside your role
- You've completed your part and need coordination
- You encounter issues requiring escalation
"""
            use_enhanced_handoff_prompt = False
        
        base_prompt = f"""
{handoff_prefix}

You are a {self.agent_data.seniority} AI specialist in {self.agent_data.role}.

CORE RESPONSIBILITIES:
- {self.agent_data.description or f"Expert work in {self.agent_data.role}"}
- Execute tasks efficiently within your expertise area
- Use handoffs for delegation, NOT task creation
- Provide clear completion signals

COMPLETION CRITERIA:
- Your task is complete when you've provided actionable results
- Signal explicit completion rather than suggesting more work
- Use handoffs to delegate follow-up work to appropriate specialists

HANDOFF GUIDELINES:
- escalate_to_senior: When you need more expertise on the same topic
- report_to_coordinator: When you've completed your part and need project coordination
- Always provide clear context and expected outcomes in handoffs

IMPORTANT: 
- Do NOT create new tasks via tools
- Do NOT suggest creating tasks for other agents
- Use direct handoffs for delegation
- Focus on completing YOUR assigned work efficiently
"""
        
        # Aggiungi guidance specifico per il ruolo
        if "coordinator" in self.agent_data.role.lower() or "manager" in self.agent_data.role.lower():
            base_prompt += """

AS A COORDINATOR/MANAGER:
- Use handoffs to delegate specific work to specialists
- Avoid creating excessive follow-up tasks
- Focus on orchestration, not micro-management
- Summarize and conclude when objectives are met
"""
        
        # Apply enhanced handoff instructions if available
        if use_enhanced_handoff_prompt:
            base_prompt = prompt_with_handoff_instructions(base_prompt)
        
        return base_prompt
    
    # ==============================================================================
    # AUTOMATION TOOLS
    # ==============================================================================
    
    def _create_auto_task_tool(self):
        """Create a tool for automatic task creation"""
        @function_tool
        async def create_task_for_agent(
            task_name: str,
            task_description: str,
            target_agent_role: str,
            priority: str
        ) -> str:
            """
            Create a new task and assign it to a specific agent role.
            
            Args:
                task_name: Name of the task to create
                task_description: Detailed description of the task
                target_agent_role: Role of the agent who should handle this task
                priority: Priority of the task (low, medium, high)
            
            Returns:
                JSON string with creation result
            """
            try:
                # Find the target agent by role
                agents = await list_agents(str(self.agent_data.workspace_id))
                target_agent = None
                
                for agent in agents:
                    if target_agent_role.lower() in agent["role"].lower():
                        target_agent = agent
                        break
                
                if not target_agent:
                    return json.dumps(TaskCreationOutput(
                        success=False,
                        task_name=task_name,
                        error_message=f"No agent found with role matching '{target_agent_role}'"
                    ).model_dump())
                
                # Create the task
                task_data = await create_task(
                    workspace_id=str(self.agent_data.workspace_id),
                    agent_id=target_agent["id"],
                    name=task_name,
                    description=f"{task_description}\n\nPriority: {priority}\nCreated by: {self.agent_data.name}",
                    status=TaskStatus.PENDING.value
                )
                
                if task_data:
                    # Log the task creation
                    await self._log_execution_internal(
                        "task_created",
                        json.dumps({
                            "created_task_id": task_data["id"],
                            "task_name": task_name,
                            "assigned_to": target_agent["name"],
                            "priority": priority
                        })
                    )
                    
                    return json.dumps(TaskCreationOutput(
                        success=True,
                        task_id=task_data["id"],
                        task_name=task_name,
                        assigned_agent=target_agent["name"]
                    ).model_dump())
                else:
                    return json.dumps(TaskCreationOutput(
                        success=False,
                        task_name=task_name,
                        error_message="Failed to create task in database"
                    ).model_dump())
                
            except Exception as e:
                logger.error(f"Error creating task: {e}")
                return json.dumps(TaskCreationOutput(
                    success=False,
                    task_name=task_name,
                    error_message=str(e)
                ).model_dump())
        
        return create_task_for_agent
    
    def _create_request_handoff_tool(self):
        """Create a tool for requesting handoffs to other agents"""
        @function_tool
        async def request_handoff(
            target_role: str,
            context: str,
            data_to_transfer: str,
            priority: str
        ) -> str:
            """
            Request a handoff to another agent with specific context and data.
            
            Args:
                target_role: Role of the target agent for handoff
                context: Context and reason for the handoff
                data_to_transfer: Information to pass to the target agent
                priority: Priority of the handoff (low, medium, high)
            
            Returns:
                JSON string with handoff result
            """
            try:
                # Log the handoff request
                await self._log_execution_internal(
                    "handoff_requested",
                    json.dumps({
                        "target_role": target_role,
                        "context": context,
                        "priority": priority,
                        "requesting_agent": self.agent_data.name
                    })
                )
                
                # Create a task for the target agent with handoff context
                task_description = f"""
HANDOFF FROM: {self.agent_data.name} ({self.agent_data.role})

CONTEXT: {context}

DATA/INFORMATION TRANSFERRED:
{data_to_transfer}

PRIORITY: {priority}

Please continue the work based on the information provided above.
"""
                
                # Use the auto task creation
                agents = await list_agents(str(self.agent_data.workspace_id))
                target_agent = None
                
                for agent in agents:
                    if target_role.lower() in agent["role"].lower():
                        target_agent = agent
                        break
                
                if not target_agent:
                    return json.dumps({
                        "success": False,
                        "error": f"No agent found with role matching '{target_role}'"
                    })
                
                # Create the handoff task
                task_data = await create_task(
                    workspace_id=str(self.agent_data.workspace_id),
                    agent_id=target_agent["id"],
                    name=f"Handoff from {self.agent_data.name}",
                    description=task_description,
                    status=TaskStatus.PENDING.value
                )
                
                if task_data:
                    return json.dumps({
                        "success": True,
                        "task_id": task_data["id"],
                        "target_agent": target_agent["name"],
                        "handoff_type": "task_creation"
                    })
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Failed to create handoff task"
                    })
                
            except Exception as e:
                logger.error(f"Error requesting handoff: {e}")
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        return request_handoff
    
    # ==============================================================================
    # INTERNAL METHODS
    # ==============================================================================
    
    async def _log_execution_internal(self, step: str, details: str) -> bool:
        """Internal method for logging execution"""
        try:
            # Parse details string to dictionary
            details_dict = {}
            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            else:
                details_dict = {"raw_message": str(details)}
            
            # Enhanced logging with metadata
            log_entry = {
                "agent_id": str(self.agent_data.id),
                "agent_name": self.agent_data.name,
                "step": step,
                "timestamp": None,  # Will be set by database
                "details": details_dict,
                "seniority": self.agent_data.seniority,
                "workspace_id": str(self.agent_data.workspace_id)
            }
            
            logger.info(f"Agent execution log: {json.dumps(log_entry)}")
            
            # TODO: Save to execution_logs table in database
            # await save_execution_log(log_entry)
            
            return True
        except Exception as e:
            logger.error(f"Error in log_execution: {e}")
            return False
    
    async def _update_health_status_internal(self, status: str, details: Optional[str] = None) -> bool:
        """Internal method for updating health status"""
        try:
            # Parse details
            details_dict = {}
            if details:
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            
            # Add system metrics
            details_dict.update({
                "model_used": self.agent.model,
                "tools_count": len(self.tools),
                "check_timestamp": None  # Will be set by database
            })
            
            health = AgentHealth(
                status=HealthStatus(status),
                details=details_dict
            )
            
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=self.agent_data.status,
                health=health.model_dump()
            )
            
            # Log health update
            logger.info(f"Agent {self.agent_data.id} health updated to {status}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to update agent health status: {e}")
            return False
    
    async def _report_progress_internal(
        self,
        task_id: str,
        progress_percentage: int,
        current_stage: str,
        notes: Optional[str] = None
    ) -> bool:
        """Internal method for reporting progress"""
        try:
            progress_data = {
                "task_id": task_id,
                "agent_id": str(self.agent_data.id),
                "progress_percentage": min(100, max(0, progress_percentage)),
                "current_stage": current_stage,
                "notes": notes,
                "timestamp": None  # Will be set by database
            }
            
            logger.info(f"Progress update: {json.dumps(progress_data)}")
            
            # TODO: Save to task_progress table
            # await save_task_progress(progress_data)
            
            return True
        except Exception as e:
            logger.error(f"Error reporting progress: {e}")
            return False
    
    # ==============================================================================
    # TOOL CREATORS
    # ==============================================================================
    
    def _create_log_execution_tool(self):
        """Create a function tool for log execution"""
        @function_tool
        async def log_execution(step: str, details: str) -> bool:
            """
            Log the execution of a step with structured data.
            
            Args:
                step: The name/description of the execution step
                details: Details about the execution (JSON string)
                
            Returns:
                Boolean indicating success
            """
            return await self._log_execution_internal(step, details)
        
        return log_execution
    
    def _create_update_health_status_tool(self):
        """Create a function tool for updating health status"""
        @function_tool
        async def update_health_status(status: str, details: Optional[str] = None) -> bool:
            """
            Update the health status of the agent with enhanced monitoring.
            
            Args:
                status: The health status (healthy, degraded, unhealthy)
                details: Optional details about the health status (JSON string)
                
            Returns:
                Boolean indicating success
            """
            return await self._update_health_status_internal(status, details)
        
        return update_health_status
    
    def _create_report_progress_tool(self):
        """Create a function tool for reporting progress"""
        @function_tool
        async def report_progress(
            task_id: str,
            progress_percentage: int,
            current_stage: str,
            notes: Optional[str] = None
        ) -> bool:
            """
            Report progress on a task.
            
            Args:
                task_id: ID of the task being worked on
                progress_percentage: Progress as percentage (0-100)
                current_stage: Description of current stage
                notes: Optional additional notes
                
            Returns:
                Boolean indicating success
            """
            return await self._report_progress_internal(task_id, progress_percentage, current_stage, notes)
        
        return report_progress
    
    def _create_custom_tool_tool(self):
        """Create a function tool for creating custom tools"""
        @function_tool
        async def create_custom_tool(
            name: str,
            description: str,
            code: str,
            test_input: Optional[str] = None
        ) -> str:
            """
            Create a custom tool with validation and testing.
            
            Args:
                name: The name of the tool function
                description: A description of what the tool does
                code: Python code implementing the tool (must be an async function)
                test_input: Optional test input to validate the tool
                
            Returns:
                Information about the created tool (JSON string)
            """
            try:
                from tools.registry import tool_registry
            except ImportError:
                logger.warning("Tool registry not available")
                return json.dumps(ToolCreationOutput(
                    success=False,
                    tool_name=name,
                    error_message="Tool registry not available"
                ).model_dump())
            
            logger.info(f"Agent {self.agent_data.id} creating custom tool: {name}")
            
            try:
                # Validate the tool code
                validation_results = await self._validate_tool_code(code, test_input)
                
                if not validation_results["valid"]:
                    return json.dumps(ToolCreationOutput(
                        success=False,
                        tool_name=name,
                        error_message=f"Validation failed: {validation_results['error']}",
                        validation_results=validation_results
                    ).model_dump())
                
                # Register the tool with the registry
                tool_info = await tool_registry.register_tool(
                    name=name,
                    description=description,
                    code=code,
                    workspace_id=str(self.agent_data.workspace_id),
                    created_by="agent"
                )
                
                # Save to database
                try:
                    from database import create_custom_tool
                    tool_db_record = await create_custom_tool(
                        name=name,
                        description=description,
                        code=code,
                        workspace_id=str(self.agent_data.workspace_id),
                        created_by="agent"
                    )
                except ImportError:
                    tool_db_record = None
                
                return json.dumps(ToolCreationOutput(
                    success=True,
                    tool_name=name,
                    tool_id=tool_db_record.get("id") if tool_db_record else None,
                    validation_results=validation_results
                ).model_dump())
                
            except Exception as e:
                logger.error(f"Failed to create custom tool: {e}")
                return json.dumps(ToolCreationOutput(
                    success=False,
                    tool_name=name,
                    error_message=str(e)
                ).model_dump())
        
        return create_custom_tool
    
    async def _validate_tool_code(self, code: str, test_input: Optional[str] = None) -> Dict[str, Any]:
        """Validate tool code for security and correctness"""
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')
            
            # Check for dangerous operations
            dangerous_patterns = [
                'import os', 'import sys', 'import subprocess',
                'eval(', 'exec(', '__import__'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    return {
                        "valid": False,
                        "error": f"Dangerous operation detected: {pattern}",
                        "security_check": False
                    }
            
            # TODO: Add more sophisticated validation
            # - Runtime testing in sandbox
            # - Security analysis
            # - Performance checks
            
            return {
                "valid": True,
                "security_check": True,
                "syntax_check": True
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {str(e)}",
                "syntax_check": False
            }
    
    # ==============================================================================
    # CONTEXT MANAGEMENT
    # ==============================================================================
    
    def create_context(self, **kwargs) -> T:
        """Create a context object of the specified type"""
        if self.context_type == dict:
            return kwargs
        else:
            # Assume it's a Pydantic model or dataclass
            return self.context_type(**kwargs)
    
    async def execute_task_with_context(self, task: Task, **context_kwargs) -> Dict[str, Any]:
        """Execute task with a properly typed context"""
        context = self.create_context(**context_kwargs)
        return await self.execute_task(task, context=context)
    
    # ==============================================================================
    # CORE METHODS
    # ==============================================================================
    
    async def verify_capabilities(self) -> bool:
        """
        Verify that the agent has all the capabilities it needs.
        
        Returns:
            Boolean indicating if all capabilities are available
        """
        try:
            # Create verification prompt
            verification_prompt = """
Perform a comprehensive capability verification:
1. List all available tools and their status
2. Check system connectivity and resources
3. Verify model configuration and access
4. Test basic functionality if possible
5. Report any missing requirements or limitations

Provide a structured assessment of your capabilities.
"""
            
            result = await Runner.run(
                self.agent,
                verification_prompt
            )
            
            # Process the structured output
            verification_output = result.final_output
            if isinstance(verification_output, CapabilityVerificationOutput):
                verification_passed = verification_output.verification_status == "passed"
            else:
                # Fallback parsing for unstructured output
                verification_passed = "verification_status: passed" in str(verification_output)
            
            # Update agent status based on verification
            if verification_passed:
                await update_agent_status(
                    agent_id=str(self.agent_data.id),
                    status=AgentStatus.ACTIVE.value,
                    health={
                        "status": HealthStatus.HEALTHY.value,
                        "last_update": None,
                        "details": {
                            "verification": "passed",
                            "tools_verified": len(self.tools),
                            "model": self.agent.model
                        }
                    }
                )
            else:
                await update_agent_status(
                    agent_id=str(self.agent_data.id),
                    status=AgentStatus.ERROR.value,
                    health={
                        "status": HealthStatus.DEGRADED.value,
                        "last_update": None,
                        "details": {
                            "verification": "failed",
                            "output": str(verification_output)
                        }
                    }
                )
            
            return verification_passed
            
        except Exception as e:
            logger.error(f"Failed to verify agent capabilities: {e}")
            
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=AgentStatus.ERROR.value,
                health={
                    "status": HealthStatus.UNHEALTHY.value,
                    "last_update": None,
                    "details": {
                        "verification": "error",
                        "error": str(e)
                    }
                }
            )
            
            return False
    
    async def execute_task(self, task: Task, context: Optional[T] = None) -> Dict[str, Any]:
        """Execute a task with full native handoff support, context management and tracing"""
        # Generate trace ID per questo task
        trace_id = gen_trace_id()
        workflow_name = f"Task-{task.name}-{self.agent_data.name}"
        
        with trace(workflow_name=workflow_name, trace_id=trace_id, group_id=str(task.id)):
            try:
                # Initialization span
                with custom_span("Task Initialization"):
                    await update_task_status(
                        task_id=str(task.id),
                        status=TaskStatus.IN_PROGRESS.value
                    )
                    
                    # Log task start with trace metadata
                    await self._log_execution_internal(
                        "task_started",
                        json.dumps({
                            "task_id": str(task.id),
                            "task_name": task.name,
                            "description": task.description,
                            "trace_id": trace_id,
                            "workflow_name": workflow_name
                        })
                    )
                
                # Task execution span
                with custom_span("Task Execution"):
                    # Enhanced task prompt with handoff capabilities
                    task_prompt = f"""
Execute the following task with full automation and handoff capabilities:

Task: {task.name}
Description: {task.description}

AUTOMATION TOOLS AVAILABLE:
1. create_task_for_agent: Create new tasks for specialists
2. request_handoff: Hand off work to other agents

HANDOFF TOOLS AVAILABLE:
1. escalate_to_senior: Escalate to more senior agents when needed
2. report_to_coordinator: Report completion to project coordinator
3. delegate_to_specialist: (Coordinators only) Delegate work to specialists

IMPORTANT INSTRUCTIONS:
- If this task involves multiple phases, create specific tasks for each phase
- If you identify work that needs specific expertise, delegate it immediately
- If you complete your part but need follow-up, create those tasks now
- Use handoffs when you need to transfer context and data to others
- Be proactive - don't wait for manual intervention

When using handoffs:
- Provide clear context and reasoning
- Include all relevant work completed so far
- Specify expected outputs from target agents
- Use appropriate priority levels

Execute the task and handle all automation and handoffs proactively.
"""
                    
                    # Execute with context support
                    result = await Runner.run(
                        self.agent, 
                        task_prompt, 
                        max_turns=20,
                        context=context
                    )
                
                # Result processing span
                with custom_span("Result Processing"):
                    # SUCCESS CASE - Task completato normalmente
                    task_result = {
                        "output": result.final_output,
                        "status": "completed",
                        "max_turns_reached": False,
                        "execution_success": True,
                        "handoffs_performed": len([item for item in result.new_items if item.type == "handoff_output_item"]),
                        "trace_id": trace_id,
                        "workflow_name": workflow_name,
                        "automation_actions": {
                            "tasks_created": [],
                            "handoffs_requested": [],
                            "next_steps_identified": []
                        }
                    }
                    
                    # Update task status with structured result
                    await update_task_status(
                        task_id=str(task.id),
                        status=TaskStatus.COMPLETED.value,
                        result=task_result
                    )
                    
                    # Log completion using internal method
                    await self._log_execution_internal(
                        "task_completed",
                        json.dumps({
                            "task_id": str(task.id),
                            "status": task_result.get("status"),
                            "handoffs_performed": task_result.get("handoffs_performed", 0),
                            "trace_id": trace_id,
                            "summary": str(result.final_output)[:200] + "..." if len(str(result.final_output)) > 200 else str(result.final_output)
                        })
                    )
                    
                    logger.info(f"Task {task.id} completed successfully. Trace: {trace_id}")
                    return task_result
                    
            except MaxTurnsExceeded as max_turns_error:
                # CRITICAL FIX - Gestione specifica per MaxTurnsExceeded
                with custom_span("Max Turns Error Handling"):
                    logger.error(f"Task {task.id} exceeded max turns without completion")
                    
                    # Prova a recuperare l'ultimo output parziale se disponibile
                    partial_output = getattr(max_turns_error, 'last_output', None)
                    
                    error_result = {
                        "error": "Task exceeded maximum turns (20) without reaching completion",
                        "status": "failed",
                        "max_turns_reached": True,
                        "partial_output": partial_output,
                        "execution_success": False,
                        "failure_reason": "max_turns_exceeded",
                        "trace_id": trace_id
                    }
                    
                    # IMPORTANTE: Marca come FAILED, non COMPLETED
                    await update_task_status(
                        task_id=str(task.id), 
                        status=TaskStatus.FAILED.value,  # ← QUESTO È IL FIX CRITICO
                        result=error_result
                    )
                    
                    await self._log_execution_internal("task_failed", 
                        json.dumps({
                            "task_id": str(task.id), 
                            "error": "max_turns_exceeded",
                            "trace_id": trace_id,
                            "partial_output_length": len(str(partial_output)) if partial_output else 0
                        }))
                    
                    return error_result
                    
            except (ModelBehaviorError, AgentsException) as sdk_error:
                # Handle SDK-specific errors
                with custom_span("SDK Error Handling"):
                    logger.error(f"Task {task.id} failed with SDK error: {sdk_error}")
                    
                    error_result = {
                        "error": f"Agent SDK error: {type(sdk_error).__name__}",
                        "details": str(sdk_error),
                        "status": "failed", 
                        "execution_success": False,
                        "failure_reason": "sdk_error",
                        "trace_id": trace_id
                    }
                    
                    await update_task_status(
                        task_id=str(task.id),
                        status=TaskStatus.FAILED.value,
                        result=error_result
                    )
                    
                    await self._log_execution_internal("task_failed",
                        json.dumps({
                            "task_id": str(task.id), 
                            "error": str(sdk_error),
                            "error_type": type(sdk_error).__name__,
                            "trace_id": trace_id
                        }))
                    
                    return error_result
                    
            except Exception as e:
                # Altri tipi di errore
                with custom_span("General Error Handling"):
                    logger.error(f"Task {task.id} failed with error: {e}")
                    
                    error_result = {
                        "error": str(e),
                        "status": "failed", 
                        "execution_success": False,
                        "failure_reason": "execution_error",
                        "trace_id": trace_id
                    }
                    
                    await update_task_status(
                        task_id=str(task.id),
                        status=TaskStatus.FAILED.value,
                        result=error_result
                    )
                    
                    await self._log_execution_internal("task_failed",
                        json.dumps({
                            "task_id": str(task.id), 
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "trace_id": trace_id
                        }))
                    
                    return error_result
    
    # ==============================================================================
    # UTILITY METHODS
    # ==============================================================================
    
    def as_tool(self, tool_name: Optional[str] = None, tool_description: Optional[str] = None):
        """
        Convert this agent into a tool that can be used by other agents.
        
        Args:
            tool_name: Custom name for the tool
            tool_description: Custom description for the tool
            
        Returns:
            Agent tool
        """
        return self.agent.as_tool(
            tool_name=tool_name or f"consult_{self.agent_data.name.lower().replace(' ', '_')}",
            tool_description=tool_description or f"Consult {self.agent_data.name} for {self.agent_data.role} expertise"
        )
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of this agent's capabilities"""
        return {
            "name": self.agent_data.name,
            "role": self.agent_data.role,
            "seniority": self.agent_data.seniority,
            "model": self.agent.model,
            "tools_count": len(self.tools),
            "can_create_tools": self.agent_data.can_create_tools,
            "handoffs_configured": len(self.handoffs),
            "guardrails_active": {
                "input": len(self.agent.input_guardrails) > 0,
                "output": len(self.agent.output_guardrails) > 0
            },
            "automation_enabled": True
        }
    
    async def test_conversation_optimization(self, sample_history: List[Dict]) -> Dict[str, Any]:
        """Test and validate conversation history optimization"""
        original_size = len(sample_history)
        
        # Test basic optimization
        handoff_data = HandoffInputData(
            input_history=tuple(sample_history),
            pre_handoff_items=tuple(),
            new_items=tuple()
        )
        
        basic_optimized = self._optimize_conversation_history(handoff_data)
        basic_size = len(basic_optimized.input_history)
        
        # Test AI optimization
        ai_optimized = await self._optimize_conversation_history_with_ai(handoff_data)
        ai_size = len(ai_optimized.input_history)
        
        return {
            "original_size": original_size,
            "basic_optimized_size": basic_size,
            "ai_optimized_size": ai_size,
            "basic_reduction": round((1 - basic_size/original_size) * 100, 2),
            "ai_reduction": round((1 - ai_size/original_size) * 100, 2),
            "optimization_effective": basic_size < original_size or ai_size < original_size
        }
    
    async def test_handoffs_configuration(self) -> Dict[str, Any]:
        """Test method to verify handoffs are properly configured"""
        handoff_info = []
        
        for handoff_obj in self.handoffs:
            info = {
                "tool_name": getattr(handoff_obj, 'tool_name', 'unknown'),
                "description": getattr(handoff_obj, 'tool_description', 'no description'),
                "input_type": str(getattr(handoff_obj, 'input_type', None)),
                "has_callback": getattr(handoff_obj, 'on_handoff', None) is not None
            }
            handoff_info.append(info)
        
        return {
            "agent_name": self.agent_data.name,
            "agent_role": self.agent_data.role,
            "handoffs_count": len(self.handoffs),
            "handoffs_details": handoff_info
        }