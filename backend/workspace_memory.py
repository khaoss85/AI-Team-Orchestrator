# backend/workspace_memory.py
"""
Workspace Memory System - Minimal implementation
Gestisce insights e memoria contestuale per migliorare performance agenti.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from collections import defaultdict

from database import get_supabase_client, get_supabase_service_client
from models import (
    WorkspaceInsight, 
    InsightType, 
    MemoryQueryRequest, 
    MemoryQueryResponse,
    WorkspaceMemorySummary,
    Task
)

logger = logging.getLogger(__name__)

class WorkspaceMemory:
    """
    Sistema di memoria per workspace - gestisce insights e context per migliorare coordination tra agenti.
    Design principles:
    - Minimal: solo insights chiave, non full conversation history
    - Targeted: focus su lessons learned e discoveries utili
    - Anti-pollution: limiti su quantità e scadenza insights
    - Performance: query ottimizzate per retrieval veloce
    """
    
    def __init__(self):
        self.supabase = get_supabase_client() # Client standard per letture, se necessario
        self.supabase_service = get_supabase_service_client() # Client con privilegi per scritture
        
        # Test service client validity
        try:
            # Test with a simple query to verify service client works
            test_result = self.supabase_service.table("workspaces").select("id").limit(1).execute()
            logger.info("✅ WorkspaceMemory initialized with valid service client")
        except Exception as e:
            logger.error(f"❌ Service client authentication failed: {e}")
            logger.error("❌ CRITICAL: WorkspaceMemory requires valid SUPABASE_SERVICE_KEY")
            raise ValueError("Invalid or expired SUPABASE_SERVICE_KEY. Please update .env file with valid service key.")
        
        # Anti-pollution settings
        self.max_insights_per_workspace = 100  # Limite massimo insights per workspace
        self.default_insight_ttl_days = 30     # TTL default per insights (anti-stale)
        self.min_confidence_threshold = 0.3   # Soglia minima confidence per storage
        
        # Performance settings  
        self.query_cache: Dict[str, Tuple[datetime, List[WorkspaceInsight]]] = {}
        self.cache_ttl_seconds = 300  # 5 minuti cache
        
        logger.info("WorkspaceMemory initialized with anti-pollution controls")

    async def store_insight(
        self, 
        workspace_id: UUID, 
        task_id: Optional[UUID] = None,
        agent_role: str = "system",
        insight_type: InsightType = InsightType.DISCOVERY,
        content: str = "",
        relevance_tags: List[str] = None,
        confidence_score: float = 1.0,
        ttl_days: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[WorkspaceInsight]:
        """
        Store a workspace insight with anti-pollution controls
        """
        try:
            # 🚨 ANTI-POLLUTION: Validate input with adaptive thresholds
            # Get workspace context to adjust thresholds for early tasks
            current_count = await self._get_workspace_insight_count(workspace_id)
            
            # Lower thresholds for early tasks (first 5 insights)
            min_length = 5 if current_count < 5 else 10
            min_confidence = 0.1 if current_count < 5 else self.min_confidence_threshold
            
            if len(content.strip()) < min_length:
                logger.debug(f"Insight too short ({len(content.strip())} < {min_length}), skipping: {content[:50]}")
                return None
                
            if confidence_score < min_confidence:
                logger.debug(f"Confidence too low ({confidence_score} < {min_confidence}), skipping insight")
                return None
            
            # Truncate content to 200 chars max
            content = content.strip()[:200]
            
            # Set expiration 
            expires_at = None
            if ttl_days is not None:
                expires_at = datetime.now() + timedelta(days=ttl_days)
            elif self.default_insight_ttl_days > 0:
                expires_at = datetime.now() + timedelta(days=self.default_insight_ttl_days)
            
            # 🚨 ANTI-POLLUTION: Check workspace insight count
            await self._cleanup_old_insights(workspace_id)
            # current_count already retrieved above for adaptive thresholds
            
            if current_count >= self.max_insights_per_workspace:
                logger.warning(f"Workspace {workspace_id} at max insights ({current_count}), skipping storage")
                return None
            
            # Create insight
            insight_data = {
                "id": uuid4(),
                "workspace_id": workspace_id,
                "agent_role": agent_role,
                "insight_type": insight_type,
                "content": content,
                "relevance_tags": relevance_tags or [],
                "confidence_score": confidence_score,
                "expires_at": expires_at,
                "created_at": datetime.now(),
                "metadata": metadata or {}
            }
            
            # Add task_id only if provided
            if task_id is not None:
                insight_data["task_id"] = task_id
                
            insight = WorkspaceInsight(**insight_data)
            
            # Store in database
            await self._insert_insight_to_db(insight)
            
            # Clear cache for this workspace
            self._clear_workspace_cache(workspace_id)
            
            # Handle both enum and string types for insight_type
            insight_type_value = insight_type.value if hasattr(insight_type, 'value') else str(insight_type)
            logger.info(f"✅ Stored insight: {insight_type_value} for workspace {workspace_id}")
            return insight
            
        except Exception as e:
            logger.error(f"Error storing insight: {e}", exc_info=True)
            return None

    async def query_insights(
        self, 
        workspace_id: UUID, 
        request: MemoryQueryRequest
    ) -> MemoryQueryResponse:
        """
        Query workspace insights with caching and filtering
        """
        try:
            # Check cache first
            cache_key = f"{workspace_id}_{hash(str(request.dict()))}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for workspace {workspace_id} query")
                insights, total = cached_result
                return MemoryQueryResponse(
                    insights=insights,
                    total_found=total,
                    query_context=self._build_query_context(insights, request.query)
                )
            
            # Query database
            insights = await self._query_insights_from_db(workspace_id, request)
            
            # Cache result
            self._cache_result(cache_key, (insights, len(insights)))
            
            # Build context for agent
            query_context = self._build_query_context(insights, request.query)
            
            logger.info(f"🔍 Found {len(insights)} insights for workspace {workspace_id}")
            return MemoryQueryResponse(
                insights=insights,
                total_found=len(insights),
                query_context=query_context
            )
            
        except Exception as e:
            logger.error(f"Error querying insights: {e}", exc_info=True)
            return MemoryQueryResponse(insights=[], total_found=0, query_context="")

    async def get_workspace_summary(self, workspace_id: UUID) -> WorkspaceMemorySummary:
        """
        Get comprehensive summary of workspace memory
        """
        try:
            # Get all active insights
            all_insights = await self._get_all_workspace_insights(workspace_id)
            
            # Build summary statistics
            total_insights = len(all_insights)
            insights_by_type = defaultdict(int)
            tag_counts = defaultdict(int)
            
            recent_discoveries = []
            key_constraints = []
            success_patterns = []
            
            for insight in all_insights:
                insights_by_type[insight.insight_type.value] += 1
                
                for tag in insight.relevance_tags:
                    tag_counts[tag] += 1
                
                # Categorize by type for summary
                if insight.insight_type == InsightType.DISCOVERY:
                    recent_discoveries.append(insight.content)
                elif insight.insight_type == InsightType.CONSTRAINT:
                    key_constraints.append(insight.content)
                elif insight.insight_type == InsightType.SUCCESS_PATTERN:
                    success_patterns.append(insight.content)
            
            # Top tags (limit to 10)
            top_tags = [tag for tag, _ in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
            
            return WorkspaceMemorySummary(
                workspace_id=workspace_id,
                total_insights=total_insights,
                insights_by_type=dict(insights_by_type),
                top_tags=top_tags,
                recent_discoveries=recent_discoveries[:5],  # Latest 5
                key_constraints=key_constraints[:5],        # Latest 5
                success_patterns=success_patterns[:5],      # Latest 5
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting workspace summary: {e}", exc_info=True)
            return WorkspaceMemorySummary(workspace_id=workspace_id)
    
    async def store_quality_validation_learning(
        self, 
        workspace_id: UUID, 
        task_id: str,
        quality_assessment: Dict[str, Any],
        task_context: Dict[str, Any] = None
    ) -> str:
        """
        🎯 QUALITY VALIDATION LEARNING: Store learnings from quality validation results
        
        Memorizza insights basati sui risultati della validazione qualità per migliorare
        future task execution e quality predictions.
        """
        try:
            passes_quality = quality_assessment.get('passes_quality_gate', False)
            quality_score = quality_assessment.get('score', 0)
            reasoning = quality_assessment.get('reasoning', '')
            
            # Determina tipo di insight basato sul risultato
            if passes_quality and quality_score >= 90:
                insight_type = InsightType.SUCCESS_PATTERN
                content = f"HIGH QUALITY SUCCESS: Task {task_id[:8]} achieved {quality_score}% quality. Pattern: {reasoning}"
                relevance_tags = ["quality_success", "high_score", "best_practice"]
                confidence = 0.9
                
            elif passes_quality and quality_score >= 70:
                insight_type = InsightType.SUCCESS_PATTERN  
                content = f"QUALITY SUCCESS: Task {task_id[:8]} passed validation with {quality_score}%. Approach: {reasoning}"
                relevance_tags = ["quality_pass", "acceptable_pattern"]
                confidence = 0.7
                
            elif not passes_quality:
                insight_type = InsightType.CONSTRAINT
                content = f"QUALITY FAILURE: Task {task_id[:8]} failed validation ({quality_score}%). Issue: {reasoning}"
                relevance_tags = ["quality_failure", "avoid_pattern", "improvement_needed"]
                confidence = 0.8
                
            else:
                insight_type = InsightType.DISCOVERY
                content = f"QUALITY BORDERLINE: Task {task_id[:8]} had mixed results ({quality_score}%). Analysis: {reasoning}"
                relevance_tags = ["quality_borderline", "requires_attention"]
                confidence = 0.6
            
            # Aggiungi contesto specifico del task se disponibile
            if task_context:
                task_type = task_context.get('task_type', 'unknown')
                agent_id = task_context.get('agent_id', 'unknown')
                relevance_tags.extend([f"task_type_{task_type}", f"agent_{agent_id}"])
                
                # Arricchisci il contenuto con dettagli del task
                content += f" [Task Type: {task_type}, Agent: {agent_id}]"
            
            # Crea metadata con dettagli completi per future analisi
            metadata = {
                "task_id": task_id,
                "quality_score": quality_score,
                "passes_quality_gate": passes_quality,
                "quality_reasoning": reasoning,
                "learning_type": "quality_validation",
                "task_context": task_context or {},
                "created_from": "quality_validation_learning"
            }
            
            # Store insight usando metodo esistente
            insight_id = await self.store_insight(
                workspace_id=workspace_id,
                insight_type=insight_type,
                content=content,
                relevance_tags=relevance_tags,
                confidence_score=confidence,
                metadata=metadata
            )
            
            logger.info(f"✅ Quality validation learning stored: {insight_id} for task {task_id}")
            return insight_id
            
        except Exception as e:
            logger.error(f"Failed to store quality validation learning: {e}")
            return f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def get_quality_patterns_for_task_type(
        self, 
        workspace_id: UUID, 
        task_type: str,
        agent_id: str = None
    ) -> Dict[str, Any]:
        """
        🎯 QUALITY PATTERN RETRIEVAL: Get learned quality patterns for specific task types
        
        Retrieves learned patterns from quality validation to help predict and improve
        quality for similar future tasks.
        """
        try:
            # Build query filters
            tag_filters = [f"task_type_{task_type}"]
            if agent_id:
                tag_filters.append(f"agent_{agent_id}")
            
            # Get insights related to this task type
            all_insights = await self._get_insights_by_tags(workspace_id, tag_filters)
            
            # Categorize insights by quality outcomes
            success_patterns = []
            failure_patterns = []
            best_practices = []
            common_issues = []
            
            for insight in all_insights:
                metadata = insight.metadata or {}
                quality_score = metadata.get('quality_score', 0)
                passes_quality = metadata.get('passes_quality_gate', False)
                
                if insight.insight_type == InsightType.SUCCESS_PATTERN:
                    if quality_score >= 90:
                        best_practices.append({
                            "content": insight.content,
                            "quality_score": quality_score,
                            "confidence": insight.confidence_score,
                            "reasoning": metadata.get('quality_reasoning', ''),
                            "created_at": insight.created_at
                        })
                    elif passes_quality:
                        success_patterns.append({
                            "content": insight.content,
                            "quality_score": quality_score,
                            "confidence": insight.confidence_score,
                            "reasoning": metadata.get('quality_reasoning', ''),
                            "created_at": insight.created_at
                        })
                
                elif insight.insight_type == InsightType.CONSTRAINT:
                    if not passes_quality:
                        failure_patterns.append({
                            "content": insight.content,
                            "quality_score": quality_score,
                            "confidence": insight.confidence_score,
                            "issue": metadata.get('quality_reasoning', ''),
                            "created_at": insight.created_at
                        })
                        
                        # Extract common issues
                        issue_summary = metadata.get('quality_reasoning', '').lower()
                        if issue_summary:
                            common_issues.append(issue_summary)
            
            # Calculate quality statistics
            all_scores = [metadata.get('quality_score', 0) for insight in all_insights 
                         if insight.metadata and 'quality_score' in insight.metadata]
            
            quality_stats = {
                "avg_quality_score": sum(all_scores) / len(all_scores) if all_scores else 0,
                "max_quality_score": max(all_scores) if all_scores else 0,
                "min_quality_score": min(all_scores) if all_scores else 0,
                "total_validations": len(all_scores),
                "success_rate": sum(1 for insight in all_insights 
                                  if insight.metadata and insight.metadata.get('passes_quality_gate', False)) / len(all_insights) if all_insights else 0
            }
            
            # Generate recommendations based on patterns
            recommendations = []
            if best_practices:
                recommendations.append(f"Follow best practices from {len(best_practices)} high-quality examples")
            if failure_patterns:
                recommendations.append(f"Avoid {len(failure_patterns)} known failure patterns")
            if quality_stats["avg_quality_score"] < 70:
                recommendations.append("Quality score is below average - review task approach")
            
            return {
                "task_type": task_type,
                "agent_id": agent_id,
                "quality_statistics": quality_stats,
                "best_practices": sorted(best_practices, key=lambda x: x['quality_score'], reverse=True)[:3],
                "success_patterns": sorted(success_patterns, key=lambda x: x['quality_score'], reverse=True)[:5],
                "failure_patterns": sorted(failure_patterns, key=lambda x: x['created_at'], reverse=True)[:3],
                "common_issues": list(set(common_issues))[:5],
                "recommendations": recommendations,
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality patterns for task type {task_type}: {e}")
            return {
                "task_type": task_type,
                "error": str(e),
                "recommendations": ["Quality pattern analysis unavailable - proceed with caution"]
            }
    
    async def get_asset_success_patterns_for_type(
        self, 
        workspace_id: UUID, 
        asset_type: str,
        goal_metric_type: str = None
    ) -> Dict[str, Any]:
        """
        🎯 ASSET SUCCESS PATTERN RETRIEVAL: Get learned asset success patterns for specific asset types
        
        Retrieves learned patterns from successful asset creation to guide future asset development
        and improve deliverable quality.
        """
        try:
            # Build query filters for asset success patterns
            tag_filters = [f"asset_type_{asset_type.lower()}", "asset_success"]
            if goal_metric_type:
                tag_filters.append(f"metric_{goal_metric_type}")
            
            # Get insights related to asset success
            all_insights = await self._get_insights_by_tags(workspace_id, tag_filters)
            
            # Categorize insights by success level
            high_quality_patterns = []
            standard_quality_patterns = []
            best_practices = []
            success_factors = []
            
            for insight in all_insights:
                metadata = insight.metadata or {}
                quality_score = metadata.get('quality_score', 0)
                artifact_name = metadata.get('artifact_name', 'unnamed')
                
                if insight.insight_type == InsightType.SUCCESS_PATTERN:
                    pattern_data = {
                        "content": insight.content,
                        "artifact_name": artifact_name,
                        "quality_score": quality_score,
                        "business_value_score": metadata.get('business_value_score', 0),
                        "actionability_score": metadata.get('actionability_score', 0),
                        "content_format": metadata.get('content_format', 'unknown'),
                        "ai_enhanced": metadata.get('ai_enhanced', False),
                        "confidence": insight.confidence_score,
                        "created_at": insight.created_at,
                        "creation_context": metadata.get('creation_context', {})
                    }
                    
                    if quality_score >= 90:
                        high_quality_patterns.append(pattern_data)
                        
                        # Extract best practices from high-quality assets
                        context = metadata.get('creation_context', {})
                        success_factors_text = context.get('success_factors', '')
                        if success_factors_text:
                            success_factors.append(success_factors_text)
                        
                        approach_text = context.get('creation_approach', '')
                        if approach_text:
                            best_practices.append(f"{approach_text} (Quality: {quality_score}%)")
                    
                    elif quality_score >= 70:
                        standard_quality_patterns.append(pattern_data)
            
            # Calculate asset success statistics
            all_scores = [metadata.get('quality_score', 0) for insight in all_insights 
                         if insight.metadata and 'quality_score' in insight.metadata]
            
            asset_stats = {
                "avg_quality_score": sum(all_scores) / len(all_scores) if all_scores else 0,
                "max_quality_score": max(all_scores) if all_scores else 0,
                "min_quality_score": min(all_scores) if all_scores else 0,
                "total_successful_assets": len(all_scores),
                "high_quality_rate": len([s for s in all_scores if s >= 90]) / len(all_scores) if all_scores else 0,
                "quality_pass_rate": len([s for s in all_scores if s >= 70]) / len(all_scores) if all_scores else 0
            }
            
            # Analyze common success factors
            unique_success_factors = list(set(success_factors))
            format_preferences = {}
            enhancement_patterns = {"ai_enhanced": 0, "manual": 0}
            
            for insight in all_insights:
                metadata = insight.metadata or {}
                content_format = metadata.get('content_format')
                if content_format:
                    format_preferences[content_format] = format_preferences.get(content_format, 0) + 1
                
                if metadata.get('ai_enhanced'):
                    enhancement_patterns["ai_enhanced"] += 1
                else:
                    enhancement_patterns["manual"] += 1
            
            # Generate asset-specific recommendations
            recommendations = []
            if asset_stats["avg_quality_score"] >= 80:
                recommendations.append(f"Excellent track record for {asset_type} assets - continue current approach")
            elif asset_stats["avg_quality_score"] >= 70:
                recommendations.append(f"Good quality trend for {asset_type} assets - review high-quality examples")
            else:
                recommendations.append(f"Quality improvement needed for {asset_type} assets - analyze best practices")
            
            if format_preferences:
                best_format = max(format_preferences.items(), key=lambda x: x[1])
                recommendations.append(f"Prefer {best_format[0]} format (used in {best_format[1]} successful assets)")
            
            if enhancement_patterns["ai_enhanced"] > enhancement_patterns["manual"]:
                recommendations.append("AI-enhanced content shows better results - leverage AI tools")
            
            return {
                "asset_type": asset_type,
                "goal_metric_type": goal_metric_type,
                "asset_statistics": asset_stats,
                "high_quality_patterns": sorted(high_quality_patterns, key=lambda x: x['quality_score'], reverse=True)[:3],
                "standard_quality_patterns": sorted(standard_quality_patterns, key=lambda x: x['quality_score'], reverse=True)[:5],
                "best_practices": list(set(best_practices))[:5],
                "success_factors": unique_success_factors[:5],
                "format_preferences": format_preferences,
                "enhancement_patterns": enhancement_patterns,
                "recommendations": recommendations,
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get asset success patterns for type {asset_type}: {e}")
            return {
                "asset_type": asset_type,
                "error": str(e),
                "recommendations": ["Asset pattern analysis unavailable - proceed with standard approach"]
            }
    
    async def _get_insights_by_tags(self, workspace_id: UUID, tags: List[str]) -> List[WorkspaceInsight]:
        """Helper method to get insights by relevance tags"""
        try:
            # Use service client for data access
            query = self.supabase_service.table("workspace_insights").select("*")\
                .eq("workspace_id", str(workspace_id))
            
            # Filter by tags (PostgreSQL array contains)
            for tag in tags:
                query = query.contains("relevance_tags", [tag])
            
            result = query.order("created_at", desc=True).limit(50).execute()
            
            if not result.data:
                return []
            
            # Convert to WorkspaceInsight objects
            insights = []
            for insight_data in result.data:
                insight = WorkspaceInsight(
                    id=UUID(insight_data["id"]),
                    workspace_id=UUID(insight_data["workspace_id"]),
                    insight_type=InsightType(insight_data["insight_type"]),
                    content=insight_data["content"],
                    relevance_tags=insight_data.get("relevance_tags", []),
                    confidence_score=insight_data.get("confidence_score", 0.5),
                    metadata=insight_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(insight_data["created_at"].replace("Z", "+00:00"))
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get insights by tags: {e}")
            return []

    async def get_relevant_context(
        self, 
        workspace_id: UUID, 
        current_task: Optional[Dict] = None,
        max_insights: int = 10,
        context_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🎯 STEP 5: Enhanced context retrieval with goal-driven filtering
        
        Get relevant context for current task execution with improved filtering:
        1. Goal-specific insights (filter by goal_id)
        2. Phase-specific insights (filter by phase)
        3. Reduced noise for specialists
        4. Strategic oversight preserved for coordinator
        """
        try:
            # 🎯 CONVERT TASK OBJECT TO DICT IF NEEDED
            if current_task and isinstance(current_task, Task):
                current_task_dict = {
                    "name": current_task.name,
                    "type": current_task.task_type,
                    "phase": current_task.project_phase,
                    "description": current_task.description,
                    "goal_id": current_task.goal_id,
                    "metric_type": current_task.metric_type,
                    "contribution_expected": current_task.contribution_expected,
                    "success_criteria": current_task.success_criteria
                }
                current_task = current_task_dict
            
            # 🎯 GOAL-DRIVEN FILTERING
            insight_types = ["success_pattern", "constraint", "discovery"]
            relevance_tags = []
            
            # Apply context filter if provided (from Step 3 integration)
            if context_filter:
                insight_types = context_filter.get("insight_types", insight_types)
                relevance_tags = context_filter.get("relevance_tags", [])
                max_insights = context_filter.get("limit", max_insights)
            
            # 🎯 TASK-SPECIFIC FILTERING
            if current_task:
                # Filter by goal_id if task is goal-driven
                goal_id = current_task.get("goal_id")
                metric_type = current_task.get("metric_type")
                
                if goal_id:
                    relevance_tags.append(f"goal_{goal_id}")
                if metric_type:
                    relevance_tags.append(f"metric_{metric_type}")
                
                # Filter by task type
                task_type = current_task.get("type", "")
                if task_type:
                    relevance_tags.append(f"task_{task_type}")
                
                # Add phase filtering if available
                phase = current_task.get("phase")
                if phase:
                    relevance_tags.append(f"phase_{phase}")
                
                # Build query from task context
                task_keywords = self._extract_task_keywords_from_dict(current_task)
                query = " ".join(task_keywords)
            else:
                query = "relevant insights for workspace execution"
            
            # 🧠 MEMORY QUERY with enhanced filtering
            request = MemoryQueryRequest(
                query=query,
                insight_types=insight_types,
                relevance_tags=relevance_tags,
                limit=max_insights
            )
            
            response = await self.query_insights(workspace_id, request)
            
            # 🎯 POST-PROCESS: Filter insights by goal alignment
            if current_task:
                relevant_insights = self._filter_insights_by_goal_alignment(
                    response.insights, current_task
                )
            else:
                relevant_insights = response.insights[:max_insights]
            
            if not relevant_insights:
                logger.debug(f"No relevant insights found for workspace {workspace_id}")
                return ""
            
            # 🎯 BUILD FOCUSED CONTEXT (reduced noise)
            context_parts = [
                "🧠 RELEVANT WORKSPACE MEMORY (Goal-Focused):",
                ""
            ]
            
            # Group insights by type for better organization
            insights_by_type = {}
            for insight in relevant_insights:
                insight_type = insight.insight_type.value
                if insight_type not in insights_by_type:
                    insights_by_type[insight_type] = []
                insights_by_type[insight_type].append(insight)
            
            # 🎯 PRIORITIZE SUCCESS PATTERNS and CONSTRAINTS for specialists
            priority_order = ["success_pattern", "constraint", "failure_lesson", "discovery", "optimization"]
            
            for insight_type in priority_order:
                if insight_type in insights_by_type:
                    insights = insights_by_type[insight_type]
                    context_parts.append(f"🎯 {insight_type.upper().replace('_', ' ')}:")
                    
                    for insight in insights[:3]:  # Limit to top 3 per type
                        context_parts.append(f"• {insight.content}")
                        
                        # Add goal context if available
                        goal_tags = [tag for tag in insight.relevance_tags if tag.startswith("goal_")]
                        if goal_tags:
                            context_parts.append(f"  Goal: {goal_tags[0].replace('goal_', '')}")
                    
                    context_parts.append("")
            
            # 🎯 ADD GOAL-SPECIFIC GUIDANCE
            if current_task and current_task.get("goal_id"):
                context_parts.extend([
                    "🎯 GOAL-DRIVEN FOCUS:",
                    f"• Your task contributes to goal: {current_task.get('metric_type', 'unknown')}",
                    f"• Expected contribution: {current_task.get('contribution_expected', 'not specified')}",
                    f"• Success criteria: {len(current_task.get('success_criteria', []))} specific requirements",
                    ""
                ])
            
            context_parts.append(
                "💡 Use these goal-focused insights to optimize your approach and ensure numerical targets are met."
            )
            
            logger.info(
                f"🧠 Built focused context: {len(relevant_insights)} insights, "
                f"{len(context_parts)} lines for workspace {workspace_id}"
            )
            
            context_text = "\n".join(context_parts)
            
            # 🔧 FIX CRITICO 2: Return Dict instead of str for compatibility
            return {
                "context_text": context_text,
                "insights_found": len(relevant_insights),
                "context_lines": len(context_parts),
                "workspace_id": str(workspace_id),
                "generated_at": datetime.now().isoformat(),
                "context_type": "workspace_memory_insights"
            }
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            # 🔧 FIX CRITICO 2: Return Dict fallback instead of empty string
            return {
                "context_text": "",
                "insights_found": 0,
                "context_lines": 0,
                "workspace_id": str(workspace_id),
                "generated_at": datetime.now().isoformat(),
                "context_type": "workspace_memory_insights_error",
                "error": str(e)
            }
    
    def _extract_task_keywords_from_dict(self, task: Dict[str, Any]) -> List[str]:
        """Extract keywords from task dictionary for memory querying"""
        keywords = []
        
        # Extract from task name and description
        task_name = task.get("name", "")
        task_description = task.get("description", "")
        
        # Basic keyword extraction
        import re
        text = f"{task_name} {task_description}".lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Filter meaningful words (length > 3, not common words)
        stop_words = {"the", "and", "for", "with", "this", "that", "from", "they", "have", "were", "been", "their"}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Add goal-specific keywords
        metric_type = task.get("metric_type")
        if metric_type:
            keywords.append(metric_type)
        
        # Add task type
        task_type = task.get("type")
        if task_type:
            keywords.append(task_type)
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def _filter_insights_by_goal_alignment(
        self, 
        insights: List[WorkspaceInsight], 
        current_task: Dict[str, Any]
    ) -> List[WorkspaceInsight]:
        """Filter insights by goal alignment and relevance to current task"""
        
        goal_id = current_task.get("goal_id")
        metric_type = current_task.get("metric_type")
        task_type = current_task.get("type")
        
        aligned_insights = []
        
        for insight in insights:
            relevance_score = 0
            
            # Goal ID alignment (highest priority)
            if goal_id and f"goal_{goal_id}" in insight.relevance_tags:
                relevance_score += 3
            
            # Metric type alignment
            if metric_type and f"metric_{metric_type}" in insight.relevance_tags:
                relevance_score += 2
            
            # Task type alignment
            if task_type and f"task_{task_type}" in insight.relevance_tags:
                relevance_score += 1
            
            # Success patterns and constraints are always valuable
            if insight.insight_type in [InsightType.SUCCESS_PATTERN, InsightType.CONSTRAINT]:
                relevance_score += 1
            
            # Only include insights with some relevance
            if relevance_score > 0:
                aligned_insights.append((insight, relevance_score))
        
        # Sort by relevance score and return top insights
        aligned_insights.sort(key=lambda x: x[1], reverse=True)
        return [insight for insight, _ in aligned_insights[:10]]

    # === PRIVATE METHODS ===

    async def _insert_insight_to_db(self, insight: WorkspaceInsight):
        """Insert insight into Supabase"""
        data = {
            "id": str(insight.id),
            "workspace_id": str(insight.workspace_id),
            "task_id": str(insight.task_id) if insight.task_id is not None else None,
            "agent_role": insight.agent_role,
            "insight_type": insight.insight_type.value,
            "content": insight.content,
            "relevance_tags": insight.relevance_tags,
            "confidence_score": insight.confidence_score,
            "expires_at": insight.expires_at.isoformat() if insight.expires_at else None,
            "created_at": insight.created_at.isoformat(),
            "metadata": insight.metadata or {}
        }
        
        result = self.supabase_service.table("workspace_insights").insert(data).execute()
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Failed to insert insight: {result.error.message}")

    async def _query_insights_from_db(
        self, 
        workspace_id: UUID, 
        request: MemoryQueryRequest
    ) -> List[WorkspaceInsight]:
        """Query insights from database with filters"""
        query = self.supabase_service.table("workspace_insights").select("*").eq("workspace_id", str(workspace_id))
        
        # Filter by insight types
        if request.insight_types:
            insight_type_values = [t.value for t in request.insight_types]
            query = query.in_("insight_type", insight_type_values)
        
        # Filter by confidence
        query = query.gte("confidence_score", request.min_confidence)
        
        # Filter expired insights
        if request.exclude_expired:
            query = query.or_("expires_at.is.null,expires_at.gt." + datetime.now().isoformat())
        
        # Filter by tags if provided
        if request.tags:
            for tag in request.tags:
                query = query.contains("relevance_tags", [tag])
        
        # Order by confidence and recency
        query = query.order("confidence_score", desc=True).order("created_at", desc=True)
        
        # Limit results
        query = query.limit(request.max_results)
        
        result = query.execute()
        
        insights = []
        for row in result.data:
            insight = WorkspaceInsight(
                id=UUID(row["id"]),
                workspace_id=UUID(row["workspace_id"]),
                task_id=UUID(row["task_id"]) if row["task_id"] is not None else None,
                agent_role=row["agent_role"],
                insight_type=InsightType(row["insight_type"]),
                content=row["content"],
                relevance_tags=row["relevance_tags"] or [],
                confidence_score=row["confidence_score"],
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=row.get("metadata", {})
            )
            insights.append(insight)
        
        return insights

    async def _get_workspace_insight_count(self, workspace_id: UUID) -> int:
        """Get current insight count for workspace"""
        result = self.supabase_service.table("workspace_insights").select("id", count="exact").eq("workspace_id", str(workspace_id)).execute()
        return result.count or 0

    async def _get_all_workspace_insights(self, workspace_id: UUID) -> List[WorkspaceInsight]:
        """Get all active insights for workspace"""
        request = MemoryQueryRequest(
            query="",
            max_results=20,  # Increased for summary
            min_confidence=0.0,
            exclude_expired=True
        )
        return await self._query_insights_from_db(workspace_id, request)

    async def _cleanup_old_insights(self, workspace_id: UUID):
        """Remove expired insights and enforce limits"""
        try:
            # Remove expired insights
            now = datetime.now().isoformat()
            self.supabase_service.table("workspace_insights").delete().eq("workspace_id", str(workspace_id)).lt("expires_at", now).execute()
            
            # If still too many, remove oldest low-confidence insights
            current_count = await self._get_workspace_insight_count(workspace_id)
            if current_count >= self.max_insights_per_workspace:
                excess = current_count - self.max_insights_per_workspace + 10  # Remove extra 10
                
                old_insights = self.supabase_service.table("workspace_insights").select("id").eq("workspace_id", str(workspace_id)).order("confidence_score").order("created_at").limit(excess).execute()
                
                if old_insights.data:
                    ids_to_delete = [row["id"] for row in old_insights.data]
                    self.supabase_service.table("workspace_insights").delete().in_("id", ids_to_delete).execute()
                    logger.info(f"Cleaned up {len(ids_to_delete)} old insights from workspace {workspace_id}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old insights: {e}")

    def _build_query_context(self, insights: List[WorkspaceInsight], query: str) -> str:
        """Build context string for agent consumption"""
        if not insights:
            return "No relevant project memory found."
        
        context_parts = []
        context_parts.append(f"RELEVANT PROJECT INSIGHTS ({len(insights)} found):")
        
        for insight in insights:
            emoji = "🔍"
            if insight.insight_type == InsightType.SUCCESS_PATTERN:
                emoji = "✅"
            elif insight.insight_type == InsightType.FAILURE_LESSON:
                emoji = "⚠️"
            elif insight.insight_type == InsightType.CONSTRAINT:
                emoji = "🚫"
            elif insight.insight_type == InsightType.OPTIMIZATION:
                emoji = "⚡"
            
            context_parts.append(f"{emoji} {insight.content}")
        
        return "\n".join(context_parts)

    def _extract_task_keywords(self, task: Task) -> List[str]:
        """Extract keywords from task for context matching"""
        text = f"{task.name} {task.description or ''}"
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w.isalpha()]
        
        return keywords[:10]  # Limit to 10 keywords

    def _get_from_cache(self, cache_key: str) -> Optional[Tuple[List[WorkspaceInsight], int]]:
        """Get result from cache if valid"""
        if cache_key in self.query_cache:
            cached_time, cached_data = self.query_cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl_seconds):
                return cached_data
            else:
                del self.query_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, data: Tuple[List[WorkspaceInsight], int]):
        """Cache query result"""
        self.query_cache[cache_key] = (datetime.now(), data)
        
        # Cleanup old cache entries
        if len(self.query_cache) > 100:
            oldest_key = min(self.query_cache.keys(), key=lambda k: self.query_cache[k][0])
            del self.query_cache[oldest_key]

    def _clear_workspace_cache(self, workspace_id: UUID):
        """Clear cache entries for specific workspace"""
        keys_to_remove = [k for k in self.query_cache.keys() if str(workspace_id) in k]
        for key in keys_to_remove:
            del self.query_cache[key]

# Singleton instance
workspace_memory = WorkspaceMemory()