# backend/ai_agents/director.py
"""DirectorAgent

Genera e valida proposte di team di AI‑agents usando il paradigma tools‑within‑tools.
Include:
* fallback completo quando l'SDK "agents" non è disponibile
* protezioni anti‑loop (team size, handoff, nomi univoci)
* un'unica sorgente di costi (RATES_PER_DAY) condivisa fra estimatore e designer
* compatibilità Python 3.8 (niente `list[str]`, `set[str]`)
* fix per 'additionalProperties' error con l'SDK agents.
* raggruppamento skill avanzato in design_team_structure.
"""

import logging
import os
import re
import json
from typing import List, Dict, Any, Optional, Union, Set # Per type hints compatibili
from uuid import UUID
from enum import Enum

# ---------------------------------------------------------------------------
# logging first (serve prima di eventuali fallback che usano logger)
# ---------------------------------------------------------------------------
logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try modern SDK, fall back gracefully
# ---------------------------------------------------------------------------
try:
    from agents import Agent as OpenAIAgent, Runner, ModelSettings, function_tool # type: ignore
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("Modern 'agents' SDK not found; falling back to 'openai_agents'. Advanced features may be unavailable.")
    try:
        # legacy sdk
        from openai_agents import Agent as OpenAIAgent, Runner, ModelSettings, function_tool # type: ignore
    except ImportError: # ultimate fallback (no runtime execution, but code loads)
        logger.error("No compatible Agent SDK found. DirectorAgent will operate in degraded mode.")

        class OpenAIAgent: # type: ignore
            def __init__(self, *args, **kwargs): pass
        class Runner: # type: ignore
            @staticmethod
            async def run(*_a, **_kw):
                # Simula un oggetto RunResult con un campo final_output per evitare AttributeError
                class DummyRunResult:
                    final_output: str = "{}" # Fallback JSON vuoto
                logger.error("Runner.run called but SDK is unavailable. Returning dummy error output.")
                error_payload = {
                    "error": "SDK unavailable",
                    "message": "Cannot execute LLM call without 'agents' or 'openai_agents' package."
                }
                # Per i tool che si aspettano un JSON di un certo tipo, questo potrebbe comunque fallire
                # ma almeno il Runner.run non dà AttributeError
                if _kw.get("prompt", "").startswith("Analyze requirements"): # analyze_project_requirements_llm
                    error_payload = {
                        "required_skills": [], "expertise_areas": [], "recommended_team_size": 1,
                        "rationale": "Fallback due to unavailable SDK."}
                elif _kw.get("prompt", "").startswith("Generate team proposal"): # create_team_proposal
                     error_payload = {
                         "agents": [], "handoffs": [], "estimated_cost": {"total_estimated_cost":0},
                         "rationale": "Fallback due to unavailable SDK."}

                DummyRunResult.final_output = json.dumps(error_payload)
                return DummyRunResult

        class ModelSettings: # type: ignore
            def __init__(self, *args, **kwargs): pass
        def function_tool(func): # type: ignore
            return func

# ---------------------------------------------------------------------------
# Local project imports (pydantic models)
# ---------------------------------------------------------------------------
from models import (
    DirectorConfig,
    DirectorTeamProposal,
    AgentCreate,
    AgentSeniority,
    HandoffProposalCreate,
)
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Module‑level constants (single source of truth)
# ---------------------------------------------------------------------------
MAX_TEAM_SIZE: int = 6 # hard cap per workspace
RATES_PER_DAY: Dict[str, int] = { # EUR/giorno
    AgentSeniority.JUNIOR.value: 8,
    AgentSeniority.SENIOR.value: 15,
    AgentSeniority.EXPERT.value: 25,
}
COST_PER_MONTH: Dict[str, int] = {k: v * 30 for k, v in RATES_PER_DAY.items()}
MODEL_BY_SENIORITY: Dict[str, str] = {
    AgentSeniority.JUNIOR.value: "gpt-4.1-nano",
    AgentSeniority.SENIOR.value: "gpt-4.1-mini",
    AgentSeniority.EXPERT.value: "gpt-4.1",
}
# Domain mapping per raggruppamento skill in design_team_structure
DOMAIN_MAPPING_DESIGN: Dict[str, List[str]] = {
    'management': ['manage', 'coordina', 'plan', 'lead', 'oversight', 'project manage'],
    'analysis': ['analy', 'research', 'investigat', 'evaluat', 'data', 'report', 'business intelligence', 'data mining', 'statistics'],
    'content': ['content', 'writ', 'edit', 'communicat', 'copywrit', 'translate', 'proofread', 'blog', 'article'],
    'marketing': ['market', 'promot', 'social media', 'brand', 'campaign', 'seo', 'advertis', 'digital market'],
    'technical': ['develop', 'implement', 'cod', 'engine', 'architect', 'design', 'test', 'qa', 'it support', 'software', 'frontend', 'backend', 'database', 'cloud', 'devops'],
    'financial': ['financ', 'budget', 'account', 'invest', 'payroll', 'cost analy'],
    'creative_design': ['design', 'graphic', 'ui/ux', 'visual', 'art', 'illustration', 'logo'], # 'creative' rinominato per chiarezza
    'legal': ['legal', 'compliance', 'contract', 'regulation'],
    'hr': ['human resource', 'recruitment', 'hr', 'talent acquisition', 'onboarding'],
    'customer_service': ['customer service', 'support', 'client interaction', 'helpdesk'],
    'sales': ['sales', 'business development', 'lead generation', 'negotiation'],
    # 'other_domain' sarà usato per skill non mappate
}


# ---------------------------------------------------------------------------
# Typed helper for structured output (già presente, verificata)
# ---------------------------------------------------------------------------
class ProjectAnalysisOutput(BaseModel):
    required_skills: List[str]
    expertise_areas: List[str]
    recommended_team_size: int
    rationale: str

