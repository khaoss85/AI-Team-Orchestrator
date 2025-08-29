# backend/routes/auto_completion.py

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from middleware.trace_middleware import get_trace_id, create_traced_logger
from services.missing_deliverable_auto_completion import (
    detect_missing_deliverables,
    auto_complete_missing_deliverable,
    unblock_goal
)

router = APIRouter(prefix="/auto-completion", tags=["auto-completion"])
logger = logging.getLogger(__name__)

class AutoCompleteRequest(BaseModel):
    deliverable_name: str
    workspace_id: str

class UnblockRequest(BaseModel):
    workspace_id: str

@router.get("/workspace/{workspace_id}/missing-deliverables")
async def get_missing_deliverables(workspace_id: str, request: Request):
    """Get missing deliverables for a workspace"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"🔍 Detecting missing deliverables for workspace {workspace_id}")
        
        missing_deliverables = await detect_missing_deliverables(workspace_id)
        
        logger.info(f"✅ Found {len(missing_deliverables)} goals with missing deliverables")
        
        return {
            'success': True,
            'missing_deliverables': missing_deliverables,
            'workspace_id': workspace_id,
            'detected_at': str(trace_id)  # Use trace_id as timestamp reference
        }
        
    except Exception as e:
        logger.error(f"❌ Error detecting missing deliverables for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect missing deliverables: {str(e)}")

@router.post("/goals/{goal_id}/auto-complete")
async def auto_complete_deliverable(
    goal_id: str, 
    request_data: AutoCompleteRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Auto-complete a missing deliverable for a goal"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"🚀 Auto-completing deliverable '{request_data.deliverable_name}' for goal {goal_id}")
        
        # Validate inputs
        if not request_data.deliverable_name.strip():
            raise HTTPException(status_code=400, detail="Deliverable name is required")
        
        if not request_data.workspace_id.strip():
            raise HTTPException(status_code=400, detail="Workspace ID is required")
        
        # Start auto-completion process
        result = await auto_complete_missing_deliverable(
            workspace_id=request_data.workspace_id,
            goal_id=goal_id,
            deliverable_name=request_data.deliverable_name
        )
        
        if result['success']:
            logger.info(f"✅ Successfully initiated auto-completion for deliverable: {request_data.deliverable_name}")
            return {
                'success': True,
                'message': result.get('message', 'Auto-completion initiated'),
                'task_id': result.get('task_id'),
                'goal_id': goal_id,
                'deliverable_name': request_data.deliverable_name
            }
        else:
            logger.warning(f"⚠️ Auto-completion failed for deliverable: {request_data.deliverable_name} - {result.get('error')}")
            
            if result.get('requires_manual_intervention'):
                return {
                    'success': False,
                    'error': result.get('error'),
                    'requires_manual_intervention': True,
                    'goal_id': goal_id,
                    'deliverable_name': request_data.deliverable_name
                }
            else:
                raise HTTPException(status_code=500, detail=result.get('error', 'Auto-completion failed'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in auto-completion for goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-completion error: {str(e)}")

@router.post("/goals/{goal_id}/unblock")
async def unblock_goal_endpoint(
    goal_id: str,
    request_data: UnblockRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Unblock a stuck goal"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"🔓 Attempting to unblock goal {goal_id}")
        
        # Validate workspace ID
        if not request_data.workspace_id.strip():
            raise HTTPException(status_code=400, detail="Workspace ID is required")
        
        # Attempt to unblock the goal
        result = await unblock_goal(
            workspace_id=request_data.workspace_id,
            goal_id=goal_id
        )
        
        if result['success']:
            logger.info(f"✅ Successfully unblocked goal {goal_id}: {result['message']}")
            return {
                'success': True,
                'message': result['message'],
                'actions_taken': result.get('actions_taken', []),
                'goal_id': goal_id
            }
        else:
            logger.error(f"❌ Failed to unblock goal {goal_id}: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to unblock goal'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error unblocking goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unblock error: {str(e)}")

@router.get("/workspace/{workspace_id}/auto-completion-status")
async def get_auto_completion_status(workspace_id: str, request: Request):
    """Get the current auto-completion status for a workspace"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"📊 Getting auto-completion status for workspace {workspace_id}")
        
        # Get missing deliverables
        missing_deliverables = await detect_missing_deliverables(workspace_id)
        
        # Calculate status metrics
        total_goals_with_missing = len(missing_deliverables)
        auto_completable = len([md for md in missing_deliverables if md.get('can_auto_complete', False)])
        blocked_goals = len([md for md in missing_deliverables if not md.get('can_auto_complete', False)])
        
        total_missing_deliverables = sum(len(md.get('missing_deliverables', [])) for md in missing_deliverables)
        
        status_summary = {
            'workspace_id': workspace_id,
            'total_goals_with_missing_deliverables': total_goals_with_missing,
            'auto_completable_goals': auto_completable,
            'blocked_goals': blocked_goals,
            'total_missing_deliverables': total_missing_deliverables,
            'auto_completion_enabled': True,  # Feature flag
            'last_check': str(trace_id),  # Use trace_id as timestamp reference
            'missing_deliverables_details': missing_deliverables
        }
        
        logger.info(f"✅ Auto-completion status: {auto_completable} completable, {blocked_goals} blocked, {total_missing_deliverables} total missing")
        
        return status_summary
        
    except Exception as e:
        logger.error(f"❌ Error getting auto-completion status for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get auto-completion status: {str(e)}")

