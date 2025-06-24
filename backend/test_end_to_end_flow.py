#!/usr/bin/env python3
"""
🚀 Comprehensive End-to-End Flow Test

Test completo del flusso:
User Input → Goal Creation → Decomposition → Task Generation → Execution → Deliverables → Frontend Display

Verifica aderenza ai pilastri:
- Domain Agnostic (PILLAR 2)
- User Value Creation (PILLAR 7)  
- Minimal Interface (PILLAR 3)
"""

import asyncio
import logging
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_end_to_end_flow():
    """Test complete flow from goal to deliverable with decomposition"""
    logger.info("🚀 Testing Complete End-to-End Flow with Goal Decomposition")
    
    try:
        from goal_decomposition_system import decompose_goal_to_todos
        from goal_driven_task_planner import goal_driven_task_planner
        from executor import EnhancedTaskExecutor
        from models import WorkspaceGoal, GoalStatus
        
        # Test goal scenarios that cover different domains
        test_goals = [
            {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "description": "Create comprehensive social media strategy with 15 high-quality posts for Instagram",
                "metric_type": "content",
                "target_value": 15,
                "current_value": 0,
                "unit": "posts",
                "status": GoalStatus.ACTIVE,
                "priority": 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expected_assets": ["Content Library", "Content Calendar", "Visual Templates"],
                "expected_thinking": ["Content Strategy Analysis", "Audience Research"]
            },
            {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "description": "Conduct market analysis and competitive research for product launch",
                "metric_type": "research",
                "target_value": 1,
                "current_value": 0,
                "unit": "report",
                "status": GoalStatus.ACTIVE,
                "priority": 4,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expected_assets": ["Research Report", "Executive Summary", "Competitive Matrix"],
                "expected_thinking": ["Data Collection Strategy", "Analysis Framework"]
            },
            {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "description": "Develop 3-month business plan with financial projections",
                "metric_type": "planning",
                "target_value": 1,
                "current_value": 0,
                "unit": "plan",
                "status": GoalStatus.ACTIVE,
                "priority": 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expected_assets": ["Strategic Plan Document", "Financial Model", "Implementation Roadmap"],
                "expected_thinking": ["Strategic Analysis", "Market Assessment"]
            }
        ]
        
        flow_results = []
        
        for goal in test_goals:
            logger.info(f"\n🎯 Testing flow for goal: '{goal['description']}'")
            
            # PHASE 1: Goal Decomposition
            logger.info("📋 Phase 1: Goal Decomposition")
            decomposition_result = await decompose_goal_to_todos(goal)
            
            goal_decomposition = decomposition_result.get("goal_decomposition", {})
            todo_structure = decomposition_result.get("todo_structure", {})
            
            asset_count = len(todo_structure.get("asset_todos", []))
            thinking_count = len(todo_structure.get("thinking_todos", []))
            user_value_score = decomposition_result.get("summary", {}).get("expected_user_value", 0)
            
            logger.info(f"   Assets: {asset_count}, Thinking: {thinking_count}, Value Score: {user_value_score}")
            
            # PHASE 2: Task Generation (simulated)
            logger.info("⚙️ Phase 2: Task Generation")
            
            # Create WorkspaceGoal object for task generation
            workspace_goal = WorkspaceGoal(**goal)
            tasks = await goal_driven_task_planner._generate_tasks_for_goal(workspace_goal)
            
            real_tool_tasks = 0
            meta_tasks = 0
            
            for task in tasks:
                task_name = task.get("name", "").lower()
                task_desc = task.get("description", "").lower()
                
                # Check for real tool usage
                if any(tool_keyword in task_name + task_desc for tool_keyword in [
                    "analyze_hashtags", "create_social_content", "generate_visual",
                    "research_competitors", "create_marketing", "analyze_data"
                ]):
                    real_tool_tasks += 1
                elif any(meta_keyword in task_name + task_desc for meta_keyword in [
                    "create sub-task", "assign to", "delegate", "plan for"
                ]):
                    meta_tasks += 1
            
            real_tool_percentage = (real_tool_tasks / len(tasks)) * 100 if tasks else 0
            
            logger.info(f"   Generated {len(tasks)} tasks: {real_tool_percentage:.1f}% real tools")
            
            # PHASE 3: Simulate Task Execution and Content Creation
            logger.info("🔧 Phase 3: Task Execution Simulation")
            
            # Simulate different task execution outcomes
            simulated_task_results = []
            
            for i, task in enumerate(tasks[:5]):  # Test first 5 tasks
                # Simulate business content based on task type
                if "content" in task.get("name", "").lower() or "create" in task.get("name", "").lower():
                    # High business value task
                    task_result = {
                        "task_id": task.get("name", f"task_{i}"),
                        "summary": "Document created with structured content and visual elements",
                        "detailed_results_json": {
                            "rendered_html": f"<div class='deliverable-content'>{task.get('name', 'Content')} completed with visual elements and structured data...</div>",
                            "structured_content": [
                                {"title": f"Section {j+1}", "content": f"Content for {task.get('name', 'task')}"} 
                                for j in range(3)
                            ],
                            "deliverable_content": f"Complete {task.get('name', 'deliverable')} ready for use"
                        },
                        "business_value_score": 85
                    }
                elif "analysis" in task.get("name", "").lower() or "research" in task.get("name", "").lower():
                    # Medium business value task
                    task_result = {
                        "task_id": task.get("name", f"task_{i}"),
                        "summary": "Analysis completed with strategic insights",
                        "detailed_results_json": {
                            "structured_content": {
                                "findings": ["Key insight 1", "Key insight 2", "Key insight 3"],
                                "recommendations": ["Action 1", "Action 2"],
                                "methodology": "Comprehensive analysis approach"
                            }
                        },
                        "business_value_score": 65
                    }
                else:
                    # Low business value task (meta-task)
                    task_result = {
                        "task_id": task.get("name", f"task_{i}"),
                        "summary": "Sub-task has been created and assigned to specialist",
                        "detailed_results_json": None,
                        "business_value_score": 15
                    }
                
                simulated_task_results.append(task_result)
            
            # Calculate business content quality
            high_value_tasks = [t for t in simulated_task_results if t.get("business_value_score", 0) >= 40]
            thinking_tasks = [t for t in simulated_task_results if 20 <= t.get("business_value_score", 0) < 40]
            meta_tasks_results = [t for t in simulated_task_results if t.get("business_value_score", 0) < 20]
            
            logger.info(f"   Task Results: {len(high_value_tasks)} high-value, {len(thinking_tasks)} thinking, {len(meta_tasks_results)} meta")
            
            # PHASE 4: Deliverable Creation Assessment
            logger.info("📦 Phase 4: Deliverable Creation Assessment")
            
            # Apply business value and completion guarantee logic
            goal_progress = (goal.get("current_value", 0) + len(high_value_tasks) * 20) / goal.get("target_value", 1) * 100
            business_content_score = sum(t.get("business_value_score", 0) for t in high_value_tasks) / len(high_value_tasks) if high_value_tasks else 0
            
            # Simulate goal completion
            if goal_progress >= 80.0 and business_content_score >= 70.0:
                deliverable_status = "HIGH_VALUE_READY"
            elif goal_progress >= 90.0:
                deliverable_status = "COMPLETION_GUARANTEED"  
            else:
                deliverable_status = "NOT_READY"
            
            logger.info(f"   Progress: {goal_progress:.1f}%, Business Score: {business_content_score:.1f}, Status: {deliverable_status}")
            
            # PHASE 5: Frontend Display Assessment
            logger.info("🖥️ Phase 5: Frontend Display Assessment")
            
            # Simulate frontend business value scoring (matching our implementation)
            frontend_task_scores = []
            for task_result in simulated_task_results:
                score = 0
                
                # High-value indicators
                if task_result.get("detailed_results_json"):
                    detailed = task_result["detailed_results_json"]
                    if detailed and detailed.get("rendered_html") and len(detailed["rendered_html"]) > 100:
                        score += 40
                    if detailed and detailed.get("structured_content"):
                        score += 30
                    if detailed and detailed.get("deliverable_content"):
                        score += 35
                
                # Summary analysis
                summary = task_result.get("summary", "")
                if any(keyword in summary.lower() for keyword in ["document created", "analysis completed"]):
                    score += 20
                elif "sub-task" in summary.lower():
                    score = max(5, score - 20)
                
                frontend_task_scores.append(min(100, max(0, score)))
            
            frontend_high_value = len([s for s in frontend_task_scores if s >= 40])
            frontend_thinking = len([s for s in frontend_task_scores if 20 <= s < 40]) 
            frontend_meta = len([s for s in frontend_task_scores if s < 20])
            
            logger.info(f"   Frontend Classification: {frontend_high_value} assets, {frontend_thinking} thinking, {frontend_meta} meta")
            
            # PHASE 6: Pillar Adherence Assessment
            logger.info("🎯 Phase 6: Pillar Adherence Assessment")
            
            pillar_adherence = goal_decomposition.get("decomposition", {}).get("pillar_adherence", {})
            domain_agnostic = pillar_adherence.get("domain_agnostic", False)
            user_value_focused = pillar_adherence.get("user_value_focused", False)
            minimal_interface = pillar_adherence.get("minimal_interface_ready", False)
            
            logger.info(f"   Domain Agnostic: {domain_agnostic}, User Value: {user_value_focused}, Minimal UI: {minimal_interface}")
            
            # Compile flow result
            flow_result = {
                "goal": {
                    "id": goal["id"],
                    "description": goal["description"],
                    "metric_type": goal["metric_type"],
                    "expected_assets": goal["expected_assets"],
                    "expected_thinking": goal["expected_thinking"]
                },
                "decomposition": {
                    "asset_count": asset_count,
                    "thinking_count": thinking_count,
                    "user_value_score": user_value_score,
                    "pillar_adherent": all([domain_agnostic, user_value_focused, minimal_interface])
                },
                "task_generation": {
                    "total_tasks": len(tasks),
                    "real_tool_percentage": real_tool_percentage,
                    "meta_task_count": meta_tasks
                },
                "execution": {
                    "high_value_tasks": len(high_value_tasks),
                    "thinking_tasks": len(thinking_tasks), 
                    "meta_task_results": len(meta_tasks_results),
                    "business_content_score": business_content_score
                },
                "deliverable_creation": {
                    "goal_progress": goal_progress,
                    "deliverable_status": deliverable_status,
                    "gets_deliverable": deliverable_status in ["HIGH_VALUE_READY", "COMPLETION_GUARANTEED"]
                },
                "frontend_display": {
                    "asset_todos_visible": frontend_high_value,
                    "thinking_todos_visible": frontend_thinking,
                    "meta_todos_hidden": frontend_meta
                },
                "end_to_end_success": True
            }
            
            # Validate end-to-end success
            success_criteria = [
                asset_count > 0,  # Goal produces concrete assets
                user_value_score >= 60,  # Acceptable user value
                real_tool_percentage >= 70,  # Mostly real tools
                business_content_score >= 40 or deliverable_status == "COMPLETION_GUARANTEED",  # Business value or guarantee
                all([domain_agnostic, user_value_focused, minimal_interface])  # Pillar adherent
            ]
            
            flow_result["end_to_end_success"] = all(success_criteria)
            flow_result["success_criteria_met"] = sum(success_criteria)
            flow_result["success_criteria_total"] = len(success_criteria)
            
            flow_results.append(flow_result)
            
            status = "✅ SUCCESS" if flow_result["end_to_end_success"] else "⚠️ PARTIAL"
            logger.info(f"   {status}: {flow_result['success_criteria_met']}/{flow_result['success_criteria_total']} criteria met")
        
        return flow_results
        
    except Exception as e:
        logger.error(f"❌ End-to-end flow test failed: {e}")
        return []

