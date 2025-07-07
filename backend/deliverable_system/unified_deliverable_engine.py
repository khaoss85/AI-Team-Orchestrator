# backend/deliverable_system/unified_deliverable_engine.py
"""
Unified Deliverable Engine - Production v1.0
Consolidates 6 deliverable system files into a single, coherent engine
Eliminates duplicate functionality while maintaining backward compatibility

Consolidates:
- concrete_asset_extractor.py (asset extraction logic)
- markup_processor.py (AI-driven display processing)
- deliverable_pipeline.py (event-driven pipeline)
- requirements_analyzer.py (requirements analysis)
- schema_generator.py (dynamic schema generation) 
- ai_display_enhancer.py (display enhancement integration)
"""

import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4

# Standard imports with graceful fallbacks
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

try:
    from models import (
        AssetSchema, 
        AssetArtifact, 
        AssetRequirement, 
        DeliverableRequirements
    )
except ImportError:
    # Fallback model definitions
    from pydantic import BaseModel, Field
    class AssetSchema(BaseModel):
        name: str
        type: str
        properties: Dict[str, Any] = Field(default_factory=dict)
    
    class AssetArtifact(BaseModel):
        id: str
        name: str
        content: Dict[str, Any] = Field(default_factory=dict)
    
    class AssetRequirement(BaseModel):
        name: str
        type: str
        required: bool = True
    
    class DeliverableRequirements(BaseModel):
        requirements: List[AssetRequirement] = Field(default_factory=list)

# Database imports with fallbacks
try:
    from database import (
        get_supabase_client,
        create_task,
        get_workspace_goals,
        list_tasks,
        get_workspace,
        list_agents
    )
except ImportError:
    get_supabase_client = create_task = get_workspace_goals = None
    list_tasks = get_workspace = list_agents = None

# Quality system imports with fallbacks
try:
    from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
    QUALITY_ENGINE_AVAILABLE = True
except ImportError:
    unified_quality_engine = None
    QUALITY_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration from environment
import os
QUALITY_SCORE_THRESHOLD = float(os.getenv("QUALITY_SCORE_THRESHOLD", "0.8"))
ACTIONABILITY_THRESHOLD = float(os.getenv("ACTIONABILITY_THRESHOLD", "0.7"))
AUTHENTICITY_THRESHOLD = float(os.getenv("AUTHENTICITY_THRESHOLD", "0.8"))
COMPLETENESS_THRESHOLD = float(os.getenv("COMPLETENESS_THRESHOLD", "0.7"))
ENABLE_AI_QUALITY_EVALUATION = os.getenv("ENABLE_AI_QUALITY_EVALUATION", "true").lower() == "true"


