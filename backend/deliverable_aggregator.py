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
            
            # Enhanced task name with type and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            task_name = f"🎯 FINAL DELIVERABLE: {deliverable_type.value.replace('_', ' ').title()} ({timestamp})"
            
            # Create the deliverable task
            deliverable_task = await create_task(
                workspace_id=workspace_id,
                agent_id=deliverable_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority="high",
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
                    "agent_selection_reason": f"Selected {deliverable_agent['name']} for {deliverable_type.value}"
                }
            )
            
            if deliverable_task and deliverable_task.get("id"):
                logger.critical(f"🎯 DELIVERABLE CREATED: {deliverable_task['id']} "
                               f"assigned to {deliverable_agent['name']} "
                               f"for type {deliverable_type.value}")
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
            """Create comprehensive deliverable description with all aggregated data"""

            # Enhanced base context with quality metrics
            quality_score = aggregated_data.get("data_quality_score", 0)
            total_tasks = aggregated_data.get("total_tasks", 0)

            base_context = f"""🎯 **FINAL PROJECT DELIVERABLE CREATION**

    **PROJECT OBJECTIVE:** {goal}

    **📊 AGGREGATED PROJECT DATA SUMMARY:**
    - Total completed tasks analyzed: {total_tasks}
    - Data quality score: {quality_score}/100
    - Task summaries: {len(aggregated_data.get('task_summaries', []))}
    - Key insights extracted: {len(aggregated_data.get('key_insights', []))}
    - Structured data sources: {aggregated_data.get('structured_data', {}).get('num_data_sources', 0)}

    **🎯 YOUR MISSION:** 
    Create the FINAL, CLIENT-READY deliverable that comprehensively addresses the project objective. 
    Use ALL the aggregated data provided in the context_data of this task to create a polished, 
    professional deliverable that synthesizes the entire project's work.

    **📋 DELIVERABLE TYPE:** {deliverable_type.value.replace('_', ' ').title()}
    """

            # Type-specific instructions with enhanced schema
            type_specific = self._get_enhanced_output_schema_instructions(deliverable_type.value, aggregated_data, goal)

            return base_context + type_specific
    
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
    """Enhanced wrapper function for integration"""
    return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)