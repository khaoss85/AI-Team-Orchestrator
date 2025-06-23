# backend/deliverable_system/requirements_analyzer.py

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import dal sistema esistente
from models import DeliverableRequirements, AssetRequirement, AssetSchema
from database import get_workspace, list_tasks, list_agents

# FIXED: Import centralizzato con fallback robusto
try:
    from backend.utils.quality_config_loader import load_quality_system_config
except ImportError:
    try:
        from utils.quality_config_loader import load_quality_system_config  # type: ignore
    except ImportError as e:
        logger = logging.getLogger(__name__)
        logger.error(
            f"❌ Critical: Could not load quality config loader - system may be unstable: {e}"
        )
        QUALITY_CONFIG_AVAILABLE = False

        # Emergency fallback
        class QualitySystemConfig:
            QUALITY_SCORE_THRESHOLD = 0.8
            ACTIONABILITY_THRESHOLD = 0.7
            AUTHENTICITY_THRESHOLD = 0.8
            COMPLETENESS_THRESHOLD = 0.7
            ENABLE_AI_QUALITY_EVALUATION = True
    else:
        QualitySystemConfig, QUALITY_CONFIG_AVAILABLE = load_quality_system_config()
        logger = logging.getLogger(__name__)
        if QUALITY_CONFIG_AVAILABLE:
            logger.info(
                "✅ QualitySystemConfig loaded successfully via centralized loader"
            )
        else:
            logger.warning("⚠️ QualitySystemConfig using fallback configuration")
else:
    QualitySystemConfig, QUALITY_CONFIG_AVAILABLE = load_quality_system_config()
    logger = logging.getLogger(__name__)
    if QUALITY_CONFIG_AVAILABLE:
        logger.info(
            "✅ QualitySystemConfig loaded successfully via centralized loader"
        )
    else:
        logger.warning("⚠️ QualitySystemConfig using fallback configuration")

logger = logging.getLogger(__name__)

