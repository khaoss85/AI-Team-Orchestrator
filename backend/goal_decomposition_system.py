#!/usr/bin/env python3
"""
🎯 Goal Decomposition System

Sistema per spacchettare logicamente ogni goal in:
1. Deliverables concreti per l'utente (asset utilizzabili)
2. Thinking process (strategia e pianificazione)

Garantisce aderenza ai pilastri:
- Domain Agnostic (PILLAR 2)
- User Value Creation (PILLAR 7)  
- Minimal Interface (PILLAR 3)
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from enum import Enum

logger = logging.getLogger(__name__)

class DeliverableType(str, Enum):
    """Types of deliverables a goal can produce"""
    ASSET = "asset"  # Concrete, actionable deliverable for user
    THINKING = "thinking"  # Strategic process, planning, analysis
    HYBRID = "hybrid"  # Both asset and thinking components

class GoalDecomposition:
    """Decompose goals into concrete deliverables and thinking processes"""
    
    def __init__(self):
        self.openai_client = None
        self._init_ai_client()
    
    def _init_ai_client(self):
        """Initialize AI client for goal decomposition"""
        try:
            import openai
            import os
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ Goal Decomposition AI client initialized")
        except Exception as e:
            logger.warning(f"⚠️ AI client not available for goal decomposition: {e}")
    
    async def decompose_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 CORE METHOD: Decompose a goal into deliverables and thinking components
        
        Returns:
            {
                "goal_id": UUID,
                "decomposition": {
                    "asset_deliverables": [...],  # Concrete deliverables for user
                    "thinking_components": [...], # Strategic thinking/planning
                    "completion_criteria": {...}, # How to validate completion
                    "user_value_score": float,    # Expected user value (0-100)
                    "complexity_level": str       # simple/medium/complex
                }
            }
        """
        try:
            goal_id = goal.get("id")
            goal_description = goal.get("description", "")
            goal_metric_type = goal.get("metric_type", "")
            goal_target_value = goal.get("target_value", 0)
            
            logger.info(f"🔍 Decomposing goal: '{goal_description}' (type: {goal_metric_type})")
            
            # Use AI to analyze goal and decompose it
            if self.openai_client:
                decomposition = await self._ai_decompose_goal(goal)
            else:
                decomposition = self._fallback_decompose_goal(goal)
            
            # Validate decomposition quality
            validation_result = self._validate_decomposition(decomposition)
            if not validation_result["valid"]:
                logger.warning(f"⚠️ Goal decomposition validation failed: {validation_result['reason']}")
                decomposition = self._fix_decomposition(decomposition, validation_result)
            
            result = {
                "goal_id": goal_id,
                "original_goal": {
                    "description": goal_description,
                    "metric_type": goal_metric_type,
                    "target_value": goal_target_value
                },
                "decomposition": decomposition,
                "decomposed_at": datetime.now().isoformat(),
                "decomposition_method": "ai" if self.openai_client else "fallback"
            }
            
            logger.info(f"✅ Goal decomposed: {len(decomposition.get('asset_deliverables', []))} assets, {len(decomposition.get('thinking_components', []))} thinking components")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error decomposing goal {goal.get('id')}: {e}")
            return self._emergency_decomposition(goal)
    
    async def _ai_decompose_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """🤖 AI-driven goal decomposition using GPT"""
        try:
            goal_description = goal.get("description", "")
            goal_metric_type = goal.get("metric_type", "")
            goal_target_value = goal.get("target_value", 0)
            
            # 🌍 PILLAR 2: Domain-agnostic decomposition prompt
            decomposition_prompt = f"""Analyze this business goal and decompose it into concrete deliverables and strategic thinking components.

GOAL: "{goal_description}"
TYPE: {goal_metric_type}
TARGET: {goal_target_value}

Decompose into:

1. ASSET DELIVERABLES (concrete, actionable outputs for the user):
   - What specific documents, templates, content, or tools will the user receive?
   - Each must be immediately usable and provide direct business value

2. THINKING COMPONENTS (strategic planning and analysis):
   - What research, analysis, planning, or strategic thinking is needed?
   - What background work supports the asset creation?

3. COMPLETION CRITERIA:
   - How do we validate each deliverable is complete and valuable?
   - What quality standards must be met?

4. USER VALUE ASSESSMENT:
   - Rate expected user value 0-100
   - Identify complexity level: simple/medium/complex

Return as JSON:
{{
  "asset_deliverables": [
    {{
      "name": "Deliverable name",
      "description": "What the user receives",
      "value_proposition": "Why this is valuable",
      "completion_criteria": "How to validate completion",
      "estimated_effort": "low/medium/high",
      "user_impact": "immediate/short-term/long-term"
    }}
  ],
  "thinking_components": [
    {{
      "name": "Thinking component name", 
      "description": "What analysis/planning is needed",
      "supports_deliverables": ["deliverable1", "deliverable2"],
      "complexity": "simple/medium/complex"
    }}
  ],
  "completion_criteria": {{
    "asset_quality_threshold": 85,
    "thinking_depth_required": "medium",
    "user_validation_needed": true/false
  }},
  "user_value_score": 85,
  "complexity_level": "medium",
  "domain_category": "universal/specific",
  "pillar_adherence": {{
    "domain_agnostic": true/false,
    "user_value_focused": true/false,
    "minimal_interface_ready": true/false
  }}
}}"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": decomposition_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                decomposition_data = json.loads(json_match.group())
                logger.info("🤖 AI goal decomposition successful")
                return decomposition_data
            else:
                logger.warning("⚠️ AI response didn't contain valid JSON, using fallback")
                return self._fallback_decompose_goal(goal)
                
        except Exception as e:
            logger.error(f"❌ AI goal decomposition failed: {e}")
            return self._fallback_decompose_goal(goal)
    
    def _fallback_decompose_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """🛡️ Fallback decomposition using pattern recognition"""
        goal_description = goal.get("description", "").lower()
        goal_metric_type = goal.get("metric_type", "").lower()
        goal_target_value = goal.get("target_value", 0)
        
        # Pattern-based decomposition
        asset_deliverables = []
        thinking_components = []
        
        # 📊 Content creation patterns
        if any(keyword in goal_description for keyword in ["content", "post", "article", "blog", "social"]):
            asset_deliverables.extend([
                {
                    "name": "Content Library",
                    "description": f"Collection of {goal_target_value} ready-to-publish content pieces",
                    "value_proposition": "Immediate publishing capability",
                    "completion_criteria": "Each piece ready for distribution",
                    "estimated_effort": "medium",
                    "user_impact": "immediate"
                },
                {
                    "name": "Content Calendar",
                    "description": "Publishing schedule and distribution plan",
                    "value_proposition": "Organized content deployment",
                    "completion_criteria": "Calendar with dates and channels",
                    "estimated_effort": "low",
                    "user_impact": "immediate"
                }
            ])
            thinking_components.extend([
                {
                    "name": "Content Strategy Analysis",
                    "description": "Research target audience and content themes",
                    "supports_deliverables": ["Content Library", "Content Calendar"],
                    "complexity": "medium"
                }
            ])
        
        # 📈 Analysis/research patterns
        elif any(keyword in goal_description for keyword in ["analysis", "research", "study", "report"]):
            asset_deliverables.extend([
                {
                    "name": "Research Report",
                    "description": "Comprehensive analysis document with findings",
                    "value_proposition": "Actionable insights and recommendations",
                    "completion_criteria": "Report with clear recommendations",
                    "estimated_effort": "high",
                    "user_impact": "long-term"
                },
                {
                    "name": "Executive Summary",
                    "description": "Key findings and action items",
                    "value_proposition": "Quick decision-making reference",
                    "completion_criteria": "1-page summary with actions",
                    "estimated_effort": "low",
                    "user_impact": "immediate"
                }
            ])
            thinking_components.extend([
                {
                    "name": "Data Collection Strategy",
                    "description": "Plan for gathering and analyzing information",
                    "supports_deliverables": ["Research Report"],
                    "complexity": "medium"
                }
            ])
        
        # 📋 Planning patterns
        elif any(keyword in goal_description for keyword in ["plan", "strategy", "roadmap", "timeline"]):
            asset_deliverables.extend([
                {
                    "name": "Strategic Plan Document",
                    "description": "Complete planning document with timelines",
                    "value_proposition": "Clear execution roadmap",
                    "completion_criteria": "Plan with milestones and deadlines",
                    "estimated_effort": "high",
                    "user_impact": "long-term"
                }
            ])
            thinking_components.extend([
                {
                    "name": "Strategic Analysis",
                    "description": "Environment and capability assessment",
                    "supports_deliverables": ["Strategic Plan Document"],
                    "complexity": "complex"
                }
            ])
        
        # 🛠️ Setup/implementation patterns
        elif any(keyword in goal_description for keyword in ["setup", "create", "build", "implement"]):
            asset_deliverables.extend([
                {
                    "name": "Implementation Package",
                    "description": "Ready-to-use setup materials and configurations",
                    "value_proposition": "Immediate implementation capability",
                    "completion_criteria": "All components tested and documented",
                    "estimated_effort": "medium",
                    "user_impact": "immediate"
                }
            ])
            thinking_components.extend([
                {
                    "name": "Requirements Analysis",
                    "description": "Technical and business requirements definition",
                    "supports_deliverables": ["Implementation Package"],
                    "complexity": "medium"
                }
            ])
        
        # 🌍 Universal fallback
        else:
            asset_deliverables.append({
                "name": "Goal Completion Package",
                "description": f"Deliverable package for {goal_description}",
                "value_proposition": "Achievement of stated objective",
                "completion_criteria": "Target value reached with documentation",
                "estimated_effort": "medium",
                "user_impact": "short-term"
            })
            thinking_components.append({
                "name": "Goal Planning Process",
                "description": "Strategic planning for goal achievement",
                "supports_deliverables": ["Goal Completion Package"],
                "complexity": "simple"
            })
        
        # Calculate user value score based on deliverable quality
        user_value_score = min(85, 50 + (len(asset_deliverables) * 10) + (goal_target_value if goal_target_value < 20 else 20))
        
        return {
            "asset_deliverables": asset_deliverables,
            "thinking_components": thinking_components,
            "completion_criteria": {
                "asset_quality_threshold": 75,
                "thinking_depth_required": "medium",
                "user_validation_needed": False
            },
            "user_value_score": user_value_score,
            "complexity_level": "medium" if len(asset_deliverables) > 1 else "simple",
            "domain_category": "universal",
            "pillar_adherence": {
                "domain_agnostic": True,
                "user_value_focused": True,
                "minimal_interface_ready": True
            }
        }
    
    def _validate_decomposition(self, decomposition: Dict[str, Any]) -> Dict[str, Any]:
        """🔍 Validate decomposition quality and pillar adherence"""
        issues = []
        
        # Check asset deliverables
        assets = decomposition.get("asset_deliverables", [])
        if not assets:
            issues.append("No asset deliverables defined")
        
        for asset in assets:
            if not asset.get("name") or not asset.get("description"):
                issues.append(f"Asset missing name/description: {asset}")
            if not asset.get("value_proposition"):
                issues.append(f"Asset missing value proposition: {asset.get('name')}")
        
        # Check thinking components
        thinking = decomposition.get("thinking_components", [])
        for component in thinking:
            if not component.get("supports_deliverables"):
                issues.append(f"Thinking component not linked to deliverables: {component.get('name')}")
        
        # Check user value score
        user_value = decomposition.get("user_value_score", 0)
        if user_value < 50:
            issues.append(f"User value score too low: {user_value}")
        
        # Check pillar adherence
        pillar_adherence = decomposition.get("pillar_adherence", {})
        if not pillar_adherence.get("user_value_focused"):
            issues.append("Decomposition not user value focused")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Valid decomposition"
        }
    
    def _fix_decomposition(self, decomposition: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 Fix decomposition issues"""
        issues = validation_result.get("issues", [])
        
        # Add missing asset deliverables
        if "No asset deliverables defined" in str(issues):
            decomposition["asset_deliverables"] = [{
                "name": "Goal Achievement Package",
                "description": "Comprehensive deliverable for goal completion",
                "value_proposition": "Concrete result of goal achievement",
                "completion_criteria": "Goal target reached with documentation",
                "estimated_effort": "medium",
                "user_impact": "immediate"
            }]
        
        # Fix missing value propositions
        for asset in decomposition.get("asset_deliverables", []):
            if not asset.get("value_proposition"):
                asset["value_proposition"] = f"Provides value through {asset.get('name', 'deliverable')}"
        
        # Fix thinking component linkage
        asset_names = [a.get("name", "") for a in decomposition.get("asset_deliverables", [])]
        for component in decomposition.get("thinking_components", []):
            if not component.get("supports_deliverables"):
                component["supports_deliverables"] = asset_names[:1]  # Link to first asset
        
        # Fix user value score
        if decomposition.get("user_value_score", 0) < 50:
            decomposition["user_value_score"] = 65
        
        # Fix pillar adherence
        if not decomposition.get("pillar_adherence"):
            decomposition["pillar_adherence"] = {
                "domain_agnostic": True,
                "user_value_focused": True,
                "minimal_interface_ready": True
            }
        
        logger.info("🔧 Decomposition fixed based on validation results")
        return decomposition
    
    def _emergency_decomposition(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """🚨 Emergency fallback decomposition"""
        return {
            "goal_id": goal.get("id"),
            "original_goal": {
                "description": goal.get("description", "Unknown goal"),
                "metric_type": goal.get("metric_type", "unknown"),
                "target_value": goal.get("target_value", 1)
            },
            "decomposition": {
                "asset_deliverables": [{
                    "name": "Goal Result",
                    "description": "Achievement of the stated goal",
                    "value_proposition": "Completion of user objective",
                    "completion_criteria": "Goal target reached",
                    "estimated_effort": "medium",
                    "user_impact": "immediate"
                }],
                "thinking_components": [{
                    "name": "Goal Planning",
                    "description": "Strategic approach to goal achievement",
                    "supports_deliverables": ["Goal Result"],
                    "complexity": "simple"
                }],
                "completion_criteria": {
                    "asset_quality_threshold": 60,
                    "thinking_depth_required": "simple",
                    "user_validation_needed": False
                },
                "user_value_score": 60,
                "complexity_level": "simple",
                "domain_category": "universal",
                "pillar_adherence": {
                    "domain_agnostic": True,
                    "user_value_focused": True,
                    "minimal_interface_ready": True
                }
            },
            "decomposed_at": datetime.now().isoformat(),
            "decomposition_method": "emergency"
        }
    
    async def create_todo_structure(self, goal_decomposition: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Create structured TODO list from goal decomposition
        
        Returns:
            {
                "asset_todos": [...],    # Concrete deliverables for user
                "thinking_todos": [...], # Strategic planning tasks
                "completion_flow": {...} # How todos lead to final deliverable
            }
        """
        try:
            decomposition = goal_decomposition.get("decomposition", {})
            goal_id = goal_decomposition.get("goal_id")
            
            asset_todos = []
            thinking_todos = []
            
            # Create asset TODOs (high priority, concrete deliverables)
            for asset in decomposition.get("asset_deliverables", []):
                asset_todo = {
                    "id": f"asset_{len(asset_todos) + 1}",
                    "type": "asset",
                    "name": asset.get("name", "Asset Creation"),
                    "description": asset.get("description", ""),
                    "value_proposition": asset.get("value_proposition", ""),
                    "completion_criteria": asset.get("completion_criteria", ""),
                    "priority": "high",
                    "estimated_effort": asset.get("estimated_effort", "medium"),
                    "user_impact": asset.get("user_impact", "immediate"),
                    "goal_id": goal_id,
                    "deliverable_type": "concrete_asset"
                }
                asset_todos.append(asset_todo)
            
            # Create thinking TODOs (medium priority, strategic support)
            for thinking in decomposition.get("thinking_components", []):
                thinking_todo = {
                    "id": f"thinking_{len(thinking_todos) + 1}",
                    "type": "thinking", 
                    "name": thinking.get("name", "Strategic Analysis"),
                    "description": thinking.get("description", ""),
                    "supports_assets": thinking.get("supports_deliverables", []),
                    "complexity": thinking.get("complexity", "medium"),
                    "priority": "medium",
                    "goal_id": goal_id,
                    "deliverable_type": "strategic_thinking"
                }
                thinking_todos.append(thinking_todo)
            
            # Create completion flow
            completion_flow = {
                "asset_dependency_chain": [todo["id"] for todo in asset_todos],
                "thinking_support_map": {
                    todo["id"]: todo.get("supports_assets", []) 
                    for todo in thinking_todos
                },
                "completion_criteria": decomposition.get("completion_criteria", {}),
                "final_deliverable": {
                    "name": f"Complete Goal Package: {goal_decomposition.get('original_goal', {}).get('description', 'Unknown')}",
                    "components": [todo["name"] for todo in asset_todos],
                    "thinking_support": [todo["name"] for todo in thinking_todos],
                    "user_value_score": decomposition.get("user_value_score", 70)
                }
            }
            
            todo_structure = {
                "goal_id": goal_id,
                "asset_todos": asset_todos,
                "thinking_todos": thinking_todos,
                "completion_flow": completion_flow,
                "total_todos": len(asset_todos) + len(thinking_todos),
                "asset_count": len(asset_todos),
                "thinking_count": len(thinking_todos),
                "expected_user_value": decomposition.get("user_value_score", 70),
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ TODO structure created: {len(asset_todos)} assets, {len(thinking_todos)} thinking components")
            
            return todo_structure
            
        except Exception as e:
            logger.error(f"❌ Error creating TODO structure: {e}")
            return {
                "goal_id": goal_decomposition.get("goal_id"),
                "asset_todos": [],
                "thinking_todos": [],
                "completion_flow": {},
                "error": str(e)
            }

# Factory function for easy usage
def create_goal_decomposer() -> GoalDecomposition:
    """Create a new GoalDecomposition instance"""
    return GoalDecomposition()

# Async wrapper for easy integration
async def decompose_goal_to_todos(goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    🎯 Convenience function: Goal → TODO structure in one call
    
    Returns complete structure with assets and thinking components
    """
    decomposer = create_goal_decomposer()
    decomposition = await decomposer.decompose_goal(goal)
    todo_structure = await decomposer.create_todo_structure(decomposition)
    
    return {
        "goal_decomposition": decomposition,
        "todo_structure": todo_structure,
        "summary": {
            "asset_deliverables_count": len(todo_structure.get("asset_todos", [])),
            "thinking_components_count": len(todo_structure.get("thinking_todos", [])),
            "expected_user_value": decomposition.get("decomposition", {}).get("user_value_score", 70),
            "pillar_compliant": decomposition.get("decomposition", {}).get("pillar_adherence", {}).get("user_value_focused", False)
        }
    }