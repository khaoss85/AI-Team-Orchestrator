import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from utils.ai_utils import get_structured_ai_response

logger = logging.getLogger(__name__)

class QualityAssessment(BaseModel):
    passes_quality_gate: bool = Field(..., description="Whether the asset passes the quality gate.")
    score: int = Field(..., description="A quality score from 0 to 100.")
    reasoning: str = Field(..., description="The reasoning behind the quality assessment.")
    improvement_suggestions: List[str] = Field(..., description="Suggestions for improving the asset.")

class QualityGate:
    async def validate_asset(self, asset_data: Dict[str, Any], goal_context: Dict[str, Any]) -> QualityAssessment:
        """Validates the quality of a produced asset against the goal context."""
        prompt = f"""You are a Quality Assurance expert. Evaluate the following asset based on the provided goal context.

Goal Context:
{json.dumps(goal_context, indent=2)}

Asset Data:
{json.dumps(asset_data, indent=2)}

Based on the goal, does this asset meet the quality standards? Provide a score from 0 to 100, a reasoning, and concrete suggestions for improvement.
"""
        assessment = await get_structured_ai_response(prompt, QualityAssessment)
        if not assessment:
            logger.error("Failed to get a quality assessment from AI.")
            return QualityAssessment(
                passes_quality_gate=False,
                score=0,
                reasoning="Failed to assess quality.",
                improvement_suggestions=[]
            )
        
        # EVENT-DRIVEN: Create quality validation events for both orchestrator and deliverable pipeline
        if isinstance(asset_data, dict) and asset_data.get('task_id') and asset_data.get('workspace_id'):
            await self._create_quality_events(
                workspace_id=asset_data['workspace_id'],
                task_id=asset_data['task_id'],
                assessment=assessment
            )
            
            # LEARNING: Store quality validation learning in workspace memory
            await self._store_quality_learning(
                workspace_id=asset_data['workspace_id'],
                task_id=asset_data['task_id'],
                assessment=assessment,
                asset_data=asset_data
            )
        
        return assessment
    
    async def _create_quality_events(self, workspace_id: str, task_id: str, assessment: QualityAssessment):
        """Create quality validation events for both orchestrator and deliverable pipeline"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Event data payload
            event_data = {
                'task_id': task_id,
                'passes_quality_gate': assessment.passes_quality_gate,
                'score': assessment.score,
                'reasoning': assessment.reasoning
            }
            
            # Event for unified orchestrator
            orchestrator_event = {
                'workspace_id': workspace_id,
                'event_type': 'quality_validated',
                'source_component': 'quality_gate',
                'target_component': 'unified_orchestrator',
                'event_data': event_data,
                'status': 'pending'
            }
            
            # Event for deliverable pipeline
            deliverable_event = {
                'workspace_id': workspace_id,
                'event_type': 'quality_validated',
                'source_component': 'quality_gate',
                'target_component': 'deliverable_pipeline',
                'event_data': event_data,
                'status': 'pending'
            }
            
            # Insert both events
            supabase.table('integration_events').insert([orchestrator_event, deliverable_event]).execute()
            logger.debug(f"Created quality validation events for task {task_id} (orchestrator + deliverable)")
            
        except Exception as e:
            logger.error(f"Failed to create quality events: {e}")
    
    async def _create_quality_event(self, workspace_id: str, task_id: str, assessment: QualityAssessment):
        """Legacy method - kept for backward compatibility"""
        await self._create_quality_events(workspace_id, task_id, assessment)
    
    async def _store_quality_learning(self, workspace_id: str, task_id: str, 
                                    assessment: QualityAssessment, asset_data: Dict[str, Any]):
        """Store quality validation learning in workspace memory"""
        try:
            from uuid import UUID
            from workspace_memory import workspace_memory
            
            # Prepare quality assessment data
            quality_assessment = {
                'passes_quality_gate': assessment.passes_quality_gate,
                'score': assessment.score,
                'reasoning': assessment.reasoning
            }
            
            # Extract task context from asset_data
            task_context = {
                'task_type': asset_data.get('task_type', 'unknown'),
                'agent_id': asset_data.get('agent_id', 'unknown'),
                'goal_id': asset_data.get('goal_id'),
                'asset_type': asset_data.get('type', 'unknown'),
                'content_length': len(str(asset_data.get('content', ''))),
                'validation_context': asset_data.get('validation_context', {})
            }
            
            # Store learning in workspace memory
            await workspace_memory.store_quality_validation_learning(
                workspace_id=UUID(workspace_id),
                task_id=task_id,
                quality_assessment=quality_assessment,
                task_context=task_context
            )
            
            logger.debug(f"✅ Quality learning stored for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to store quality learning for task {task_id}: {e}")
            # Non-blocking error - quality validation should still succeed