#!/usr/bin/env python3
"""
🎯 MISSING DELIVERABLE AUTO-COMPLETION SYSTEM

Automatically detects and completes missing deliverables for goals that should be finished.
Provides unblock mechanisms for stuck tasks and manual intervention options.
"""

import logging
import asyncio
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from uuid import UUID

from database import (
    get_workspace_goals, 
    list_tasks,
    create_task, 
    get_deliverables,
    get_workspace,
    update_task_fields,
    get_task,
    update_task_status
)
from models import Task, TaskStatus
from services.enhanced_goal_driven_planner import EnhancedGoalDrivenPlanner
from services.api_rate_limiter import api_rate_limiter
from executor import start_task_executor

logger = logging.getLogger(__name__)

class MissingDeliverableDetection:
    """Detects missing deliverables for goals"""
    
    def __init__(self):
        # CONFIGURATION EXTERNALIZED: Load from environment with fallbacks
        self.completion_threshold = float(os.getenv('DELIVERABLE_COMPLETION_THRESHOLD', '60.0'))
        
        # Default deliverable templates - can be overridden via environment
        default_templates = {
            'content_creation': ['content_strategy', 'content_pieces', 'distribution_plan'],
            'marketing_campaign': ['campaign_strategy', 'content_assets', 'performance_tracking'],
            'website_development': ['site_structure', 'content_pages', 'functionality_testing'],
            'email_marketing': ['email_sequences', 'automation_setup', 'performance_analytics']
        }
        
        # Allow environment override of deliverable templates
        env_templates = os.getenv('DELIVERABLE_TEMPLATES_JSON')
        if env_templates:
            try:
                self.expected_deliverables_per_goal = json.loads(env_templates)
                logger.info("✅ CONFIGURED: Loaded deliverable templates from environment")
            except json.JSONDecodeError:
                logger.warning("⚠️ Invalid DELIVERABLE_TEMPLATES_JSON, using defaults")
                self.expected_deliverables_per_goal = default_templates
        else:
            self.expected_deliverables_per_goal = default_templates
            
        logger.info(f"✅ CONFIGURED: Completion threshold: {self.completion_threshold}%, Templates: {len(self.expected_deliverables_per_goal)} types")
        
    async def detect_missing_deliverables(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Detect goals with missing deliverables"""
        try:
            # Get workspace goals
            goals = await get_workspace_goals(workspace_id)
            missing_deliverables = []
            
            for goal in goals:
                goal_id = goal.get('id')
                goal_title = goal.get('metric_type', 'Unknown Goal')
                current_value = goal.get('current_value', 0)
                target_value = goal.get('target_value', 1)
                
                # Calculate progress
                progress_percentage = (current_value / max(target_value, 1)) * 100
                
                # Only check goals with significant progress
                if progress_percentage >= self.completion_threshold:
                    # Get existing deliverables for this goal
                    existing_deliverables = await self._get_goal_deliverables(workspace_id, goal_id)
                    
                    # Determine expected deliverables based on goal type
                    expected = self._get_expected_deliverables_for_goal(goal_title)
                    
                    # Find missing deliverables
                    missing = self._find_missing_deliverables(existing_deliverables, expected)
                    
                    if missing:
                        # Check if goal is blocked or can auto-complete
                        can_auto_complete, blocked_reason = await self._can_auto_complete_goal(workspace_id, goal_id)
                        
                        missing_deliverables.append({
                            'goal_id': goal_id,
                            'goal_title': goal_title,
                            'progress_percentage': progress_percentage,
                            'missing_deliverables': missing,
                            'can_auto_complete': can_auto_complete,
                            'blocked_reason': blocked_reason,
                            'existing_deliverables_count': len(existing_deliverables),
                            'expected_deliverables_count': len(expected)
                        })
            
            logger.info(f"✅ Detected {len(missing_deliverables)} goals with missing deliverables")
            return missing_deliverables
            
        except Exception as e:
            logger.error(f"❌ Error detecting missing deliverables: {e}")
            return []
    
    async def _get_goal_deliverables(self, workspace_id: str, goal_id: str) -> List[Dict[str, Any]]:
        """Get existing deliverables for a specific goal - SDK COMPLIANT"""
        try:
            # Use SDK-compliant function instead of direct database access
            all_deliverables = await get_deliverables(workspace_id)
            
            # Filter deliverables related to this goal
            goal_deliverables = []
            for deliverable in all_deliverables:
                # Check if deliverable is linked to this goal
                metadata = deliverable.get('metadata', {})
                if metadata.get('goal_id') == goal_id:
                    goal_deliverables.append(deliverable)
            
            logger.info(f"✅ SDK COMPLIANT: Retrieved {len(goal_deliverables)} deliverables for goal {goal_id}")
            return goal_deliverables
            
        except Exception as e:
            logger.error(f"❌ Error getting goal deliverables: {e}")
            return []
    
    def _get_expected_deliverables_for_goal(self, goal_title: str) -> List[str]:
        """Determine expected deliverables based on goal type"""
        goal_title_lower = goal_title.lower()
        
        # Pattern matching for goal types
        if any(keyword in goal_title_lower for keyword in ['email', 'newsletter', 'sequence']):
            return self.expected_deliverables_per_goal.get('email_marketing', ['email_sequence_1', 'email_sequence_2', 'email_sequence_3'])
        elif any(keyword in goal_title_lower for keyword in ['content', 'blog', 'article']):
            return self.expected_deliverables_per_goal.get('content_creation', ['content_strategy', 'content_pieces'])
        elif any(keyword in goal_title_lower for keyword in ['marketing', 'campaign', 'promotion']):
            return self.expected_deliverables_per_goal.get('marketing_campaign', ['campaign_strategy', 'marketing_assets'])
        elif any(keyword in goal_title_lower for keyword in ['website', 'site', 'web']):
            return self.expected_deliverables_per_goal.get('website_development', ['website_structure', 'website_content'])
        
        # CONFIGURED: Default deliverables for unrecognized goals
        default_count = int(os.getenv('DEFAULT_DELIVERABLES_COUNT', '3'))
        return [f'deliverable_{i+1}' for i in range(default_count)]
    
    def _find_missing_deliverables(self, existing: List[Dict[str, Any]], expected: List[str]) -> List[str]:
        """Find which expected deliverables are missing"""
        existing_titles = set()
        for deliverable in existing:
            title = deliverable.get('title', '').lower()
            existing_titles.add(title)
        
        missing = []
        for expected_deliverable in expected:
            # Check if this expected deliverable exists (fuzzy matching)
            if not any(expected_deliverable.lower() in existing_title for existing_title in existing_titles):
                missing.append(expected_deliverable.replace('_', ' ').title())
        
        return missing
    
    async def _can_auto_complete_goal(self, workspace_id: str, goal_id: str) -> Tuple[bool, Optional[str]]:
        """Check if goal can be auto-completed or if it's blocked"""
        try:
            # Get goal tasks to check for blocks
            tasks = await list_tasks(workspace_id, goal_id=goal_id)
            
            # Check for blocking conditions
            failed_tasks = [t for t in tasks if t.get('status') == TaskStatus.FAILED.value]
            pending_human_feedback = [t for t in tasks if 'human_feedback' in t.get('name', '').lower() and t.get('status') == TaskStatus.PENDING.value]
            
            if failed_tasks:
                return False, f"{len(failed_tasks)} tasks have failed and need attention"
            
            if pending_human_feedback:
                return False, f"Waiting for human feedback on {len(pending_human_feedback)} tasks"
            
            # Check workspace health
            workspace = await get_workspace(workspace_id)
            if not workspace:
                return False, "Workspace not accessible"
            
            workspace_status = workspace.get('status', '')
            if workspace_status in ['paused', 'error', 'maintenance']:
                return False, f"Workspace is in {workspace_status} state"
            
            # If no blocking conditions, goal can auto-complete
            return True, None
            
        except Exception as e:
            logger.error(f"❌ Error checking goal auto-completion: {e}")
            return False, "System error - cannot determine completion status"


class MissingDeliverableAutoCompleter:
    """Automatically completes missing deliverables"""
    
    def __init__(self):
        self.detection_system = MissingDeliverableDetection()
        
    async def auto_complete_missing_deliverable(
        self, 
        workspace_id: str, 
        goal_id: str, 
        deliverable_name: str
    ) -> Dict[str, Any]:
        """Auto-complete a specific missing deliverable with rate limiting"""
        # RATE LIMITING: Acquire permit for auto-completion operations
        try:
            await api_rate_limiter.acquire("auto_completion", "high")
            logger.info(f"✅ RATE LIMITED: Acquired permit for auto-completion operation")
        except Exception as e:
            logger.error(f"🚫 RATE LIMIT ERROR: {e}")
            return {
                'success': False,
                'error': 'Rate limit exceeded - please try again later',
                'requires_manual_intervention': True
            }
        
        try:
            logger.info(f"🚀 Auto-completing missing deliverable: {deliverable_name} for goal {goal_id}")
            
            # First check if goal can be auto-completed
            can_complete, blocked_reason = await self.detection_system._can_auto_complete_goal(workspace_id, goal_id)
            
            if not can_complete:
                return {
                    'success': False,
                    'error': f'Goal is blocked: {blocked_reason}',
                    'requires_manual_intervention': True
                }
            
            # Get goal-driven planner
            goal_planner = EnhancedGoalDrivenPlanner()
            
            # Create completion task
            task_data = {
                'name': f'Complete missing deliverable: {deliverable_name}',
                'description': f'Auto-generated task to complete the missing deliverable "{deliverable_name}" for goal completion',
                'workspace_id': workspace_id,
                'goal_id': goal_id,
                'priority': "high",  # High priority for completion tasks
                'task_type': 'deliverable_completion',
                'metadata': {
                    'auto_generated': True,
                    'deliverable_name': deliverable_name,
                    'completion_reason': 'missing_deliverable_auto_completion',
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Use goal-driven planner to create and assign the task
            completion_tasks = await goal_planner._create_goal_driven_tasks(
                workspace_id=workspace_id,
                goal_requirements=[{
                    'requirement': f'Create and deliver: {deliverable_name}',
                    'priority': 'high',
                    'deliverable_type': 'content_asset'
                }],
                context={'auto_completion': True, 'goal_id': goal_id}
            )
            
            if completion_tasks:
                task_executor = start_task_executor()
                # Execute the completion task immediately
                execution_result = await task_executor.process_single_task(completion_tasks[0])
                
                return {
                    'success': True,
                    'task_id': completion_tasks[0].id,
                    'execution_result': execution_result,
                    'message': f'Successfully auto-completed deliverable: {deliverable_name}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create completion task',
                    'requires_manual_intervention': True
                }
                
        except Exception as e:
            logger.error(f"❌ Error auto-completing deliverable {deliverable_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_manual_intervention': True
            }
    
    async def unblock_goal(self, workspace_id: str, goal_id: str) -> Dict[str, Any]:
        """Attempt to unblock a stuck goal with rate limiting"""
        # RATE LIMITING: Acquire permit for goal unblock operations
        try:
            await api_rate_limiter.acquire("goal_unblock", "high")
            logger.info(f"✅ RATE LIMITED: Acquired permit for goal unblock operation")
        except Exception as e:
            logger.error(f"🚫 RATE LIMIT ERROR: {e}")
            return {
                'success': False,
                'error': 'Rate limit exceeded - please try again later'
            }
        
        try:
            logger.info(f"🔓 Attempting to unblock goal {goal_id}")
            
            # Get tasks for the goal
            tasks = await list_tasks(workspace_id, goal_id=goal_id)
            
            unblock_actions = []
            
            # Handle failed tasks
            failed_tasks = [t for t in tasks if t.get('status') == TaskStatus.FAILED.value]
            for task in failed_tasks:
                # Retry the failed task
                task_id = task.get('id')
                try:
                    # SDK COMPLIANT: Use update_task_fields instead of direct database access
                    await update_task_fields(task_id, {
                        'status': TaskStatus.PENDING.value,
                        'error_message': None,
                        'retry_count': task.get('retry_count', 0) + 1,
                        'updated_at': datetime.utcnow().isoformat()
                    })
                    
                    unblock_actions.append(f"Retried failed task: {task.get('name')}")
                    logger.info(f"✅ SDK COMPLIANT: Retried task {task_id} using update_task_fields")
                except Exception as e:
                    logger.error(f"Failed to retry task {task_id}: {e}")
            
            # Handle human feedback tasks - SECURITY: Never auto-approve, only flag for manual review
            feedback_tasks = [t for t in tasks if 'human_feedback' in t.get('name', '').lower()]
            for task in feedback_tasks:
                # SECURITY CRITICAL: Flag for manual human review instead of auto-approval
                task_id = task.get('id')
                try:
                    # SDK COMPLIANT: Use update_task_fields for security-critical updates
                    await update_task_fields(task_id, {
                        'priority': "urgent",
                        'metadata': {
                            **task.get('metadata', {}),
                            'requires_manual_review': True,
                            'unblock_request_time': datetime.utcnow().isoformat(),
                            'security_flag': 'human_feedback_review_required'
                        },
                        'updated_at': datetime.utcnow().isoformat()
                    })
                    
                    unblock_actions.append(f"Flagged for urgent manual review: {task.get('name')}")
                    logger.warning(f"🚨 SECURITY: Human feedback task {task_id} requires manual review - auto-approval removed for security")
                    logger.info(f"✅ SDK COMPLIANT: Updated task {task_id} with security flags using update_task_fields")
                except Exception as e:
                    logger.error(f"Failed to flag task {task_id} for manual review: {e}")
            
            return {
                'success': True,
                'actions_taken': unblock_actions,
                'message': f'Applied {len(unblock_actions)} unblock actions to goal {goal_id}'
            }
            
        except Exception as e:
            logger.error(f"❌ Error unblocking goal {goal_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instances
missing_deliverable_detector = MissingDeliverableDetection()
missing_deliverable_auto_completer = MissingDeliverableAutoCompleter()

async def detect_missing_deliverables(workspace_id: str) -> List[Dict[str, Any]]:
    """Convenience function to detect missing deliverables"""
    return await missing_deliverable_detector.detect_missing_deliverables(workspace_id)

async def auto_complete_missing_deliverable(workspace_id: str, goal_id: str, deliverable_name: str) -> Dict[str, Any]:
    """Convenience function to auto-complete missing deliverable"""
    return await missing_deliverable_auto_completer.auto_complete_missing_deliverable(workspace_id, goal_id, deliverable_name)

async def unblock_goal(workspace_id: str, goal_id: str) -> Dict[str, Any]:
    """Convenience function to unblock a goal"""
    return await missing_deliverable_auto_completer.unblock_goal(workspace_id, goal_id)