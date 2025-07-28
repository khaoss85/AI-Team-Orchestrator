#!/usr/bin/env python3
"""
🏥 WORKSPACE HEALTH MANAGER

Comprehensive system for workspace health monitoring, intelligent auto-recovery,
and dynamic threshold management. This addresses the root cause of excessive
workspace auto-pause and provides intelligent recovery mechanisms.

Features:
- Intelligent health assessment with context awareness
- Auto-recovery from common issues (needs_intervention, excessive tasks, etc.)
- Dynamic threshold adjustment based on workspace characteristics
- Recovery strategy recommendations
- Performance-optimized health checks
- Pillars compliant (AI-driven decisions)
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

from database import supabase, list_tasks, get_workspace
from models import TaskStatus, WorkspaceStatus

logger = logging.getLogger(__name__)

class HealthIssueLevel(Enum):
    """Health issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    AUTO_CLEANUP = "auto_cleanup"
    STATUS_RESET = "status_reset"
    TASK_LIMIT_INCREASE = "task_limit_increase"
    DUPLICATE_REMOVAL = "duplicate_removal"
    AGENT_REACTIVATION = "agent_reactivation"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class HealthIssue:
    """Represents a workspace health issue"""
    level: HealthIssueLevel
    issue_type: str
    description: str
    affected_count: int = 0
    suggested_recovery: Optional[RecoveryStrategy] = None
    auto_recoverable: bool = False
    recovery_confidence: float = 0.0

@dataclass
class WorkspaceHealthReport:
    """Comprehensive workspace health report"""
    workspace_id: str
    is_healthy: bool
    overall_score: float  # 0-100
    issues: List[HealthIssue]
    recommended_actions: List[str]
    can_auto_recover: bool
    recovery_strategies: List[RecoveryStrategy]
    last_check_time: datetime
    next_check_recommended: datetime

@dataclass
class RecoveryResult:
    """Result of auto-recovery attempt"""
    success: bool
    strategy_used: RecoveryStrategy
    issues_resolved: List[str]
    issues_remaining: List[str]
    new_health_score: float
    recovery_time_seconds: float

