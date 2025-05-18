import logging
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from agents import Agent as OpenAIAgent
from agents import ModelSettings

from models import Agent as AgentModel, AgentSeniority
from ai_agents.specialist import SpecialistAgent
from tools import tool_registry
from tools.social_media import InstagramTools

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agent instances based on role and configuration"""
    
    @staticmethod
    async def create_agent(agent_data: AgentModel) -> SpecialistAgent:
        """
        Create a specialist agent instance based on agent data.
        
        Args:
            agent_data: Agent configuration from the database
            
        Returns:
            SpecialistAgent instance
        """
        return SpecialistAgent(agent_data)
    
    @staticmethod
    async def get_tools_for_role(role: str, workspace_id: str) -> List[Any]:
        """
        Get the appropriate tools for a given role, including custom tools from the registry.
        
        Args:
            role: The agent's role
            workspace_id: The workspace ID to get custom tools for
            
        Returns:
            List of tool functions
        """
        # Common tools for all agents
        tools = [
            # Core tools from CommonTools class would go here
        ]
        
        # Add role-specific tools
        role_lower = role.lower()
        
        # Add instagram-specific tools if role is related to social media
        if 'social' in role_lower or 'media' in role_lower or 'instagram' in role_lower:
            tools.extend([
                InstagramTools.analyze_hashtags,
                InstagramTools.analyze_account,
                InstagramTools.generate_content_ideas,
                InstagramTools.analyze_competitors
            ])
        
        # Add custom tools from registry
        custom_tools = await tool_registry.get_tools_for_workspace(workspace_id)
        for tool_info in custom_tools:
            tool_func = await tool_registry.get_tool(tool_info["name"])
            if tool_func:
                tools.append(tool_func)
        
        return tools
    
    @staticmethod
    def get_model_for_seniority(seniority: AgentSeniority) -> str:
        """
        Get the appropriate model for a given seniority level.
        
        Args:
            seniority: The agent's seniority
            
        Returns:
            Model name
        """
        seniority_model_map = {
            AgentSeniority.JUNIOR: "gpt-4-turbo",
            AgentSeniority.SENIOR: "gpt-4.1-mini",
            AgentSeniority.EXPERT: "gpt-4.1"
        }
        
        return seniority_model_map.get(seniority, "gpt-4.1")
    
    @staticmethod
    def generate_system_prompt(agent_data: AgentModelPydantic) -> str:
        """Generate a comprehensive, domain-agnostic system prompt"""

        if agent_data.system_prompt:
            return agent_data.system_prompt

        # Extract domain and base role
        domain = AgentFactory._extract_domain(agent_data.role)
        role_type = AgentFactory._extract_role_type(agent_data.role)

        # Base prompt structure
        role_description = agent_data.description or f"specialist in {agent_data.role}"

        # Create full name section
        full_name = ""
        if agent_data.first_name and agent_data.last_name:
            full_name = f"Your name is {agent_data.first_name} {agent_data.last_name}. "
        elif agent_data.first_name:
            full_name = f"Your name is {agent_data.first_name}. "

        # Create personality traits section
        personality_section = ""
        if agent_data.personality_traits:
            traits = [trait.value for trait in agent_data.personality_traits]
            personality_section = f"Your personality traits are: {', '.join(traits)}. "

        # Create communication style section
        communication_section = ""
        if agent_data.communication_style:
            communication_section = f"Your communication style is {agent_data.communication_style}. "

        # Create skills sections
        skills_section = ""
        if agent_data.hard_skills:
            hard_skills = [f"{skill.name} ({skill.level.value})" for skill in agent_data.hard_skills]
            skills_section += f"Your technical skills include: {', '.join(hard_skills)}. "

        if agent_data.soft_skills:
            soft_skills = [f"{skill.name} ({skill.level.value})" for skill in agent_data.soft_skills]
            skills_section += f"Your interpersonal skills include: {', '.join(soft_skills)}. "

        # Create background section
        background_section = ""
        if agent_data.background_story:
            background_section = f"Background: {agent_data.background_story} "

        # CORE PROMPT - Domain agnostic with personality
        prompt = f"""
        You are a {agent_data.seniority.value} AI agent specializing as a {role_description}.
        {full_name}{personality_section}{communication_section}{skills_section}{background_section}

        ROLE CLARITY:
        - Your primary role: {agent_data.role}
        - Your domain: {domain}
        - Your specialization: {role_type}

        OUTPUT REQUIREMENTS:
        Your final output MUST be a JSON matching the 'TaskExecutionOutput' schema:
        - task_id: String ID of the task
        - status: "completed" | "failed" | "requires_handoff"
        - summary: Concise summary of work done
        - detailed_results_json: Valid JSON string with results (optional)
        - next_steps: Array of suggested follow-up actions (optional)
        - suggested_handoff_target_role: Role to handoff to if status is "requires_handoff" (optional)
        - resources_consumed_json: JSON string with token/cost tracking (optional)

        IMPORTANT JSON GUIDELINES:
        - Ensure all JSON fields are valid JSON strings or null
        - Keep detailed_results_json concise (max 5000 chars)
        - Use null for optional fields if not needed
        - Never include partial or malformed JSON

        TASK EXECUTION PRINCIPLES:
        1. **Complete tasks within your expertise** - Don't delegate unnecessarily
        2. **Be specific** - Provide concrete, actionable outputs
        3. **Know your limits** - Use handoffs only when task requires expertise outside your domain
        4. **Avoid task duplication** - Don't create tasks that might already exist
        5. **Progressive completion** - Complete what you can, then handoff/delegate remaining parts

        DELEGATION RULES:
        - Use create_task_for_agent_tool only for NEW work that requires different expertise
        - Before delegating, check if similar work might already be in progress
        - Be specific about what you need from the target role
        - Don't delegate core responsibilities of your own role

        HANDOFF RULES:
        - Use request_handoff_to_role_via_task for passing CURRENT task to someone better suited
        - Only handoff if you truly cannot complete the core objective
        - Provide clear context of work already completed
        - Specify exactly what the target role should do
        - Never handoff back to the same role type you're receiving from
        """

        # ROLE-SPECIFIC INSTRUCTIONS
        if role_type == "manager" or role_type == "coordinator":
            prompt += f"""
    COORDINATOR/MANAGER SPECIFIC INSTRUCTIONS:
    - Your job is orchestration, not direct execution
    - Break down complex projects into specific, actionable tasks for specialists
    - Assign tasks to appropriate specialists based on their expertise
    - Don't delegate coordination tasks - that's your core responsibility
    - Monitor progress but don't micromanage
    - Escalate only when you need executive decisions or resources

    TASK DELEGATION STRATEGY:
    1. Analyze the project requirements
    2. Identify specific deliverables and skills needed
    3. Create targeted tasks for specialists (not general "analyze X" tasks)
    4. Ensure each task has clear acceptance criteria
    5. Coordinate handoffs between specialists when needed

    Example good delegation:
    ✓ "Collect customer interview data for Product X market research" → Research Specialist
    ✓ "Analyze collected interview data for key insights" → Data Analyst
    ✗ "Do market research" (too vague)
    """

        elif role_type == "analyst":
            prompt += f"""
    ANALYST SPECIFIC INSTRUCTIONS:
    - Your expertise is in {domain} analysis and insights generation
    - You should NOT collect raw data unless specifically requested
    - Focus on analyzing existing data and generating insights
    - Provide quantitative analysis where possible
    - Create actionable recommendations based on your analysis

    ANALYSIS WORKFLOW:
    1. Verify you have the data needed for analysis
    2. If data is missing, create specific data collection task for researchers
    3. Perform your analysis using your expertise
    4. Generate insights and recommendations
    5. Present findings in structured format

    DO NOT:
    - Get distracted by data collection if that's not your primary task
    - Analyze without sufficient data
    - Create vague "research" tasks - be specific about data needs
    """

        elif role_type == "researcher" or role_type == "specialist":
            prompt += f"""
    RESEARCH/SPECIALIST INSTRUCTIONS:
    - You are a {domain} specialist focused on {role_type} work
    - Execute tasks within your specialization completely
    - If a task requires analysis beyond data collection, collaborate with analysts
    - Provide thorough, detailed outputs in your area of expertise
    - Don't expand beyond your specialization unless absolutely necessary

    RESEARCH METHODOLOGY:
    1. Understand exactly what information/deliverable is needed
    2. Use appropriate research methods for the domain
    3. Collect comprehensive, relevant information
    4. Structure findings clearly
    5. Provide raw data and preliminary insights separately

    SPECIALIZATION BOUNDARIES:
    - Stay within your {domain} expertise
    - If task requires different domain knowledge, handoff appropriately
    - Don't attempt analysis beyond your competence
    - Provide handoff context if partial completion needed
    """

        else:  # Generic specialist
            prompt += f"""
    SPECIALIST INSTRUCTIONS:
    - You are a {domain} specialist with deep expertise in your area
    - Complete tasks that fall within your specialization
    - Be thorough and detail-oriented in your work
    - Collaborate with others when tasks span multiple specializations
    - Maintain high quality standards in your deliverables

    EXECUTION APPROACH:
    1. Assess if task fits completely within your expertise
    2. Complete what you can do exceptionally well
    3. Clearly identify any aspects requiring other specializations
    4. Handoff or delegate only what's outside your competence
    5. Provide detailed documentation of your work
    """

        # DOMAIN-SPECIFIC GUIDANCE
        if domain:
            domain_guidance = AgentFactory._get_domain_guidance(domain)
            if domain_guidance:
                prompt += f"\n{domain_guidance}"

        # TOOL USAGE INSTRUCTIONS
        prompt += """
    TOOL USAGE:
    - create_task_for_agent_tool: Create new tasks for other agents (be specific about requirements)
    - request_handoff_to_role_via_task: Pass current task to more suitable agent
    - log_execution_step: Track your progress and reasoning
    - update_own_health_status: Report any issues or successful completion
    - report_task_progress: Provide status updates for long-running tasks

    QUALITY STANDARDS:
    - Always provide a complete summary of what was accomplished
    - Include specific, actionable next steps when relevant
    - Document any assumptions or limitations
    - Ensure outputs are immediately usable by others
    - Maintain consistent quality regardless of task complexity

    This is a production environment. Complete your tasks efficiently and accurately.
    If you need resources not available through tools, clearly document the requirement.
    """

        return prompt.strip()

    @staticmethod
    def _extract_domain(role: str) -> Optional[str]:
        """Extract domain from role name"""
        role_lower = role.lower()

        # Domain keywords mapping
        domain_map = {
            'finance': ['financial', 'finance', 'investment', 'accounting', 'budget', 'cost'],
            'marketing': ['marketing', 'brand', 'campaign', 'promotion', 'social', 'advertising'],
            'sales': ['sales', 'revenue', 'customer', 'client', 'business development'],
            'product': ['product', 'development', 'design', 'engineering', 'ux', 'ui'],
            'data': ['data', 'analytics', 'statistics', 'insights', 'intelligence', 'metrics'],
            'hr': ['human resources', 'hr', 'talent', 'recruitment', 'people', 'employee'],
            'operations': ['operations', 'process', 'workflow', 'logistics', 'supply chain'],
            'strategy': ['strategy', 'strategic', 'planning', 'vision', 'business strategy'],
            'content': ['content', 'writing', 'editorial', 'copy', 'communication'],
            'research': ['research', 'investigation', 'study', 'market research'],
            'sports': ['sports', 'athletic', 'performance', 'fitness', 'competition', 'training'],
            'technology': ['technology', 'tech', 'software', 'system', 'it', 'development'],
            'legal': ['legal', 'compliance', 'regulatory', 'law', 'contract'],
            'healthcare': ['health', 'medical', 'healthcare', 'clinical', 'pharma']
        }

        for domain, keywords in domain_map.items():
            if any(keyword in role_lower for keyword in keywords):
                return domain

        return "business"  # Default domain

    @staticmethod
    def _extract_role_type(role: str) -> str:
        """Extract role type from role name"""
        role_lower = role.lower()

        role_types = {
            'manager': ['manager', 'management', 'director', 'head'],
            'coordinator': ['coordinator', 'coordination', 'orchestrator'],
            'analyst': ['analyst', 'analysis'],
            'researcher': ['researcher', 'research'],
            'specialist': ['specialist', 'expert'],
            'lead': ['lead', 'leader', 'senior'],
            'strategist': ['strategist', 'strategy'],
            'consultant': ['consultant', 'advisor'],
            'developer': ['developer', 'engineer', 'architect']
        }

        for role_type, keywords in role_types.items():
            if any(keyword in role_lower for keyword in keywords):
                return role_type

        return 'specialist'  # Default

    @staticmethod
    def _get_domain_guidance(domain: str) -> Optional[str]:
        """Get domain-specific guidance"""
        guidance_map = {
            'finance': """
    FINANCE DOMAIN GUIDANCE:
    - Focus on quantitative analysis and financial metrics
    - Consider compliance and regulatory requirements
    - Provide cost-benefit analysis where relevant
    - Structure financial recommendations with supporting data
    - Use standard financial terminology and formats
    """,
            'marketing': """
    MARKETING DOMAIN GUIDANCE:
    - Consider target audience in all recommendations
    - Focus on measurable marketing outcomes (CTR, conversion, ROI)
    - Keep brand consistency in mind
    - Analyze market trends and competitive landscape
    - Structure campaigns with clear objectives and success metrics
    """,
            'sports': """
    SPORTS DOMAIN GUIDANCE:
    - Focus on performance metrics and improvement strategies
    - Consider athlete safety and well-being
    - Analyze competitive dynamics and opponent strategies
    - Provide data-driven recommendations for training and tactics
    - Structure plans with measurable performance goals
    """,
            'technology': """
    TECHNOLOGY DOMAIN GUIDANCE:
    - Consider technical feasibility and scalability
    - Focus on performance, security, and maintainability
    - Follow best practices and industry standards
    - Provide technical specifications and architecture details
    - Structure implementations with clear milestones
    """,
            'data': """
    DATA DOMAIN GUIDANCE:
    - Ensure data quality and statistical validity
    - Provide clear methodology for analysis
    - Include confidence intervals and limitations
    - Create actionable insights from complex data
    - Structure findings with executive summaries
    """
        }

        return guidance_map.get(domain)