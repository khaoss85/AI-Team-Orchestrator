"""
Enhanced Insight Database Integration
Database layer for Content-Aware Learning System domain-specific insights

This module provides database operations for storing and retrieving EnhancedBusinessInsight
objects with domain-specific metadata, quantifiable metrics, and actionable recommendations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from models import EnhancedBusinessInsight, WorkspaceInsight, InsightType
from database import supabase

logger = logging.getLogger(__name__)

class EnhancedInsightDatabase:
    """Database operations for domain-specific business insights"""
    
    def __init__(self):
        self.table = "workspace_insights"
        
    async def store_enhanced_insight(self, insight: EnhancedBusinessInsight) -> str:
        """Store an enhanced business insight in the database
        
        Args:
            insight: EnhancedBusinessInsight object to store
            
        Returns:
            str: ID of the stored insight
            
        Raises:
            Exception: If storage fails
        """
        try:
            # Convert to WorkspaceInsight for database compatibility
            workspace_insight = insight.to_workspace_insight()
            
            # Prepare data for database insertion
            insert_data = {
                'id': str(workspace_insight.id),
                'workspace_id': str(workspace_insight.workspace_id),
                'task_id': str(workspace_insight.task_id) if workspace_insight.task_id else None,
                'agent_role': workspace_insight.agent_role,
                'insight_type': workspace_insight.insight_type.value,
                'content': workspace_insight.content,
                'relevance_tags': workspace_insight.relevance_tags,
                'confidence_score': workspace_insight.confidence_score,
                'expires_at': workspace_insight.expires_at.isoformat() if workspace_insight.expires_at else None,
                'created_at': workspace_insight.created_at.isoformat(),
                'updated_at': datetime.now().isoformat(),
                'metadata': workspace_insight.metadata
            }
            
            # Store in database
            result = supabase.table(self.table).insert(insert_data).execute()
            
            if result.data:
                stored_id = result.data[0]['id']
                logger.info(f"✅ Stored enhanced insight {stored_id} for domain: {insight.domain_type}")
                return stored_id
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"❌ Failed to store enhanced insight: {e}")
            raise
            
    async def retrieve_domain_insights(
        self, 
        workspace_id: str, 
        domain_type: Optional[str] = None,
        min_business_value: float = 0.0,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[EnhancedBusinessInsight]:
        """Retrieve domain-specific insights from the database
        
        Args:
            workspace_id: Workspace to retrieve insights for
            domain_type: Specific domain to filter by (e.g., 'instagram_marketing')
            min_business_value: Minimum business value score filter
            min_confidence: Minimum confidence score filter
            limit: Maximum number of insights to return
            
        Returns:
            List[EnhancedBusinessInsight]: List of enhanced business insights
        """
        try:
            # Build query
            query = supabase.table(self.table).select('*').eq('workspace_id', workspace_id)
            
            # Apply confidence filter
            if min_confidence > 0.0:
                query = query.gte('confidence_score', min_confidence)
            
            # Order by creation date (newest first) and apply limit
            query = query.order('created_at', desc=True).limit(limit)
            
            result = query.execute()
            insights_data = result.data or []
            
            # Convert to EnhancedBusinessInsight objects
            enhanced_insights = []
            for data in insights_data:
                try:
                    # Create WorkspaceInsight from database data
                    workspace_insight = self._create_workspace_insight_from_data(data)
                    
                    # Convert to EnhancedBusinessInsight
                    enhanced_insight = EnhancedBusinessInsight.from_workspace_insight(workspace_insight)
                    
                    # Apply domain and business value filters
                    if domain_type and enhanced_insight.domain_type != domain_type:
                        continue
                        
                    if enhanced_insight.business_value_score < min_business_value:
                        continue
                        
                    enhanced_insights.append(enhanced_insight)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse insight {data.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Retrieved {len(enhanced_insights)} domain insights for workspace {workspace_id}")
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve domain insights: {e}")
            return []
            
    async def retrieve_high_value_insights(
        self, 
        workspace_id: str,
        top_n: int = 10
    ) -> List[EnhancedBusinessInsight]:
        """Retrieve highest value insights for a workspace
        
        Args:
            workspace_id: Workspace to retrieve insights for
            top_n: Number of top insights to return
            
        Returns:
            List[EnhancedBusinessInsight]: Top insights by composite value score
        """
        try:
            insights = await self.retrieve_domain_insights(
                workspace_id=workspace_id,
                min_business_value=0.5,
                min_confidence=0.5,
                limit=100  # Get more to sort and filter
            )
            
            # Calculate composite score (business_value * confidence) and sort
            insights_with_scores = [
                (insight, insight.business_value_score * insight.confidence_score)
                for insight in insights
            ]
            
            # Sort by composite score (descending) and take top N
            insights_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_insights = [insight for insight, _ in insights_with_scores[:top_n]]
            
            logger.info(f"✅ Retrieved top {len(top_insights)} high-value insights for workspace {workspace_id}")
            return top_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve high-value insights: {e}")
            return []
            
    async def get_domain_summary(self, workspace_id: str) -> Dict[str, Any]:
        """Get summary statistics for domain insights in a workspace
        
        Args:
            workspace_id: Workspace to analyze
            
        Returns:
            Dict containing domain insight statistics
        """
        try:
            insights = await self.retrieve_domain_insights(workspace_id=workspace_id, limit=1000)
            
            if not insights:
                return {"total_insights": 0, "domains": {}}
            
            # Analyze by domain
            domain_stats = {}
            total_business_value = 0
            total_confidence = 0
            
            for insight in insights:
                domain = insight.domain_type
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        "count": 0,
                        "avg_business_value": 0,
                        "avg_confidence": 0,
                        "total_applications": 0,
                        "validated_count": 0
                    }
                
                stats = domain_stats[domain]
                stats["count"] += 1
                stats["avg_business_value"] += insight.business_value_score
                stats["avg_confidence"] += insight.confidence_score
                stats["total_applications"] += insight.application_count
                if insight.validation_status == "validated":
                    stats["validated_count"] += 1
                
                total_business_value += insight.business_value_score
                total_confidence += insight.confidence_score
            
            # Calculate averages
            for domain, stats in domain_stats.items():
                count = stats["count"]
                stats["avg_business_value"] = round(stats["avg_business_value"] / count, 3)
                stats["avg_confidence"] = round(stats["avg_confidence"] / count, 3)
            
            summary = {
                "total_insights": len(insights),
                "avg_business_value": round(total_business_value / len(insights), 3),
                "avg_confidence": round(total_confidence / len(insights), 3),
                "domains": domain_stats,
                "top_domains": sorted(
                    domain_stats.items(), 
                    key=lambda x: x[1]["avg_business_value"], 
                    reverse=True
                )[:5]
            }
            
            logger.info(f"✅ Generated domain summary for workspace {workspace_id}: {len(insights)} insights across {len(domain_stats)} domains")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate domain summary: {e}")
            return {"error": str(e)}
            
    async def mark_insight_applied(self, insight_id: str) -> bool:
        """Mark an insight as applied and update application tracking
        
        Args:
            insight_id: ID of the insight to mark as applied
            
        Returns:
            bool: True if successfully marked as applied
        """
        try:
            # Get current insight data
            result = supabase.table(self.table).select('*').eq('id', insight_id).execute()
            
            if not result.data:
                logger.warning(f"⚠️ Insight {insight_id} not found for application marking")
                return False
                
            current_data = result.data[0]
            metadata = current_data.get('metadata', {})
            
            # Update application tracking
            current_count = metadata.get('application_count', 0)
            metadata.update({
                'application_count': current_count + 1,
                'last_applied_at': datetime.now().isoformat(),
                'validation_status': 'applied'
            })
            
            # Update in database
            update_result = supabase.table(self.table).update({
                'metadata': metadata,
                'updated_at': datetime.now().isoformat()
            }).eq('id', insight_id).execute()
            
            if update_result.data:
                logger.info(f"✅ Marked insight {insight_id} as applied (count: {current_count + 1})")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to mark insight {insight_id} as applied: {e}")
            return False
            
    async def search_insights_by_content(
        self, 
        workspace_id: str, 
        search_query: str,
        domain_type: Optional[str] = None,
        limit: int = 20
    ) -> List[EnhancedBusinessInsight]:
        """Search insights by content keywords
        
        Args:
            workspace_id: Workspace to search in
            search_query: Keywords to search for
            domain_type: Optional domain filter
            limit: Maximum results to return
            
        Returns:
            List[EnhancedBusinessInsight]: Matching insights
        """
        try:
            # Build query with text search
            query = supabase.table(self.table).select('*').eq('workspace_id', workspace_id)
            
            # Use ilike for case-insensitive search
            query = query.ilike('content', f'%{search_query}%')
            
            # Apply limit
            query = query.limit(limit)
            
            result = query.execute()
            insights_data = result.data or []
            
            # Convert to EnhancedBusinessInsight objects and apply domain filter
            enhanced_insights = []
            for data in insights_data:
                try:
                    workspace_insight = self._create_workspace_insight_from_data(data)
                    enhanced_insight = EnhancedBusinessInsight.from_workspace_insight(workspace_insight)
                    
                    # Apply domain filter if specified
                    if domain_type and enhanced_insight.domain_type != domain_type:
                        continue
                        
                    enhanced_insights.append(enhanced_insight)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse search result {data.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Found {len(enhanced_insights)} insights matching '{search_query}'")
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to search insights: {e}")
            return []
    
    def _create_workspace_insight_from_data(self, data: Dict[str, Any]) -> WorkspaceInsight:
        """Convert database row to WorkspaceInsight object"""
        return WorkspaceInsight(
            id=UUID(data['id']),
            workspace_id=UUID(data['workspace_id']),
            task_id=UUID(data['task_id']) if data.get('task_id') else None,
            agent_role=data.get('agent_role', 'system'),
            insight_type=InsightType(data.get('insight_type', 'success_pattern')),
            content=data.get('content', ''),
            relevance_tags=data.get('relevance_tags', []),
            confidence_score=float(data.get('confidence_score', 0.0)),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            metadata=data.get('metadata', {})
        )

# Global instance
enhanced_insight_db = EnhancedInsightDatabase()

# Convenience functions
async def store_domain_insight(insight: EnhancedBusinessInsight) -> str:
    """Store a domain-specific insight"""
    return await enhanced_insight_db.store_enhanced_insight(insight)

async def get_domain_insights(
    workspace_id: str, 
    domain_type: Optional[str] = None,
    min_business_value: float = 0.0,
    limit: int = 50
) -> List[EnhancedBusinessInsight]:
    """Retrieve domain-specific insights"""
    return await enhanced_insight_db.retrieve_domain_insights(
        workspace_id=workspace_id,
        domain_type=domain_type,
        min_business_value=min_business_value,
        limit=limit
    )

async def get_high_value_insights(workspace_id: str, top_n: int = 10) -> List[EnhancedBusinessInsight]:
    """Get top high-value insights for task execution"""
    return await enhanced_insight_db.retrieve_high_value_insights(workspace_id, top_n)

async def mark_insight_used(insight_id: str) -> bool:
    """Mark an insight as applied to a task"""
    return await enhanced_insight_db.mark_insight_applied(insight_id)

async def search_domain_insights(
    workspace_id: str, 
    query: str, 
    domain: Optional[str] = None
) -> List[EnhancedBusinessInsight]:
    """Search insights by content"""
    return await enhanced_insight_db.search_insights_by_content(workspace_id, query, domain)

async def get_workspace_insight_summary(workspace_id: str) -> Dict[str, Any]:
    """Get summary of all domain insights for a workspace"""
    return await enhanced_insight_db.get_domain_summary(workspace_id)