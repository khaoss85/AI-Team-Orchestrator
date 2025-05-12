import logging
import os
import re
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import json

from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool

from models import (
    DirectorConfig,
    DirectorTeamProposal,
    AgentCreate,
    AgentSeniority,
    HandoffProposalCreate 
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ProjectAnalysisOutput(BaseModel):
    required_skills: List[str] = Field(..., description="List of specific skills required for the project.")
    expertise_areas: List[str] = Field(..., description="Key areas of expertise needed.")
    recommended_team_size: int = Field(..., description="Recommended number of agents for the team.")
    rationale: str = Field(..., description="Brief explanation for the recommendations.")

class DirectorAgent:
    """Director Agent that plans and manages the team of AI agents"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.info("OPENAI_API_KEY environment variable is not set (DirectorAgent __init__), but tools are static.")

    @staticmethod
    @function_tool
    async def analyze_project_requirements_llm(goal: str, constraints: str) -> str:
        logger.info(f"Director Tool: Analyzing project requirements for goal: {goal}")
        try:
            constraints_dict = {}
            if isinstance(constraints, str):
                try:
                    constraints_dict = json.loads(constraints)
                except json.JSONDecodeError:
                    constraints_dict = {"raw_constraints": constraints}
            else: 
                constraints_dict = {"raw_constraints": str(constraints)}

            budget = 0
            if 'max_amount' in constraints_dict:
                budget = constraints_dict['max_amount']
            elif 'budget' in constraints_dict and isinstance(constraints_dict['budget'], dict):
                budget = constraints_dict['budget'].get('max_amount', 0)
            elif 'budget_constraint' in constraints_dict and isinstance(constraints_dict['budget_constraint'], dict): 
                budget = constraints_dict['budget_constraint'].get('max_amount', 0)
            
            analyzer_agent_instructions = f"""
            You are a highly experienced project analyst AI. Your task is to meticulously analyze project requirements to determine the necessary skills, expertise areas, and an optimal team size.

            Project Goal: "{goal}"
            Constraints (including budget if specified): {json.dumps(constraints_dict)}
            Budget (EUR, if available): {budget if budget > 0 else 'Not specified or 0'}

            Carefully consider the following when determining the 'recommended_team_size':
            1.  **Number and Diversity of Skills**: Identify all distinct skills truly essential for the project's success. A higher number of diverse skills often requires more specialized agents.
            2.  **Project Complexity**: Gauge the overall complexity. Is it a straightforward task, or does it involve multiple interconnected parts, significant research, or creative generation?
            3.  **Budget Impact**:
                * Low Budget (e.g., < 1500 EUR): Likely supports 1-2 agents, focusing on the most critical skills.
                * Medium Budget (e.g., 1500-5000 EUR): Can support 2-4 agents, allowing for more specialization.
                * High Budget (e.g., > 5000 EUR): Can support 3-6+ agents, enabling a comprehensive team with diverse seniorities.
            4.  **Agent Roles**: Each agent should have a clear, distinct primary responsibility. Avoid excessive overlap. A typical project might involve roles like coordination/management, research, content creation, technical execution, analysis, etc., depending on the goal.
            5.  **Efficiency vs. Coverage**: Balance the need for comprehensive skill coverage with team efficiency. Too many agents can increase coordination overhead.
            6.  **Realistic Team Sizes**:
                * Very Simple Tasks (1-2 core skills, low budget): 1-2 agents.
                * Standard Projects (3-5 core skills, medium budget): 2-4 agents is typical.
                * Complex Projects (5+ core skills, high budget, significant depth needed): 3-6 agents. Only recommend 7-8 for very large, multifaceted enterprise-level initiatives with substantial budgets.
                * **Critically evaluate if the project truly needs more than 3-4 agents.** Justify clearly if recommending more.

            Your output MUST be a single, valid JSON object with the following structure:
            {{
              "required_skills": ["Specific Skill 1", "Specific Skill 2", ...],
              "expertise_areas": ["Broader Expertise Area 1", "Broader Expertise Area 2", ...],
              "recommended_team_size": X,  // An integer representing the number of agents
              "rationale": "A detailed explanation for your skill, expertise, and team size recommendations, explicitly justifying the team size based on the factors above, especially how the chosen number of agents will cover the identified skills within the given budget."
            }}

            Example for a complex task: If 'required_skills' has 6 items and budget is high, 'recommended_team_size' could be 4 or 5. If 'required_skills' has 3 items and budget is low, 'recommended_team_size' is likely 2 or 3.
            Do not simply default to 3 agents if more or fewer are justifiable.
            """

            analyzer_agent = OpenAIAgent(
                name="ProjectRequirementsAnalyzerAgent",
                instructions=analyzer_agent_instructions,
                model="gpt-4.1", 
                model_settings=ModelSettings(temperature=0.25) 
            )
            
            run_result = await Runner.run(analyzer_agent, 
                                          "Analyze the provided project goal and constraints, then output the required skills, expertise areas, recommended team size, and rationale as a single JSON object.")
            
            analysis_output_str = run_result.final_output
            analysis_output = {}
            try:
                analysis_output = json.loads(analysis_output_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON directly from LLM output for project analysis. Output: {analysis_output_str}. Attempting to extract.")
                json_match = re.search(r'({[\s\S]*})', analysis_output_str, re.DOTALL) 
                if json_match:
                    try:
                        analysis_output = json.loads(json_match.group(1))
                    except json.JSONDecodeError as e_json_extract:
                        logger.error(f"Failed to parse extracted JSON: {e_json_extract}. Extracted: {json_match.group(1)}")
                        raise ValueError("Failed to parse or extract JSON from LLM.") from e_json_extract
                else:
                    logger.error("Could not extract JSON from LLM output for project analysis. Using fallback.")
                    raise ValueError("No JSON found in LLM output.")

            team_size = analysis_output.get("recommended_team_size")
            if not isinstance(team_size, int) or team_size < 1:
                logger.warning(f"Invalid or missing recommended_team_size ('{team_size}') from LLM, defaulting to 2 or based on skills.")
                skills_count = len(analysis_output.get("required_skills", []))
                team_size = max(1, min(skills_count, 3)) 
            elif team_size > 8: 
                logger.warning(f"Recommended_team_size {team_size} is too high, capping at 8.")
                team_size = 8
            
            analysis_output["recommended_team_size"] = team_size
            analysis_output.setdefault("required_skills", [])
            analysis_output.setdefault("expertise_areas", [])
            analysis_output.setdefault("rationale", "Rationale not explicitly provided by LLM or parsing error occurred.")

            logger.info(f"Project analysis for goal '{goal}': {analysis_output}")
            return json.dumps(analysis_output)
            
        except Exception as e:
            logger.error(f"Error in analyze_project_requirements_llm: {e}", exc_info=True)
            budget_val = 0
            try:
                constraints_dict_fb = json.loads(constraints) if isinstance(constraints, str) else constraints if isinstance(constraints, dict) else {}
                if 'max_amount' in constraints_dict_fb: budget_val = constraints_dict_fb['max_amount']
                elif 'budget' in constraints_dict_fb and isinstance(constraints_dict_fb['budget'], dict): budget_val = constraints_dict_fb['budget'].get('max_amount', 0)
                elif 'budget_constraint' in constraints_dict_fb and isinstance(constraints_dict_fb['budget_constraint'], dict): budget_val = constraints_dict_fb['budget_constraint'].get('max_amount', 0)
            except:
                budget_val = 1000 

            num_words = len(goal.split())
            if num_words < 5: base_size = 1
            elif num_words < 10: base_size = 2
            elif num_words < 20: base_size = 3
            else: base_size = 4
            
            team_size_fb = min(max(2, base_size + (1 if budget_val > 2000 else 0)), 5) 
            
            analysis_data = {
                "required_skills": ["domain_expertise", "research", "content_creation"],
                "expertise_areas": ["subject_matter_expertise", "user_experience"],
                "recommended_team_size": team_size_fb,
                "rationale": f"Fallback logic applied due to analysis error. Estimated team of {team_size_fb} agents based on project goal length and budget of {budget_val} EUR."
            }
            logger.warning(f"Using fallback project analysis: {analysis_data}")
            return json.dumps(analysis_data)

    async def create_team_proposal(self, config: DirectorConfig) -> DirectorTeamProposal:
        logger.info(f"Director Agent: Creating team proposal for workspace {config.workspace_id}")

        director_agent_instructions = f"""
You are an expert project director AI specializing in planning and assembling teams of AI agents for complex projects.
Your primary goal is to analyze the given project requirements, design an optimal team of AI agents, define their roles, seniority, system prompts, and necessary handoffs, while adhering to budget constraints.
Project Goal: {config.goal}
Budget Constraints: {json.dumps(config.budget_constraint)}
User ID (for context, if needed): {config.user_id}
Workspace ID (for context): {config.workspace_id}
"""

        if hasattr(config, 'user_feedback') and config.user_feedback:
            director_agent_instructions += f"""
USER FEEDBACK (Please consider this carefully when designing the team):
{config.user_feedback}
"""

        director_agent_instructions += """
Your tasks are:
1.  **Analyze Project Requirements**: Understand the project goal and constraints. Identify the core skills and expertise areas needed.
    You MUST use the 'analyze_project_requirements_llm' tool to get a structured analysis including recommended team size.
2.  **Design Team Structure**: Based on the analysis from step 1 (especially the 'required_skills' and 'recommended_team_size'), define the composition of the AI agent team by calling the 'design_team_structure' tool. Pass the 'recommended_team_size' as the 'max_agents' parameter to this tool.
    The 'design_team_structure' tool will return a list of agent specifications.
3.  **Define Handoffs**: Based on the designed team structure from step 2, identify critical points where tasks or information must be passed between agents.
    For each handoff, specify:
    * `from`: The name of the source agent (string, must match a name from the designed team).
    * `to`: The name of the target agent (string, must match a name from the designed team) OR a list of target agent names (List[str]).
    * `description`: A brief description of what is being handed off.
4.  **Estimate Costs**: Provide a rough cost estimation using the 'estimate_costs' tool, passing the team composition from step 2 and a reasonable duration (e.g., 30 days).
5.  **Provide Rationale**: Explain your overall team strategy, including why the final team structure (number of agents, roles, seniorities) is optimal, considering the project goal, identified skills, budget, and the output from the 'design_team_structure' tool.

REMEMBER: Your final output MUST be a SINGLE VALID JSON OBJECT ONLY, not a Markdown document containing JSON. Do not include any explanatory text or markdown formatting - return ONLY pure JSON.
The JSON structure MUST be:
{
  "agents": [
    {
      "name": "AgentName1", "role": "Role1", "seniority": "senior", "description": "...", "system_prompt": "...", 
      "llm_config": {"model": "gpt-4.1-mini", "temperature": 0.3}, "tools": []
    }
  ],
  "handoffs": [
    {"from": "AgentName1", "to": "AgentName2", "description": "..."},
    {"from": "AgentName2", "to": ["AgentName3", "AgentName1"], "description": "..."}
  ],
  "estimated_cost": {"total_estimated_cost": 123, "currency": "EUR", ...},
  "rationale": "..."
}
DO NOT include any explanations, markdown, or other text outside this JSON structure.
"""

        available_tools_for_director_llm = [
            DirectorAgent.analyze_project_requirements_llm,
            DirectorAgent.estimate_costs,
            DirectorAgent.design_team_structure
        ]

        director_llm_agent = OpenAIAgent(
            name="AICrewTeamDirectorLLM",
            instructions=director_agent_instructions,
            model="gpt-4.1", 
            model_settings=ModelSettings(temperature=0.2),
            tools=available_tools_for_director_llm
        )
        
        final_output_json_str = ""
        try:
            initial_prompt_to_llm = (
                "Generate the AI agent team proposal for the project detailed in your instructions. "
                "Follow these steps precisely: "
                "1. Call 'analyze_project_requirements_llm' to get skills and recommended team size. "
                "2. Call 'design_team_structure' using the 'required_skills' JSON string from step 1, and pass the 'recommended_team_size' from step 1 as the 'max_agents' parameter. "
                "3. Call 'estimate_costs' using the agent list JSON string returned by 'design_team_structure'. "
                "4. Formulate the handoffs based on the agent list from 'design_team_structure'. "
                "5. Finally, construct the complete JSON proposal including 'agents' (from design_team_structure), 'handoffs', 'estimated_cost', and your 'rationale'. "
                "YOUR RESPONSE MUST BE A VALID JSON OBJECT ONLY, with NO markdown, explanations, or other text."
            )
            run_result = await Runner.run(
                director_llm_agent,
                initial_prompt_to_llm
            )
            final_output_json_str = run_result.final_output
            logger.info(f"Director LLM Agent Raw Output: {final_output_json_str}")
            
            parsed_json = None
            try:
                parsed_json = json.loads(final_output_json_str)
            except json.JSONDecodeError:
                logger.warning("LLM output is not valid JSON. Attempting to extract from markdown or text.")
                json_match_md = re.search(r'```json\s*({[\s\S]*?})\s*```', final_output_json_str, re.DOTALL)
                if json_match_md:
                    final_output_json_str = json_match_md.group(1).strip()
                else:
                    json_match_braces = re.search(r'({[\s\S]*})', final_output_json_str, re.DOTALL)
                    if json_match_braces:
                        final_output_json_str = json_match_braces.group(1).strip()
                
                try:
                    parsed_json = json.loads(final_output_json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Still failed to parse JSON after extraction attempts: {e}. LLM Output: {run_result.final_output}")
                    raise ValueError(f"LLM output was not valid JSON after extraction: {e}")

            if not parsed_json:
                 raise ValueError("Parsed JSON is empty after processing LLM output.")

            proposal_data = parsed_json

            # Ensure 'agents' key from LLM output is used, not re-created from an older list.
            # The LLM is instructed to use the output of design_team_structure for the 'agents' list.
            proposed_agents_data = proposal_data.get("agents", [])
            agents_create_list: List[AgentCreate] = []
            for agent_spec_data in proposed_agents_data:
                agent_spec_data["workspace_id"] = str(config.workspace_id) # Ensure it's a string for Pydantic
                
                if "tools" in agent_spec_data and isinstance(agent_spec_data["tools"], list):
                    converted_tools = []
                    for tool_item in agent_spec_data["tools"]:
                        if isinstance(tool_item, str):
                            converted_tools.append({
                                "name": tool_item, "type": "function", 
                                "description": f"Custom tool: {tool_item}"
                            })
                        elif isinstance(tool_item, dict) and "name" in tool_item:
                             converted_tools.append(tool_item)
                        else:
                            logger.warning(f"Skipping invalid tool format: {tool_item}")
                    agent_spec_data["tools"] = converted_tools
                
                # Convert seniority string to AgentSeniority enum
                if 'seniority' in agent_spec_data and isinstance(agent_spec_data['seniority'], str):
                    try:
                        agent_spec_data['seniority'] = AgentSeniority(agent_spec_data['seniority'].lower())
                    except ValueError:
                        logger.warning(f"Invalid seniority value '{agent_spec_data['seniority']}', defaulting to JUNIOR.")
                        agent_spec_data['seniority'] = AgentSeniority.JUNIOR

                agents_create_list.append(AgentCreate(**agent_spec_data))

            proposed_handoffs_data = proposal_data.get("handoffs", [])
            handoffs_proposal_list: List[HandoffProposalCreate] = []
            for handoff_spec_data in proposed_handoffs_data:
                source_name = handoff_spec_data.get("from") 
                target_names = handoff_spec_data.get("to")
                
                if source_name and target_names:
                    handoffs_proposal_list.append(HandoffProposalCreate(**handoff_spec_data))
                else:
                    logger.warning(f"Skipping handoff due to missing 'from' or 'to' field: {handoff_spec_data}")

            proposal_data_extra = {}
            if hasattr(config, 'user_feedback') and config.user_feedback:
                proposal_data_extra["user_feedback"] = config.user_feedback

            final_proposal = DirectorTeamProposal(
                workspace_id=config.workspace_id,
                agents=agents_create_list,
                handoffs=handoffs_proposal_list,
                estimated_cost=proposal_data.get("estimated_cost", {"total_estimated_cost": 0, "currency": "EUR", "breakdown_by_agent": {}}),
                rationale=proposal_data.get("rationale", "No rationale provided by LLM."),
                **proposal_data_extra
            )
            logger.info(f"Successfully created team proposal for workspace {config.workspace_id} with {len(agents_create_list)} agents")
            return final_proposal
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from LLM output: {e}\nLLM Output was: {final_output_json_str}")
            raise ValueError(f"LLM output was not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error creating team proposal via LLM Director: {e}", exc_info=True)
            return DirectorTeamProposal(
                workspace_id=config.workspace_id,
                agents=[],
                handoffs=[],
                estimated_cost={"total_estimated_cost": 0, "currency": "EUR", "breakdown_by_agent": {}, "notes": "Error during estimation."},
                rationale="Failed to generate team proposal due to an internal error. Please review logs."
            )

    @staticmethod
    @function_tool
    async def estimate_costs(team_composition_json: str, duration_days: Optional[int]) -> str:
        if duration_days is None:
            duration_days = 30
            
        logger.info(f"Director Tool: Estimating costs for duration {duration_days} days.")
        try:
            team_composition = json.loads(team_composition_json)
            total_cost = 0
            cost_breakdown = {}
            rates_per_day = {
                AgentSeniority.JUNIOR.value: 5,
                AgentSeniority.SENIOR.value: 10,
                AgentSeniority.EXPERT.value: 18
            }
            
            for agent_spec in team_composition:
                role = agent_spec.get("role", "Unknown Role")
                seniority_str = agent_spec.get("seniority", AgentSeniority.JUNIOR.value)
                # Handle case where seniority_str might be an enum member if not properly stringified before json.loads
                if isinstance(seniority_str, Enum):
                    seniority_str = seniority_str.value

                rate = rates_per_day.get(seniority_str, rates_per_day[AgentSeniority.JUNIOR.value])
                agent_cost = rate * duration_days
                total_cost += agent_cost
                cost_breakdown[f"{role} ({seniority_str})"] = agent_cost
            
            logger.info(f"Estimated costs: Total={total_cost}, Breakdown={cost_breakdown}")
            result = {
                "total_estimated_cost": total_cost,
                "currency": "EUR",
                "breakdown_by_agent": cost_breakdown,
                "estimated_duration_days": duration_days,
                "notes": "Costs are estimates based on predefined daily rates per seniority. GPT-4.1 models offer better cost-efficiency than previous versions."
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error in estimate_costs: {e}", exc_info=True)
            error_result = {
                "error": str(e),
                "total_estimated_cost": 0,
                "currency": "EUR",
                "breakdown_by_agent": {},
                "estimated_duration_days": duration_days,
                "notes": "Error during cost estimation."
            }
            return json.dumps(error_result)

    @staticmethod
    @function_tool
    async def design_team_structure(
        required_skills_json: str,
        expertise_areas_json: str,
        budget_total: float,
        max_agents: Optional[int] 
    ) -> str:
        try:
            required_skills = json.loads(required_skills_json)
            expertise_areas = json.loads(expertise_areas_json)
            
            # === INIZIO LOGICA AGGIORNATA PER effective_max_agents ===
            initial_recommended_max_agents = max_agents # Il valore passato, che è 'recommended_team_size'

            if not isinstance(initial_recommended_max_agents, int) or initial_recommended_max_agents < 1:
                # Se max_agents non è valido, calcola un default basato sulle skill
                effective_max_agents = max(1, min(len(required_skills), 4)) 
                logger.info(f"Max_agents (recommended_team_size) was invalid ({initial_recommended_max_agents}), defaulting to {effective_max_agents} based on skills count.")
            else:
                effective_max_agents = initial_recommended_max_agents
            
            logger.info(f"Initial Max Agents for design (from recommendation): {effective_max_agents}")

            num_required_skills = len(required_skills)
            # Stima un costo medio per agente (es. per un senior) per valutare il budget
            avg_cost_per_senior_agent_month = 30 * 10 # 300 EUR

            # Se ci sono più skill del max_agents raccomandato E c'è budget teorico per più agenti
            if num_required_skills > effective_max_agents:
                # Quanti agenti in più servirebbero per coprire le skill?
                needed_additional_agents = num_required_skills - effective_max_agents
                
                # Budget stimato rimanente se usassimo il numero corrente di agenti (tutti senior per semplicità di stima)
                estimated_current_team_cost = effective_max_agents * avg_cost_per_senior_agent_month
                remaining_budget_if_current_max = budget_total - estimated_current_team_cost

                # Quanti agenti *senior* aggiuntivi ci si potrebbe permettere?
                affordable_additional_senior_agents = 0
                if avg_cost_per_senior_agent_month > 0:
                    affordable_additional_senior_agents = int(remaining_budget_if_current_max / avg_cost_per_senior_agent_month)

                # Aumenta effective_max_agents se è logico e possibile, ma con moderazione
                # Prendi il minimo tra gli agenti aggiuntivi necessari e quelli che ci si può permettere
                increase_by = min(needed_additional_agents, affordable_additional_senior_agents)
                
                # Limita l'aumento (es. non più di 2 agenti aggiuntivi rispetto alla raccomandazione, o un cap assoluto)
                increase_by = min(increase_by, 2) 
                
                if increase_by > 0:
                    new_max_agents = min(effective_max_agents + increase_by, 8) # Cap assoluto di 8
                    if new_max_agents > effective_max_agents:
                        logger.info(f"Adjusting Max Agents for design from {effective_max_agents} to {new_max_agents} due to {num_required_skills} skills and available budget of {budget_total}.")
                        effective_max_agents = new_max_agents
            # === FINE LOGICA AGGIORNATA PER effective_max_agents ===
            
            logger.info(f"Director Tool: Designing team structure. Skills: {required_skills}, Budget: {budget_total}, Effective Max Agents for design: {effective_max_agents}")

            team_specification: List[Dict[str, Any]] = []
            
            # Logica per il Project Coordinator (come prima)
            # ... (assicurati che usi effective_max_agents) ...
            if effective_max_agents >= 3 and \
               "project_management" not in [s.lower() for s in required_skills] and \
               "project coordination" not in [s.lower() for s in required_skills] and \
               "coordination" not in [s.lower() for s in required_skills]:
                if len(team_specification) < effective_max_agents:
                    team_specification.append({
                        "name": "ProjectCoordinatorAgent",
                        "role": "Project Coordination & Management",
                        "seniority": AgentSeniority.SENIOR.value,
                        "description": "Oversees the project, coordinates agent activities, manages timelines, and ensures goal alignment.",
                        "system_prompt": "You are an AI Project Coordinator. Your goal is to ensure the efficient execution of the project by managing tasks, coordinating between specialist AI agents, tracking progress, and reporting status. You proactively identify bottlenecks and facilitate communication.",
                        "llm_config": {"model": "gpt-4.1-mini", "temperature": 0.3},
                        "tools": []
                    })
                else:
                    logger.warning("Wanted to add ProjectCoordinatorAgent, but effective_max_agents limit reached.")


            avg_cost_per_agent_seniority_map = {
                AgentSeniority.JUNIOR.value: 30 * 5,
                AgentSeniority.SENIOR.value: 30 * 10,
                AgentSeniority.EXPERT.value: 30 * 18,
            }
            current_budget_allocated = sum(avg_cost_per_agent_seniority_map.get(spec["seniority"], 0) for spec in team_specification)
            
            # Escludi le skill di coordinamento se il ProjectCoordinatorAgent è già stato aggiunto
            skills_to_assign = [
                skill for skill in required_skills 
                if skill.lower() not in ["project_management", "project coordination", "coordination"] or \
                   not any(agent['name'] == "ProjectCoordinatorAgent" for agent in team_specification)
            ]


            for skill in skills_to_assign:
                if len(team_specification) >= effective_max_agents:
                    logger.warning(f"Reached effective_max_agents ({effective_max_agents}) before covering skill: {skill}.")
                    break 
                
                remaining_budget = budget_total - current_budget_allocated
                
                chosen_seniority = AgentSeniority.JUNIOR.value # Default
                # Logica di scelta seniority (come prima, ma usa avg_cost_per_agent_seniority_map)
                if remaining_budget >= avg_cost_per_agent_seniority_map[AgentSeniority.EXPERT.value] and skill in expertise_areas:
                    chosen_seniority = AgentSeniority.EXPERT.value
                elif remaining_budget >= avg_cost_per_agent_seniority_map[AgentSeniority.SENIOR.value]:
                    chosen_seniority = AgentSeniority.SENIOR.value
                
                cost_of_chosen_agent = avg_cost_per_agent_seniority_map[chosen_seniority]

                if cost_of_chosen_agent > remaining_budget:
                    if chosen_seniority == AgentSeniority.EXPERT.value and remaining_budget >= avg_cost_per_agent_seniority_map[AgentSeniority.SENIOR.value]:
                        chosen_seniority = AgentSeniority.SENIOR.value
                        cost_of_chosen_agent = avg_cost_per_agent_seniority_map[chosen_seniority]
                    elif chosen_seniority != AgentSeniority.JUNIOR.value and remaining_budget >= avg_cost_per_agent_seniority_map[AgentSeniority.JUNIOR.value]:
                         chosen_seniority = AgentSeniority.JUNIOR.value
                         cost_of_chosen_agent = avg_cost_per_agent_seniority_map[chosen_seniority]
                    else:
                        logger.warning(f"Not enough budget for skill '{skill}' even with junior (cost: {cost_of_chosen_agent}, remaining: {remaining_budget}). Skipping this skill.")
                        continue 

                agent_name_base = skill.replace('_', ' ').title().replace(' ', '')
                agent_name = f"{agent_name_base}SpecialistAgent"
                name_suffix = 1
                while any(a['name'] == agent_name for a in team_specification):
                    agent_name = f"{agent_name_base}{name_suffix}SpecialistAgent"
                    name_suffix += 1

                agent_role = f"{skill.replace('_', ' ').title()} Specialization"
                agent_description = f"Handles all tasks related to {skill.replace('_', ' ')}, utilizing specialized knowledge and tools."
                agent_system_prompt = f"You are an AI specialist in {skill.replace('_', ' ')}. Your tasks involve detailed work in this area. Collaborate with other agents as needed and report your progress to the Project Coordinator if present."
                
                llm_model = "gpt-4.1-nano" 
                if chosen_seniority == AgentSeniority.EXPERT.value: llm_model = "gpt-4.1"
                elif chosen_seniority == AgentSeniority.SENIOR.value: llm_model = "gpt-4.1-mini"
                
                team_specification.append({
                    "name": agent_name,
                    "role": agent_role,
                    "seniority": chosen_seniority, # Già stringa .value
                    "description": agent_description,
                    "system_prompt": agent_system_prompt,
                    "llm_config": {"model": llm_model, "temperature": 0.3},
                    "tools": [] 
                })
                current_budget_allocated += cost_of_chosen_agent
            
            if not team_specification and required_skills:
                logger.warning("Could not form any team based on budget/constraints.")
                return json.dumps([{"error": "Could not design a team within the given constraints (budget or agent limit)."}])
            
            logger.info(f"Designed team structure with {len(team_specification)} agents using effective_max_agents: {effective_max_agents}.")
            return json.dumps(team_specification)
            
        except Exception as e:
            logger.error(f"Error in design_team_structure: {e}", exc_info=True)
            error_result = [{"error": str(e), "message": "Failed to design team structure"}]
            return json.dumps(error_result)