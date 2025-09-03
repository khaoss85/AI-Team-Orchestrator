"""
User Insights Management Service
Provides comprehensive CRUD operations for user-managed knowledge insights
with audit trail, versioning, and bulk operations support.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from models import (
    WorkspaceInsight, 
    InsightType,
    EnhancedBusinessInsight
)
from database import supabase
from services.enhanced_insight_database import enhanced_insight_db

logger = logging.getLogger(__name__)

class UserInsightFlag(str, Enum):
    """User-defined flags for insights"""
    VERIFIED = "verified"
    IMPORTANT = "important"
    OUTDATED = "outdated"
    NEEDS_REVIEW = "needs_review"
    ARCHIVED = "archived"

class BulkOperation(str, Enum):
    """Bulk operation types"""
    DELETE = "delete"
    CATEGORIZE = "categorize"
    FLAG = "flag"
    UNFLAG = "unflag"
    RESTORE = "restore"
    EXPORT = "export"

class InsightSource(str, Enum):
    """Source of insight creation"""
    AI_GENERATED = "ai_generated"
    USER_CREATED = "user_created"
    HYBRID = "hybrid"
    IMPORTED = "imported"

class UserManagedInsight:
    """Enhanced insight model with user management fields"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid4()))
        self.workspace_id = kwargs.get('workspace_id')
        self.title = kwargs.get('title', '')
        self.content = kwargs.get('content', '')
        self.insight_type = kwargs.get('insight_type', InsightType.DISCOVERY)
        self.category = kwargs.get('category', 'general')
        self.domain_type = kwargs.get('domain_type', 'general')
        
        # Agent role - required field for database
        self.agent_role = kwargs.get('agent_role', 'user_curator')
        
        # User management fields
        self.created_by = kwargs.get('created_by', 'system')
        self.last_modified_by = kwargs.get('last_modified_by')
        self.is_user_created = kwargs.get('is_user_created', False)
        self.is_user_modified = kwargs.get('is_user_modified', False)
        self.is_deleted = kwargs.get('is_deleted', False)
        self.deleted_at = kwargs.get('deleted_at')
        self.deleted_by = kwargs.get('deleted_by')
        
        # Versioning
        self.version_number = kwargs.get('version_number', 1)
        self.parent_insight_id = kwargs.get('parent_insight_id')
        self.original_content = kwargs.get('original_content')
        
        # User flags
        self.user_flags = kwargs.get('user_flags', {})
        
        # Metrics and metadata
        self.quantifiable_metrics = kwargs.get('quantifiable_metrics', {})
        self.action_recommendations = kwargs.get('action_recommendations', [])
        self.business_value_score = kwargs.get('business_value_score', 0.5)
        self.confidence_score = kwargs.get('confidence_score', 0.5)
        self.metadata = kwargs.get('metadata', {})
        
        # Timestamps
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        base_dict = {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'title': self.title,
            'content': self.content,
            'insight_type': self.insight_type.value if isinstance(self.insight_type, Enum) else self.insight_type,
            'insight_category': self.category,
            'domain_type': self.domain_type,
            'agent_role': self.agent_role,  # Add required agent_role field
            'created_by': self.created_by,
            'last_modified_by': self.last_modified_by,
            'is_user_created': self.is_user_created,
            'is_user_modified': self.is_user_modified,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': self.deleted_by,
            'version_number': self.version_number,
            'parent_insight_id': str(self.parent_insight_id) if self.parent_insight_id else None,
            'original_content': self.original_content,
            'user_flags': self.user_flags,
            'quantifiable_metrics': self.quantifiable_metrics,
            # NOTE: action_recommendations stored in metadata until column is added
            # 'action_recommendations': self.action_recommendations,
            'business_value_score': self.business_value_score,
            'confidence_score': self.confidence_score,
            'metadata': {
                **self.metadata,
                # Store action_recommendations in metadata until column is added
                'action_recommendations': self.action_recommendations
            },
            'relevance_tags': self.metadata.get('tags', []),
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserManagedInsight':
        """Create instance from dictionary"""
        # Extract action_recommendations from metadata if not in top-level
        metadata = data.get('metadata', {})
        if 'action_recommendations' not in data and 'action_recommendations' in metadata:
            data['action_recommendations'] = metadata.get('action_recommendations', [])
        return cls(**data)

class UserInsightManager:
    """Manages user-created and user-modified insights with full CRUD operations"""
    
    def __init__(self):
        self.table = "workspace_insights"
        self.audit_table = "insight_audit_trail"
        
    async def create_user_insight(
        self, 
        workspace_id: str,
        title: str,
        content: str,
        category: str,
        created_by: str,
        domain_type: str = "general",
        metrics: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserManagedInsight:
        """Create a new user-generated insight
        
        Args:
            workspace_id: Workspace to add insight to
            title: User-friendly title
            content: Insight content/description
            category: Category type (insight, best_practice, learning, etc)
            created_by: User ID creating the insight
            domain_type: Business domain (optional)
            metrics: Quantifiable metrics (optional)
            recommendations: Action recommendations (optional)
            tags: Relevance tags for search (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            UserManagedInsight: Created insight object
        """
        try:
            insight = UserManagedInsight(
                workspace_id=workspace_id,
                title=title,
                content=content,
                category=category,
                insight_type=self._category_to_insight_type(category),
                domain_type=domain_type,
                agent_role='user_curator',  # Set appropriate agent_role for user-created insights
                created_by=created_by,
                is_user_created=True,
                quantifiable_metrics=metrics or {},
                action_recommendations=recommendations or [],
                metadata={
                    **(metadata or {}),
                    'tags': tags or [],
                    'source': InsightSource.USER_CREATED.value
                },
                user_flags={'created_manually': True}
            )
            
            # Store in database
            result = supabase.table(self.table).insert(insight.to_dict()).execute()
            
            if result.data:
                created_insight = UserManagedInsight.from_dict(result.data[0])
                logger.info(f"✅ Created user insight {created_insight.id} by {created_by}")
                
                # Log to audit trail
                await self._log_audit_trail(
                    insight_id=created_insight.id,
                    action="CREATE",
                    performed_by=created_by,
                    new_values=insight.to_dict(),
                    workspace_id=workspace_id
                )
                
                return created_insight
            else:
                raise Exception("Failed to create insight")
                
        except Exception as e:
            logger.error(f"❌ Failed to create user insight: {e}")
            raise
    
    async def update_insight(
        self,
        insight_id: str,
        updates: Dict[str, Any],
        modified_by: str
    ) -> UserManagedInsight:
        """Update an existing insight
        
        Args:
            insight_id: ID of insight to update
            updates: Dictionary of fields to update
            modified_by: User ID performing the update
            
        Returns:
            UserManagedInsight: Updated insight object
        """
        try:
            # Get current insight
            result = supabase.table(self.table).select('*').eq('id', insight_id).execute()
            
            if not result.data:
                raise ValueError(f"Insight {insight_id} not found")
            
            current_data = result.data[0]
            old_values = current_data.copy()
            
            # Map API field names to database column names
            field_mapping = {
                'category': 'insight_category',
                'metrics': 'quantifiable_metrics',
                'recommendations': 'action_recommendations'
            }
            
            # Apply field mapping to updates
            mapped_updates = {}
            for key, value in updates.items():
                db_field = field_mapping.get(key, key)
                mapped_updates[db_field] = value
            
            # Prepare update data
            update_data = {
                **mapped_updates,
                'last_modified_by': modified_by,
                'is_user_modified': True,
                'updated_at': datetime.now().isoformat(),
                'version_number': current_data.get('version_number', 1) + 1
            }
            
            # Store original content if first modification
            if not current_data.get('is_user_modified'):
                update_data['original_content'] = current_data.get('content')
                update_data['original_metadata'] = current_data.get('metadata')
            
            # Update in database
            update_result = supabase.table(self.table).update(update_data).eq('id', insight_id).execute()
            
            if update_result.data:
                updated_insight = UserManagedInsight.from_dict(update_result.data[0])
                logger.info(f"✅ Updated insight {insight_id} by {modified_by}")
                
                # Log to audit trail
                await self._log_audit_trail(
                    insight_id=insight_id,
                    action="UPDATE",
                    performed_by=modified_by,
                    old_values=old_values,
                    new_values=update_result.data[0],
                    workspace_id=current_data['workspace_id']
                )
                
                return updated_insight
            else:
                raise Exception("Failed to update insight")
                
        except Exception as e:
            logger.error(f"❌ Failed to update insight {insight_id}: {e}")
            raise
    
    async def delete_insight(
        self,
        insight_id: str,
        deleted_by: str,
        hard_delete: bool = False
    ) -> bool:
        """Delete an insight (soft delete by default)
        
        Args:
            insight_id: ID of insight to delete
            deleted_by: User ID performing the deletion
            hard_delete: If True, permanently delete from database
            
        Returns:
            bool: True if successfully deleted
        """
        try:
            if hard_delete:
                # Permanent deletion
                result = supabase.table(self.table).delete().eq('id', insight_id).execute()
                action = "HARD_DELETE"
            else:
                # Soft delete
                result = supabase.table(self.table).update({
                    'is_deleted': True,
                    'deleted_at': datetime.now().isoformat(),
                    'deleted_by': deleted_by,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', insight_id).execute()
                action = "DELETE"
            
            if result.data:
                logger.info(f"✅ {'Hard' if hard_delete else 'Soft'} deleted insight {insight_id} by {deleted_by}")
                
                # Log to audit trail
                await self._log_audit_trail(
                    insight_id=insight_id,
                    action=action,
                    performed_by=deleted_by,
                    workspace_id=result.data[0].get('workspace_id') if result.data else None
                )
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete insight {insight_id}: {e}")
            return False
    
    async def restore_insight(
        self,
        insight_id: str,
        restored_by: str
    ) -> UserManagedInsight:
        """Restore a soft-deleted insight
        
        Args:
            insight_id: ID of insight to restore
            restored_by: User ID performing the restoration
            
        Returns:
            UserManagedInsight: Restored insight object
        """
        try:
            result = supabase.table(self.table).update({
                'is_deleted': False,
                'deleted_at': None,
                'deleted_by': None,
                'last_modified_by': restored_by,
                'updated_at': datetime.now().isoformat()
            }).eq('id', insight_id).eq('is_deleted', True).execute()
            
            if result.data:
                restored_insight = UserManagedInsight.from_dict(result.data[0])
                logger.info(f"✅ Restored insight {insight_id} by {restored_by}")
                
                # Log to audit trail
                await self._log_audit_trail(
                    insight_id=insight_id,
                    action="RESTORE",
                    performed_by=restored_by,
                    workspace_id=result.data[0].get('workspace_id')
                )
                
                return restored_insight
            else:
                raise ValueError(f"Insight {insight_id} not found or not deleted")
                
        except Exception as e:
            logger.error(f"❌ Failed to restore insight {insight_id}: {e}")
            raise
    
    async def recategorize_insight(
        self,
        insight_id: str,
        new_category: str,
        modified_by: str
    ) -> UserManagedInsight:
        """Change the category of an insight
        
        Args:
            insight_id: ID of insight to recategorize
            new_category: New category value
            modified_by: User ID performing the change
            
        Returns:
            UserManagedInsight: Updated insight object
        """
        try:
            updates = {
                'insight_category': new_category,
                'insight_type': self._category_to_insight_type(new_category).value
            }
            
            updated_insight = await self.update_insight(insight_id, updates, modified_by)
            
            # Log specific categorization action
            await self._log_audit_trail(
                insight_id=insight_id,
                action="CATEGORIZE",
                performed_by=modified_by,
                new_values={'category': new_category},
                workspace_id=updated_insight.workspace_id
            )
            
            return updated_insight
            
        except Exception as e:
            logger.error(f"❌ Failed to recategorize insight {insight_id}: {e}")
            raise
    
    async def flag_insight(
        self,
        insight_id: str,
        flag_type: str,
        flag_value: bool,
        flagged_by: str
    ) -> UserManagedInsight:
        """Add or remove a flag on an insight
        
        Args:
            insight_id: ID of insight to flag
            flag_type: Type of flag (verified, important, outdated, etc)
            flag_value: True to set flag, False to remove
            flagged_by: User ID performing the flagging
            
        Returns:
            UserManagedInsight: Updated insight object
        """
        try:
            # Get current insight
            result = supabase.table(self.table).select('*').eq('id', insight_id).execute()
            
            if not result.data:
                raise ValueError(f"Insight {insight_id} not found")
            
            current_data = result.data[0]
            user_flags = current_data.get('user_flags', {})
            
            # Update flags
            user_flags[flag_type] = flag_value
            user_flags['last_flagged_by'] = flagged_by
            user_flags['last_flagged_at'] = datetime.now().isoformat()
            
            # Track flag history
            flag_history = user_flags.get('flag_history', [])
            flag_history.append({
                'flag': flag_type,
                'value': flag_value,
                'by': flagged_by,
                'at': datetime.now().isoformat()
            })
            user_flags['flag_history'] = flag_history[-10:]  # Keep last 10 changes
            
            # Update in database
            update_result = supabase.table(self.table).update({
                'user_flags': user_flags,
                'last_modified_by': flagged_by,
                'updated_at': datetime.now().isoformat()
            }).eq('id', insight_id).execute()
            
            if update_result.data:
                updated_insight = UserManagedInsight.from_dict(update_result.data[0])
                logger.info(f"✅ {'Set' if flag_value else 'Removed'} flag '{flag_type}' on insight {insight_id}")
                
                # Log to audit trail
                await self._log_audit_trail(
                    insight_id=insight_id,
                    action="FLAG" if flag_value else "UNFLAG",
                    performed_by=flagged_by,
                    new_values={'flag': flag_type, 'value': flag_value},
                    workspace_id=current_data['workspace_id']
                )
                
                return updated_insight
            else:
                raise Exception("Failed to flag insight")
                
        except Exception as e:
            logger.error(f"❌ Failed to flag insight {insight_id}: {e}")
            raise
    
    async def bulk_operation(
        self,
        insight_ids: List[str],
        operation: BulkOperation,
        performed_by: str,
        operation_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform bulk operation on multiple insights
        
        Args:
            insight_ids: List of insight IDs to operate on
            operation: Type of bulk operation
            performed_by: User ID performing the operation
            operation_data: Additional data for the operation
            
        Returns:
            Dict containing operation results and statistics
        """
        try:
            results = {
                'operation': operation.value,
                'total': len(insight_ids),
                'succeeded': 0,
                'failed': 0,
                'errors': []
            }
            
            for insight_id in insight_ids:
                try:
                    if operation == BulkOperation.DELETE:
                        success = await self.delete_insight(insight_id, performed_by)
                        if success:
                            results['succeeded'] += 1
                        else:
                            results['failed'] += 1
                            
                    elif operation == BulkOperation.RESTORE:
                        await self.restore_insight(insight_id, performed_by)
                        results['succeeded'] += 1
                        
                    elif operation == BulkOperation.CATEGORIZE:
                        new_category = operation_data.get('category', 'general')
                        await self.recategorize_insight(insight_id, new_category, performed_by)
                        results['succeeded'] += 1
                        
                    elif operation == BulkOperation.FLAG:
                        flag_type = operation_data.get('flag_type', UserInsightFlag.VERIFIED.value)
                        flag_value = operation_data.get('flag_value', True)
                        await self.flag_insight(insight_id, flag_type, flag_value, performed_by)
                        results['succeeded'] += 1
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'insight_id': insight_id,
                        'error': str(e)
                    })
            
            logger.info(f"✅ Bulk operation {operation.value} completed: {results['succeeded']}/{results['total']} succeeded")
            
            # Log bulk operation to tracking table
            await self._log_bulk_operation(
                operation_type=operation.value,
                affected_insights=insight_ids,
                performed_by=performed_by,
                result=results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed bulk operation: {e}")
            raise
    
    async def list_insights(
        self,
        workspace_id: str,
        include_ai: bool = True,
        include_user: bool = True,
        include_deleted: bool = False,
        category: Optional[str] = None,
        flags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[UserManagedInsight], int]:
        """List insights with filtering options
        
        Args:
            workspace_id: Workspace to list insights from
            include_ai: Include AI-generated insights
            include_user: Include user-created insights
            include_deleted: Include soft-deleted insights
            category: Filter by specific category
            flags: Filter by specific flags
            search_query: Search in title and content
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of insights, total count)
        """
        try:
            # Build query
            query = supabase.table(self.table).select('*', count='exact').eq('workspace_id', workspace_id)
            
            # Apply source filters
            source_conditions = []
            if include_user:
                source_conditions.append('is_user_created.eq.true')
            if include_ai:
                source_conditions.append('is_user_created.eq.false')
            
            # Apply deleted filter
            if not include_deleted:
                query = query.eq('is_deleted', False)
            
            # Apply category filter
            if category:
                query = query.eq('insight_category', category)
            
            # Apply search filter
            if search_query:
                query = query.or_(f'title.ilike.%{search_query}%,content.ilike.%{search_query}%')
            
            # Apply pagination
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            insights = []
            for data in result.data:
                insight = UserManagedInsight.from_dict(data)
                
                # Apply flag filters if specified
                if flags:
                    has_required_flags = all(
                        insight.user_flags.get(flag) == True for flag in flags
                    )
                    if not has_required_flags:
                        continue
                
                insights.append(insight)
            
            total_count = result.count if hasattr(result, 'count') else len(insights)
            
            logger.info(f"✅ Listed {len(insights)} insights for workspace {workspace_id}")
            return insights, total_count
            
        except Exception as e:
            logger.error(f"❌ Failed to list insights: {e}")
            return [], 0
    
    async def get_insight_history(
        self,
        insight_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get audit trail history for an insight
        
        Args:
            insight_id: ID of insight to get history for
            limit: Maximum history entries to return
            
        Returns:
            List of audit trail entries
        """
        try:
            result = supabase.table(self.audit_table)\
                .select('*')\
                .eq('insight_id', insight_id)\
                .order('performed_at', desc=True)\
                .limit(limit)\
                .execute()
            
            history = result.data if result.data else []
            logger.info(f"✅ Retrieved {len(history)} history entries for insight {insight_id}")
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get insight history: {e}")
            return []
    
    async def undo_last_change(
        self,
        insight_id: str,
        user_id: str
    ) -> UserManagedInsight:
        """Undo the last modification to an insight
        
        Args:
            insight_id: ID of insight to undo changes for
            user_id: User performing the undo
            
        Returns:
            UserManagedInsight: Insight restored to previous state
        """
        try:
            # Get last audit entry with old values
            history = await self.get_insight_history(insight_id, limit=2)
            
            if len(history) < 2:
                raise ValueError("No previous state to restore")
            
            # Get the old values from the previous state
            previous_state = history[1].get('old_values', {})
            
            if not previous_state:
                raise ValueError("No previous state data available")
            
            # Restore previous state
            restore_data = {
                key: value for key, value in previous_state.items()
                if key not in ['id', 'workspace_id', 'created_at']
            }
            restore_data['last_modified_by'] = user_id
            restore_data['updated_at'] = datetime.now().isoformat()
            
            result = supabase.table(self.table).update(restore_data).eq('id', insight_id).execute()
            
            if result.data:
                restored_insight = UserManagedInsight.from_dict(result.data[0])
                logger.info(f"✅ Undone last change to insight {insight_id}")
                
                # Log undo action
                await self._log_audit_trail(
                    insight_id=insight_id,
                    action="UNDO",
                    performed_by=user_id,
                    workspace_id=restored_insight.workspace_id
                )
                
                return restored_insight
            else:
                raise Exception("Failed to undo changes")
                
        except Exception as e:
            logger.error(f"❌ Failed to undo changes for insight {insight_id}: {e}")
            raise
    
    # Helper methods
    
    def _category_to_insight_type(self, category: str) -> InsightType:
        """Map category to InsightType enum"""
        mapping = {
            'insight': InsightType.DISCOVERY,
            'best_practice': InsightType.SUCCESS_PATTERN,
            'learning': InsightType.DISCOVERY,
            'optimization': InsightType.OPTIMIZATION,
            'warning': InsightType.FAILURE_LESSON,
            'constraint': InsightType.CONSTRAINT
        }
        return mapping.get(category, InsightType.DISCOVERY)
    
    async def _log_audit_trail(
        self,
        insight_id: str,
        action: str,
        performed_by: str,
        workspace_id: str = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None
    ):
        """Log action to audit trail"""
        try:
            audit_entry = {
                'insight_id': str(insight_id),
                'action': action,
                'performed_by': performed_by,
                'performed_at': datetime.now().isoformat(),
                'workspace_id': str(workspace_id) if workspace_id else None,
                'old_values': old_values,
                'new_values': new_values
            }
            
            # Try to insert into audit table - if it doesn't exist, just log a warning
            try:
                supabase.table(self.audit_table).insert(audit_entry).execute()
            except Exception as audit_error:
                # Check if error is due to missing table
                if 'relation' in str(audit_error) and 'does not exist' in str(audit_error):
                    logger.warning(f"Audit table '{self.audit_table}' does not exist yet. Skipping audit log. Run migration 017 to enable audit trail.")
                else:
                    raise audit_error
            
        except Exception as e:
            logger.warning(f"Failed to log audit trail: {e}")
    
    async def _log_bulk_operation(
        self,
        operation_type: str,
        affected_insights: List[str],
        performed_by: str,
        result: Dict[str, Any]
    ):
        """Log bulk operation to tracking table"""
        try:
            operation_entry = {
                'operation_type': operation_type,
                'affected_insights': affected_insights,
                'performed_by': performed_by,
                'performed_at': datetime.now().isoformat(),
                'operation_status': 'completed',
                'operation_result': result
            }
            
            # Try to insert into bulk operations table - if it doesn't exist, just log a warning
            try:
                supabase.table('insight_bulk_operations').insert(operation_entry).execute()
            except Exception as bulk_error:
                # Check if error is due to missing table
                if 'relation' in str(bulk_error) and 'does not exist' in str(bulk_error):
                    logger.warning(f"Bulk operations table 'insight_bulk_operations' does not exist yet. Skipping bulk operation log. Run migration 017 to enable bulk tracking.")
                else:
                    raise bulk_error
            
        except Exception as e:
            logger.warning(f"Failed to log bulk operation: {e}")

# Global instance
user_insight_manager = UserInsightManager()

# Convenience functions
async def create_insight(
    workspace_id: str,
    title: str,
    content: str,
    category: str,
    created_by: str,
    **kwargs
) -> UserManagedInsight:
    """Create a new user insight"""
    return await user_insight_manager.create_user_insight(
        workspace_id, title, content, category, created_by, **kwargs
    )

async def update_insight(insight_id: str, updates: Dict, modified_by: str) -> UserManagedInsight:
    """Update an existing insight"""
    return await user_insight_manager.update_insight(insight_id, updates, modified_by)

async def delete_insight(insight_id: str, deleted_by: str, hard_delete: bool = False) -> bool:
    """Delete an insight"""
    return await user_insight_manager.delete_insight(insight_id, deleted_by, hard_delete)

async def flag_insight(insight_id: str, flag: str, value: bool, by: str) -> UserManagedInsight:
    """Flag or unflag an insight"""
    return await user_insight_manager.flag_insight(insight_id, flag, value, by)

async def list_workspace_insights(workspace_id: str, **filters) -> Tuple[List[UserManagedInsight], int]:
    """List insights for a workspace with filters"""
    return await user_insight_manager.list_insights(workspace_id, **filters)