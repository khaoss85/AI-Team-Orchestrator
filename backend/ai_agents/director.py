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
            else: # Assume it's already a dict or can be stringified
                constraints_dict = {"raw_constraints": str(constraints)}


            budget = 0
            if 'max_amount' in constraints_dict: # Check top level first
                budget = constraints_dict['max_amount']
            elif 'budget' in constraints_dict and isinstance(constraints_dict['budget'], dict): # Then nested
                budget = constraints_dict['budget'].get('max_amount', 0)
            elif 'budget_constraint' in constraints_dict and isinstance(constraints_dict['budget_constraint'], dict): # From DirectorConfig
                budget = constraints_dict['budget_constraint'].get('max_amount', 0)


            analyzer_agent = OpenAIAgent(
                name="ProjectAnalyzerAgent",
                instructions=f"""
                You are a specialized agent that analyzes project requirements to determine the skills and expertise needed.
                
                Project Goal: {goal}
                Constraints: {json.dumps(constraints_dict)}
                Budget: {budget} EUR
                
                Your task is to determine:
                1. The required skills (be specific and relevant to the project domain)
                2. Key expertise areas needed
                3. Recommended team size (consider complexity, budget, and skills needed). Aim for a practical number, usually between 2 and 6 agents unless the project is extremely simple or complex.
                4. A brief rationale for your recommendations
                
                IMPORTANT FOR TEAM SIZE:
                - Simple projects with limited skills needed: 1-2 agents
                - Medium complexity projects: 2-4 agents  
                - Complex projects with many diverse skills: 3-6 agents
                - Very complex enterprise projects: 4-8 agents
                - Consider budget constraints (higher budget allows for more specialists or more senior specialists).
                - Each agent should have a clear, non-overlapping responsibility.
                - Avoid recommending a team size of 1 unless absolutely necessary for extremely simple tasks.
                
                Think about what skills and expertise would ACTUALLY be needed for this specific project.
                Provide a specific number for recommended_team_size.
                
                Return your analysis in the following JSON format:
                {{
                  "required_skills": ["skill1", "skill2", "skill3"],
                  "expertise_areas": ["area1", "area2", "area3"],
                  "recommended_team_size": X,
                  "rationale": "Brief explanation for these recommendations including team size justification"
                }}
                """,
                model="gpt-4.1", 
                model_settings=ModelSettings(temperature=0.3)
            )
            
            run_result = await Runner.run(analyzer_agent, "Analyze the project requirements and provide specific skills and expertise needed for this particular project. Consider the project complexity and budget when recommending team size.")
            
            analysis_output_str = run_result.final_output
            analysis_output = {}
            try:
                analysis_output = json.loads(analysis_output_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON directly from LLM output. Output: {analysis_output_str}. Attempting to extract.")
                json_match = re.search(r'({[\s\S]*})', analysis_output_str) 
                if json_match:
                    analysis_output = json.loads(json_match.group(1))
                else:
                    logger.error("Could not extract JSON from LLM output for project analysis. Using fallback.")
                    num_skills_estimated = len(goal.split()) // 3 + 1
                    budget_factor = 1 if budget < 1000 else 1.5 if budget < 5000 else 2
                    dynamic_team_size = min(max(2, int(num_skills_estimated * budget_factor)), 6)
                    
                    analysis_output = {
                        "required_skills": ["domain_expertise", "research", "content_creation", "analytical_thinking"],
                        "expertise_areas": ["subject_matter_expertise", "user_experience", "data_analysis"],
                        "recommended_team_size": dynamic_team_size,
                        "rationale": f"Based on project complexity and budget of {budget} EUR, recommending a team of {dynamic_team_size} specialists (fallback logic)."
                    }
            
            team_size = analysis_output.get("recommended_team_size", 3) 
            if not isinstance(team_size, int) or team_size < 1:
                logger.warning(f"Invalid recommended_team_size '{team_size}', defaulting to 2.")
                team_size = 2 
            elif team_size > 8:
                logger.warning(f"Recommended_team_size {team_size} is too high, capping at 8.")
                team_size = 8
            
            analysis_output["recommended_team_size"] = team_size
            
            logger.info(f"Project analysis for goal '{goal}': {analysis_output}")
            return json.dumps(analysis_output)
            
        except Exception as e:
            logger.error(f"Error in analyze_project_requirements_llm: {e}", exc_info=True)
            budget_val = 1000 
            try:
                constraints_dict_fb = json.loads(constraints) if isinstance(constraints, str) else constraints if isinstance(constraints, dict) else {}
                budget_val = constraints_dict_fb.get('budget_constraint', {}).get('max_amount', 1000) if 'budget_constraint' in constraints_dict_fb else constraints_dict_fb.get('budget', {}).get('max_amount', 1000)

            except:
                pass 

            num_words = len(goal.split())
            if num_words < 5: base_size = 1
            elif num_words < 10: base_size = 2
            elif num_words < 20: base_size = 3
            else: base_size = 4
            
            team_size_fb = min(max(2, base_size + (1 if budget_val > 2000 else 0)), 6)
            
            analysis_data = {
                "required_skills": ["domain_expertise", "research", "content_creation"],
                "expertise_areas": ["subject_matter_expertise", "user_experience"],
                "recommended_team_size": team_size_fb,
                "rationale": f"Fallback: Estimated team of {team_size_fb} agents based on project complexity and budget of {budget_val} EUR."
            }
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
2.  **Design Team Structure**: Based on the analysis, define the composition of the AI agent team. 
    - Use the recommended team size from the analysis as a PRIMARY guide. You can adjust slightly (+/-1 agent) based on your expert judgment of skills and budget, but clearly justify any deviation in your rationale.
    - Team size can range from 1 to 8 agents.
    - Each agent should have a clear, non-overlapping role.
    For each proposed agent, specify:
    * `name`: A descriptive name for the agent (e.g., "FitnessExpertAgent", "ResearchAgent").
    * `role`: A clear role (e.g., "Fitness Expertise", "Research & Analysis", "Content Creation").
    * `seniority`: Choose from 'junior', 'senior', 'expert'. Justify your choice based on task complexity and budget.
    * `description`: A brief description of the agent's responsibilities.
    * `system_prompt`: A concise and effective system prompt that will guide the agent's behavior and tasks.
    * `llm_config` (optional): Suggest a base model (e.g., "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano") and temperature if relevant.
    * `tools` (IMPORTANT): If specifying tools, they MUST be dictionaries, not strings. Use this format:
      [{"name": "web_search", "type": "function", "description": "Search the web for information"}]
3.  **Define Handoffs**: Identify critical points where tasks or information must be passed between agents.
    For each handoff, specify:
    * `from`: The name of the source agent (string).
    * `to`: The name of the target agent (string) OR a list of target agent names (List[str]).
    * `description`: A brief description of what is being handed off.
4.  **Estimate Costs**: Provide a rough cost estimation using the 'estimate_costs' tool, passing the designed team and a reasonable duration (e.g., 30 days).
5.  **Provide Rationale**: Explain your team strategy, including why you chose this specific team size and structure, and how it aligns with the project goal, skills, and budget.

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
                "1. Call 'analyze_project_requirements_llm' first. "
                "2. Then call 'design_team_structure' using the analysis results (especially recommended_team_size as max_agents). "
                "3. Then call 'estimate_costs' with the designed team. "
                "4. Finally, formulate the complete JSON proposal. "
                "YOUR RESPONSE MUST BE A VALID JSON OBJECT ONLY, with NO markdown, explanations, or other text. "
                "The JSON must contain the keys 'agents', 'handoffs', 'estimated_cost', and 'rationale'."
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
                    json_match_braces = re.search(r'({[\s\S]*})', final_output_json_str, re.DOTALL) # Make regex DOTALL
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

            proposed_agents_data = proposal_data.get("agents", [])
            agents_create_list: List[AgentCreate] = []
            for agent_spec_data in proposed_agents_data:
                agent_spec_data["workspace_id"] = config.workspace_id
                
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
                
                agents_create_list.append(AgentCreate(**agent_spec_data))

            proposed_handoffs_data = proposal_data.get("handoffs", [])
            handoffs_proposal_list: List[HandoffProposalCreate] = []
            for handoff_spec_data in proposed_handoffs_data:
                source_name = handoff_spec_data.get("from") 
                target_names = handoff_spec_data.get("to")
                
                if source_name and target_names:
                    # Pass data directly to HandoffProposalCreate, Pydantic will use aliases
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
            
            if not isinstance(max_agents, int) or max_agents < 1:
                effective_max_agents = max(1, min(len(required_skills), 5))
                logger.info(f"Max_agents was invalid ({max_agents}), defaulting to {effective_max_agents} based on skills.")
            else:
                effective_max_agents = max_agents
            
            logger.info(f"Director Tool: Designing team structure. Skills: {required_skills}, Budget: {budget_total}, Max Agents for design: {effective_max_agents}")

            team_specification: List[Dict[str, Any]] = []
            
            # Add Project Coordinator if team size is substantial and it's not a core skill
            # Consider it part of the effective_max_agents if added
            if effective_max_agents >= 3 and \
               "project_management" not in required_skills and \
               "project coordination" not in required_skills and \
               "coordination" not in required_skills:
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
                    logger.warning("Wanted to add ProjectCoordinatorAgent, but max_agents limit reached.")


            avg_cost_per_agent_seniority = {
                AgentSeniority.JUNIOR.value: 30 * 5,
                AgentSeniority.SENIOR.value: 30 * 10,
                AgentSeniority.EXPERT.value: 30 * 18,
            }
            current_budget_allocated = sum(avg_cost_per_agent_seniority.get(spec["seniority"], 0) for spec in team_specification)
            
            skills_to_assign = [skill for skill in required_skills if skill not in ["project_management", "coordination"]]


            for skill in skills_to_assign:
                if len(team_specification) >= effective_max_agents:
                    logger.warning(f"Reached max_agents ({effective_max_agents}) before covering skill: {skill}.")
                    break 
                
                remaining_budget = budget_total - current_budget_allocated
                
                chosen_seniority = AgentSeniority.JUNIOR.value
                if remaining_budget >= avg_cost_per_agent_seniority[AgentSeniority.EXPERT.value] and skill in expertise_areas:
                    chosen_seniority = AgentSeniority.EXPERT.value
                elif remaining_budget >= avg_cost_per_agent_seniority[AgentSeniority.SENIOR.value]:
                    chosen_seniority = AgentSeniority.SENIOR.value
                
                cost_of_chosen_agent = avg_cost_per_agent_seniority[chosen_seniority]

                if cost_of_chosen_agent > remaining_budget:
                    if chosen_seniority == AgentSeniority.EXPERT.value and remaining_budget >= avg_cost_per_agent_seniority[AgentSeniority.SENIOR.value]:
                        chosen_seniority = AgentSeniority.SENIOR.value
                        cost_of_chosen_agent = avg_cost_per_agent_seniority[chosen_seniority]
                    elif chosen_seniority != AgentSeniority.JUNIOR.value and remaining_budget >= avg_cost_per_agent_seniority[AgentSeniority.JUNIOR.value]:
                         chosen_seniority = AgentSeniority.JUNIOR.value
                         cost_of_chosen_agent = avg_cost_per_agent_seniority[chosen_seniority]
                    else:
                        logger.warning(f"Not enough budget for skill '{skill}' even with junior. Skipping this skill.")
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
                    "seniority": chosen_seniority,
                    "description": agent_description,
                    "system_prompt": agent_system_prompt,
                    "llm_config": {"model": llm_model, "temperature": 0.3},
                    "tools": [] 
                })
                current_budget_allocated += cost_of_chosen_agent
            
            if not team_specification and required_skills:
                logger.warning("Could not form any team based on budget/constraints.")
                return json.dumps([{"error": "Could not design a team within the given constraints (budget or agent limit)."}])
            
            logger.info(f"Designed team structure with {len(team_specification)} agents.")
            return json.dumps(team_specification)
            
        except Exception as e:
            logger.error(f"Error in design_team_structure: {e}", exc_info=True)
            error_result = [{"error": str(e), "message": "Failed to design team structure"}]
            return json.dumps(error_result)