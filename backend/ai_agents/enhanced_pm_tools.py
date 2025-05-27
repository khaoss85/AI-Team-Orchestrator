# backend/ai_agents/enhanced_pm_tools.py

import logging
import json
from typing import List, Dict, Any, Optional, Literal
from uuid import UUID
from datetime import datetime
from pydantic import Field

try:
    from agents import function_tool
except ImportError:
    from openai_agents import function_tool # type: ignore

# Import dal sistema esistente
from ai_agents.tools import PMOrchestrationTools
from models import TaskStatus, AssetProductionContext
from database import (
    create_task as db_create_task,
    list_agents as db_list_agents,
    list_tasks as db_list_tasks,
)

# Import dal nuovo sistema di deliverable
from deliverable_system.requirements_analyzer import DeliverableRequirementsAnalyzer
from deliverable_system.schema_generator import AssetSchemaGenerator

logger = logging.getLogger(__name__)

class EnhancedPMOrchestrationTools(PMOrchestrationTools):
    """
    Estensione di PMOrchestrationTools per supportare asset-oriented task creation
    Mantiene backward compatibility con il sistema esistente
    """
    
    # Definisci i nomi dei nuovi tool come attributi di CLASSE
    TOOL_NAME_CREATE_ASSET_TASK = "create_asset_production_task"
    TOOL_NAME_ANALYZE_DELIVERABLE_NEEDS = "analyze_deliverable_requirements"
    TOOL_NAME_GET_ASSET_SCHEMAS = "get_available_asset_schemas"
    
    def __init__(self, workspace_id: str):
        super().__init__(workspace_id)
        
        # Inizializza i componenti per asset dinamici
        self.requirements_analyzer = DeliverableRequirementsAnalyzer()
        self.schema_generator = AssetSchemaGenerator()
        
        # Cache per requirements e schema (per evitare multiple chiamate)
        self._requirements_cache = None
        self._schemas_cache = None
        
        logger.info(f"EnhancedPMOrchestrationTools initialized for workspace: {workspace_id}")
    
    def get_enhanced_tools_list(self) -> List[Any]:
        """
        Restituisce la lista completa di tool (esistenti + nuovi)
        """
        
        # Tool esistenti dalla classe padre
        existing_tools = [
            self.create_and_assign_sub_task_tool(),
            self.get_team_roles_and_status_tool()
        ]
        
        # Nuovi tool per asset production
        asset_tools = [
            self.create_asset_production_task_tool(),
            self.analyze_deliverable_requirements_tool(),
            self.get_available_asset_schemas_tool()
        ]
        
        return existing_tools + asset_tools
    
    def create_asset_production_task_tool(self):
        """
        Tool per creare task specifici per la produzione di asset azionabili
        """
        workspace_id_str = self.workspace_id
        
        @function_tool(name_override=self.TOOL_NAME_CREATE_ASSET_TASK)
        async def impl(
            asset_type: str = Field(..., description="Tipo di asset da produrre (es. content_calendar, contact_database, training_program)"),
            task_name: str = Field(..., description="Nome specifico del task (deve iniziare con 'PRODUCE ASSET:')"),
            task_description: str = Field(..., description="Descrizione dettagliata del task con schema output richiesto"),
            target_agent_role: str = Field(..., description="Nome esatto dell'agente per produrre questo asset"),
            priority: Literal["low", "medium", "high"] = Field(default="high", description="Priorità del task di produzione asset"),
            quality_requirements: List[str] = Field(default_factory=list, description="Requisiti specifici di qualità"),
            automation_requirements: List[str] = Field(default_factory=list, description="Requisiti per automazione")
        ) -> str:
            """
            Crea un task specifico per la produzione di un asset azionabile.
            Questo tool si differenzia dal normale create_and_assign_sub_task perché:
            1. È specificamente per asset production
            2. Include schema validation
            3. Ha context data specifico per asset
            4. Include requirements per qualità e automazione
            """
            
            try:
                logger.info(f"🎯 ASSET TASK: Creating '{asset_type}' production task for '{target_agent_role}' in workspace {workspace_id_str}")
                
                # Verifica che il task name sia corretto per asset production
                if not task_name.upper().startswith("PRODUCE ASSET:"):
                    task_name = f"PRODUCE ASSET: {task_name}"
                
                # Recupera schema per questo tipo di asset (se disponibile)
                asset_schema = await self._get_asset_schema(asset_type)
                
                # Arricchisci la descrizione del task con lo schema
                enhanced_description = await self._enhance_task_description_with_schema(
                    task_description, asset_type, asset_schema, quality_requirements, automation_requirements
                )
                
                # Trova l'agente target
                agents_in_db = await db_list_agents(workspace_id=workspace_id_str)
                target_agent = self._find_agent_for_asset_production(agents_in_db, target_agent_role, asset_type)
                
                if not target_agent:
                    error_msg = f"No suitable agent found for asset production. Target: '{target_agent_role}', Asset: '{asset_type}'"
                    logger.error(error_msg)
                    return json.dumps({
                        "success": False,
                        "error": error_msg,
                        "suggestion": "Call 'get_team_roles_and_status' to see available agents"
                    })
                
                # Verifica duplicati (stesso asset type in progress)
                if await self._check_asset_production_duplicate(workspace_id_str, asset_type):
                    logger.warning(f"Asset production task for '{asset_type}' already exists or in progress")
                    return json.dumps({
                        "success": False,
                        "error": f"Asset production for '{asset_type}' already in progress",
                        "message": "Avoid creating duplicate asset production tasks"
                    })
                
                # Context data specifico per asset production
                asset_context = AssetProductionContext(
                    asset_production=True,
                    target_schema=asset_type,
                    asset_type=asset_type,
                    quality_requirements=quality_requirements,
                    automation_requirements=automation_requirements
                )
                
                # Context data esteso per il database
                full_context_data = {
                    **asset_context.model_dump(),
                    "project_phase": "FINALIZATION",  # Asset production tipicamente nella fase finale
                    "asset_oriented_task": True,
                    "deliverable_critical": True,
                    "creation_method": "enhanced_pm_asset_tool",
                    "tool_call_timestamp": datetime.now().isoformat(),
                    "expected_output_format": "structured_asset_data",
                    "schema_available": asset_schema is not None,
                    "validation_enabled": True
                }
                
                # Crea il task nel database
                created_task = await db_create_task(
                    workspace_id=workspace_id_str,
                    agent_id=str(target_agent["id"]),
                    assigned_to_role=target_agent.get("role"),
                    name=task_name,
                    description=enhanced_description,
                    status=TaskStatus.PENDING.value,
                    priority=priority,
                    context_data=full_context_data,
                    creation_type="asset_production"
                )
                
                if created_task and created_task.get("id"):
                    success_response = {
                        "success": True,
                        "task_id": created_task["id"],
                        "asset_type": asset_type,
                        "assigned_agent": target_agent["name"],
                        "message": f"Asset production task created for '{asset_type}'",
                        "schema_provided": asset_schema is not None,
                        "validation_enabled": True
                    }
                    
                    logger.info(f"✅ ASSET TASK CREATED: {created_task['id']} for {asset_type}")
                    return json.dumps(success_response)
                else:
                    error_msg = f"Database error: Failed to create asset production task for '{asset_type}'"
                    logger.error(error_msg)
                    return json.dumps({"success": False, "error": error_msg})
                    
            except Exception as e:
                logger.error(f"Error in {self.TOOL_NAME_CREATE_ASSET_TASK}: {e}", exc_info=True)
                return json.dumps({
                    "success": False,
                    "error": f"Critical error: {str(e)}",
                    "asset_type": asset_type
                })
        
        return impl
    
    def analyze_deliverable_requirements_tool(self):
        """
        Tool per analizzare dinamicamente i requirements del deliverable
        """
        workspace_id_str = self.workspace_id
        
        @function_tool(name_override=self.TOOL_NAME_ANALYZE_DELIVERABLE_NEEDS)
        async def impl() -> str:
            """
            Analizza il workspace e determina dinamicamente che asset azionabili servono per il deliverable finale.
            Questo tool aiuta il PM a capire che tipo di asset produrre per massimizzare l'azionabilità del deliverable.
            """
            
            try:
                logger.info(f"📋 DELIVERABLE ANALYSIS: Starting for workspace {workspace_id_str}")
                
                # Usa cache se disponibile
                if self._requirements_cache is None:
                    self._requirements_cache = await self.requirements_analyzer.analyze_deliverable_requirements(workspace_id_str)
                
                requirements = self._requirements_cache
                
                # Formatta response per il PM
                analysis_response = {
                    "workspace_id": workspace_id_str,
                    "deliverable_category": requirements.deliverable_category,
                    "total_assets_needed": len(requirements.primary_assets_needed),
                    "recommended_assets": [
                        {
                            "asset_type": asset.asset_type,
                            "priority": asset.priority,
                            "actionability_level": asset.actionability_level,
                            "business_impact": asset.business_impact,
                            "format": asset.asset_format,
                            "validation_criteria": asset.validation_criteria
                        }
                        for asset in requirements.primary_assets_needed
                    ],
                    "next_steps": [
                        f"Create asset production task for '{asset.asset_type}' (Priority: {asset.priority})"
                        for asset in sorted(requirements.primary_assets_needed, key=lambda x: x.priority)
                    ],
                    "deliverable_structure": requirements.deliverable_structure
                }
                
                logger.info(f"📋 ANALYSIS COMPLETE: {requirements.deliverable_category} with {len(requirements.primary_assets_needed)} assets")
                return json.dumps(analysis_response, indent=2)
                
            except Exception as e:
                logger.error(f"Error in {self.TOOL_NAME_ANALYZE_DELIVERABLE_NEEDS}: {e}", exc_info=True)
                return json.dumps({
                    "error": str(e),
                    "workspace_id": workspace_id_str,
                    "fallback_recommendation": "Create comprehensive project report as fallback deliverable"
                })
        
        return impl
    
    def get_available_asset_schemas_tool(self):
        """
        Tool per ottenere gli schemi disponibili per i tipi di asset
        """
        workspace_id_str = self.workspace_id
        
        @function_tool(name_override=self.TOOL_NAME_GET_ASSET_SCHEMAS)
        async def impl(
            asset_type: Optional[str] = Field(None, description="Tipo specifico di asset (lascia vuoto per vedere tutti)")
        ) -> str:
            """
            Recupera gli schemi disponibili per asset azionabili.
            Utile per sapere che struttura deve avere l'output di un task di produzione asset.
            """
            
            try:
                logger.info(f"📐 SCHEMAS: Retrieving for workspace {workspace_id_str}, asset_type: {asset_type}")
                
                # Genera/recupera requirements se non già fatto
                if self._requirements_cache is None:
                    self._requirements_cache = await self.requirements_analyzer.analyze_deliverable_requirements(workspace_id_str)
                
                # Genera/recupera schemas se non già fatto
                if self._schemas_cache is None:
                    self._schemas_cache = await self.schema_generator.generate_asset_schemas(self._requirements_cache)
                
                # Filtra per asset_type specifico se richiesto
                if asset_type:
                    if asset_type in self._schemas_cache:
                        schema = self._schemas_cache[asset_type]
                        schema_response = {
                            "asset_type": asset_type,
                            "schema_definition": schema.schema_definition,
                            "validation_rules": schema.validation_rules,
                            "usage_instructions": schema.usage_instructions,
                            "automation_ready": schema.automation_ready
                        }
                    else:
                        # Fallback per asset type non riconosciuto
                        schema_response = {
                            "asset_type": asset_type,
                            "error": f"No schema available for '{asset_type}'",
                            "available_types": list(self._schemas_cache.keys()),
                            "suggestion": "Use one of the available asset types or create a custom structured output"
                        }
                else:
                    # Restituisci tutti gli schemi disponibili (versione compatta)
                    schema_response = {
                        "available_asset_types": list(self._schemas_cache.keys()),
                        "schemas_summary": [
                            {
                                "asset_type": name,
                                "automation_ready": schema.automation_ready,
                                "validation_rules_count": len(schema.validation_rules),
                                "main_fields": list(schema.schema_definition.keys())[:5]  # Prime 5 chiavi
                            }
                            for name, schema in self._schemas_cache.items()
                        ],
                        "usage_note": "Call this tool again with specific asset_type to get full schema"
                    }
                
                return json.dumps(schema_response, indent=2)
                
            except Exception as e:
                logger.error(f"Error in {self.TOOL_NAME_GET_ASSET_SCHEMAS}: {e}", exc_info=True)
                return json.dumps({
                    "error": str(e),
                    "workspace_id": workspace_id_str,
                    "fallback": "Use standard TaskExecutionOutput format with detailed_results_json"
                })
        
        return impl
    
    async def _get_asset_schema(self, asset_type: str) -> Optional[Dict]:
        """Recupera schema per un tipo di asset specifico"""
        
        try:
            # Usa cache se disponibile
            if self._schemas_cache is None:
                if self._requirements_cache is None:
                    self._requirements_cache = await self.requirements_analyzer.analyze_deliverable_requirements(self.workspace_id)
                self._schemas_cache = await self.schema_generator.generate_asset_schemas(self._requirements_cache)
            
            schema_obj = self._schemas_cache.get(asset_type)
            return schema_obj.schema_definition if schema_obj else None
            
        except Exception as e:
            logger.error(f"Error retrieving schema for {asset_type}: {e}")
            return None
    
    async def _enhance_task_description_with_schema(
        self, 
        base_description: str, 
        asset_type: str, 
        asset_schema: Optional[Dict],
        quality_requirements: List[str],
        automation_requirements: List[str]
    ) -> str:
        """
        Arricchisce la descrizione del task con schema specifico e requirements
        """
        
        enhanced_description = f"""🎯 **ASSET PRODUCTION TASK**

**ASSET TYPE:** {asset_type}
**DELIVERABLE CRITICALITY:** HIGH - This asset is essential for the final project deliverable

**ORIGINAL TASK DESCRIPTION:**
{base_description}

**🚨 CRITICAL OUTPUT REQUIREMENTS:**
Your detailed_results_json MUST contain a valid, complete {asset_type} that can be used immediately by the client.

"""
        
        # Aggiungi schema se disponibile
        if asset_schema:
            enhanced_description += f"""**📋 REQUIRED OUTPUT SCHEMA:**
The detailed_results_json MUST follow this exact structure:

```json
{json.dumps(asset_schema, indent=2)}
```

**SCHEMA COMPLIANCE:**
- Every required field MUST be populated with real, actionable data
- Do not use placeholder values like "string" or "TBD" 
- Ensure all data is ready for immediate business use
- Validate your output against the schema before submitting

"""
        else:
            enhanced_description += f"""**📋 OUTPUT STRUCTURE:**
Since no predefined schema exists for '{asset_type}', create a comprehensive structured output that includes:
- Complete, actionable data ready for immediate use
- Clear field names and organized structure
- All necessary details for business implementation
- Validation-ready format

"""
        
        # Aggiungi quality requirements
        if quality_requirements:
            enhanced_description += f"""**✅ QUALITY REQUIREMENTS:**
{chr(10).join(f"- {req}" for req in quality_requirements)}

"""
        
        # Aggiungi automation requirements
        if automation_requirements:
            enhanced_description += f"""**🤖 AUTOMATION REQUIREMENTS:**
{chr(10).join(f"- {req}" for req in automation_requirements)}

"""
        
        enhanced_description += f"""**🎯 SUCCESS CRITERIA:**
1. Output is immediately actionable (ready-to-use)
2. All fields contain real business data (no placeholders)
3. Structure follows schema requirements
4. Quality and automation requirements are met
5. Client can implement immediately without modifications

**⚠️ IMPORTANT:**
This is not a planning or strategy task - you must produce the actual, complete {asset_type} ready for business use.
"""
        
        return enhanced_description
    
    def _find_agent_for_asset_production(
        self, 
        agents: List[Dict], 
        target_agent_role: str, 
        asset_type: str
    ) -> Optional[Dict]:
        """
        Trova l'agente migliore per produrre un specifico tipo di asset
        Estende la logica esistente con asset-specific matching
        """
        
        # Prima usa la logica esistente per il role matching
        from ai_agents.specialist import SpecialistAgent
        dummy_specialist = SpecialistAgent.__new__(SpecialistAgent)
        dummy_specialist.agents = {}  # Non serve per questo metodo
        
        compatible_agents = dummy_specialist._find_compatible_agents_anti_loop(agents, target_agent_role)
        
        if compatible_agents:
            # Se abbiamo candidati, selezioniamo il migliore per questo asset type
            best_agent = self._select_best_agent_for_asset(compatible_agents, asset_type)
            return best_agent
        
        # Fallback: cerca agenti con competenze specifiche per l'asset
        asset_specialists = self._find_asset_specialists(agents, asset_type)
        return asset_specialists[0] if asset_specialists else None
    
    def _select_best_agent_for_asset(self, candidates: List[Dict], asset_type: str) -> Dict:
        """
        Seleziona il candidato migliore per un tipo di asset specifico
        """
        
        # Mapping asset type -> role preferences
        asset_role_preferences = {
            "content_calendar": ["content", "marketing", "social"],
            "instagram_growth_strategy": ["social", "marketing", "growth"],
            "qualified_contact_database": ["sales", "business", "lead"],
            "outreach_email_templates": ["sales", "marketing", "communication"],
            "training_program": ["fitness", "trainer", "coach", "sports"],
            "financial_model": ["finance", "analyst", "business"],
            "research_database": ["research", "analyst", "data"],
            "action_plan": ["manager", "coordinator", "planner"]
        }
        
        preferred_keywords = asset_role_preferences.get(asset_type, ["specialist"])
        
        # Score candidates based on asset-specific preferences
        scored_candidates = []
        
        for candidate in candidates:
            role = candidate.get("role", "").lower()
            name = candidate.get("name", "").lower()
            base_score = candidate.get("match_score", 0)
            
            # Asset-specific bonus
            asset_bonus = 0
            for keyword in preferred_keywords:
                if keyword in role or keyword in name:
                    asset_bonus += 5
            
            final_score = base_score + asset_bonus
            scored_candidates.append((candidate, final_score))
        
        # Restituisci il migliore
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate = scored_candidates[0][0]
        
        logger.info(f"🎯 ASSET AGENT SELECTION: {best_candidate['name']} selected for {asset_type}")
        return best_candidate
    
    def _find_asset_specialists(self, agents: List[Dict], asset_type: str) -> List[Dict]:
        """
        Trova specialisti per un tipo di asset (fallback quando role matching fallisce)
        """
        
        # Keywords di fallback per asset type
        asset_keywords = {
            "content_calendar": ["content", "creative", "writer"],
            "qualified_contact_database": ["sales", "business"],
            "training_program": ["trainer", "coach", "fitness"],
            "financial_model": ["finance", "analyst"],
            "research_database": ["research", "data", "analyst"]
        }
        
        keywords = asset_keywords.get(asset_type, ["specialist"])
        specialists = []
        
        for agent in agents:
            if agent.get("status") == "active":
                role = agent.get("role", "").lower()
                if any(keyword in role for keyword in keywords):
                    specialists.append(agent)
        
        return specialists
    
    async def _check_asset_production_duplicate(self, workspace_id: str, asset_type: str) -> bool:
        """
        Verifica se esiste già un task per la produzione di questo asset
        """
        
        try:
            tasks = await db_list_tasks(workspace_id)
            
            for task in tasks:
                if task.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]:
                    context_data = task.get("context_data", {}) or {}
                    
                    # Controlla se è un task di asset production per lo stesso asset type
                    if (isinstance(context_data, dict) and
                        context_data.get("asset_production") and
                        context_data.get("asset_type") == asset_type):
                        
                        logger.warning(f"Duplicate asset production found: {task.get('id')} for {asset_type}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking asset production duplicates: {e}")
            return False  # In caso di errore, permetti la creazione