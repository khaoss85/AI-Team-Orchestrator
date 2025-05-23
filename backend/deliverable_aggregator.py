# backend/deliverable_aggregator.py - Nuovo sistema per deliverable finali

import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from database import (
    get_workspace, list_tasks, list_agents, create_task,
    update_workspace_status
)
from models import TaskStatus, ProjectPhase

logger = logging.getLogger(__name__)

class DeliverableType(str, Enum):
    """Tipi di deliverable finali supportati"""
    CONTACT_LIST = "contact_list"
    CONTENT_STRATEGY = "content_strategy"
    COMPETITOR_ANALYSIS = "competitor_analysis"  
    MARKET_RESEARCH = "market_research"
    BUSINESS_PLAN = "business_plan"
    LEAD_GENERATION = "lead_generation"
    SOCIAL_MEDIA_PLAN = "social_media_plan"
    GENERIC_REPORT = "generic_report"

class DeliverableAggregator:
    """Aggrega risultati di task e crea deliverable finali strutturati"""
    
    def __init__(self):
        self.goal_patterns = {
            DeliverableType.CONTACT_LIST: [
                r"find.*contact", r"lead.*generation", r"prospect", 
                r"cold.*call", r"email.*list", r"outreach"
            ],
            DeliverableType.CONTENT_STRATEGY: [
                r"content.*strategy", r"editorial.*plan", r"content.*plan",
                r"social.*media.*strategy", r"instagram.*strategy"
            ],
            DeliverableType.COMPETITOR_ANALYSIS: [
                r"competitor.*analy", r"competitive.*landscap", 
                r"competitor.*research", r"market.*position"
            ],
            DeliverableType.MARKET_RESEARCH: [
                r"market.*research", r"market.*analysis", r"industry.*analysis",
                r"target.*audience", r"customer.*research"
            ],
            DeliverableType.SOCIAL_MEDIA_PLAN: [
                r"social.*media", r"instagram.*plan", r"facebook.*strategy",
                r"twitter.*strategy", r"linkedin.*strategy"
            ],
            DeliverableType.LEAD_GENERATION: [
                r"lead.*generation", r"sales.*funnel", r"conversion.*strategy"
            ]
        }
    
    async def check_and_create_final_deliverable(self, workspace_id: str) -> Optional[str]:
        """Controlla se è il momento di creare il deliverable finale"""
        try:
            # Verifica se il progetto è pronto per il deliverable finale
            if not await self._is_ready_for_final_deliverable(workspace_id):
                return None
            
            # Verifica se esiste già un deliverable finale
            if await self._final_deliverable_exists(workspace_id):
                logger.info(f"Final deliverable already exists for workspace {workspace_id}")
                return None
            
            # Raccogli tutti i dati necessari
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if not workspace or len(completed_tasks) < 3:
                return None
            
            # Determina il tipo di deliverable
            deliverable_type = self._determine_deliverable_type(workspace.get("goal", ""))
            
            # Aggrega i risultati
            aggregated_data = await self._aggregate_task_results(completed_tasks, deliverable_type)
            
            # Crea il deliverable finale
            deliverable_task_id = await self._create_final_deliverable_task(
                workspace_id, workspace, deliverable_type, aggregated_data
            )
            
            logger.info(f"Created final deliverable task {deliverable_task_id} "
                       f"for workspace {workspace_id} (type: {deliverable_type.value})")
            
            return deliverable_task_id
            
        except Exception as e:
            logger.error(f"Error creating final deliverable: {e}", exc_info=True)
            return None
    
    async def _is_ready_for_final_deliverable(self, workspace_id: str) -> bool:
        """Verifica se il progetto è pronto per il deliverable finale"""
        try:
            tasks = await list_tasks(workspace_id)
            
            if not tasks:
                return False
            
            completed = [t for t in tasks if t.get("status") == "completed"]
            pending = [t for t in tasks if t.get("status") == "pending"]
            
            # Criteri per deliverable finale:
            # 1. Almeno 80% dei task completati
            completion_rate = len(completed) / len(tasks)
            
            # 2. Almeno 5 task completati in totale
            min_completed = len(completed) >= 5
            
            # 3. Massimo 2 task pending (per evitare deliverable prematuri)
            low_pending = len(pending) <= 2
            
            # 4. Almeno 2 task di FINALIZATION completati
            finalization_completed = len([
                t for t in completed 
                if (t.get("context_data", {}) or {}).get("project_phase") == "FINALIZATION"
            ]) >= 2
            
            logger.info(f"Final deliverable readiness check for {workspace_id}: "
                       f"completion_rate={completion_rate:.2f}, "
                       f"min_completed={min_completed}, "
                       f"low_pending={low_pending}, "
                       f"finalization_completed={finalization_completed}")
            
            return completion_rate >= 0.8 and min_completed and low_pending and finalization_completed
            
        except Exception as e:
            logger.error(f"Error checking final deliverable readiness: {e}")
            return False
    
    async def _final_deliverable_exists(self, workspace_id: str) -> bool:
        """Verifica se esiste già un deliverable finale"""
        try:
            tasks = await list_tasks(workspace_id)
            
            for task in tasks:
                context_data = task.get("context_data", {}) or {}
                if (context_data.get("is_final_deliverable") or 
                    context_data.get("deliverable_aggregation") or
                    "FINAL DELIVERABLE" in (task.get("name", "") or "").upper()):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking existing final deliverable: {e}")
            return True  # In caso di errore, assumiamo che esista per evitare duplicati
    
    def _determine_deliverable_type(self, goal: str) -> DeliverableType:
        """Determina il tipo di deliverable basato sul goal"""
        if not goal:
            return DeliverableType.GENERIC_REPORT
        
        goal_lower = goal.lower()
        
        for deliverable_type, patterns in self.goal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, goal_lower):
                    logger.info(f"Detected deliverable type {deliverable_type.value} "
                               f"for goal: {goal[:100]}")
                    return deliverable_type
        
        return DeliverableType.GENERIC_REPORT
    
    async def _aggregate_task_results(
        self, 
        completed_tasks: List[Dict], 
        deliverable_type: DeliverableType
    ) -> Dict[str, Any]:
        """Aggrega i risultati dei task completati per tipo di deliverable"""
        
        aggregated = {
            "total_tasks": len(completed_tasks),
            "task_summaries": [],
            "structured_data": {},
            "key_insights": [],
            "recommendations": []
        }
        
        # Estrai dati strutturati dai task
        all_structured_data = []
        
        for task in completed_tasks:
            result = task.get("result", {}) or {}
            summary = result.get("summary", "")
            
            # Aggiungi summary al aggregated
            if summary and len(summary.strip()) > 10:
                aggregated["task_summaries"].append({
                    "task_name": task.get("name", ""),
                    "summary": summary,
                    "agent_role": task.get("assigned_to_role", ""),
                    "completed_at": task.get("updated_at", "")
                })
            
            # Estrai JSON strutturato se presente
            detailed_json = result.get("detailed_results_json")
            if detailed_json and isinstance(detailed_json, str):
                try:
                    structured = json.loads(detailed_json)
                    if isinstance(structured, dict):
                        all_structured_data.append({
                            "task_id": task.get("id"),
                            "task_name": task.get("name", ""),
                            "data": structured
                        })
                except json.JSONDecodeError:
                    pass
            
            # Estrai next_steps come insights/recommendations
            next_steps = result.get("next_steps", [])
            if isinstance(next_steps, list):
                aggregated["recommendations"].extend(next_steps)
        
        # Elaborazione specifica per tipo di deliverable
        if deliverable_type == DeliverableType.CONTACT_LIST:
            aggregated["structured_data"] = self._extract_contact_data(all_structured_data)
        elif deliverable_type == DeliverableType.CONTENT_STRATEGY:
            aggregated["structured_data"] = self._extract_content_strategy_data(all_structured_data)
        elif deliverable_type == DeliverableType.COMPETITOR_ANALYSIS:
            aggregated["structured_data"] = self._extract_competitor_data(all_structured_data)
        else:
            # Aggregazione generica
            aggregated["structured_data"] = {
                "all_data": all_structured_data,
                "data_sources": len(all_structured_data)
            }
        
        # Estrai key insights
        aggregated["key_insights"] = self._extract_key_insights(
            aggregated["task_summaries"], deliverable_type
        )
        
        return aggregated
    
    def _extract_contact_data(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Estrae e struttura dati di contatti"""
        contacts = []
        sources = []
        
        for item in structured_data:
            data = item.get("data", {})
            
            # Cerca liste di contatti
            for key, value in data.items():
                if "contact" in key.lower() or "lead" in key.lower():
                    if isinstance(value, list):
                        contacts.extend(value)
                    elif isinstance(value, dict):
                        contacts.append(value)
                elif "company" in key.lower() or "business" in key.lower():
                    if isinstance(value, list):
                        contacts.extend(value)
            
            sources.append(item.get("task_name", ""))
        
        return {
            "total_contacts": len(contacts),
            "contacts": contacts[:500],  # Limita per performance
            "data_sources": sources,
            "collection_methods": list(set(sources))
        }
    
    def _extract_content_strategy_data(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Estrae dati per strategia di contenuti"""
        content_ideas = []
        strategies = []
        calendars = []
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                if "content" in key.lower() or "post" in key.lower():
                    if isinstance(value, list):
                        content_ideas.extend(value)
                elif "strategy" in key.lower() or "plan" in key.lower():
                    strategies.append(value)
                elif "calendar" in key.lower() or "schedule" in key.lower():
                    calendars.append(value)
        
        return {
            "content_ideas": content_ideas,
            "strategies": strategies,
            "calendars": calendars,
            "total_content_pieces": len(content_ideas)
        }
    
    def _extract_competitor_data(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Estrae dati di analisi competitor"""
        competitors = []
        analyses = []
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                if "competitor" in key.lower():
                    if isinstance(value, list):
                        competitors.extend(value)
                    else:
                        competitors.append(value)
                elif "analysis" in key.lower():
                    analyses.append(value)
        
        return {
            "competitors_analyzed": len(competitors),
            "competitor_profiles": competitors,
            "analysis_results": analyses
        }
    
    def _extract_key_insights(
        self, 
        task_summaries: List[Dict], 
        deliverable_type: DeliverableType
    ) -> List[str]:
        """Estrae key insights dai summaries dei task"""
        insights = []
        
        # Parole chiave per insights per tipo
        insight_keywords = {
            DeliverableType.CONTACT_LIST: ["identified", "found", "qualified", "prospects"],
            DeliverableType.CONTENT_STRATEGY: ["engagement", "audience", "platform", "content"],
            DeliverableType.COMPETITOR_ANALYSIS: ["competitive", "advantage", "weakness", "strength"],
        }
        
        keywords = insight_keywords.get(deliverable_type, ["key", "important", "significant"])
        
        for summary_item in task_summaries:
            summary = summary_item.get("summary", "")
            
            # Trova frasi che contengono parole chiave
            sentences = re.split(r'[.!?]+', summary)
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 20 and 
                    any(keyword in sentence.lower() for keyword in keywords)):
                    insights.append(sentence)
        
        return insights[:10]  # Limita a 10 insights top
    
    async def _create_final_deliverable_task(
        self, 
        workspace_id: str, 
        workspace: Dict, 
        deliverable_type: DeliverableType,
        aggregated_data: Dict[str, Any]
    ) -> Optional[str]:
        """Crea il task finale per il deliverable aggregato"""
        
        # Trova Project Manager
        agents = await list_agents(workspace_id)
        pm_agent = next(
            (a for a in agents if "project manager" in (a.get("role") or "").lower()),
            None
        )
        
        if not pm_agent:
            pm_agent = agents[0] if agents else None
        
        if not pm_agent:
            logger.error(f"No agent found for final deliverable task in workspace {workspace_id}")
            return None
        
        # Crea descrizione specifica per tipo
        description = self._create_deliverable_description(
            workspace.get("goal", ""), deliverable_type, aggregated_data
        )
        
        # Crea il task
        deliverable_task = await create_task(
            workspace_id=workspace_id,
            agent_id=pm_agent["id"],
            name=f"🎯 FINAL DELIVERABLE: {deliverable_type.value.replace('_', ' ').title()}",
            description=description,
            status="pending",
            priority="high",
            creation_type="final_deliverable_aggregation",
            context_data={
                "is_final_deliverable": True,
                "deliverable_aggregation": True,
                "deliverable_type": deliverable_type.value,
                "project_phase": "FINALIZATION",
                "aggregated_data": aggregated_data,
                "workspace_goal": workspace.get("goal", ""),
                "creation_timestamp": datetime.now().isoformat(),
                "triggers_project_completion": True
            }
        )
        
        if deliverable_task and deliverable_task.get("id"):
            return deliverable_task["id"]
        
        return None
    
    def _create_deliverable_description(
        self, 
        goal: str, 
        deliverable_type: DeliverableType,
        aggregated_data: Dict[str, Any]
    ) -> str:
        """Crea descrizione specifica per il tipo di deliverable"""
        
        base_context = f"""
🎯 OBJECTIVE: {goal}

📊 PROJECT SUMMARY:
- Total tasks completed: {aggregated_data.get('total_tasks', 0)}
- Key insights identified: {len(aggregated_data.get('key_insights', []))}
- Structured data sources: {len(aggregated_data.get('structured_data', {}).get('data_sources', []))}

🔍 YOUR MISSION: Create the FINAL DELIVERABLE that directly addresses the objective above.
"""
        
        if deliverable_type == DeliverableType.CONTACT_LIST:
            specific_instructions = f"""
📋 DELIVERABLE TYPE: CONTACT LIST

📈 DATA AVAILABLE:
- Total contacts found: {aggregated_data.get('structured_data', {}).get('total_contacts', 0)}
- Collection sources: {aggregated_data.get('structured_data', {}).get('collection_methods', [])}

✅ REQUIRED OUTPUT in detailed_results_json:
{{
  "deliverable_type": "contact_list",
  "final_contact_list": [
    {{
      "name": "Contact Name",
      "company": "Company",
      "email": "email@example.com",
      "phone": "+1234567890",
      "title": "Job Title",
      "source": "How this contact was found",
      "qualification_score": "1-10",
      "notes": "Additional relevant information"
    }}
  ],
  "list_statistics": {{
    "total_contacts": 500,
    "qualified_leads": 300,
    "sources_used": ["LinkedIn", "Company websites", "Industry databases"],
    "quality_score": "8.5/10"
  }},
  "usage_recommendations": [
    "Best outreach approach for this list",
    "Optimal contact timing",
    "Key messaging recommendations"
  ]
}}

🎯 FOCUS: Create a clean, usable contact list ready for cold calling/outreach.
"""
        
        elif deliverable_type == DeliverableType.CONTENT_STRATEGY:
            specific_instructions = f"""
📋 DELIVERABLE TYPE: CONTENT STRATEGY

📈 DATA AVAILABLE:
- Content ideas generated: {aggregated_data.get('structured_data', {}).get('total_content_pieces', 0)}
- Strategy components: {len(aggregated_data.get('structured_data', {}).get('strategies', []))}

✅ REQUIRED OUTPUT in detailed_results_json:
{{
  "deliverable_type": "content_strategy",
  "content_calendar": [
    {{
      "date": "2024-01-15",
      "platform": "Instagram",
      "content_type": "Image Post",
      "caption": "Full caption text...",
      "hashtags": ["#tag1", "#tag2"],
      "engagement_target": "1000 likes, 50 comments"
    }}
  ],
  "strategy_overview": {{
    "content_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
    "posting_frequency": "3 posts per week",
    "target_audience": "Primary audience description",
    "brand_voice": "Tone and style guidelines"
  }},
  "performance_targets": {{
    "monthly_reach": 50000,
    "engagement_rate": "4.5%",
    "follower_growth": "10% monthly"
  }}
}}

🎯 FOCUS: Create an actionable content strategy with specific posts and timing.
"""
        
        else:
            # Generic deliverable
            specific_instructions = f"""
📋 DELIVERABLE TYPE: PROJECT REPORT

✅ REQUIRED OUTPUT in detailed_results_json:
{{
  "deliverable_type": "project_report",
  "executive_summary": "2-3 sentence overview of what was accomplished",
  "key_findings": [
    "Main finding 1",
    "Main finding 2"
  ],
  "deliverables_created": [
    {{
      "name": "Deliverable Name",
      "description": "What it contains",
      "file_location": "Where to find it",
      "usage_instructions": "How to use it"
    }}
  ],
  "recommendations": [
    "Next step 1",
    "Next step 2"
  ],
  "project_metrics": {{
    "tasks_completed": {aggregated_data.get('total_tasks', 0)},
    "timeline": "Project duration",
    "success_criteria_met": "Yes/No with explanation"
  }}
}}

🎯 FOCUS: Create a comprehensive project report with actionable outcomes.
"""
        
        return base_context + specific_instructions

# Istanza globale
deliverable_aggregator = DeliverableAggregator()

# Funzione helper per integrazione con task_analyzer
async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """Wrapper function per integrazione con task_analyzer"""
    return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)