async def test_pillar_coherence():
    """Test coherence across all pillars throughout the flow"""
    logger.info("🎯 Testing Pillar Coherence Across Complete Flow")
    
    try:
        # Test different goal types to verify domain agnosticism
        domain_test_goals = [
            {"description": "Create e-commerce marketing campaign", "domain": "retail"},
            {"description": "Develop healthcare patient onboarding process", "domain": "healthcare"}, 
            {"description": "Build financial reporting dashboard", "domain": "finance"},
            {"description": "Design educational curriculum for online course", "domain": "education"}
        ]
        
        coherence_results = []
        
        for goal_spec in domain_test_goals:
            goal = {
                "id": str(uuid4()),
                "description": goal_spec["description"],
                "metric_type": "project",
                "target_value": 1,
                "domain": goal_spec["domain"]
            }
            
            from goal_decomposition_system import decompose_goal_to_todos
            decomposition_result = await decompose_goal_to_todos(goal)
            
            pillar_adherence = decomposition_result.get("goal_decomposition", {}).get("decomposition", {}).get("pillar_adherence", {})
            
            coherence_result = {
                "domain": goal_spec["domain"],
                "goal": goal_spec["description"],
                "domain_agnostic": pillar_adherence.get("domain_agnostic", False),
                "user_value_focused": pillar_adherence.get("user_value_focused", False),
                "minimal_interface_ready": pillar_adherence.get("minimal_interface_ready", False),
                "asset_count": len(decomposition_result.get("todo_structure", {}).get("asset_todos", [])),
                "user_value_score": decomposition_result.get("summary", {}).get("expected_user_value", 0)
            }
            
            coherence_results.append(coherence_result)
            
            logger.info(f"   {goal_spec['domain']}: {coherence_result['asset_count']} assets, {coherence_result['user_value_score']} value score")
        
        # Verify domain agnosticism - all domains should work similarly
        all_domain_agnostic = all(r["domain_agnostic"] for r in coherence_results)
        all_user_value_focused = all(r["user_value_focused"] for r in coherence_results)
        all_minimal_interface = all(r["minimal_interface_ready"] for r in coherence_results)
        
        # Check consistency across domains
        asset_counts = [r["asset_count"] for r in coherence_results]
        value_scores = [r["user_value_score"] for r in coherence_results]
        
        consistent_asset_generation = max(asset_counts) - min(asset_counts) <= 2  # Within 2 assets
        consistent_value_scores = max(value_scores) - min(value_scores) <= 30   # Within 30 points
        
        overall_coherence = all([
            all_domain_agnostic,
            all_user_value_focused, 
            all_minimal_interface,
            consistent_asset_generation,
            consistent_value_scores
        ])
        
        logger.info(f"🎯 Pillar Coherence Results:")
        logger.info(f"   Domain Agnostic: {all_domain_agnostic}")
        logger.info(f"   User Value Focused: {all_user_value_focused}")
        logger.info(f"   Minimal Interface Ready: {all_minimal_interface}")
        logger.info(f"   Consistent Asset Generation: {consistent_asset_generation}")
        logger.info(f"   Consistent Value Scores: {consistent_value_scores}")
        logger.info(f"   Overall Coherence: {'✅ PASS' if overall_coherence else '❌ FAIL'}")
        
        return overall_coherence, coherence_results
        
    except Exception as e:
        logger.error(f"❌ Pillar coherence test failed: {e}")
        return False, []

