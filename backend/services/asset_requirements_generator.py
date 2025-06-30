"""
Asset Requirements Generator - AI-driven asset requirements generation (Pillar 2: AI-Driven)
Generates concrete, actionable asset requirements from workspace goals using OpenAI SDK.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from openai import AsyncOpenAI
from models import AssetRequirement, WorkspaceGoal
from database_asset_extensions import AssetDrivenDatabaseManager

logger = logging.getLogger(__name__)

class AssetRequirementsGenerator:
    """AI-driven asset requirements generation (Pillar 2: AI-Driven)"""
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.openai_client = openai_client or AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_manager = AssetDrivenDatabaseManager()
        
        # Configuration from environment (Pillar-compliant)
        self.enhancement_model = os.getenv("AI_ENHANCEMENT_MODEL", "gpt-4o-mini")
        self.auto_decomposition_enabled = os.getenv("AUTO_GOAL_DECOMPOSITION_TO_ASSETS", "true").lower() == "true"
        self.universal_patterns_enabled = os.getenv("UNIVERSAL_ASSET_PATTERNS", "true").lower() == "true"
        self.domain_agnostic = os.getenv("DOMAIN_AGNOSTIC_VALIDATION", "true").lower() == "true"
        
        logger.info("🤖 AssetRequirementsGenerator initialized with AI-driven configuration")
        
    async def generate_from_goal(self, goal: WorkspaceGoal) -> List[AssetRequirement]:
        """Generate asset requirements from goal using AI decomposition (Pillar 2: AI-Driven)"""
        
        try:
            logger.info(f"🎯 Generating asset requirements for goal: {goal.metric_type}")
            
            # Check if requirements already exist
            existing_requirements = await self.db_manager.get_asset_requirements_for_goal(goal.id)
            if existing_requirements:
                logger.info(f"Goal {goal.id} already has {len(existing_requirements)} asset requirements")
                return existing_requirements
            
            # AI-driven goal decomposition
            decomposition_prompt = self._build_decomposition_prompt(goal)
            
            # Use OpenAI SDK for decomposition (Pillar 1: OpenAI SDK)
            response = await self.openai_client.chat.completions.create(
                model=self.enhancement_model,
                messages=[{"role": "user", "content": decomposition_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2  # Low temperature for consistent results
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            logger.info(f"🤖 AI decomposition completed for goal {goal.id}")
            
            # Parse AI response and create requirements
            requirements = await self._create_requirements_from_ai_output(goal, ai_response)
            
            # Store requirements in database
            stored_requirements = []
            for req in requirements:
                try:
                    stored_req = await self.db_manager.create_asset_requirement(req)
                    stored_requirements.append(stored_req)
                    logger.info(f"✅ Asset requirement created: {stored_req.asset_name}")
                except Exception as e:
                    logger.error(f"Failed to store requirement {req.asset_name}: {e}")
                    
            logger.info(f"🎯 Generated {len(stored_requirements)} asset requirements for goal {goal.id}")
            return stored_requirements
            
        except Exception as e:
            logger.error(f"Failed to generate asset requirements for goal {goal.id}: {e}")
            return []
    
    def _build_decomposition_prompt(self, goal: WorkspaceGoal) -> str:
        """Build AI prompt for goal decomposition (Pillar 2: AI-Driven, zero hard-coding)"""
        
        # Universal decomposition prompt (Pillar 3: Universal & Language-agnostic)
        prompt = f"""
        You are an expert business analyst specializing in breaking down goals into concrete, actionable asset requirements.
        
        GOAL TO DECOMPOSE:
        - Metric Type: {goal.metric_type}
        - Target Value: {goal.target_value}
        - Current Value: {goal.current_value}
        - Status: {goal.status}
        - Workspace ID: {goal.workspace_id}
        
        TASK:
        Decompose this goal into 3-7 concrete asset requirements that, when completed, will achieve the goal.
        
        ASSET REQUIREMENTS CRITERIA:
        1. Each asset must be CONCRETE and ACTIONABLE (not abstract concepts)
        2. Each asset must have clear BUSINESS VALUE and immediate utility
        3. Assets should be SPECIFIC enough that someone could create them with clear instructions
        4. Focus on DELIVERABLE OUTPUTS rather than processes
        5. Each asset should contribute measurably to the goal achievement
        
        ASSET TYPES TO CONSIDER:
        - document: Reports, strategies, analyses, plans, guides
        - data: Databases, lists, datasets, spreadsheets, structured information
        - design: Mockups, graphics, layouts, wireframes, visual assets
        - code: Scripts, applications, tools, automations
        - presentation: Slides, demos, training materials
        
        RESPONSE FORMAT (JSON):
        {{
            "goal_analysis": {{
                "complexity_level": "simple|medium|complex",
                "domain_category": "universal|specific",
                "estimated_completion_time": "hours or days",
                "success_indicators": ["list of measurable success indicators"]
            }},
            "asset_requirements": [
                {{
                    "asset_name": "Specific name of the asset",
                    "asset_type": "document|data|design|code|presentation",
                    "asset_format": "structured_data|document|spreadsheet|json|etc",
                    "description": "Detailed description of what this asset contains",
                    "business_value_score": 0.8,
                    "actionability_score": 0.9,
                    "acceptance_criteria": {{
                        "content_requirements": ["specific content that must be included"],
                        "quality_standards": ["quality standards to meet"],
                        "completion_criteria": ["criteria for considering this complete"]
                    }},
                    "priority": "high|medium|low",
                    "estimated_effort": "low|medium|high",
                    "user_impact": "immediate|short-term|long-term",
                    "weight": 1.5,
                    "mandatory": true,
                    "value_proposition": "Clear value this asset provides"
                }}
            ]
        }}
        
        IMPORTANT:
        - Focus on CONCRETE OUTPUTS that deliver business value
        - Avoid generic or abstract requirements
        - Each asset should be something a stakeholder could immediately use
        - Ensure assets are specific to achieving the stated goal
        - Consider the target value when sizing requirements
        """
        
        return prompt
    
    async def _create_requirements_from_ai_output(self, goal: WorkspaceGoal, ai_response: Dict[str, Any]) -> List[AssetRequirement]:
        """Parse AI response and create AssetRequirement objects"""
        
        requirements = []
        
        try:
            goal_analysis = ai_response.get("goal_analysis", {})
            asset_requirements_data = ai_response.get("asset_requirements", [])
            
            for i, req_data in enumerate(asset_requirements_data):
                try:
                    # Create AssetRequirement object with AI-generated data
                    requirement = AssetRequirement(
                        goal_id=goal.id,
                        workspace_id=goal.workspace_id,
                        
                        # Core asset identification
                        asset_name=req_data.get("asset_name"),
                        asset_type=req_data.get("asset_type", "document"),
                        asset_format=req_data.get("asset_format", "structured_data"),
                        description=req_data.get("description"),
                        
                        # Requirements and criteria
                        acceptance_criteria=req_data.get("acceptance_criteria", {}),
                        weight=float(req_data.get("weight", 1.0)),
                        mandatory=req_data.get("mandatory", True),
                        business_value_score=float(req_data.get("business_value_score", 0.7)),
                        
                        # From AI analysis
                        priority=req_data.get("priority", "medium"),
                        estimated_effort=req_data.get("estimated_effort", "medium"),
                        user_impact=req_data.get("user_impact", "short-term"),
                        value_proposition=req_data.get("value_proposition"),
                        
                        # Quality and validation
                        validation_rules={
                            "ai_generated": True,
                            "goal_analysis": goal_analysis,
                            "business_value_threshold": req_data.get("business_value_score", 0.7),
                            "actionability_threshold": req_data.get("actionability_score", 0.8)
                        },
                        
                        # Pillar compliance
                        ai_generated=True,
                        language_agnostic=True,
                        sdk_compatible=True,
                        
                        # Status
                        status="pending",
                        progress_percentage=0
                    )
                    
                    requirements.append(requirement)
                    
                except Exception as e:
                    logger.error(f"Failed to create requirement {i}: {e}")
                    continue
                    
            logger.info(f"✅ Created {len(requirements)} asset requirements from AI output")
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return []
    
    async def validate_and_enhance_requirements(self, requirements: List[AssetRequirement]) -> List[AssetRequirement]:
        """AI validation and enhancement of requirements (Pillar 12: Concrete Deliverables)"""
        
        enhanced_requirements = []
        
        for requirement in requirements:
            try:
                # AI validation prompt for requirement quality
                validation_prompt = f"""
                Validate and enhance this asset requirement for business value and actionability:
                
                CURRENT REQUIREMENT:
                Name: {requirement.asset_name}
                Type: {requirement.asset_type}
                Description: {requirement.description}
                Business Value Score: {requirement.business_value_score}
                
                VALIDATION CRITERIA:
                1. Is this requirement CONCRETE and SPECIFIC?
                2. Does it have clear BUSINESS VALUE?
                3. Can someone create this asset with clear instructions?
                4. Is it ACTIONABLE (not abstract)?
                5. Does it contribute measurably to goal achievement?
                
                ENHANCEMENT TASK:
                If needed, enhance the requirement to make it more:
                - Concrete and specific
                - Immediately actionable
                - Business-valuable
                - Clearly defined
                
                RESPONSE FORMAT (JSON):
                {{
                    "validation_score": 0.85,
                    "passed_validation": true,
                    "enhancement_needed": false,
                    "enhanced_requirement": {{
                        "asset_name": "Enhanced name if needed",
                        "description": "Enhanced description if needed",
                        "acceptance_criteria": {{"enhanced": "criteria"}},
                        "business_value_score": 0.9
                    }},
                    "validation_feedback": "Specific feedback on quality"
                }}
                """
                
                response = await self.openai_client.chat.completions.create(
                    model=self.enhancement_model,
                    messages=[{"role": "user", "content": validation_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                validation_result = json.loads(response.choices[0].message.content)
                
                # Apply enhancements if needed
                if validation_result.get("enhancement_needed", False):
                    enhanced_data = validation_result.get("enhanced_requirement", {})
                    
                    # Update requirement with enhanced data
                    if enhanced_data.get("asset_name"):
                        requirement.asset_name = enhanced_data["asset_name"]
                    if enhanced_data.get("description"):
                        requirement.description = enhanced_data["description"]
                    if enhanced_data.get("acceptance_criteria"):
                        requirement.acceptance_criteria.update(enhanced_data["acceptance_criteria"])
                    if enhanced_data.get("business_value_score"):
                        requirement.business_value_score = float(enhanced_data["business_value_score"])
                    
                    logger.info(f"🤖 Enhanced requirement: {requirement.asset_name}")
                
                enhanced_requirements.append(requirement)
                
            except Exception as e:
                logger.error(f"Failed to validate requirement {requirement.asset_name}: {e}")
                enhanced_requirements.append(requirement)  # Keep original if validation fails
                
        return enhanced_requirements
    
    async def auto_categorize_asset_type(self, requirement_description: str) -> str:
        """AI categorization of asset types (Pillar 2: AI-Driven)"""
        
        try:
            categorization_prompt = f"""
            Categorize this asset requirement into the most appropriate type:
            
            REQUIREMENT: {requirement_description}
            
            ASSET TYPES:
            - document: Reports, strategies, analyses, plans, guides, documentation
            - data: Databases, lists, datasets, spreadsheets, structured information
            - design: Mockups, graphics, layouts, wireframes, visual assets, UI/UX
            - code: Scripts, applications, tools, automations, software
            - presentation: Slides, demos, training materials, videos
            
            Choose the single most appropriate type based on the primary deliverable.
            
            RESPONSE: Just the type name (document|data|design|code|presentation)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.enhancement_model,
                messages=[{"role": "user", "content": categorization_prompt}],
                temperature=0.1,
                max_tokens=20
            )
            
            asset_type = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            valid_types = {"document", "data", "design", "code", "presentation"}
            if asset_type in valid_types:
                return asset_type
            else:
                logger.warning(f"Invalid asset type '{asset_type}' returned, defaulting to 'document'")
                return "document"
                
        except Exception as e:
            logger.error(f"Failed to categorize asset type: {e}")
            return "document"  # Default fallback
    
    async def get_enhancement_suggestions(self, requirement: AssetRequirement) -> Dict[str, Any]:
        """Get AI-driven enhancement suggestions for a requirement"""
        
        try:
            suggestion_prompt = f"""
            Provide specific enhancement suggestions for this asset requirement:
            
            REQUIREMENT:
            Name: {requirement.asset_name}
            Type: {requirement.asset_type}
            Description: {requirement.description}
            Current Business Value: {requirement.business_value_score}
            
            PROVIDE SUGGESTIONS FOR:
            1. Making it more concrete and specific
            2. Increasing business value and actionability
            3. Clearer acceptance criteria
            4. Better naming if needed
            5. Additional value-add components
            
            RESPONSE FORMAT (JSON):
            {{
                "specificity_improvements": ["suggestion 1", "suggestion 2"],
                "business_value_enhancements": ["enhancement 1", "enhancement 2"],
                "acceptance_criteria_additions": {{"new_criteria": "values"}},
                "naming_suggestions": ["alternative name 1", "alternative name 2"],
                "value_add_components": ["additional component 1", "component 2"]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.enhancement_model,
                messages=[{"role": "user", "content": suggestion_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Failed to get enhancement suggestions: {e}")
            return {}