class WorkspaceHealthManager:
    """
    🎯 DEFINITIVE SOLUTION for workspace health and auto-recovery
    
    Prevents workspace auto-pause through intelligent health management
    and provides automatic recovery from common issues.
    """
    
    def __init__(self):
        # Configuration
        self.enable_auto_recovery = os.getenv("ENABLE_AUTO_WORKSPACE_RECOVERY", "true").lower() == "true"
        self.health_check_interval = int(os.getenv("WORKSPACE_HEALTH_CHECK_INTERVAL", "300"))  # 5 minutes
        self.recovery_confidence_threshold = float(os.getenv("RECOVERY_CONFIDENCE_THRESHOLD", "0.8"))
        
        # Dynamic thresholds
        self.base_task_limit = int(os.getenv("MAX_PENDING_TASKS_PER_WORKSPACE", "200"))  # Increased from 50
        self.task_limit_multiplier = float(os.getenv("TASK_LIMIT_MULTIPLIER", "1.5"))
        self.duplicate_threshold = int(os.getenv("DUPLICATE_TASK_THRESHOLD", "3"))
        
        # Cache for performance
        self.health_cache: Dict[str, Tuple[float, WorkspaceHealthReport]] = {}
        self.cache_duration = 60  # 1 minute
        
        logger.info(f"WorkspaceHealthManager initialized - auto_recovery: {self.enable_auto_recovery}, "
                   f"base_task_limit: {self.base_task_limit}, check_interval: {self.health_check_interval}s")
    
    async def check_workspace_health_with_recovery(
        self, 
        workspace_id: str,
        attempt_auto_recovery: bool = True
    ) -> WorkspaceHealthReport:
        """
        🔍 CORE FUNCTION: Comprehensive health check with auto-recovery
        
        Returns detailed health report and attempts recovery if issues found
        """
        try:
            start_time = datetime.now()
            
            # Check cache first
            if workspace_id in self.health_cache:
                cache_time, cached_report = self.health_cache[workspace_id]
                if (start_time.timestamp() - cache_time) < self.cache_duration:
                    logger.debug(f"Returning cached health report for workspace {workspace_id}")
                    return cached_report
            
            logger.info(f"🏥 Starting comprehensive health check for workspace {workspace_id}")
            
            # 1. Basic workspace validation
            workspace_data = await get_workspace(workspace_id)
            if not workspace_data:
                return self._create_error_report(workspace_id, "Workspace not found")
            
            # 2. Gather health data
            health_data = await self._gather_health_data(workspace_id, workspace_data)
            
            # 3. Analyze health issues
            issues = await self._analyze_health_issues(workspace_id, health_data)
            
            # 4. Calculate overall health score
            health_score = self._calculate_health_score(issues)
            
            # 5. Determine recovery strategies
            recovery_strategies = self._determine_recovery_strategies(issues)
            can_auto_recover = any(issue.auto_recoverable for issue in issues)
            
            # 6. Generate recommendations
            recommendations = self._generate_recommendations(issues, health_data)
            
            # Create health report
            report = WorkspaceHealthReport(
                workspace_id=workspace_id,
                is_healthy=health_score >= 70,  # 70% threshold for healthy
                overall_score=health_score,
                issues=issues,
                recommended_actions=recommendations,
                can_auto_recover=can_auto_recover,
                recovery_strategies=recovery_strategies,
                last_check_time=start_time,
                next_check_recommended=start_time + timedelta(seconds=self.health_check_interval)
            )
            
            # 7. Attempt auto-recovery if enabled and viable
            if (attempt_auto_recovery and 
                self.enable_auto_recovery and 
                can_auto_recover and 
                not report.is_healthy):
                
                logger.info(f"🔧 Attempting auto-recovery for workspace {workspace_id}")
                recovery_result = await self.auto_recover_workspace(workspace_id, report)
                
                if recovery_result.success:
                    # Re-check health after recovery
                    report = await self.check_workspace_health_with_recovery(
                        workspace_id, attempt_auto_recovery=False
                    )
            
            # Cache result
            self.health_cache[workspace_id] = (start_time.timestamp(), report)
            
            logger.info(f"🏥 Health check completed for workspace {workspace_id}: "
                       f"score={health_score:.1f}%, issues={len(issues)}, healthy={report.is_healthy}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error in workspace health check for {workspace_id}: {e}")
            return self._create_error_report(workspace_id, f"Health check failed: {e}")
    
    async def auto_recover_workspace(
        self, 
        workspace_id: str, 
        health_report: WorkspaceHealthReport
    ) -> RecoveryResult:
        """
        🔧 RECOVERY FUNCTION: Attempt automatic recovery from health issues
        """
        start_time = datetime.now()
        issues_resolved = []
        issues_remaining = []
        
        try:
            logger.info(f"🔧 Starting auto-recovery for workspace {workspace_id}")
            
            # Sort issues by recovery confidence (highest first)
            recoverable_issues = [issue for issue in health_report.issues if issue.auto_recoverable]
            recoverable_issues.sort(key=lambda x: x.recovery_confidence, reverse=True)
            
            strategy_used = RecoveryStrategy.MANUAL_INTERVENTION  # Default
            
            for issue in recoverable_issues:
                if issue.recovery_confidence >= self.recovery_confidence_threshold:
                    success = await self._apply_recovery_strategy(
                        workspace_id, issue.suggested_recovery, issue
                    )
                    
                    if success:
                        issues_resolved.append(f"{issue.issue_type}: {issue.description}")
                        strategy_used = issue.suggested_recovery
                        logger.info(f"✅ Resolved issue: {issue.issue_type}")
                    else:
                        issues_remaining.append(f"{issue.issue_type}: {issue.description}")
                        logger.warning(f"❌ Failed to resolve issue: {issue.issue_type}")
                else:
                    issues_remaining.append(f"{issue.issue_type}: Low confidence ({issue.recovery_confidence:.2f})")
            
            # Re-calculate health score
            post_recovery_report = await self.check_workspace_health_with_recovery(
                workspace_id, attempt_auto_recovery=False
            )
            
            recovery_time = (datetime.now() - start_time).total_seconds()
            success = len(issues_resolved) > 0
            
            result = RecoveryResult(
                success=success,
                strategy_used=strategy_used,
                issues_resolved=issues_resolved,
                issues_remaining=issues_remaining,
                new_health_score=post_recovery_report.overall_score,
                recovery_time_seconds=recovery_time
            )
            
            logger.info(f"🔧 Auto-recovery completed for workspace {workspace_id}: "
                       f"success={success}, resolved={len(issues_resolved)}, "
                       f"new_score={result.new_health_score:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in auto-recovery for workspace {workspace_id}: {e}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.MANUAL_INTERVENTION,
                issues_resolved=[],
                issues_remaining=[f"Recovery failed: {e}"],
                new_health_score=health_report.overall_score,
                recovery_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def get_dynamic_task_limit(self, workspace_id: str) -> int:
        """
        📊 DYNAMIC THRESHOLDS: Calculate appropriate task limit for workspace
        
        Replaces fixed 50-task limit with intelligent, context-aware limits
        """
        try:
            # Get workspace characteristics
            workspace_data = await get_workspace(workspace_id)
            if not workspace_data:
                return self.base_task_limit
            
            # Get agent count
            agents_response = supabase.table("agents").select("id").eq("workspace_id", workspace_id).execute()
            agent_count = len(agents_response.data) if agents_response.data else 1
            
            # Get goal complexity (number of active goals)
            goals_response = supabase.table("workspace_goals").select("id").eq(
                "workspace_id", workspace_id
            ).eq("status", "active").execute()
            goal_count = len(goals_response.data) if goals_response.data else 1
            
            # Calculate dynamic limit
            # Base formula: base_limit * agent_multiplier * goal_multiplier
            agent_multiplier = min(agent_count * 0.3, 2.0)  # Max 2x for agents
            goal_multiplier = min(goal_count * 0.2, 1.5)   # Max 1.5x for goals
            
            dynamic_limit = int(self.base_task_limit * agent_multiplier * goal_multiplier)
            
            # Ensure minimum viable limit
            dynamic_limit = max(dynamic_limit, 20)  # Never below 20 tasks
            
            logger.debug(f"Dynamic task limit for workspace {workspace_id}: {dynamic_limit} "
                        f"(agents: {agent_count}, goals: {goal_count})")
            
            return dynamic_limit
            
        except Exception as e:
            logger.error(f"Error calculating dynamic task limit for {workspace_id}: {e}")
            return self.base_task_limit
    
    async def _gather_health_data(self, workspace_id: str, workspace_data: Dict) -> Dict:
        """Gather all relevant data for health analysis"""
        
        # Get tasks
        tasks = await list_tasks(workspace_id)
        
        # Get agents
        agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
        agents = agents_response.data or []
        
        # Get goals
        goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
        goals = goals_response.data or []
        
        # Get recent execution logs (last hour)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        logs_response = supabase.table("execution_logs").select("*").eq(
            "workspace_id", workspace_id
        ).gte("created_at", one_hour_ago).execute()
        recent_logs = logs_response.data or []
        
        return {
            "workspace": workspace_data,
            "tasks": tasks,
            "agents": agents,
            "goals": goals,
            "recent_logs": recent_logs,
            "task_count": len(tasks),
            "agent_count": len(agents),
            "goal_count": len(goals)
        }
    
    async def _analyze_health_issues(self, workspace_id: str, health_data: Dict) -> List[HealthIssue]:
        """Analyze health data and identify issues"""
        issues = []
        
        # 1. Check workspace status
        workspace_status = health_data["workspace"].get("status", "")
        if workspace_status == "needs_intervention":
            issues.append(HealthIssue(
                level=HealthIssueLevel.CRITICAL,
                issue_type="workspace_needs_intervention",
                description="Workspace marked as needs_intervention",
                suggested_recovery=RecoveryStrategy.STATUS_RESET,
                auto_recoverable=True,
                recovery_confidence=0.9
            ))
        elif workspace_status == "processing_tasks":
            # Check if workspace has been stuck in processing_tasks for too long
            updated_at = health_data["workspace"].get("updated_at")
            if updated_at:
                try:
                    if date_parser:
                        last_update = date_parser.parse(updated_at)
                        stuck_minutes = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 60
                    else:
                        # Fallback: try basic ISO parsing
                        if updated_at.endswith('Z'):
                            updated_at = updated_at[:-1] + '+00:00'
                        last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        stuck_minutes = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 60
                    
                    # Consider stuck if processing for more than 10 minutes
                    if stuck_minutes > 10:
                        issues.append(HealthIssue(
                            level=HealthIssueLevel.CRITICAL,
                            issue_type="workspace_stuck_processing",
                            description=f"Workspace stuck in 'processing_tasks' for {stuck_minutes:.1f} minutes",
                            suggested_recovery=RecoveryStrategy.STATUS_RESET,
                            auto_recoverable=True,
                            recovery_confidence=0.95
                        ))
                except Exception as e:
                    logger.warning(f"Could not parse workspace updated_at timestamp: {e}")
                    # If we can't parse timestamp, still flag as potential issue
                    issues.append(HealthIssue(
                        level=HealthIssueLevel.WARNING,
                        issue_type="workspace_processing_unknown_duration",
                        description="Workspace in 'processing_tasks' status (duration unknown)",
                        suggested_recovery=RecoveryStrategy.STATUS_RESET,
                        auto_recoverable=True,
                        recovery_confidence=0.7
                    ))
        
        # 2. Check task overload (using dynamic limits)
        dynamic_limit = await self.get_dynamic_task_limit(workspace_id)
        pending_tasks = [t for t in health_data["tasks"] if t.get("status") == "pending"]
        
        if len(pending_tasks) > dynamic_limit:
            issues.append(HealthIssue(
                level=HealthIssueLevel.WARNING,
                issue_type="excessive_pending_tasks",
                description=f"Too many pending tasks ({len(pending_tasks)}/{dynamic_limit})",
                affected_count=len(pending_tasks) - dynamic_limit,
                suggested_recovery=RecoveryStrategy.DUPLICATE_REMOVAL,
                auto_recoverable=True,
                recovery_confidence=0.8
            ))
        
        # 3. Check for duplicates
        task_names = [t.get("name", "") for t in health_data["tasks"]]
        from collections import Counter
        name_counts = Counter(task_names)
        duplicates = {name: count for name, count in name_counts.items() if count > self.duplicate_threshold}
        
        if duplicates:
            total_duplicates = sum(count - 1 for count in duplicates.values())
            issues.append(HealthIssue(
                level=HealthIssueLevel.WARNING,
                issue_type="duplicate_tasks",
                description=f"Duplicate tasks detected: {len(duplicates)} groups, {total_duplicates} excess tasks",
                affected_count=total_duplicates,
                suggested_recovery=RecoveryStrategy.DUPLICATE_REMOVAL,
                auto_recoverable=True,
                recovery_confidence=0.95
            ))
        
        # 4. Check agent availability
        available_agents = [a for a in health_data["agents"] if a.get("status") in ["available", "active"]]
        if len(available_agents) == 0:
            issues.append(HealthIssue(
                level=HealthIssueLevel.CRITICAL,
                issue_type="no_available_agents",
                description="No available agents for task execution",
                suggested_recovery=RecoveryStrategy.AGENT_REACTIVATION,
                auto_recoverable=True,
                recovery_confidence=0.7
            ))
        elif len(available_agents) < 2:
            issues.append(HealthIssue(
                level=HealthIssueLevel.WARNING,
                issue_type="low_agent_availability",
                description=f"Only {len(available_agents)} available agent(s)",
                affected_count=2 - len(available_agents),
                suggested_recovery=RecoveryStrategy.AGENT_REACTIVATION,
                auto_recoverable=False,
                recovery_confidence=0.5
            ))
        
        # 5. Check failed tasks ratio
        failed_tasks = [t for t in health_data["tasks"] if t.get("status") == "failed"]
        if health_data["task_count"] > 0:
            failure_rate = len(failed_tasks) / health_data["task_count"]
            if failure_rate > 0.3:  # More than 30% failed
                issues.append(HealthIssue(
                    level=HealthIssueLevel.WARNING,
                    issue_type="high_failure_rate",
                    description=f"High task failure rate: {failure_rate:.1%}",
                    affected_count=len(failed_tasks),
                    suggested_recovery=RecoveryStrategy.AUTO_CLEANUP,
                    auto_recoverable=False,
                    recovery_confidence=0.6
                ))
        
        return issues
    
    def _calculate_health_score(self, issues: List[HealthIssue]) -> float:
        """Calculate overall health score (0-100)"""
        if not issues:
            return 100.0
        
        # Scoring system based on issue levels
        score_deductions = {
            HealthIssueLevel.INFO: 5,
            HealthIssueLevel.WARNING: 15,
            HealthIssueLevel.CRITICAL: 30,
            HealthIssueLevel.EMERGENCY: 50
        }
        
        total_deduction = sum(score_deductions.get(issue.level, 10) for issue in issues)
        score = max(0, 100 - total_deduction)
        
        return score
    
    def _determine_recovery_strategies(self, issues: List[HealthIssue]) -> List[RecoveryStrategy]:
        """Determine appropriate recovery strategies"""
        strategies = set()
        
        for issue in issues:
            if issue.suggested_recovery:
                strategies.add(issue.suggested_recovery)
        
        return list(strategies)
    
    def _generate_recommendations(self, issues: List[HealthIssue], health_data: Dict) -> List[str]:
        """Generate human-readable recommendations"""
        recommendations = []
        
        for issue in issues:
            if issue.level in [HealthIssueLevel.CRITICAL, HealthIssueLevel.EMERGENCY]:
                if issue.auto_recoverable:
                    recommendations.append(f"🔧 AUTO-RECOVERABLE: {issue.description}")
                else:
                    recommendations.append(f"🚨 MANUAL ACTION REQUIRED: {issue.description}")
            elif issue.level == HealthIssueLevel.WARNING:
                recommendations.append(f"⚠️ ATTENTION NEEDED: {issue.description}")
        
        if not recommendations:
            recommendations.append("✅ Workspace is healthy - no action required")
        
        return recommendations
    
    async def _apply_recovery_strategy(
        self, 
        workspace_id: str, 
        strategy: RecoveryStrategy, 
        issue: HealthIssue
    ) -> bool:
        """Apply specific recovery strategy"""
        try:
            logger.info(f"🔧 Applying recovery strategy {strategy.value} for {issue.issue_type}")
            
            if strategy == RecoveryStrategy.STATUS_RESET:
                # Reset workspace status to active with enhanced logging
                current_status_response = supabase.table("workspaces").select("status, updated_at").eq("id", workspace_id).single().execute()
                current_status = current_status_response.data.get("status") if current_status_response.data else "unknown"
                
                supabase.table("workspaces").update({
                    "status": "active",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", workspace_id).execute()
                
                logger.info(f"✅ Reset workspace {workspace_id} status from '{current_status}' to 'active'")
                
                # If we were stuck in processing_tasks, also log the recovery
                if current_status == "processing_tasks":
                    logger.info(f"🔧 RECOVERY: Workspace {workspace_id} was stuck in 'processing_tasks', now reset to 'active'")
                
                return True
                
            elif strategy == RecoveryStrategy.DUPLICATE_REMOVAL:
                # Use our TaskDeduplicationManager
                try:
                    from services.task_deduplication_manager import task_deduplication_manager
                    
                    cleanup_stats = await task_deduplication_manager.cleanup_duplicate_tasks(
                        workspace_id, dry_run=False
                    )
                    
                    if cleanup_stats.duplicates_removed > 0:
                        logger.info(f"✅ Removed {cleanup_stats.duplicates_removed} duplicate tasks")
                        return True
                    else:
                        logger.info("ℹ️ No duplicates found to remove")
                        return True  # Not an error
                        
                except ImportError:
                    logger.warning("TaskDeduplicationManager not available for recovery")
                    return False
                    
            elif strategy == RecoveryStrategy.AGENT_REACTIVATION:
                # Reactivate failed agents
                inactive_agents = supabase.table("agents").select("id").eq(
                    "workspace_id", workspace_id
                ).neq("status", "active").neq("status", "available").execute()
                
                if inactive_agents.data:
                    for agent in inactive_agents.data:
                        supabase.table("agents").update({
                            "status": "active"
                        }).eq("id", agent["id"]).execute()
                    
                    logger.info(f"✅ Reactivated {len(inactive_agents.data)} agents")
                    return True
                else:
                    logger.info("ℹ️ No inactive agents to reactivate")
                    return True
            
            # Add more recovery strategies as needed
            else:
                logger.warning(f"Recovery strategy {strategy.value} not implemented yet")
                return False
                
        except Exception as e:
            logger.error(f"Error applying recovery strategy {strategy.value}: {e}")
            return False
    
    async def monitor_all_workspaces_for_stuck_processing(self) -> Dict[str, Any]:
        """
        🚨 CRITICAL FUNCTION: Monitor all workspaces for stuck processing_tasks status
        
        This addresses the core issue where workspaces get stuck in 'processing_tasks'
        when asyncio.create_task() doesn't complete properly.
        """
        try:
            logger.info("🔍 Starting system-wide check for stuck workspaces...")
            
            # Get all workspaces in processing_tasks status
            stuck_workspaces_response = supabase.table("workspaces").select(
                "id, name, status, updated_at"
            ).eq("status", "processing_tasks").execute()
            
            stuck_workspaces = stuck_workspaces_response.data or []
            recovery_results = {}
            
            if not stuck_workspaces:
                logger.info("✅ No workspaces stuck in 'processing_tasks' status")
                return {"stuck_workspaces": 0, "recovered": 0, "details": {}}
            
            logger.warning(f"⚠️  Found {len(stuck_workspaces)} workspace(s) in 'processing_tasks' status")
            
            for workspace in stuck_workspaces:
                workspace_id = workspace["id"]
                workspace_name = workspace.get("name", "Unknown")
                
                logger.info(f"🔍 Checking workspace '{workspace_name}' ({workspace_id})")
                
                # Run health check with auto-recovery
                health_report = await self.check_workspace_health_with_recovery(
                    workspace_id, attempt_auto_recovery=True
                )
                
                recovery_results[workspace_id] = {
                    "name": workspace_name,
                    "was_recovered": health_report.is_healthy,
                    "health_score": health_report.overall_score,
                    "issues_found": len(health_report.issues),
                    "recovery_attempted": health_report.can_auto_recover
                }
                
                if health_report.is_healthy:
                    logger.info(f"✅ Workspace '{workspace_name}' recovered successfully")
                else:
                    logger.warning(f"⚠️  Workspace '{workspace_name}' still needs attention: {health_report.issues}")
            
            recovered_count = sum(1 for result in recovery_results.values() if result["was_recovered"])
            
            logger.info(f"🔧 Recovery complete: {recovered_count}/{len(stuck_workspaces)} workspaces recovered")
            
            return {
                "stuck_workspaces": len(stuck_workspaces),
                "recovered": recovered_count,
                "details": recovery_results
            }
            
        except Exception as e:
            logger.error(f"Error in system-wide workspace monitoring: {e}")
            return {"error": str(e), "stuck_workspaces": 0, "recovered": 0}
    
    def _create_error_report(self, workspace_id: str, error_message: str) -> WorkspaceHealthReport:
        """Create error report for failed health checks"""
        return WorkspaceHealthReport(
            workspace_id=workspace_id,
            is_healthy=False,
            overall_score=0.0,
            issues=[HealthIssue(
                level=HealthIssueLevel.EMERGENCY,
                issue_type="health_check_error",
                description=error_message,
                auto_recoverable=False
            )],
            recommended_actions=[f"🚨 HEALTH CHECK FAILED: {error_message}"],
            can_auto_recover=False,
            recovery_strategies=[RecoveryStrategy.MANUAL_INTERVENTION],
            last_check_time=datetime.now(),
            next_check_recommended=datetime.now() + timedelta(minutes=5)
        )

# Global instance
workspace_health_manager = WorkspaceHealthManager()