# backend/ai_quality_assurance/enhancement_orchestrator.py
import logging
import json
import os
import asyncio 
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import asyncio 

# FIXED: Aggiunti import mancanti
from pydantic import BaseModel, Field

# FIXED: Import corretto per il codebase
from ai_quality_assurance.quality_validator import QualityAssessment, QualityIssueType
from ai_quality_assurance.ai_evaluator import EnhancedAIQualityValidator
from database import create_task, list_agents, list_tasks, update_task_status
from models import TaskStatus

logger = logging.getLogger(__name__)

# ENHANCED: Configurazioni da environment per production
ENHANCEMENT_EFFORT_ESTIMATION = {
    "contact_database": float(os.getenv("CONTACT_DB_EFFORT_HOURS", "3.0")),
    "content_calendar": float(os.getenv("CONTENT_CAL_EFFORT_HOURS", "2.5")),
    "training_program": float(os.getenv("TRAINING_PROG_EFFORT_HOURS", "4.0")),
    "financial_model": float(os.getenv("FINANCIAL_MODEL_EFFORT_HOURS", "3.5")),
    "research_database": float(os.getenv("RESEARCH_DB_EFFORT_HOURS", "3.0")),
    "default": float(os.getenv("DEFAULT_ENHANCEMENT_EFFORT_HOURS", "2.5"))
}

ENHANCEMENT_PRIORITY_THRESHOLDS = {
    "critical_ratio": float(os.getenv("CRITICAL_ASSETS_THRESHOLD", "0.4")),
    "fake_content_ratio": float(os.getenv("FAKE_CONTENT_THRESHOLD", "0.6")),
    "generic_structure_ratio": float(os.getenv("GENERIC_STRUCTURE_THRESHOLD", "0.5"))
}

class EnhancementPlan(BaseModel):
    """Piano di miglioramento per un asset - PRODUCTION VERSION"""
    asset_id: str
    asset_name: str
    current_quality_score: float
    target_quality_score: float = Field(default=0.8, ge=0.0, le=1.0)
    
    enhancement_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_effort_hours: float = Field(default=2.5, ge=0.5, le=10.0)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")  # FIXED: regex -> pattern
    
    quality_issues: List[QualityIssueType]
    improvement_actions: List[str]
    
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|failed)$")  # FIXED: regex -> pattern
    
    # ENHANCED: Tracking per production
    workspace_id: Optional[str] = None
    total_assets_in_deliverable: Optional[int] = None
    enhancement_strategy: Optional[str] = None

