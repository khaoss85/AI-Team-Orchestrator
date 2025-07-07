# backend/deliverable_system/schema_generator.py

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import dal sistema esistente
from models import DeliverableRequirements, AssetSchema, AssetRequirement

logger = logging.getLogger(__name__)

class AssetSchemaGenerator:
    """Genera dinamicamente schemi per asset azionabili"""
    
    def __init__(self):
        self.schema_cache = {}
        self.base_schemas = self._load_base_schemas()
    
    def _load_base_schemas(self) -> Dict[str, Dict]:
        """Carica schemi base per tipi comuni di asset"""
        
        return {
            # MARKETING ASSETS
            "content_calendar": {
                "posts": [
                    {
                        "date": "YYYY-MM-DD",
                        "time": "HH:MM",
                        "platform": "instagram|facebook|linkedin|twitter",
                        "content_type": "image|video|carousel|story",
                        "caption": "string",
                        "hashtags": ["string"],
                        "visual_description": "string",
                        "call_to_action": "string",
                        "target_audience": "string",
                        "engagement_goal": "likes|comments|shares|saves|clicks",
                        "automation_command": "string"
                    }
                ],
                "posting_schedule": {
                    "frequency": "daily|weekly|biweekly",
                    "optimal_times": ["HH:MM"],
                    "content_mix": {
                        "educational": "percentage",
                        "promotional": "percentage", 
                        "entertaining": "percentage"
                    }
                },
                "performance_targets": {
                    "monthly_reach": "number",
                    "engagement_rate": "percentage",
                    "follower_growth": "number"
                }
            },
            
            "instagram_growth_strategy": {
                "content_pillars": ["string"],
                "posting_frequency": "number_per_week",
                "hashtag_strategy": {
                    "primary_hashtags": ["string"],
                    "secondary_hashtags": ["string"],
                    "trending_hashtags": ["string"],
                    "hashtag_mix_ratio": "string"
                },
                "engagement_tactics": [
                    {
                        "tactic": "string",
                        "implementation": "string",
                        "expected_result": "string"
                    }
                ],
                "automation_setup": {
                    "scheduling_tool": "string",
                    "auto_responses": ["string"],
                    "monitoring_keywords": ["string"]
                }
            },
            
            "audience_analysis_report": {
                "demographics": {
                    "age_groups": {"18-24": "percentage", "25-34": "percentage", "35-44": "percentage"},
                    "gender_split": {"male": "percentage", "female": "percentage", "other": "percentage"},
                    "locations": [{"country": "string", "percentage": "number"}],
                    "interests": ["string"],
                    "behavior_patterns": ["string"]
                },
                "engagement_insights": {
                    "best_posting_times": ["HH:MM"],
                    "preferred_content_types": ["string"],
                    "interaction_preferences": ["string"]
                },
                "content_preferences": {
                    "topics_of_interest": ["string"],
                    "content_format_preferences": ["string"],
                    "tone_preference": "string"
                },
                "actionable_recommendations": [
                    {
                        "recommendation": "string",
                        "implementation": "string",
                        "expected_impact": "string"
                    }
                ]
            },
            
            # SALES ASSETS
            "qualified_contact_database": {
                "contacts": [
                    {
                        "name": "string",
                        "company": "string",
                        "title": "string",
                        "email": "email_format",
                        "phone": "phone_format",
                        "linkedin_url": "url_format",
                        "company_size": "1-10|11-50|51-200|201-1000|1000+",
                        "industry": "string",
                        "qualification_score": "1-10",
                        "lead_source": "string",
                        "pain_points": ["string"],
                        "budget_range": "string",
                        "decision_timeline": "immediate|1-3_months|3-6_months|6+_months",
                        "next_action": "call|email|demo|proposal|follow_up",
                        "priority": "hot|warm|cold",
                        "notes": "string",
                        "last_contact_date": "YYYY-MM-DD",
                        "assigned_to": "string"
                    }
                ],
                "summary_stats": {
                    "total_contacts": "number",
                    "qualified_leads": "number",
                    "hot_prospects": "number",
                    "estimated_pipeline_value": "currency"
                },
                "segmentation": {
                    "by_industry": {"industry_name": "count"},
                    "by_company_size": {"size_range": "count"},
                    "by_qualification_score": {"score_range": "count"}
                }
            },
            
            "outreach_email_templates": {
                "templates": [
                    {
                        "template_name": "string",
                        "subject_line": "string",
                        "email_body": "string",
                        "personalization_fields": ["{{field_name}}"],
                        "call_to_action": "string",
                        "follow_up_sequence": [
                            {
                                "days_after": "number",
                                "subject": "string",
                                "body": "string"
                            }
                        ],
                        "target_segment": "string",
                        "expected_response_rate": "percentage"
                    }
                ],
                "automation_setup": {
                    "email_tool": "string",
                    "merge_fields_mapping": {"field_name": "data_source"},
                    "sending_schedule": "string",
                    "tracking_metrics": ["opens", "clicks", "responses"]
                }
            },
            
            # SPORTS ASSETS
            "training_program": {
                "program_overview": {
                    "name": "string",
                    "duration_weeks": "number",
                    "skill_level": "beginner|intermediate|advanced",
                    "goals": ["string"],
                    "equipment_needed": ["string"]
                },
                "weekly_schedule": [
                    {
                        "week": "number",
                        "focus": "string",
                        "workouts": [
                            {
                                "day": "string",
                                "workout_name": "string",
                                "duration_minutes": "number",
                                "exercises": [
                                    {
                                        "name": "string",
                                        "sets": "number",
                                        "reps": "number|range",
                                        "weight": "string",
                                        "rest_seconds": "number",
                                        "notes": "string"
                                    }
                                ],
                                "warm_up": "string",
                                "cool_down": "string"
                            }
                        ]
                    }
                ],
                "progression_plan": {
                    "progression_method": "string",
                    "milestones": [
                        {
                            "week": "number",
                            "target": "string",
                            "measurement": "string"
                        }
                    ]
                },
                "nutrition_guidelines": {
                    "calorie_target": "number",
                    "macro_split": {"protein": "percentage", "carbs": "percentage", "fat": "percentage"},
                    "meal_timing": "string",
                    "hydration": "string"
                }
            },
            
            "performance_tracking_system": {
                "kpis": [
                    {
                        "metric_name": "string",
                        "measurement_unit": "string",
                        "target_value": "number",
                        "current_baseline": "number",
                        "tracking_frequency": "daily|weekly|monthly",
                        "measurement_method": "string"
                    }
                ],
                "tracking_schedule": {
                    "daily_metrics": ["string"],
                    "weekly_assessments": ["string"],
                    "monthly_evaluations": ["string"]
                },
                "reporting_dashboard": {
                    "charts_to_create": ["string"],
                    "alert_thresholds": {"metric": "threshold_value"},
                    "review_schedule": "string"
                }
            },
            
            # FINANCE ASSETS
            "financial_model": {
                "revenue_projections": {
                    "monthly_revenue": [{"month": "string", "amount": "number"}],
                    "revenue_streams": [{"stream": "string", "percentage": "number"}],
                    "growth_assumptions": {"monthly_growth_rate": "percentage"}
                },
                "cost_structure": {
                    "fixed_costs": [{"category": "string", "monthly_amount": "number"}],
                    "variable_costs": [{"category": "string", "percentage_of_revenue": "number"}],
                    "one_time_costs": [{"item": "string", "amount": "number", "timing": "string"}]
                },
                "cash_flow": {
                    "monthly_cash_flow": [{"month": "string", "inflow": "number", "outflow": "number", "net": "number"}],
                    "break_even_month": "number",
                    "runway_months": "number"
                },
                "scenarios": {
                    "best_case": {"assumptions": "string", "outcome": "string"},
                    "base_case": {"assumptions": "string", "outcome": "string"},
                    "worst_case": {"assumptions": "string", "outcome": "string"}
                }
            },
            
            "budget_allocation_plan": {
                "total_budget": "number",
                "budget_categories": [
                    {
                        "category": "string",
                        "allocated_amount": "number",
                        "percentage_of_total": "number",
                        "justification": "string",
                        "expected_roi": "string"
                    }
                ],
                "timeline": {
                    "budget_period": "string",
                    "spending_schedule": [{"month": "string", "planned_spend": "number"}],
                    "review_milestones": ["string"]
                },
                "approval_workflow": {
                    "approval_levels": [{"amount_threshold": "number", "approver": "string"}],
                    "documentation_required": ["string"]
                }
            },
            
            # RESEARCH ASSETS
            "research_database": {
                "data_sources": [
                    {
                        "source_name": "string",
                        "source_type": "primary|secondary",
                        "credibility_score": "1-10",
                        "data_points": "number",
                        "last_updated": "YYYY-MM-DD"
                    }
                ],
                "key_findings": [
                    {
                        "finding": "string",
                        "supporting_evidence": ["string"],
                        "confidence_level": "high|medium|low",
                        "business_implication": "string"
                    }
                ],
                "data_quality": {
                    "completeness_score": "percentage",
                    "accuracy_indicators": ["string"],
                    "limitations": ["string"]
                }
            },
            
            "executive_recommendations": {
                "strategic_recommendations": [
                    {
                        "recommendation": "string",
                        "rationale": "string",
                        "expected_impact": "string",
                        "implementation_effort": "low|medium|high",
                        "timeline": "string",
                        "resources_required": ["string"],
                        "success_metrics": ["string"],
                        "risks": ["string"]
                    }
                ],
                "quick_wins": [
                    {
                        "action": "string",
                        "effort": "string",
                        "impact": "string",
                        "timeline": "string"
                    }
                ],
                "implementation_roadmap": {
                    "phase_1": {"duration": "string", "actions": ["string"]},
                    "phase_2": {"duration": "string", "actions": ["string"]},
                    "phase_3": {"duration": "string", "actions": ["string"]}
                }
            },
            
            # GENERIC BUSINESS ASSETS
            "action_plan": {
                "objectives": [
                    {
                        "objective": "string",
                        "success_criteria": ["string"],
                        "deadline": "YYYY-MM-DD",
                        "owner": "string",
                        "priority": "high|medium|low"
                    }
                ],
                "tasks": [
                    {
                        "task": "string",
                        "description": "string",
                        "assigned_to": "string",
                        "due_date": "YYYY-MM-DD",
                        "status": "not_started|in_progress|completed",
                        "dependencies": ["string"],
                        "resources_needed": ["string"]
                    }
                ],
                "milestones": [
                    {
                        "milestone": "string",
                        "target_date": "YYYY-MM-DD",
                        "completion_criteria": ["string"]
                    }
                ],
                "risk_mitigation": [
                    {
                        "risk": "string",
                        "impact": "high|medium|low",
                        "probability": "high|medium|low",
                        "mitigation_plan": "string"
                    }
                ]
            },
            
            "implementation_guide": {
                "step_by_step_process": [
                    {
                        "step": "number",
                        "title": "string",
                        "description": "string",
                        "estimated_time": "string",
                        "required_skills": ["string"],
                        "tools_needed": ["string"],
                        "success_indicators": ["string"],
                        "troubleshooting": [
                            {
                                "problem": "string",
                                "solution": "string"
                            }
                        ]
                    }
                ],
                "best_practices": ["string"],
                "common_pitfalls": ["string"],
                "quality_checklist": ["string"],
                "support_resources": [
                    {
                        "resource_type": "documentation|training|support",
                        "name": "string",
                        "location": "string"
                    }
                ]
            }
        }
    
    async def generate_asset_schemas(self, requirements: DeliverableRequirements) -> Dict[str, AssetSchema]:
        """
        Genera schemi dinamici per tutti gli asset richiesti
        """
        
        schemas = {}
        
        for asset_req in requirements.primary_assets_needed:
            schema = await self._generate_single_asset_schema(asset_req, requirements)
            schemas[asset_req.asset_type] = schema
            
        logger.info(f"📐 SCHEMAS: Generated {len(schemas)} asset schemas for {requirements.workspace_id}")
        return schemas
    
    async def _generate_single_asset_schema(
        self, 
        asset_req: AssetRequirement, 
        requirements: DeliverableRequirements
    ) -> AssetSchema:
        """
        Genera schema per un singolo asset
        """
        
        # Prima controlla se esiste uno schema base
        base_schema = self.base_schemas.get(asset_req.asset_type)
        
        if base_schema:
            # Usa schema base e personalizza
            schema_definition = self._customize_base_schema(base_schema, asset_req, requirements)
        else:
            # Genera schema dinamico
            schema_definition = await self._generate_dynamic_schema(asset_req, requirements)
        
        # Genera istruzioni d'uso
        usage_instructions = self._generate_usage_instructions(asset_req, schema_definition)
        
        # Determina automation readiness
        automation_ready = self._assess_automation_readiness(asset_req, schema_definition)
        
        return AssetSchema(
            asset_name=asset_req.asset_type,
            schema_definition=schema_definition,
            validation_rules=asset_req.validation_criteria,
            usage_instructions=usage_instructions,
            automation_ready=automation_ready
        )
    
    def _customize_base_schema(
        self, 
        base_schema: Dict, 
        asset_req: AssetRequirement, 
        requirements: DeliverableRequirements
    ) -> Dict[str, Any]:
        """
        Personalizza uno schema base in base ai requirements specifici
        """
        
        # Copia lo schema base
        customized_schema = json.loads(json.dumps(base_schema))
        
        # Personalizzazioni basate sulla categoria del deliverable
        category = requirements.deliverable_category
        
        if category == "marketing" and asset_req.asset_type == "content_calendar":
            # Personalizzazioni per marketing
            customized_schema["brand_guidelines"] = {
                "tone_of_voice": "string",
                "visual_style": "string",
                "brand_colors": ["string"],
                "logo_usage": "string"
            }
            
        elif category == "sales" and asset_req.asset_type == "qualified_contact_database":
            # Personalizzazioni per sales
            customized_schema["crm_integration"] = {
                "import_format": "csv|xlsx|json",
                "field_mapping": {"crm_field": "database_field"},
                "automation_triggers": ["string"]
            }
        
        # Aggiungi metadati per validazione
        customized_schema["_metadata"] = {
            "asset_type": asset_req.asset_type,
            "actionability_level": asset_req.actionability_level,
            "business_impact": asset_req.business_impact,
            "priority": asset_req.priority
        }
        
        return customized_schema
    
    async def _generate_dynamic_schema(
        self, 
        asset_req: AssetRequirement, 
        requirements: DeliverableRequirements
    ) -> Dict[str, Any]:
        """
        Genera schema dinamico per asset non predefiniti
        NOTA: In implementazione reale userebbe LLM calls
        """
        
        # Schema dinamico basato su pattern comuni
        dynamic_schema = {
            "asset_info": {
                "name": asset_req.asset_type,
                "description": f"Dynamic asset for {requirements.deliverable_category}",
                "format": asset_req.asset_format,
                "actionability": asset_req.actionability_level
            },
            "main_content": {},
            "metadata": {
                "created_at": "timestamp",
                "version": "string",
                "last_updated": "timestamp"
            },
            "usage": {
                "instructions": "string",
                "required_tools": ["string"],
                "automation_possible": "boolean"
            }
        }
        
        # Personalizza in base al formato
        if asset_req.asset_format == "structured_data":
            dynamic_schema["main_content"] = {
                "data_points": [
                    {
                        "field_name": "string",
                        "field_value": "any",
                        "field_type": "string|number|boolean|date"
                    }
                ]
            }
        elif asset_req.asset_format == "document":
            dynamic_schema["main_content"] = {
                "sections": [
                    {
                        "section_title": "string",
                        "section_content": "string",
                        "subsections": ["string"]
                    }
                ]
            }
        elif asset_req.asset_format == "spreadsheet":
            dynamic_schema["main_content"] = {
                "worksheets": [
                    {
                        "sheet_name": "string",
                        "columns": ["string"],
                        "data_rows": [["any"]],
                        "formulas": ["string"]
                    }
                ]
            }
        
        return dynamic_schema
    
    def _generate_usage_instructions(self, asset_req: AssetRequirement, schema: Dict) -> str:
        """
        Genera istruzioni d'uso specifiche per l'asset
        """
        
        instructions = f"""
ASSET: {asset_req.asset_type}
ACTIONABILITY LEVEL: {asset_req.actionability_level}
BUSINESS IMPACT: {asset_req.business_impact}

USAGE INSTRUCTIONS:

1. VALIDATION:
   - Verify all required fields are populated
   - Check data quality against validation criteria: {', '.join(asset_req.validation_criteria)}
   
2. IMPLEMENTATION:
"""
        
        if asset_req.actionability_level == "ready_to_use":
            instructions += """   - Asset can be used immediately without modifications
   - Copy/paste or import directly into your target system
   - Follow automation instructions if provided"""
        elif asset_req.actionability_level == "needs_customization":
            instructions += """   - Review and customize fields marked as [CUSTOMIZE]
   - Adapt content to your specific context
   - Test before full implementation"""
        else:  # template
            instructions += """   - Use as template/framework for your specific needs
   - Fill in all placeholder content
   - Adapt structure to your requirements"""
        
        instructions += f"""

3. SUCCESS METRICS:
   - Monitor performance against business impact: {asset_req.business_impact}
   - Track validation criteria compliance
   - Measure ROI and effectiveness

4. TROUBLESHOOTING:
   - Refer to validation_rules for quality checks
   - Contact support if automation features fail
   - Document any customizations made
"""
        
        return instructions.strip()
    
    def _assess_automation_readiness(self, asset_req: AssetRequirement, schema: Dict) -> bool:
        """
        Valuta se l'asset è pronto per automazione
        """
        
        # Criteri per automation readiness
        automation_indicators = [
            asset_req.actionability_level == "ready_to_use",
            asset_req.asset_format in ["structured_data", "spreadsheet"],
            "automation" in str(schema).lower(),
            len(asset_req.validation_criteria) >= 2
        ]
        
        # Deve soddisfare almeno 3 criteri su 4
        return sum(automation_indicators) >= 3
    
    def get_schema_for_asset_type(self, asset_type: str) -> Optional[Dict]:
        """
        Recupera schema esistente per un tipo di asset
        """
        
        return self.base_schemas.get(asset_type)
    
    def validate_asset_against_schema(self, asset_data: Dict, schema: AssetSchema) -> Dict[str, Any]:
        """
        Valida asset data contro il suo schema
        """
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "completeness_score": 0.0
        }
        
        try:
            schema_def = schema.schema_definition
            
            # Validazione strutturale base
            if not self._validate_structure(asset_data, schema_def):
                validation_result["valid"] = False
                validation_result["errors"].append("Structure does not match schema")
            
            # Validazione criteri specifici
            for criterion in schema.validation_rules:
                if not self._validate_criterion(asset_data, criterion):
                    validation_result["warnings"].append(f"Validation criterion not met: {criterion}")
            
            # Calcola completeness score
            validation_result["completeness_score"] = self._calculate_completeness_score(asset_data, schema_def)
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_structure(self, data: Dict, schema: Dict) -> bool:
        """
        Validazione strutturale base (simplified)
        """
        
        # Implementazione semplificata - in realtà userebbe jsonschema o simile
        return isinstance(data, dict) and len(data) > 0
    
    def _validate_criterion(self, data: Dict, criterion: str) -> bool:
        """
        Valida criterio specifico
        """
        
        data_str = json.dumps(data).lower()
        return criterion.replace("_", " ").lower() in data_str
    
    def _calculate_completeness_score(self, data: Dict, schema: Dict) -> float:
        """
        Calcola score di completezza (0.0 - 1.0)
        """
        
        # Implementazione semplificata
        if not data:
            return 0.0
        
        # Conta campi popolati vs campi attesi
        total_fields = self._count_schema_fields(schema)
        populated_fields = self._count_populated_fields(data)
        
        if total_fields == 0:
            return 1.0
        
        return min(1.0, populated_fields / total_fields)
    
    def _count_schema_fields(self, schema: Dict, depth: int = 0) -> int:
        """
        Conta campi nello schema (max depth 3)
        """
        
        if depth > 3:
            return 0
        
        count = 0
        for key, value in schema.items():
            if isinstance(value, dict):
                count += self._count_schema_fields(value, depth + 1)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                count += self._count_schema_fields(value[0], depth + 1)
            else:
                count += 1
        
        return count
    
    def _count_populated_fields(self, data: Dict, depth: int = 0) -> int:
        """
        Conta campi popolati nei dati (max depth 3)
        """
        
        if depth > 3:
            return 0
        
        count = 0
        for key, value in data.items():
            if value is not None and value != "":
                if isinstance(value, dict):
                    count += self._count_populated_fields(value, depth + 1)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    count += self._count_populated_fields(value[0], depth + 1)
                else:
                    count += 1
        
        return count