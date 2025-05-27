# backend/deliverable_aggregator.py - COMPLETE ENHANCED VERSION
# Sostituisce completamente il file esistente

import logging
import json
import re
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from database import (
    get_workspace, list_tasks, list_agents, create_task,
    update_workspace_status
)
from models import TaskStatus, ProjectPhase
from deliverable_system.requirements_analyzer import DeliverableRequirementsAnalyzer
from deliverable_system.schema_generator import AssetSchemaGenerator
from models import ExtractedAsset, ActionableDeliverable, AssetSchema

logger = logging.getLogger(__name__)

# Enhanced configuration from environment
DELIVERABLE_READINESS_THRESHOLD = int(os.getenv("DELIVERABLE_READINESS_THRESHOLD", "50"))
ENABLE_AUTO_PROJECT_COMPLETION = os.getenv("ENABLE_AUTO_PROJECT_COMPLETION", "true").lower() == "true"
MIN_COMPLETED_TASKS_FOR_DELIVERABLE = int(os.getenv("MIN_COMPLETED_TASKS_FOR_DELIVERABLE", "2"))
ENABLE_ENHANCED_DELIVERABLE_LOGIC = os.getenv("ENABLE_ENHANCED_DELIVERABLE_LOGIC", "true").lower() == "true"

class DeliverableType(str, Enum):
    """Enhanced deliverable types with broader coverage"""
    CONTACT_LIST = "contact_list"
    CONTENT_STRATEGY = "content_strategy"
    COMPETITOR_ANALYSIS = "competitor_analysis"  
    MARKET_RESEARCH = "market_research"
    BUSINESS_PLAN = "business_plan"
    LEAD_GENERATION = "lead_generation"
    SOCIAL_MEDIA_PLAN = "social_media_plan"
    CAMPAIGN_STRATEGY = "campaign_strategy"
    MARKETING_AUDIT = "marketing_audit"
    WEBSITE_ANALYSIS = "website_analysis"
    BRAND_STRATEGY = "brand_strategy"
    GENERIC_REPORT = "generic_report"