class AssetEnhancementOrchestrator:
    """
    PRODUCTION-READY: Orchestratore che coordina il miglioramento degli asset
    con configurazioni dinamiche e error handling robusto
    """
    
    def __init__(self):
        self.validator = EnhancedAIQualityValidator()
        self.enhancement_plans: Dict[str, EnhancementPlan] = {}
        
        # ENHANCED: Asset expertise mapping più completo e configurabile
        self.asset_expertise_mapping = self._load_asset_expertise_mapping()
        self._tracking_lock = asyncio.Lock()
        self.phase_planning_tracker: Dict[str, Set[str]] = defaultdict(set)
        
        # ENHANCED: Tracking per monitoring
        self.orchestration_count = 0
        self.total_assets_analyzed = 0
        self.total_enhancements_created = 0
        
        logger.info("🔧 AssetEnhancementOrchestrator initialized with Enhanced AI Quality Validator")
        
    def _load_asset_expertise_mapping(self) -> Dict[str, Dict[str, Any]]:
        """ENHANCED: Carica mapping expertise dinamico"""
        
        return {
            "contact_database": {
                "primary_roles": ["analysis", "research", "data", "sales"],
                "secondary_roles": ["business", "marketing"],
                "expertise_keywords": ["contact", "lead", "crm", "database", "research"],
                "complexity_multiplier": 1.2
            },
            "content_calendar": {
                "primary_roles": ["content", "marketing", "social"],
                "secondary_roles": ["creative", "writer", "digital"],
                "expertise_keywords": ["content", "social", "calendar", "marketing", "creative"],
                "complexity_multiplier": 1.0
            },
            "training_program": {
                "primary_roles": ["fitness", "coach", "trainer", "sports"],
                "secondary_roles": ["wellness", "health", "specialist"],
                "expertise_keywords": ["training", "fitness", "exercise", "coach", "sports"],
                "complexity_multiplier": 1.5
            },
            "financial_model": {
                "primary_roles": ["finance", "analyst", "business"],
                "secondary_roles": ["strategy", "economics", "data"],
                "expertise_keywords": ["financial", "finance", "budget", "model", "analysis"],
                "complexity_multiplier": 1.8
            },
            "research_database": {
                "primary_roles": ["research", "analyst", "data"],
                "secondary_roles": ["academic", "science", "intelligence"],
                "expertise_keywords": ["research", "data", "analysis", "academic", "intelligence"],
                "complexity_multiplier": 1.4
            },
            "strategy_framework": {
                "primary_roles": ["strategy", "business", "consultant"],
                "secondary_roles": ["manager", "analyst", "planning"],
                "expertise_keywords": ["strategy", "framework", "business", "planning"],
                "complexity_multiplier": 1.3
            }
        }
    
    async def analyze_and_enhance_deliverable_assets(
        self, 
        workspace_id: str, 
        actionable_deliverable: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ENHANCED: Analizza tutti gli asset con error handling robusto e monitoring
        """
        
        start_time = datetime.now()
        self.orchestration_count += 1
        
        try:
            logger.info(f"🔍 QUALITY ANALYSIS: Starting orchestration #{self.orchestration_count} for workspace {workspace_id}")
            
            # Validazione input
            if not actionable_deliverable or not isinstance(actionable_deliverable, dict):
                raise ValueError("Invalid actionable_deliverable provided")
            
            # Estrai asset dal deliverable
            actionable_assets = actionable_deliverable.get("actionable_assets", {})
            workspace_goal = actionable_deliverable.get("meta", {}).get("project_goal", "")
            
            if not actionable_assets:
                logger.warning(f"No actionable assets found in deliverable for {workspace_id}")
                return self._add_quality_metadata(actionable_deliverable, {}, {})
            
            self.total_assets_analyzed += len(actionable_assets)
            
            # Analizza qualità di ogni asset con batch processing
            quality_reports = {}
            assets_needing_enhancement = []
            
            logger.info(f"📊 ANALYZING: {len(actionable_assets)} assets for quality")
            
            for asset_id, asset_obj in actionable_assets.items():
                try:
                    quality_assessment = await self._analyze_single_asset_quality(
                        asset_id, asset_obj, workspace_goal, workspace_id
                    )
                    
                    quality_reports[asset_id] = quality_assessment
                    
                    # Determina se necessita enhancement
                    if quality_assessment.needs_enhancement:
                        assets_needing_enhancement.append({
                            "asset_id": asset_id,
                            "asset_obj": asset_obj,
                            "quality_assessment": quality_assessment
                        })
                        
                        logger.warning(f"🔧 NEEDS ENHANCEMENT: {quality_assessment.asset_name} "
                                     f"(score: {quality_assessment.overall_score:.2f}, "
                                     f"issues: {len(quality_assessment.quality_issues)})")
                    else:
                        logger.info(f"✅ QUALITY OK: {quality_assessment.asset_name} "
                                   f"(score: {quality_assessment.overall_score:.2f})")
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing asset {asset_id}: {e}", exc_info=True)
                    # Crea assessment fallback
                    quality_reports[asset_id] = self._create_fallback_assessment(asset_id, str(e))
                    continue
            
            # Orchestra enhancement se necessario
            enhancement_results = {}
            if assets_needing_enhancement:
                logger.info(f"🚀 ORCHESTRATING: {len(assets_needing_enhancement)} assets need improvement")
                
                enhancement_results = await self._orchestrate_asset_enhancement_robust(
                    workspace_id, assets_needing_enhancement, workspace_goal, actionable_deliverable
                )
                
                self.total_enhancements_created += len(enhancement_results)
            
            # Aggiorna deliverable con risultati
            enhanced_deliverable = self._add_quality_metadata(
                actionable_deliverable, quality_reports, enhancement_results
            )
            
            # Log finale con statistiche
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"🔍 QUALITY ANALYSIS COMPLETE: {workspace_id} ({execution_time:.1f}s)")
            logger.info(f"  ├─ Assets analyzed: {len(actionable_assets)}")
            logger.info(f"  ├─ High quality: {len([q for q in quality_reports.values() if not q.needs_enhancement])}")
            logger.info(f"  ├─ Need enhancement: {len(assets_needing_enhancement)}")
            logger.info(f"  └─ Enhancement tasks created: {len(enhancement_results)}")
            
            return enhanced_deliverable
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in orchestration: {e}", exc_info=True)
            # Return original deliverable with error metadata
            return self._add_error_metadata(actionable_deliverable, str(e))
    
    async def _analyze_single_asset_quality(
        self, 
        asset_id: str, 
        asset_obj: Dict, 
        workspace_goal: str, 
        workspace_id: str
    ) -> QualityAssessment:
        """ENHANCED: Analizza qualità di un singolo asset con retry logic"""
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                asset_data = asset_obj.get("asset_data", {})
                asset_name = asset_obj.get("asset_name", f"asset_{asset_id}")
                
                # Validazione asset data
                if not asset_data or not isinstance(asset_data, dict):
                    logger.warning(f"Invalid asset data for {asset_id}")
                    return self._create_fallback_assessment(asset_id, "Invalid asset data structure")
                
                # Valuta qualità con AI
                quality_assessment = await self.validator.validate_asset_quality(
                    asset_data, 
                    asset_name,
                    {
                        "workspace_goal": workspace_goal, 
                        "workspace_id": workspace_id,
                        "asset_id": asset_id
                    }
                )
                
                return quality_assessment
                
            except Exception as e:
                logger.warning(f"Quality analysis attempt {attempt + 1} failed for {asset_id}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for asset {asset_id}")
                    return self._create_fallback_assessment(asset_id, f"Analysis failed: {e}")
                
                # Exponential backoff
                await asyncio.sleep(base_delay * (2 ** attempt))
        
        # Questo non dovrebbe mai essere raggiunto
        return self._create_fallback_assessment(asset_id, "Unexpected analysis failure")
    
    def _create_fallback_assessment(self, asset_id: str, error_reason: str) -> QualityAssessment:
        """Crea assessment di fallback per errori"""
        
        return QualityAssessment(
            overall_score=0.1,
            actionability_score=0.1,
            authenticity_score=0.1,
            completeness_score=0.1,
            quality_issues=[QualityIssueType.INCOMPLETE_DATA],
            issue_details={"analysis_error": error_reason},
            improvement_suggestions=[f"Manual review required for asset {asset_id}"],
            enhancement_priority="critical",
            ready_for_use=False,
            needs_enhancement=True,
            ai_model_used="fallback",
            validation_cost=0.0
        )
    
    async def _orchestrate_asset_enhancement_robust(
        self, 
        workspace_id: str, 
        assets_needing_enhancement: List[Dict],
        workspace_goal: str,
        actionable_deliverable: Dict
    ) -> Dict[str, Any]:
        """ENHANCED: Orchestra enhancement con error handling robusto"""
        
        enhancement_results = {}
        
        try:
            # Trova Project Manager con fallback
            pm_agent = await self._find_project_manager_robust(workspace_id)
            if not pm_agent:
                logger.error(f"❌ CRITICAL: No Project Manager found for enhancement in {workspace_id}")
                return enhancement_results
            
            # Crea piano di enhancement con effort estimation dinamico
            overall_plan = await self._create_comprehensive_enhancement_plan(
                assets_needing_enhancement, workspace_goal, actionable_deliverable
            )
            
            # Crea task di coordinamento PM con priorità appropriata
            pm_task_id = await self._create_pm_coordination_task_robust(
                workspace_id, pm_agent, overall_plan, assets_needing_enhancement
            )
            
            if pm_task_id:
                enhancement_results["pm_coordination_task"] = pm_task_id
                logger.info(f"✅ PM Enhancement coordination task created: {pm_task_id}")
            else:
                logger.error(f"❌ Failed to create PM coordination task")
                return enhancement_results
            
            # Crea task specifici per asset critici/high priority
            priority_assets = [
                asset for asset in assets_needing_enhancement
                if asset["quality_assessment"].enhancement_priority in ["critical", "high"]
            ]
            
            logger.info(f"🎯 Creating enhancement tasks for {len(priority_assets)} priority assets")
            
            for asset_info in priority_assets:
                try:
                    enhancement_task_id = await self._create_asset_enhancement_task_robust(
                        workspace_id, asset_info, workspace_goal
                    )
                    
                    if enhancement_task_id:
                        asset_id = asset_info["asset_id"]
                        enhancement_results[f"enhancement_{asset_id}"] = enhancement_task_id
                        logger.info(f"✅ Enhancement task created for {asset_id}: {enhancement_task_id}")
                    else:
                        logger.warning(f"⚠️ Failed to create enhancement task for {asset_info['asset_id']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating enhancement task for {asset_info['asset_id']}: {e}", exc_info=True)
                    continue
            
            return enhancement_results
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in enhancement orchestration: {e}", exc_info=True)
            return enhancement_results
    
    async def _find_project_manager_robust(self, workspace_id: str) -> Optional[Dict]:
        """ENHANCED: Trova Project Manager con logica di fallback robusta"""
        
        try:
            agents = await list_agents(workspace_id)
            if not agents:
                logger.error(f"No agents found in workspace {workspace_id}")
                return None
            
            active_agents = [a for a in agents if a.get("status") == "active"]
            if not active_agents:
                logger.error(f"No active agents in workspace {workspace_id}")
                return None
            
            # Priority 1: Explicit Project Manager
            for agent in active_agents:
                role_lower = (agent.get("role") or "").lower()
                if "project manager" in role_lower:
                    logger.info(f"✅ Found explicit PM: {agent['name']}")
                    return agent
            
            # Priority 2: Management roles
            management_keywords = ["manager", "coordinator", "director", "lead", "pm"]
            for agent in active_agents:
                role_lower = (agent.get("role") or "").lower()
                if any(keyword in role_lower for keyword in management_keywords):
                    logger.info(f"🔧 Using management role as PM: {agent['name']} ({agent['role']})")
                    return agent
            
            # Priority 3: Expert/Senior agents
            senior_agents = [
                a for a in active_agents 
                if a.get("seniority", "").lower() in ["expert", "senior"]
            ]
            if senior_agents:
                # Prefer experts over seniors
                expert_agents = [a for a in senior_agents if a.get("seniority", "").lower() == "expert"]
                selected_agent = expert_agents[0] if expert_agents else senior_agents[0]
                logger.warning(f"⚠️ Using senior agent as PM fallback: {selected_agent['name']}")
                return selected_agent
            
            # Priority 4: Any active agent (last resort)
            fallback_agent = active_agents[0]
            logger.warning(f"⚠️ FALLBACK: Using any agent as PM: {fallback_agent['name']}")
            return fallback_agent
            
        except Exception as e:
            logger.error(f"❌ Error finding project manager: {e}", exc_info=True)
            return None
    
    async def _create_comprehensive_enhancement_plan(
        self, 
        assets_needing_enhancement: List[Dict],
        workspace_goal: str,
        actionable_deliverable: Dict
    ) -> Dict[str, Any]:
        """ENHANCED: Crea piano di enhancement completo con effort estimation dinamico"""
        
        # Analizza distribuzione priorità e issue
        priority_dist = {}
        issue_dist = {}
        total_effort = 0.0
        
        for asset_info in assets_needing_enhancement:
            quality_assessment = asset_info["quality_assessment"]
            asset_name = asset_info["asset_obj"].get("asset_name", "unknown")
            
            # Conta priorità
            priority = quality_assessment.enhancement_priority
            priority_dist[priority] = priority_dist.get(priority, 0) + 1
            
            # Conta issue types
            for issue in quality_assessment.quality_issues:
                issue_type = issue.value
                issue_dist[issue_type] = issue_dist.get(issue_type, 0) + 1
            
            # Calcola effort dinamicamente
            effort = self._estimate_enhancement_effort(asset_name, quality_assessment)
            total_effort += effort
        
        # Determina strategia basata su pattern
        enhancement_strategy = self._determine_enhancement_strategy_robust(
            priority_dist, issue_dist, len(assets_needing_enhancement)
        )
        
        # Analizza contesto deliverable
        deliverable_context = self._analyze_deliverable_context(actionable_deliverable)
        
        return {
            "total_assets": len(assets_needing_enhancement),
            "priority_distribution": priority_dist,
            "common_issues": issue_dist,
            "estimated_effort_hours": round(total_effort, 1),
            "workspace_goal": workspace_goal,
            "enhancement_strategy": enhancement_strategy,
            "deliverable_context": deliverable_context,
            "urgency_level": self._determine_urgency_level(priority_dist, issue_dist),
            "resource_requirements": self._estimate_resource_requirements(assets_needing_enhancement)
        }
    
    def _estimate_enhancement_effort(self, asset_name: str, quality_assessment: QualityAssessment) -> float:
        """ENHANCED: Stima effort dinamicamente basato su asset type e quality issues"""
        
        # Base effort da configurazione
        asset_type = self._determine_asset_type_from_name(asset_name)
        base_effort = ENHANCEMENT_EFFORT_ESTIMATION.get(asset_type, ENHANCEMENT_EFFORT_ESTIMATION["default"])
        
        # Moltiplicatori basati su priorità
        priority_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3,
            "critical": 1.6
        }
        
        priority_multiplier = priority_multipliers.get(quality_assessment.enhancement_priority, 1.0)
        
        # Moltiplicatori basati su numero di issue
        issue_count = len(quality_assessment.quality_issues)
        issue_multiplier = 1.0 + (issue_count * 0.2)  # +20% per ogni issue
        
        # Moltiplicatori basati su score quality
        quality_multiplier = 2.0 - quality_assessment.overall_score  # Lower score = more effort
        
        # Calcola effort finale
        final_effort = base_effort * priority_multiplier * issue_multiplier * quality_multiplier
        
        # Clamp tra 0.5 e 8.0 ore
        return max(0.5, min(8.0, final_effort))
    
    def _determine_asset_type_from_name(self, asset_name: str) -> str:
        """Determina asset type dal nome"""
        
        name_lower = asset_name.lower()
        
        for asset_type in self.asset_expertise_mapping.keys():
            if asset_type.replace("_", " ") in name_lower or asset_type in name_lower:
                return asset_type
        
        return "default"
    
    def _determine_enhancement_strategy_robust(
        self, 
        priority_dist: Dict, 
        issue_dist: Dict,
        total_assets: int
    ) -> str:
        """ENHANCED: Determina strategia usando threshold configurabili"""
        
        if total_assets == 0:
            return "no_enhancement_needed"
        
        # Usa threshold configurabili
        critical_threshold = ENHANCEMENT_PRIORITY_THRESHOLDS["critical_ratio"]
        fake_content_threshold = ENHANCEMENT_PRIORITY_THRESHOLDS["fake_content_ratio"]
        generic_threshold = ENHANCEMENT_PRIORITY_THRESHOLDS["generic_structure_ratio"]
        
        critical_ratio = priority_dist.get("critical", 0) / total_assets
        fake_content_ratio = issue_dist.get("fake_content", 0) / total_assets
        generic_ratio = issue_dist.get("generic_structure", 0) / total_assets
        
        if critical_ratio > critical_threshold:
            return "emergency_enhancement"
        elif fake_content_ratio > fake_content_threshold:
            return "authenticity_focused"
        elif generic_ratio > generic_threshold:
            return "structure_focused"
        elif priority_dist.get("high", 0) > total_assets * 0.5:
            return "quality_focused"
        else:
            return "comprehensive_improvement"
    
    def _analyze_deliverable_context(self, actionable_deliverable: Dict) -> Dict[str, Any]:
        """Analizza contesto del deliverable per migliorare orchestrazione"""
        
        meta = actionable_deliverable.get("meta", {})
        
        return {
            "total_assets_in_deliverable": meta.get("total_assets", 0),
            "ready_to_use_assets": meta.get("ready_to_use_assets", 0),
            "automation_ready": actionable_deliverable.get("automation_ready", False),
            "overall_actionability_score": actionable_deliverable.get("actionability_score", 0),
            "deliverable_creation_method": meta.get("generation_method", "unknown")
        }
    
    def _determine_urgency_level(self, priority_dist: Dict, issue_dist: Dict) -> str:
        """Determina livello di urgenza per l'enhancement"""
        
        if priority_dist.get("critical", 0) > 0:
            return "urgent"
        elif priority_dist.get("high", 0) > priority_dist.get("medium", 0) + priority_dist.get("low", 0):
            return "high"
        elif issue_dist.get("fake_content", 0) > 0 or issue_dist.get("placeholder_data", 0) > 0:
            return "medium"
        else:
            return "low"
    
    def _estimate_resource_requirements(self, assets_needing_enhancement: List[Dict]) -> Dict[str, Any]:
        """Stima requirement di risorse per enhancement"""
        
        required_roles = set()
        estimated_specialists_needed = 0
        
        for asset_info in assets_needing_enhancement:
            asset_name = asset_info["asset_obj"].get("asset_name", "unknown")
            asset_type = self._determine_asset_type_from_name(asset_name)
            
            if asset_type in self.asset_expertise_mapping:
                primary_roles = self.asset_expertise_mapping[asset_type]["primary_roles"]
                required_roles.update(primary_roles)
                estimated_specialists_needed += 1
        
        return {
            "required_specialist_roles": list(required_roles),
            "estimated_specialists_needed": min(estimated_specialists_needed, len(required_roles)),
            "coordination_complexity": "high" if len(required_roles) > 3 else "medium" if len(required_roles) > 1 else "low"
        }
    
    async def _create_pm_coordination_task_robust(
        self, 
        workspace_id: str, 
        pm_agent: Dict, 
        overall_plan: Dict,
        assets_needing_enhancement: List[Dict]
    ) -> Optional[str]:
        """ENHANCED: Crea task PM con error handling e validation"""
        
        try:
            # Validazione input
            if not pm_agent or not pm_agent.get("id"):
                raise ValueError("Invalid PM agent provided")
            
            # Prepara quality summary più dettagliato
            quality_summary = []
            for asset_info in assets_needing_enhancement:
                quality_assessment = asset_info["quality_assessment"]
                asset_name = asset_info["asset_obj"].get("asset_name", "unknown")
                
                quality_summary.append({
                    "asset_name": asset_name,
                    "quality_score": round(quality_assessment.overall_score, 2),
                    "priority": quality_assessment.enhancement_priority,
                    "main_issues": [issue.value for issue in quality_assessment.quality_issues[:3]],
                    "estimated_effort": self._estimate_enhancement_effort(asset_name, quality_assessment),
                    "specialist_needed": self._get_specialist_needed_for_asset(asset_name)
                })
            
            # Crea descrizione task migliorata
            task_description = self._create_enhanced_pm_task_description(
                quality_summary, overall_plan, workspace_id
            )
            
            # Context data esteso
            context_data = {
                "asset_enhancement_coordination": True,
                "project_phase": "FINALIZATION",
                "quality_analysis_results": {
                    "total_assets_analyzed": len(assets_needing_enhancement),
                    "assets_needing_enhancement": len(assets_needing_enhancement),
                    "critical_assets": len([a for a in assets_needing_enhancement 
                                          if a["quality_assessment"].enhancement_priority == "critical"]),
                    "high_priority_assets": len([a for a in assets_needing_enhancement 
                                               if a["quality_assessment"].enhancement_priority == "high"]),
                    "total_estimated_effort": overall_plan["estimated_effort_hours"],
                    "enhancement_strategy": overall_plan["enhancement_strategy"],
                    "urgency_level": overall_plan["urgency_level"]
                },
                "enhancement_coordination": True,
                "pm_coordination_task": True,
                "ai_quality_analysis_version": "2.0_production",
                "orchestrator_version": "1.0_production",
                "created_by_orchestrator": True
            }
            
            # Task name più informativo
            urgency_indicator = "🚨 URGENT" if overall_plan["urgency_level"] == "urgent" else "🔧"
            task_name = f"{urgency_indicator} Asset Quality Enhancement: {len(assets_needing_enhancement)} assets ({overall_plan['estimated_effort_hours']:.1f}h)"
            
            # Determina priorità task basata su urgency
            task_priority = self._determine_task_priority_from_urgency(overall_plan["urgency_level"])
            
            # Crea task
            created_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name=task_name,
                description=task_description,
                status=TaskStatus.PENDING.value,
                priority=task_priority,
                context_data=context_data,
                creation_type="ai_quality_enhancement_coordination"
            )
            
            if created_task and created_task.get("id"):
                logger.info(f"✅ PM coordination task created: {created_task['id']} "
                           f"(Priority: {task_priority}, Effort: {overall_plan['estimated_effort_hours']:.1f}h)")
                return created_task["id"]
            else:
                logger.error("❌ Database returned invalid response for PM task creation")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating PM coordination task: {e}", exc_info=True)
            return None
    
    def _create_enhanced_pm_task_description(
        self, 
        quality_summary: List[Dict], 
        overall_plan: Dict,
        workspace_id: str
    ) -> str:
        """ENHANCED: Crea descrizione task PM più dettagliata"""
        
        urgency_level = overall_plan.get("urgency_level", "medium")
        enhancement_strategy = overall_plan.get("enhancement_strategy", "comprehensive_improvement")
        total_effort = overall_plan.get("estimated_effort_hours", 0)
        
        # Header con urgency indicator
        urgency_section = ""
        if urgency_level == "urgent":
            urgency_section = "🚨 **URGENT QUALITY ISSUES DETECTED** 🚨\n"
        elif urgency_level == "high":
            urgency_section = "⚠️ **HIGH PRIORITY QUALITY ENHANCEMENT REQUIRED** ⚠️\n"
        
        description = f"""{urgency_section}
🔧 **ASSET QUALITY ENHANCEMENT COORDINATION**

**SITUATION**: AI Quality Analysis identified {len(quality_summary)} assets requiring improvement before deliverable completion.

**ENHANCEMENT STRATEGY**: {enhancement_strategy.replace('_', ' ').title()}
**TOTAL ESTIMATED EFFORT**: {total_effort:.1f} hours
**URGENCY LEVEL**: {urgency_level.upper()}

**DETAILED QUALITY ANALYSIS**:
{self._format_detailed_quality_summary_for_pm(quality_summary)}

**YOUR COORDINATION RESPONSIBILITIES**:

1. **Immediate Assessment**: Review AI-identified quality issues and validate priorities
2. **Resource Allocation**: Assign appropriate specialists to enhancement tasks  
3. **Quality Standards**: Ensure all enhanced assets meet business-ready criteria
4. **Timeline Management**: Coordinate enhancement work within project timeline
5. **Final Validation**: Verify enhanced assets are immediately actionable

**ENHANCEMENT STRATEGY DETAILS**:
{self._format_strategy_details(enhancement_strategy, overall_plan)}

**CRITICAL SUCCESS FACTORS**:
- All enhanced assets must score >0.8 in quality assessment
- Zero fake/placeholder content in final deliverables
- Assets must be immediately implementable by client
- Maintain project timeline while ensuring quality

**DELIVERABLES EXPECTED**:
- Delegate enhancement tasks to appropriate specialists
- Create quality validation checkpoints
- Coordinate final asset integration into deliverable
- Ensure client handoff readiness

**WORKSPACE**: {workspace_id}
**ORCHESTRATION**: AI-guided enhancement process (Production v1.0)"""
        
        return description.strip()
    
    def _format_detailed_quality_summary_for_pm(self, quality_summary: List[Dict]) -> str:
        """Formatta riassunto qualità dettagliato per PM"""
        
        lines = []
        for i, asset in enumerate(quality_summary, 1):
            effort_str = f"{asset['estimated_effort']:.1f}h"
            issues_str = ", ".join(asset["main_issues"][:2])  # Top 2 issues
            
            lines.append(f"{i}. **{asset['asset_name']}** (Score: {asset['quality_score']:.2f}/1.0)")
            lines.append(f"   ├─ Priority: {asset['priority'].upper()}")
            lines.append(f"   ├─ Effort: {effort_str} | Specialist: {asset['specialist_needed']}")
            lines.append(f"   └─ Key Issues: {issues_str}")
            
            if i < len(quality_summary):
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_strategy_details(self, strategy: str, overall_plan: Dict) -> str:
        """Formatta dettagli strategia enhancement"""
        
        strategy_descriptions = {
            "emergency_enhancement": "🚨 Critical quality issues require immediate attention. Focus on critical assets first.",
            "authenticity_focused": "🎯 High levels of fake content detected. Prioritize replacing fake data with real business information.",
            "structure_focused": "📋 Generic structures need domain-specific formatting. Focus on restructuring assets.",
            "quality_focused": "✨ General quality improvements needed. Systematic enhancement of all assets.",
            "comprehensive_improvement": "🔄 Balanced approach to address all identified quality issues."
        }
        
        description = strategy_descriptions.get(strategy, "Standard enhancement approach")
        
        resource_req = overall_plan.get("resource_requirements", {})
        required_roles = resource_req.get("required_specialist_roles", [])
        
        details = [
            f"**Strategy**: {description}",
            f"**Required Specialists**: {', '.join(required_roles) if required_roles else 'General specialists'}",
            f"**Coordination Complexity**: {resource_req.get('coordination_complexity', 'medium').title()}"
        ]
        
        return "\n".join(details)
    
    def _determine_task_priority_from_urgency(self, urgency_level: str) -> str:
        """Converte urgency level in task priority"""
        
        urgency_to_priority = {
            "urgent": "high",
            "high": "high", 
            "medium": "medium",
            "low": "medium"
        }
        
        return urgency_to_priority.get(urgency_level, "medium")
    
    def _get_specialist_needed_for_asset(self, asset_name: str) -> str:
        """Determina che tipo di specialist serve per un asset"""
        
        asset_type = self._determine_asset_type_from_name(asset_name)
        
        if asset_type in self.asset_expertise_mapping:
            primary_roles = self.asset_expertise_mapping[asset_type]["primary_roles"]
            return primary_roles[0] if primary_roles else "specialist"
        
        return "specialist"
    
    async def _create_asset_enhancement_task_robust(
        self, 
        workspace_id: str, 
        asset_info: Dict,
        workspace_goal: str
    ) -> Optional[str]:
        """ENHANCED: Crea task enhancement per asset con error handling robusto"""
        
        try:
            asset_obj = asset_info["asset_obj"]
            quality_assessment = asset_info["quality_assessment"]
            asset_name = asset_obj.get("asset_name", "unknown")
            asset_data = asset_obj.get("asset_data", {})
            
            # Validazione input
            if not asset_data:
                logger.warning(f"No asset data for {asset_name}, skipping enhancement task creation")
                return None
            
            # Trova specialist con algoritmo migliorato
            target_agent = await self._find_appropriate_specialist_robust(
                workspace_id, asset_name, asset_data, quality_assessment
            )
            
            if not target_agent:
                logger.warning(f"⚠️ No appropriate specialist found for {asset_name}")
                return None
            
            # Stima effort
            estimated_effort = self._estimate_enhancement_effort(asset_name, quality_assessment)
            
            # Crea descrizione task migliorata
            task_description = self._create_enhanced_asset_task_description(
                asset_name, asset_data, quality_assessment, workspace_goal, estimated_effort
            )
            
            # Context data esteso
            context_data = {
                "asset_enhancement_task": True,
                "project_phase": "FINALIZATION", 
                "original_asset_id": asset_info["asset_id"],
                "original_quality_score": quality_assessment.overall_score,
                "target_quality_score": 0.8,
                "quality_issues": [issue.value for issue in quality_assessment.quality_issues],
                "enhancement_priority": quality_assessment.enhancement_priority,
                "estimated_effort_hours": estimated_effort,
                "specialist_type": self._get_specialist_needed_for_asset(asset_name),
                "ai_guided_enhancement": True,
                "orchestrator_version": "1.0_production",
                "enhancement_method": "ai_quality_guided"
            }
            
            # Task name più informativo
            priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "🔧", "low": "🔍"}
            emoji = priority_emoji.get(quality_assessment.enhancement_priority, "🔧")
            
            task_name = f"{emoji} ENHANCE: {asset_name} (Score: {quality_assessment.overall_score:.1f}→0.8, {estimated_effort:.1f}h)"
            
            # Crea task
            created_task = await create_task(
                workspace_id=workspace_id,
                agent_id=target_agent["id"],
                name=task_name,
                description=task_description,
                status=TaskStatus.PENDING.value,
                priority=quality_assessment.enhancement_priority if quality_assessment.enhancement_priority != "critical" else "high",
                context_data=context_data,
                creation_type="ai_asset_enhancement_specialist"
            )
            
            if created_task and created_task.get("id"):
                logger.info(f"✅ Enhancement task created: {created_task['id']} "
                           f"for {asset_name} → {target_agent['name']}")
                return created_task["id"]
            else:
                logger.error(f"❌ Database error creating enhancement task for {asset_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating asset enhancement task: {e}", exc_info=True)
            return None
    
    def _create_enhanced_asset_task_description(
        self, 
        asset_name: str, 
        asset_data: Dict, 
        quality_assessment: QualityAssessment,
        workspace_goal: str,
        estimated_effort: float
    ) -> str:
        """ENHANCED: Crea descrizione task più dettagliata per specialist"""
        
        # Prepara current asset sample (limitato per leggibilità)
        asset_sample = self._create_asset_sample_for_task(asset_data)
        
        # Formatta issue specifici
        issues_section = self._format_quality_issues_for_specialist_enhanced(quality_assessment)
        
        # Determina tipo di specialist
        specialist_type = self._get_specialist_needed_for_asset(asset_name)
        
        description = f"""🔧 **ASSET ENHANCEMENT: {asset_name}**

**ENHANCEMENT TARGET**: Transform this asset into a high-quality, immediately actionable business deliverable
**ESTIMATED EFFORT**: {estimated_effort:.1f} hours
**QUALITY TARGET**: >0.8 overall score (currently: {quality_assessment.overall_score:.2f})

{issues_section}

**CURRENT ASSET PREVIEW**:
```json
{asset_sample}
```

**SPECIFIC IMPROVEMENTS REQUIRED**:
{chr(10).join(f"• {suggestion}" for suggestion in quality_assessment.improvement_suggestions)}

**ENHANCEMENT CHECKLIST**:
✅ Replace ALL fake/placeholder content with real, specific business data
✅ Conduct actual research if needed to gather authentic information  
✅ Make it immediately actionable - client should use it without modification
✅ Follow {specialist_type} domain best practices for {asset_name}
✅ Ensure complete data in all sections - no missing information
✅ Validate business readiness and implementation feasibility

**PROJECT CONTEXT**: {workspace_goal}

**SUCCESS CRITERIA**:
- Overall quality score >0.8 (currently: {quality_assessment.overall_score:.2f})
- Actionability score >0.8 (currently: {quality_assessment.actionability_score:.2f})
- Zero fake/placeholder content
- Immediate client usability

**OUTPUT REQUIREMENTS**:
Provide the complete enhanced asset as structured JSON in detailed_results_json field.
Include validation notes in summary explaining changes made.

**IMPORTANT**: This is asset enhancement, not creation. Improve the existing structure and content to business-ready standards."""
        
        return description.strip()
    
    def _create_asset_sample_for_task(self, asset_data: Dict, max_length: int = 800) -> str:
        """Crea sample asset data per task description"""
        
        # Remove metadati generici che non servono
        cleaned_data = {
            k: v for k, v in asset_data.items()
            if k not in ["task_metadata", "task_summary", "error", "extraction_method"]
        }
        
        sample_str = json.dumps(cleaned_data, indent=2, default=str, ensure_ascii=False)
        
        if len(sample_str) > max_length:
            sample_str = sample_str[:max_length] + "\n  ... (truncated)"
        
        return sample_str
    
    def _format_quality_issues_for_specialist_enhanced(self, quality_assessment: QualityAssessment) -> str:
        """ENHANCED: Formatta issue di qualità per specialist"""
        
        lines = [
            f"**CURRENT QUALITY ANALYSIS**:",
            f"├─ Overall Score: {quality_assessment.overall_score:.2f}/1.0",
            f"├─ Actionability: {quality_assessment.actionability_score:.2f}/1.0",
            f"├─ Authenticity: {quality_assessment.authenticity_score:.2f}/1.0",
            f"└─ Completeness: {quality_assessment.completeness_score:.2f}/1.0",
            "",
            "**DETECTED QUALITY ISSUES**:"
        ]
        
        for issue in quality_assessment.quality_issues:
            issue_detail = quality_assessment.issue_details.get(issue.value, "No details provided")
            issue_name = issue.value.replace('_', ' ').title()
            lines.append(f"🔍 **{issue_name}**: {issue_detail}")
        
        return "\n".join(lines)
    
    async def _find_appropriate_specialist_robust(
        self, 
        workspace_id: str, 
        asset_name: str, 
        asset_data: Dict,
        quality_assessment: QualityAssessment
    ) -> Optional[Dict]:
        """ENHANCED: Trova specialist con algoritmo migliorato"""
        
        try:
            agents = await list_agents(workspace_id)
            active_agents = [a for a in agents if a.get("status") == "active"]
            
            if not active_agents:
                logger.error(f"No active agents in workspace {workspace_id}")
                return None
            
            # Determina asset type
            asset_type = self._determine_asset_type_from_name(asset_name)
            
            # Scoring algorithm migliorato
            candidates = []
            
            for agent in active_agents:
                score = self._calculate_agent_suitability_score(
                    agent, asset_type, asset_name, quality_assessment
                )
                
                if score > 0:
                    candidates.append({
                        "agent": agent,
                        "score": score,
                        "role": agent.get("role", ""),
                        "seniority": agent.get("seniority", "junior")
                    })
            
            # Ordina per score
            candidates.sort(key=lambda x: x["score"], reverse=True)
            
            if candidates:
                best_candidate = candidates[0]
                logger.info(f"✅ Specialist selection for {asset_name}: "
                           f"{best_candidate['agent']['name']} "
                           f"({best_candidate['role']}) - Score: {best_candidate['score']:.1f}")
                return best_candidate["agent"]
            else:
                logger.warning(f"⚠️ No suitable specialist found for {asset_name}, using fallback")
                return active_agents[0]  # Fallback
                
        except Exception as e:
            logger.error(f"❌ Error finding specialist: {e}", exc_info=True)
            return None
    
    def _calculate_agent_suitability_score(
        self, 
        agent: Dict, 
        asset_type: str, 
        asset_name: str,
        quality_assessment: QualityAssessment
    ) -> float:
        """Calcola score di idoneità agente per asset enhancement"""
        
        score = 0.0
        
        role = (agent.get("role") or "").lower()
        name = (agent.get("name") or "").lower()
        seniority = agent.get("seniority", "junior").lower()
        
        # Base score da asset expertise mapping
        if asset_type in self.asset_expertise_mapping:
            expertise = self.asset_expertise_mapping[asset_type]
            
            # Primary roles match
            for primary_role in expertise["primary_roles"]:
                if primary_role in role or primary_role in name:
                    score += 15.0
            
            # Secondary roles match
            for secondary_role in expertise["secondary_roles"]:
                if secondary_role in role or secondary_role in name:
                    score += 8.0
            
            # Expertise keywords match
            for keyword in expertise["expertise_keywords"]:
                if keyword in role or keyword in name:
                    score += 5.0
        
        # Seniority bonus
        seniority_bonus = {
            "expert": 10.0,
            "senior": 6.0,
            "junior": 2.0
        }
        score += seniority_bonus.get(seniority, 0.0)
        
        # Bonus per alta priorità enhancement
        if quality_assessment.enhancement_priority in ["critical", "high"]:
            if seniority in ["expert", "senior"]:
                score += 5.0
        
        # Penalty per mismatch completo
        if score < 5.0:
            score = max(1.0, score)  # Minimum score for fallback
        
        return score
    
    def _add_quality_metadata(
        self, 
        actionable_deliverable: Dict[str, Any],
        quality_reports: Dict[str, QualityAssessment],
        enhancement_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ENHANCED: Aggiunge metadata di qualità al deliverable"""
        
        if not quality_reports:
            return actionable_deliverable
        
        # Calcola statistiche qualità
        total_assets = len(quality_reports)
        ready_assets = sum(1 for q in quality_reports.values() if q.ready_for_use)
        avg_quality = sum(q.overall_score for q in quality_reports.values()) / total_assets
        avg_actionability = sum(q.actionability_score for q in quality_reports.values()) / total_assets
        
        # Statistiche issue
        all_issues = []
        for q in quality_reports.values():
            all_issues.extend(q.quality_issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue.value] = issue_counts.get(issue.value, 0) + 1
        
        # Aggiorna meta con informazioni complete
        actionable_deliverable["meta"]["quality_analysis"] = {
            "total_assets_analyzed": total_assets,
            "ready_to_use_assets": ready_assets,
            "average_quality_score": round(avg_quality, 2),
            "average_actionability_score": round(avg_actionability, 2),
            "quality_distribution": {
                "excellent": sum(1 for q in quality_reports.values() if q.overall_score >= 0.8),
                "good": sum(1 for q in quality_reports.values() if 0.6 <= q.overall_score < 0.8),
                "poor": sum(1 for q in quality_reports.values() if q.overall_score < 0.6)
            },
            "common_quality_issues": issue_counts,
            "enhancement_tasks_created": len(enhancement_results),
            "analysis_timestamp": datetime.now().isoformat(),
            "orchestrator_version": "1.0_production"
        }
        
        # Aggiorna executive summary con quality insights
        original_summary = actionable_deliverable.get("executive_summary", "")
        quality_addendum = self._create_quality_summary_addendum(
            total_assets, ready_assets, avg_quality, len(enhancement_results)
        )
        
        actionable_deliverable["executive_summary"] = original_summary + quality_addendum
        
        # Aggiorna next steps con quality-specific actions
        if enhancement_results:
            quality_next_steps = [
                f"🔧 Complete {len(enhancement_results)} asset enhancement tasks to achieve business-ready quality",
                "🎯 Replace all fake/placeholder content with real business data through enhancement process",
                "✅ Validate enhanced assets meet >0.8 quality score before final client delivery",
                "📊 Review quality analysis report to understand specific improvements made"
            ]
            actionable_deliverable["next_steps"].extend(quality_next_steps)
        
        return actionable_deliverable
    
    def _create_quality_summary_addendum(
        self, 
        total_assets: int, 
        ready_assets: int, 
        avg_quality: float,
        enhancement_tasks_count: int
    ) -> str:
        """Crea addendum per executive summary con quality insights"""
        
        quality_level = "excellent" if avg_quality >= 0.8 else "good" if avg_quality >= 0.6 else "needs improvement"
        
        addendum = f"""

**🔍 AI Quality Analysis Summary**: 
{ready_assets}/{total_assets} assets are immediately ready for business use (average quality: {avg_quality:.1f}/1.0 - {quality_level}). """
        
        if enhancement_tasks_count > 0:
            addendum += f"""{enhancement_tasks_count} automated enhancement tasks have been created to upgrade remaining assets to business-ready standards. The AI quality orchestrator has identified specific improvements needed and assigned appropriate specialists to execute them."""
        else:
            addendum += "All assets meet high quality standards and are ready for immediate client implementation."
        
        return addendum
    
    def _add_error_metadata(self, actionable_deliverable: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Aggiunge metadata di errore in caso di failure"""
        
        actionable_deliverable["meta"]["quality_analysis_error"] = {
            "error_occurred": True,
            "error_message": error_message,
            "analysis_timestamp": datetime.now().isoformat(),
            "fallback_applied": True
        }
        
        # Aggiungi warning in executive summary
        warning = f"\n\n**⚠️ Quality Analysis Warning**: Automated quality analysis encountered an error ({error_message}). Manual quality review is recommended before client delivery."
        
        original_summary = actionable_deliverable.get("executive_summary", "")
        actionable_deliverable["executive_summary"] = original_summary + warning
        
        return actionable_deliverable
    
    # === MONITORING E STATS ===
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche dell'orchestratore"""
        
        validator_stats = self.validator.get_validation_stats()
        
        return {
            "orchestrator_version": "1.0_production",
            "total_orchestrations": self.orchestration_count,
            "total_assets_analyzed": self.total_assets_analyzed,
            "total_enhancements_created": self.total_enhancements_created,
            "validator_stats": validator_stats,
            "asset_expertise_types": list(self.asset_expertise_mapping.keys()),
            "configuration": {
                "effort_estimation": ENHANCEMENT_EFFORT_ESTIMATION,
                "priority_thresholds": ENHANCEMENT_PRIORITY_THRESHOLDS
            },
            "enhancement_plans_active": len(self.enhancement_plans)
        }
    
    def reset_stats(self):
        """Reset delle statistiche"""
        self.orchestration_count = 0
        self.total_assets_analyzed = 0
        self.total_enhancements_created = 0
        self.enhancement_plans.clear()
        self.validator.reset_stats()
        logger.info("🔄 Orchestrator stats reset")