class DeliverableRequirementsAnalyzer:
    """Analizza dinamicamente i requirements per deliverable azionabili"""
    
    def __init__(self):
        self.cache = {}
        
        # ENHANCED: Usa configurazione qualità se disponibile
        if QUALITY_CONFIG_AVAILABLE:
            self.quality_threshold = QualitySystemConfig.QUALITY_SCORE_THRESHOLD
            self.actionability_threshold = QualitySystemConfig.ACTIONABILITY_THRESHOLD
            logger.info(f"🔍 Using Quality Config: threshold={self.quality_threshold}")
        else:
            self.quality_threshold = 0.8
            self.actionability_threshold = 0.7
            logger.warning(f"🔄 Using default thresholds: quality={self.quality_threshold}")
        
    async def analyze_deliverable_requirements(
        self, 
        workspace_id: str, 
        force_refresh: bool = False
    ) -> DeliverableRequirements:
        """
        Analizza dinamicamente che tipo di deliverable azionabili servono
        Integrato con il sistema esistente di fasi e task
        """
        
        # Controlla cache se non force refresh
        cache_key = f"requirements_{workspace_id}"
        if not force_refresh and cache_key in self.cache:
            logger.info(f"📋 REQUIREMENTS: Using cached analysis for {workspace_id}")
            return self.cache[cache_key]
        
        try:
            # Recupera dati workspace dal sistema esistente
            workspace = await get_workspace(workspace_id)
            if not workspace:
                raise ValueError(f"Workspace {workspace_id} non trovato")
            
            # Raccogli context completo
            context = await self._gather_workspace_context(workspace_id)
            
            # Analisi AI dinamica
            requirements = await self._ai_analyze_requirements(
                workspace.get("goal", ""), context
            )
            
            # Valida e migliora requirements
            validated_requirements = await self._validate_and_enhance_requirements(
                requirements, context
            )
            
            # Cache result
            self.cache[cache_key] = validated_requirements
            
            logger.info(f"📋 REQUIREMENTS: Generated for {workspace_id} - "
                       f"Category: {validated_requirements.deliverable_category}, "
                       f"Assets: {len(validated_requirements.primary_assets_needed)}")
            
            return validated_requirements
            
        except Exception as e:
            logger.error(f"Error analyzing deliverable requirements: {e}", exc_info=True)
            # Fallback a requirements generici
            return self._create_fallback_requirements(workspace_id, workspace.get("goal", ""))
    
    async def _gather_workspace_context(self, workspace_id: str) -> Dict[str, Any]:
        """Raccoglie context completo dal workspace usando il sistema esistente"""
        
        try:
            # Dati base
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)
            agents = await list_agents(workspace_id)
            
            # Analisi task per fase (integrato con ProjectPhase esistente)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            phase_analysis = self._analyze_phase_progress(completed_tasks)
            
            # Analisi competenze team
            team_capabilities = self._analyze_team_capabilities(agents)
            
            # Analisi output esistenti
            existing_outputs = self._analyze_existing_outputs(completed_tasks)
            
            context = {
                "workspace_goal": workspace.get("goal", ""),
                "workspace_status": workspace.get("status", ""),
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "phase_progress": phase_analysis,
                "team_capabilities": team_capabilities,
                "existing_outputs": existing_outputs,
                "budget_info": workspace.get("budget", {}),
                "timeline_pressure": self._assess_timeline_pressure(tasks)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering workspace context: {e}")
            return {"workspace_goal": "", "error": str(e)}
    
    def _analyze_phase_progress(self, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """Analizza il progresso per fase (integrato con ProjectPhase)"""
        
        phase_counts = {"ANALYSIS": 0, "IMPLEMENTATION": 0, "FINALIZATION": 0}
        phase_outputs = {"ANALYSIS": [], "IMPLEMENTATION": [], "FINALIZATION": []}
        
        for task in completed_tasks:
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                phase = context_data.get("project_phase", "ANALYSIS").upper()
                if phase in phase_counts:
                    phase_counts[phase] += 1
                    
                    # Raccogli sample output per analisi
                    result = task.get("result", {})
                    if result.get("summary"):
                        phase_outputs[phase].append({
                            "task_name": task.get("name", ""),
                            "summary": result.get("summary", "")[:200]
                        })
        
        return {
            "phase_distribution": phase_counts,
            "current_phase": self._determine_current_phase(phase_counts),
            "phase_outputs_sample": phase_outputs
        }
    
    def _determine_current_phase(self, phase_counts: Dict) -> str:
        """Determina la fase attuale basata sui task completati"""
        
        if phase_counts["FINALIZATION"] >= 2:
            return "FINALIZATION"
        elif phase_counts["IMPLEMENTATION"] >= 2:
            return "IMPLEMENTATION"
        else:
            return "ANALYSIS"
    
    def _analyze_team_capabilities(self, agents: List[Dict]) -> Dict[str, Any]:
        """🤖 AI-DRIVEN UNIVERSAL team capability analysis"""
        
        capabilities = {
            "roles_available": [],
            "seniority_distribution": {},
            "specialized_skills": [],
            "asset_production_capacity": {}
        }
        
        for agent in agents:
            if agent.get("status") == "available":
                role = agent.get("role", "").lower()
                seniority = agent.get("seniority", "junior")
                
                capabilities["roles_available"].append(role)
                capabilities["seniority_distribution"][seniority] = capabilities["seniority_distribution"].get(seniority, 0) + 1
                
                # 🤖 UNIVERSAL CAPABILITY MAPPING: Based on functional skills, not domain assumptions
                role_capabilities = self._extract_universal_capabilities_from_role(role)
                for capability, enabled in role_capabilities.items():
                    if enabled:
                        capabilities["asset_production_capacity"][capability] = True
        
        return capabilities
    
    def _extract_universal_capabilities_from_role(self, role: str) -> Dict[str, bool]:
        """🤖 Extract universal capabilities from role description without domain assumptions"""
        
        # Universal functional capability patterns
        universal_capabilities = {
            "content_creation": False,     # Can create any type of content
            "data_analysis": False,        # Can analyze and process data
            "automation_setup": False,     # Can set up automated processes
            "strategic_planning": False,   # Can create strategic plans
            "communication_assets": False, # Can create communication materials
            "process_documentation": False # Can document processes
        }
        
        # Universal pattern matching (no business domain assumptions)
        role_lower = role.lower()
        
        # Content creation capability
        if any(keyword in role_lower for keyword in ["content", "writ", "editor", "creativ", "author"]):
            universal_capabilities["content_creation"] = True
            universal_capabilities["communication_assets"] = True
            
        # Data analysis capability  
        if any(keyword in role_lower for keyword in ["analy", "research", "data", "evaluat", "report"]):
            universal_capabilities["data_analysis"] = True
            
        # Automation capability
        if any(keyword in role_lower for keyword in ["technical", "develop", "engineer", "automat", "system"]):
            universal_capabilities["automation_setup"] = True
            
        # Strategic planning capability
        if any(keyword in role_lower for keyword in ["strateg", "plan", "manag", "direct", "lead", "coordin"]):
            universal_capabilities["strategic_planning"] = True
            
        # Communication assets capability
        if any(keyword in role_lower for keyword in ["market", "social", "communic", "promot", "brand", "sales"]):
            universal_capabilities["communication_assets"] = True
            
        # Process documentation capability
        if any(keyword in role_lower for keyword in ["document", "process", "quality", "compliance", "guideline"]):
            universal_capabilities["process_documentation"] = True
        
        return universal_capabilities
    
    def _analyze_existing_outputs(self, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """Analizza gli output esistenti per capire che asset sono già disponibili"""
        
        outputs = {
            "has_structured_data": False,
            "has_contact_data": False,
            "has_content_ideas": False,
            "has_strategic_plans": False,
            "output_quality_indicators": []
        }
        
        for task in completed_tasks:
            result = task.get("result", {})
            detailed_json = result.get("detailed_results_json", "")
            summary = result.get("summary", "")
            
            # Analisi contenuto per identificare tipi di asset
            if detailed_json:
                outputs["has_structured_data"] = True
                
                # Pattern matching per tipi specifici
                json_lower = detailed_json.lower()
                if any(keyword in json_lower for keyword in ["contact", "email", "phone", "lead"]):
                    outputs["has_contact_data"] = True
                if any(keyword in json_lower for keyword in ["content", "post", "caption", "calendar"]):
                    outputs["has_content_ideas"] = True
                if any(keyword in json_lower for keyword in ["strategy", "plan", "framework", "approach"]):
                    outputs["has_strategic_plans"] = True
            
            # Quality indicators
            if len(summary) > 100:
                outputs["output_quality_indicators"].append("detailed_summaries")
            if detailed_json and len(detailed_json) > 200:
                outputs["output_quality_indicators"].append("rich_structured_data")
        
        return outputs
    
    def _assess_timeline_pressure(self, tasks: List[Dict]) -> str:
        """Valuta la pressione temporale del progetto"""
        
        # Analisi basata su pattern temporali
        pending_count = len([t for t in tasks if t.get("status") == "pending"])
        
        if pending_count > 10:
            return "high"
        elif pending_count > 5:
            return "medium"
        else:
            return "low"
    
    async def _ai_analyze_requirements(self, goal: str, context: Dict) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN UNIVERSAL REQUIREMENTS ANALYSIS
        
        Analyzes requirements dynamically without domain-specific assumptions
        """
        
        # Try AI-driven analysis first if available
        if QUALITY_CONFIG_AVAILABLE:
            try:
                ai_requirements = await self._ai_driven_requirements_analysis(goal, context)
                if ai_requirements:
                    return ai_requirements
            except Exception as e:
                logger.debug(f"AI requirements analysis failed, using fallback: {e}")
        
        # Fallback: Universal functional analysis
        return await self._universal_requirements_fallback(goal, context)
    
    async def _ai_driven_requirements_analysis(self, goal: str, context: Dict) -> Dict[str, Any]:
        """🤖 AI-driven requirements analysis without domain assumptions"""
        try:
            # Check if we have AI capabilities
            import os
            if not os.getenv("OPENAI_API_KEY"):
                return {}
            
            from ai_quality_assurance.quality_validator import AIQualityValidator
            ai_validator = AIQualityValidator()
            
            team_capabilities = context.get("team_capabilities", {})
            phase_progress = context.get("phase_progress", {})
            
            analysis_prompt = f"""Analyze this project goal and determine what types of deliverable assets would be most valuable:

PROJECT GOAL: "{goal}"

TEAM CAPABILITIES: {team_capabilities.get('asset_production_capacity', {})}
PROJECT PHASE: {phase_progress.get('current_phase', 'ANALYSIS')}
COMPLETED TASKS: {context.get('completed_tasks', 0)}

Based on the goal and context, determine:
1. What functional category best describes this project (e.g., "content_strategy", "data_analysis", "process_optimization", "communication_plan")
2. What 2-4 specific asset types would deliver the most value (be specific about format and purpose)
3. Priority level for each asset (1=highest, 2=medium, 3=supporting)

Return ONLY a JSON object in this format:
{{
  "functional_category": "category_name",
  "recommended_assets": [
    {{
      "asset_type": "specific_asset_name",
      "asset_format": "structured_data|document|spreadsheet",
      "purpose": "what this asset accomplishes",
      "priority": 1,
      "business_impact": "immediate|short_term|strategic"
    }}
  ]
}}"""

            ai_result = await ai_validator._call_openai_api(analysis_prompt, "requirements_analysis")
            if ai_result and "raw_response" in ai_result:
                try:
                    parsed_requirements = json.loads(ai_result["raw_response"])
                    if isinstance(parsed_requirements, dict) and parsed_requirements.get("recommended_assets"):
                        # Convert to expected format
                        assets = []
                        for asset in parsed_requirements["recommended_assets"]:
                            assets.append({
                                "asset_type": asset.get("asset_type", "general_deliverable"),
                                "asset_format": asset.get("asset_format", "document"),
                                "actionability_level": "ready_to_use",
                                "business_impact": asset.get("business_impact", "immediate"),
                                "priority": asset.get("priority", 2),
                                "validation_criteria": ["completeness", "actionability", "relevance"]
                            })
                        
                        return {
                            "deliverable_category": parsed_requirements.get("functional_category", "business"),
                            "primary_assets_needed": assets,
                            "deliverable_structure": self._create_universal_deliverable_structure(assets)
                        }
                except json.JSONDecodeError:
                    logger.debug("AI returned non-JSON response for requirements analysis")
        except Exception as e:
            logger.debug(f"AI requirements analysis error: {e}")
        
        return {}
    
    async def _universal_requirements_fallback(self, goal: str, context: Dict) -> Dict[str, Any]:
        """🔄 UNIVERSAL FALLBACK: Functional analysis without domain assumptions"""
        
        goal_lower = goal.lower()
        team_capabilities = context.get("team_capabilities", {}).get("asset_production_capacity", {})
        
        # Universal functional categorization based on action patterns
        if any(pattern in goal_lower for pattern in ["create", "develop", "build", "design", "generate"]):
            category = "creation_project"
            assets = self._generate_creation_assets(goal, context, team_capabilities)
        elif any(pattern in goal_lower for pattern in ["analyze", "research", "study", "investigate", "evaluate"]):
            category = "analysis_project"
            assets = self._generate_analysis_assets(goal, context, team_capabilities)
        elif any(pattern in goal_lower for pattern in ["optimize", "improve", "enhance", "increase", "boost"]):
            category = "optimization_project"
            assets = self._generate_optimization_assets(goal, context, team_capabilities)
        elif any(pattern in goal_lower for pattern in ["plan", "strategy", "framework", "roadmap", "approach"]):
            category = "strategic_project"
            assets = self._generate_strategic_assets(goal, context, team_capabilities)
        else:
            category = "general_project"
            assets = self._generate_general_assets(goal, context, team_capabilities)
        
        return {
            "deliverable_category": category,
            "primary_assets_needed": assets,
            "deliverable_structure": self._create_universal_deliverable_structure(assets)
        }
    
    def _create_universal_deliverable_structure(self, assets: List[Dict]) -> Dict[str, Any]:
        """Create universal deliverable structure based on assets"""
        return {
            "executive_summary": "required",
            "actionable_assets": {asset["asset_type"]: asset for asset in assets},
            "usage_guide": "required",
            "implementation_notes": "optional",
            "next_steps": "required"
        }
    
    def _generate_creation_assets(self, goal: str, context: Dict, capabilities: Dict) -> List[Dict]:
        """🤖 Generate assets for creation-focused projects (universal)"""
        assets = []
        
        # Primary creation asset based on capabilities
        if capabilities.get("content_creation"):
            assets.append({
                "asset_type": "content_creation_plan",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "immediate",
                "priority": 1,
                "validation_criteria": ["creation_schedule", "content_specifications", "quality_standards"]
            })
        
        if capabilities.get("automation_setup"):
            assets.append({
                "asset_type": "creation_workflow",
                "asset_format": "structured_data", 
                "actionability_level": "ready_to_use",
                "business_impact": "short_term",
                "priority": 2,
                "validation_criteria": ["workflow_steps", "automation_triggers", "quality_checks"]
            })
        
        # Always include implementation guide
        assets.append({
            "asset_type": "implementation_guide",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["step_by_step", "success_criteria", "troubleshooting"]
        })
        
        return assets
    
    def _generate_analysis_assets(self, goal: str, context: Dict, capabilities: Dict) -> List[Dict]:
        """🤖 Generate assets for analysis-focused projects (universal)"""
        assets = []
        
        # Core analysis deliverable
        assets.append({
            "asset_type": "analysis_report",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "strategic",
            "priority": 1,
            "validation_criteria": ["data_sources_credible", "methodology_clear", "actionable_insights"]
        })
        
        if capabilities.get("data_analysis"):
            assets.append({
                "asset_type": "data_summary_dashboard",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "immediate",
                "priority": 1,
                "validation_criteria": ["key_metrics", "trend_analysis", "visualization_ready"]
            })
        
        # Recommendations based on analysis
        assets.append({
            "asset_type": "actionable_recommendations", 
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["evidence_based", "implementation_timeline", "success_metrics"]
        })
        
        return assets
    
    def _generate_optimization_assets(self, goal: str, context: Dict, capabilities: Dict) -> List[Dict]:
        """🤖 Generate assets for optimization-focused projects (universal)"""
        assets = []
        
        # Optimization plan
        assets.append({
            "asset_type": "optimization_plan",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["improvement_targets", "implementation_steps", "success_metrics"]
        })
        
        if capabilities.get("process_documentation"):
            assets.append({
                "asset_type": "process_improvement_guide",
                "asset_format": "document",
                "actionability_level": "ready_to_use",
                "business_impact": "short_term",
                "priority": 2,
                "validation_criteria": ["current_state_analysis", "improvement_recommendations", "implementation_roadmap"]
            })
        
        if capabilities.get("automation_setup"):
            assets.append({
                "asset_type": "automation_recommendations",
                "asset_format": "structured_data",
                "actionability_level": "needs_customization",
                "business_impact": "strategic",
                "priority": 2,
                "validation_criteria": ["automation_opportunities", "technical_requirements", "roi_estimates"]
            })
        
        return assets
    
    def _generate_strategic_assets(self, goal: str, context: Dict, capabilities: Dict) -> List[Dict]:
        """🤖 Generate assets for strategic-focused projects (universal)"""
        assets = []
        
        # Core strategic plan
        assets.append({
            "asset_type": "strategic_plan",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "strategic",
            "priority": 1,
            "validation_criteria": ["clear_objectives", "implementation_timeline", "resource_requirements"]
        })
        
        if capabilities.get("strategic_planning"):
            assets.append({
                "asset_type": "execution_roadmap",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "immediate",
                "priority": 1,
                "validation_criteria": ["milestone_definition", "resource_allocation", "risk_mitigation"]
            })
        
        # Success measurement framework
        assets.append({
            "asset_type": "success_measurement_framework",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "short_term",
            "priority": 2,
            "validation_criteria": ["kpi_definition", "measurement_methods", "reporting_schedule"]
        })
        
        return assets
    
    def _generate_general_assets(self, goal: str, context: Dict, capabilities: Dict) -> List[Dict]:
        """🤖 Generate universal assets for general projects"""
        assets = []
        
        # Universal action plan
        assets.append({
            "asset_type": "action_plan",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["tasks_defined", "timeline_realistic", "resources_allocated"]
        })
        
        # Implementation support
        assets.append({
            "asset_type": "implementation_guide",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["step_by_step", "success_criteria", "troubleshooting"]
        })
        
        # Progress tracking if data analysis capability exists
        if capabilities.get("data_analysis"):
            assets.append({
                "asset_type": "progress_tracking_system",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "short_term",
                "priority": 2,
                "validation_criteria": ["measurable_kpis", "tracking_methods", "reporting_format"]
            })
        
        return assets
    
    async def _validate_and_enhance_requirements(
        self, 
        requirements: Dict, 
        context: Dict
    ) -> DeliverableRequirements:
        """Valida e migliora i requirements generati"""
        
        # Converti in oggetti Pydantic per validazione
        asset_requirements = []
        for asset_data in requirements.get("primary_assets_needed", []):
            asset_req = AssetRequirement(**asset_data)
            asset_requirements.append(asset_req)
        
        # Ordina per priorità
        asset_requirements.sort(key=lambda x: x.priority)
        
        # Crea oggetto finale
        validated = DeliverableRequirements(
            workspace_id=context.get("workspace_id", ""),
            deliverable_category=requirements.get("deliverable_category", "business"),
            primary_assets_needed=asset_requirements,
            deliverable_structure=requirements.get("deliverable_structure", {}),
            generated_at=datetime.now()
        )
        
        return validated
    
    def _create_fallback_requirements(self, workspace_id: str, goal: str) -> DeliverableRequirements:
        """Crea requirements di fallback in caso di errore"""
        
        fallback_assets = [
            AssetRequirement(
                asset_type="comprehensive_report",
                asset_format="document",
                actionability_level="ready_to_use",
                business_impact="immediate",
                priority=1,
                validation_criteria=["executive_summary", "key_findings", "next_steps"]
            )
        ]
        
        return DeliverableRequirements(
            workspace_id=workspace_id,
            deliverable_category="business",
            primary_assets_needed=fallback_assets,
            deliverable_structure={"executive_summary": "required"},
            generated_at=datetime.now()
        )

# 🤖 AI-DRIVEN UNIVERSAL FUNCTION DETECTION
# No longer using hard-coded domain registry - replaced with functional analysis

def detect_functional_category_from_goal(goal: str) -> str:
    """🤖 Detect functional category from goal using universal patterns"""
    goal_lower = goal.lower()
    
    # Universal functional patterns (not domain-specific)
    functional_patterns = {
        "creation_project": ["create", "develop", "build", "design", "generate", "produce"],
        "analysis_project": ["analyze", "research", "study", "investigate", "evaluate", "assess"],
        "optimization_project": ["optimize", "improve", "enhance", "increase", "boost", "streamline"],
        "strategic_project": ["plan", "strategy", "framework", "roadmap", "approach", "vision"],
        "communication_project": ["communicate", "present", "share", "engage", "connect", "outreach"],
        "automation_project": ["automate", "systematize", "workflow", "process", "integrate"]
    }
    
    # Find the best functional match
    for category, keywords in functional_patterns.items():
        if any(keyword in goal_lower for keyword in keywords):
            return category
    
    return "general_project"  # Universal fallback

def get_supported_functional_categories() -> Dict[str, List[str]]:
    """Return supported functional categories with their patterns"""
    return {
        "creation_project": ["create", "develop", "build", "design", "generate"],
        "analysis_project": ["analyze", "research", "study", "investigate", "evaluate"],
        "optimization_project": ["optimize", "improve", "enhance", "increase", "boost"],
        "strategic_project": ["plan", "strategy", "framework", "roadmap", "approach"],
        "communication_project": ["communicate", "present", "share", "engage", "connect"],
        "automation_project": ["automate", "systematize", "workflow", "process", "integrate"],
        "general_project": ["execute", "complete", "deliver", "implement", "achieve"]
    }