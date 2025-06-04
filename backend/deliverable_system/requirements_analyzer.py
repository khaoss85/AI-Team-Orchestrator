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
    QualitySystemConfig, QUALITY_CONFIG_AVAILABLE = load_quality_system_config()
    logger = logging.getLogger(__name__)
    if QUALITY_CONFIG_AVAILABLE:
        logger.info("✅ QualitySystemConfig loaded successfully via centralized loader")
    else:
        logger.warning("⚠️ QualitySystemConfig using fallback configuration")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("❌ Critical: Could not load quality config loader - system may be unstable")
    QUALITY_CONFIG_AVAILABLE = False
    
    # Emergency fallback
    class QualitySystemConfig:
        QUALITY_SCORE_THRESHOLD = 0.8
        ACTIONABILITY_THRESHOLD = 0.7
        AUTHENTICITY_THRESHOLD = 0.8
        COMPLETENESS_THRESHOLD = 0.7
        ENABLE_AI_QUALITY_EVALUATION = True

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
        """Analizza le capacità del team per determinare che asset possono produrre"""
        
        capabilities = {
            "roles_available": [],
            "seniority_distribution": {},
            "specialized_skills": [],
            "asset_production_capacity": {}
        }
        
        for agent in agents:
            if agent.get("status") == "active":
                role = agent.get("role", "").lower()
                seniority = agent.get("seniority", "junior")
                
                capabilities["roles_available"].append(role)
                capabilities["seniority_distribution"][seniority] = capabilities["seniority_distribution"].get(seniority, 0) + 1
                
                # Mappping ruoli -> capacità di produzione asset
                if any(keyword in role for keyword in ["content", "marketing", "social"]):
                    capabilities["asset_production_capacity"]["content_assets"] = True
                if any(keyword in role for keyword in ["analysis", "research", "data"]):
                    capabilities["asset_production_capacity"]["data_assets"] = True
                if any(keyword in role for keyword in ["technical", "developer", "automation"]):
                    capabilities["asset_production_capacity"]["automation_assets"] = True
                if any(keyword in role for keyword in ["sales", "business", "lead"]):
                    capabilities["asset_production_capacity"]["business_assets"] = True
        
        return capabilities
    
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
        Analisi AI per determinare requirements dinamici
        NOTA: In implementazione reale, questa userebbe chiamate LLM
        Per ora, logica rule-based intelligente
        """
        
        # Analisi del goal per categoria principale
        goal_lower = goal.lower()
        
        # Mapping intelligente goal -> categoria
        if any(keyword in goal_lower for keyword in ["instagram", "social", "content", "marketing", "campaign"]):
            category = "marketing"
            assets = self._generate_marketing_assets(goal, context)
        elif any(keyword in goal_lower for keyword in ["lead", "contact", "sales", "prospect", "business"]):
            category = "sales"
            assets = self._generate_sales_assets(goal, context)
        elif any(keyword in goal_lower for keyword in ["fitness", "training", "sport", "athletic", "performance"]):
            category = "sports"
            assets = self._generate_sports_assets(goal, context)
        elif any(keyword in goal_lower for keyword in ["finance", "budget", "investment", "financial", "cost"]):
            category = "finance"
            assets = self._generate_finance_assets(goal, context)
        elif any(keyword in goal_lower for keyword in ["analysis", "research", "study", "data", "report"]):
            category = "research"
            assets = self._generate_research_assets(goal, context)
        else:
            category = "business"
            assets = self._generate_business_assets(goal, context)
        
        # Struttura del deliverable dinamica
        deliverable_structure = {
            "executive_summary": "required",
            "actionable_assets": {asset["asset_type"]: asset for asset in assets},
            "usage_guide": "required",
            "automation_instructions": "optional",
            "next_steps": "required"
        }
        
        return {
            "deliverable_category": category,
            "primary_assets_needed": assets,
            "deliverable_structure": deliverable_structure
        }
    
    def _generate_marketing_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements per progetti marketing"""
        
        assets = []
        
        # Asset sempre richiesti per marketing
        assets.append({
            "asset_type": "content_calendar",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["posts_with_dates", "complete_captions", "hashtags_included"]
        })
        
        # Asset condizionali basati su context
        if context.get("team_capabilities", {}).get("asset_production_capacity", {}).get("data_assets"):
            assets.append({
                "asset_type": "audience_analysis_report",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "strategic",
                "priority": 2,
                "validation_criteria": ["demographic_data", "behavior_insights", "recommendations"]
            })
        
        if "instagram" in goal.lower():
            assets.append({
                "asset_type": "instagram_growth_strategy",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "short_term",
                "priority": 1,
                "validation_criteria": ["posting_schedule", "engagement_tactics", "hashtag_strategy"]
            })
        
        return assets
    
    def _generate_sales_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements per progetti sales"""
        
        assets = []
        
        assets.append({
            "asset_type": "qualified_contact_database",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use", 
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["contact_info_complete", "qualification_scores", "next_actions"]
        })
        
        assets.append({
            "asset_type": "outreach_email_templates",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["personalization_fields", "call_to_action", "follow_up_sequence"]
        })
        
        return assets
    
    def _generate_sports_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements per progetti sports"""
        
        assets = []
        
        if "training" in goal.lower():
            assets.append({
                "asset_type": "training_program",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "immediate",
                "priority": 1,
                "validation_criteria": ["exercise_details", "progression_plan", "performance_metrics"]
            })
        
        assets.append({
            "asset_type": "performance_tracking_system",
            "asset_format": "structured_data",
            "actionability_level": "needs_customization",
            "business_impact": "short_term",
            "priority": 2,
            "validation_criteria": ["measurable_kpis", "tracking_methods", "improvement_targets"]
        })
        
        return assets
    
    def _generate_finance_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements per progetti finance"""
        
        assets = []
        
        assets.append({
            "asset_type": "financial_model",
            "asset_format": "spreadsheet",
            "actionability_level": "ready_to_use",
            "business_impact": "strategic",
            "priority": 1,
            "validation_criteria": ["formulas_correct", "scenario_analysis", "assumptions_clear"]
        })
        
        if "budget" in goal.lower():
            assets.append({
                "asset_type": "budget_allocation_plan",
                "asset_format": "structured_data",
                "actionability_level": "ready_to_use",
                "business_impact": "immediate",
                "priority": 1,
                "validation_criteria": ["category_breakdown", "timeline_aligned", "approval_workflow"]
            })
        
        return assets
    
    def _generate_research_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements per progetti research"""
        
        assets = []
        
        assets.append({
            "asset_type": "research_database",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "strategic",
            "priority": 1,
            "validation_criteria": ["data_sources_credible", "analysis_methodology", "actionable_insights"]
        })
        
        assets.append({
            "asset_type": "executive_recommendations",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "strategic",
            "priority": 1,
            "validation_criteria": ["evidence_based", "implementation_timeline", "success_metrics"]
        })
        
        return assets
    
    def _generate_business_assets(self, goal: str, context: Dict) -> List[Dict]:
        """Genera asset requirements generici per progetti business"""
        
        assets = []
        
        assets.append({
            "asset_type": "action_plan",
            "asset_format": "structured_data",
            "actionability_level": "ready_to_use",
            "business_impact": "immediate",
            "priority": 1,
            "validation_criteria": ["tasks_defined", "timeline_realistic", "resources_allocated"]
        })
        
        assets.append({
            "asset_type": "implementation_guide",
            "asset_format": "document",
            "actionability_level": "ready_to_use",
            "business_impact": "short_term",
            "priority": 2,
            "validation_criteria": ["step_by_step", "success_criteria", "troubleshooting"]
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