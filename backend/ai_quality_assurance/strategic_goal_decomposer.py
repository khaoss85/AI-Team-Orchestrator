#!/usr/bin/env python3
"""
🧠 STRATEGIC GOAL DECOMPOSER
AI-driven system che spacchetta obiettivi complessi in tutti i deliverable e asset necessari
per raggiungerli, mantenendo il collegamento con le metriche finali.
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DeliverableType(Enum):
    """Tipi di deliverable che il sistema può identificare e produrre"""
    STRATEGY_DOCUMENT = "strategy_document"           # Documenti strategici
    CONTENT_CALENDAR = "content_calendar"           # Calendari editoriali
    TEMPLATE_COLLECTION = "template_collection"      # Template e modelli
    ANALYSIS_REPORT = "analysis_report"             # Analisi e ricerche
    MONITORING_SYSTEM = "monitoring_system"         # Sistemi di monitoraggio
    WORKFLOW_PROCESS = "workflow_process"           # Processi e workflow
    GUIDELINE_DOCUMENT = "guideline_document"       # Linee guida
    CONTACT_DATABASE = "contact_database"           # Database contatti
    EMAIL_SEQUENCE = "email_sequence"               # Sequenze email
    SOCIAL_MEDIA_PLAN = "social_media_plan"        # Piani social media
    MARKETING_CAMPAIGN = "marketing_campaign"       # Campagne marketing
    TRAINING_MATERIAL = "training_material"         # Materiali formativi
    AUTOMATION_SETUP = "automation_setup"          # Setup automazioni
    MEASUREMENT_FRAMEWORK = "measurement_framework"  # Framework di misurazione
    # Additional types needed for AI-generated deliverables
    CONTACT_LIST = "contact_list"                   # Lista contatti
    PERFORMANCE_MONITORING_FRAMEWORK = "performance_monitoring_framework"  # Framework monitoraggio performance
    AUDIENCE_ANALYSIS = "audience_analysis"         # Analisi audience
    MARKET_RESEARCH = "market_research"             # Ricerca di mercato
    EMAIL_TEMPLATE = "email_template"               # Template email
    COMPETITOR_ANALYSIS = "competitor_analysis"     # Analisi competitor
    BRAND_GUIDE = "brand_guide"                     # Guida brand
    CONTENT_STRATEGY = "content_strategy"           # Strategia contenuti
    ENGAGEMENT_WORKFLOW = "engagement_workflow"     # Workflow engagement
    ANALYTICS_SETUP = "analytics_setup"             # Setup analytics
    # Missing types from logs
    PROSPECT_LIST = "prospect_list"                 # Lista prospect
    EMAIL_SEQUENCES = "email_sequences"             # Sequenze email multiple
    EMAIL_PERFORMANCE_MONITORING = "email_performance_monitoring"  # Monitoraggio performance email
    PERFORMANCE_MONITORING = "performance_monitoring"  # Monitoraggio performance generico
    EMAIL_VALIDATION = "email_validation"               # Validazione email
    DATA_SOURCES = "data_sources"                   # Fonti dati
    EMAIL_STRATEGY = "email_strategy"               # Strategia email
    FEEDBACK_LOOP = "feedback_loop"                 # Loop di feedback
    AUDIENCE_ANALYSIS_REPORT = "audience_analysis_report"  # Report analisi audience
    AB_TESTING_PLAN = "ab_testing_plan"             # Piano A/B testing
    HUBSPOT_SETUP = "hubspot_setup"                 # Setup e configurazione HubSpot
    GDPR_COMPLIANCE_CHECKLIST = "gdpr_compliance_checklist"  # Checklist conformità GDPR
    # Social Media & Content Marketing Types
    CONTENT_STRATEGY_DOCUMENT = "content_strategy_document"  # Documento strategia contenuti
    HASHTAG_RESEARCH = "hashtag_research"                   # Ricerca hashtag
    HASHTAG_STRATEGY = "hashtag_strategy"                   # Strategia hashtag
    CONTENT_CREATION_GUIDELINES = "content_creation_guidelines"  # Linee guida creazione contenuti
    BRAND_VOICE_GUIDE = "brand_voice_guide"                # Guida voice & tone brand
    COMPETITOR_ANALYSIS_REPORT = "competitor_analysis_report"  # Report analisi competitor
    INFLUENCER_OUTREACH_STRATEGY = "influencer_outreach_strategy"  # Strategia influencer outreach
    INFLUENCER_OUTREACH = "influencer_outreach"             # Piano outreach influencer
    ANALYTICS_TRACKING_SETUP = "analytics_tracking_setup"   # Setup tracking analytics
    # Generic Strategies
    STRATEGY_PLAN = "strategy_plan"                         # Piano strategico generico

@dataclass
class StrategicDeliverable:
    """Rappresenta un deliverable necessario per raggiungere l'obiettivo"""
    deliverable_type: DeliverableType
    name: str
    description: str
    priority: int                    # 1=alta, 5=bassa
    estimated_effort: str           # "2-3 hours", "1 week", etc.
    depends_on: List[str]           # Lista di deliverable prerequisiti
    contributes_to_metrics: List[str]  # Quali metriche finali impatta
    acceptance_criteria: List[str]   # Criteri di accettazione
    business_value: str             # Valore business di questo deliverable
    required_tools: List[str]       # Tool o risorse necessarie
    semantic_context: Dict[str, Any] # Contesto per la generazione AI
    # AI Autonomy Analysis
    autonomy_level: str = "autonomous"  # "autonomous", "assisted", "human_required"
    autonomy_reason: str = ""       # Spiegazione del livello di autonomia
    available_tools: List[str] = None  # Tool disponibili per questo task
    human_input_required: List[str] = None  # Cosa serve dall'utente