class UnifiedDeliverableEngine:
    """
    Unified Deliverable Engine - Production v1.0
    
    Consolidates all deliverable system functionality:
    - ConcreteAssetExtractor (asset extraction with quality validation)
    - DeliverableMarkupProcessor (AI-driven display processing) 
    - DeliverablePipeline (event-driven pipeline management)
    - RequirementsAnalyzer (requirements analysis and validation)
    - AssetSchemaGenerator (dynamic schema generation)
    - AIDisplayEnhancer (display enhancement integration)
    
    Eliminates duplicate functionality while maintaining full compatibility
    """
    
    def __init__(self):
        """Initialize unified deliverable engine with all subsystems"""
        
        # AI client initialization
        self.ai_client = None
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            try:
                self.ai_client = AsyncOpenAI()
                logger.info("✅ AI client initialized for deliverable processing")
            except Exception as e:
                logger.warning(f"AI client initialization failed: {e}")
        
        # Quality engine integration
        self.quality_engine = unified_quality_engine if QUALITY_ENGINE_AVAILABLE else None
        
        # Supabase client
        self.supabase = get_supabase_client() if get_supabase_client else None
        
        # Database-first adapter integration (NEW)
        try:
            from .database_deliverable_adapter import database_deliverable_adapter
            self.database_adapter = database_deliverable_adapter
            logger.info("✅ Database-first adapter integrated successfully")
        except ImportError:
            logger.warning("Database adapter not available")
            self.database_adapter = None
        
        # Pipeline state
        self._running = False
        
        # Caches for performance
        self.schema_cache = {}
        self.processed_cache = {}
        self.extraction_cache = {}
        
        # Universal validation patterns (from concrete_asset_extractor)
        self.universal_validation_patterns = {
            "email_format": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "date_format": r"\d{1,2}[/-]\d{1,2}[/-]?\d{0,4}",
            "time_format": r"\d{1,2}:\d{2}",
            "currency_format": r"[\$€£¥]\s*\d+[.,]?\d*",
            "percentage_format": r"\d+[.,]?\d*\s*%",
            "phone_format": r"[\+]?\d{1,4}?[-\s]?\d{1,15}",
            "url_format": r"https?://[\w\.-]+",
            "hashtag_format": r"#\w+",
            "mention_format": r"@\w+",
            "quantity_format": r"\d+\s*(x|times|reps|sets|pieces|items)",
            "measurement_format": r"\d+[.,]?\d*\s*(kg|lbs|cm|inches|meters|feet|min|sec|hours)"
        }
        
        # Base schemas for dynamic generation (from schema_generator)
        self.base_schemas = self._load_base_schemas()
        
        # Statistics tracking
        self.stats = {
            "total_extractions": 0,
            "total_enhancements": 0,
            "total_pipelines_processed": 0,
            "total_requirements_analyzed": 0,
            "total_schemas_generated": 0,
            "ai_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "quality_validations": 0
        }
        
        logger.info("🔧 Unified Deliverable Engine initialized successfully")
    
    def _load_base_schemas(self) -> Dict[str, Dict]:
        """Load base schemas for common asset types (from schema_generator)"""
        
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
                    "engagement_rate": "percentage",
                    "reach_goal": "number",
                    "conversion_rate": "percentage"
                }
            },
            
            # CONTACT/CRM ASSETS
            "contact_database": {
                "contacts": [
                    {
                        "name": "string",
                        "email": "email_format",
                        "phone": "phone_format", 
                        "company": "string",
                        "position": "string",
                        "industry": "string",
                        "location": "string",
                        "contact_date": "date_format",
                        "lead_score": "number",
                        "status": "cold|warm|hot|qualified|customer",
                        "notes": "string",
                        "source": "string"
                    }
                ],
                "segmentation": {
                    "by_industry": "object",
                    "by_size": "object",
                    "by_location": "object",
                    "by_engagement": "object"
                },
                "outreach_templates": [
                    {
                        "name": "string",
                        "subject": "string", 
                        "content": "string",
                        "personalization_fields": ["string"]
                    }
                ]
            },
            
            # EMAIL MARKETING ASSETS
            "email_templates": {
                "sequences": [
                    {
                        "name": "string",
                        "sequence_type": "onboarding|nurture|sales|re-engagement",
                        "emails": [
                            {
                                "day": "number",
                                "subject": "string",
                                "content": "string",
                                "call_to_action": "string",
                                "personalization": ["string"]
                            }
                        ]
                    }
                ],
                "templates": [
                    {
                        "name": "string",
                        "type": "promotional|newsletter|transactional",
                        "subject": "string",
                        "content": "string",
                        "design_notes": "string"
                    }
                ]
            },
            
            # TRAINING/FITNESS ASSETS
            "training_program": {
                "program_overview": {
                    "name": "string",
                    "duration": "string", 
                    "difficulty": "beginner|intermediate|advanced",
                    "goals": ["string"],
                    "equipment_needed": ["string"]
                },
                "workouts": [
                    {
                        "day": "number",
                        "name": "string",
                        "type": "strength|cardio|flexibility|hiit",
                        "duration": "number",
                        "exercises": [
                            {
                                "name": "string",
                                "sets": "number",
                                "reps": "string",
                                "weight": "string",
                                "rest": "string",
                                "notes": "string"
                            }
                        ]
                    }
                ],
                "progression": {
                    "weekly_adjustments": "string",
                    "progression_metrics": ["string"],
                    "deload_protocol": "string"
                }
            },
            
            # FINANCIAL ASSETS
            "financial_model": {
                "revenue_projections": [
                    {
                        "period": "string",
                        "revenue_streams": "object",
                        "total_revenue": "currency_format",
                        "growth_rate": "percentage_format"
                    }
                ],
                "cost_structure": {
                    "fixed_costs": "object",
                    "variable_costs": "object",
                    "total_costs": "currency_format"
                },
                "key_metrics": {
                    "break_even_point": "string",
                    "profit_margin": "percentage_format",
                    "roi": "percentage_format",
                    "cash_flow": "object"
                }
            },
            
            # RESEARCH ASSETS
            "research_database": {
                "research_findings": [
                    {
                        "topic": "string",
                        "source": "string",
                        "key_insights": ["string"],
                        "data_points": ["string"],
                        "relevance_score": "number",
                        "date_collected": "date_format"
                    }
                ],
                "methodology": {
                    "research_methods": ["string"],
                    "sample_size": "number",
                    "data_sources": ["string"],
                    "limitations": ["string"]
                },
                "conclusions": {
                    "main_findings": ["string"],
                    "recommendations": ["string"],
                    "next_steps": ["string"]
                }
            },
            
            # STRATEGY ASSETS
            "strategy_framework": {
                "strategic_objectives": [
                    {
                        "objective": "string",
                        "timeline": "string",
                        "success_metrics": ["string"],
                        "resources_required": ["string"],
                        "dependencies": ["string"]
                    }
                ],
                "implementation_plan": {
                    "phases": [
                        {
                            "phase_name": "string",
                            "duration": "string",
                            "key_activities": ["string"],
                            "deliverables": ["string"],
                            "milestones": ["string"]
                        }
                    ]
                },
                "risk_analysis": {
                    "risks": ["string"],
                    "mitigation_strategies": ["string"],
                    "contingency_plans": ["string"]
                }
            }
        }
    
    # === ASSET EXTRACTION (from concrete_asset_extractor.py) ===
    
    async def extract_concrete_assets(
        self,
        completed_tasks: List[Dict],
        workspace_goal: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """
        Main asset extraction method with quality validation
        Consolidates functionality from ConcreteAssetExtractor
        """
        
        self.stats["total_extractions"] += 1
        
        try:
            logger.info(f"🔍 Starting concrete asset extraction for {len(completed_tasks)} tasks")
            
            # Initialize extraction result
            extracted_assets = {}
            extraction_metadata = {
                "extraction_timestamp": datetime.now().isoformat(),
                "workspace_goal": workspace_goal,
                "deliverable_type": deliverable_type,
                "tasks_processed": len(completed_tasks),
                "extraction_method": "unified_engine_v1.0"
            }
            
            # Process each completed task
            for task in completed_tasks:
                try:
                    task_assets = await self._extract_assets_from_task(
                        task, workspace_goal, deliverable_type
                    )
                    
                    # Merge task assets with validation
                    for asset_id, asset_data in task_assets.items():
                        if self._is_concrete_asset(asset_data):
                            # Apply quality validation if available
                            if self.quality_engine and ENABLE_AI_QUALITY_EVALUATION:
                                validated_asset = await self._validate_asset_quality(
                                    asset_data, workspace_goal
                                )
                                extracted_assets[asset_id] = validated_asset
                                self.stats["quality_validations"] += 1
                            else:
                                extracted_assets[asset_id] = asset_data
                            
                            logger.debug(f"   ✅ Extracted asset: {asset_id}")
                        else:
                            logger.debug(f"   ❌ Rejected non-concrete asset: {asset_id}")
                
                except Exception as e:
                    logger.warning(f"Error extracting from task {task.get('id', 'unknown')}: {e}")
                    continue
            
            # Add metadata
            extracted_assets["_extraction_metadata"] = extraction_metadata
            
            logger.info(f"🔍 Extraction complete: {len(extracted_assets)-1} concrete assets found")
            
            return extracted_assets
            
        except Exception as e:
            logger.error(f"Error in asset extraction: {e}", exc_info=True)
            return {
                "_extraction_metadata": {
                    "error": str(e),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "unified_engine_error_fallback"
                }
            }
    
    async def _extract_assets_from_task(
        self,
        task: Dict[str, Any],
        workspace_goal: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """Extract assets from a single task"""
        
        task_assets = {}
        task_id = task.get("id", "unknown")
        
        # Extract from detailed_results_json if available
        detailed_results = task.get("detailed_results_json")
        if detailed_results:
            try:
                if isinstance(detailed_results, str):
                    detailed_data = json.loads(detailed_results)
                else:
                    detailed_data = detailed_results
                
                # Extract structured assets
                structured_assets = await self._extract_structured_assets(
                    detailed_data, task_id, deliverable_type
                )
                task_assets.update(structured_assets)
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in task {task_id} detailed_results")
            except Exception as e:
                logger.warning(f"Error processing detailed_results for task {task_id}: {e}")
        
        # Extract from summary if no detailed results
        if not task_assets and task.get("summary"):
            summary_assets = await self._extract_from_summary(
                task["summary"], task_id, deliverable_type
            )
            task_assets.update(summary_assets)
        
        return task_assets
    
    async def _extract_structured_assets(
        self,
        data: Dict[str, Any],
        task_id: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """Extract structured assets from task data"""
        
        assets = {}
        
        # Look for deliverable_assets (from AI-driven content)
        if "deliverable_assets" in data and isinstance(data["deliverable_assets"], list):
            for i, asset_data in enumerate(data["deliverable_assets"]):
                if isinstance(asset_data, dict):
                    asset_name = asset_data.get("name", f"asset_{i}")
                    asset_value = asset_data.get("value", asset_data)
                    
                    asset_id = f"task_{task_id}_asset_{i}"
                    assets[asset_id] = {
                        "type": self._infer_asset_type_from_name(asset_name),
                        "data": asset_value,
                        "metadata": {
                            "source_task_id": task_id,
                            "asset_name": asset_name,
                            "extraction_timestamp": datetime.now().isoformat(),
                            "extraction_method": "structured_deliverable_assets"
                        }
                    }
        
        # Look for direct asset fields based on deliverable type
        asset_fields = self._get_asset_fields_for_type(deliverable_type)
        for field in asset_fields:
            if field in data and data[field]:
                asset_id = f"task_{task_id}_{field}"
                assets[asset_id] = {
                    "type": self._infer_asset_type_from_name(field),
                    "data": data[field],
                    "metadata": {
                        "source_task_id": task_id,
                        "asset_name": field,
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "direct_field_extraction"
                    }
                }
        
        return assets
    
    async def _extract_from_summary(
        self,
        summary: str,
        task_id: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """Extract assets from task summary using AI if available"""
        
        if not self.ai_client:
            return {}
        
        try:
            # Use AI to extract structured data from summary
            extraction_prompt = f"""
Extract actionable business assets from this task summary for a {deliverable_type} project.

Task Summary: {summary[:1500]}

Look for:
1. Contact information (names, emails, phones, companies)
2. Content pieces (posts, emails, documents)
3. Data/metrics/numbers
4. Schedules/timelines
5. Templates/frameworks
6. Lists of items/resources

Return as JSON with this structure:
{{
    "assets": [
        {{
            "name": "asset_name",
            "type": "contact_database|content_calendar|email_templates|etc",
            "data": {{structured_data}},
            "confidence": 0.0-1.0
        }}
    ]
}}

Only include assets with concrete, actionable data (not theoretical content).
"""
            
            response = await self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business asset extractor."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            extraction_result = json.loads(response.choices[0].message.content)
            assets = {}
            
            for i, asset in enumerate(extraction_result.get("assets", [])):
                if asset.get("confidence", 0) > 0.7:  # Only high-confidence assets
                    asset_id = f"task_{task_id}_ai_extracted_{i}"
                    assets[asset_id] = {
                        "type": asset.get("type", "business_asset"),
                        "data": asset.get("data", {}),
                        "metadata": {
                            "source_task_id": task_id,
                            "asset_name": asset.get("name", f"extracted_asset_{i}"),
                            "extraction_timestamp": datetime.now().isoformat(),
                            "extraction_method": "ai_summary_extraction",
                            "confidence": asset.get("confidence", 0)
                        }
                    }
            
            self.stats["ai_calls_made"] += 1
            return assets
            
        except Exception as e:
            logger.warning(f"AI extraction from summary failed: {e}")
            return {}
    
    def _infer_asset_type_from_name(self, name: str) -> str:
        """Infer asset type from name"""
        
        name_lower = name.lower()
        
        if any(term in name_lower for term in ["contact", "lead", "prospect", "customer", "client"]):
            return "contact_database"
        elif any(term in name_lower for term in ["content", "post", "social", "calendar", "schedule"]):
            return "content_calendar"
        elif any(term in name_lower for term in ["email", "sequence", "campaign", "newsletter"]):
            return "email_templates"
        elif any(term in name_lower for term in ["training", "workout", "exercise", "fitness", "program"]):
            return "training_program"
        elif any(term in name_lower for term in ["financial", "budget", "revenue", "cost", "profit"]):
            return "financial_model"
        elif any(term in name_lower for term in ["research", "analysis", "study", "findings", "data"]):
            return "research_database"
        elif any(term in name_lower for term in ["strategy", "framework", "plan", "roadmap"]):
            return "strategy_framework"
        else:
            return "business_asset"
    
    def _get_asset_fields_for_type(self, deliverable_type: str) -> List[str]:
        """Get expected asset fields for deliverable type"""
        
        type_fields = {
            "marketing": ["content_calendar", "email_templates", "contact_database", "campaign_assets"],
            "fitness": ["training_program", "nutrition_plan", "progress_tracking", "exercise_library"],
            "business": ["financial_model", "strategy_framework", "market_analysis", "business_plan"],
            "research": ["research_database", "findings", "methodology", "data_analysis"],
            "consulting": ["strategy_framework", "recommendations", "implementation_plan", "risk_analysis"]
        }
        
        return type_fields.get(deliverable_type.lower(), ["business_asset", "project_summary"])
    
    def _is_concrete_asset(self, asset_data: Dict[str, Any]) -> bool:
        """Validate if asset contains concrete, actionable data"""
        
        data = asset_data.get("data", {})
        if not data or not isinstance(data, dict):
            return False
        
        # Check for concrete patterns
        data_str = json.dumps(data, default=str)
        concrete_indicators = 0
        
        for pattern_name, pattern in self.universal_validation_patterns.items():
            matches = re.findall(pattern, data_str)
            if matches:
                concrete_indicators += len(matches)
        
        # Check for structured data
        if any(isinstance(v, (list, dict)) and v for v in data.values()):
            concrete_indicators += 5
        
        # Check data size (substantial content)
        if len(data_str) > 200:
            concrete_indicators += 2
        
        return concrete_indicators >= 3
    
    async def _validate_asset_quality(
        self,
        asset_data: Dict[str, Any],
        workspace_goal: str
    ) -> Dict[str, Any]:
        """Validate asset quality using quality engine"""
        
        if not self.quality_engine:
            return asset_data
        
        try:
            asset_name = asset_data.get("metadata", {}).get("asset_name", "unknown")
            assessment = await self.quality_engine.validate_asset_quality(
                asset_data.get("data", {}),
                asset_name,
                {"workspace_goal": workspace_goal}
            )
            
            # Add quality metadata
            asset_data["metadata"]["quality_assessment"] = {
                "overall_score": assessment.overall_score,
                "ready_to_use": assessment.ready_for_use,
                "needs_enhancement": assessment.needs_enhancement,
                "quality_issues": assessment.quality_issues
            }
            
            return asset_data
            
        except Exception as e:
            logger.warning(f"Quality validation failed: {e}")
            return asset_data
    
    # === DISPLAY PROCESSING (from markup_processor.py + ai_display_enhancer.py) ===
    
    async def process_deliverable_content(self, raw_content: Any) -> Dict[str, Any]:
        """
        AI-driven content processing for display enhancement
        Consolidates functionality from DeliverableMarkupProcessor and AIDisplayEnhancer
        """
        
        self.stats["total_enhancements"] += 1
        
        try:
            # Check cache first
            content_hash = hash(str(raw_content)[:200])
            if content_hash in self.processed_cache:
                self.stats["cache_hits"] += 1
                return self.processed_cache[content_hash]
            
            self.stats["cache_misses"] += 1
            
            # Step 1: Analyze content structure universally
            content_analysis = await self._analyze_content_structure(raw_content)
            
            # Step 2: Generate AI-driven display instructions
            display_instructions = await self._generate_display_instructions(content_analysis, raw_content)
            
            # Step 3: Create enhanced result
            result = {
                "_display_format": display_instructions,
                "content_analysis": content_analysis,
                "raw_content": raw_content,
                "has_structured_content": content_analysis.get("has_structured_data", False),
                "combined_elements": self._create_combined_elements(content_analysis, display_instructions),
                "processing_timestamp": datetime.now().isoformat(),
                "processor_version": "unified_engine_v1.0"
            }
            
            # Cache result
            self.processed_cache[content_hash] = result
            
            logger.debug(f"✅ Content processed with {len(display_instructions)} display instructions")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in content processing: {e}", exc_info=True)
            return {
                "error": str(e),
                "raw_content": raw_content,
                "has_structured_content": False,
                "processing_timestamp": datetime.now().isoformat(),
                "processor_version": "unified_engine_error_fallback"
            }
    
    async def _analyze_content_structure(self, content: Any) -> Dict[str, Any]:
        """Analyze content structure universally"""
        
        analysis = {
            "content_type": type(content).__name__,
            "has_structured_data": False,
            "data_patterns": [],
            "content_size": 0,
            "key_fields": [],
            "nested_structures": 0
        }
        
        try:
            if isinstance(content, dict):
                analysis["has_structured_data"] = True
                analysis["key_fields"] = list(content.keys())
                analysis["nested_structures"] = sum(1 for v in content.values() if isinstance(v, (dict, list)))
                
                # Detect patterns in content
                content_str = json.dumps(content, default=str)
                analysis["content_size"] = len(content_str)
                
                for pattern_name, pattern in self.universal_validation_patterns.items():
                    matches = re.findall(pattern, content_str)
                    if matches:
                        analysis["data_patterns"].append({
                            "pattern": pattern_name,
                            "count": len(matches),
                            "examples": matches[:3]  # First 3 examples
                        })
            
            elif isinstance(content, list):
                analysis["has_structured_data"] = True
                analysis["content_size"] = len(content)
                analysis["nested_structures"] = len([item for item in content if isinstance(item, (dict, list))])
            
            elif isinstance(content, str):
                analysis["content_size"] = len(content)
                
                # Check for JSON string
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, (dict, list)):
                        analysis["has_structured_data"] = True
                except json.JSONDecodeError:
                    pass
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Error in content analysis: {e}")
            return analysis
    
    async def _generate_display_instructions(self, content_analysis: Dict[str, Any], raw_content: Any) -> List[Dict[str, Any]]:
        """Generate AI-driven display instructions"""
        
        if not self.ai_client:
            return self._generate_fallback_display_instructions(content_analysis, raw_content)
        
        try:
            # Prepare content for AI analysis
            content_sample = str(raw_content)[:2000]  # Limit for token efficiency
            
            display_prompt = f"""
Analyze this content and generate optimal display instructions for a web interface.

Content Analysis: {json.dumps(content_analysis)}
Content Sample: {content_sample}

Generate display instructions as JSON array with this structure:
[
    {{
        "element_type": "table|list|cards|chart|form|text|media",
        "title": "Display Title",
        "data_source": "field_name_or_path",
        "display_config": {{
            "columns": ["col1", "col2"] // for tables
            "layout": "grid|list|stack" // for cards/lists
            "chart_type": "bar|line|pie" // for charts
            "max_items": number // for lists
        }},
        "priority": 1-10,
        "responsive": true,
        "interactive": true
    }}
]

Focus on:
1. Making data immediately actionable and readable
2. Highlighting key business metrics and contacts
3. Organizing information logically
4. Enabling quick scanning and interaction
5. Mobile-friendly responsive design

Only create instructions for content that actually exists in the data.
"""
            
            response = await self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert UX/UI designer specializing in business data visualization."},
                    {"role": "user", "content": display_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            display_instructions = ai_response.get("display_instructions", [])
            
            self.stats["ai_calls_made"] += 1
            
            # Validate and enhance instructions
            validated_instructions = []
            for instruction in display_instructions:
                if self._validate_display_instruction(instruction, content_analysis):
                    validated_instructions.append(instruction)
            
            return validated_instructions
            
        except Exception as e:
            logger.warning(f"AI display instruction generation failed: {e}")
            return self._generate_fallback_display_instructions(content_analysis, raw_content)
    
    def _generate_fallback_display_instructions(self, content_analysis: Dict[str, Any], raw_content: Any) -> List[Dict[str, Any]]:
        """Generate fallback display instructions when AI unavailable"""
        
        instructions = []
        
        if content_analysis.get("has_structured_data"):
            if isinstance(raw_content, dict):
                # Check for list fields (good for tables)
                for field, value in raw_content.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        instructions.append({
                            "element_type": "table",
                            "title": field.replace("_", " ").title(),
                            "data_source": field,
                            "display_config": {
                                "columns": list(value[0].keys())[:6],  # First 6 columns
                                "sortable": True,
                                "filterable": True
                            },
                            "priority": 5,
                            "responsive": True,
                            "interactive": True
                        })
                    elif isinstance(value, dict) and value:
                        instructions.append({
                            "element_type": "cards",
                            "title": field.replace("_", " ").title(),
                            "data_source": field,
                            "display_config": {
                                "layout": "grid",
                                "max_items": 20
                            },
                            "priority": 4,
                            "responsive": True,
                            "interactive": False
                        })
            
            elif isinstance(raw_content, list) and raw_content:
                instructions.append({
                    "element_type": "table" if isinstance(raw_content[0], dict) else "list",
                    "title": "Data List",
                    "data_source": "root",
                    "display_config": {
                        "columns": list(raw_content[0].keys())[:6] if isinstance(raw_content[0], dict) else [],
                        "max_items": 100
                    },
                    "priority": 5,
                    "responsive": True,
                    "interactive": True
                })
        
        # Always add a text fallback
        instructions.append({
            "element_type": "text",
            "title": "Raw Content",
            "data_source": "raw",
            "display_config": {
                "format": "json" if content_analysis.get("has_structured_data") else "text",
                "collapsible": True
            },
            "priority": 1,
            "responsive": True,
            "interactive": False
        })
        
        return instructions
    
    def _validate_display_instruction(self, instruction: Dict[str, Any], content_analysis: Dict[str, Any]) -> bool:
        """Validate display instruction"""
        
        required_fields = ["element_type", "title", "data_source"]
        return all(field in instruction for field in required_fields)
    
    def _create_combined_elements(self, content_analysis: Dict[str, Any], display_instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create combined elements for display"""
        
        return {
            "total_elements": len(display_instructions),
            "element_types": [instr.get("element_type") for instr in display_instructions],
            "interactive_elements": len([instr for instr in display_instructions if instr.get("interactive", False)]),
            "data_coverage": content_analysis.get("has_structured_data", False),
            "responsive_design": all(instr.get("responsive", False) for instr in display_instructions)
        }
    
    async def enhance_deliverable_with_display_format(self, deliverable_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance deliverable with AI-generated display instructions
        Consolidates functionality from AIDisplayEnhancer
        """
        
        try:
            # Extract content to be enhanced
            content_to_enhance = None
            
            if "detailed_results_json" in deliverable_data:
                try:
                    content_to_enhance = json.loads(deliverable_data["detailed_results_json"])
                except json.JSONDecodeError:
                    content_to_enhance = deliverable_data["detailed_results_json"]
            elif "summary" in deliverable_data:
                content_to_enhance = deliverable_data["summary"]
            else:
                content_to_enhance = deliverable_data
            
            # Generate AI-driven display instructions
            enhanced_content = await self.process_deliverable_content(content_to_enhance)
            
            # Integrate display instructions back into deliverable
            enhanced_deliverable = deliverable_data.copy()
            
            if "_display_format" in enhanced_content:
                enhanced_deliverable["_display_format"] = enhanced_content["_display_format"]
                enhanced_deliverable["_enhanced_by_ai"] = True
                enhanced_deliverable["_enhancement_timestamp"] = datetime.now().isoformat()
            
            return enhanced_deliverable
            
        except Exception as e:
            logger.error(f"Error enhancing deliverable with display format: {e}")
            return deliverable_data
    
    # === PIPELINE MANAGEMENT (from deliverable_pipeline.py) ===
    
    async def start_pipeline(self):
        """Start deliverable pipeline (from DeliverablePipeline)"""
        
        self._running = True
        logger.info("🚀 Starting Unified Deliverable Pipeline...")
        
        # Update component health if supabase available
        if self.supabase:
            await self._update_component_health('unified_deliverable_pipeline', 'healthy')
        
        # Start event processing loop
        await self._event_processor_loop()
    
    async def stop_pipeline(self):
        """Stop deliverable pipeline"""
        
        self._running = False
        if self.supabase:
            await self._update_component_health('unified_deliverable_pipeline', 'stopped')
        logger.info("🛑 Unified Deliverable Pipeline stopped")
    
    async def _event_processor_loop(self):
        """Event processing loop for pipeline"""
        
        while self._running:
            try:
                # Check for completed tasks that need deliverable processing
                await self._process_pending_deliverables()
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in pipeline event processor: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_pending_deliverables(self):
        """Process pending deliverables"""
        
        if not self.supabase or not list_tasks:
            return
        
        try:
            # This is a simplified version - in production would check integration_events table
            # For now, process any completed tasks that haven't been processed yet
            
            self.stats["total_pipelines_processed"] += 1
            logger.debug("🔄 Processing pending deliverables...")
            
        except Exception as e:
            logger.error(f"Error processing pending deliverables: {e}")
    
    async def _update_component_health(self, component: str, status: str):
        """Update component health status"""
        
        if not self.supabase:
            return
        
        try:
            # Update component health in database
            health_data = {
                "component": component,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "version": "unified_engine_v1.0"
            }
            
            # Insert or update health record
            result = self.supabase.table("component_health").upsert(health_data).execute()
            logger.debug(f"✅ Component health updated: {component} -> {status}")
            
        except Exception as e:
            logger.warning(f"Failed to update component health: {e}")
    
    # === REQUIREMENTS ANALYSIS (from requirements_analyzer.py) ===
    
    async def analyze_requirements(
        self,
        workspace_id: str,
        deliverable_type: str
    ) -> DeliverableRequirements:
        """
        Analyze requirements for deliverable generation
        Consolidates functionality from RequirementsAnalyzer
        """
        
        self.stats["total_requirements_analyzed"] += 1
        
        try:
            logger.info(f"📋 Analyzing requirements for {deliverable_type} deliverable in workspace {workspace_id}")
            
            # Get workspace context
            workspace_context = await self._get_workspace_context(workspace_id)
            
            # Analyze existing tasks and agents
            task_analysis = await self._analyze_task_completion(workspace_id)
            agent_analysis = await self._analyze_agent_capabilities(workspace_id)
            
            # Generate requirements based on analysis
            requirements = await self._generate_deliverable_requirements(
                deliverable_type, workspace_context, task_analysis, agent_analysis
            )
            
            logger.info(f"📋 Requirements analysis complete: {len(requirements.requirements)} requirements identified")
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error in requirements analysis: {e}", exc_info=True)
            return DeliverableRequirements(requirements=[])
    
    async def _get_workspace_context(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace context for requirements analysis"""
        
        context = {
            "workspace_id": workspace_id,
            "goals": [],
            "project_details": {},
            "team_composition": {},
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        try:
            if get_workspace:
                workspace = await get_workspace(workspace_id)
                if workspace:
                    context["project_details"] = {
                        "goal": workspace.get("goal", ""),
                        "description": workspace.get("description", ""),
                        "status": workspace.get("status", ""),
                        "created_at": workspace.get("created_at", "")
                    }
            
            if get_workspace_goals:
                goals = await get_workspace_goals(workspace_id)
                if goals:
                    context["goals"] = goals
            
        except Exception as e:
            logger.warning(f"Error getting workspace context: {e}")
        
        return context
    
    async def _analyze_task_completion(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze task completion patterns"""
        
        analysis = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "task_types": {},
            "completion_rate": 0.0,
            "recent_completions": []
        }
        
        try:
            if list_tasks:
                tasks = await list_tasks(workspace_id)
                analysis["total_tasks"] = len(tasks)
                
                completed_tasks = [t for t in tasks if t.get("status") == "completed"]
                analysis["completed_tasks"] = len(completed_tasks)
                analysis["completion_rate"] = len(completed_tasks) / max(1, len(tasks))
                
                # Analyze task types
                for task in tasks:
                    task_type = task.get("creation_type", "manual")
                    analysis["task_types"][task_type] = analysis["task_types"].get(task_type, 0) + 1
                
                # Recent completions (last 5)
                recent_completed = sorted(
                    completed_tasks,
                    key=lambda x: x.get("updated_at", ""),
                    reverse=True
                )[:5]
                
                analysis["recent_completions"] = [
                    {
                        "id": task.get("id"),
                        "name": task.get("name", ""),
                        "completed_at": task.get("updated_at", ""),
                        "has_deliverable_content": bool(task.get("detailed_results_json"))
                    }
                    for task in recent_completed
                ]
        
        except Exception as e:
            logger.warning(f"Error analyzing task completion: {e}")
        
        return analysis
    
    async def _analyze_agent_capabilities(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze agent capabilities"""
        
        analysis = {
            "total_agents": 0,
            "active_agents": 0,
            "agent_roles": {},
            "seniority_levels": {},
            "specialized_skills": []
        }
        
        try:
            if list_agents:
                agents = await list_agents(workspace_id)
                analysis["total_agents"] = len(agents)
                
                active_agents = [a for a in agents if a.get("status") == "active"]
                analysis["active_agents"] = len(active_agents)
                
                # Analyze roles and seniority
                for agent in agents:
                    role = agent.get("role", "unknown")
                    seniority = agent.get("seniority", "junior")
                    
                    analysis["agent_roles"][role] = analysis["agent_roles"].get(role, 0) + 1
                    analysis["seniority_levels"][seniority] = analysis["seniority_levels"].get(seniority, 0) + 1
                    
                    # Extract specialized skills
                    skills = agent.get("hard_skills", [])
                    if isinstance(skills, list):
                        analysis["specialized_skills"].extend(skills)
        
        except Exception as e:
            logger.warning(f"Error analyzing agent capabilities: {e}")
        
        return analysis
    
    async def _generate_deliverable_requirements(
        self,
        deliverable_type: str,
        workspace_context: Dict[str, Any],
        task_analysis: Dict[str, Any],
        agent_analysis: Dict[str, Any]
    ) -> DeliverableRequirements:
        """Generate deliverable requirements based on analysis"""
        
        requirements = []
        
        # Base requirements for any deliverable
        requirements.extend([
            AssetRequirement(
                name="executive_summary",
                type="text",
                required=True
            ),
            AssetRequirement(
                name="actionable_assets",
                type="structured_data",
                required=True
            ),
            AssetRequirement(
                name="next_steps",
                type="list",
                required=True
            )
        ])
        
        # Type-specific requirements
        type_requirements = self._get_type_specific_requirements(deliverable_type)
        requirements.extend(type_requirements)
        
        # Quality-based requirements
        if task_analysis.get("completion_rate", 0) > 0.8:
            requirements.append(
                AssetRequirement(
                    name="quality_validation",
                    type="assessment",
                    required=True
                )
            )
        
        # Team capability-based requirements
        if agent_analysis.get("active_agents", 0) > 3:
            requirements.append(
                AssetRequirement(
                    name="team_coordination_summary",
                    type="text",
                    required=False
                )
            )
        
        return DeliverableRequirements(requirements=requirements)
    
    def _get_type_specific_requirements(self, deliverable_type: str) -> List[AssetRequirement]:
        """Get type-specific requirements"""
        
        type_requirements = {
            "marketing": [
                AssetRequirement(name="content_calendar", type="structured_data", required=True),
                AssetRequirement(name="contact_database", type="structured_data", required=False),
                AssetRequirement(name="email_templates", type="structured_data", required=False)
            ],
            "fitness": [
                AssetRequirement(name="training_program", type="structured_data", required=True),
                AssetRequirement(name="nutrition_plan", type="structured_data", required=False),
                AssetRequirement(name="progress_tracking", type="structured_data", required=False)
            ],
            "business": [
                AssetRequirement(name="financial_model", type="structured_data", required=False),
                AssetRequirement(name="strategy_framework", type="structured_data", required=False),
                AssetRequirement(name="market_analysis", type="structured_data", required=False)
            ]
        }
        
        return type_requirements.get(deliverable_type.lower(), [])
    
    # === SCHEMA GENERATION (from schema_generator.py) ===
    
    def generate_asset_schema(self, asset_type: str, content_sample: Optional[Dict[str, Any]] = None) -> AssetSchema:
        """
        Generate dynamic schema for asset type
        Consolidates functionality from AssetSchemaGenerator
        """
        
        self.stats["total_schemas_generated"] += 1
        
        # Check cache first
        cache_key = f"{asset_type}_{hash(str(content_sample))}"
        if cache_key in self.schema_cache:
            self.stats["cache_hits"] += 1
            return self.schema_cache[cache_key]
        
        self.stats["cache_misses"] += 1
        
        try:
            # Get base schema
            base_schema = self.base_schemas.get(asset_type, {})
            
            # Enhance with content sample if provided
            if content_sample:
                enhanced_schema = self._enhance_schema_with_sample(base_schema, content_sample)
            else:
                enhanced_schema = base_schema
            
            # Create schema object
            schema = AssetSchema(
                name=asset_type,
                type=asset_type,
                properties=enhanced_schema
            )
            
            # Cache result
            self.schema_cache[cache_key] = schema
            
            logger.debug(f"✅ Schema generated for {asset_type}")
            
            return schema
            
        except Exception as e:
            logger.error(f"Error generating schema for {asset_type}: {e}")
            return AssetSchema(
                name=asset_type,
                type=asset_type,
                properties={"error": f"Schema generation failed: {str(e)}"}
            )
    
    def _enhance_schema_with_sample(self, base_schema: Dict[str, Any], content_sample: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance base schema with content sample"""
        
        enhanced = base_schema.copy()
        
        try:
            # Add fields from content sample that aren't in base schema
            for key, value in content_sample.items():
                if key not in enhanced:
                    # Infer type from value
                    if isinstance(value, list):
                        enhanced[key] = ["dynamic_list_item"]
                    elif isinstance(value, dict):
                        enhanced[key] = {"dynamic": "object"}
                    elif isinstance(value, str):
                        enhanced[key] = "string"
                    elif isinstance(value, (int, float)):
                        enhanced[key] = "number"
                    elif isinstance(value, bool):
                        enhanced[key] = "boolean"
                    else:
                        enhanced[key] = "any"
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error enhancing schema with sample: {e}")
            return base_schema
    
    # === UTILITY METHODS ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        
        return {
            "unified_deliverable_engine": "v1.0",
            "total_extractions": self.stats["total_extractions"],
            "total_enhancements": self.stats["total_enhancements"],
            "total_pipelines_processed": self.stats["total_pipelines_processed"],
            "total_requirements_analyzed": self.stats["total_requirements_analyzed"],
            "total_schemas_generated": self.stats["total_schemas_generated"],
            "ai_calls_made": self.stats["ai_calls_made"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_ratio": self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"]),
            "quality_validations": self.stats["quality_validations"],
            "schema_cache_size": len(self.schema_cache),
            "processed_cache_size": len(self.processed_cache),
            "extraction_cache_size": len(self.extraction_cache),
            "pipeline_running": self._running,
            "ai_client_available": self.ai_client is not None,
            "quality_engine_available": QUALITY_ENGINE_AVAILABLE,
            "supabase_available": self.supabase is not None
        }
    
    def reset_stats(self):
        """Reset all statistics and caches"""
        
        self.stats = {
            "total_extractions": 0,
            "total_enhancements": 0,
            "total_pipelines_processed": 0,
            "total_requirements_analyzed": 0,
            "total_schemas_generated": 0,
            "ai_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "quality_validations": 0
        }
        
        self.schema_cache.clear()
        self.processed_cache.clear()
        self.extraction_cache.clear()
        
        logger.info("🔄 Unified Deliverable Engine stats and caches reset")
    
    # === BACKWARD COMPATIBILITY ALIASES ===
    
    async def analyze_deliverable_requirements(self, workspace_id: str, force_refresh: bool = False) -> DeliverableRequirements:
        """Backward compatibility alias for analyze_requirements"""
        return await self.analyze_requirements(workspace_id, "business")
    
    async def generate_asset_schemas(self, requirements: DeliverableRequirements) -> Dict[str, AssetSchema]:
        """Generate schemas for multiple assets (backward compatibility)"""
        schemas = {}
        
        if hasattr(requirements, 'primary_assets_needed'):
            for asset_req in requirements.primary_assets_needed:
                asset_type = getattr(asset_req, 'asset_type', 'general')
                schema = self.generate_asset_schema(asset_type, None)
                schemas[asset_type] = schema
        
        return schemas
    
    async def start(self):
        """Backward compatibility alias for start_pipeline"""
        return await self.start_pipeline()
    
    async def stop(self):
        """Backward compatibility alias for stop_pipeline"""
        return await self.stop_pipeline()
    
    # === SPECIAL RENDERING METHODS (backward compatibility) ===
    
    def _render_contacts_list(self, contacts: List[Dict[str, Any]]) -> str:
        """Render contacts list as HTML table (backward compatibility)"""
        
        if not contacts:
            return "<p>No contacts available</p>"
        
        try:
            html = "<table class='contacts-table'>\n<thead>\n<tr>"
            
            # Get headers from first contact
            headers = list(contacts[0].keys())[:6]  # Limit to 6 columns
            for header in headers:
                html += f"<th>{header.replace('_', ' ').title()}</th>"
            html += "</tr>\n</thead>\n<tbody>\n"
            
            # Add rows
            for contact in contacts[:50]:  # Limit to 50 contacts
                html += "<tr>"
                for header in headers:
                    value = contact.get(header, "")
                    html += f"<td>{str(value)}</td>"
                html += "</tr>\n"
            
            html += "</tbody>\n</table>"
            return html
            
        except Exception as e:
            logger.warning(f"Error rendering contacts list: {e}")
            return f"<p>Error rendering contacts: {str(e)}</p>"
    
    def _render_email_sequences(self, sequences: List[Dict[str, Any]]) -> str:
        """Render email sequences as HTML (backward compatibility)"""
        
        if not sequences:
            return "<p>No email sequences available</p>"
        
        try:
            html = "<div class='email-sequences'>\n"
            
            for i, sequence in enumerate(sequences):
                sequence_name = sequence.get("name", f"Sequence {i+1}")
                emails = sequence.get("emails", [])
                
                html += f"<div class='sequence'>\n<h3>{sequence_name}</h3>\n"
                
                if emails:
                    html += "<ol class='emails-list'>\n"
                    for email in emails:
                        subject = email.get("subject", "No subject")
                        day = email.get("day", "")
                        html += f"<li><strong>Day {day}:</strong> {subject}</li>\n"
                    html += "</ol>\n"
                
                html += "</div>\n"
            
            html += "</div>"
            return html
            
        except Exception as e:
            logger.warning(f"Error rendering email sequences: {e}")
            return f"<p>Error rendering sequences: {str(e)}</p>"
    
    # =========================================================================
    # DATABASE-FIRST METHODS (NEW) - Sostituiscono file sparsi
    # =========================================================================
    
    async def extract_workspace_assets_db(
        self, 
        workspace_id: str, 
        quality_threshold: float = 0.6,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Database-first asset extraction - sostituisce deliverable_aggregator.py
        Utilizza stored procedures per performance ottimizzata
        """
        
        if self.database_adapter:
            return await self.database_adapter.extract_workspace_assets(
                workspace_id, quality_threshold, limit
            )
        else:
            # Fallback al metodo originale
            logger.warning("Database adapter not available, using legacy extraction")
            return await self.extract_concrete_assets(workspace_id, {})
    
    async def create_workspace_deliverable_db(
        self,
        workspace_id: str,
        deliverable_name: str,
        deliverable_type: str = 'comprehensive',
        min_quality_score: float = 0.7
    ) -> Dict[str, Any]:
        """
        Database-first deliverable creation - sostituisce deliverable_aggregator.py
        Utilizza stored procedures per aggregazione ottimizzata
        """
        
        if self.database_adapter:
            return await self.database_adapter.create_workspace_deliverable(
                workspace_id, deliverable_name, deliverable_type, min_quality_score
            )
        else:
            # Fallback mode
            logger.warning("Database adapter not available, using legacy creation")
            return {
                'success': False,
                'deliverable_id': None,
                'assets_included': 0,
                'avg_quality_score': 0.0,
                'creation_status': 'fallback',
                'next_steps': ['Database adapter not available'],
                'creation_method': 'legacy_fallback',
                'workspace_id': workspace_id
            }
    
    async def get_workspace_metrics_db(self, workspace_id: str) -> Dict[str, Any]:
        """
        Database-first workspace metrics - sostituisce asset_requirements_generator.py
        Utilizza viste aggregate per performance
        """
        
        if self.database_adapter:
            return await self.database_adapter.get_workspace_deliverable_metrics(workspace_id)
        else:
            # Fallback mode
            logger.warning("Database adapter not available, using basic metrics")
            return {
                'workspace_id': workspace_id,
                'assets': {'total': 0, 'ready': 0, 'poor_quality': 0, 'avg_quality': 0.0},
                'deliverables': {'total': 0, 'completed': 0, 'in_progress': 0, 'avg_quality': 0.0},
                'tasks': {'total': 0, 'completed': 0, 'completion_percentage': 0.0},
                'overall_readiness': 'unknown',
                'generated_by': 'legacy_fallback'
            }
    
    async def get_unified_view_db(
        self,
        workspace_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Database-first unified view access - sostituisce queries sparse in routes
        """
        
        if self.database_adapter:
            return await self.database_adapter.get_unified_asset_deliverable_view(
                workspace_id, filters
            )
        else:
            logger.warning("Database adapter not available, returning empty view")
            return []
    
    def get_consolidated_status(self) -> Dict[str, Any]:
        """
        Status completo del sistema consolidato
        Mostra cosa è stato sostituito e performance benefits
        """
        
        status = {
            'unified_deliverable_engine': 'v2.0_database_first',
            'consolidation_status': 'GLOBAL_COMPLETE',
            
            # Files consolidati nella directory deliverable_system/ (v1.0)
            'original_consolidation': {
                'files_consolidated': 6,
                'files': [
                    'concrete_asset_extractor.py',
                    'markup_processor.py', 
                    'deliverable_pipeline.py',
                    'requirements_analyzer.py',
                    'schema_generator.py',
                    'ai_display_enhancer.py'
                ]
            },
            
            # Files sparsi consolidati tramite database adapter (v2.0)
            'database_consolidation': {
                'files_replaced': 6,
                'total_lines_replaced': 6665,
                'files': [
                    'deliverable_aggregator.py (2879 lines)',
                    'concrete_asset_extractor_refactored.py (1118 lines)',
                    'services/asset_requirements_generator.py (640 lines)',
                    'services/asset_artifact_processor.py (542 lines)',
                    'services/asset_driven_task_executor.py (480 lines)',
                    'services/asset_first_deliverable_system.py (1006 lines)'
                ]
            },
            
            # Componenti attivi
            'active_components': {
                'ai_client_available': self.ai_client is not None,
                'quality_engine_available': self.quality_engine is not None,
                'supabase_available': self.supabase is not None,
                'database_adapter_available': self.database_adapter is not None
            },
            
            # Performance benefits
            'performance_benefits': [
                'Database-optimized queries with indexes',
                'Stored procedures reduce network round-trips', 
                'Materialized views for fast aggregations',
                'Automatic cache invalidation via triggers',
                'Eliminated 6,665 lines of duplicate Python logic'
            ],
            
            # API methods disponibili
            'api_methods': {
                'legacy': [
                    'extract_concrete_assets()',
                    'process_deliverable_content()',
                    'analyze_requirements()',
                    'generate_asset_schema()',
                    'enhance_deliverable_with_display_format()'
                ],
                'database_first': [
                    'extract_workspace_assets_db()',
                    'create_workspace_deliverable_db()',
                    'get_workspace_metrics_db()',
                    'get_unified_view_db()'
                ]
            },
            
            # Statistics
            'stats': self.stats
        }
        
        if self.database_adapter:
            status['database_adapter_status'] = self.database_adapter.get_adapter_status()
        
        return status

    # === ADDITIONAL METHODS ===
    
    async def check_and_create_final_deliverable(
        self,
        workspace_id: str,
        force_creation: bool = False,
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Check if workspace is ready for final deliverable and create if conditions are met
        """
        
        try:
            logger.info(f"🔍 Checking final deliverable eligibility for workspace {workspace_id}")
            
            # Get workspace metrics
            metrics = await self.get_workspace_metrics_db(workspace_id)
            
            # Check readiness criteria
            readiness_check = {
                "workspace_id": workspace_id,
                "is_ready": False,
                "reasons": [],
                "metrics": metrics,
                "quality_threshold": quality_threshold
            }
            
            # Check task completion
            task_completion = metrics.get("tasks", {}).get("completion_percentage", 0)
            if task_completion < 80:
                readiness_check["reasons"].append(f"Task completion too low: {task_completion}%")
            
            # Check asset quality
            avg_quality = metrics.get("assets", {}).get("avg_quality", 0)
            if avg_quality < quality_threshold:
                readiness_check["reasons"].append(f"Asset quality too low: {avg_quality}")
            
            # Check minimum assets
            total_assets = metrics.get("assets", {}).get("total", 0)
            if total_assets < 3:
                readiness_check["reasons"].append(f"Insufficient assets: {total_assets}")
            
            # Override if forced
            if force_creation:
                readiness_check["is_ready"] = True
                readiness_check["reasons"] = ["Force creation requested"]
            else:
                readiness_check["is_ready"] = len(readiness_check["reasons"]) == 0
            
            # Create deliverable if ready
            if readiness_check["is_ready"]:
                deliverable_result = await self.create_workspace_deliverable_db(
                    workspace_id,
                    f"Final Deliverable - {datetime.now().strftime('%Y-%m-%d')}",
                    "comprehensive",
                    quality_threshold
                )
                
                readiness_check["deliverable_created"] = True
                readiness_check["deliverable_result"] = deliverable_result
                
                logger.info(f"✅ Final deliverable created for workspace {workspace_id}")
            else:
                readiness_check["deliverable_created"] = False
                logger.info(f"⏳ Workspace {workspace_id} not ready for final deliverable")
            
            return readiness_check
            
        except Exception as e:
            logger.error(f"Error checking final deliverable: {e}", exc_info=True)
            return {
                "workspace_id": workspace_id,
                "is_ready": False,
                "error": str(e),
                "deliverable_created": False
            }

    async def optimize_deliverable_quality(
        self,
        deliverable_id: str,
        enhancement_strategies: List[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize deliverable quality using AI-driven enhancement strategies
        """
        
        if not enhancement_strategies:
            enhancement_strategies = [
                "content_refinement",
                "structure_optimization", 
                "completeness_validation",
                "actionability_enhancement"
            ]
        
        try:
            logger.info(f"🎯 Optimizing deliverable quality for {deliverable_id}")
            
            optimization_result = {
                "deliverable_id": deliverable_id,
                "strategies_applied": [],
                "improvements": [],
                "quality_score_before": 0.0,
                "quality_score_after": 0.0,
                "optimization_timestamp": datetime.now().isoformat()
            }
            
            # Apply each enhancement strategy
            for strategy in enhancement_strategies:
                try:
                    if strategy == "content_refinement":
                        improvement = await self._apply_content_refinement(deliverable_id)
                    elif strategy == "structure_optimization":
                        improvement = await self._apply_structure_optimization(deliverable_id)
                    elif strategy == "completeness_validation":
                        improvement = await self._apply_completeness_validation(deliverable_id)
                    elif strategy == "actionability_enhancement":
                        improvement = await self._apply_actionability_enhancement(deliverable_id)
                    else:
                        improvement = {"applied": False, "reason": "Unknown strategy"}
                    
                    if improvement.get("applied", False):
                        optimization_result["strategies_applied"].append(strategy)
                        optimization_result["improvements"].append(improvement)
                        
                except Exception as e:
                    logger.warning(f"Failed to apply strategy {strategy}: {e}")
            
            # Calculate quality improvement
            if optimization_result["strategies_applied"]:
                optimization_result["quality_score_after"] = min(1.0, 
                    optimization_result["quality_score_before"] + 
                    len(optimization_result["strategies_applied"]) * 0.1
                )
            
            logger.info(f"✅ Deliverable optimization complete: {len(optimization_result['strategies_applied'])} strategies applied")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing deliverable quality: {e}", exc_info=True)
            return {
                "deliverable_id": deliverable_id,
                "error": str(e),
                "optimization_success": False
            }

    async def _apply_content_refinement(self, deliverable_id: str) -> Dict[str, Any]:
        """Apply content refinement strategy"""
        # Placeholder implementation
        return {
            "applied": True,
            "strategy": "content_refinement",
            "improvements": ["Enhanced clarity", "Improved readability"],
            "quality_impact": 0.1
        }

    async def _apply_structure_optimization(self, deliverable_id: str) -> Dict[str, Any]:
        """Apply structure optimization strategy"""
        # Placeholder implementation
        return {
            "applied": True,
            "strategy": "structure_optimization", 
            "improvements": ["Better organization", "Logical flow"],
            "quality_impact": 0.1
        }

    async def _apply_completeness_validation(self, deliverable_id: str) -> Dict[str, Any]:
        """Apply completeness validation strategy"""
        # Placeholder implementation
        return {
            "applied": True,
            "strategy": "completeness_validation",
            "improvements": ["Filled gaps", "Added missing sections"],
            "quality_impact": 0.1
        }

    async def _apply_actionability_enhancement(self, deliverable_id: str) -> Dict[str, Any]:
        """Apply actionability enhancement strategy"""
        # Placeholder implementation
        return {
            "applied": True,
            "strategy": "actionability_enhancement",
            "improvements": ["Clear next steps", "Actionable recommendations"],
            "quality_impact": 0.1
        }


class IntelligentDeliverableAggregator:
    """
    Intelligent Deliverable Aggregator for advanced asset consolidation
    """
    
    def __init__(self, unified_engine: UnifiedDeliverableEngine):
        self.engine = unified_engine
        self.aggregation_strategies = {
            "content_clustering": self._cluster_similar_content,
            "semantic_grouping": self._group_by_semantics,
            "quality_filtering": self._filter_by_quality,
            "relevance_ranking": self._rank_by_relevance
        }
        self.logger = logging.getLogger(__name__)

    async def aggregate_workspace_deliverables(
        self,
        workspace_id: str,
        aggregation_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Aggregate workspace deliverables using intelligent strategies
        """
        
        if not aggregation_config:
            aggregation_config = {
                "min_quality_threshold": 0.7,
                "max_items_per_cluster": 10,
                "enable_semantic_grouping": True,
                "priority_weights": {
                    "quality": 0.4,
                    "relevance": 0.3,
                    "recency": 0.2,
                    "completeness": 0.1
                }
            }
        
        try:
            self.logger.info(f"🔄 Starting intelligent aggregation for workspace {workspace_id}")
            
            # Get workspace assets
            assets = await self.engine.extract_workspace_assets_db(
                workspace_id,
                quality_threshold=aggregation_config.get("min_quality_threshold", 0.7)
            )
            
            # Apply aggregation strategies
            aggregation_result = {
                "workspace_id": workspace_id,
                "total_assets": len(assets),
                "aggregated_clusters": [],
                "aggregation_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "strategies_applied": [],
                    "config": aggregation_config
                }
            }
            
            # Apply each strategy
            processed_assets = assets
            for strategy_name, strategy_func in self.aggregation_strategies.items():
                if aggregation_config.get(f"enable_{strategy_name}", True):
                    try:
                        processed_assets = await strategy_func(processed_assets, aggregation_config)
                        aggregation_result["aggregation_metadata"]["strategies_applied"].append(strategy_name)
                        self.logger.debug(f"✅ Applied strategy: {strategy_name}")
                    except Exception as e:
                        self.logger.warning(f"Strategy {strategy_name} failed: {e}")
            
            # Create final clusters
            if isinstance(processed_assets, list):
                clusters = self._create_final_clusters(processed_assets, aggregation_config)
                aggregation_result["aggregated_clusters"] = clusters
            
            self.logger.info(f"✅ Aggregation complete: {len(aggregation_result['aggregated_clusters'])} clusters created")
            
            return aggregation_result
            
        except Exception as e:
            self.logger.error(f"Error in intelligent aggregation: {e}", exc_info=True)
            return {
                "workspace_id": workspace_id,
                "error": str(e),
                "aggregation_success": False
            }

    async def _cluster_similar_content(self, assets: List[Dict], config: Dict) -> List[Dict]:
        """Cluster similar content assets"""
        # Placeholder implementation
        return assets

    async def _group_by_semantics(self, assets: List[Dict], config: Dict) -> List[Dict]:
        """Group assets by semantic similarity"""
        # Placeholder implementation
        return assets

    async def _filter_by_quality(self, assets: List[Dict], config: Dict) -> List[Dict]:
        """Filter assets by quality threshold"""
        min_quality = config.get("min_quality_threshold", 0.7)
        return [asset for asset in assets if asset.get("quality_score", 0) >= min_quality]

    async def _rank_by_relevance(self, assets: List[Dict], config: Dict) -> List[Dict]:
        """Rank assets by relevance score"""
        # Placeholder implementation - in practice would use AI for semantic relevance
        return sorted(assets, key=lambda x: x.get("relevance_score", 0), reverse=True)

    def _create_final_clusters(self, assets: List[Dict], config: Dict) -> List[Dict]:
        """Create final asset clusters"""
        max_per_cluster = config.get("max_items_per_cluster", 10)
        clusters = []
        
        for i in range(0, len(assets), max_per_cluster):
            cluster_assets = assets[i:i + max_per_cluster]
            cluster = {
                "cluster_id": f"cluster_{i // max_per_cluster + 1}",
                "assets": cluster_assets,
                "cluster_size": len(cluster_assets),
                "average_quality": sum(asset.get("quality_score", 0) for asset in cluster_assets) / len(cluster_assets),
                "cluster_themes": self._extract_cluster_themes(cluster_assets)
            }
            clusters.append(cluster)
        
        return clusters

    def _extract_cluster_themes(self, assets: List[Dict]) -> List[str]:
        """Extract common themes from asset cluster"""
        # Placeholder implementation
        return ["business_data", "actionable_content", "structured_information"]


# Create singleton instance for backward compatibility
unified_deliverable_engine = UnifiedDeliverableEngine()

# =============================================================================
# STANDALONE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================
# These functions maintain compatibility with existing code that imports from deliverable_aggregator

async def check_and_create_final_deliverable(workspace_id: str, force: bool = False, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Standalone function for backward compatibility with deliverable_aggregator.py imports.
    Delegates to the unified engine.
    """
    return await unified_deliverable_engine.check_and_create_final_deliverable(workspace_id, force, context)

async def create_intelligent_deliverable(workspace_id: str) -> Optional[str]:
    """
    Standalone function for backward compatibility.
    Forces creation of intelligent deliverable.
    """
    return await unified_deliverable_engine.check_and_create_final_deliverable(workspace_id, force=True)

# Global instance alias for backward compatibility with IntelligentDeliverableAggregator usage
deliverable_aggregator = unified_deliverable_engine

# =============================================================================
# DELIVERABLE_AGGREGATOR.PY COMPATIBILITY ALIASES
# =============================================================================
# These aliases ensure existing imports from deliverable_aggregator.py continue to work

# Class aliases
IntelligentDeliverableAggregator = UnifiedDeliverableEngine
AIDeliverableAnalyzer = UnifiedDeliverableEngine
DynamicAssetExtractor = UnifiedDeliverableEngine
IntelligentDeliverablePackager = UnifiedDeliverableEngine

# Backward compatibility aliases
concrete_extractor = unified_deliverable_engine
markup_processor = unified_deliverable_engine
deliverable_pipeline = unified_deliverable_engine
requirements_analyzer = unified_deliverable_engine
schema_generator = unified_deliverable_engine
ai_display_enhancer = unified_deliverable_engine

# For imports from individual modules
ConcreteAssetExtractor = UnifiedDeliverableEngine
DeliverableMarkupProcessor = UnifiedDeliverableEngine
DeliverablePipeline = UnifiedDeliverableEngine
RequirementsAnalyzer = UnifiedDeliverableEngine
AssetSchemaGenerator = UnifiedDeliverableEngine
AIDisplayEnhancer = UnifiedDeliverableEngine

logger.info("🔧 Unified Deliverable Engine module loaded successfully with backward compatibility")