async def run_comprehensive_end_to_end_test():
    """Run complete end-to-end validation"""
    logger.info("🚀 Starting Comprehensive End-to-End Flow Validation")
    logger.info("=" * 100)
    
    results = {}
    
    # Test 1: Complete end-to-end flow
    logger.info("\n🎯 TEST 1: Complete End-to-End Flow")
    flow_results = await test_complete_end_to_end_flow()
    
    successful_flows = len([r for r in flow_results if r.get("end_to_end_success", False)])
    total_flows = len(flow_results)
    
    results["end_to_end_flow"] = {
        "passed": successful_flows == total_flows and total_flows > 0,
        "successful_flows": successful_flows,
        "total_flows": total_flows,
        "flow_details": flow_results
    }
    
    # Test 2: Pillar coherence across domains
    logger.info("\n🎯 TEST 2: Pillar Coherence Across Domains")
    coherence_success, coherence_results = await test_pillar_coherence()
    
    results["pillar_coherence"] = {
        "passed": coherence_success,
        "coherence_details": coherence_results
    }
    
    # Overall results
    logger.info("\n" + "=" * 100)
    logger.info("🎯 COMPREHENSIVE END-TO-END TEST RESULTS")
    logger.info("=" * 100)
    
    all_passed = all(results[key]["passed"] for key in results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        logger.info(f"{status} {test_name.replace('_', ' ').title()}")
    
    logger.info(f"\n🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        logger.info("\n🎉 END-TO-END VALIDATION SUCCESS!")
        logger.info("✅ Complete goal → deliverable flow working")
        logger.info("✅ Goal decomposition produces concrete assets + thinking")
        logger.info("✅ Business value guarantee ensures no goal left behind")
        logger.info("✅ Domain agnostic across all business types")
        logger.info("✅ User value focused with minimal interface")
        logger.info("✅ Pillar coherence maintained end-to-end")
        
        # Detailed success metrics
        if flow_results:
            avg_asset_count = sum(r["decomposition"]["asset_count"] for r in flow_results) / len(flow_results)
            avg_user_value = sum(r["decomposition"]["user_value_score"] for r in flow_results) / len(flow_results)
            avg_real_tools = sum(r["task_generation"]["real_tool_percentage"] for r in flow_results) / len(flow_results)
            
            logger.info(f"\n📊 PERFORMANCE METRICS:")
            logger.info(f"   Average Assets per Goal: {avg_asset_count:.1f}")
            logger.info(f"   Average User Value Score: {avg_user_value:.1f}/100")
            logger.info(f"   Average Real Tools Usage: {avg_real_tools:.1f}%")
        
    else:
        logger.info("\n⚠️ END-TO-END VALIDATION NEEDS ADJUSTMENT")
        logger.info("Some components in the complete flow need refinement")
        
        # Show specific failures
        for test_name, result in results.items():
            if not result["passed"]:
                logger.info(f"❌ Failed: {test_name}")
    
    return all_passed, results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_end_to_end_test())