class EnhancedDeliverableAggregator:
    """Enhanced deliverable aggregator with improved detection and creation logic"""
    
    def __init__(self):
        self.goal_patterns = {
            DeliverableType.CONTACT_LIST: [
                r"find.*contact", r"lead.*generation", r"prospect", 
                r"cold.*call", r"email.*list", r"outreach", r"lead.*list"
            ],
            DeliverableType.CONTENT_STRATEGY: [
                r"content.*strategy", r"editorial.*plan", r"content.*plan",
                r"social.*media.*strategy", r"instagram.*strategy", r"content.*marketing"
            ],
            DeliverableType.COMPETITOR_ANALYSIS: [
                r"competitor.*analy", r"competitive.*landscap", 
                r"competitor.*research", r"market.*position", r"competitive.*intelligence"
            ],
            DeliverableType.MARKET_RESEARCH: [
                r"market.*research", r"market.*analysis", r"industry.*analysis",
                r"target.*audience", r"customer.*research", r"market.*study"
            ],
            DeliverableType.SOCIAL_MEDIA_PLAN: [
                r"social.*media", r"instagram.*plan", r"facebook.*strategy",
                r"twitter.*strategy", r"linkedin.*strategy", r"social.*campaign"
            ],
            DeliverableType.LEAD_GENERATION: [
                r"lead.*generation", r"sales.*funnel", r"conversion.*strategy",
                r"lead.*qualification", r"lead.*nurturing"
            ],
            DeliverableType.CAMPAIGN_STRATEGY: [
                r"campaign.*strategy", r"marketing.*campaign", r"advertising.*campaign",
                r"promotion.*strategy", r"campaign.*plan"
            ],
            DeliverableType.MARKETING_AUDIT: [
                r"marketing.*audit", r"marketing.*analysis", r"marketing.*review",
                r"digital.*audit", r"marketing.*assessment"
            ]
        }
        
        # Enhanced readiness criteria
        self.readiness_threshold = DELIVERABLE_READINESS_THRESHOLD / 100.0
        self.min_completed_tasks = MIN_COMPLETED_TASKS_FOR_DELIVERABLE
        
        logger.info(f"Enhanced Deliverable Aggregator initialized: "
                   f"threshold={self.readiness_threshold}, min_tasks={self.min_completed_tasks}")
    
    async def check_and_create_final_deliverable(self, workspace_id: str) -> Optional[str]:
        """
        ENHANCED: Check if ready for final deliverable with improved logic
        """
        try:
            logger.info(f"🎯 DELIVERABLE CHECK: Starting for workspace {workspace_id}")
            
            # Enhanced readiness check with multiple criteria
            if not await self._is_ready_for_final_deliverable_enhanced(workspace_id):
                logger.debug(f"🎯 NOT READY: Workspace {workspace_id}")
                return None
            
            # Check if deliverable already exists
            if await self._final_deliverable_exists_enhanced(workspace_id):
                logger.info(f"🎯 EXISTS: Final deliverable already exists for {workspace_id}")
                return None
            
            # Gather comprehensive project data
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if not workspace:
                logger.error(f"🎯 ERROR: Workspace {workspace_id} not found")
                return None
            
            if len(completed_tasks) < self.min_completed_tasks:
                logger.info(f"🎯 INSUFFICIENT: Only {len(completed_tasks)} completed tasks "
                           f"(need {self.min_completed_tasks})")
                return None
            
            # Enhanced deliverable type detection
            deliverable_type = self._determine_deliverable_type_enhanced(workspace.get("goal", ""))
            logger.info(f"🎯 TYPE: Detected deliverable type: {deliverable_type.value}")
            
            # Enhanced data aggregation
            aggregated_data = await self._aggregate_task_results_enhanced(completed_tasks, deliverable_type)
            
            # Create final deliverable with enhanced features
            deliverable_task_id = await self._create_final_deliverable_task_enhanced(
                workspace_id, workspace, deliverable_type, aggregated_data
            )
            
            if deliverable_task_id:
                logger.critical(f"🎯 SUCCESS: Created final deliverable {deliverable_task_id} "
                               f"for workspace {workspace_id} (type: {deliverable_type.value})")
                
                # Enhanced: Trigger auto-completion if enabled
                if ENABLE_AUTO_PROJECT_COMPLETION:
                    try:
                        await self._trigger_project_completion_sequence(workspace_id, deliverable_task_id)
                    except Exception as e:
                        logger.error(f"Error in project completion sequence: {e}")
                
                return deliverable_task_id
            else:
                logger.error(f"🎯 FAILED: Could not create deliverable for {workspace_id}")
                return None
            
        except Exception as e:
            logger.error(f"🎯 ERROR: Exception in deliverable check for {workspace_id}: {e}", exc_info=True)
            return None
    
    async def _is_ready_for_final_deliverable_enhanced(self, workspace_id: str) -> bool:
        """
        ENHANCED: Multi-criteria readiness check with improved logic
        """
        try:
            tasks = await list_tasks(workspace_id)
            
            if not tasks:
                logger.debug(f"🎯 READINESS: No tasks in {workspace_id}")
                return False
            
            completed = [t for t in tasks if t.get("status") == "completed"]
            pending = [t for t in tasks if t.get("status") == "pending"]
            failed = [t for t in tasks if t.get("status") == "failed"]
            
            total_tasks = len(tasks)
            completed_count = len(completed)
            pending_count = len(pending)
            
            # === CRITERION 1: Completion Rate ===
            completion_rate = completed_count / total_tasks if total_tasks > 0 else 0
            completion_threshold_met = completion_rate >= self.readiness_threshold
            
            logger.info(f"🎯 READINESS: Completion rate: {completion_rate:.2f} "
                       f"(threshold: {self.readiness_threshold})")
            
            # === CRITERION 2: Minimum Completed Tasks ===
            min_tasks_met = completed_count >= self.min_completed_tasks
            
            # === CRITERION 3: Low Pending Count ===
            # More permissive: allow up to 5 pending tasks (was 2)
            low_pending = pending_count <= 5
            
            # === CRITERION 4: FINALIZATION Phase Progress ===
            finalization_progress = False
            finalization_completed = 0
            
            for task in completed:
                context_data = task.get("context_data", {}) or {}
                if isinstance(context_data, dict):
                    project_phase = context_data.get("project_phase", "").upper()
                    if project_phase == "FINALIZATION":
                        finalization_completed += 1
            
            # More permissive: 1 FINALIZATION task completed (was 2)
            finalization_progress = finalization_completed >= 1
            
            # === CRITERION 5: Quality Check - No Excessive Failures ===
            failure_rate = len(failed) / total_tasks if total_tasks > 0 else 0
            quality_threshold_met = failure_rate <= 0.3  # Allow up to 30% failures
            
            # === CRITERION 6: Time-based Check ===
            # Allow deliverable creation if project has been running for sufficient time
            workspace = await get_workspace(workspace_id)
            time_based_ready = False
            
            if workspace and workspace.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(workspace["created_at"].replace('Z', '+00:00'))
                    project_age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600
                    
                    # If project is over 2 hours old and has reasonable progress, allow deliverable
                    if project_age_hours > 2 and completed_count >= 3:
                        time_based_ready = True
                        
                except Exception as e:
                    logger.debug(f"Error calculating project age: {e}")
            
            # === ENHANCED DECISION LOGIC ===
            # Multiple paths to readiness for improved deliverable generation
            
            # Path 1: Standard criteria (most restrictive)
            standard_ready = (completion_threshold_met and min_tasks_met and 
                            low_pending and finalization_progress and quality_threshold_met)
            
            # Path 2: High completion rate with some flexibility
            high_completion_ready = (completion_rate >= 0.8 and completed_count >= 5 and 
                                   pending_count <= 8 and quality_threshold_met)
            
            # Path 3: FINALIZATION phase focus
            finalization_ready = (finalization_completed >= 2 and completed_count >= 4 and
                                pending_count <= 6)
            
            # Path 4: Time-based with reasonable progress
            time_ready = (time_based_ready and completion_rate >= 0.6 and 
                         completed_count >= 4 and pending_count <= 7)
            
            is_ready = standard_ready or high_completion_ready or finalization_ready or time_ready
            
            # Detailed logging for analysis
            logger.info(f"🎯 READINESS ANALYSIS for {workspace_id}:")
            logger.info(f"  ├─ Tasks: {completed_count}/{total_tasks} completed ({completion_rate:.2f}), "
                       f"{pending_count} pending, {len(failed)} failed")
            logger.info(f"  ├─ FINALIZATION: {finalization_completed} tasks completed")
            logger.info(f"  ├─ Standard Ready: {standard_ready}")
            logger.info(f"  ├─ High Completion Ready: {high_completion_ready}")
            logger.info(f"  ├─ Finalization Ready: {finalization_ready}")
            logger.info(f"  ├─ Time Ready: {time_ready}")
            logger.info(f"  └─ FINAL DECISION: {is_ready}")
            
            return is_ready
            
        except Exception as e:
            logger.error(f"Error checking enhanced deliverable readiness: {e}")
            return False
    
    async def _final_deliverable_exists_enhanced(self, workspace_id: str) -> bool:
            """
            ENHANCED: Check for existing deliverable with multiple detection methods
            FIXED: Improved logic to avoid false positives from planning tasks
            """
            try:
                tasks = await list_tasks(workspace_id)

                for task in tasks:
                    context_data = task.get("context_data", {}) or {}
                    task_name = (task.get("name", "") or "").upper()

                    # PRIORITY 1: Explicit deliverable markers (most reliable)
                    if isinstance(context_data, dict):
                        # Check for explicit deliverable flags
                        if (context_data.get("is_final_deliverable") or 
                            context_data.get("deliverable_aggregation") or
                            context_data.get("triggers_project_completion")):
                            logger.info(f"🎯 EXISTING: Found deliverable by explicit marker: {task['id']}")
                            return True

                        # Check for deliverable creation types
                        creation_type = context_data.get("creation_type", "")
                        if creation_type in ["final_deliverable_aggregation", "final_deliverable_aggregation_enhanced", "project_completion"]:
                            logger.info(f"🎯 EXISTING: Found deliverable by creation type: {task['id']}")
                            return True

                        # CRITICAL FIX: Exclude planning tasks explicitly
                        if (context_data.get("planning_task_marker") or 
                            creation_type == "phase_transition" or
                            context_data.get("is_finalization_planning") or
                            context_data.get("phase_transition")):
                            logger.debug(f"🎯 SKIPPING: Planning task excluded from deliverable check: {task['id']}")
                            continue  # Skip this task, it's a planning task

                    # PRIORITY 2: Specific name patterns (more restrictive than before)
                    # Only look for complete phrases that clearly indicate final deliverables
                    specific_deliverable_patterns = [
                        "FINAL DELIVERABLE:", 
                        "PROJECT DELIVERABLE:", 
                        "COMPLETE DELIVERABLE:",
                        "FINAL PROJECT DELIVERABLE",
                        "DELIVERABLE AGGREGATION"
                    ]

                    # Check for specific patterns but exclude planning patterns
                    planning_exclusion_patterns = [
                        "CREATE FINAL DELIVERABLES",  # This is planning, not the actual deliverable
                        "PLANNING",
                        "SETUP", 
                        "CRITICAL: CREATE"
                    ]

                    # If it matches a planning pattern, skip it
                    if any(exclusion in task_name for exclusion in planning_exclusion_patterns):
                        logger.debug(f"🎯 SKIPPING: Planning pattern detected in task name: {task['id']}")
                        continue

                    # Now check for deliverable patterns
                    if any(pattern in task_name for pattern in specific_deliverable_patterns):
                        logger.info(f"🎯 EXISTING: Found deliverable by specific name pattern: {task['id']}")
                        return True

                    # PRIORITY 3: Legacy emoji check (most restrictive)
                    # Only if it's clearly a deliverable context AND has the emoji
                    if ("🎯" in task_name and 
                        isinstance(context_data, dict) and
                        context_data.get("deliverable_aggregation") and
                        not context_data.get("planning_task_marker")):
                        logger.info(f"🎯 EXISTING: Found deliverable by emoji + context validation: {task['id']}")
                        return True

                logger.debug(f"🎯 NOT EXISTS: No final deliverable found for {workspace_id}")
                return False

            except Exception as e:
                logger.error(f"Error checking existing deliverable: {e}")
                return True  # Safe default to prevent duplicates
    
    def _determine_deliverable_type_enhanced(self, goal: str) -> DeliverableType:
        """
        ENHANCED: Determine deliverable type with improved pattern matching
        """
        if not goal:
            return DeliverableType.GENERIC_REPORT
        
        goal_lower = goal.lower()
        
        # Enhanced scoring system for better type detection
        type_scores = {}
        
        for deliverable_type, patterns in self.goal_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower))
                score += matches * 10  # Weight each match
                
                # Bonus for exact phrase matches
                if pattern.replace(r"\.", ".").replace(r"\*", "") in goal_lower:
                    score += 5
            
            if score > 0:
                type_scores[deliverable_type] = score
        
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            logger.info(f"🎯 TYPE DETECTION: '{goal[:100]}' -> {best_type.value} "
                       f"(score: {type_scores[best_type]})")
            return best_type
        
        # Fallback: try keyword matching
        keyword_mapping = {
            "instagram": DeliverableType.SOCIAL_MEDIA_PLAN,
            "marketing": DeliverableType.MARKETING_AUDIT,
            "content": DeliverableType.CONTENT_STRATEGY,
            "leads": DeliverableType.LEAD_GENERATION,
            "contacts": DeliverableType.CONTACT_LIST,
            "research": DeliverableType.MARKET_RESEARCH,
            "competition": DeliverableType.COMPETITOR_ANALYSIS,
            "strategy": DeliverableType.BUSINESS_PLAN
        }
        
        for keyword, deliverable_type in keyword_mapping.items():
            if keyword in goal_lower:
                logger.info(f"🎯 TYPE FALLBACK: '{goal[:100]}' -> {deliverable_type.value} "
                           f"(keyword: {keyword})")
                return deliverable_type
        
        logger.info(f"🎯 TYPE DEFAULT: '{goal[:100]}' -> {DeliverableType.GENERIC_REPORT.value}")
        return DeliverableType.GENERIC_REPORT
    
    async def _aggregate_task_results_enhanced(
        self, 
        completed_tasks: List[Dict], 
        deliverable_type: DeliverableType
    ) -> Dict[str, Any]:
        """
        ENHANCED: Aggregate task results with improved data extraction and fallback handling
        """
        
        aggregated = {
            "total_tasks": len(completed_tasks),
            "task_summaries": [],
            "structured_data": {},
            "key_insights": [],
            "recommendations": [],
            "project_metrics": {},
            "data_quality_score": 0
        }
        
        all_structured_data = []
        quality_indicators = {
            "tasks_with_summaries": 0,
            "tasks_with_structured_data": 0,
            "tasks_with_recommendations": 0,
            "total_content_length": 0
        }
        
        # Enhanced task processing with better error handling
        for task in completed_tasks:
            try:
                result = task.get("result", {}) or {}
                summary = result.get("summary", "")
                
                # Process task summary
                if summary and len(summary.strip()) > 10:
                    task_summary = {
                        "task_name": task.get("name", ""),
                        "summary": summary,
                        "agent_role": task.get("assigned_to_role", "Unknown"),
                        "completed_at": task.get("updated_at", ""),
                        "task_id": task.get("id", "")
                    }
                    aggregated["task_summaries"].append(task_summary)
                    quality_indicators["tasks_with_summaries"] += 1
                    quality_indicators["total_content_length"] += len(summary)
                
                # Process structured data
                detailed_json = result.get("detailed_results_json")
                if detailed_json and isinstance(detailed_json, str) and detailed_json.strip():
                    try:
                        structured = json.loads(detailed_json)
                        if isinstance(structured, dict) and structured:
                            structured_item = {
                                "task_id": task.get("id"),
                                "task_name": task.get("name", ""),
                                "data": structured,
                                "data_size": len(str(structured))
                            }
                            all_structured_data.append(structured_item)
                            quality_indicators["tasks_with_structured_data"] += 1
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error for task {task.get('id')}: {e}")
                        # Fallback: try to extract partial data
                        partial_data = self._extract_partial_json_data(detailed_json)
                        if partial_data:
                            all_structured_data.append({
                                "task_id": task.get("id"),
                                "task_name": task.get("name", ""),
                                "data": partial_data,
                                "data_source": "partial_extraction"
                            })
                
                # Process recommendations
                next_steps = result.get("next_steps", [])
                if isinstance(next_steps, list) and next_steps:
                    aggregated["recommendations"].extend(next_steps)
                    quality_indicators["tasks_with_recommendations"] += 1
                    
            except Exception as e:
                logger.warning(f"Error processing task {task.get('id', 'unknown')}: {e}")
                continue
        
        # Calculate data quality score
        total_tasks = len(completed_tasks)
        if total_tasks > 0:
            quality_score = (
                (quality_indicators["tasks_with_summaries"] / total_tasks * 40) +
                (quality_indicators["tasks_with_structured_data"] / total_tasks * 30) +
                (quality_indicators["tasks_with_recommendations"] / total_tasks * 20) +
                (min(quality_indicators["total_content_length"] / 2000, 1) * 10)
            )
            aggregated["data_quality_score"] = round(quality_score, 1)
        
        # Enhanced structured data processing
        aggregated["structured_data"] = await self._process_structured_data_by_type(
            all_structured_data, deliverable_type
        )
        
        # Enhanced key insights extraction
        aggregated["key_insights"] = self._extract_key_insights_enhanced(
            aggregated["task_summaries"], deliverable_type
        )
        
        # Project metrics calculation
        aggregated["project_metrics"] = self._calculate_project_metrics(completed_tasks)
        
        logger.info(f"🎯 AGGREGATION: {total_tasks} tasks processed, "
                   f"quality score: {aggregated['data_quality_score']}, "
                   f"structured data: {len(all_structured_data)}")
        
        return aggregated
    
    def _extract_partial_json_data(self, json_str: str) -> Dict[str, Any]:
        """Extract partial data from malformed JSON"""
        try:
            # Try to find JSON objects in the string
            json_matches = re.finditer(r'\{[^{}]*\}', json_str)
            partial_data = {}
            
            for match in json_matches:
                try:
                    obj = json.loads(match.group())
                    if isinstance(obj, dict):
                        partial_data.update(obj)
                except:
                    continue
            
            return partial_data if partial_data else {}
            
        except Exception:
            return {}
    
    async def _process_structured_data_by_type(
        self, 
        structured_data: List[Dict], 
        deliverable_type: DeliverableType
    ) -> Dict[str, Any]:
        """
        ENHANCED: Process structured data based on deliverable type with better extraction
        """
        
        if deliverable_type == DeliverableType.CONTACT_LIST:
            return self._extract_contact_data_enhanced(structured_data)
        elif deliverable_type == DeliverableType.CONTENT_STRATEGY:
            return self._extract_content_strategy_data_enhanced(structured_data)
        elif deliverable_type == DeliverableType.COMPETITOR_ANALYSIS:
            return self._extract_competitor_data_enhanced(structured_data)
        elif deliverable_type == DeliverableType.MARKET_RESEARCH:
            return self._extract_market_research_data(structured_data)
        elif deliverable_type == DeliverableType.SOCIAL_MEDIA_PLAN:
            return self._extract_social_media_data(structured_data)
        else:
            # Enhanced generic aggregation
            return self._extract_generic_data_enhanced(structured_data)
    
    def _extract_contact_data_enhanced(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced contact data extraction with better field detection"""
        contacts = []
        sources = []
        contact_fields = set()
        
        for item in structured_data:
            data = item.get("data", {})
            
            # Enhanced field detection
            potential_contact_keys = [
                key for key in data.keys() 
                if any(term in key.lower() for term in 
                      ["contact", "lead", "prospect", "company", "business", "client", "email", "phone"])
            ]
            
            for key in potential_contact_keys:
                value = data[key]
                if isinstance(value, list):
                    for contact in value:
                        if isinstance(contact, dict):
                            contacts.append(contact)
                            contact_fields.update(contact.keys())
                        elif isinstance(contact, str) and "@" in contact:
                            contacts.append({"email": contact, "source": item.get("task_name", "")})
                elif isinstance(value, dict):
                    contacts.append(value)
                    contact_fields.update(value.keys())
            
            sources.append(item.get("task_name", ""))
        
        return {
            "total_contacts": len(contacts),
            "contacts": contacts[:1000],  # Limit for performance
            "data_sources": sources,
            "contact_fields": list(contact_fields),
            "collection_methods": list(set(sources))
        }
    
    def _extract_content_strategy_data_enhanced(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced content strategy data extraction"""
        content_ideas = []
        strategies = []
        calendars = []
        hashtags = set()
        
        for item in structured_data:
            data = item.get("data", {})
            
            # Enhanced content detection
            for key, value in data.items():
                key_lower = key.lower()
                
                if any(term in key_lower for term in ["content", "post", "idea", "topic"]):
                    if isinstance(value, list):
                        content_ideas.extend(value)
                    elif isinstance(value, str) and len(value) > 10:
                        content_ideas.append(value)
                        
                elif any(term in key_lower for term in ["strategy", "plan", "framework"]):
                    strategies.append(value)
                    
                elif any(term in key_lower for term in ["calendar", "schedule", "timeline"]):
                    calendars.append(value)
                    
                elif "hashtag" in key_lower and isinstance(value, list):
                    hashtags.update(value)
        
        return {
            "content_ideas": content_ideas,
            "strategies": strategies,
            "calendars": calendars,
            "hashtags": list(hashtags),
            "total_content_pieces": len(content_ideas)
        }
    
    def _extract_competitor_data_enhanced(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced competitor data extraction"""
        competitors = []
        analyses = []
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                if "competitor" in key.lower():
                    if isinstance(value, list):
                        competitors.extend(value)
                    else:
                        competitors.append(value)
                elif "analysis" in key.lower():
                    analyses.append(value)
        
        return {
            "competitors_analyzed": len(competitors),
            "competitor_profiles": competitors,
            "analysis_results": analyses
        }
    
    def _extract_market_research_data(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Extract market research specific data"""
        market_data = []
        audience_data = []
        trends = []
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                key_lower = key.lower()
                if any(term in key_lower for term in ["market", "industry", "sector"]):
                    market_data.append(value)
                elif any(term in key_lower for term in ["audience", "demographic", "customer"]):
                    audience_data.append(value)
                elif any(term in key_lower for term in ["trend", "pattern", "behavior"]):
                    trends.append(value)
        
        return {
            "market_insights": market_data,
            "audience_profiles": audience_data,
            "trends_identified": trends,
            "research_depth": len(market_data) + len(audience_data) + len(trends)
        }
    
    def _extract_social_media_data(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Extract social media specific data"""
        platforms = {}
        campaigns = []
        metrics = {}
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                key_lower = key.lower()
                if any(platform in key_lower for platform in ["instagram", "facebook", "twitter", "linkedin"]):
                    platform_name = next((p for p in ["instagram", "facebook", "twitter", "linkedin"] if p in key_lower), "unknown")
                    if platform_name not in platforms:
                        platforms[platform_name] = []
                    platforms[platform_name].append(value)
                elif "campaign" in key_lower:
                    campaigns.append(value)
                elif any(term in key_lower for term in ["metric", "analytics", "performance"]):
                    metrics[key] = value
        
        return {
            "platforms": platforms,
            "campaigns": campaigns,
            "metrics": metrics,
            "platform_count": len(platforms)
        }
    
    def _extract_generic_data_enhanced(self, structured_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced generic data extraction with intelligent categorization"""
        categories = {
            "analysis_results": [],
            "recommendations": [],
            "data_points": [],
            "metrics": {},
            "insights": []
        }
        
        for item in structured_data:
            data = item.get("data", {})
            
            for key, value in data.items():
                key_lower = key.lower()
                
                if any(term in key_lower for term in ["analysis", "result", "finding"]):
                    categories["analysis_results"].append({"key": key, "value": value})
                elif any(term in key_lower for term in ["recommend", "suggest", "action"]):
                    categories["recommendations"].append(value)
                elif any(term in key_lower for term in ["metric", "number", "count", "rate"]):
                    categories["metrics"][key] = value
                elif any(term in key_lower for term in ["insight", "observation", "conclusion"]):
                    categories["insights"].append(value)
                else:
                    categories["data_points"].append({"key": key, "value": value})
        
        categories["data_sources"] = [item.get("task_name", "Unknown") for item in structured_data]
        categories["num_data_sources"] = len(structured_data)
        
        return categories
    
    def _extract_key_insights_enhanced(
        self, 
        task_summaries: List[Dict], 
        deliverable_type: DeliverableType
    ) -> List[str]:
        """Enhanced key insights extraction with better NLP"""
        insights = []
        
        # Enhanced keyword patterns for different deliverable types
        insight_patterns = {
            DeliverableType.CONTACT_LIST: [
                r"identified (\d+) (?:contacts?|leads?|prospects?)",
                r"found (\d+) (?:qualified|potential) (?:contacts?|leads?)",
                r"generated (?:a )?(?:list of )?(\d+) (?:contacts?|leads?)"
            ],
            DeliverableType.CONTENT_STRATEGY: [
                r"(?:created?|developed?) (\d+) content (?:ideas?|concepts?)",
                r"identified (\d+) (?:themes?|pillars?|topics?)",
                r"engagement rate of ([\d.]+)%"
            ],
            DeliverableType.COMPETITOR_ANALYSIS: [
                r"analyzed (\d+) (?:competitors?|rival companies?)",
                r"identified (\d+) (?:competitive advantages?|weaknesses?|opportunities?)",
                r"market share of ([\d.]+)%"
            ]
        }
        
        # Default patterns for any deliverable type
        default_patterns = [
            r"achieved (\d+)% (?:improvement|increase|growth)",
            r"identified (\d+) (?:key|main|primary|important) (?:factors?|elements?|points?)",
            r"recommended (\d+) (?:actions?|steps?|strategies?)",
            r"found (\d+) (?:opportunities?|issues?|solutions?)"
        ]
        
        patterns_to_use = insight_patterns.get(deliverable_type, default_patterns)
        
        for summary_item in task_summaries:
            summary = summary_item.get("summary", "")
            
            # Extract quantified insights
            for pattern in patterns_to_use:
                matches = re.finditer(pattern, summary, re.IGNORECASE)
                for match in matches:
                    # Extract the full sentence containing the match
                    sentences = re.split(r'[.!?]+', summary)
                    for sentence in sentences:
                        if match.group() in sentence:
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 20 and clean_sentence not in insights:
                                insights.append(clean_sentence)
                            break
            
            # Extract sentences with insight keywords
            insight_keywords = ["discovered", "revealed", "found", "identified", "concluded", 
                              "determined", "observed", "noted", "realized", "established"]
            
            sentences = re.split(r'[.!?]+', summary)
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 25 and 
                    any(keyword in sentence.lower() for keyword in insight_keywords) and
                    sentence not in insights):
                    insights.append(sentence)
        
        return insights[:15]  # Limit to top 15 insights
    
    def _calculate_project_metrics(self, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive project metrics"""
        
        total_tasks = len(completed_tasks)
        
        # Time analysis
        task_durations = []
        for task in completed_tasks:
            try:
                created_at = task.get("created_at")
                updated_at = task.get("updated_at")
                
                if created_at and updated_at:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    duration_hours = (updated - created).total_seconds() / 3600
                    task_durations.append(duration_hours)
            except:
                continue
        
        # Phase distribution
        phase_distribution = {}
        for task in completed_tasks:
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                phase = context_data.get("project_phase", "UNKNOWN")
                phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        # Agent activity
        agent_activity = {}
        for task in completed_tasks:
            agent_role = task.get("assigned_to_role", "Unknown")
            agent_activity[agent_role] = agent_activity.get(agent_role, 0) + 1
        
        metrics = {
            "total_completed_tasks": total_tasks,
            "average_task_duration_hours": round(sum(task_durations) / len(task_durations), 2) if task_durations else 0,
            "phase_distribution": phase_distribution,
            "agent_activity": agent_activity,
            "tasks_with_structured_data": sum(1 for t in completed_tasks if t.get("result", {}).get("detailed_results_json")),
            "completion_rate_estimate": "85-95%" if total_tasks >= 8 else "70-85%"
        }
        
        return metrics
    
    async def _create_final_deliverable_task_enhanced(
        self, 
        workspace_id: str, 
        workspace: Dict, 
        deliverable_type: DeliverableType,
        aggregated_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        ENHANCED: Create final deliverable task with comprehensive data and smart assignment
        """

        try:
            # Find the best agent for deliverable creation
            agents = await list_agents(workspace_id)
            deliverable_agent = await self._find_best_deliverable_agent(agents, deliverable_type)

            if not deliverable_agent:
                logger.error(f"🎯 ERROR: No suitable agent for deliverable in workspace {workspace_id}")
                return None

            # Generate comprehensive task description
            description = self._create_enhanced_deliverable_description(
                workspace.get("goal", ""), deliverable_type, aggregated_data
            )

            # FIXED: Enhanced task name WITHOUT "CRITICAL" to avoid priority validation issues
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            task_name = f"🎯 FINAL DELIVERABLE: {deliverable_type.value.replace('_', ' ').title()} ({timestamp})"

            # FIXED: Explicitly ensure priority is valid
            task_priority = "high"  # Must be one of: "low", "medium", "high"

            # Create the deliverable task
            deliverable_task = await create_task(
                workspace_id=workspace_id,
                agent_id=deliverable_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority=task_priority,  # FIXED: Use explicit valid priority
                creation_type="final_deliverable_aggregation_enhanced",
                context_data={
                    "is_final_deliverable": True,
                    "deliverable_aggregation": True,
                    "deliverable_type": deliverable_type.value,
                    "project_phase": "FINALIZATION",
                    "aggregated_data_summary": {
                        "total_tasks": aggregated_data.get("total_tasks", 0),
                        "data_quality_score": aggregated_data.get("data_quality_score", 0),
                        "key_insights_count": len(aggregated_data.get("key_insights", [])),
                        "structured_data_sources": aggregated_data.get("structured_data", {}).get("num_data_sources", 0)
                    },
                    "workspace_goal": workspace.get("goal", ""),
                    "creation_timestamp": datetime.now().isoformat(),
                    "triggers_project_completion": True,
                    "enhanced_deliverable_version": "2.0",
                    "data_quality_score": aggregated_data.get("data_quality_score", 0),
                    "agent_selection_reason": f"Selected {deliverable_agent['name']} for {deliverable_type.value}",
                    "is_high_priority_deliverable": True
                }
            )

            if deliverable_task and deliverable_task.get("id"):
                logger.critical(f"🎯 DELIVERABLE CREATED: {deliverable_task['id']} "
                               f"assigned to {deliverable_agent['name']} "
                               f"for type {deliverable_type.value} with priority '{task_priority}'")
                return deliverable_task["id"]
            else:
                logger.error(f"🎯 DELIVERABLE FAILED: Database creation failed")
                return None

        except Exception as e:
            logger.error(f"Error creating enhanced deliverable task: {e}", exc_info=True)
            return None
    
    async def _find_best_deliverable_agent(self, agents: List[Dict], deliverable_type: DeliverableType) -> Optional[Dict]:
        """Find the best agent for creating the deliverable"""
        
        if not agents:
            return None
        
        # Agent role preferences for different deliverable types
        role_preferences = {
            DeliverableType.CONTACT_LIST: ["analysis", "research", "data", "lead"],
            DeliverableType.CONTENT_STRATEGY: ["content", "marketing", "strategy", "social"],
            DeliverableType.COMPETITOR_ANALYSIS: ["analysis", "research", "competitive", "market"],
            DeliverableType.MARKET_RESEARCH: ["research", "analysis", "market", "data"],
            DeliverableType.SOCIAL_MEDIA_PLAN: ["social", "marketing", "content", "digital"],
            DeliverableType.LEAD_GENERATION: ["sales", "marketing", "lead", "business"],
            DeliverableType.CAMPAIGN_STRATEGY: ["marketing", "campaign", "strategy", "advertising"],
            DeliverableType.MARKETING_AUDIT: ["marketing", "analysis", "audit", "strategy"],
            DeliverableType.GENERIC_REPORT: ["manager", "coordinator", "analysis", "specialist"]
        }
        
        preferred_keywords = role_preferences.get(deliverable_type, ["manager", "specialist"])
        
        # Score agents based on role match
        scored_agents = []
        
        for agent in agents:
            if agent.get("status") != "active":
                continue
                
            role = (agent.get("role", "") or "").lower()
            name = (agent.get("name", "") or "").lower()
            seniority = agent.get("seniority", "junior")
            
            score = 0
            
            # Role matching score
            for keyword in preferred_keywords:
                if keyword in role or keyword in name:
                    score += 10
            
            # Seniority bonus
            seniority_bonus = {"expert": 15, "senior": 10, "junior": 5}
            score += seniority_bonus.get(seniority, 0)
            
            # Special case: prefer Project Manager for generic reports
            if deliverable_type == DeliverableType.GENERIC_REPORT:
                if "project" in role and "manager" in role:
                    score += 20
                elif "manager" in role or "coordinator" in role:
                    score += 15
            
            if score > 0:
                scored_agents.append((agent, score))
        
        if scored_agents:
            # Sort by score and return the best match
            scored_agents.sort(key=lambda x: x[1], reverse=True)
            best_agent = scored_agents[0][0]
            logger.info(f"🎯 AGENT SELECTION: {best_agent['name']} ({best_agent['role']}) "
                       f"selected for {deliverable_type.value} (score: {scored_agents[0][1]})")
            return best_agent
        
        # Fallback: return any active agent
        active_agents = [a for a in agents if a.get("status") == "active"]
        if active_agents:
            fallback_agent = active_agents[0]
            logger.warning(f"🎯 AGENT FALLBACK: {fallback_agent['name']} selected as fallback")
            return fallback_agent
        
        return None
    
    def _create_enhanced_deliverable_description(
            self, 
            goal: str, 
            deliverable_type: DeliverableType,
            aggregated_data: Dict[str, Any]
        ) -> str:
            """Create comprehensive deliverable description with all aggregated data - ENHANCED"""

            # Enhanced base context with quality metrics
            quality_score = aggregated_data.get("data_quality_score", 0)
            total_tasks = aggregated_data.get("total_tasks", 0)
            key_insights_count = len(aggregated_data.get("key_insights", []))

            base_context = f"""🎯 **FINAL PROJECT DELIVERABLE CREATION**

    **PROJECT OBJECTIVE:** {goal}

    **📊 AGGREGATED PROJECT DATA SUMMARY:**
    - Total completed tasks analyzed: {total_tasks}
    - Data quality score: {quality_score}/100
    - Task summaries: {len(aggregated_data.get('task_summaries', []))}
    - Key insights extracted: {key_insights_count}
    - Structured data sources: {aggregated_data.get('structured_data', {}).get('num_data_sources', 0)}

    **🎯 YOUR CRITICAL MISSION:** 
    Create the FINAL, CLIENT-READY deliverable that comprehensively addresses the project objective. 

    **🚨 MANDATORY OUTPUT FORMAT:**
    Your response MUST be a valid JSON object in the detailed_results_json field that includes:
    1. "executive_summary" - A compelling 2-3 paragraph project overview
    2. "deliverable_type" - The type of deliverable created  
    3. "key_findings" - Array of key insights from the project
    4. "project_metrics" - Object with project statistics and metrics

    **⚠️ CRITICAL REQUIREMENTS:**
    - The detailed_results_json MUST be valid JSON (no trailing commas, proper escaping)
    - The executive_summary MUST be comprehensive and client-ready
    - Include ALL available data from the aggregated results provided
    - This deliverable represents the culmination of the entire project

    **📋 DELIVERABLE TYPE:** {deliverable_type.value.replace('_', ' ').title()}
    """

            # Enhanced type-specific instructions with foolproof JSON templates
            type_specific = self._get_foolproof_output_schema(deliverable_type.value, aggregated_data, goal)

            return base_context + type_specific
    
    def _get_foolproof_output_schema(self, deliverable_type_value: str, aggregated_data: Dict, goal: str) -> str:
        """Get foolproof output schema with simple, reliable JSON templates"""

        # Simplified, reliable JSON templates to prevent parsing errors
        if deliverable_type_value == "contact_list":
            return f"""
    **📞 CONTACT LIST DELIVERABLE - EXACT JSON TEMPLATE:**

    Copy this EXACT template and fill in the data:

    {{
      "deliverable_type": "contact_list",
      "executive_summary": "Write a comprehensive 2-3 paragraph summary of the contact list generation project. Include the business objective, methodology used, and key results achieved. This should be client-ready and professional.",
      "key_findings": [
        "Key insight 1 from contact research",
        "Key insight 2 from lead generation", 
        "Key insight 3 from data analysis"
      ],
      "project_metrics": {{
        "total_contacts_generated": 0,
        "data_quality_score": "{aggregated_data.get('data_quality_score', 0)}",
        "tasks_completed": {aggregated_data.get('total_tasks', 0)}
      }},
      "final_deliverable": {{
        "contact_count": 0,
        "primary_sources": ["List your data sources here"],
        "recommended_next_steps": ["Immediate action 1", "Follow-up action 2"]
      }}
    }}

    🎯 **REPLACE THE PLACEHOLDER VALUES** with actual data from your analysis!
    """

        elif deliverable_type_value == "content_strategy":
            return f"""
    **📝 CONTENT STRATEGY DELIVERABLE - EXACT JSON TEMPLATE:**

    Copy this EXACT template and fill in the data:

    {{
      "deliverable_type": "content_strategy",
      "executive_summary": "Write a comprehensive 2-3 paragraph summary of the content strategy development. Include the business objective, strategic approach, and expected outcomes. This should be client-ready and professional.",
      "key_findings": [
        "Strategic insight 1",
        "Content opportunity 2",
        "Audience insight 3"
      ],
      "project_metrics": {{
        "content_ideas_generated": 0,
        "strategy_frameworks_created": 0,
        "tasks_completed": {aggregated_data.get('total_tasks', 0)}
      }},
      "final_deliverable": {{
        "content_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
        "platform_strategy": "Your platform recommendations",
        "implementation_timeline": "Your recommended timeline"
      }}
    }}

    🎯 **REPLACE THE PLACEHOLDER VALUES** with actual data from your analysis!
    """

        else:  # Generic report - MOST RELIABLE template
            return f"""
    **📊 COMPREHENSIVE PROJECT REPORT - EXACT JSON TEMPLATE:**

    Copy this EXACT template and fill in the data:

    {{
      "deliverable_type": "project_report",
      "executive_summary": "Write a comprehensive 2-3 paragraph summary of the entire project. Start with the business objective: '{goal}'. Describe the methodology, key activities completed, main findings, and business value delivered. This should be professional and client-ready.",
      "key_findings": [
        "Major finding or insight 1 from project analysis",
        "Important discovery or result 2 from completed tasks",
        "Key outcome or recommendation 3 from project work"
      ],
      "project_metrics": {{
        "total_tasks_completed": {aggregated_data.get('total_tasks', 0)},
        "data_quality_score": "{aggregated_data.get('data_quality_score', 0)}",
        "key_insights_generated": {len(aggregated_data.get('key_insights', []))},
        "completion_timeline": "X weeks/days"
      }},
      "final_deliverable": {{
        "business_value": "Describe the main business value delivered",
        "deliverables_produced": ["List main outputs created"],
        "recommended_next_steps": ["Immediate action 1", "Follow-up action 2"],
        "success_metrics": "How to measure success of this project"
      }}
    }}

    🎯 **CRITICAL INSTRUCTIONS:**
    1. Copy the template EXACTLY as shown above
    2. Replace ALL placeholder text with real data from your project analysis
    3. Ensure the executive_summary is compelling and comprehensive
    4. Include specific, actionable findings and recommendations
    5. Double-check that your JSON is valid (no syntax errors)

    🚨 **THIS IS THE FINAL PROJECT DELIVERABLE - MAKE IT EXCEPTIONAL!**
    """
    
    def _get_enhanced_output_schema_instructions(self, deliverable_type_value: str, aggregated_data: Dict, goal: str) -> str:
        """Get enhanced output schema with actual data integration"""

        import json

        # Enhanced schemas with real data integration
        if deliverable_type_value == "contact_list":
            structured_data = aggregated_data.get('structured_data', {})
            total_contacts = structured_data.get('total_contacts', 0)
            collection_methods = structured_data.get('collection_methods', [])
            contact_fields = structured_data.get('contact_fields', [])
            quality_score = aggregated_data.get('data_quality_score', 0)

            # Serialize lists properly for JSON
            collection_methods_json = json.dumps(collection_methods)
            contact_fields_json = json.dumps(contact_fields)

            return f"""
    **📞 CONTACT LIST DELIVERABLE REQUIREMENTS:**

    **Available Data:**
    - {total_contacts} contacts identified from project tasks
    - Collection methods: {', '.join(collection_methods)}

    **✅ REQUIRED OUTPUT in detailed_results_json:**
    {{
      "deliverable_type": "contact_list",
      "executive_summary": "Professional summary of contact list generation and quality.",
      "final_contact_list": [
        {{
          "name": "Contact Name",
          "company": "Company Name", 
          "email": "email@company.com",
          "phone": "+1-555-000-0000",
          "title": "Job Title",
          "source": "Task/Method that found this contact",
          "qualification_score": "8/10",
          "notes": "Relevant notes about this contact"
        }}
      ],
      "list_statistics": {{
        "total_contacts_generated": {total_contacts},
        "quality_score": "{quality_score}/100",
        "primary_sources": {collection_methods_json},
        "contact_fields_available": {contact_fields_json}
      }},
      "usage_recommendations": [
        "Prioritize contacts with highest qualification scores",
        "Segment by company size for targeted outreach",
        "Use personalized messaging based on source context"
      ]
    }}

    🎯 **CRITICAL:** Transform ALL contact data from aggregated_data into the final_contact_list!
    """

        elif deliverable_type_value == "content_strategy":
            structured_data = aggregated_data.get('structured_data', {})
            content_count = len(structured_data.get('content_ideas', []))
            strategies_count = len(structured_data.get('strategies', []))
            hashtags_count = len(structured_data.get('hashtags', []))
            content_ideas = structured_data.get('content_ideas', [])[:5]  # First 5 ideas
            hashtags = structured_data.get('hashtags', [])[:20]

            # Serialize lists properly for JSON  
            content_ideas_json = json.dumps(content_ideas)
            hashtags_json = json.dumps(hashtags)

            return f"""
    **📝 CONTENT STRATEGY DELIVERABLE REQUIREMENTS:**

    **Available Data:**
    - {content_count} content ideas generated
    - {strategies_count} strategy frameworks
    - Hashtags: {hashtags_count} identified

    **✅ REQUIRED OUTPUT in detailed_results_json:**
    {{
      "deliverable_type": "content_strategy",
      "executive_summary": "Comprehensive content strategy overview and objectives.",
      "content_pillars": ["Educational Content", "Brand Storytelling", "Community Engagement"],
      "content_calendar": [
        {{
          "month": "Current Month",
          "theme": "Monthly Theme",
          "content_pieces": {content_ideas_json}
        }}
      ],
      "platform_strategy": {{
        "instagram": "Strategy for Instagram based on analysis",
        "linkedin": "Professional content approach",
        "blog": "In-depth thought leadership"
      }},
      "recommended_hashtags": {hashtags_json},
      "performance_targets": {{
        "engagement_rate": "Target %",
        "reach_growth": "Monthly growth target",
        "lead_generation": "Leads per month target"
      }}
    }}

    🎯 **CRITICAL:** Integrate ALL content ideas and strategies from project analysis!
    """

        else:  # Generic report
            # FIX: Serialize complex data properly for JSON
            total_tasks = aggregated_data.get('total_tasks', 0)
            key_insights_count = len(aggregated_data.get('key_insights', []))
            quality_score = aggregated_data.get('data_quality_score', 0)
            key_insights = aggregated_data.get('key_insights', [])
            project_metrics = aggregated_data.get('project_metrics', {})
            recommendations = aggregated_data.get('recommendations', [])

            # Serialize complex data properly
            key_insights_json = json.dumps(key_insights)
            project_metrics_json = json.dumps(project_metrics)
            recommendations_json = json.dumps(recommendations)

            return f"""
    **📊 COMPREHENSIVE PROJECT REPORT REQUIREMENTS:**

    **Available Project Data:**
    - {total_tasks} completed tasks
    - {key_insights_count} key insights
    - Quality score: {quality_score}/100

    **✅ REQUIRED OUTPUT in detailed_results_json:**
    {{
      "deliverable_type": "project_report",
      "executive_summary": "2-3 sentence overview of project accomplishments and outcomes.",
      "project_goal_recap": "{goal}",
      "key_findings": {key_insights_json},
      "project_metrics": {project_metrics_json},
      "deliverables_produced": [
        {{
          "deliverable_name": "Name from task analysis",
          "description": "What was accomplished",
          "value_delivered": "Business impact"
        }}
      ],
      "final_recommendations": {recommendations_json},
      "implementation_next_steps": [
        "Immediate action item 1",
        "Follow-up action item 2"
      ],
      "project_success_metrics": {{
        "completion_rate": "X% of objectives achieved",
        "quality_score": "{quality_score}/100",
        "timeline_performance": "On schedule/Ahead/Behind"
      }}
    }}

    🎯 **CRITICAL:** Synthesize ALL project data into comprehensive final report!
    """
    
    async def _trigger_project_completion_sequence(self, workspace_id: str, deliverable_task_id: str):
        """
        ENHANCED: Trigger project completion sequence after deliverable creation
        """
        try:
            logger.info(f"🎯 COMPLETION SEQUENCE: Starting for workspace {workspace_id}")
            
            # Wait for deliverable task to complete (check periodically)
            max_wait_minutes = 30
            check_interval_seconds = 60
            
            for attempt in range(max_wait_minutes):
                await asyncio.sleep(check_interval_seconds)
                
                # Check if deliverable task is completed
                tasks = await list_tasks(workspace_id)
                deliverable_task = next((t for t in tasks if t.get("id") == deliverable_task_id), None)
                
                if not deliverable_task:
                    logger.warning(f"🎯 COMPLETION: Deliverable task {deliverable_task_id} not found")
                    break
                
                if deliverable_task.get("status") == "completed":
                    logger.info(f"🎯 COMPLETION: Deliverable task completed, triggering project completion")
                    
                    # Update workspace status to completed
                    await update_workspace_status(workspace_id, "completed")
                    
                    # Log completion
                    logger.critical(f"🎯 PROJECT COMPLETED: Workspace {workspace_id} automatically marked as completed")
                    break
                    
                elif deliverable_task.get("status") == "failed":
                    logger.error(f"🎯 COMPLETION: Deliverable task failed, not completing project")
                    break
            
        except Exception as e:
            logger.error(f"Error in project completion sequence: {e}")

# Global instance
deliverable_aggregator = EnhancedDeliverableAggregator()

# Helper function for integration
async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """
    FIXED: Helper function che utilizza l'istanza globale dell'aggregator
    """
    try:
        return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)
    except Exception as e:
        logger.error(f"Error in check_and_create_final_deliverable helper: {e}", exc_info=True)
        return None

    
async def verify_deliverable_completion(workspace_id: str, deliverable_task_id: str) -> bool:
    """Verify that the deliverable task was completed successfully with valid data"""
    try:
        return await deliverable_aggregator._verify_deliverable_completion(workspace_id, deliverable_task_id)
    except Exception as e:
        logger.error(f"Error in verify_deliverable_completion helper: {e}")
        return False
    
async def monitor_deliverable_completion(workspace_id: str, deliverable_task_id: str):
    """Monitor deliverable task completion and take action if it fails"""
    try:
        await deliverable_aggregator._monitor_deliverable_completion(workspace_id, deliverable_task_id)
    except Exception as e:
        logger.error(f"Error in monitor_deliverable_completion helper: {e}")
        
# === ENHANCED ASSET-ORIENTED DELIVERABLE SYSTEM ===

class SmartAssetExtractor:
    """Estrattore intelligente di asset azionabili dai task results"""
    
    def __init__(self):
        self.schema_generator = AssetSchemaGenerator()
        
    async def extract_actionable_assets(
        self, 
        completed_tasks: List[Dict], 
        asset_schemas: Dict[str, AssetSchema],
        workspace_id: str
    ) -> Dict[str, ExtractedAsset]:
        """
        Estrae asset azionabili validandoli contro gli schemi dinamici
        """
        
        extracted_assets = {}
        
        logger.info(f"🔍 ASSET EXTRACTION: Processing {len(completed_tasks)} completed tasks")
        
        # Identifica task di produzione asset
        asset_tasks = [
            task for task in completed_tasks 
            if self._is_asset_production_task(task)
        ]
        
        logger.info(f"🔍 ASSET TASKS: Found {len(asset_tasks)} asset production tasks")
        
        # Processa ogni task di asset production
        for task in asset_tasks:
            asset_type = self._identify_asset_type(task, asset_schemas)
            
            if asset_type and asset_type in asset_schemas:
                # Estrazione con validazione contro schema
                asset_data = await self._extract_and_validate_asset(
                    task, asset_schemas[asset_type]
                )
                
                if asset_data:
                    extracted_assets[asset_type] = asset_data
                    logger.info(f"✅ EXTRACTED: {asset_type} from task {task.get('id')}")
            else:
                # Tentativo di estrazione generica
                generic_asset = await self._extract_generic_asset(task)
                if generic_asset:
                    generic_name = f"generic_asset_{task.get('id', '')}"
                    extracted_assets[generic_name] = generic_asset
                    logger.info(f"✅ EXTRACTED GENERIC: {generic_name}")
        
        logger.info(f"🔍 EXTRACTION COMPLETE: {len(extracted_assets)} assets extracted")
        return extracted_assets
    
    def _is_asset_production_task(self, task: Dict) -> bool:
        """Determina se un task è di produzione asset"""
        
        # Metodo 1: Check context_data
        context_data = task.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            if context_data.get("asset_production") or context_data.get("asset_oriented_task"):
                return True
            
            # Check creation_type
            creation_type = context_data.get("creation_type", "")
            if creation_type in ["asset_production", "enhanced_pm_asset_tool"]:
                return True
        
        # Metodo 2: Check task name pattern
        task_name = (task.get("name") or "").upper()
        if "PRODUCE ASSET:" in task_name or "ASSET PRODUCTION:" in task_name:
            return True
        
        # Metodo 3: Check detailed_results_json per indicatori asset
        result = task.get("result", {}) or {}
        detailed_json = result.get("detailed_results_json", "")
        
        if detailed_json:
            # Look for structured asset patterns
            try:
                data = json.loads(detailed_json)
                if isinstance(data, dict):
                    # Check for asset-specific structures
                    asset_indicators = [
                        "contacts", "posts", "calendar", "exercises", "budget_categories",
                        "recommendations", "action_plan", "strategy", "database"
                    ]
                    
                    data_keys = set(str(k).lower() for k in data.keys())
                    if any(indicator in " ".join(data_keys) for indicator in asset_indicators):
                        return True
            except json.JSONDecodeError:
                pass
        
        return False
    
    def _identify_asset_type(self, task: Dict, asset_schemas: Dict[str, AssetSchema]) -> Optional[str]:
        """Identifica il tipo di asset prodotto dal task"""
        
        # Metodo 1: Esplicito dal context_data
        context_data = task.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            asset_type = context_data.get("asset_type") or context_data.get("target_schema")
            if asset_type and asset_type in asset_schemas:
                return asset_type
        
        # Metodo 2: Deduzione dal nome del task
        task_name = (task.get("name") or "").lower()
        for asset_type in asset_schemas.keys():
            asset_type_clean = asset_type.replace("_", " ")
            if asset_type_clean in task_name or asset_type in task_name:
                return asset_type
        
        # Metodo 3: Analisi del contenuto dell'output
        result = task.get("result", {}) or {}
        detailed_json = result.get("detailed_results_json", "")
        
        if detailed_json:
            try:
                data = json.loads(detailed_json)
                return self._infer_asset_type_from_content(data, asset_schemas)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _infer_asset_type_from_content(self, data: Dict, asset_schemas: Dict[str, AssetSchema]) -> Optional[str]:
        """Inferisce il tipo di asset dal contenuto"""
        
        if not isinstance(data, dict):
            return None
        
        data_keys = set(str(k).lower() for k in data.keys())
        content_indicators = {
            "content_calendar": ["posts", "calendar", "content", "schedule", "hashtags"],
            "qualified_contact_database": ["contacts", "leads", "email", "phone", "company"],
            "training_program": ["exercises", "workout", "training", "program", "sets", "reps"],
            "financial_model": ["revenue", "costs", "budget", "financial", "cash_flow"],
            "research_database": ["findings", "sources", "research", "data", "analysis"],
            "action_plan": ["tasks", "objectives", "plan", "milestones", "actions"]
        }
        
        best_match = None
        max_matches = 0
        
        for asset_type, indicators in content_indicators.items():
            if asset_type in asset_schemas:
                matches = sum(1 for indicator in indicators if indicator in " ".join(data_keys))
                if matches > max_matches:
                    max_matches = matches
                    best_match = asset_type
        
        return best_match if max_matches >= 2 else None
    
    async def _extract_and_validate_asset(self, task: Dict, schema: AssetSchema) -> Optional[ExtractedAsset]:
        """
        Estrae asset dal task result e lo valida contro lo schema
        """
        
        result = task.get("result", {}) or {}
        detailed_json = result.get("detailed_results_json", "")
        
        if not detailed_json:
            logger.warning(f"No detailed_results_json in task {task.get('id')}")
            return None
        
        try:
            # Parse JSON
            data = json.loads(detailed_json)
            
            if not isinstance(data, dict):
                logger.warning(f"Invalid data format in task {task.get('id')}")
                return None
            
            # Validazione contro schema
            validation_result = self.schema_generator.validate_asset_against_schema(data, schema)
            
            # Calcola actionability score
            actionability_score = self._calculate_actionability_score(data, schema, validation_result)
            
            # Determina se è ready to use
            ready_to_use = (
                validation_result.get("valid", False) and
                validation_result.get("completeness_score", 0) >= 0.8 and
                actionability_score >= 0.7
            )
            
            extracted_asset = ExtractedAsset(
                asset_name=schema.asset_name,
                asset_data=data,
                source_task_id=task.get("id", ""),
                extraction_method="schema_validation",
                validation_score=validation_result.get("completeness_score", 0),
                actionability_score=actionability_score,
                ready_to_use=ready_to_use
            )
            
            return extracted_asset
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in task {task.get('id')}: {e}")
            # Tentativo di estrazione da testo non strutturato
            return await self._extract_from_unstructured_text(
                result.get("summary", ""), schema, task.get("id", "")
            )
        except Exception as e:
            logger.error(f"Error extracting asset from task {task.get('id')}: {e}")
            return None
    
    async def _extract_from_unstructured_text(self, text: str, schema: AssetSchema, task_id: str) -> Optional[ExtractedAsset]:
        """
        Estrae asset da testo non strutturato (fallback)
        """
        
        if not text or len(text) < 50:
            return None
        
        # Extraction pattern molto semplice per ora
        # In implementazione completa, userebbe NLP o LLM per estrazione
        extracted_data = {
            "extracted_from_text": True,
            "original_text": text[:1000],  # Primi 1000 caratteri
            "extraction_method": "text_fallback",
            "confidence": "low"
        }
        
        # Cerca pattern specifici nel testo
        if "contact" in text.lower() or "email" in text.lower():
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if emails:
                extracted_data["extracted_emails"] = emails
        
        if "http" in text.lower():
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            if urls:
                extracted_data["extracted_urls"] = urls
        
        return ExtractedAsset(
            asset_name=schema.asset_name,
            asset_data=extracted_data,
            source_task_id=task_id,
            extraction_method="text_fallback",
            validation_score=0.3,  # Basso per text extraction
            actionability_score=0.3,
            ready_to_use=False
        )
    
    async def _extract_generic_asset(self, task: Dict) -> Optional[ExtractedAsset]:
        """
        Estrazione generica per task non identificati come asset specifici
        """
        
        result = task.get("result", {}) or {}
        detailed_json = result.get("detailed_results_json", "")
        summary = result.get("summary", "")
        
        if not detailed_json and not summary:
            return None
        
        asset_data = {}
        
        # Estrai da detailed_results_json se disponibile
        if detailed_json:
            try:
                parsed_data = json.loads(detailed_json)
                if isinstance(parsed_data, dict):
                    asset_data.update(parsed_data)
            except json.JSONDecodeError:
                asset_data["unparsed_json"] = detailed_json
        
        # Aggiungi summary
        if summary:
            asset_data["task_summary"] = summary
        
        # Metadati del task
        asset_data["task_metadata"] = {
            "task_name": task.get("name", ""),
            "task_id": task.get("id", ""),
            "assigned_to_role": task.get("assigned_to_role", ""),
            "completed_at": task.get("updated_at", "")
        }
        
        if not asset_data:
            return None
        
        return ExtractedAsset(
            asset_name="generic_output",
            asset_data=asset_data,
            source_task_id=task.get("id", ""),
            extraction_method="generic_fallback",
            validation_score=0.5,
            actionability_score=0.4,
            ready_to_use=False
        )
    
    def _calculate_actionability_score(
        self, 
        data: Dict, 
        schema: AssetSchema, 
        validation_result: Dict
    ) -> float:
        """
        Calcola score di azionabilità (0.0 - 1.0)
        """
        
        score = 0.0
        
        # Base score dalla completeness
        completeness = validation_result.get("completeness_score", 0)
        score += completeness * 0.4
        
        # Bonus per assenza di placeholder
        if not self._has_placeholders(data):
            score += 0.2
        
        # Bonus per presenza di dati azionabili
        if self._has_actionable_data(data):
            score += 0.2
        
        # Bonus per automation readiness
        if schema.automation_ready and self._is_automation_compatible(data):
            score += 0.2
        
        return min(1.0, score)
    
    def _has_placeholders(self, data: Dict, depth: int = 0) -> bool:
        """Verifica presenza di placeholder nei dati"""
        
        if depth > 3:  # Limite ricorsione
            return False
        
        placeholders = ["string", "number", "tbd", "todo", "placeholder", "example", "sample"]
        
        for key, value in data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if any(placeholder in value_lower for placeholder in placeholders):
                    return True
            elif isinstance(value, dict):
                if self._has_placeholders(value, depth + 1):
                    return True
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                if self._has_placeholders(value[0], depth + 1):
                    return True
        
        return False
    
    def _has_actionable_data(self, data: Dict) -> bool:
        """Verifica presenza di dati azionabili"""
        
        # Indicatori di dati azionabili
        actionable_indicators = [
            "@",  # Email
            "http",  # URL
            "phone",  # Telefono
            "date",  # Date
            "$",  # Valori monetari
            "%"   # Percentuali
        ]
        
        data_str = json.dumps(data).lower()
        return any(indicator in data_str for indicator in actionable_indicators)
    
    def _is_automation_compatible(self, data: Dict) -> bool:
        """Verifica compatibilità con automazione"""
        
        # Criteri per automation compatibility
        has_structured_lists = any(isinstance(v, list) and v for v in data.values())
        has_consistent_fields = len(data) >= 3  # Almeno 3 campi
        has_identifiers = any(key in str(data).lower() for key in ["id", "email", "name", "date"])
        
        return has_structured_lists and has_consistent_fields and has_identifiers


class EnhancedDeliverablePackager:
    """Assembla deliverable finali con asset azionabili"""
    
    def __init__(self):
        self.requirements_analyzer = DeliverableRequirementsAnalyzer()
    
    async def create_actionable_deliverable(
        self,
        workspace_id: str,
        workspace_goal: str,
        extracted_assets: Dict[str, ExtractedAsset],
        requirements: Optional[Dict] = None
    ) -> ActionableDeliverable:
        """
        Crea deliverable finale con asset azionabili integrato
        """
        
        # Genera executive summary dinamico
        executive_summary = await self._generate_dynamic_executive_summary(
            workspace_goal, extracted_assets
        )
        
        # Genera usage guide
        usage_guide = self._generate_comprehensive_usage_guide(extracted_assets)
        
        # Genera next steps azionabili
        next_steps = self._generate_actionable_next_steps(extracted_assets)
        
        # Calcola automation readiness complessiva
        automation_ready = self._calculate_overall_automation_readiness(extracted_assets)
        
        # Calcola actionability score complessivo
        actionability_score = self._calculate_overall_actionability_score(extracted_assets)
        
        deliverable = ActionableDeliverable(
            workspace_id=workspace_id,
            deliverable_id=f"deliverable_{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            meta={
                "project_goal": workspace_goal,
                "total_assets": len(extracted_assets),
                "ready_to_use_assets": sum(1 for asset in extracted_assets.values() if asset.ready_to_use),
                "generation_method": "enhanced_asset_oriented",
                "requirements_used": requirements is not None
            },
            executive_summary=executive_summary,
            actionable_assets=extracted_assets,
            usage_guide=usage_guide,
            next_steps=next_steps,
            automation_ready=automation_ready,
            actionability_score=actionability_score
        )
        
        logger.info(f"🎯 DELIVERABLE CREATED: {actionability_score}/100 actionability score, "
                   f"{len(extracted_assets)} assets, automation: {automation_ready}")
        
        return deliverable
    
    async def _generate_dynamic_executive_summary(
        self, 
        workspace_goal: str, 
        extracted_assets: Dict[str, ExtractedAsset]
    ) -> str:
        """
        Genera executive summary dinamico basato sugli asset estratti
        """
        
        total_assets = len(extracted_assets)
        ready_assets = sum(1 for asset in extracted_assets.values() if asset.ready_to_use)
        avg_actionability = sum(asset.actionability_score for asset in extracted_assets.values()) / total_assets if total_assets > 0 else 0
        
        # Asset breakdown
        asset_types = list(extracted_assets.keys())
        
        summary = f"""**Project Objective Achievement Summary**

**Goal:** {workspace_goal}

**Deliverable Overview:**
This project has successfully produced {total_assets} actionable business assets, with {ready_assets} assets ready for immediate implementation. The overall actionability score is {avg_actionability:.1%}, indicating {self._get_actionability_rating(avg_actionability)} business readiness.

**Key Assets Delivered:**
{self._format_asset_list(extracted_assets)}

**Business Impact:**
The delivered assets provide immediate value through {self._describe_business_impact(extracted_assets)}. These deliverables are designed for direct implementation and can generate measurable business outcomes within the first 30 days of deployment.

**Implementation Readiness:**
{ready_assets}/{total_assets} assets are ready for immediate use without modification. The remaining assets require minimal customization and can be implemented with standard business processes.
"""
        
        return summary.strip()
    
    def _get_actionability_rating(self, score: float) -> str:
        """Converte score in rating testuale"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "moderate"
        else:
            return "basic"
    
    def _format_asset_list(self, assets: Dict[str, ExtractedAsset]) -> str:
        """Formatta lista asset per executive summary"""
        
        asset_lines = []
        for name, asset in assets.items():
            status = "✅ Ready to use" if asset.ready_to_use else "🔧 Needs customization"
            asset_lines.append(f"- **{name.replace('_', ' ').title()}**: {status} (Actionability: {asset.actionability_score:.0%})")
        
        return "\n".join(asset_lines)
    
    def _describe_business_impact(self, assets: Dict[str, ExtractedAsset]) -> str:
        """Descrive l'impatto business degli asset"""
        
        impact_areas = []
        
        for name, asset in assets.items():
            if "contact" in name or "lead" in name:
                impact_areas.append("lead generation and sales pipeline development")
            elif "content" in name or "calendar" in name:
                impact_areas.append("marketing campaign execution and content strategy")
            elif "training" in name or "program" in name:
                impact_areas.append("performance improvement and skill development")
            elif "financial" in name or "budget" in name:
                impact_areas.append("financial planning and resource optimization")
            elif "research" in name or "analysis" in name:
                impact_areas.append("data-driven decision making and strategic insights")
        
        if not impact_areas:
            impact_areas.append("operational efficiency and strategic execution")
        
        return ", ".join(set(impact_areas))
    
    def _generate_comprehensive_usage_guide(self, assets: Dict[str, ExtractedAsset]) -> Dict[str, str]:
        """Genera usage guide completa per tutti gli asset"""
        
        usage_guide = {}
        
        for name, asset in assets.items():
            if asset.ready_to_use:
                guide = f"✅ **Ready for immediate use**: This {name.replace('_', ' ')} can be implemented directly. "
            else:
                guide = f"🔧 **Requires customization**: Review and adapt this {name.replace('_', ' ')} to your specific context. "
            
            # Aggiungi istruzioni specifiche basate sul tipo
            if "contact" in name:
                guide += "Import into your CRM system and begin outreach campaigns. Prioritize contacts with highest qualification scores."
            elif "content" in name:
                guide += "Load into your content management tool and schedule posts according to the recommended timeline."
            elif "calendar" in name:
                guide += "Import into your scheduling system and set up automated posting if available."
            elif "training" in name:
                guide += "Begin implementation following the structured program timeline. Track progress using provided metrics."
            elif "financial" in name:
                guide += "Review assumptions, customize for your business model, and use for budget planning and investor presentations."
            else:
                guide += "Follow the structured format and adapt content to your specific business requirements."
            
            usage_guide[name] = guide
        
        return usage_guide
    
    def _generate_actionable_next_steps(self, assets: Dict[str, ExtractedAsset]) -> List[str]:
        """Genera next steps azionabili"""
        
        next_steps = []
        
        # Step 1: Immediate actions
        ready_assets = [name for name, asset in assets.items() if asset.ready_to_use]
        if ready_assets:
            next_steps.append(f"IMMEDIATE (Week 1): Implement ready-to-use assets: {', '.join(ready_assets[:3])}")
        
        # Step 2: Customization needed
        custom_assets = [name for name, asset in assets.items() if not asset.ready_to_use]
        if custom_assets:
            next_steps.append(f"SHORT-TERM (Week 2-3): Customize and deploy: {', '.join(custom_assets[:3])}")
        
        # Step 3: Monitoring and optimization
        if len(assets) > 0:
            next_steps.append("ONGOING (Month 1+): Monitor performance metrics and optimize based on results")
        
        # Step 4: Asset-specific recommendations
        for name, asset in assets.items():
            if "contact" in name and asset.ready_to_use:
                next_steps.append(f"Contact Strategy: Begin outreach to top-qualified leads from {name}")
            elif "content" in name and asset.ready_to_use:
                next_steps.append(f"Content Execution: Schedule first month of posts from {name}")
        
        return next_steps
    
    def _calculate_overall_automation_readiness(self, assets: Dict[str, ExtractedAsset]) -> bool:
        """Calcola automation readiness complessiva"""
        
        if not assets:
            return False
        
        automation_scores = []
        for asset in assets.values():
            # Considera automation ready se ha score alto e structured data
            score = 0
            if asset.actionability_score >= 0.7:
                score += 0.5
            if asset.ready_to_use:
                score += 0.3
            if isinstance(asset.asset_data, dict) and len(asset.asset_data) >= 3:
                score += 0.2
            
            automation_scores.append(score)
        
        avg_automation_score = sum(automation_scores) / len(automation_scores)
        return avg_automation_score >= 0.6  # 60% threshold
    
    def _calculate_overall_actionability_score(self, assets: Dict[str, ExtractedAsset]) -> int:
        """Calcola actionability score complessivo (0-100)"""
        
        if not assets:
            return 0
        
        # Media ponderata degli score individuali
        total_score = sum(asset.actionability_score for asset in assets.values())
        avg_score = total_score / len(assets)
        
        # Bonus per diversità di asset
        diversity_bonus = min(len(assets) * 0.05, 0.2)  # Max 20% bonus
        
        # Bonus per asset ready-to-use
        ready_ratio = sum(1 for asset in assets.values() if asset.ready_to_use) / len(assets)
        ready_bonus = ready_ratio * 0.15  # Max 15% bonus
        
        final_score = (avg_score + diversity_bonus + ready_bonus) * 100
        return min(100, int(final_score))


# === INTEGRATION WITH EXISTING ENHANCED DELIVERABLE AGGREGATOR ===

# Estendi la classe esistente EnhancedDeliverableAggregator
class AssetOrientedDeliverableAggregator(EnhancedDeliverableAggregator):
    """
    Estensione della classe esistente per supportare asset-oriented deliverables
    Mantiene backward compatibility completa
    """
    
    def __init__(self):
        super().__init__()
        self.asset_extractor = SmartAssetExtractor()
        self.asset_packager = EnhancedDeliverablePackager()
        self.requirements_analyzer = DeliverableRequirementsAnalyzer()
        self.schema_generator = AssetSchemaGenerator()
        
        logger.info("Asset-oriented deliverable aggregator initialized")
    
    async def check_and_create_final_deliverable(self, workspace_id: str) -> Optional[str]:
        """
        ENHANCED VERSION: Controlla e crea deliverable con asset azionabili
        Fallback alla versione originale se asset-oriented approach fallisce
        """
        
        try:
            logger.info(f"🎯 ENHANCED DELIVERABLE CHECK: Starting asset-oriented approach for {workspace_id}")
            
            # Prima controlla readiness con logica esistente (mantiene compatibilità)
            if not await self._is_ready_for_final_deliverable_enhanced(workspace_id):
                logger.debug(f"🎯 NOT READY: Workspace {workspace_id} (using enhanced criteria)")
                return None
            
            # Controlla se deliverable esiste già
            if await self._final_deliverable_exists_enhanced(workspace_id):
                logger.info(f"🎯 EXISTS: Final deliverable already exists for {workspace_id}")
                return None
            
            # Tentativo asset-oriented approach
            try:
                asset_deliverable_id = await self._create_asset_oriented_deliverable(workspace_id)
                if asset_deliverable_id:
                    logger.critical(f"🎯 SUCCESS: Asset-oriented deliverable created: {asset_deliverable_id}")
                    return asset_deliverable_id
            except Exception as e:
                logger.warning(f"Asset-oriented approach failed: {e}, falling back to original method")
            
            # Fallback alla versione originale
            logger.info(f"🎯 FALLBACK: Using original deliverable approach for {workspace_id}")
            return await super().check_and_create_final_deliverable(workspace_id)
            
        except Exception as e:
            logger.error(f"Error in enhanced deliverable check: {e}", exc_info=True)
            return None
    
    async def _create_asset_oriented_deliverable(self, workspace_id: str) -> Optional[str]:
        """
        Crea deliverable usando il nuovo approccio asset-oriented
        """
        
        # 1. Analizza requirements dinamicamente
        requirements = await self.requirements_analyzer.analyze_deliverable_requirements(workspace_id)
        
        # 2. Genera schemi per asset
        asset_schemas = await self.schema_generator.generate_asset_schemas(requirements)
        
        # 3. Raccogli task completati
        workspace = await get_workspace(workspace_id)
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        if len(completed_tasks) < 2:
            logger.warning(f"Insufficient completed tasks for asset extraction: {len(completed_tasks)}")
            raise ValueError("Insufficient completed tasks")
        
        # 4. Estrai asset azionabili
        extracted_assets = await self.asset_extractor.extract_actionable_assets(
            completed_tasks, asset_schemas, workspace_id
        )
        
        if not extracted_assets:
            logger.warning(f"No actionable assets extracted from {len(completed_tasks)} tasks")
            raise ValueError("No actionable assets extracted")
        
        # 5. Crea deliverable finale
        actionable_deliverable = await self.asset_packager.create_actionable_deliverable(
            workspace_id,
            workspace.get("goal", ""),
            extracted_assets,
            requirements.model_dump()
        )
        
        # 6. Crea task deliverable nel database
        deliverable_task_id = await self._create_asset_deliverable_task(
            workspace_id, workspace, actionable_deliverable
        )
        
        return deliverable_task_id
    
    async def _create_asset_deliverable_task(
        self,
        workspace_id: str,
        workspace: Dict,
        actionable_deliverable: ActionableDeliverable
    ) -> Optional[str]:
        """
        Crea task deliverable con asset azionabili
        """
        
        try:
            # Trova agente per deliverable (usa logica esistente)
            agents = await list_agents(workspace_id)
            deliverable_agent = await self._find_best_deliverable_agent(
                agents, DeliverableType.GENERIC_REPORT  # Fallback type
            )
            
            if not deliverable_agent:
                logger.error(f"No suitable agent for asset deliverable in {workspace_id}")
                return None
            
            # Crea descrizione arricchita
            description = self._create_asset_deliverable_description(
                workspace.get("goal", ""), actionable_deliverable
            )
            
            # Nome task con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            task_name = f"🎯 FINAL ASSET-READY DELIVERABLE ({timestamp})"
            
            # Context data arricchito
            context_data = {
                "is_final_deliverable": True,
                "deliverable_aggregation": True,
                "asset_oriented_deliverable": True,
                "deliverable_type": "asset_ready_package",
                "project_phase": "FINALIZATION",
                "actionability_score": actionable_deliverable.actionability_score,
                "automation_ready": actionable_deliverable.automation_ready,
                "total_assets": len(actionable_deliverable.actionable_assets),
                "ready_to_use_assets": sum(1 for asset in actionable_deliverable.actionable_assets.values() if asset.ready_to_use),
                "workspace_goal": workspace.get("goal", ""),
                "creation_timestamp": datetime.now().isoformat(),
                "triggers_project_completion": True,
                "enhanced_deliverable_version": "3.0_asset_oriented"
            }
            
            # Serializza actionable_deliverable per il task
            deliverable_json = actionable_deliverable.model_dump()
            
            # Crea task con FIXED priority
            deliverable_task = await create_task(
                workspace_id=workspace_id,
                agent_id=deliverable_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority="high",  # FIXED: Use valid priority value
                creation_type="asset_oriented_deliverable",
                context_data={
                    **context_data,
                    "precomputed_deliverable": deliverable_json  # Include pre-computed deliverable
                }
            )
            
            if deliverable_task and deliverable_task.get("id"):
                logger.critical(f"🎯 ASSET DELIVERABLE CREATED: {deliverable_task['id']} "
                               f"with {actionable_deliverable.actionability_score}/100 actionability")
                return deliverable_task["id"]
            else:
                logger.error(f"Failed to create asset deliverable task in database")
                return None
                
        except Exception as e:
            logger.error(f"Error creating asset deliverable task: {e}", exc_info=True)
            return None
    
    def _create_asset_deliverable_description(
        self,
        goal: str,
        actionable_deliverable: ActionableDeliverable
    ) -> str:
        """
        Crea descrizione per il task deliverable con asset azionabili
        """
        
        total_assets = len(actionable_deliverable.actionable_assets)
        ready_assets = sum(1 for asset in actionable_deliverable.actionable_assets.values() if asset.ready_to_use)
        
        description = f"""🎯 **FINAL ASSET-READY DELIVERABLE COMPILATION**

**PROJECT OBJECTIVE:** {goal}

**📦 PRE-COMPUTED DELIVERABLE PACKAGE:**
This task contains a pre-computed deliverable package with {total_assets} actionable business assets.
Your job is to format and present this package as the final project deliverable.

**📊 ASSET INVENTORY:**
- Total Assets: {total_assets}
- Ready-to-Use: {ready_assets}
- Actionability Score: {actionable_deliverable.actionability_score}/100
- Automation Ready: {"Yes" if actionable_deliverable.automation_ready else "No"}

**🎯 YOUR TASK:**
1. Review the pre-computed deliverable data in your context
2. Format it into a professional, client-ready presentation
3. Ensure all assets are properly documented with usage instructions
4. Create an executive summary that highlights business value
5. Package everything into a comprehensive final deliverable

**✅ REQUIRED OUTPUT FORMAT:**
Your detailed_results_json must contain:
```json
{{
  "deliverable_type": "asset_ready_package",
  "executive_summary": "Professional 2-3 paragraph summary of deliverable value",
  "actionable_assets": {{
    "asset_name": {{
      "data": "Complete asset data ready for use",
      "usage_instructions": "How to implement this asset",
      "business_value": "Expected impact and ROI",
      "automation_potential": "How this can be automated"
    }}
  }},
  "implementation_guide": {{
    "immediate_actions": ["Week 1 actions"],
    "short_term_goals": ["Month 1 goals"], 
    "success_metrics": ["How to measure success"]
  }},
  "business_impact_projection": {{
    "time_to_value": "Expected timeline for ROI",
    "estimated_impact": "Projected business outcomes",
    "automation_savings": "Efficiency gains from automation"
  }}
}}
```

**🚨 CRITICAL REQUIREMENTS:**
- All assets must be immediately actionable (ready-to-copy-paste)
- Include specific implementation steps for each asset
- Provide clear ROI projections and success metrics
- Ensure professional presentation suitable for client delivery
- This is the FINAL deliverable - make it exceptional

**📋 SUCCESS CRITERIA:**
✅ Professional executive summary highlighting business value
✅ All assets formatted for immediate business use  
✅ Clear implementation roadmap with timelines
✅ Measurable success criteria and ROI projections
✅ Ready for client presentation and implementation
"""
        
        return description.strip()


# === GLOBAL INSTANCE REPLACEMENT ===

# Sostituisci l'istanza globale con la versione asset-oriented
deliverable_aggregator = AssetOrientedDeliverableAggregator()

# Mantieni backward compatibility per la funzione helper esistente
async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """
    ENHANCED: Helper function che usa il nuovo sistema asset-oriented
    Mantiene backward compatibility completa
    """
    try:
        return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)
    except Exception as e:
        logger.error(f"Error in enhanced check_and_create_final_deliverable: {e}", exc_info=True)
        return None