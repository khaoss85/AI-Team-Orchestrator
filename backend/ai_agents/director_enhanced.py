# backend/ai_agents/director_enhanced.py
"""Enhanced DirectorAgent that uses strategic goals and deliverables for team composition"""

import logging
import json
from typing import List, Dict, Any, Optional
from ai_agents.director import DirectorAgent, DirectorConfig, DirectorTeamProposal

logger = logging.getLogger(__name__)

class EnhancedDirectorAgent(DirectorAgent):
    """Enhanced Director that considers strategic goals and deliverables when creating teams"""
    
    async def create_proposal_with_goals(
        self, 
        config: DirectorConfig,
        strategic_goals: Optional[Dict[str, Any]] = None
    ) -> DirectorTeamProposal:
        """
        Create team proposal considering strategic goals and deliverables
        
        Args:
            config: Standard director configuration
            strategic_goals: Dictionary containing:
                - final_metrics: List of final success metrics
                - strategic_deliverables: List of deliverables with autonomy analysis
                - execution_phases: List of project phases
        """
        
        try:
            # If no strategic goals provided, fall back to standard behavior
            if not strategic_goals:
                logger.info("No strategic goals provided, using standard team creation")
                return await self.create_team_proposal(config)
        except Exception as e:
            logger.error(f"Error in enhanced director, falling back to standard: {e}")
            return await self.create_team_proposal(config)
        
        logger.info(f"🎯 Creating team with strategic goals context: {len(strategic_goals.get('strategic_deliverables', []))} deliverables")
        
        # Enhance the goal with strategic context
        enhanced_goal = self._enhance_goal_with_context(config.goal, strategic_goals)
        
        # Analyze skill requirements based on deliverables
        required_skills = self._analyze_required_skills(strategic_goals)
        
        # Determine team composition based on autonomy levels
        team_composition = self._determine_team_composition(strategic_goals, config.budget_constraint)
        
        # Create enhanced config with strategic context
        enhanced_config = DirectorConfig(
            workspace_id=config.workspace_id,
            goal=enhanced_goal,
            budget_constraint=config.budget_constraint,
            user_id=config.user_id,
            user_feedback=config.user_feedback,
            extracted_goals=config.extracted_goals  # Pass through extracted goals
        )
        
        # Add strategic context to the proposal generation
        proposal = await self.create_team_proposal(enhanced_config)
        
        # Enhance proposal with strategic alignment
        enhanced_proposal = self._enhance_proposal_with_deliverables(proposal, strategic_goals)
        
        return enhanced_proposal
    
    def _enhance_goal_with_context(self, original_goal: str, strategic_goals: Dict[str, Any]) -> str:
        """Add strategic context to the goal description"""
        
        deliverables = strategic_goals.get('strategic_deliverables', [])
        metrics = strategic_goals.get('final_metrics', [])
        
        context_parts = [original_goal]
        
        # Add key deliverables
        if deliverables:
            priority_deliverables = [d for d in deliverables if d.get('priority', 5) <= 2]
            if priority_deliverables:
                deliverable_names = [d.get('name', d.get('deliverable_type', 'Unknown')) for d in priority_deliverables[:3]]
                context_parts.append(f"Key deliverables: {', '.join(deliverable_names)}")
        
        # Add success metrics
        if metrics:
            metric_descriptions = []
            for metric in metrics[:2]:  # Top 2 metrics
                value = metric.get('target_value', 0)
                unit = metric.get('unit', '')
                metric_descriptions.append(f"{value} {unit}")
            context_parts.append(f"Success metrics: {', '.join(metric_descriptions)}")
        
        # Add autonomy analysis summary
        autonomy_levels = [d.get('autonomy_level', 'unknown') for d in deliverables]
        autonomous_count = autonomy_levels.count('autonomous')
        assisted_count = autonomy_levels.count('assisted')
        
        if deliverables:
            context_parts.append(
                f"AI autonomy: {autonomous_count} fully autonomous, {assisted_count} assisted deliverables"
            )
        
        return " | ".join(context_parts)
    
    def _analyze_required_skills(self, strategic_goals: Dict[str, Any]) -> List[str]:
        """Extract required skills from deliverables"""
        
        skills = set()
        deliverables = strategic_goals.get('strategic_deliverables', [])
        
        # Map deliverable types to skills
        skill_mapping = {
            'content_calendar': ['Content Planning', 'Social Media Strategy', 'Scheduling'],
            'content_strategy': ['Strategic Planning', 'Audience Analysis', 'Content Marketing'],
            'audience_analysis': ['Data Analysis', 'Market Research', 'User Research'],
            'hashtag_strategy': ['SEO', 'Social Media Analytics', 'Trend Analysis'],
            'engagement_workflow': ['Community Management', 'Process Design', 'Automation'],
            'performance_monitoring': ['Analytics', 'KPI Tracking', 'Reporting'],
            'content_creation_guidelines': ['Content Creation', 'Brand Management', 'Documentation'],
            'brand_guide': ['Brand Strategy', 'Visual Design', 'Copywriting'],
            'competitor_analysis': ['Market Research', 'Competitive Intelligence', 'Analytics'],
            'strategy_document': ['Strategic Planning', 'Business Analysis', 'Documentation'],
            'analytics_setup': ['Technical Implementation', 'Analytics Tools', 'Data Engineering']
        }
        
        for deliverable in deliverables:
            deliverable_type = deliverable.get('deliverable_type', '')
            if deliverable_type in skill_mapping:
                skills.update(skill_mapping[deliverable_type])
            
            # Also check required tools
            tools = deliverable.get('available_tools', [])
            if 'web_search' in tools:
                skills.add('Research')
            if 'data_analysis' in tools:
                skills.add('Data Analysis')
            if 'content_creation' in tools:
                skills.add('Content Creation')
        
        return list(skills)
    
    def _determine_team_composition(self, strategic_goals: Dict[str, Any], budget_constraint: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal team composition based on deliverables and budget"""
        
        deliverables = strategic_goals.get('strategic_deliverables', [])
        budget = budget_constraint.get('max_amount', 1000)
        
        # Count deliverables by autonomy level
        autonomy_counts = {
            'autonomous': 0,
            'assisted': 0,
            'human_required': 0
        }
        
        for d in deliverables:
            level = d.get('autonomy_level', 'assisted')
            if level in autonomy_counts:
                autonomy_counts[level] += 1
        
        # Determine team size and seniority mix
        total_deliverables = len(deliverables)
        
        # More autonomous deliverables = smaller team with higher seniority
        # More human-required deliverables = larger team with mixed seniority
        
        if autonomy_counts['autonomous'] > total_deliverables * 0.6:
            # Highly autonomous project
            return {
                'recommended_size': min(3, self.max_team_size),
                'seniority_mix': {
                    'expert': 1,
                    'senior': 1,
                    'junior': 1
                },
                'focus': 'automation and quality control'
            }
        elif autonomy_counts['human_required'] > total_deliverables * 0.4:
            # Human-intensive project
            return {
                'recommended_size': min(5, self.max_team_size),
                'seniority_mix': {
                    'expert': 1,
                    'senior': 2,
                    'junior': 2
                },
                'focus': 'collaboration and human coordination'
            }
        else:
            # Balanced project
            return {
                'recommended_size': 4,
                'seniority_mix': {
                    'expert': 1,
                    'senior': 2,
                    'junior': 1
                },
                'focus': 'balanced automation and human input'
            }
    
    def _enhance_proposal_with_deliverables(
        self, 
        proposal: DirectorTeamProposal, 
        strategic_goals: Dict[str, Any]
    ) -> DirectorTeamProposal:
        """Add deliverable assignments to the proposal"""
        
        # Update rationale with strategic context
        deliverable_count = len(strategic_goals.get('strategic_deliverables', []))
        autonomy_summary = self._get_autonomy_summary(strategic_goals)
        
        # Create enhanced rationale with strategic information
        strategic_context = []
        
        # Indicate source of goals
        goal_source = strategic_goals.get('source', 'database')
        if goal_source == 'frontend_confirmed':
            strategic_context.append("obiettivi confermati dall'utente")
        
        if deliverable_count > 0:
            strategic_context.append(f"{deliverable_count} deliverable strategici identificati")
        
        if autonomy_summary:
            strategic_context.append(f"autonomia AI: {autonomy_summary}")
        
        # Get deliverable assignments for context
        deliverable_assignments = self._assign_deliverables_to_agents(
            proposal.agents,
            strategic_goals.get('strategic_deliverables', [])
        )
        
        if deliverable_assignments:
            key_assignments = list(deliverable_assignments.keys())[:3]  # Top 3 assignments
            strategic_context.append(f"deliverable assegnati: {', '.join(key_assignments)}")
        
        enhanced_rationale = proposal.rationale
        if strategic_context:
            enhanced_rationale += f" | Strategic Enhancement: {', '.join(strategic_context)}."
        
        proposal.rationale = enhanced_rationale
        
        return proposal
    
    def _assign_deliverables_to_agents(self, agents: List[Any], deliverables: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Assign deliverables to agents based on their roles"""
        
        assignments = {}
        
        # Simple assignment based on agent roles
        for agent in agents:
            agent_role = agent.role.lower()
            assigned_deliverables = []
            
            for deliverable in deliverables:
                deliverable_type = deliverable.get('deliverable_type', '').lower()
                deliverable_name = deliverable.get('name', deliverable_type)
                
                # Match deliverables to agent roles
                if 'content' in agent_role and 'content' in deliverable_type:
                    assigned_deliverables.append(deliverable_name)
                elif 'strateg' in agent_role and 'strategy' in deliverable_type:
                    assigned_deliverables.append(deliverable_name)
                elif 'analy' in agent_role and ('analysis' in deliverable_type or 'monitoring' in deliverable_type):
                    assigned_deliverables.append(deliverable_name)
                elif 'social' in agent_role and ('hashtag' in deliverable_type or 'engagement' in deliverable_type):
                    assigned_deliverables.append(deliverable_name)
                elif 'brand' in agent_role and 'brand' in deliverable_type:
                    assigned_deliverables.append(deliverable_name)
                elif 'project' in agent_role and len(assigned_deliverables) == 0:
                    # Project manager gets oversight of unassigned deliverables
                    assigned_deliverables.append(deliverable_name)
            
            if assigned_deliverables:
                assignments[agent.name] = assigned_deliverables
        
        return assignments
    
    def _get_autonomy_summary(self, strategic_goals: Dict[str, Any]) -> str:
        """Get a summary of autonomy levels"""
        
        deliverables = strategic_goals.get('strategic_deliverables', [])
        if not deliverables:
            return "nessuna analisi di autonomia disponibile"
        
        autonomy_counts = {}
        for d in deliverables:
            level = d.get('autonomy_level', 'unknown')
            autonomy_counts[level] = autonomy_counts.get(level, 0) + 1
        
        parts = []
        if autonomy_counts.get('autonomous', 0) > 0:
            parts.append(f"{autonomy_counts['autonomous']} deliverable completamente autonomi")
        if autonomy_counts.get('assisted', 0) > 0:
            parts.append(f"{autonomy_counts['assisted']} che richiedono assistenza")
        if autonomy_counts.get('human_required', 0) > 0:
            parts.append(f"{autonomy_counts['human_required']} che richiedono intervento umano")
        
        return ", ".join(parts) if parts else "tutti i deliverable gestibili con AI"