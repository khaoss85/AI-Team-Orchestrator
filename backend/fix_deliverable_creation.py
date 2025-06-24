#!/usr/bin/env python3
"""
Fix deliverable creation for completed goals
Forces deliverable generation when goals are 100% complete but no deliverables exist
"""
import asyncio
import logging
from database import supabase
from uuid import UUID

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_fix_deliverable_creation():
    """Check workspaces with completed goals but no deliverables and create them"""
    logger.info("🔧 Starting deliverable creation fix...")
    
    try:
        # Get all workspaces with completed goals
        goals_response = supabase.table('workspace_goals').select('*').eq('status', 'completed').execute()
        
        if not goals_response.data:
            logger.info("No completed goals found")
            return
        
        # Group by workspace
        workspaces_with_completed_goals = {}
        for goal in goals_response.data:
            workspace_id = goal['workspace_id']
            if workspace_id not in workspaces_with_completed_goals:
                workspaces_with_completed_goals[workspace_id] = []
            workspaces_with_completed_goals[workspace_id].append(goal)
        
        logger.info(f"Found {len(workspaces_with_completed_goals)} workspaces with completed goals")
        
        for workspace_id, goals in workspaces_with_completed_goals.items():
            logger.info(f"Checking workspace {workspace_id} with {len(goals)} completed goals")
            
            # Check if this workspace already has deliverables
            deliverables_response = supabase.table('deliverables').select('id').eq('workspace_id', workspace_id).execute()
            
            if deliverables_response.data:
                logger.info(f"  ✅ Workspace {workspace_id} already has {len(deliverables_response.data)} deliverables")
                continue
            
            # Get workspace tasks
            tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
            tasks = tasks_response.data or []
            
            # Check if we have enough completed/verified tasks
            completed_tasks = [t for t in tasks if t['status'] in ['completed', 'pending_verification']]
            
            if len(completed_tasks) < 2:
                logger.info(f"  ⚠️ Workspace {workspace_id} has only {len(completed_tasks)} completed tasks, need at least 2")
                continue
            
            # Check goal completion percentage
            total_goals = len(goals)
            all_completed = all(goal['current_value'] >= goal['target_value'] for goal in goals)
            
            if not all_completed:
                logger.info(f"  ⚠️ Workspace {workspace_id} has incomplete goals")
                continue
            
            logger.info(f"  🎯 Workspace {workspace_id} qualifies for deliverable creation:")
            logger.info(f"     - {total_goals} goals all completed")
            logger.info(f"     - {len(completed_tasks)} completed tasks")
            logger.info(f"     - No existing deliverables")
            
            # Force deliverable creation
            try:
                await force_create_deliverable(workspace_id, goals, completed_tasks)
                logger.info(f"  ✅ Successfully created deliverable for workspace {workspace_id}")
            except Exception as e:
                logger.error(f"  ❌ Failed to create deliverable for workspace {workspace_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in deliverable creation fix: {e}")

async def force_create_deliverable(workspace_id: str, goals: list, tasks: list):
    """Force create a deliverable for a workspace with completed goals"""
    
    # Get workspace info
    workspace_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
    workspace = workspace_response.data[0] if workspace_response.data else {}
    
    workspace_goal = workspace.get('goal', 'Complete project objectives')
    
    # Aggregate results from completed tasks
    task_results = []
    for task in tasks:
        if task.get('result') and isinstance(task['result'], dict):
            summary = task['result'].get('summary', '')
            detailed_results = task['result'].get('detailed_results_json', '{}')
            
            if summary:
                task_results.append({
                    'task_name': task['name'],
                    'summary': summary,
                    'detailed_results': detailed_results,
                    'agent_role': task.get('assigned_to_role', 'AI Agent'),
                    'created_at': task['created_at']
                })
    
    # AI-DRIVEN deliverable content generation (instead of hardcoded templates)
    from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
    
    # Create dynamic content using AI
    enhancer = AIContentEnhancer()
    
    # Generate AI-driven deliverable structure
    raw_content = {
        'workspace_goal': workspace_goal,
        'goals_data': goals,
        'task_results': task_results,
        'completion_context': f"{len(goals)} project objectives completed with {len(task_results)} deliverable outputs"
    }
    
    # Use AI to enhance and structure the deliverable content
    enhanced_content = await enhancer.enhance_deliverable_content(
        workspace_id=workspace_id,
        raw_content=raw_content,
        deliverable_type='final_completion_report'
    )
    
    deliverable_content = enhanced_content
    
    from database import create_deliverable

    payload = {
        'type': 'final_report',
        'title': f"Project Completion Report - {workspace.get('name', workspace_goal)[:50]}",
        'content': deliverable_content,
        'status': 'completed',
        'readiness_score': 100,
        'completion_percentage': 100,
        'business_value_score': 85,
    }
    created = await create_deliverable(workspace_id, payload)
    deliverable_id = created.get('id')
    if not deliverable_id:
        raise Exception(f"Failed to create deliverable via helper: {created}")
    logger.info(f"✅ Created deliverable with ID: {deliverable_id}")
    return deliverable_id

if __name__ == "__main__":
    asyncio.run(check_and_fix_deliverable_creation())