# ---------------------------------------------------------------------------
# DirectorAgent definition
# ---------------------------------------------------------------------------
class DirectorAgent:
    """Crea proposte di team di AI‑agents evitando delega circolare."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY") and SDK_AVAILABLE:
            logger.warning("OPENAI_API_KEY non impostata – i tools LLM potrebbero fallire.")
        self.max_team_size: int = MAX_TEAM_SIZE
        self.min_team_size: int = 1
        self.max_coordinator_ratio: float = 0.4

    @staticmethod
    @function_tool
    async def analyze_project_requirements_llm(goal: str, constraints_json: str) -> str:
        """Restituisce JSON con skill, aree di expertise, team raccomandato. 'constraints_json' DEVE essere una stringa JSON valida."""
        logger.info("Director Tool: analyze_project_requirements_llm invoked")
        try:
            constraints_dict: Dict[str, Any] = {}
            try:
                constraints_dict = json.loads(constraints_json)
            except json.JSONDecodeError:
                logger.warning(f"constraints_json non era un JSON valido: {constraints_json[:100]}. Trattato come testo grezzo.")
                constraints_dict = {"raw_constraints": constraints_json} # Fallback se non è JSON

            budget = (
                constraints_dict.get("max_amount")
                or constraints_dict.get("budget", {}).get("max_amount")
                or constraints_dict.get("budget_constraint", {}).get("max_amount")
                or 0
            )
            if not isinstance(budget, (int, float)): budget = 0 # Ensure budget is numeric

            instruction = f"""You are a strategic project analyst AI.
Project Goal: \"{goal}\"
Constraints (from JSON string): {json.dumps(constraints_dict)}
Budget (EUR): {budget or 'Not specified'}

CRITICAL GUIDELINES:
1. Keep team size CONSERVATIVE (1-{MAX_TEAM_SIZE}).
2. Focus on ESSENTIAL skills only – avoid redundancy. Combine related skills where possible.
3. Consider budget strictly.
4. Prefer versatile agents when budget is tight.
5. Each agent must have CLEAR, NON‑OVERLAPPING responsibilities.

TEAM SIZE RULE OF THUMB (EUR):
<1500 ⇒ 1‑2 | 1500‑3000 ⇒ 2‑3 | 3000‑5000 ⇒ 3‑4 | >5000 ⇒ up to {MAX_TEAM_SIZE}