@router.post("/workspace/{workspace_id}/missing-deliverables")
async def auto_complete_missing_deliverables_for_workspace(
    workspace_id: str,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Auto-complete missing deliverables for a specific workspace/goal"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"🚀 Auto-completing missing deliverables for workspace {workspace_id}")
        
        # Get all missing deliverables for this workspace
        missing_deliverables = await detect_missing_deliverables(workspace_id)
        
        if not missing_deliverables:
            logger.info(f"✅ No missing deliverables found for workspace {workspace_id}")
            return {
                'success': True,
                'message': 'No missing deliverables to complete',
                'workspace_id': workspace_id,
                'completed_deliverables': 0
            }
        
        completion_results = []
        successful_completions = 0
        
        # Process each goal with missing deliverables
        for goal_missing in missing_deliverables:
            goal_id = goal_missing.get('goal_id')
            can_auto_complete = goal_missing.get('can_auto_complete', False)
            
            if not can_auto_complete:
                logger.info(f"⏭️ Skipping blocked goal {goal_id}: {goal_missing.get('blocked_reason')}")
                continue
            
            # Auto-complete each missing deliverable for this goal
            for deliverable_name in goal_missing.get('missing_deliverables', []):
                try:
                    result = await auto_complete_missing_deliverable(
                        workspace_id=workspace_id,
                        goal_id=goal_id,
                        deliverable_name=deliverable_name
                    )
                    
                    if result.get('success'):
                        successful_completions += 1
                        logger.info(f"✅ Completed deliverable: {deliverable_name} for goal {goal_id}")
                    
                    completion_results.append({
                        'goal_id': goal_id,
                        'deliverable_name': deliverable_name,
                        'status': 'success' if result.get('success') else 'failed',
                        'task_id': result.get('task_id'),
                        'message': result.get('message', result.get('error'))
                    })
                    
                except Exception as deliverable_error:
                    logger.error(f"❌ Failed to complete {deliverable_name} for goal {goal_id}: {deliverable_error}")
                    completion_results.append({
                        'goal_id': goal_id,
                        'deliverable_name': deliverable_name,
                        'status': 'error',
                        'error': str(deliverable_error)
                    })
        
        logger.info(f"✅ Auto-completion finished: {successful_completions}/{len(completion_results)} successful")
        
        return {
            'success': True,
            'workspace_id': workspace_id,
            'total_attempts': len(completion_results),
            'successful_completions': successful_completions,
            'completion_results': completion_results,
            'message': f'Successfully completed {successful_completions} missing deliverables'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in auto-completion for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-completion error: {str(e)}")

@router.post("/workspace/{workspace_id}/auto-complete-all")
async def auto_complete_all_missing(
    workspace_id: str,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    🤖 ENHANCED AUTO-COMPLETE: Complete missing deliverables AND recover failed tasks
    This is the main endpoint for complete autonomous recovery
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    
    try:
        logger.info(f"🚀 ENHANCED AUTO-COMPLETE: Starting complete autonomous recovery for workspace {workspace_id}")
        
        # STEP 1: Autonomous Failed Task Recovery FIRST
        from services.failed_task_resolver import process_workspace_failed_tasks
        
        logger.info(f"🔧 STEP 1: Recovering failed tasks in workspace {workspace_id}")
        recovery_result = await process_workspace_failed_tasks(workspace_id)
        
        recovery_summary = {
            'failed_task_recovery_attempted': True,
            'recovery_success': recovery_result.get('success', False),
            'total_failed_tasks': recovery_result.get('total_processed', 0),
            'successful_recoveries': recovery_result.get('successful_recoveries', 0),
            'recovery_rate': recovery_result.get('recovery_rate', 0.0)
        }
        
        logger.info(f"🔧 RECOVERY COMPLETE: {recovery_summary['successful_recoveries']}/{recovery_summary['total_failed_tasks']} failed tasks recovered")
        
        # STEP 2: Auto-complete missing deliverables (original logic)
        logger.info(f"📦 STEP 2: Auto-completing missing deliverables for workspace {workspace_id}")
        
        # Get all missing deliverables
        missing_deliverables = await detect_missing_deliverables(workspace_id)
        
        completion_results = []
        
        for goal_missing in missing_deliverables:
            goal_id = goal_missing.get('goal_id')
            can_auto_complete = goal_missing.get('can_auto_complete', False)
            
            if not can_auto_complete:
                completion_results.append({
                    'goal_id': goal_id,
                    'status': 'skipped',
                    'reason': goal_missing.get('blocked_reason', 'Goal is blocked')
                })
                continue
            
            # Auto-complete each missing deliverable for this goal
            for deliverable_name in goal_missing.get('missing_deliverables', []):
                try:
                    result = await auto_complete_missing_deliverable(
                        workspace_id=workspace_id,
                        goal_id=goal_id,
                        deliverable_name=deliverable_name
                    )
                    
                    completion_results.append({
                        'goal_id': goal_id,
                        'deliverable_name': deliverable_name,
                        'status': 'success' if result['success'] else 'failed',
                        'task_id': result.get('task_id'),
                        'message': result.get('message', result.get('error'))
                    })
                    
                except Exception as deliverable_error:
                    logger.error(f"❌ Failed to auto-complete {deliverable_name} for goal {goal_id}: {deliverable_error}")
                    completion_results.append({
                        'goal_id': goal_id,
                        'deliverable_name': deliverable_name,
                        'status': 'error',
                        'error': str(deliverable_error)
                    })
        
        successful_completions = len([r for r in completion_results if r.get('status') == 'success'])
        
        logger.info(f"✅ ENHANCED AUTO-COMPLETE FINISHED:")
        logger.info(f"   💫 Failed Tasks: {recovery_summary['successful_recoveries']}/{recovery_summary['total_failed_tasks']} recovered")
        logger.info(f"   📦 Deliverables: {successful_completions}/{len(completion_results)} completed")
        
        return {
            'success': True,
            'workspace_id': workspace_id,
            'enhanced_auto_complete': True,
            
            # Failed Task Recovery Results
            'failed_task_recovery': recovery_summary,
            
            # Deliverable Completion Results
            'deliverable_completion': {
                'total_attempts': len(completion_results),
                'successful_completions': successful_completions,
                'completion_results': completion_results
            },
            
            # Overall Summary
            'overall_summary': {
                'total_actions': recovery_summary['total_failed_tasks'] + len(completion_results),
                'total_successes': recovery_summary['successful_recoveries'] + successful_completions,
                'autonomous_recovery_rate': (recovery_summary['successful_recoveries'] + successful_completions) / max(recovery_summary['total_failed_tasks'] + len(completion_results), 1),
                'human_intervention_required': False  # Always autonomous
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced auto-completion for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced auto-completion error: {str(e)}")