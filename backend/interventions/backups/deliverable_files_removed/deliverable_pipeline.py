"""
Deliverable Pipeline - Sistema di Generazione Deliverables Event-Driven

Integrato con:
- integration_events per trigger automatici
- asset_artifacts table per persistenza
- quality_gate per validazione
- concrete_asset_extractor per content generation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from database import get_supabase_client, create_task, get_workspace_goals, list_tasks
from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from .requirements_analyzer import RequirementsAnalyzer
from models import AssetArtifact, AssetRequirement

logger = logging.getLogger(__name__)


class DeliverablePipeline:
    """
    Pipeline automatica per generazione deliverables da task completati
    """
    
    def __init__(self):
        self.asset_extractor = ConcreteAssetExtractor()
        self.requirements_analyzer = RequirementsAnalyzer()
        self.supabase = get_supabase_client()
        self._running = False
    
    async def start(self):
        """Start deliverable pipeline"""
        self._running = True
        logger.info("🚀 Starting Deliverable Pipeline...")
        
        # Update component health
        await self._update_component_health('deliverable_pipeline', 'healthy')
        
        # Start event processing loop
        await self._event_processor_loop()
    
    async def stop(self):
        """Stop deliverable pipeline"""
        self._running = False
        await self._update_component_health('deliverable_pipeline', 'stopped')
        logger.info("🛑 Deliverable Pipeline stopped")
    
    async def _event_processor_loop(self):
        """Process deliverable events"""
        while self._running:
            try:
                # Get pending deliverable events
                events = await self._get_pending_deliverable_events()
                
                for event in events:
                    await self._process_deliverable_event(event)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Deliverable pipeline error: {e}")
                await self._update_component_health('deliverable_pipeline', 'degraded', str(e))
                await asyncio.sleep(30)
    
    async def _process_deliverable_event(self, event: Dict[str, Any]):
        """Process a single deliverable event"""
        try:
            event_type = event.get('event_type')
            workspace_id = event.get('workspace_id')
            event_data = event.get('event_data', {})
            
            if event_type == 'ready_for_deliverable':
                await self._generate_deliverable(workspace_id, event_data)
            elif event_type == 'task_completed':
                await self._process_task_completion(workspace_id, event_data)
            elif event_type == 'quality_validated':
                await self._process_quality_validation(workspace_id, event_data)
            
            # Mark event as processed
            await self._mark_event_processed(event['id'])
            
        except Exception as e:
            logger.error(f"Error processing deliverable event {event['id']}: {e}")
            await self._mark_event_failed(event['id'], str(e))
    
    async def _generate_deliverable(self, workspace_id: str, event_data: Dict[str, Any]):
        """Generate deliverable for workspace"""
        try:
            logger.info(f"🎯 Generating deliverable for workspace {workspace_id}")
            
            # Get workspace context
            workspace_goals = await get_workspace_goals(workspace_id)
            if not workspace_goals:
                logger.warning(f"No goals found for workspace {workspace_id}")
                return
            
            # Get completed tasks
            completed_tasks = await list_tasks(
                workspace_id=workspace_id,
                status=['completed']
            )
            
            if not completed_tasks:
                logger.warning(f"No completed tasks found for workspace {workspace_id}")
                return
            
            # Determine deliverable type based on workspace goals
            deliverable_type = await self._determine_deliverable_type(workspace_goals)
            
            # Extract concrete assets
            assets = await self.asset_extractor.extract_concrete_assets(
                completed_tasks=completed_tasks,
                workspace_goal=workspace_goals[0].get('description', ''),
                deliverable_type=deliverable_type
            )
            
            # Create asset artifacts in database
            artifact_ids = []
            for asset_name, asset_data in assets.items():
                if asset_name.startswith('_'):  # Skip metadata
                    continue
                
                artifact_id = await self._create_asset_artifact(
                    workspace_id=workspace_id,
                    asset_name=asset_name,
                    asset_data=asset_data,
                    deliverable_type=deliverable_type
                )
                
                if artifact_id:
                    artifact_ids.append(artifact_id)
            
            # Create integration event for deliverable completion
            await self._create_integration_event(
                workspace_id=workspace_id,
                event_type='deliverable_completed',
                source_component='deliverable_pipeline',
                target_component='unified_orchestrator',
                event_data={
                    'deliverable_type': deliverable_type,
                    'artifact_ids': artifact_ids,
                    'asset_count': len(artifact_ids)
                }
            )
            
            # 🛡️ AUTOMATIC QUALITY TRIGGER: Trigger quality validation on deliverable creation
            try:
                from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
                quality_trigger = unified_quality_engine.get_automatic_quality_trigger()
                
                # Trigger immediate quality check for new artifacts
                quality_result = await quality_trigger.trigger_immediate_quality_check(workspace_id)
                
                if quality_result.get("status") == "completed":
                    logger.info(f"✅ Quality validation triggered for deliverable: {quality_result.get('new_validations', 0)} validations created")
                else:
                    logger.warning(f"⚠️ Quality validation failed for deliverable: {quality_result.get('error', 'Unknown error')}")
                    
            except Exception as quality_error:
                logger.error(f"Error triggering quality validation for deliverable: {quality_error}")
            
            logger.info(f"✅ Deliverable generated for workspace {workspace_id}: {len(artifact_ids)} assets created")
            
        except Exception as e:
            logger.error(f"Failed to generate deliverable for workspace {workspace_id}: {e}")
            raise
    
    async def _process_task_completion(self, workspace_id: str, event_data: Dict[str, Any]):
        """Process individual task completion for incremental deliverable updates"""
        try:
            task_id = event_data.get('task_id')
            completion_result = event_data.get('completion_result', {})
            
            if not task_id or not completion_result:
                return
            
            logger.info(f"🔄 Processing task completion for incremental deliverable: {task_id}")
            
            # Extract assets from single task result
            if completion_result.get('output'):
                # Create individual asset artifact
                artifact_id = await self._create_asset_artifact(
                    workspace_id=workspace_id,
                    task_id=task_id,
                    asset_name=f"Task Output - {task_id[:8]}",
                    asset_data=completion_result,
                    deliverable_type='task_output'
                )
                
                if artifact_id:
                    # Create incremental update event
                    await self._create_integration_event(
                        workspace_id=workspace_id,
                        event_type='asset_created',
                        source_component='deliverable_pipeline',
                        target_component='unified_orchestrator',
                        event_data={
                            'task_id': task_id,
                            'artifact_id': str(artifact_id)
                        }
                    )
            
        except Exception as e:
            logger.error(f"Failed to process task completion {task_id}: {e}")
    
    async def _process_quality_validation(self, workspace_id: str, event_data: Dict[str, Any]):
        """Process quality validation event for immediate asset enhancement"""
        try:
            task_id = event_data.get('task_id')
            quality_passed = event_data.get('passes_quality_gate', False)
            quality_score = event_data.get('score', 0)
            quality_reasoning = event_data.get('reasoning', '')
            
            if not task_id:
                logger.warning("Quality validation event missing task_id")
                return
            
            logger.info(f"🔍 Processing quality validation for task {task_id}: passed={quality_passed}, score={quality_score}")
            
            if quality_passed:
                # Get task data for enhanced asset creation
                task_data = await self._get_task_data(task_id)
                
                if task_data and task_data.get('result_payload'):
                    # Create enhanced asset with quality context
                    artifact_id = await self._create_quality_enhanced_asset(
                        workspace_id=workspace_id,
                        task_id=task_id,
                        task_data=task_data,
                        quality_context={
                            'quality_score': quality_score,
                            'quality_reasoning': quality_reasoning,
                            'validation_timestamp': datetime.now().isoformat()
                        }
                    )
                    
                    if artifact_id:
                        # Create quality enhancement event
                        await self._create_integration_event(
                            workspace_id=workspace_id,
                            event_type='quality_enhanced_asset_created',
                            source_component='deliverable_pipeline',
                            target_component='unified_orchestrator',
                            event_data={
                                'task_id': task_id,
                                'artifact_id': str(artifact_id),
                                'quality_score': quality_score
                            }
                        )
                        
                        logger.info(f"✅ Quality-enhanced asset created for task {task_id}")
                else:
                    logger.warning(f"No task data found for quality-validated task {task_id}")
            else:
                logger.info(f"⚠️ Task {task_id} failed quality validation (score: {quality_score})")
                
        except Exception as e:
            logger.error(f"Failed to process quality validation for task {task_id}: {e}")
    
    async def _get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data by ID"""
        try:
            result = self.supabase.table('tasks').select('*').eq('id', task_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Failed to get task data for {task_id}: {e}")
            return None
    
    async def _create_quality_enhanced_asset(self, workspace_id: str, task_id: str, 
                                           task_data: Dict[str, Any], 
                                           quality_context: Dict[str, Any]) -> Optional[UUID]:
        """Create quality-enhanced asset artifact"""
        try:
            # Extract enhanced content from task result
            result_payload = task_data.get('result_payload', {})
            task_output = result_payload.get('output', '')
            
            if not task_output:
                logger.warning(f"No output found in task {task_id} for asset creation")
                return None
            
            # Determine artifact type based on content and quality
            artifact_type = self._determine_artifact_type(result_payload)
            
            # Create enhanced asset name with quality context
            quality_score = quality_context.get('quality_score', 0)
            asset_name = f"Quality-Enhanced Asset ({quality_score}%) - Task {task_id[:8]}"
            
            # Create artifact record with quality enhancement
            artifact_data = {
                'id': str(uuid4()),
                'workspace_id': workspace_id,
                'task_id': task_id,
                'artifact_name': asset_name,
                'artifact_type': artifact_type,
                'content': task_output,
                'metadata': {
                    'deliverable_type': 'quality_enhanced',
                    'creation_method': 'quality_validation_trigger',
                    'source': 'deliverable_pipeline',
                    'quality_context': quality_context,
                    'original_task_type': task_data.get('task_type', 'unknown'),
                    'agent_id': task_data.get('agent_id')
                },
                'quality_score': quality_score / 100.0,  # Convert to 0-1 scale
                'created_at': datetime.now().isoformat()
            }
            
            # Insert into database
            result = self.supabase.table('asset_artifacts').insert(artifact_data).execute()
            
            if result.data:
                logger.debug(f"Created quality-enhanced asset: {asset_name}")
                return UUID(artifact_data['id'])
            
        except Exception as e:
            logger.error(f"Failed to create quality-enhanced asset: {e}")
            return None
    
    async def _create_asset_artifact(self, workspace_id: str, asset_name: str, 
                                   asset_data: Dict[str, Any], deliverable_type: str,
                                   task_id: str = None) -> Optional[UUID]:
        """Create asset artifact in database"""
        try:
            # Determine artifact type based on content
            artifact_type = self._determine_artifact_type(asset_data)
            
            # Extract content
            if isinstance(asset_data, dict):
                content = asset_data.get('output') or asset_data.get('content') or str(asset_data)
            else:
                content = str(asset_data)
            
            # Create artifact record
            artifact_data = {
                'id': str(uuid4()),
                'workspace_id': workspace_id,
                'task_id': task_id,
                'artifact_name': asset_name,
                'artifact_type': artifact_type,
                'content': content,
                'metadata': {
                    'deliverable_type': deliverable_type,
                    'creation_method': 'automatic',
                    'source': 'deliverable_pipeline'
                },
                'quality_score': self._calculate_quality_score(content),
                'created_at': datetime.now().isoformat()
            }
            
            # Insert into database
            result = self.supabase.table('asset_artifacts').insert(artifact_data).execute()
            
            if result.data:
                logger.debug(f"Created asset artifact: {asset_name}")
                return UUID(artifact_data['id'])
            
        except Exception as e:
            logger.error(f"Failed to create asset artifact: {e}")
            return None
    
    def _determine_deliverable_type(self, workspace_goals: List[Dict]) -> str:
        """Determine deliverable type based on workspace goals"""
        # Simple heuristic based on goal keywords
        if not workspace_goals:
            return 'general'
        
        goal_text = ' '.join([goal.get('description', '') for goal in workspace_goals]).lower()
        
        if any(keyword in goal_text for keyword in ['marketing', 'campaign', 'social', 'content']):
            return 'marketing_deliverable'
        elif any(keyword in goal_text for keyword in ['financial', 'budget', 'revenue', 'cost']):
            return 'financial_deliverable'
        elif any(keyword in goal_text for keyword in ['training', 'education', 'course', 'learning']):
            return 'training_deliverable'
        elif any(keyword in goal_text for keyword in ['research', 'analysis', 'study', 'data']):
            return 'research_deliverable'
        else:
            return 'business_deliverable'
    
    def _determine_artifact_type(self, asset_data: Dict[str, Any]) -> str:
        """Determine artifact type from content"""
        if isinstance(asset_data, dict):
            content = str(asset_data.get('output', '') or asset_data.get('content', ''))
        else:
            content = str(asset_data)
        
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['<html>', '<div>', '<table>', 'class="']):
            return 'html'
        elif any(keyword in content_lower for keyword in ['```json', '{"', '[{']):
            return 'json'
        elif any(keyword in content_lower for keyword in ['http://', 'https://', 'www.']):
            return 'url'
        elif len(content) > 1000:
            return 'document'
        else:
            return 'text'
    
    def _calculate_quality_score(self, content: str) -> float:
        """Calculate simple quality score based on content"""
        if not content:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length bonus
        if len(content) > 100:
            score += 0.2
        if len(content) > 500:
            score += 0.1
        
        # Structure bonus
        if any(marker in content for marker in ['\n', '<', '{', '|']):
            score += 0.1
        
        # URL/email bonus (actionable content)
        if any(marker in content.lower() for marker in ['http', '@', '.com', '.org']):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _get_pending_deliverable_events(self) -> List[Dict[str, Any]]:
        """Get pending deliverable events"""
        try:
            result = self.supabase.table('integration_events').select('*').or_(
                'target_component.eq.deliverable_pipeline,event_type.eq.ready_for_deliverable,event_type.eq.task_completed,event_type.eq.quality_validated'
            ).eq('status', 'pending').order('created_at').limit(50).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to fetch deliverable events: {e}")
            return []
    
    async def _create_integration_event(self, workspace_id: str, event_type: str,
                                      source_component: str, target_component: str = None,
                                      event_data: Dict[str, Any] = None):
        """Create integration event"""
        try:
            event = {
                'workspace_id': workspace_id,
                'event_type': event_type,
                'source_component': source_component,
                'target_component': target_component,
                'event_data': event_data or {},
                'status': 'pending'
            }
            
            self.supabase.table('integration_events').insert(event).execute()
            logger.debug(f"Created event: {event_type} from {source_component}")
            
        except Exception as e:
            logger.error(f"Failed to create integration event: {e}")
    
    async def _mark_event_processed(self, event_id: str):
        """Mark event as processed"""
        try:
            self.supabase.table('integration_events').update({
                'status': 'completed',
                'processed_at': datetime.now().isoformat(),
                'processed_by': 'deliverable_pipeline'
            }).eq('id', event_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to mark event processed: {e}")
    
    async def _mark_event_failed(self, event_id: str, error_message: str):
        """Mark event as failed"""
        try:
            self.supabase.table('integration_events').update({
                'status': 'failed',
                'processed_at': datetime.now().isoformat(),
                'processed_by': 'deliverable_pipeline',
                'error_message': error_message
            }).eq('id', event_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to mark event failed: {e}")
    
    async def _update_component_health(self, component_name: str, status: str, error: str = None):
        """Update component health"""
        try:
            health_data = {
                'status': status,
                'last_heartbeat': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if error:
                health_data['last_error'] = error
            
            self.supabase.table('component_health').update(
                health_data
            ).eq('component_name', component_name).execute()
            
        except Exception as e:
            logger.error(f"Failed to update component health: {e}")


# Global instance
deliverable_pipeline = DeliverablePipeline()