Return *only* valid JSON as a string:
{{
  "required_skills": ["Skill 1", "Aggregated Skill 2 (e.g. Content Creation encompassing writing, editing)"],
  "expertise_areas": ["Domain 1", "Broader Area 2"],
  "recommended_team_size": X,
  "rationale": "Brief explanation for skills, expertise, and team size, considering budget and skill aggregation."
}}"""

            analyzer = OpenAIAgent(
                name="ProjectRequirementsAnalyzer",
                instructions=instruction,
                model="gpt-4.1",
                model_settings=ModelSettings(temperature=0.2),
            )
            result = await Runner.run(analyzer, "Analyze requirements and output structured JSON.")
            raw_output = result.final_output
            
            data: Dict[str, Any] = {}
            parsed_ok = False
            try:
                data = json.loads(raw_output)
                parsed_ok = True
            except json.JSONDecodeError:
                match = re.search(r"```json\s*({[\s\S]*?})\s*```", raw_output, re.DOTALL) or \
                        re.search(r"({[\s\S]*})", raw_output, re.DOTALL) # DOTALL per multiline
                if match:
                    try:
                        data = json.loads(match.group(1))
                        parsed_ok = True
                    except json.JSONDecodeError:
                        logger.error(f"analyze_project: Could not parse extracted JSON: {match.group(1)[:200]}")
                else:
                    logger.error(f"analyze_project: Could not extract JSON from raw output: {raw_output[:200]}")

            if not parsed_ok or not isinstance(data, dict) or not data.get("required_skills") : # Check for a key field
                logger.warning("analyze_project: Fallback due to parsing error or missing critical fields.")
                data = {
                    "required_skills": ["project_management", "general_task_execution"],
                    "expertise_areas": ["general_business"],
                    "recommended_team_size": 2,
                    "rationale": "Fallback due to parsing error or incomplete LLM output for project analysis."
                }

            ts = data.get("recommended_team_size", 2)
            if not isinstance(ts, int) or ts < 1: ts = 1 # Min 1
            data["recommended_team_size"] = min(ts, MAX_TEAM_SIZE) # Cap at max
            # Ensure all fields for ProjectAnalysisOutput are present
            data.setdefault("required_skills", ["project_management"])
            data.setdefault("expertise_areas", ["general"])
            data.setdefault("rationale", "Analysis completed.")
            
            return json.dumps(data)

        except Exception as exc:
            logger.error(f"analyze_project_requirements_llm failed critically: {exc}", exc_info=True)
            return json.dumps({
                "required_skills": ["critical_fallback_skill"], "expertise_areas": ["error_handling"],
                "recommended_team_size": 1, "rationale": f"Critical fallback in analysis tool: {exc}"})

    @staticmethod
    @function_tool
    async def estimate_costs(team_composition_json: str, duration_days: Optional[int] = None) -> str:
        """
        Stima i costi del team.

        Args:
            team_composition_json: Stringa JSON contenente la lista di specifiche agenti.
            duration_days: Durata del progetto in giorni. Se non specificato, usa 30 giorni come default.

        Returns:
            JSON string con i costi stimati e breakdown per agente.
        """
        # Gestisci il default internamente
        actual_duration = duration_days if duration_days is not None and duration_days > 0 else 30
        logger.info(f"Director Tool: estimate_costs invoked for {actual_duration} days.")

        try:
            agents_specs: List[Dict[str, Any]] = json.loads(team_composition_json)
            if not isinstance(agents_specs, list):
                raise ValueError("team_composition_json must be a list of agent specifications.")

            total_cost = 0.0
            cost_breakdown: Dict[str, float] = {}
            for agent_spec in agents_specs:
                seniority_val = agent_spec.get("seniority", AgentSeniority.JUNIOR.value)
                # Handle if seniority_val is an Enum member or string
                if isinstance(seniority_val, Enum):
                    seniority_str = seniority_val.value
                else:
                    seniority_str = str(seniority_val).lower()

                rate = RATES_PER_DAY.get(seniority_str, RATES_PER_DAY[AgentSeniority.JUNIOR.value])
                agent_cost = rate * actual_duration
                total_cost += agent_cost
                agent_name = agent_spec.get('name', 'UnnamedAgent')
                cost_breakdown[f"{agent_name} ({seniority_str})"] = round(agent_cost, 2)

            return json.dumps({
                "total_estimated_cost": round(total_cost, 2), "currency": "EUR",
                "estimated_duration_days": actual_duration, "breakdown_by_agent": cost_breakdown,
                "notes": "Cost estimates are based on projected daily rates and duration."})
        except Exception as exc:
            logger.error(f"estimate_costs failed: {exc}", exc_info=True)
            return json.dumps({"error": str(exc), "total_estimated_cost": 0, "notes": "Error during cost estimation."})

    @staticmethod
    @function_tool
    async def design_team_structure(required_skills_json: str, budget_total: float, max_agents: Optional[int] = None) -> str:
        """Progetta la struttura del team. 'required_skills_json' è una stringa JSON di una lista di skill."""
        logger.info(f"Director Tool: design_team_structure invoked. Max_agents: {max_agents}, Budget: {budget_total}")
        try:
            required_skills: List[str] = json.loads(required_skills_json)
            
            # Determine effective_max_agents respecting MAX_TEAM_SIZE
            eff_max_agents = MAX_TEAM_SIZE
            if isinstance(max_agents, int) and 0 < max_agents <= MAX_TEAM_SIZE:
                eff_max_agents = max_agents
            elif not required_skills: # No skills, no complex team needed
                eff_max_agents = 1
            # If max_agents is invalid or None, eff_max_agents remains MAX_TEAM_SIZE, or 1 if no skills.

            team: List[Dict[str, Any]] = []
            allocated_budget = 0.0
            agents_created_count = 0

            # --- Helper functions specific to design_team_structure ---
            def _get_model_for_design(s_val: str) -> str:
                return MODEL_BY_SENIORITY.get(s_val.lower(), MODEL_BY_SENIORITY[AgentSeniority.JUNIOR.value])

            def _get_tools_for_design(role_str: str, s_val: str) -> List[Dict[str, str]]:
                tools_list: List[Dict[str, str]] = []
                if s_val.lower() in (AgentSeniority.SENIOR.value, AgentSeniority.EXPERT.value) or "manager" in role_str.lower():
                    tools_list.append({"type": "web_search", "name": "web_search", "description": "Enables web searching for current information."})
                if any(k_word in role_str.lower() for k_word in ("content", "research", "analysis", "market", "manager", "writing")):
                    tools_list.append({"type": "file_search", "name": "file_search", "description": "Enables searching through provided documents."})
                return tools_list
     
            def _generate_personality_for_role(role_str: str) -> Dict[str, Any]:
                """Genera attributi di personalità basati sul ruolo."""
                role_lower = role_str.lower()

                # Default traits for all agents
                personality = {
                    "first_name": "",
                    "last_name": "",
                    "personality_traits": [],
                    "communication_style": "",
                    "hard_skills": [],
                    "soft_skills": [],
                    "background_story": ""
                }

                # Generate a suitable first name and last name
                import random
                first_names = ["Alex", "Sam", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Avery", "Quinn", "Jamie"]
                last_names = ["Chen", "Smith", "Rodriguez", "Johnson", "Patel", "Wilson", "Garcia", "Martinez", "Lee", "Brown"]
                personality["first_name"] = random.choice(first_names)
                personality["last_name"] = random.choice(last_names)

                # Set personality traits based on role
                if "manager" in role_lower or "coordinator" in role_lower or "lead" in role_lower:
                    personality["personality_traits"] = ["DECISIVE", "COLLABORATIVE", "PROACTIVE"]
                    personality["communication_style"] = "ASSERTIVE"
                    personality["soft_skills"] = [
                        {"name": "Leadership", "level": "EXPERT"},
                        {"name": "Communication", "level": "EXPERT"},
                        {"name": "Team Coordination", "level": "EXPERT"}
                    ]

                elif "analyst" in role_lower or "research" in role_lower:
                    personality["personality_traits"] = ["ANALYTICAL", "DETAIL_ORIENTED", "METHODICAL"]
                    personality["communication_style"] = "TECHNICAL"
                    personality["soft_skills"] = [
                        {"name": "Critical Thinking", "level": "EXPERT"},
                        {"name": "Problem Solving", "level": "EXPERT"}
                    ]

                elif "content" in role_lower or "writ" in role_lower:
                    personality["personality_traits"] = ["CREATIVE", "DETAIL_ORIENTED", "ADAPTABLE"]
                    personality["communication_style"] = "DETAILED"
                    personality["soft_skills"] = [
                        {"name": "Creativity", "level": "EXPERT"},
                        {"name": "Writing", "level": "EXPERT"}
                    ]

                elif "develop" in role_lower or "engineer" in role_lower:
                    personality["personality_traits"] = ["ANALYTICAL", "METHODICAL", "INNOVATIVE"]
                    personality["communication_style"] = "TECHNICAL"
                    personality["soft_skills"] = [
                        {"name": "Problem Solving", "level": "EXPERT"},
                        {"name": "Logical Thinking", "level": "EXPERT"}
                    ]

                else:
                    # Default traits for unknown roles
                    personality["personality_traits"] = ["ADAPTABLE", "COLLABORATIVE", "PROACTIVE"]
                    personality["communication_style"] = "CONCISE"
                    personality["soft_skills"] = [
                        {"name": "Adaptability", "level": "EXPERT"},
                        {"name": "Communication", "level": "INTERMEDIATE"}
                    ]

                # Add hard skills based on role keywords
                hard_skills = []
                if "analyst" in role_lower:
                    hard_skills.append({"name": "Data Analysis", "level": "EXPERT"})
                    hard_skills.append({"name": "Statistics", "level": "EXPERT"})
                if "content" in role_lower or "writ" in role_lower:
                    hard_skills.append({"name": "Content Creation", "level": "EXPERT"})
                    hard_skills.append({"name": "Editing", "level": "EXPERT"})
                if "develop" in role_lower or "engineer" in role_lower:
                    hard_skills.append({"name": "Software Development", "level": "EXPERT"})
                    hard_skills.append({"name": "Problem Solving", "level": "EXPERT"})
                if "market" in role_lower:
                    hard_skills.append({"name": "Market Research", "level": "EXPERT"})
                    hard_skills.append({"name": "Campaign Planning", "level": "EXPERT"})

                # If no specific hard skills were added, add general ones
                if not hard_skills:
                    hard_skills.append({"name": "Problem Solving", "level": "EXPERT"})
                    hard_skills.append({"name": "Research", "level": "INTERMEDIATE"})

                personality["hard_skills"] = hard_skills

                # Add a background story based on role
                if "manager" in role_lower:
                    personality["background_story"] = "Experienced project manager with a track record of successfully coordinating cross-functional teams on complex projects."
                elif "analyst" in role_lower:
                    personality["background_story"] = "Data-driven analyst with expertise in extracting actionable insights from complex datasets."
                elif "content" in role_lower:
                    personality["background_story"] = "Creative content specialist with a passion for crafting engaging narratives that resonate with target audiences."
                elif "develop" in role_lower:
                    personality["background_story"] = "Skilled developer with experience building robust solutions to complex technical challenges."
                else:
                    personality["background_story"] = f"Specialized {role_str} with extensive experience in delivering high-quality results."

                return personality

            def _group_skills_for_design(skills_list: List[str]) -> List[Dict[str, Any]]:
                s_groups: Dict[str, List[str]] = {domain_key: [] for domain_key in DOMAIN_MAPPING_DESIGN}
                s_groups['other_domain'] = [] # For unmapped skills
                
                processed: Set[str] = set()
                for skill_item in skills_list:
                    normalized_skill = skill_item.lower()
                    if normalized_skill in processed: continue
                    
                    assigned = False
                    for domain_key, keywords in DOMAIN_MAPPING_DESIGN.items():
                        if any(kw in normalized_skill for kw in keywords):
                            s_groups[domain_key].append(skill_item) # Store original skill name
                            assigned = True
                            break 
                    if not assigned:
                        s_groups['other_domain'].append(skill_item)
                    processed.add(normalized_skill)
                
                final_skill_groups: List[Dict[str, Any]] = []
                for domain_name_key, skills_in_group_list in s_groups.items():
                    if skills_in_group_list:
                        final_skill_groups.append({
                            'domain': domain_name_key if domain_name_key != 'other_domain' else None,
                            'skills': skills_in_group_list,
                            'importance': 'high' if domain_name_key in ['management', 'technical', 'analysis', 'sales'] else 'medium'
                        })
                return final_skill_groups

            # --- Main design logic ---
            # 1. Add Project Manager if team > 1 agent and budget allows
            if eff_max_agents > 1:
                pm_s_val = AgentSeniority.SENIOR.value
                pm_c_val = COST_PER_MONTH[pm_s_val]
                if allocated_budget + pm_c_val <= budget_total and agents_created_count < eff_max_agents:
                    pm_personality = _generate_personality_for_role("Project Manager")

                    team.append({
                        "name": "ProjectManager", "role": "Project Manager", "seniority": pm_s_val,
                        "description": "Oversees project execution, coordinates team, manages communication and ensures goal alignment.",
                        "system_prompt": "You are a Project Manager. Your primary goal is to lead the team to successfully complete the project. Coordinate tasks, manage resources, resolve blockers, and ensure clear communication. You are expected to handle coordination tasks yourself rather than delegating them further.",
                        "llm_config": {"model": _get_model_for_design(pm_s_val), "temperature": 0.3},
                        "tools": _get_tools_for_design("Project Manager", pm_s_val),
                        "first_name": pm_personality["first_name"],
                        "last_name": pm_personality["last_name"],
                        "personality_traits": pm_personality["personality_traits"],
                        "communication_style": pm_personality["communication_style"],
                        "hard_skills": pm_personality["hard_skills"],
                        "soft_skills": pm_personality["soft_skills"],
                        "background_story": pm_personality["background_story"]
                    })
                    allocated_budget += pm_c_val; agents_created_count += 1
            
            # 2. Group remaining skills
            skills_to_assign = required_skills
            if any(a.get("role") == "Project Manager" for a in team): # If PM exists, filter out mgmt skills
                mgmt_keywords = DOMAIN_MAPPING_DESIGN.get('management', [])
                skills_to_assign = [s for s in required_skills if not any(kw in s.lower() for kw in mgmt_keywords)]
            
            skill_groups_list = _group_skills_for_design(skills_to_assign)

            # 3. Create specialists for skill groups
            for group_item in skill_groups_list:
                if agents_created_count >= eff_max_agents or allocated_budget >= budget_total: break
                if not group_item['skills']: continue

                # Determine seniority based on remaining budget per slot and importance
                s_val = AgentSeniority.JUNIOR.value # Default
                slots_remaining = eff_max_agents - agents_created_count
                if slots_remaining > 0:
                    avg_budget_per_slot = (budget_total - allocated_budget) / slots_remaining
                    if avg_budget_per_slot >= COST_PER_MONTH[AgentSeniority.EXPERT.value] and group_item['importance'] == 'high':
                        s_val = AgentSeniority.EXPERT.value
                    elif avg_budget_per_slot >= COST_PER_MONTH[AgentSeniority.SENIOR.value]:
                        s_val = AgentSeniority.SENIOR.value
                
                agent_cost = COST_PER_MONTH[s_val]
                # Downgrade if current seniority choice exceeds budget for this agent
                if allocated_budget + agent_cost > budget_total:
                    if s_val == AgentSeniority.EXPERT.value and allocated_budget + COST_PER_MONTH[AgentSeniority.SENIOR.value] <= budget_total:
                        s_val = AgentSeniority.SENIOR.value
                    elif s_val != AgentSeniority.JUNIOR.value and allocated_budget + COST_PER_MONTH[AgentSeniority.JUNIOR.value] <= budget_total:
                        s_val = AgentSeniority.JUNIOR.value
                    else: continue # Cannot afford even a Junior for this group
                    agent_cost = COST_PER_MONTH[s_val] # Update cost after downgrade

                # Create agent name and role
                skill_name_base = group_item['skills'][0].replace('_', ' ').title()
                domain_name_part = group_item['domain'].title().replace('_', '') + "" if group_item['domain'] and group_item['domain'] != "OtherDomain" else ""
                name_prefix = domain_name_part if domain_name_part else re.sub(r'\W+', '', skill_name_base.split(' ')[0])
                
                base_agent_name = f"{name_prefix}Specialist"
                unique_agent_name = base_agent_name
                name_counter = 1
                while any(a.get("name") == unique_agent_name for a in team):
                    unique_agent_name = f"{base_agent_name}{name_counter}"; name_counter += 1
                
                agent_role_title = f"{domain_name_part} {skill_name_base} Specialist" if domain_name_part else f"{skill_name_base} Specialist"
                specialist_personality = _generate_personality_for_role(agent_role_title)
                team.append({
                    "name": unique_agent_name, 
                    "role": agent_role_title.strip(), 
                    "seniority": s_val,
                    "description": f"Handles tasks related to: {', '.join(group_item['skills'])} within the {group_item['domain'] or 'general'} domain.",
                    "system_prompt": f"You are a {agent_role_title.strip()}. Your expertise covers: {', '.join(group_item['skills'])}. Complete tasks efficiently, collaborate when necessary, and avoid re-delegating tasks within your scope.",
                    "llm_config": {"model": _get_model_for_design(s_val), "temperature": 0.35},
                    "tools": _get_tools_for_design(agent_role_title, s_val),
                    "first_name": specialist_personality["first_name"],
                    "last_name": specialist_personality["last_name"],
                    "personality_traits": specialist_personality["personality_traits"],
                    "communication_style": specialist_personality["communication_style"],
                    "hard_skills": specialist_personality["hard_skills"],
                    "soft_skills": specialist_personality["soft_skills"],
                    "background_story": specialist_personality["background_story"]
                })
                allocated_budget += agent_cost; agents_created_count += 1

            if not team and required_skills: # If no agents were created but skills were listed
                logger.warning("design_team_structure: No agents created, attempting minimal fallback agent.")
                s_val = AgentSeniority.JUNIOR.value
                if budget_total >= COST_PER_MONTH[s_val] and agents_created_count < eff_max_agents:
                    fallback_personality = _generate_personality_for_role("General Task Executor")
                    team.append({
                        "name": "GeneralTaskExecutor", "role": "General Task Executor", "seniority": s_val,
                        "description": "Handles general project tasks due to constraints.",
                        "system_prompt": "You are a General Task Executor. Handle all assigned tasks efficiently.",
                        "llm_config": {"model": _get_model_for_design(s_val), "temperature": 0.4},
                        "tools": _get_tools_for_design("General Task Executor", s_val),
                        "first_name": fallback_personality["first_name"],
                        "last_name": fallback_personality["last_name"],
                        "personality_traits": fallback_personality["personality_traits"],
                        "communication_style": fallback_personality["communication_style"],
                        "hard_skills": fallback_personality["hard_skills"],
                        "soft_skills": fallback_personality["soft_skills"],
                        "background_story": fallback_personality["background_story"]
                    })
                else:
                    logger.error("design_team_structure: Could not create even a fallback agent.")
                    return json.dumps([{"error": "Unable to design any agent within budget/constraints."}])
            
            logger.info(f"Team designed with {len(team)} agents. Budget used: {allocated_budget:.2f}/{budget_total:.2f}.")
            return json.dumps(team)
        except Exception as exc:
            logger.error(f"design_team_structure critically failed: {exc}", exc_info=True)
            return json.dumps([{"error": f"Critical failure in team design: {exc}"}])

    def _is_same_role_type(self, role1: str, role2: str) -> bool:
        """Checks if two roles are of the same broad type (manager, specialist)."""
        if not role1 or not role2: return False
        r1_lower, r2_lower = role1.lower(), role2.lower()
        manager_kw = ("manager", "coordinator", "director", "lead", "supervisor")
        # Specialist can include analyst, researcher, etc.
        specialist_kw = ("specialist", "expert", "developer", "engineer", "writer", "designer", "analyst", "researcher", "consultant", "artist")
        
        def get_broad_type(role_str: str) -> str:
            if any(kw in role_str for kw in manager_kw): return "manager"
            if any(kw in role_str for kw in specialist_kw): return "specialist"
            return "other"
            
        type_r1, type_r2 = get_broad_type(r1_lower), get_broad_type(r2_lower)
        return type_r1 == type_r2 and type_r1 != "other"

    async def create_team_proposal(self, config: DirectorConfig) -> DirectorTeamProposal:
        logger.info(f"Director: Creating team proposal for workspace {config.workspace_id}")

        # Instructions per l'LLM orchestratore
        # L'LLM deve capire che `constraints_json` per `analyze_project_requirements_llm` deve essere una stringa JSON.
        # E che `required_skills_json` e `team_composition_json` per gli altri tool sono anche stringhe JSON.
        director_instructions = f"""You are an expert AI team architect. Your goal is to design an efficient team of AI agents.
