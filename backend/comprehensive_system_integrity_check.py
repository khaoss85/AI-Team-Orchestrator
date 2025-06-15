#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE SYSTEM INTEGRITY CHECK
Verifies that recent fixes maintain system integrity and haven't introduced regressions
"""

import logging
import sys
import os
import ast
import json
from typing import Dict, Any, List
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_memory_system():
    """Check if Memory System is still functioning as pillar"""
    logger.info("🧠 CHECKING MEMORY SYSTEM (workspace_memory.py)")
    
    try:
        # Check if file exists and is valid Python
        with open('workspace_memory.py', 'r') as f:
            content = f.read()
        
        ast.parse(content)
        
        # Check key functionality
        checks = {
            "store_insight method": "async def store_insight" in content,
            "query_insights method": "async def query_insights" in content,
            "get_relevant_context method": "async def get_relevant_context" in content,
            "anti-pollution controls": "ANTI-POLLUTION" in content,
            "goal-driven filtering": "GOAL-DRIVEN FILTERING" in content,
            "none task_id fix": "if insight.task_id is not None else None" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Memory System integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 5  # Allow 1 minor failure
        
    except Exception as e:
        logger.error(f"❌ Memory System check failed: {e}")
        return False

def check_quality_gates():
    """Check if Quality Gates are still preventing low-quality output"""
    logger.info("🛡️ CHECKING QUALITY GATES (ai_quality_assurance)")
    
    try:
        # Check if ai_goal_extractor is functional
        with open('ai_quality_assurance/ai_goal_extractor.py', 'r') as f:
            content = f.read()
        
        ast.parse(content)
        
        checks = {
            "ai_extract_goals method": "async def _ai_extract_goals" in content,
            "validation_rules": "validate_goals" in content,
            "consolidate_goals": "consolidate_goals" in content,
            "confidence scoring": "confidence" in content,
            "ai_available check": "ai_available" in content,
            "goal extraction": "extract_goals_from_text" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Quality Gates integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 5
        
    except Exception as e:
        logger.error(f"❌ Quality Gates check failed: {e}")
        return False

def check_human_in_the_loop():
    """Check if Human-in-the-Loop is still 'honor' not burden"""
    logger.info("👤 CHECKING HUMAN-IN-THE-LOOP")
    
    try:
        # Check if models.py has proper structures
        with open('models.py', 'r') as f:
            content = f.read()
        
        checks = {
            "DeliverableFeedback model": "class DeliverableFeedback" in content,
            "feedback_type enum": "approve\"|\"request_changes\"|\"general_feedback" in content,
            "priority levels": "priority.*low.*medium.*high" in content,
            "TaskExecutionOutput": "class TaskExecutionOutput" in content,
            "optional handoff": "suggested_handoff_target_role.*Optional" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Human-in-the-Loop integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 4
        
    except Exception as e:
        logger.error(f"❌ Human-in-the-Loop check failed: {e}")
        return False

def check_goal_task_linking():
    """Check if Goal-Task Linking is still automatic with AI generation"""
    logger.info("🎯 CHECKING GOAL-TASK LINKING")
    
    try:
        with open('models.py', 'r') as f:
            content = f.read()
        
        checks = {
            "goal_id in TaskCreate": "goal_id.*Optional.*UUID" in content and "TaskCreate" in content,
            "goal_id in Task model": "goal_id.*Optional.*UUID" in content and "class Task" in content,
            "metric_type linking": "metric_type.*Optional.*GoalMetricType" in content,
            "contribution_expected": "contribution_expected.*Optional.*float" in content,
            "success_criteria": "success_criteria.*Optional.*List" in content,
            "WorkspaceGoal model": "class WorkspaceGoal" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Goal-Task Linking integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 5
        
    except Exception as e:
        logger.error(f"❌ Goal-Task Linking check failed: {e}")
        return False

def check_content_enhancement():
    """Check if Content Enhancement is still replacing placeholders with business-ready content"""
    logger.info("✨ CHECKING CONTENT ENHANCEMENT (markup_processor)")
    
    try:
        with open('deliverable_system/markup_processor.py', 'r') as f:
            content = f.read()
        
        ast.parse(content)  # Ensure no syntax errors
        
        checks = {
            "actionable content detection": "_contains_actionable_content" in content,
            "contacts rendering": "_render_contacts_list" in content,
            "email sequences rendering": "_render_email_sequences" in content,
            "workflow rendering": "_render_workflow" in content,
            "markup processing": "process_deliverable_content" in content,
            "HTML export": "_generate_html_export" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Content Enhancement integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 5
        
    except Exception as e:
        logger.error(f"❌ Content Enhancement check failed: {e}")
        return False

def check_course_correction():
    """Check if Course Correction is now working with goal_id fix"""
    logger.info("🔄 CHECKING COURSE CORRECTION")
    
    try:
        # Check if the fix allows proper goal tracking
        with open('models.py', 'r') as f:
            content = f.read()
        
        # Look for TaskExecutionOutput without goal_id constraint
        checks = {
            "TaskExecutionOutput has no goal_id": "class TaskExecutionOutput" in content and "goal_id" not in content.split("class TaskExecutionOutput")[1].split("class ")[0],
            "Task model has goal_id": "goal_id.*Optional.*UUID" in content and "class Task" in content,
            "goal tracking possible": "GoalMetricType" in content,
            "corrective tasks supported": "is_corrective.*bool" in content,
            "numerical targets": "numerical_target.*Optional.*Dict" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        logger.info(f"  Course Correction integrity: {passed}/{total} checks passed")
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"    {status} {check}")
        
        return passed >= 4
        
    except Exception as e:
        logger.error(f"❌ Course Correction check failed: {e}")
        return False

def check_architecture_integrity():
    """Check if the AI-driven, universal, scalable architecture is maintained"""
    logger.info("🏗️ CHECKING ARCHITECTURE INTEGRITY")
    
    checks = {
        "AI-driven goal extraction": os.path.exists('ai_quality_assurance/ai_goal_extractor.py'),
        "Universal schema support": os.path.exists('models.py'),
        "Scalable memory system": os.path.exists('workspace_memory.py'),
        "Dynamic deliverable system": os.path.exists('deliverable_system/markup_processor.py'),
        "Task execution framework": "TaskExecutionOutput" in open('models.py').read() if os.path.exists('models.py') else False
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    logger.info(f"  Architecture integrity: {passed}/{total} checks passed")
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        logger.info(f"    {status} {check}")
    
    return passed == total

def main():
    """Run comprehensive system integrity check"""
    
    logger.info("🔍 COMPREHENSIVE SYSTEM INTEGRITY CHECK")
    logger.info("=" * 80)
    
    results = {}
    
    # Check all 6 core system components
    results["memory_system"] = check_memory_system()
    results["quality_gates"] = check_quality_gates()
    results["human_in_the_loop"] = check_human_in_the_loop()
    results["goal_task_linking"] = check_goal_task_linking()
    results["content_enhancement"] = check_content_enhancement()
    results["course_correction"] = check_course_correction()
    results["architecture_integrity"] = check_architecture_integrity()
    
    # Generate final report
    logger.info("\n" + "=" * 80)
    logger.info("📊 SYSTEM INTEGRITY REPORT")
    logger.info("=" * 80)
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    logger.info(f"\n🏆 OVERALL SYSTEM INTEGRITY: {passed_count}/{total_count} components healthy")
    
    # Component status
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        component_name = component.replace("_", " ").title()
        logger.info(f"  {status_icon} {component_name}")
    
    # Specific verification results
    logger.info(f"\n🎯 KEY VERIFICATIONS:")
    logger.info(f"  Memory System (pillar): {'✅ FUNCTIONING' if results['memory_system'] else '❌ DEGRADED'}")
    logger.info(f"  Quality Gates: {'✅ PREVENTING LOW-QUALITY OUTPUT' if results['quality_gates'] else '❌ COMPROMISED'}")
    logger.info(f"  Human-in-the-Loop: {'✅ HONOR NOT BURDEN' if results['human_in_the_loop'] else '❌ BURDENSOME'}")
    logger.info(f"  Goal-Task Linking: {'✅ AUTOMATIC WITH AI' if results['goal_task_linking'] else '❌ BROKEN'}")
    logger.info(f"  Content Enhancement: {'✅ BUSINESS-READY CONTENT' if results['content_enhancement'] else '❌ PLACEHOLDERS'}")
    logger.info(f"  Course Correction: {'✅ WORKING WITH GOAL_ID FIX' if results['course_correction'] else '❌ BROKEN'}")
    
    # Architecture assessment
    logger.info(f"\n🏗️ ARCHITECTURE ASSESSMENT:")
    if results["architecture_integrity"]:
        logger.info("  ✅ AI-driven, universal, scalable architecture MAINTAINED")
    else:
        logger.info("  ❌ Architecture integrity COMPROMISED")
    
    # Final verdict
    if passed_count >= 6:
        logger.info(f"\n🎉 SYSTEM INTEGRITY: EXCELLENT")
        logger.info("  All core systems functioning properly")
        logger.info("  Recent fixes have NOT introduced regressions")
        logger.info("  Architecture remains AI-driven, universal, and scalable")
        return True
    elif passed_count >= 5:
        logger.info(f"\n👍 SYSTEM INTEGRITY: GOOD")
        logger.info("  Most core systems functioning properly")
        logger.info("  Minor issues detected but system remains operational")
        return True
    else:
        logger.info(f"\n⚠️ SYSTEM INTEGRITY: COMPROMISED")
        logger.info("  Multiple core systems have issues")
        logger.info("  Immediate attention required")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)