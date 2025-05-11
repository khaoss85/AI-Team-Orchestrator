import logging
import os
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import json
import re # Importa il modulo re per la pulizia del JSON

# Importazione dal pacchetto installato
from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool

# Import assoluti dalla root del backend
from models import (
    DirectorConfig,
    DirectorTeamProposal,
    AgentCreate,
    AgentSeniority,
    HandoffCreate
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
        logger.info("DirectorAgent initialized. Note: OPENAI_API_KEY is used by the Runner/Agent, not directly by static tools.")

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

            analysis_data = {
                "required_skills": ["python_programming", "data_analysis", "technical_writing", "api_integration"],
                "expertise_areas": ["SaaS_development", "AI_agent_orchestration", "database_management"],
                "recommended_team_size": 4,
                "rationale": "Project requires backend development, AI logic, data handling, and documentation. Team size of 4 allows for specialized roles."
            }
            validated_output = ProjectAnalysisOutput(**analysis_data)
            logger.info(f"Returning placeholder (but structured) analysis: {validated_output.model_dump()}")
            return json.dumps(validated_output.model_dump())
        except Exception as e:
            logger.error(f"Error in analyze_project_requirements_llm: {e}")
            error_data = {
                "error": str(e),
                "required_skills": [],
                "expertise_areas": [],
                "recommended_team_size": 0,
                "rationale": "Failed to analyze project requirements."
            }
            return json.dumps(error_data)

    async def create_team_proposal(self, config: DirectorConfig) -> DirectorTeamProposal:
        logger.info(f"Director Agent: Creating team proposal for workspace {config.workspace_id}")

        director_agent_instructions = f"""
You are an expert project director AI specializing in planning and assembling teams of AI agents for complex SaaS projects.
Your primary goal is to analyze the given project requirements, design an optimal team of AI agents, define their roles, seniority, system prompts, and necessary handoffs, while adhering to budget constraints.

Project Goal: {config.goal}
Budget Constraints: {json.dumps(config.budget_constraint)}
User ID (for context, if needed): {config.user_id}
Workspace ID (for context): {config.workspace_id}

Your tasks are:
1.  **Analyze Project Requirements**: Understand the project goal and constraints. Identify the core skills and expertise areas needed.
    (You can use the 'analyze_project_requirements_llm' tool if you need to delegate parts of this or if the tool provides a structured way to perform this sub-task).
2.  **Design Team Structure**: Based on the analysis, define the composition of the AI agent team. For each proposed agent, specify:
    * `name`: A descriptive name for the agent.
    * `role`: A clear role.
    * `seniority`: Choose from 'junior', 'senior', 'expert'.
    * `description`: A brief description of the agent's responsibilities.
    * `system_prompt`: A concise and effective system prompt.
    * `llm_config` (optional): Suggest model and temperature.
    * `tools` (optional): Suggest a list of tools.
3.  **Define Handoffs**: Identify critical handoffs. For each, specify:
    * `source_agent_name`: Name of the source agent.
    * `target_agent_name`: Name of the target agent.
    * `description`: Handoff description.
4.  **Estimate Costs**: Provide cost estimation. Explain budget adherence.
    (You can use the 'estimate_costs' tool).
5.  **Provide Rationale**: Briefly explain the overall strategy.

**Output Format Strictness**:
Your *entire response* MUST be *only* a single, valid JSON object.
This JSON object must conform to the structure of a `DirectorTeamProposal`.
The `agents` list within the JSON must contain objects matching the `AgentCreate` structure.
The `handoffs` list must contain objects matching the `HandoffCreate` structure (use placeholder valid UUIDs like "00000000-0000-0000-0000-000000000001" if actual IDs are not yet known for agents you are proposing).
The `estimated_cost` must be a dictionary with "total" and "breakdown".

Do NOT include any introductory text, explanatory sentences, Markdown formatting (like ### or ```json), or any characters whatsoever before the opening curly brace of the JSON object. Your response must begin with the literal character '{{' and end with the literal character '}}'.

Example of an AgentCreate structure to embed in your JSON (ensure correct escaping if directly in f-string, or build separately):
{{
    "workspace_id": "{config.workspace_id}",
    "name": "Example Agent",
    "role": "Example Role",
    "seniority": "senior",
    "description": "This agent does X, Y, Z.",
    "system_prompt": "You are an AI agent that...",
    "llm_config": {{"model": "gpt-4", "temperature": 0.5}},
    "tools": ["tool_name_1"]
}}

Example of a HandoffCreate structure to embed in your JSON:
{{
    "source_agent_id": "00000000-0000-0000-0000-000000000001",
    "target_agent_id": "00000000-0000-0000-0000-000000000002",
    "description": "Handoff of X from Source to Target for Y reason."
}}

Produce the JSON output now.
"""
        # Nota: Per le parti "Example of an AgentCreate/HandoffCreate" nel prompt:
        # Le doppie parentesi graffe { { e } } sono per far sì che l'f-string produca parentesi graffe letterali { e }.
        # La parte "{config.workspace_id}" è un'espressione f-string che verrà interpolata.
        # La parte {{"model": "gpt-4", "temperature": 0.5}} dovrebbe diventare {"model": "gpt-4", "temperature": 0.5}
        # È cruciale che questa formattazione sia corretta per evitare SyntaxError.

        available_tools_for_director_llm = [
            DirectorAgent.analyze_project_requirements_llm,
            DirectorAgent.estimate_costs,
            DirectorAgent.design_team_structure
        ]

        director_llm_agent = OpenAIAgent(
            name="AICrewTeamDirectorLLM",
            instructions=director_agent_instructions,
            model="gpt-4-turbo",
            model_settings=ModelSettings(temperature=0.3),
            tools=available_tools_for_director_llm
        )
        try:
            initial_prompt_to_llm = (
                "Generate the AI agent team proposal as a single, valid JSON object, adhering strictly to the format specified in your instructions."
            )
            run_result = await Runner.run(
                director_llm_agent,
                initial_prompt_to_llm
            )
            final_output_json_str = run_result.final_output
            logger.info(f"Director LLM Agent Raw Output String (length {len(final_output_json_str)}): '{final_output_json_str[:500]}...'")


            # Tentativo di pulizia più robusto
            json_to_parse = final_output_json_str
            match_markdown_block = re.search(r"```json\s*([\s\S]*?)\s*```", final_output_json_str, re.DOTALL)
            if match_markdown_block:
                json_to_parse = match_markdown_block.group(1).strip()
                logger.info(f"Extracted JSON from markdown block: '{json_to_parse[:500]}...'")
            else:
                # Se non è in un blocco ```json, cerca il primo '{' e l'ultimo '}'
                first_brace = final_output_json_str.find('{')
                last_brace = final_output_json_str.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_to_parse = final_output_json_str[first_brace : last_brace+1]
                    logger.info(f"Extracted JSON by finding first and last braces: '{json_to_parse[:500]}...'")
                else:
                    logger.warning("Could not identify a clear JSON structure in LLM output. Attempting to parse as is.")
            
            proposal_data = json.loads(json_to_parse)
            logger.info(f"Successfully parsed JSON from LLM output.")

            proposed_agents_data = proposal_data.get("agents", [])
            agents_create_list: List[AgentCreate] = []
            for agent_spec_data in proposed_agents_data:
                agent_spec_data["workspace_id"] = config.workspace_id
                agents_create_list.append(AgentCreate(**agent_spec_data))

            proposed_handoffs_data = proposal_data.get("handoffs", [])
            handoffs_create_list: List[HandoffCreate] = []
            for handoff_spec_data in proposed_handoffs_data:
                try:
                    source_id_str = handoff_spec_data.get("source_agent_id", "00000000-0000-0000-0000-000000000000")
                    target_id_str = handoff_spec_data.get("target_agent_id", "00000000-0000-0000-0000-000000000000")
                    handoffs_create_list.append(HandoffCreate(
                        source_agent_id=UUID(source_id_str),
                        target_agent_id=UUID(target_id_str),
                        description=handoff_spec_data.get("description")
                    ))
                except ValueError as ve:
                    logger.warning(f"Could not parse UUID for handoff, using placeholder or skipping: {ve} - Data: {handoff_spec_data}")

            final_proposal = DirectorTeamProposal(
                workspace_id=config.workspace_id,
                agents=agents_create_list,
                handoffs=handoffs_create_list,
                estimated_cost=proposal_data.get("estimated_cost", {"total": 0, "breakdown": {}}),
                rationale=proposal_data.get("rationale", "No rationale provided by LLM.")
            )
            logger.info(f"Successfully created team proposal for workspace {config.workspace_id}")
            return final_proposal
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from LLM output: {e}. LLM Output was: '{final_output_json_str}'")
            raise ValueError(f"LLM output was not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error creating team proposal via LLM Director: {e}")
            raise

    @staticmethod
    @function_tool
    async def estimate_costs(team_composition_json: str, duration_days: int) -> str:
        logger.info(f"Director Tool: Estimating costs for duration {duration_days} days.")
        try:
            team_composition = json.loads(team_composition_json)
            total_cost = 0
            cost_breakdown = {}
            rates_per_day = {
                AgentSeniority.JUNIOR.value: 50,
                AgentSeniority.SENIOR.value: 100,
                AgentSeniority.EXPERT.value: 180
            }
            for agent_spec in team_composition:
                role = agent_spec.get("role", "Unknown Role")
                seniority_str = agent_spec.get("seniority", AgentSeniority.JUNIOR.value)
                rate = rates_per_day.get(seniority_str, rates_per_day[AgentSeniority.JUNIOR.value])
                agent_cost = rate * duration_days
                total_cost += agent_cost
                cost_breakdown[f"{role} ({seniority_str})"] = agent_cost
            
            result = {
                "total_estimated_cost": total_cost,
                "currency": "EUR",
                "breakdown_by_agent": cost_breakdown,
                "estimated_duration_days": duration_days,
                "notes": "Costs are estimates based on predefined daily rates per seniority."
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error in estimate_costs: {e}")
            error_result = { "error": str(e), "total_estimated_cost": 0, "currency": "EUR", "breakdown_by_agent": {}, "estimated_duration_days": duration_days }
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
            
            max_agents_resolved = max_agents if max_agents is not None else 5
            
            logger.info(f"Director Tool: Designing team structure. Skills: {required_skills}, Budget: {budget_total}, Max Agents: {max_agents_resolved}")

            team_specification: List[Dict[str, Any]] = []
            if "project_management" in required_skills or "coordination" in expertise_areas:
                team_specification.append({
                    "name": "ProjectCoordinatorAgent", "role": "Project Coordination & Management", "seniority": AgentSeniority.SENIOR.value,
                    "description": "Oversees the project, coordinates agent activities, manages timelines, and ensures goal alignment.",
                    "system_prompt": "You are an AI Project Coordinator. Your goal is to ensure the efficient execution of the project by managing tasks, coordinating between specialist AI agents, tracking progress, and reporting status. You proactively identify bottlenecks and facilitate communication."
                })
                required_skills = [s for s in required_skills if s != "project_management"]

            avg_cost_per_agent_seniority = { AgentSeniority.JUNIOR.value: 500, AgentSeniority.SENIOR.value: 1000, AgentSeniority.EXPERT.value: 1800 }
            current_budget_allocated = sum(avg_cost_per_agent_seniority.get(spec["seniority"], avg_cost_per_agent_seniority[AgentSeniority.JUNIOR.value]) for spec in team_specification)

            for skill in required_skills:
                if len(team_specification) >= max_agents_resolved:
                    logger.warning(f"Reached max_agents ({max_agents_resolved}) before covering all skills.")
                    break
                remaining_budget = budget_total - current_budget_allocated
                chosen_seniority_value = AgentSeniority.JUNIOR.value
                if remaining_budget > avg_cost_per_agent_seniority[AgentSeniority.EXPERT.value]:
                    if skill in ["ai_modeling", "cybersecurity", "complex_data_analysis"]: chosen_seniority_value = AgentSeniority.EXPERT.value
                    elif remaining_budget > avg_cost_per_agent_seniority[AgentSeniority.SENIOR.value] * 1.5: chosen_seniority_value = AgentSeniority.SENIOR.value
                elif remaining_budget > avg_cost_per_agent_seniority[AgentSeniority.SENIOR.value]: chosen_seniority_value = AgentSeniority.SENIOR.value
                
                if avg_cost_per_agent_seniority[chosen_seniority_value] > remaining_budget and team_specification:
                    logger.warning(f"Not enough budget for an agent for skill '{skill}' with chosen seniority {chosen_seniority_value}.")
                    continue

                agent_name = f"{skill.replace('_', ' ').title().replace(' ', '')}SpecialistAgent"
                agent_role = f"{skill.replace('_', ' ').title()} Specialization"
                agent_description = f"Handles all tasks related to {skill.replace('_', ' ')}, utilizing specialized knowledge and tools."
                agent_system_prompt = f"You are an AI specialist in {skill.replace('_', ' ')}. Your tasks involve detailed work in this area. Collaborate with other agents as needed and report your progress to the Project Coordinator." # Simplified
                
                team_specification.append({
                    "name": agent_name, "role": agent_role, "seniority": chosen_seniority_value,
                    "description": agent_description, "system_prompt": agent_system_prompt
                })
                current_budget_allocated += avg_cost_per_agent_seniority[chosen_seniority_value]
            
            if not team_specification and required_skills:
                logger.warning("Could not form any team based on budget/constraints.")
                return json.dumps([{"error": "Could not design a team within the given constraints."}])
            
            logger.info(f"Designed team structure with {len(team_specification)} agents.")
            return json.dumps(team_specification)
            
        except Exception as e:
            logger.error(f"Error in design_team_structure: {e}")
            error_result = [{"error": str(e), "message": "Failed to design team structure"}]
            return json.dumps(error_result)