Max team size is {self.max_team_size}.
Project Goal: {config.goal}
Budget Constraints (passed as JSON string to analysis tool): {json.dumps(config.budget_constraint)}
User Feedback (if any): {config.user_feedback or "None"}

Follow these steps precisely using the provided tools:
1.  **Analyze Requirements**: Call `analyze_project_requirements_llm` with the project `goal` and `constraints_json` (which must be a JSON string representing the budget and other constraints). This will return a JSON string with `required_skills`, `expertise_areas`, `recommended_team_size`, and `rationale`.
2.  **Design Team Structure**: Call `design_team_structure` using:
    * `required_skills_json`: The `required_skills` list from step 1, formatted as a JSON string.
    * `budget_total`: The `max_amount` from the budget constraints (float).
    * `max_agents`: The `recommended_team_size` (int) from step 1.
    This tool returns a JSON string list of agent specifications.
3.  **Estimate Costs**: Call `estimate_costs` using:
    * `team_composition_json`: The list of agents from step 2, formatted as a JSON string.
    * `duration_days`: (Optional, defaults to 30) An estimated project duration in days.
    This returns a JSON string with cost details.
4.  **Define Handoffs**: Based on the team from step 2, define a list of handoff objects. Each handoff should have `from` (source agent name), `to` (list of target agent names), and `description`. Ensure handoffs are minimal, logical, and prevent loops (e.g., manager to specialist, specialist to specialist, specialist escalates to manager for critical issues only).
5.  **Final Rationale**: Provide a brief rationale for your overall team design and handoff strategy.

