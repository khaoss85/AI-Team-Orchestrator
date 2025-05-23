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
        
        aggregated = {
            "total_tasks": len(completed_tasks),
            "task_summaries": [],
            "structured_data": {}, # Inizializzato come dizionario vuoto
            "key_insights": [],
            "recommendations": []
        }
        
        all_structured_data = []
        
        for task in completed_tasks:
            result = task.get("result", {}) or {}
            summary = result.get("summary", "")
            
            if summary and len(summary.strip()) > 10:
                aggregated["task_summaries"].append({
                    "task_name": task.get("name", ""),
                    "summary": summary,
                    "agent_role": task.get("assigned_to_role", ""), # Corretto da result.get(...) a task.get(...)
                    "completed_at": task.get("updated_at", "")
                })
            
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
                    pass # Ignora errori di parsing JSON per ora
            
            next_steps = result.get("next_steps", [])
            if isinstance(next_steps, list): # Assicurati che sia una lista
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
            data_sources_list = [item.get("task_name", "Unknown Source") for item in all_structured_data]
            aggregated["structured_data"] = {
                "all_data": all_structured_data,
                "data_sources": data_sources_list, # Ora è una lista di nomi
                "num_data_sources": len(all_structured_data) # Campo aggiuntivo per il conteggio
            }
        
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
        
        # Utilizza 'num_data_sources' per il conteggio
        num_sources = aggregated_data.get('structured_data', {}).get('num_data_sources', 0)
        # Se 'num_data_sources' non è presente o non è un intero, fai un fallback
        if not isinstance(num_sources, int):
            data_sources_list_check = aggregated_data.get('structured_data', {}).get('data_sources', [])
            num_sources = len(data_sources_list_check) if isinstance(data_sources_list_check, list) else 0

        base_context = f"""
🎯 OBJECTIVE: {goal}

📊 PROJECT SUMMARY (based on aggregated data):
- Total tasks outputs aggregated: {aggregated_data.get('total_tasks', 0)}
- Key insights extracted: {len(aggregated_data.get('key_insights', []))}
- Number of structured data sources considered: {num_sources}

🔍 YOUR MISSION: Based on the aggregated project data, create the FINAL DELIVERABLE document that directly and comprehensively addresses the project objective stated above.
Synthesize the information, key findings, and structured data provided in the 'context_data' of this task (specifically under 'aggregated_data') into a cohesive and actionable final output.
"""
        
        # Istruzioni specifiche per il tipo di deliverable (come prima)
        if deliverable_type == DeliverableType.CONTACT_LIST:
            num_actual_contacts = len(aggregated_data.get('structured_data', {}).get('contacts', []))
            collection_methods_list = aggregated_data.get('structured_data', {}).get('collection_methods', [])
            specific_instructions = f"""
📋 DELIVERABLE TYPE: CONTACT LIST

📈 DATA AVAILABLE FOR SYNTHESIS (from 'aggregated_data' in context):
- Total contacts found: {num_actual_contacts}
- Collection sources: {collection_methods_list}

✅ REQUIRED OUTPUT in detailed_results_json (your response):
{self._get_output_schema_instructions("contact_list")}

🎯 FOCUS: Create a clean, usable contact list ready for cold calling/outreach, including qualification scores and notes.
"""
        elif deliverable_type == DeliverableType.CONTENT_STRATEGY:
            total_content_pieces = len(aggregated_data.get('structured_data', {}).get('content_ideas', []))
            num_strategies = len(aggregated_data.get('structured_data', {}).get('strategies', []))
            specific_instructions = f"""
📋 DELIVERABLE TYPE: CONTENT STRATEGY

📈 DATA AVAILABLE FOR SYNTHESIS (from 'aggregated_data' in context):
- Content ideas generated: {total_content_pieces}
- Strategy components: {num_strategies}

✅ REQUIRED OUTPUT in detailed_results_json (your response):
{self._get_output_schema_instructions("content_strategy")}

🎯 FOCUS: Create an actionable content strategy with specific posts, timing, content pillars, and performance targets.
"""
        else: # Generic deliverable
            specific_instructions = f"""
📋 DELIVERABLE TYPE: PROJECT REPORT ({deliverable_type.value.replace('_', ' ').title() if deliverable_type else 'Generic'})

✅ REQUIRED OUTPUT in detailed_results_json (your response):
{self._get_output_schema_instructions(deliverable_type.value if deliverable_type else "generic_report")}

🎯 FOCUS: Create a comprehensive project report with an executive summary, key findings, list of deliverables created during the project, actionable recommendations, and relevant project metrics.
"""
        
        return base_context + specific_instructions

    # Assicurati che _get_output_schema_instructions sia definito come nella risposta precedente
    def _get_output_schema_instructions(self, deliverable_type_value: str) -> str:
        # Schemi JSON per i diversi tipi di deliverable
        schemas = {
            "contact_list": """
{
  "deliverable_type": "contact_list",
  "executive_summary": "Summary of the contact list generation process and quality.",
  "final_contact_list": [
    {
      "name": "Example Contact Name", 
      "company": "Example Company Inc.", 
      "email": "contact@example.com", 
      "phone": "+1-555-123-4567", 
      "title": "Chief Marketing Officer", 
      "source_task_name": "ICP Research Task X",
      "qualification_score": "8/10", 
      "notes": "Interested in AI solutions for B2B."
    }
  ],
  "list_statistics": { 
    "total_contacts_generated": 500, 
    "qualified_leads_criteria_met": 350,
    "primary_sources_used": ["LinkedIn Sales Navigator", "Apollo.io", "Company Websites"],
    "average_qualification_score": "7.5/10"
  },
  "usage_recommendations": [
    "Segment list by company size for tailored outreach.",
    "Prioritize contacts with qualification_score > 7 for initial email sequence.",
    "Follow up within 24-48 hours for best engagement."
  ]
}""",
            "content_strategy": """
{
  "deliverable_type": "content_strategy",
  "executive_summary": "Overview of the content strategy, target audience, and key objectives.",
  "content_pillars": ["Pillar 1: Educate on X", "Pillar 2: Showcase Y", "Pillar 3: Build Community Z"],
  "target_audience_personas": [
      {"name": "Persona A", "description": "Details of Persona A"},
      {"name": "Persona B", "description": "Details of Persona B"}
  ],
  "editorial_calendar_highlights": [
    {
      "month": "June 2025", "theme": "Theme for June", 
      "key_content_pieces": ["Blog Post: Title 1", "Webinar: Title 2", "Social Campaign: Theme A"]
    }
  ],
  "platform_strategy": {
      "linkedin": "Focus on thought leadership articles and case studies.",
      "instagram": "Utilize reels for short tips and user-generated content.",
      "blog": "In-depth guides and industry analysis."
  },
  "kpi_and_metrics": {
    "primary_kpis": ["Website Traffic Increase by X%", "Lead Generation Y per month", "Engagement Rate Z%"],
    "tracking_tools": ["Google Analytics", "MailUp Analytics", "Social Media Insights"]
  },
  "brand_voice_and_tone": "Professional yet approachable, expert but not condescending."
}""",
            "generic_report": """
{
  "deliverable_type": "project_report",
  "executive_summary": "A concise (2-3 sentences) overview of the project's main accomplishments and outcomes.",
  "project_goal_recap": "Restate the original project goal.",
  "key_findings_and_insights": [
    "Significant finding or insight 1, supported by data/evidence if possible.",
    "Significant finding or insight 2, detailing its impact or implication."
  ],
  "summary_of_deliverables_produced": [
    {
      "deliverable_name": "Name of a key output/document produced during the project",
      "description": "Brief description of what this deliverable contains and its purpose.",
      "link_or_reference_if_applicable": "e.g., 'See attached document' or 'Result of Task XYZ'"
    }
  ],
  "final_recommendations_and_next_steps": [
    "Actionable recommendation 1 based on project outcomes.",
    "Proposed next step 2 for future work or implementation."
  ],
  "overall_project_assessment": {
    "tasks_completed_ratio": "X/Y tasks completed",
    "budget_utilization_if_applicable": "Details on budget usage if tracked.",
    "timeline_adherence": "Assessment of how the project adhered to its timeline.",
    "challenges_faced_and_solutions": "Briefly mention any major challenges and how they were addressed.",
    "project_success_rating": "Qualitative assessment (e.g., Highly Successful, Partially Successful, Needs Improvement) with justification."
  }
}"""
        }
        return schemas.get(deliverable_type_value, schemas["generic_report"])


# Istanza globale
deliverable_aggregator = DeliverableAggregator()

# Funzione helper per integrazione con task_analyzer
async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """Wrapper function per integrazione con task_analyzer"""
    return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)