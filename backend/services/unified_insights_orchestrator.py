"""
Unified Insights Orchestrator Service
Orchestrates between AI extraction, user management, and workspace memory systems
Provides single source of truth for all insights with intelligent caching and sync
"""

import logging
import asyncio
import hashlib
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from uuid import UUID
from dataclasses import dataclass, field

from unified_insight import (
    UnifiedInsight, 
    InsightOrigin,
    InsightConfidenceLevel,
    InsightCategory,
    UnifiedInsightResponse,
    InsightSyncStatus
)
from services.universal_learning_engine import UniversalLearningEngine
from services.user_insight_manager import user_insight_manager
from database import get_supabase_client, get_workspace
from utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class InsightCache:
    """In-memory cache for insights with TTL"""
    insights: List[UnifiedInsight] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        age = (datetime.utcnow() - self.last_updated).total_seconds()
        return age < self.ttl_seconds
    
    def invalidate(self):
        """Force cache invalidation"""
        self.last_updated = datetime.min


class UnifiedInsightsOrchestrator:
    """
    Orchestrates insights from multiple sources into unified interface.
    
    ARCHITECTURE:
    - Single entry point for all insight operations
    - Intelligent caching with TTL
    - Background synchronization between systems
    - Conflict resolution for user edits
    - Progressive enhancement from AI to user-managed
    """
    
    def __init__(self):
        self.learning_engine = UniversalLearningEngine()
        self.cache_manager = CacheManager()
        self.workspace_caches: Dict[str, InsightCache] = {}
        self.sync_locks: Dict[str, asyncio.Lock] = {}
        
        # Configuration
        self.ai_cache_ttl = 300  # 5 minutes for AI insights
        self.user_cache_ttl = 60  # 1 minute for user insights
        self.sync_batch_size = 50
        self.high_value_threshold = 0.7
        
    async def get_unified_insights(
        self,
        workspace_id: str,
        category: Optional[str] = None,
        confidence_level: Optional[str] = None,
        origin: Optional[str] = None,
        include_deleted: bool = False,
        force_refresh: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> UnifiedInsightResponse:
        """
        Get unified insights from all sources with intelligent aggregation.
        
        Flow:
        1. Check cache validity
        2. Fetch from all sources in parallel
        3. Merge and deduplicate
        4. Apply filters
        5. Return paginated results
        """
        try:
            logger.info(f"Getting unified insights for workspace {workspace_id}")
            
            # Get or create workspace lock
            if workspace_id not in self.sync_locks:
                self.sync_locks[workspace_id] = asyncio.Lock()
            
            # Check cache unless forced refresh
            if not force_refresh and workspace_id in self.workspace_caches:
                cache = self.workspace_caches[workspace_id]
                if cache.is_valid():
                    logger.info(f"Cache hit for workspace {workspace_id}")
                    filtered = self._apply_filters(
                        cache.insights, category, confidence_level, 
                        origin, include_deleted
                    )
                    return self._paginate_response(filtered, limit, offset, "hit")
            
            # Fetch from all sources in parallel
            insights = await self._fetch_all_sources(workspace_id)
            
            # Cache the results
            self.workspace_caches[workspace_id] = InsightCache(
                insights=insights,
                ttl_seconds=self.ai_cache_ttl
            )
            
            # Apply filters
            filtered = self._apply_filters(
                insights, category, confidence_level, 
                origin, include_deleted
            )
            
            # Return paginated response
            return self._paginate_response(filtered, limit, offset, "miss")
            
        except Exception as e:
            logger.error(f"Error getting unified insights: {e}")
            raise
    
    async def _fetch_all_sources(self, workspace_id: str) -> List[UnifiedInsight]:
        """Fetch insights from all three sources in parallel"""
        tasks = [
            self._fetch_ai_insights(workspace_id),
            self._fetch_user_insights(workspace_id),
            self._fetch_memory_insights(workspace_id)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_insights = []
        source_insights = {
            'ai': results[0] if not isinstance(results[0], Exception) else [],
            'user': results[1] if not isinstance(results[1], Exception) else [],
            'memory': results[2] if not isinstance(results[2], Exception) else []
        }
        
        # Log source statistics
        for source, insights in source_insights.items():
            logger.info(f"Fetched {len(insights)} insights from {source} source")
            if isinstance(insights, list):
                all_insights.extend(insights)
        
        # Deduplicate insights
        deduped = self._deduplicate_insights(all_insights)
        logger.info(f"Total unique insights after deduplication: {len(deduped)}")
        
        return deduped
    
    async def _fetch_ai_insights(self, workspace_id: str) -> List[UnifiedInsight]:
        """Fetch AI-generated insights from content-learning API"""
        try:
            # Use the existing content-learning API which works
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f'http://localhost:8000/api/content-learning/insights/{workspace_id}')
                if response.status_code != 200:
                    logger.error(f"Failed to fetch AI insights: {response.status_code}")
                    return []
                
                data = response.json()
                
            if 'actionable_insights' not in data:
                return []
            
            # Convert to unified format
            insights = []
            for idx, insight_text in enumerate(data.get('actionable_insights', [])):
                # Parse the formatted insight text
                unified = self._parse_ai_insight(insight_text, workspace_id)
                if unified:
                    insights.append(unified)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error fetching AI insights: {e}")
            return []
    
    async def _fetch_user_insights(self, workspace_id: str) -> List[UnifiedInsight]:
        """Fetch user-managed insights from database"""
        try:
            client = get_supabase_client()
            
            # Query workspace_insights table
            response = client.table('workspace_insights').select('*').eq(
                'workspace_id', workspace_id
            ).eq('is_deleted', False).execute()
            
            insights = []
            for record in response.data:
                unified = self._convert_user_insight(record)
                if unified:
                    insights.append(unified)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error fetching user insights: {e}")
            return []
    
    async def _fetch_memory_insights(self, workspace_id: str) -> List[UnifiedInsight]:
        """Fetch insights from workspace memory if available"""
        try:
            # Try to import workspace_memory
            from workspace_memory import workspace_memory
            from models import MemoryQueryRequest, InsightType
            
            # Query all insight types
            query = MemoryQueryRequest(
                query="all insights patterns discoveries",
                limit=100
            )
            response = await workspace_memory.query_insights(UUID(workspace_id), query)
            
            insights = []
            for memory_insight in response.insights:
                unified = self._convert_memory_insight(memory_insight, workspace_id)
                if unified:
                    insights.append(unified)
            
            return insights
            
        except ImportError:
            logger.info("Workspace memory not available")
            return []
        except Exception as e:
            logger.error(f"Error fetching memory insights: {e}")
            return []
    
    def _parse_ai_insight(self, insight_text: str, workspace_id: str) -> Optional[UnifiedInsight]:
        """Parse AI-generated insight text into unified format"""
        try:
            # Parse format: "✅ HIGH: metric shows X% better performance than baseline"
            confidence_level = InsightConfidenceLevel.MODERATE  # default
            
            # Extract confidence level from emoji/prefix
            if insight_text.startswith("✅") or "HIGH:" in insight_text:
                confidence_level = InsightConfidenceLevel.HIGH
                confidence_score = 0.85
            elif insight_text.startswith("📊") or "MODERATE:" in insight_text:
                confidence_level = InsightConfidenceLevel.MODERATE
                confidence_score = 0.65
            else:
                confidence_level = InsightConfidenceLevel.LOW
                confidence_score = 0.45
            
            # Clean the text
            clean_text = insight_text
            for prefix in ["✅", "📊", "🔍", "HIGH:", "MODERATE:", "LOW:"]:
                clean_text = clean_text.replace(prefix, "").strip()
            
            # Try to extract metric components
            metric_name = None
            metric_value = None
            comparison_baseline = None
            
            if "shows" in clean_text and "better performance than" in clean_text:
                parts = clean_text.split("shows")
                if len(parts) == 2:
                    metric_name = parts[0].strip()
                    value_part = parts[1].strip()
                    
                    if "%" in value_part:
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)\%', value_part)
                        if match:
                            metric_value = float(match.group(1)) / 100
                    
                    if "than" in value_part:
                        baseline_parts = value_part.split("than")
                        if len(baseline_parts) == 2:
                            comparison_baseline = baseline_parts[1].strip()
            
            # Create title from content
            title = clean_text[:100] + "..." if len(clean_text) > 100 else clean_text
            
            return UnifiedInsight(
                workspace_id=UUID(workspace_id),
                origin=InsightOrigin.AI_GENERATED,
                title=title,
                content=clean_text,
                category=InsightCategory.PERFORMANCE if metric_name else InsightCategory.DISCOVERY,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                metric_name=metric_name,
                metric_value=metric_value,
                comparison_baseline=comparison_baseline,
                created_by="ai_system",
                business_value_score=confidence_score * 0.9,  # Derive from confidence
                actionability_score=0.7 if metric_name else 0.5
            )
            
        except Exception as e:
            logger.error(f"Error parsing AI insight: {e}")
            return None
    
    def _convert_user_insight(self, record: Dict[str, Any]) -> Optional[UnifiedInsight]:
        """Convert database record to unified insight"""
        try:
            return UnifiedInsight(
                id=UUID(record['id']),
                workspace_id=UUID(record['workspace_id']),
                origin=InsightOrigin.USER_CREATED if record.get('is_user_created') else InsightOrigin.USER_MODIFIED,
                title=record['title'],
                content=record['content'],
                category=InsightCategory(record.get('category', 'general')),
                confidence_level=self._score_to_level(record.get('confidence_score', 0.5)),
                confidence_score=record.get('confidence_score', 0.5),
                domain_context=record.get('domain_type'),
                created_by=record.get('created_by', 'unknown'),
                created_at=datetime.fromisoformat(record['created_at']) if isinstance(record['created_at'], str) else record['created_at'],
                updated_at=datetime.fromisoformat(record['updated_at']) if isinstance(record['updated_at'], str) else record['updated_at'],
                is_verified=record.get('user_flags', {}).get('verified', False),
                is_important=record.get('user_flags', {}).get('important', False),
                is_outdated=record.get('user_flags', {}).get('outdated', False),
                needs_review=record.get('user_flags', {}).get('needs_review', False),
                tags=record.get('tags', []),
                action_recommendations=record.get('recommendations', []),
                business_value_score=record.get('business_value_score', 0.5),
                version=record.get('version_number', 1),
                is_deleted=record.get('is_deleted', False),
                metadata=record.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error converting user insight: {e}")
            return None
    
    def _convert_memory_insight(self, memory_insight: Any, workspace_id: str) -> Optional[UnifiedInsight]:
        """Convert workspace memory insight to unified format"""
        try:
            return UnifiedInsight(
                id=memory_insight.id,
                workspace_id=UUID(workspace_id),
                origin=InsightOrigin.WORKSPACE_MEMORY,
                title=memory_insight.content[:100] + "..." if len(memory_insight.content) > 100 else memory_insight.content,
                content=memory_insight.content,
                category=self._map_insight_type(memory_insight.insight_type.value),
                confidence_level=self._score_to_level(memory_insight.confidence_score),
                confidence_score=memory_insight.confidence_score,
                created_at=memory_insight.created_at,
                tags=memory_insight.relevance_tags,
                business_value_score=memory_insight.confidence_score * 0.8
            )
        except Exception as e:
            logger.error(f"Error converting memory insight: {e}")
            return None
    
    def _deduplicate_insights(self, insights: List[UnifiedInsight]) -> List[UnifiedInsight]:
        """Remove duplicate insights, preferring user-modified versions"""
        seen_contents = {}
        deduped = []
        
        # Sort by priority: user_modified > user_created > memory > ai_generated
        priority_map = {
            InsightOrigin.USER_MODIFIED: 0,
            InsightOrigin.USER_CREATED: 1,
            InsightOrigin.WORKSPACE_MEMORY: 2,
            InsightOrigin.AI_GENERATED: 3,
            InsightOrigin.EXTERNAL_IMPORT: 4
        }
        
        sorted_insights = sorted(insights, key=lambda x: priority_map.get(x.origin, 5))
        
        for insight in sorted_insights:
            # Create content hash for deduplication
            content_hash = hashlib.md5(insight.content.lower().encode()).hexdigest()
            
            if content_hash not in seen_contents:
                seen_contents[content_hash] = True
                deduped.append(insight)
            else:
                # If higher priority version exists, skip
                logger.debug(f"Skipping duplicate insight: {insight.title[:50]}")
        
        return deduped
    
    def _apply_filters(
        self,
        insights: List[UnifiedInsight],
        category: Optional[str],
        confidence_level: Optional[str],
        origin: Optional[str],
        include_deleted: bool
    ) -> List[UnifiedInsight]:
        """Apply filters to insight list"""
        filtered = insights
        
        if not include_deleted:
            filtered = [i for i in filtered if not i.is_deleted]
        
        if category:
            filtered = [i for i in filtered if i.category.value == category]
        
        if confidence_level:
            filtered = [i for i in filtered if i.confidence_level.value == confidence_level]
        
        if origin:
            filtered = [i for i in filtered if i.origin.value == origin]
        
        # Sort by business value and recency
        filtered.sort(key=lambda x: (x.business_value_score, x.created_at), reverse=True)
        
        return filtered
    
    def _paginate_response(
        self, 
        insights: List[UnifiedInsight], 
        limit: int, 
        offset: int, 
        cache_status: str
    ) -> UnifiedInsightResponse:
        """Create paginated response"""
        total = len(insights)
        paginated = insights[offset:offset + limit]
        
        # Determine which source systems contributed
        source_systems = list(set(i.origin.value for i in paginated))
        
        return UnifiedInsightResponse(
            insights=paginated,
            total=total,
            offset=offset,
            limit=limit,
            filters_applied={
                "total_before_pagination": len(insights)
            },
            source_systems=source_systems,
            cache_status=cache_status
        )
    
    def _score_to_level(self, score: float) -> InsightConfidenceLevel:
        """Convert numeric score to confidence level"""
        if score >= 0.8:
            return InsightConfidenceLevel.HIGH
        elif score >= 0.6:
            return InsightConfidenceLevel.MODERATE
        elif score >= 0.3:
            return InsightConfidenceLevel.LOW
        else:
            return InsightConfidenceLevel.EXPLORATORY
    
    def _map_insight_type(self, insight_type: str) -> InsightCategory:
        """Map memory insight type to unified category"""
        mapping = {
            'success_pattern': InsightCategory.PERFORMANCE,
            'failure_lesson': InsightCategory.RISK,
            'discovery': InsightCategory.DISCOVERY,
            'constraint': InsightCategory.CONSTRAINT,
            'optimization': InsightCategory.OPTIMIZATION,
            'progress': InsightCategory.OPERATIONAL
        }
        return mapping.get(insight_type, InsightCategory.GENERAL)
    
    async def persist_valuable_insights(self, workspace_id: str):
        """Background job to persist high-value AI insights"""
        try:
            insights = await self.get_unified_insights(workspace_id, origin=InsightOrigin.AI_GENERATED.value)
            
            client = get_supabase_client()
            persisted_count = 0
            
            for insight in insights.insights:
                if insight.should_persist():
                    # Check if already exists
                    existing = client.table('workspace_insights').select('id').eq(
                        'workspace_id', workspace_id
                    ).eq('content', insight.content).execute()
                    
                    if not existing.data:
                        # Persist to database
                        record = {
                            'workspace_id': str(insight.workspace_id),
                            'title': insight.title,
                            'content': insight.content,
                            'category': insight.category.value,
                            'confidence_score': insight.confidence_score,
                            'business_value_score': insight.business_value_score,
                            'created_by': 'ai_system',
                            'is_user_created': False,
                            'metadata': {
                                'origin': 'ai_persisted',
                                'metric_name': insight.metric_name,
                                'metric_value': insight.metric_value,
                                'comparison_baseline': insight.comparison_baseline
                            }
                        }
                        
                        client.table('workspace_insights').insert(record).execute()
                        persisted_count += 1
            
            logger.info(f"Persisted {persisted_count} valuable insights for workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Error persisting insights: {e}")
    
    async def get_sync_status(self, workspace_id: str) -> InsightSyncStatus:
        """Get synchronization status between all systems"""
        try:
            # Fetch counts from each source
            ai_insights = await self._fetch_ai_insights(workspace_id)
            user_insights = await self._fetch_user_insights(workspace_id)
            memory_insights = await self._fetch_memory_insights(workspace_id)
            
            # Get unified count
            unified = await self.get_unified_insights(workspace_id)
            
            return InsightSyncStatus(
                workspace_id=UUID(workspace_id),
                ai_insights_count=len(ai_insights),
                user_insights_count=len(user_insights),
                memory_insights_count=len(memory_insights),
                total_unified=unified.total,
                last_sync=datetime.utcnow(),
                sync_errors=[],
                pending_syncs=0
            )
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            raise


# Singleton instance
unified_insights_orchestrator = UnifiedInsightsOrchestrator()