@dataclass
class StrategicGoalPlan:
    """Piano strategico completo per raggiungere un obiettivo"""
    original_goal: str
    final_metrics: List[Dict[str, Any]]      # Metriche finali da raggiungere
    required_deliverables: List[StrategicDeliverable]  # Tutti i deliverable necessari
    execution_phases: List[Dict[str, Any]]   # Fasi di esecuzione
    estimated_timeline: str                  # Timeline complessiva
    critical_success_factors: List[str]      # Fattori critici di successo
    potential_risks: List[str]               # Rischi identificati
    required_resources: Dict[str, Any]       # Risorse necessarie

class StrategicGoalDecomposer:
    """
    🧠 AI-driven decomposer che analizza obiettivi complessi e li spacchetta
    in tutti i deliverable, asset e task necessari per raggiungerli.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ Strategic Goal Decomposer initialized with OpenAI")
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for strategic decomposition")
        else:
            self.ai_available = False
        
        
        # 🚀 Available tools in current system (can be extended dynamically)
        self.current_available_tools = [
            "content_creation", "web_search", "data_analysis", "code_generation", 
            "file_search", "market_research", "email_template_generation"
        ]
    
    async def decompose_strategic_goal(self, goal_text: str, workspace_context: Optional[Dict] = None, progress_callback: Optional[callable] = None) -> StrategicGoalPlan:
        """
        🧠 Spacchetta un obiettivo complesso in piano strategico completo
        """
        logger.info(f"🎯 Strategic decomposition of: {goal_text[:100]}...")
        
        if not self.ai_available:
            logger.error("AI not available for strategic decomposition")
            raise Exception("AI service required for strategic goal decomposition")
        
        # Progress tracking
        if progress_callback:
            progress_callback({"status": "analyzing", "progress": 10, "message": "Analisi obiettivo iniziata..."})
        
        try:
            # Step 1: Analizza l'obiettivo e identifica le metriche finali
            if progress_callback:
                progress_callback({"status": "extracting_metrics", "progress": 20, "message": "Estrazione metriche finali..."})
            final_metrics = await self._extract_final_metrics(goal_text)
            
            # Step 2: Identifica tutti i deliverable necessari
            if progress_callback:
                progress_callback({"status": "identifying_deliverables", "progress": 40, "message": "Identificazione deliverable strategici..."})
            deliverables = await self._identify_required_deliverables(goal_text, workspace_context, progress_callback)
            
            # Step 3: Crea piano di esecuzione con fasi
            if progress_callback:
                progress_callback({"status": "creating_plan", "progress": 75, "message": "Creazione piano di esecuzione..."})
            execution_plan = await self._create_execution_plan(goal_text, deliverables)
            
            # Step 4: Analizza rischi e fattori di successo
            if progress_callback:
                progress_callback({"status": "analyzing_risks", "progress": 90, "message": "Analisi rischi e fattori di successo..."})
            strategic_analysis = await self._analyze_strategic_factors(goal_text, deliverables)
            
            plan = StrategicGoalPlan(
                original_goal=goal_text,
                final_metrics=final_metrics,
                required_deliverables=deliverables,
                execution_phases=execution_plan["phases"],
                estimated_timeline=execution_plan["timeline"],
                critical_success_factors=strategic_analysis["success_factors"],
                potential_risks=strategic_analysis["risks"],
                required_resources=strategic_analysis["resources"]
            )
            
            if progress_callback:
                progress_callback({"status": "completed", "progress": 100, "message": f"Piano strategico completato: {len(deliverables)} deliverable, {len(plan.execution_phases)} fasi"})
            
            logger.info(f"✅ Strategic plan created: {len(deliverables)} deliverables, {len(plan.execution_phases)} phases")
            return plan
            
        except Exception as e:
            logger.error(f"Strategic decomposition failed: {e}")
            raise
    
    async def _extract_final_metrics(self, goal_text: str) -> List[Dict[str, Any]]:
        """Estrae le metriche finali quantificabili dall'obiettivo"""
        
        prompt = f"""Analyze this business goal and extract ONLY the final, quantifiable metrics that define success:

Goal: "{goal_text}"

Extract specific numerical targets that measure final success. For example:
- "200 followers per week" -> {{metric: "followers", target: 200, period: "weekly", unit: "followers"}}
- "+10% interaction rate" -> {{metric: "interaction_rate", target: 10, period: "ongoing", unit: "percentage_increase"}}

Return JSON format:
{{
    "final_metrics": [
        {{
            "metric_name": "followers_growth",
            "target_value": 200,
            "unit": "followers", 
            "period": "weekly",
            "metric_type": "contacts",
            "is_increase": true,
            "description": "Grow Instagram followers by 200 per week"
        }}
    ]
}}

Focus ONLY on final success metrics, not on deliverables or processes."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business metrics analyst. Extract only final quantifiable success metrics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("final_metrics", [])
            
        except Exception as e:
            logger.error(f"Final metrics extraction failed: {e}")
            return []
    
    async def _identify_required_deliverables(self, goal_text: str, workspace_context: Optional[Dict] = None, progress_callback: Optional[callable] = None) -> List[StrategicDeliverable]:
        """Identifica TUTTI i deliverable necessari per raggiungere l'obiettivo"""
        
        context_str = ""
        if workspace_context:
            context_str = f"\nWorkspace context: {json.dumps(workspace_context, indent=2)}"
        
        prompt = f"""Analyze this business goal and identify ALL the specific deliverables, assets, and resources needed to achieve it:

Goal: "{goal_text}"{context_str}

Think strategically about EVERYTHING needed. For an Instagram growth goal, you might need:
- Content calendar with posting schedule
- Content strategy document for target audience  
- Template collection for posts and reels
- Audience analysis and persona documentation
- Hashtag research and strategy
- Engagement workflow and guidelines
- Performance monitoring framework
- Content creation guidelines
- Brand voice and visual identity guide
- Competitor analysis report
- Influencer outreach strategy
- Analytics tracking setup

For each deliverable, specify:
1. What exactly needs to be created
2. Why it's necessary for the goal
3. Priority level (1=critical, 5=nice-to-have)
4. Effort estimate
5. Dependencies on other deliverables
6. Which final metrics it impacts
7. AI Autonomy Analysis - can AI agents do this autonomously?

Available AI Tools: web_search, file_search, code_generation, data_analysis, content_creation
Future Tools (in development): hubspot_integration, crm_connector, linkedin_api, email_validator

AI agents CANNOT: access private databases, make phone calls, conduct interviews, access paid services without proper API tools

Autonomy Levels (tool-dependent):
- "autonomous": AI can complete fully using CURRENT available tools
- "assisted": AI can do most work but needs specific tools or human input that aren't available yet
- "human_required": Requires significant human work or external services
- "tool_upgradeable": Currently assisted/human_required but could become autonomous with future tool development

IMPORTANT: Autonomy assessment must be based on CURRENT tool availability. If a deliverable needs HubSpot access, mark as "assisted" or "tool_upgradeable" and specify which tool would make it autonomous.

Return JSON format:
{{
    "required_deliverables": [
        {{
            "deliverable_type": "content_calendar",
            "name": "Instagram Content Calendar for Bodybuilding Audience",
            "description": "3-month detailed content calendar with daily posting schedule, content types, and engagement strategies tailored for male bodybuilders",
            "priority": 1,
            "estimated_effort": "3-4 days",
            "depends_on": ["content_strategy", "audience_analysis"], 
            "contributes_to_metrics": ["followers_growth", "interaction_rate"],
            "acceptance_criteria": [
                "90 days of planned content",
                "Mix of educational, motivational, and promotional posts",
                "Specific posting times optimized for target audience",
                "Hashtag strategy included for each post"
            ],
            "business_value": "Ensures consistent, targeted content that drives follower growth and engagement",
            "required_tools": ["content_planning_tool", "image_editing_software"],
            "semantic_context": {{
                "target_audience": "male bodybuilders",
                "platform": "instagram", 
                "content_focus": "fitness_motivation_education"
            }},
            "autonomy_level": "tool_upgradeable",
            "autonomy_reason": "AI can create framework templates and KPI definitions, but needs CRM integration tool for live monitoring setup",
            "available_tools": ["code_generation", "content_creation"],
            "human_input_required": ["API credentials", "CRM system access"],
            "future_tools_needed": ["hubspot_integration", "crm_connector"]
        }}
    ]
}}

Be comprehensive - identify EVERY deliverable needed for success."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strategic business analyst. Identify ALL deliverables needed to achieve complex goals. Be comprehensive and detailed."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            deliverables = []
            total_deliverables = len(result.get("required_deliverables", []))
            
            for idx, d in enumerate(result.get("required_deliverables", []), 1):
                try:
                    # Progress update for each deliverable analysis
                    if progress_callback:
                        progress = 40 + (idx / total_deliverables) * 30  # 40-70% progress range
                        progress_callback({
                            "status": "analyzing_deliverable", 
                            "progress": int(progress), 
                            "message": f"Analisi autonomia: {d.get('name', 'deliverable')} ({idx}/{total_deliverables})"
                        })
                    
                    # 🤖 AI-driven tool capability validation for concrete results
                    autonomy_analysis = await self._ai_validate_tool_capability(
                        deliverable_type=d.get("deliverable_type", "strategy_document"),
                        deliverable_name=d["name"],
                        deliverable_description=d["description"]
                    )
                    
                    deliverable = StrategicDeliverable(
                        deliverable_type=DeliverableType(d.get("deliverable_type", "strategy_document")),
                        name=d["name"],
                        description=d["description"],
                        priority=d.get("priority", 3),
                        estimated_effort=d.get("estimated_effort", "1-2 days"),
                        depends_on=d.get("depends_on", []),
                        contributes_to_metrics=d.get("contributes_to_metrics", []),
                        acceptance_criteria=d.get("acceptance_criteria", []),
                        business_value=d.get("business_value", ""),
                        required_tools=d.get("required_tools", []),
                        semantic_context=d.get("semantic_context", {}),
                        # 🎯 AI-driven autonomy analysis (no hardcoded mappings)
                        autonomy_level=autonomy_analysis.get("autonomy_level", "autonomous"),
                        autonomy_reason=autonomy_analysis.get("autonomy_reason", ""),
                        available_tools=autonomy_analysis.get("available_tools", []),
                        human_input_required=autonomy_analysis.get("human_input_required", [])
                    )
                    deliverables.append(deliverable)
                    autonomy_icon = "🤖" if deliverable.autonomy_level == "autonomous" else "👥" if deliverable.autonomy_level == "human_required" else "🤝"
                    logger.info(f"  ✅ {autonomy_icon} Identified deliverable: {deliverable.name} (priority: {deliverable.priority}, autonomy: {deliverable.autonomy_level})")
                except Exception as e:
                    logger.warning(f"Failed to parse deliverable: {e}")
                    # 🤖 AI-driven fallback: map unknown types to closest match
                    fallback_type = self._ai_map_unknown_deliverable_type(d.get("deliverable_type", "strategy_document"))
                    logger.info(f"🤖 AI fallback mapping: '{d.get('deliverable_type')}' → '{fallback_type}'")
                    
                    try:
                        # Retry with fallback type
                        autonomy_analysis = await self._ai_validate_tool_capability(
                            deliverable_type=fallback_type,
                            deliverable_name=d["name"],
                            deliverable_description=d["description"]
                        )
                        
                        deliverable = StrategicDeliverable(
                            deliverable_type=DeliverableType(fallback_type),
                            name=d["name"],
                            description=d["description"],
                            priority=d.get("priority", 3),
                            estimated_effort=d.get("estimated_effort", "1-2 days"),
                            depends_on=d.get("depends_on", []),
                            contributes_to_metrics=d.get("contributes_to_metrics", []),
                            acceptance_criteria=d.get("acceptance_criteria", []),
                            business_value=d.get("business_value", ""),
                            required_tools=d.get("required_tools", []),
                            semantic_context=d.get("semantic_context", {}),
                            autonomy_level=autonomy_analysis.get("autonomy_level", "autonomous"),
                            autonomy_reason=autonomy_analysis.get("autonomy_reason", ""),
                            available_tools=autonomy_analysis.get("available_tools", []),
                            human_input_required=autonomy_analysis.get("human_input_required", [])
                        )
                        deliverables.append(deliverable)
                        logger.info(f"  ✅ 🤖 AI-recovered deliverable: {deliverable.name}")
                    except Exception as e2:
                        logger.error(f"Failed to recover deliverable even with AI fallback: {e2}")
                        continue
            
            return deliverables
            
        except Exception as e:
            logger.error(f"Deliverable identification failed: {e}")
            return []
    
    async def _create_execution_plan(self, goal_text: str, deliverables: List[StrategicDeliverable]) -> Dict[str, Any]:
        """Crea un piano di esecuzione con fasi logiche"""
        
        deliverables_summary = "\n".join([
            f"- {d.name} (priority: {d.priority}, effort: {d.estimated_effort}, depends_on: {d.depends_on})"
            for d in deliverables
        ])
        
        prompt = f"""Create an execution plan for this goal with logical phases:

Goal: "{goal_text}"

Available deliverables:
{deliverables_summary}

Create phases that:
1. Group related deliverables logically
2. Respect dependencies 
3. Prioritize critical items first
4. Allow parallel work where possible

Return JSON format:
{{
    "phases": [
        {{
            "phase_name": "Foundation & Analysis",
            "phase_number": 1,
            "duration_estimate": "1-2 weeks",
            "deliverables": ["audience_analysis", "competitor_analysis"],
            "objectives": ["Understand target market and competitive landscape"],
            "success_criteria": ["Clear audience personas", "Competitive insights documented"]
        }}
    ],
    "timeline": "6-8 weeks total",
    "critical_path": ["audience_analysis", "content_strategy", "content_calendar"]
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a project management expert. Create logical execution phases with proper dependencies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Execution plan creation failed: {e}")
            return {"phases": [], "timeline": "Unknown", "critical_path": []}
    
    async def _analyze_strategic_factors(self, goal_text: str, deliverables: List[StrategicDeliverable]) -> Dict[str, Any]:
        """Analizza fattori di successo, rischi e risorse necessarie"""
        
        prompt = f"""Analyze the strategic factors for achieving this goal:

Goal: "{goal_text}"

Deliverables planned: {len(deliverables)} items including content calendar, strategy documents, monitoring systems, etc.

Identify:
1. Critical success factors (what MUST go right)
2. Potential risks and mitigation strategies  
3. Required resources (tools, skills, time, budget)

Return JSON format:
{{
    "success_factors": [
        "Consistent content creation and posting",
        "Deep understanding of bodybuilding community",
        "High-quality visuals and videos"
    ],
    "risks": [
        "Algorithm changes affecting reach",
        "Content creation burnout", 
        "Competition from established accounts"
    ],
    "resources": {{
        "required_skills": ["content creation", "community management", "analytics"],
        "required_tools": ["content scheduling", "analytics platform", "design software"],
        "estimated_budget": "low",
        "time_commitment": "10-15 hours per week"
    }}
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strategic risk analyst. Identify success factors and potential obstacles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Strategic analysis failed: {e}")
            return {"success_factors": [], "risks": [], "resources": {}}
    
    async def _ai_validate_tool_capability(self, deliverable_type: str, deliverable_name: str, deliverable_description: str) -> Dict[str, Any]:
        """
        🤖 AI-driven validation of tool capability for concrete deliverable completion
        Completely agnostic and without hardcoded mappings
        """
        if not self.ai_available:
            # Fallback to optimistic autonomy if AI not available
            return {
                "autonomy_level": "autonomous",
                "autonomy_reason": "AI tools available for content creation",
                "available_tools": self.current_available_tools,
                "human_input_required": [],
                "future_tools_needed": []
            }
        
        available_tools_str = ", ".join(self.current_available_tools)
        
        prompt = f"""Analyze if the current AI tools can complete this deliverable autonomously and concretely.

DELIVERABLE TO ANALYZE:
- Type: {deliverable_type}
- Name: {deliverable_name}
- Description: {deliverable_description}

AVAILABLE AI TOOLS:
{available_tools_str}

ANALYSIS REQUIRED:
1. Can the available AI tools actually COMPLETE this deliverable to a professional standard?
2. What specific human input or external tools would be needed?
3. What level of autonomy is realistic?

AUTONOMY LEVELS:
- "autonomous": AI can complete 90%+ of the work to professional standard using current tools
- "assisted": AI can do 50-90% of work, needs human input for specific aspects
- "human_required": AI can do <50% of work, requires significant human expertise
- "tool_upgradeable": Currently limited but could become autonomous with specific future tools

IMPORTANT: Be realistic about AI limitations. Consider:
- Does this need real-time system access, APIs, or integrations not available?
- Does this require domain expertise, legal knowledge, or specialized skills?
- Can AI actually produce the final deliverable or just assist with it?

Return JSON format:
{{
    "autonomy_level": "autonomous|assisted|human_required|tool_upgradeable",
    "autonomy_reason": "specific explanation of what AI can/cannot do",
    "available_tools": ["list", "of", "usable", "current", "tools"],
    "human_input_required": ["specific", "things", "humans", "must", "provide"],
    "future_tools_needed": ["specific", "tools", "that", "would", "enable", "autonomy"],
    "completion_percentage": 85
}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI capability analyst. Be realistic about what AI can accomplish autonomously vs what requires human input."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"🤖 AI autonomy analysis for {deliverable_type}: {result.get('autonomy_level')} ({result.get('completion_percentage', 0)}%)")
            
            return result
            
        except Exception as e:
            logger.error(f"AI tool capability validation failed: {e}")
            # Fallback to conservative estimate
            return {
                "autonomy_level": "assisted",
                "autonomy_reason": "AI can assist with content creation, human verification needed",
                "available_tools": ["content_creation", "web_search"],
                "human_input_required": ["domain expertise", "final validation"],
                "future_tools_needed": [],
                "completion_percentage": 60
            }
    
    def _ai_map_unknown_deliverable_type(self, unknown_type: str) -> str:
        """
        🤖 AI-driven mapping of unknown deliverable types to closest available enum
        Pure agnostic approach - no hardcoded mappings
        """
        # Get all available deliverable types
        available_types = [dt.value for dt in DeliverableType]
        
        # Simple semantic mapping based on keywords
        unknown_lower = unknown_type.lower()
        
        # Keyword-based intelligent mapping
        if "strategy" in unknown_lower or "plan" in unknown_lower:
            return "strategy_document"
        elif "content" in unknown_lower and ("guidelines" in unknown_lower or "creation" in unknown_lower):
            return "guideline_document" 
        elif "hashtag" in unknown_lower:
            return "market_research"  # Hashtag research is a form of market research
        elif "voice" in unknown_lower or "brand" in unknown_lower:
            return "brand_guide"
        elif "competitor" in unknown_lower:
            return "competitor_analysis"
        elif "influencer" in unknown_lower or "outreach" in unknown_lower:
            return "marketing_campaign"  # Influencer outreach is a marketing campaign type
        elif "analytics" in unknown_lower or "tracking" in unknown_lower:
            return "analytics_setup"
        else:
            # Universal fallback
            logger.info(f"🤖 Unknown deliverable type '{unknown_type}' mapped to generic 'strategy_document'")
            return "strategy_document"

# Global instance
strategic_decomposer = StrategicGoalDecomposer()

async def decompose_goal_strategically(goal_text: str, workspace_context: Optional[Dict] = None) -> StrategicGoalPlan:
    """Helper function per decomposizione strategica"""
    return await strategic_decomposer.decompose_strategic_goal(goal_text, workspace_context)