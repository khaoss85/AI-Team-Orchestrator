# backend/auto_agent_provisioner.py
"""
🤖 AUTO AGENT PROVISIONER - UNIVERSAL & AI-DRIVEN

Fixes review flow blockage by automatically provisioning basic agents
for workspaces that have goals but no agents.

Adheres to architectural principles:
- AI-driven agent role determination 
- Universal across all business domains
- Agnostic to project types
- Autonomous provisioning
- Scalable and learning
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from database import supabase
from models import GoalStatus

logger = logging.getLogger(__name__)

class AutoAgentProvisioner:
    """
    🤖 UNIVERSAL AUTO AGENT PROVISIONER
    
    Automatically provisions minimal agent teams for workspaces with goals but no agents.
    Prevents review flow deadlocks while maintaining architectural principles.
    """
    
    def __init__(self):
        # 🤖 Initialize AI for universal agent role determination
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ Auto Agent Provisioner initialized with AI")
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for AI agent provisioning")
        else:
            self.ai_available = False
    
    async def provision_agents_for_orphaned_workspaces(self) -> Dict[str, Any]:
        """
        🎯 MAIN ENTRY POINT: Find and fix workspaces with goals but no agents
        """
        try:
            # Find orphaned workspaces (have goals but no agents)
            orphaned_workspaces = await self._find_orphaned_workspaces()
            
            if not orphaned_workspaces:
                logger.info("✅ No orphaned workspaces found")
                return {"fixed_workspaces": 0, "details": []}
            
            logger.warning(f"🚨 Found {len(orphaned_workspaces)} orphaned workspaces - provisioning agents")
            
            # Provision agents for each orphaned workspace
            fixed_workspaces = []
            for workspace_info in orphaned_workspaces:
                workspace_id = workspace_info["workspace_id"]
                goals = workspace_info["goals"]
                workspace_data = workspace_info["workspace_data"]
                
                provisioned_agents = await self._provision_minimal_agent_team(
                    workspace_id, goals, workspace_data
                )
                
                if provisioned_agents:
                    fixed_workspaces.append({
                        "workspace_id": workspace_id,
                        "workspace_name": workspace_data.get("name", "Unknown"),
                        "goals_count": len(goals),
                        "agents_created": len(provisioned_agents),
                        "agent_roles": [agent["role"] for agent in provisioned_agents]
                    })
                    logger.info(f"✅ Fixed workspace {workspace_id}: created {len(provisioned_agents)} agents")
            
            return {
                "fixed_workspaces": len(fixed_workspaces),
                "details": fixed_workspaces
            }
            
        except Exception as e:
            logger.error(f"Error in auto agent provisioning: {e}")
            return {"fixed_workspaces": 0, "error": str(e)}
    
    async def _find_orphaned_workspaces(self) -> List[Dict[str, Any]]:
        """Find workspaces that have goals but no agents"""
        try:
            # Get all workspaces with active goals
            goals_response = supabase.table("workspace_goals").select(
                "workspace_id"
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            workspace_ids_with_goals = set(goal["workspace_id"] for goal in goals_response.data)
            
            if not workspace_ids_with_goals:
                return []
            
            # Check which workspaces have no agents
            orphaned_workspaces = []
            for workspace_id in workspace_ids_with_goals:
                # Check if workspace has agents
                agents_response = supabase.table("agents").select("id").eq(
                    "workspace_id", workspace_id
                ).execute()
                
                if not agents_response.data:  # No agents found
                    # Get workspace details and goals
                    workspace_response = supabase.table("workspaces").select("*").eq(
                        "id", workspace_id
                    ).single().execute()
                    
                    goals_response = supabase.table("workspace_goals").select("*").eq(
                        "workspace_id", workspace_id
                    ).eq("status", GoalStatus.ACTIVE.value).execute()
                    
                    orphaned_workspaces.append({
                        "workspace_id": workspace_id,
                        "workspace_data": workspace_response.data,
                        "goals": goals_response.data or []
                    })
            
            logger.info(f"🔍 Found {len(orphaned_workspaces)} orphaned workspaces out of {len(workspace_ids_with_goals)} with goals")
            return orphaned_workspaces
            
        except Exception as e:
            logger.error(f"Error finding orphaned workspaces: {e}")
            return []
    
    async def _provision_minimal_agent_team(
        self, 
        workspace_id: str, 
        goals: List[Dict], 
        workspace_data: Dict
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN MINIMAL AGENT TEAM PROVISIONING
        
        Creates minimal but sufficient agent team based on goals and workspace context.
        Universal across all business domains.
        """
        try:
            if self.ai_available:
                # Use AI to determine optimal agent roles
                agents_to_create = await self._ai_determine_agent_roles(workspace_data, goals)
            else:
                # Fallback to generic minimal team
                agents_to_create = self._fallback_minimal_team(workspace_data, goals)
            
            # Create agents in database
            created_agents = []
            for agent_spec in agents_to_create:
                agent_data = {
                    "id": str(uuid4()),
                    "workspace_id": workspace_id,
                    "name": agent_spec["name"],
                    "role": agent_spec["role"],
                    "seniority": agent_spec.get("seniority", "senior"),
                    "status": "active",
                    "description": f"Auto-provisioned {agent_spec['role']} - {agent_spec.get('description', 'Basic agent')}",
                    "system_prompt": f"You are a {agent_spec['role']}. {agent_spec.get('description', 'You execute tasks assigned to you.')} Focus on delivering concrete, measurable results that contribute to workspace goals.",
                    "health": {"status": "healthy", "details": {"initialization": "auto_provisioned"}, "last_update": datetime.now().isoformat()},
                    "llm_config": '{"model": "gpt-4o-mini", "temperature": 0.3}',
                    "tools": '[]',  # Basic agents start with no tools
                    "can_create_tools": False,
                    "first_name": agent_spec["name"].split()[0] if " " in agent_spec["name"] else agent_spec["name"],
                    "last_name": agent_spec["name"].split()[-1] if " " in agent_spec["name"] else "Agent",
                    "personality_traits": '["reliable", "focused", "goal-oriented"]',
                    "communication_style": "professional",
                    "hard_skills": f'[{{"name": "General Execution", "level": "intermediate", "description": "Capable of executing various tasks"}}]',
                    "soft_skills": f'[{{"name": "Adaptability", "level": "intermediate", "description": "Can adapt to different task requirements"}}]',
                    "background_story": f"Auto-provisioned agent created to resolve review flow blockage. Specializes in {agent_spec['role'].lower()} tasks."
                }
                
                result = supabase.table("agents").insert(agent_data).execute()
                if result.data:
                    created_agents.append(result.data[0])
                    logger.info(f"✅ Created agent: {agent_spec['name']} ({agent_spec['role']}) for workspace {workspace_id}")
            
            return created_agents
            
        except Exception as e:
            logger.error(f"Error provisioning agents for workspace {workspace_id}: {e}")
            return []
    
    async def _ai_determine_agent_roles(
        self, 
        workspace_data: Dict, 
        goals: List[Dict]
    ) -> List[Dict[str, Any]]:
        """🤖 AI-driven agent role determination based on workspace context and goals"""
        try:
            workspace_name = workspace_data.get("name", "Unknown Project")
            workspace_goal = workspace_data.get("goal", "General business project")
            workspace_description = workspace_data.get("description", "")
            
            # Build goals summary for AI
            goals_summary = []
            for goal in goals:
                goals_summary.append(f"- {goal.get('description', 'Unknown goal')} ({goal.get('metric_type', 'unknown')}): {goal.get('target_value', '?')} {goal.get('unit', 'units')}")
            
            goals_text = "\n".join(goals_summary) if goals_summary else "- No specific goals defined"
            
            prompt = f"""You are an expert project management AI. A workspace needs minimal agent provisioning to unblock its review flow.

WORKSPACE CONTEXT:
- Name: {workspace_name}
- Goal: {workspace_goal}
- Description: {workspace_description}

ACTIVE GOALS:
{goals_text}

TASK: Create a MINIMAL but SUFFICIENT agent team (2-3 agents max) that can:
1. Handle corrective tasks for goal gaps
2. Work across any business domain (universal)
3. Be immediately productive
4. Follow our architectural principles

IMPORTANT CONSTRAINTS:
- Maximum 2-3 agents (minimal team)
- Roles must be universal (work for ANY business domain)
- Include one coordinator/manager role
- Include one specialist/executor role
- Optional: one quality/review role if complex goals
- Avoid domain-specific roles (no "Marketing Manager" etc.)

Generate agent specifications in this JSON format:
{{
    "agents": [
        {{
            "name": "Professional descriptive name",
            "role": "Universal role that works across domains",
            "seniority": "senior|expert|junior",
            "description": "What this agent does and why needed",
            "capabilities": ["capability1", "capability2", "capability3"],
            "primary_responsibility": "Main area of focus"
        }}
    ]
}}

Examples of GOOD universal roles:
✅ "Project Coordinator" (manages tasks and workflows)
✅ "Execution Specialist" (implements solutions)
✅ "Quality Reviewer" (validates outputs)

Examples of BAD domain-specific roles:
❌ "Marketing Manager" (too domain-specific)
❌ "Software Developer" (assumes tech project)
❌ "Sales Representative" (assumes sales project)

Focus on creating agents that can handle the goals and unblock corrective task creation."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at creating universal, minimal agent teams for any business domain."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            agents = result.get("agents", [])
            
            logger.info(f"🤖 AI determined {len(agents)} agents for workspace provisioning")
            return agents
            
        except Exception as e:
            logger.error(f"AI agent role determination failed: {e}")
            return self._fallback_minimal_team(workspace_data, goals)
    
    def _fallback_minimal_team(self, workspace_data: Dict, goals: List[Dict]) -> List[Dict[str, Any]]:
        """Fallback minimal team when AI is not available"""
        workspace_name = workspace_data.get("name", "Project")
        
        return [
            {
                "name": f"{workspace_name} Project Coordinator",
                "role": "Project Coordinator",
                "seniority": "senior",
                "description": "Manages tasks, coordinates work, and handles corrective actions",
                "capabilities": ["task_management", "coordination", "problem_solving", "goal_tracking"],
                "primary_responsibility": "Overall project coordination and corrective task execution"
            },
            {
                "name": f"{workspace_name} Execution Specialist",
                "role": "Execution Specialist", 
                "seniority": "expert",
                "description": "Implements solutions and delivers concrete results",
                "capabilities": ["implementation", "execution", "deliverable_creation", "quality_assurance"],
                "primary_responsibility": "Executing tasks and creating deliverables to meet goals"
            }
        ]

# Singleton instance
auto_agent_provisioner = AutoAgentProvisioner()

# Integration function for goal validation system
async def fix_orphaned_workspaces() -> Dict[str, Any]:
    """
    🎯 INTEGRATION POINT: Called by goal validation when corrective task creation fails
    """
    return await auto_agent_provisioner.provision_agents_for_orphaned_workspaces()