Your final output MUST be a single, valid JSON object containing the keys: "agents", "handoffs", "estimated_cost", and "rationale".
Do NOT include any markdown formatting or explanatory text outside this JSON structure.
Example for passing JSON string to tools: If constraints are {{"budget": 1000}}, pass it as the string "{{\\"budget\\": 1000}}".
"""
        available_tools_list = [
            DirectorAgent.analyze_project_requirements_llm,
            DirectorAgent.estimate_costs,
            DirectorAgent.design_team_structure,
        ]
        llm_director_agent = OpenAIAgent(
            name="EfficientTeamDirectorLLM",
            instructions=director_instructions,
            model="gpt-4.1", # Or "gpt-4-turbo" / "gpt-4o" if available and preferred
            model_settings=ModelSettings(temperature=0.1), # Low temperature for more deterministic output
            tools=available_tools_list,
        )
        try:
            # The prompt to the LLM Director agent. It needs to understand how to use the tools.
            # The LLM will make multiple tool calls based on the instructions.
            initial_user_prompt = (
                "Please generate the AI agent team proposal as per your detailed instructions. "
                "Ensure all tool inputs requiring JSON strings are correctly formatted. "
                "Your final response must be only the complete JSON proposal object."
            )
            run_result_obj = await Runner.run(llm_director_agent, initial_user_prompt)
            raw_llm_output_json_str = run_result_obj.final_output
            logger.debug(f"Director LLM raw output for proposal: {raw_llm_output_json_str}")

            proposal_dict: Optional[Dict[str, Any]] = None
            try:
                proposal_dict = json.loads(raw_llm_output_json_str)
            except json.JSONDecodeError:
                logger.warning("LLM output for proposal is not valid JSON, attempting extraction...")
                # Regex to find JSON block, even if wrapped in markdown
                match_obj = re.search(r"```json\s*({[\s\S]*?})\s*```", raw_llm_output_json_str, re.DOTALL) or \
                            re.search(r"({[\s\S]*})", raw_llm_output_json_str, re.DOTALL)
                if match_obj:
                    try:
                        proposal_dict = json.loads(match_obj.group(1))
                    except json.JSONDecodeError as e_inner:
                        logger.error(f"Failed to parse extracted JSON for proposal: {e_inner}. Extracted: {match_obj.group(1)[:200]}")
            
            if proposal_dict is None or not isinstance(proposal_dict, dict) or not proposal_dict.get("agents"):
                logger.error(f"Could not parse or extract valid JSON proposal from LLM. Using fallback. Output: {raw_llm_output_json_str[:300]}")
                proposal_dict = self._create_fallback_dict(config) # Use dict fallback first

            # Validate and sanitize the dictionary before creating Pydantic models
            validated_proposal_data = self._validate_and_sanitize_proposal(proposal_dict, config)

            agents_create_obj_list: List[AgentCreate] = []
            for agent_spec_dict in validated_proposal_data.get("agents", []):
                agent_spec_dict["workspace_id"] = config.workspace_id # Ensure UUID is passed
                
                # Robust seniority handling before Pydantic model creation
                s_input = agent_spec_dict.get('seniority')
                s_value_str: str
                if isinstance(s_input, AgentSeniority): s_value_str = s_input.value
                elif isinstance(s_input, str): s_value_str = s_input.lower()
                else: s_value_str = AgentSeniority.JUNIOR.value # Default
                try:
                    agent_spec_dict['seniority'] = AgentSeniority(s_value_str) # Convert to Enum for Pydantic
                except ValueError:
                    agent_spec_dict['seniority'] = AgentSeniority.JUNIOR

                # Ensure tools is a list of dicts
                tools_list_sanitized: List[Dict[str,str]] = []
                raw_tools = agent_spec_dict.get("tools", [])
                if isinstance(raw_tools, list):
                    for t_item in raw_tools:
                        if isinstance(t_item, str): # If tool is just a name string
                            tools_list_sanitized.append({"name": t_item, "type": "function", "description": f"Tool: {t_item}"})
                        elif isinstance(t_item, dict) and "name" in t_item:
                            t_item.setdefault("type", "function")
                            t_item.setdefault("description", f"Tool: {t_item['name']}")
                            tools_list_sanitized.append(t_item) # type: ignore
                agent_spec_dict["tools"] = tools_list_sanitized
                
                try:
                    agents_create_obj_list.append(AgentCreate(**agent_spec_dict))
                except Exception as e_ac: # Catch Pydantic validation errors etc.
                    logger.error(f"Error creating AgentCreate for agent '{agent_spec_dict.get('name')}': {e_ac}", exc_info=True)

            handoffs_obj_list: List[HandoffProposalCreate] = []
            for h_spec in validated_proposal_data.get("handoffs", []):
                if h_spec.get("from") and h_spec.get("to"):
                    # Ensure 'to' is List[str] for HandoffProposalCreate
                    if isinstance(h_spec["to"], str): h_spec["to"] = [h_spec["to"]]
                    try:
                        handoffs_obj_list.append(HandoffProposalCreate(**h_spec))
                    except Exception as e_hc: # Catch Pydantic validation errors etc.
                         logger.warning(f"Skipping invalid handoff spec {h_spec}: {e_hc}")
            
            extra_data_for_proposal: Dict[str, Any] = {}
            if hasattr(config, 'user_feedback') and config.user_feedback:
                extra_data_for_proposal["user_feedback"] = config.user_feedback

            return DirectorTeamProposal(
                workspace_id=config.workspace_id, # UUID
                agents=agents_create_obj_list,
                handoffs=handoffs_obj_list,
                estimated_cost=validated_proposal_data.get("estimated_cost", {"total_estimated_cost": 0, "currency": "EUR"}),
                rationale=validated_proposal_data.get("rationale", "Team proposal generated by DirectorAgent."),
                **extra_data_for_proposal
            )
        except Exception as exc_outer:
            logger.error(f"create_team_proposal critically failed: {exc_outer}", exc_info=True)
            return self._create_minimal_fallback_proposal(config, str(exc_outer))

    def _validate_and_sanitize_proposal(self, data: Dict[str, Any], config: DirectorConfig) -> Dict[str, Any]:
        """Validates and sanitizes the raw proposal dictionary from LLM."""
        agents_list: List[Dict[str, Any]] = data.get("agents", [])
        if not agents_list or not isinstance(agents_list, list): # If no agents or not a list, use default
            logger.warning("_validate_and_sanitize_proposal: No agents found or invalid format, creating default.")
            data = self._create_fallback_dict(config) # This returns a dict with 'agents'
            agents_list = data["agents"]

        # 1. Cap team size
        if len(agents_list) > self.max_team_size:
            logger.info(f"Team size {len(agents_list)} exceeds max {self.max_team_size}. Truncating.")
            agents_list = agents_list[:self.max_team_size]

        # 2. Ensure unique agent names
        final_agents_list: List[Dict[str, Any]] = []
        seen_agent_names: Set[str] = set()
        for idx, agent_data in enumerate(agents_list):
            base_name = agent_data.get("name", f"Agent{idx+1}")
            current_name = base_name
            name_idx = 1
            while current_name in seen_agent_names:
                current_name = f"{base_name}_{name_idx}"; name_idx += 1
            if current_name != base_name: logger.info(f"Sanitized agent name from '{base_name}' to '{current_name}'.")
            agent_data["name"] = current_name
            seen_agent_names.add(current_name)

            # Normalize case for enum values to fix Pydantic validation errors
            # Fix personality_traits enum values
            if "personality_traits" in agent_data and isinstance(agent_data["personality_traits"], list):
                sanitized_traits = []
                for trait in agent_data["personality_traits"]:
                    if isinstance(trait, str):
                        # Replace underscores with hyphens for enum compatibility
                        normalized_trait = trait.lower().replace("_", "-")
                        sanitized_traits.append(normalized_trait)
                    else:
                        sanitized_traits.append(trait)

                agent_data["personality_traits"] = sanitized_traits

            # Fix communication_style enum value
            if "communication_style" in agent_data and isinstance(agent_data["communication_style"], str):
                agent_data["communication_style"] = agent_data["communication_style"].lower()

            # Fix skill levels in hard_skills
            if "hard_skills" in agent_data and isinstance(agent_data["hard_skills"], list):
                for skill in agent_data["hard_skills"]:
                    if isinstance(skill, dict) and "level" in skill and isinstance(skill["level"], str):
                        skill["level"] = skill["level"].lower()

            # Fix skill levels in soft_skills
            if "soft_skills" in agent_data and isinstance(agent_data["soft_skills"], list):
                for skill in agent_data["soft_skills"]:
                    if isinstance(skill, dict) and "level" in skill and isinstance(skill["level"], str):
                        skill["level"] = skill["level"].lower()

            final_agents_list.append(agent_data)

        data["agents"] = final_agents_list

        # 3. Ensure at least 1 manager if team has more than 1 agent
        if len(data["agents"]) > 1:
            is_manager_present = any("manager" in a.get("role", "").lower() for a in data["agents"])
            if not is_manager_present and data["agents"]: # Ensure list is not empty
                logger.info("No manager in team > 1. Promoting first agent to Project Manager.")
                data["agents"][0]["role"] = "Project Manager"
                data["agents"][0]["seniority"] = AgentSeniority.SENIOR.value # Ensure it's the string value
                data["agents"][0]["description"] = (data["agents"][0].get("description", "") + " Also coordinates the team and project.").strip()

        # 4. Validate handoffs
        raw_handoffs = data.get("handoffs", [])
        data["handoffs"] = self._validate_handoffs_list(raw_handoffs, data["agents"])

        # 5. Ensure other fields exist
        data.setdefault("estimated_cost", {"total_estimated_cost": 0, "currency": "EUR", "breakdown_by_agent": {}})
        data.setdefault("rationale", "Proposal validated and sanitized by DirectorAgent.")
        return data

    def _validate_handoffs_list(self, handoffs_list_raw: List[Any], agents_list_validated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates a list of handoff specifications."""
        agent_name_to_role_map = {a["name"]: a.get("role", "").lower() for a in agents_list_validated if "name" in a}
        valid_agent_names: Set[str] = set(agent_name_to_role_map.keys())
        
        final_valid_handoffs: List[Dict[str, Any]] = []
        if not isinstance(handoffs_list_raw, list):
            logger.warning("Handoffs data is not a list, defaulting to empty.")
            return []

        for h_data in handoffs_list_raw:
            if not isinstance(h_data, dict): continue # Skip non-dict handoff items

            src_agent_name = h_data.get("from")
            raw_target_agent_names = h_data.get("to")

            if not src_agent_name or src_agent_name not in valid_agent_names:
                logger.warning(f"Invalid or missing 'from' agent '{src_agent_name}' in handoff. Skipping.")
                continue

            current_handoff_targets: List[str] = []
            if isinstance(raw_target_agent_names, str): # Single target string
                current_handoff_targets = [raw_target_agent_names]
            elif isinstance(raw_target_agent_names, list): # List of target strings
                current_handoff_targets = [tgt for tgt in raw_target_agent_names if isinstance(tgt, str)]
            
            validated_targets_for_handoff: List[str] = []
            for target_name_candidate in current_handoff_targets:
                if target_name_candidate not in valid_agent_names:
                    logger.warning(f"Target agent '{target_name_candidate}' in handoff from '{src_agent_name}' not found. Skipping this target.")
                    continue
                if target_name_candidate == src_agent_name:
                    logger.warning(f"Self-handoff from '{src_agent_name}' to self prevented.")
                    continue
                
                # Check for manager-to-manager handoff of the same type
                src_role_str = agent_name_to_role_map.get(src_agent_name, "")
                target_role_str = agent_name_to_role_map.get(target_name_candidate, "")
                if self._is_same_role_type(src_role_str, target_role_str) and "manager" in src_role_str:
                    logger.warning(f"Preventing manager-to-manager handoff between similar roles: {src_agent_name} ({src_role_str}) -> {target_name_candidate} ({target_role_str}).")
                    continue
                validated_targets_for_handoff.append(target_name_candidate)
            
            if validated_targets_for_handoff:
                final_valid_handoffs.append({
                    "from": src_agent_name,
                    "to": validated_targets_for_handoff, # Will be List[str]
                    "description": h_data.get("description", f"Handoff from {src_agent_name} to {', '.join(validated_targets_for_handoff)}")
                })
        return final_valid_handoffs

    def _create_fallback_dict(self, config: DirectorConfig) -> Dict[str, Any]:
        """Creates a fallback proposal dictionary for internal use."""
        logger.info("Creating fallback proposal dictionary.")
        # Pass budget_constraint (which can be None or Dict) to _create_default_agents
        default_agents_list = self._create_default_agents(config.budget_constraint)
        
        total_est_cost = sum(agent.get("estimated_monthly_cost", COST_PER_MONTH[AgentSeniority.JUNIOR.value]) for agent in default_agents_list)
        breakdown = {
            agent.get("name", f"DefaultAgent{i}"): agent.get("estimated_monthly_cost", COST_PER_MONTH[AgentSeniority.JUNIOR.value])
            for i, agent in enumerate(default_agents_list)
        }
        return {
            "agents": default_agents_list, "handoffs": [],
            "estimated_cost": {"total_estimated_cost": total_est_cost, "currency": "EUR", "breakdown_by_agent": breakdown},
            "rationale": "Fallback minimal team due to an issue in proposal generation. Please review."
        }

    def _create_default_agents(self, budget_constraint_data: Optional[Union[Dict[str, Any], float]] = None) -> List[Dict[str, Any]]:
        """Creates a default list of agent specifications."""
        logger.debug("Creating default agents set for fallback.")
        current_budget = 1000.0 # Default budget if parsing fails or not provided
        if isinstance(budget_constraint_data, dict):
            current_budget = float(budget_constraint_data.get("max_amount", 1000.0))
        elif isinstance(budget_constraint_data, (int, float)):
            current_budget = float(budget_constraint_data)

        # estimated_monthly_cost is for internal fallback logic, not the primary estimate_costs tool
        default_pm_spec = {
            "name": "ProjectManager", "role": "Project Manager", "seniority": AgentSeniority.SENIOR.value,
            "description": "Fallback: Manages project execution, coordinates team, ensures efficient completion.",
            "system_prompt": self._create_specialist_prompt("Project Manager", ["project planning", "team coordination"]),
            "llm_config": {"model": self._get_model_for_seniority(AgentSeniority.SENIOR.value), "temperature": 0.3},
            "tools": self._get_tools_for_role("Project Manager", AgentSeniority.SENIOR.value),
            "estimated_monthly_cost": COST_PER_MONTH[AgentSeniority.SENIOR.value]
        }
        agents_list_default: List[Dict[str, Any]] = [default_pm_spec]

        if current_budget > 1500 or len(agents_list_default) < self.min_team_size:
            default_specialist_spec = {
                "name": "TaskExecutorSpecialist", "role": "Task Executor Specialist", "seniority": AgentSeniority.JUNIOR.value,
                "description": "Fallback: Handles specific project tasks and provides general support.",
                "system_prompt": self._create_specialist_prompt("Task Executor Specialist", ["task execution", "problem solving"]),
                "llm_config": {"model": self._get_model_for_seniority(AgentSeniority.JUNIOR.value), "temperature": 0.35},
                "tools": self._get_tools_for_role("Task Executor Specialist", AgentSeniority.JUNIOR.value),
                "estimated_monthly_cost": COST_PER_MONTH[AgentSeniority.JUNIOR.value]
            }
            agents_list_default.append(default_specialist_spec)
        return agents_list_default

    def _create_minimal_fallback_proposal(self, config: DirectorConfig, error_reason: str) -> DirectorTeamProposal:
        """Creates a Pydantic DirectorTeamProposal object for critical fallback."""
        logger.info(f"Creating minimal fallback DirectorTeamProposal due to: {error_reason}")
        fallback_data_dict = self._create_fallback_dict(config) # Gets a dict with default agent(s)
        
        # Convert agent dicts to AgentCreate objects
        minimal_agents_list: List[AgentCreate] = []
        for agent_s in fallback_data_dict.get("agents", []):
            agent_s["workspace_id"] = config.workspace_id # UUID
            # Ensure seniority is Enum for AgentCreate
            s_val_str = agent_s.get("seniority", AgentSeniority.JUNIOR.value)
            if isinstance(s_val_str, Enum): s_val_str = s_val_str.value # if already enum, get value
            try:
                agent_s["seniority"] = AgentSeniority(s_val_str.lower())
            except: agent_s["seniority"] = AgentSeniority.JUNIOR
            
            try: minimal_agents_list.append(AgentCreate(**agent_s))
            except Exception as e_ac_fb: logger.error(f"Error creating AgentCreate in minimal fallback: {e_ac_fb}")

        if not minimal_agents_list: # Ensure at least one agent always
            panic_agent_spec = self._create_default_agents()[0] # Get the PM spec
            panic_agent_spec["workspace_id"] = config.workspace_id
            panic_agent_spec["seniority"] = AgentSeniority(panic_agent_spec["seniority"])
            minimal_agents_list.append(AgentCreate(**panic_agent_spec))
            logger.warning("Panic: Created an ultra-minimal agent as last resort in fallback proposal.")


        return DirectorTeamProposal(
            workspace_id=config.workspace_id, # UUID
            agents=minimal_agents_list,
            handoffs=[], # No handoffs in minimal fallback
            estimated_cost=fallback_data_dict.get("estimated_cost", {"total_estimated_cost": 0}), # type: ignore
            rationale=f"Minimal fallback proposal automatically generated due to a critical error: {error_reason}. Please review team and project scope.",
        )

    # Helper methods for instance use (e.g., in _create_default_agents, _create_minimal_fallback_proposal)
    # These are kept as instance methods for potential future use of 'self' if needed.
    def _get_model_for_seniority(self, seniority_value_str: str) -> str:
        """Get appropriate LLM model based on agent seniority string value."""
        return MODEL_BY_SENIORITY.get(seniority_value_str.lower(), MODEL_BY_SENIORITY[AgentSeniority.JUNIOR.value])

    def _get_tools_for_role(self, role_str: str, seniority_value_str: str) -> List[Dict[str, str]]:
        """Get appropriate tools based on agent role and seniority string values."""
        tools_output: List[Dict[str, str]] = []
        role_l = role_str.lower()
        seniority_l = seniority_value_str.lower()

        if seniority_l in [AgentSeniority.SENIOR.value, AgentSeniority.EXPERT.value] or "manager" in role_l:
            tools_output.append({"type": "web_search", "name": "web_search", "description": "Enables searching the web for current information."})
        
        if any(keyword in role_l for keyword in ['content', 'writing', 'research', 'analysis', 'marketing', 'manager']):
            tools_output.append({"type": "file_search", "name": "file_search", "description": "Enables searching through provided documents and knowledge base."})
        return tools_output

    def _create_specialist_prompt(self, role_str: str, skills_list: List[str]) -> str:
        """Create a standardized system prompt for specialist agents."""
        skills_str_display = ', '.join(skills_list) if skills_list else "assigned tasks according to your role"
        return f"""You are a {role_str}. Your expertise covers: {skills_str_display}.
KEY PRINCIPLES:
1. Execute tasks within your defined area of expertise with precision and high quality.
2. Provide concrete, actionable results and complete deliverables directly.
3. Do NOT delegate tasks back to the Project Manager that fall within your expertise. Escalate to the Project Manager ONLY for critical roadblocks, tasks clearly outside your scope (after attempting to clarify), or for significant project-level decisions.
4. Focus on task completion and quality, minimizing unnecessary coordination overhead.
5. Collaborate directly with other specialists when interdependent tasks arise, keeping the Project Manager informed of significant progress and critical interactions that may impact the project timeline or scope."""