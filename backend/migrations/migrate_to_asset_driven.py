#!/usr/bin/env python3
"""
Asset-Driven System Migration Script
Migrates existing workspaces to the new asset-driven architecture while preserving data integrity.

This script handles:
1. Data migration from old to new asset tables
2. Quality rule initialization
3. Goal decomposition to asset requirements
4. Existing task-to-artifact mapping
5. System validation and rollback capabilities

Usage:
    python migrate_to_asset_driven.py --workspace-id <id> [--dry-run] [--rollback]
"""

import asyncio
import argparse
import logging
import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4

# Import existing models and database
from database import DatabaseManager
from models import WorkspaceGoal, Task

# Import new asset system components
from services.asset_requirements_generator import AssetRequirementsGenerator
from database_asset_extensions import AssetDrivenDatabaseManager
from monitoring.asset_system_monitor import AssetSystemMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AssetDrivenMigrationManager:
    """
    Manages the migration process from traditional goals to asset-driven system.
    
    Implements safe migration with rollback capabilities and comprehensive validation.
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.asset_db_manager = AssetDrivenDatabaseManager()
        self.requirements_generator = AssetRequirementsGenerator()
        self.monitor = AssetSystemMonitor()
        
        # Migration state tracking
        self.migration_state = {
            "started_at": None,
            "workspace_id": None,
            "steps_completed": [],
            "rollback_data": {},
            "errors": [],
            "warnings": []
        }
        
        # Migration statistics
        self.stats = {
            "workspaces_processed": 0,
            "goals_migrated": 0,
            "requirements_generated": 0,
            "artifacts_created": 0,
            "quality_rules_applied": 0,
            "tasks_mapped": 0
        }
    
    async def migrate_workspace(self, workspace_id: UUID, dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate a single workspace to asset-driven system.
        
        Args:
            workspace_id: UUID of workspace to migrate
            dry_run: If True, only simulate migration without making changes
            
        Returns:
            Migration result with status and details
        """
        try:
            logger.info(f"🚀 Starting migration for workspace: {workspace_id}")
            
            self.migration_state["started_at"] = datetime.now(timezone.utc)
            self.migration_state["workspace_id"] = str(workspace_id)
            
            migration_result = {
                "workspace_id": str(workspace_id),
                "status": "in_progress",
                "dry_run": dry_run,
                "started_at": self.migration_state["started_at"].isoformat(),
                "steps": [],
                "statistics": {},
                "errors": [],
                "warnings": []
            }
            
            # Step 1: Validate workspace exists and get current state
            logger.info("📋 Step 1: Validating workspace and gathering data")
            workspace_data = await self._validate_and_gather_workspace_data(workspace_id)
            
            if not workspace_data["valid"]:
                raise ValueError(f"Workspace validation failed: {workspace_data['error']}")
            
            migration_result["steps"].append({
                "step": "workspace_validation",
                "status": "completed",
                "data": {
                    "goals_count": workspace_data["goals_count"],
                    "tasks_count": workspace_data["tasks_count"],
                    "team_members_count": workspace_data["team_members_count"]
                }
            })
            
            # Step 2: Generate asset requirements from existing goals
            logger.info("🎯 Step 2: Generating asset requirements from goals")
            requirements_data = await self._generate_asset_requirements(
                workspace_data["goals"], dry_run
            )
            
            migration_result["steps"].append({
                "step": "asset_requirements_generation",
                "status": "completed",
                "data": {
                    "requirements_generated": len(requirements_data["requirements"]),
                    "goals_processed": len(workspace_data["goals"])
                }
            })
            
            # Step 3: Map existing tasks to potential artifacts
            logger.info("📦 Step 3: Mapping existing tasks to artifacts")
            artifact_mapping = await self._map_tasks_to_artifacts(
                workspace_data["tasks"], requirements_data["requirements"], dry_run
            )
            
            migration_result["steps"].append({
                "step": "task_artifact_mapping",
                "status": "completed",
                "data": {
                    "tasks_mapped": len(artifact_mapping["mappings"]),
                    "artifacts_created": len(artifact_mapping["artifacts"])
                }
            })
            
            # Step 4: Initialize quality rules for workspace
            logger.info("🛡️ Step 4: Initializing quality rules")
            quality_setup = await self._initialize_quality_system(workspace_id, dry_run)
            
            migration_result["steps"].append({
                "step": "quality_system_initialization",
                "status": "completed",
                "data": {
                    "quality_rules_created": len(quality_setup["rules"]),
                    "validation_templates": len(quality_setup["templates"])
                }
            })
            
            # Step 5: Update goal progress calculations
            logger.info("📊 Step 5: Updating goal progress calculations")
            progress_update = await self._update_goal_progress_calculations(
                workspace_id, requirements_data["requirements"], dry_run
            )
            
            migration_result["steps"].append({
                "step": "goal_progress_update",
                "status": "completed",
                "data": progress_update
            })
            
            # Step 6: Validate migration integrity
            logger.info("✅ Step 6: Validating migration integrity")
            validation_result = await self._validate_migration_integrity(workspace_id)
            
            migration_result["steps"].append({
                "step": "migration_validation",
                "status": "completed",
                "data": validation_result
            })
            
            # Update statistics
            self.stats["workspaces_processed"] += 1
            self.stats["goals_migrated"] += len(workspace_data["goals"])
            self.stats["requirements_generated"] += len(requirements_data["requirements"])
            self.stats["artifacts_created"] += len(artifact_mapping["artifacts"])
            self.stats["quality_rules_applied"] += len(quality_setup["rules"])
            self.stats["tasks_mapped"] += len(artifact_mapping["mappings"])
            
            migration_result["statistics"] = self.stats.copy()
            migration_result["status"] = "completed"
            migration_result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ Migration completed successfully for workspace: {workspace_id}")
            
            return migration_result
            
        except Exception as e:
            error_msg = f"Migration failed for workspace {workspace_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            self.migration_state["errors"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            
            return {
                "workspace_id": str(workspace_id),
                "status": "failed",
                "error": error_msg,
                "steps": migration_result.get("steps", []),
                "migration_state": self.migration_state
            }
    
    async def _validate_and_gather_workspace_data(self, workspace_id: UUID) -> Dict[str, Any]:
        """Validate workspace exists and gather all relevant data for migration."""
        try:
            # Get workspace goals
            goals = await self.db_manager.get_workspace_goals(workspace_id)
            
            # Get workspace tasks
            tasks = await self.db_manager.get_workspace_tasks(workspace_id)
            
            # Get team members
            team_members = await self.db_manager.get_workspace_team_members(workspace_id)
            
            # Check if workspace has any asset system data already
            existing_requirements = await self.asset_db_manager.get_workspace_asset_requirements(workspace_id)
            
            return {
                "valid": True,
                "goals": goals,
                "tasks": tasks,
                "team_members": team_members,
                "goals_count": len(goals),
                "tasks_count": len(tasks),
                "team_members_count": len(team_members),
                "has_existing_assets": len(existing_requirements) > 0,
                "existing_requirements_count": len(existing_requirements)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def _generate_asset_requirements(self, goals: List[WorkspaceGoal], dry_run: bool) -> Dict[str, Any]:
        """Generate asset requirements from existing workspace goals."""
        try:
            requirements = []
            
            for goal in goals:
                try:
                    # Generate requirements using the AI service
                    goal_requirements = await self.requirements_generator.generate_from_goal(goal)
                    
                    if not dry_run:
                        # Save requirements to database
                        for req in goal_requirements:
                            saved_req = await self.asset_db_manager.create_asset_requirement(req)
                            requirements.append(saved_req)
                    else:
                        requirements.extend(goal_requirements)
                    
                    logger.info(f"Generated {len(goal_requirements)} requirements for goal: {goal.metric_type}")
                    
                except Exception as e:
                    logger.warning(f"Failed to generate requirements for goal {goal.id}: {e}")
                    self.migration_state["warnings"].append(f"Goal {goal.id} requirements generation failed: {e}")
            
            return {
                "requirements": requirements,
                "success_count": len(requirements),
                "goals_processed": len(goals)
            }
            
        except Exception as e:
            logger.error(f"Asset requirements generation failed: {e}")
            raise
    
    async def _map_tasks_to_artifacts(self, tasks: List[Task], requirements: List[Any], dry_run: bool) -> Dict[str, Any]:
        """Map existing completed tasks to potential artifacts."""
        try:
            mappings = []
            artifacts = []
            
            # Get completed tasks that could become artifacts
            completed_tasks = [t for t in tasks if t.status == "completed" and t.output]
            
            for task in completed_tasks:
                try:
                    # Find matching requirement based on task content/type
                    matching_req = self._find_matching_requirement(task, requirements)
                    
                    if matching_req:
                        # Create artifact from task output
                        artifact_data = {
                            "id": uuid4(),
                            "requirement_id": matching_req.id,
                            "task_id": task.id,
                            "artifact_name": task.description[:100] + "..." if len(task.description) > 100 else task.description,
                            "artifact_type": self._determine_artifact_type(task),
                            "content": task.output,
                            "quality_score": 0.7,  # Initial score, will be validated
                            "status": "migrated",
                            "business_value_score": 0.8,
                            "actionability_score": 0.7,
                            "created_at": task.created_at,
                            "updated_at": datetime.now(timezone.utc)
                        }
                        
                        if not dry_run:
                            saved_artifact = await self.asset_db_manager.create_asset_artifact(artifact_data)
                            artifacts.append(saved_artifact)
                        else:
                            artifacts.append(artifact_data)
                        
                        mappings.append({
                            "task_id": task.id,
                            "artifact_id": artifact_data["id"],
                            "requirement_id": matching_req.id,
                            "confidence": 0.8
                        })
                        
                        logger.debug(f"Mapped task {task.id} to artifact for requirement {matching_req.id}")
                
                except Exception as e:
                    logger.warning(f"Failed to map task {task.id}: {e}")
                    self.migration_state["warnings"].append(f"Task {task.id} mapping failed: {e}")
            
            return {
                "mappings": mappings,
                "artifacts": artifacts,
                "tasks_processed": len(completed_tasks)
            }
            
        except Exception as e:
            logger.error(f"Task to artifact mapping failed: {e}")
            raise
    
    def _find_matching_requirement(self, task: Task, requirements: List[Any]) -> Optional[Any]:
        """Find the best matching requirement for a task based on content similarity."""
        # This is a simplified matching algorithm
        # In production, you might use more sophisticated NLP matching
        
        task_keywords = set(task.description.lower().split())
        
        best_match = None
        best_score = 0
        
        for req in requirements:
            req_keywords = set(req.asset_name.lower().split())
            
            # Simple keyword overlap scoring
            overlap = len(task_keywords.intersection(req_keywords))
            score = overlap / max(len(task_keywords), len(req_keywords))
            
            if score > best_score and score > 0.3:  # Minimum threshold
                best_score = score
                best_match = req
        
        return best_match
    
    def _determine_artifact_type(self, task: Task) -> str:
        """Determine artifact type based on task characteristics."""
        output_lower = task.output.lower() if task.output else ""
        
        if any(keyword in output_lower for keyword in ["report", "analysis", "document", "study"]):
            return "document"
        elif any(keyword in output_lower for keyword in ["code", "script", "function", "class"]):
            return "code"
        elif any(keyword in output_lower for keyword in ["design", "mockup", "wireframe", "prototype"]):
            return "design"
        elif any(keyword in output_lower for keyword in ["test", "validation", "verification"]):
            return "test"
        else:
            return "document"  # Default type
    
    async def _initialize_quality_system(self, workspace_id: UUID, dry_run: bool) -> Dict[str, Any]:
        """Initialize quality rules and validation templates for the workspace."""
        try:
            # Default quality rules for different asset types
            default_rules = [
                {
                    "id": uuid4(),
                    "workspace_id": workspace_id,
                    "asset_type": "document",
                    "rule_name": "Content Completeness Check",
                    "ai_validation_prompt": "Evaluate if this document provides complete, actionable information with specific details and clear next steps. Score from 0.0 to 1.0 based on completeness and actionability.",
                    "validation_model": "gpt-4o-mini",
                    "threshold_score": 0.7,
                    "auto_learning_enabled": True,
                    "pillar_focus": "Concrete Deliverables",
                    "business_impact_weight": 0.8,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": uuid4(),
                    "workspace_id": workspace_id,
                    "asset_type": "document",
                    "rule_name": "Business Value Assessment",
                    "ai_validation_prompt": "Assess the business value and strategic impact of this deliverable. Does it provide clear business benefits, data-driven insights, or actionable recommendations? Score from 0.0 to 1.0.",
                    "validation_model": "gpt-4o-mini",
                    "threshold_score": 0.6,
                    "auto_learning_enabled": True,
                    "pillar_focus": "Business Value",
                    "business_impact_weight": 0.9,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": uuid4(),
                    "workspace_id": workspace_id,
                    "asset_type": "all",
                    "rule_name": "AI Quality Enhancement Check",
                    "ai_validation_prompt": "Evaluate if this content can be enhanced with AI capabilities. Check for opportunities to add data insights, automation, or intelligent features. Score enhancement potential from 0.0 to 1.0.",
                    "validation_model": "gpt-4o-mini",
                    "threshold_score": 0.5,
                    "auto_learning_enabled": True,
                    "pillar_focus": "AI-Driven",
                    "business_impact_weight": 0.7,
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            rules_created = []
            
            if not dry_run:
                for rule_data in default_rules:
                    saved_rule = await self.asset_db_manager.create_quality_rule(rule_data)
                    rules_created.append(saved_rule)
            else:
                rules_created = default_rules
            
            # Create validation templates
            templates = [
                {
                    "name": "Document Quality Template",
                    "asset_type": "document",
                    "validation_points": [
                        "Content completeness and depth",
                        "Actionable recommendations",
                        "Data-driven insights",
                        "Clear next steps",
                        "Business value proposition"
                    ]
                },
                {
                    "name": "Code Quality Template", 
                    "asset_type": "code",
                    "validation_points": [
                        "Code functionality and correctness",
                        "Documentation and comments",
                        "Performance optimization",
                        "Security considerations",
                        "Maintainability and scalability"
                    ]
                }
            ]
            
            return {
                "rules": rules_created,
                "templates": templates,
                "workspace_id": str(workspace_id)
            }
            
        except Exception as e:
            logger.error(f"Quality system initialization failed: {e}")
            raise
    
    async def _update_goal_progress_calculations(self, workspace_id: UUID, requirements: List[Any], dry_run: bool) -> Dict[str, Any]:
        """Update goal progress calculations to include asset completion rates."""
        try:
            goals = await self.db_manager.get_workspace_goals(workspace_id)
            updated_goals = []
            
            for goal in goals:
                try:
                    # Get requirements for this goal
                    goal_requirements = [r for r in requirements if hasattr(r, 'goal_id') and r.goal_id == goal.id]
                    
                    if goal_requirements:
                        # Calculate asset completion rate
                        total_requirements = len(goal_requirements)
                        completed_requirements = len([r for r in goal_requirements if hasattr(r, 'completion_status') and r.completion_status == 'completed'])
                        
                        asset_completion_rate = completed_requirements / total_requirements if total_requirements > 0 else 0.0
                        
                        # Calculate average quality score
                        quality_scores = [r.quality_score for r in goal_requirements if hasattr(r, 'quality_score') and r.quality_score > 0]
                        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
                        
                        if not dry_run:
                            # Update goal with asset-driven metrics
                            updated_goal = await self.asset_db_manager.update_goal_asset_metrics(
                                goal.id,
                                asset_completion_rate,
                                avg_quality_score
                            )
                            updated_goals.append(updated_goal)
                        else:
                            updated_goals.append({
                                "goal_id": goal.id,
                                "asset_completion_rate": asset_completion_rate,
                                "quality_score": avg_quality_score
                            })
                        
                        logger.debug(f"Updated goal {goal.id} with asset completion rate: {asset_completion_rate:.2f}")
                
                except Exception as e:
                    logger.warning(f"Failed to update goal {goal.id}: {e}")
                    self.migration_state["warnings"].append(f"Goal {goal.id} progress update failed: {e}")
            
            return {
                "goals_updated": len(updated_goals),
                "total_goals": len(goals),
                "update_details": updated_goals
            }
            
        except Exception as e:
            logger.error(f"Goal progress update failed: {e}")
            raise
    
    async def _validate_migration_integrity(self, workspace_id: UUID) -> Dict[str, Any]:
        """Validate that the migration was successful and data is consistent."""
        try:
            validation_result = {
                "overall_status": "valid",
                "checks": [],
                "warnings": [],
                "errors": []
            }
            
            # Check 1: Verify asset requirements exist
            requirements = await self.asset_db_manager.get_workspace_asset_requirements(workspace_id)
            validation_result["checks"].append({
                "check": "asset_requirements_exist",
                "status": "pass" if len(requirements) > 0 else "fail",
                "details": f"Found {len(requirements)} asset requirements"
            })
            
            # Check 2: Verify quality rules are initialized
            quality_rules = await self.asset_db_manager.get_workspace_quality_rules(workspace_id)
            validation_result["checks"].append({
                "check": "quality_rules_initialized",
                "status": "pass" if len(quality_rules) > 0 else "warning",
                "details": f"Found {len(quality_rules)} quality rules"
            })
            
            # Check 3: Verify goal progress calculations
            goals = await self.db_manager.get_workspace_goals(workspace_id)
            goals_with_assets = 0
            for goal in goals:
                goal_requirements = [r for r in requirements if hasattr(r, 'goal_id') and r.goal_id == goal.id]
                if goal_requirements:
                    goals_with_assets += 1
            
            validation_result["checks"].append({
                "check": "goals_have_asset_requirements",
                "status": "pass" if goals_with_assets > 0 else "warning",
                "details": f"{goals_with_assets}/{len(goals)} goals have asset requirements"
            })
            
            # Check 4: System health check
            system_health = await self.monitor.check_system_health()
            validation_result["checks"].append({
                "check": "system_health",
                "status": "pass" if system_health.overall_status.value == "healthy" else "warning",
                "details": f"System status: {system_health.overall_status.value}"
            })
            
            # Determine overall status
            failed_checks = [c for c in validation_result["checks"] if c["status"] == "fail"]
            if failed_checks:
                validation_result["overall_status"] = "invalid"
                validation_result["errors"] = [c["details"] for c in failed_checks]
            
            warning_checks = [c for c in validation_result["checks"] if c["status"] == "warning"]
            if warning_checks and validation_result["overall_status"] == "valid":
                validation_result["overall_status"] = "valid_with_warnings"
                validation_result["warnings"] = [c["details"] for c in warning_checks]
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return {
                "overall_status": "error",
                "error": str(e)
            }
    
    async def rollback_migration(self, workspace_id: UUID) -> Dict[str, Any]:
        """Rollback a migration if something went wrong."""
        try:
            logger.info(f"🔄 Starting rollback for workspace: {workspace_id}")
            
            rollback_result = {
                "workspace_id": str(workspace_id),
                "status": "in_progress",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "actions": []
            }
            
            # Remove asset requirements
            requirements_removed = await self.asset_db_manager.remove_workspace_asset_requirements(workspace_id)
            rollback_result["actions"].append(f"Removed {requirements_removed} asset requirements")
            
            # Remove quality rules
            rules_removed = await self.asset_db_manager.remove_workspace_quality_rules(workspace_id)
            rollback_result["actions"].append(f"Removed {rules_removed} quality rules")
            
            # Remove asset artifacts
            artifacts_removed = await self.asset_db_manager.remove_workspace_asset_artifacts(workspace_id)
            rollback_result["actions"].append(f"Removed {artifacts_removed} asset artifacts")
            
            # Reset goal asset metrics
            goals_reset = await self.asset_db_manager.reset_goal_asset_metrics(workspace_id)
            rollback_result["actions"].append(f"Reset asset metrics for {goals_reset} goals")
            
            rollback_result["status"] = "completed"
            rollback_result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ Rollback completed for workspace: {workspace_id}")
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Rollback failed for workspace {workspace_id}: {e}")
            return {
                "workspace_id": str(workspace_id),
                "status": "failed",
                "error": str(e)
            }
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Get comprehensive migration report."""
        return {
            "migration_statistics": self.stats,
            "migration_state": self.migration_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def main():
    """Main CLI interface for the migration script."""
    parser = argparse.ArgumentParser(description='Migrate workspace to asset-driven system')
    parser.add_argument('--workspace-id', type=str, required=True, help='Workspace UUID to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without making changes')
    parser.add_argument('--rollback', action='store_true', help='Rollback previous migration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        workspace_id = UUID(args.workspace_id)
    except ValueError:
        logger.error(f"Invalid workspace ID format: {args.workspace_id}")
        sys.exit(1)
    
    migration_manager = AssetDrivenMigrationManager()
    
    try:
        if args.rollback:
            logger.info("Starting rollback process...")
            result = await migration_manager.rollback_migration(workspace_id)
        else:
            logger.info(f"Starting migration process (dry_run={args.dry_run})...")
            result = await migration_manager.migrate_workspace(workspace_id, args.dry_run)
        
        # Print results
        print("\n" + "="*80)
        print("MIGRATION RESULT")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))
        
        # Print summary report
        report = migration_manager.get_migration_report()
        print("\n" + "="*80)
        print("MIGRATION REPORT")
        print("="*80)
        print(json.dumps(report, indent=2, default=str))
        
        if result["status"] == "completed":
            logger.info("✅ Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())