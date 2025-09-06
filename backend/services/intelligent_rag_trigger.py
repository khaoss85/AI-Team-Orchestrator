#!/usr/bin/env python3
"""
🎯 INTELLIGENT RAG TRIGGER SERVICE

Automatic document search triggering during task execution.
Detects when document context would be helpful and automatically
searches workspace documents for relevant information.

Part of the Goal-Driven Intelligent Integration:
Memory → Enhanced Task Generation → RAG-Enhanced Execution → Quality Gates → Learning Feedback
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class IntelligentRAGTrigger:
    """
    🔍 Intelligent RAG Trigger for automatic document search during task execution
    
    Analyzes task context and automatically triggers document searches when:
    - Task mentions research, analysis, or documentation review
    - Task requires historical context or existing information
    - Task involves creating content based on existing materials
    - Task confidence is low and additional context would help
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        self.trigger_threshold = float(os.getenv("RAG_TRIGGER_CONFIDENCE_THRESHOLD", "0.7"))
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ Intelligent RAG Trigger initialized with AI")
            except ImportError:
                self.ai_available = False
                logger.warning("⚠️ OpenAI not available for intelligent RAG triggering")
        else:
            self.ai_available = False
            logger.info("ℹ️ RAG Trigger operating in rule-based mode")
    
    async def should_trigger_document_search(
        self, 
        task_name: str,
        task_description: str,
        task_type: Optional[str] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str], float]:
        """
        Determine if document search should be triggered for this task
        
        Returns:
            Tuple of (should_trigger, suggested_queries, confidence_score)
        """
        
        # Quick rule-based check for obvious cases
        quick_triggers = await self._check_quick_triggers(task_name, task_description)
        if quick_triggers[0]:
            return quick_triggers
        
        # AI-driven analysis for nuanced cases
        if self.ai_available:
            return await self._ai_analyze_rag_need(
                task_name, task_description, task_type, execution_context
            )
        
        # Fallback to comprehensive rule-based analysis
        return await self._rule_based_rag_analysis(
            task_name, task_description, task_type
        )
    
    async def _check_quick_triggers(
        self, 
        task_name: str, 
        task_description: str
    ) -> Tuple[bool, List[str], float]:
        """Quick pattern matching for obvious RAG triggers"""
        
        trigger_keywords = [
            "research", "analyze", "review", "documentation", "existing",
            "historical", "previous", "based on", "reference", "context",
            "background", "prior", "update", "improve", "enhance existing"
        ]
        
        text_to_check = f"{task_name} {task_description}".lower()
        
        for keyword in trigger_keywords:
            if keyword in text_to_check:
                # Generate suggested queries based on the task
                queries = await self._generate_search_queries(task_name, task_description)
                return (True, queries, 0.85)
        
        return (False, [], 0.0)
    
    async def _ai_analyze_rag_need(
        self,
        task_name: str,
        task_description: str,
        task_type: Optional[str],
        execution_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str], float]:
        """Use AI to determine if RAG would be helpful"""
        
        try:
            prompt = f"""
            Analyze this task and determine if searching existing workspace documents would be helpful.
            
            Task: {task_name}
            Description: {task_description}
            Type: {task_type or 'general'}
            Context: {execution_context or 'No additional context'}
            
            Consider:
            1. Would existing documents provide useful context?
            2. Does the task require knowledge of previous work?
            3. Would document search improve task execution quality?
            4. Are there likely to be relevant documents in the workspace?
            
            Respond with JSON:
            {{
                "should_search": true/false,
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                "suggested_queries": ["query1", "query2", "query3"] // max 3
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an intelligent document search analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = eval(response.choices[0].message.content)
            
            if result["should_search"] and result["confidence"] >= self.trigger_threshold:
                logger.info(f"🔍 AI recommends RAG: {result['reasoning']}")
                return (True, result["suggested_queries"], result["confidence"])
            
            return (False, [], result["confidence"])
            
        except Exception as e:
            logger.error(f"Error in AI RAG analysis: {e}")
            # Fallback to rule-based
            return await self._rule_based_rag_analysis(task_name, task_description, task_type)
    
    async def _rule_based_rag_analysis(
        self,
        task_name: str,
        task_description: str,
        task_type: Optional[str]
    ) -> Tuple[bool, List[str], float]:
        """Comprehensive rule-based RAG triggering"""
        
        confidence = 0.0
        
        # Task type analysis
        if task_type:
            rag_beneficial_types = [
                "research", "analysis", "documentation", "content_creation",
                "update", "review", "improvement", "enhancement"
            ]
            if any(t in task_type.lower() for t in rag_beneficial_types):
                confidence += 0.4
        
        # Description complexity analysis
        desc_length = len(task_description.split())
        if desc_length > 20:  # Complex tasks benefit from context
            confidence += 0.2
        
        # Specific patterns that benefit from RAG
        patterns = [
            r"based on .* (document|material|content)",
            r"update .* (documentation|content|material)",
            r"analyze .* (existing|current|previous)",
            r"improve .* (current|existing)",
            r"create .* from .* (template|example|reference)"
        ]
        
        import re
        text = f"{task_name} {task_description}".lower()
        for pattern in patterns:
            if re.search(pattern, text):
                confidence += 0.3
                break
        
        if confidence >= 0.6:
            queries = await self._generate_search_queries(task_name, task_description)
            return (True, queries, min(confidence, 1.0))
        
        return (False, [], confidence)
    
    async def _generate_search_queries(
        self, 
        task_name: str, 
        task_description: str
    ) -> List[str]:
        """Generate intelligent search queries based on task context"""
        
        queries = []
        
        # Extract key terms from task name
        import re
        key_terms = re.findall(r'\b[A-Z][a-z]+\b|\b\w+(?:ing|tion|ment)\b', task_name)
        if key_terms:
            queries.append(" ".join(key_terms[:3]))
        
        # Extract action and object from description
        words = task_description.split()[:20]  # First 20 words
        
        # Look for action verbs and their objects
        action_verbs = ["create", "update", "analyze", "review", "improve", "develop", "design"]
        for i, word in enumerate(words):
            if word.lower() in action_verbs and i + 1 < len(words):
                # Get the next 2-3 words as the object
                object_phrase = " ".join(words[i+1:min(i+4, len(words))])
                queries.append(object_phrase)
                break
        
        # Add a general query if we don't have enough
        if len(queries) < 2:
            queries.append(task_name.replace("_", " ").replace("-", " "))
        
        # Limit to 3 queries and remove duplicates
        seen = set()
        unique_queries = []
        for q in queries[:3]:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        return unique_queries
    
    async def execute_intelligent_document_search(
        self,
        workspace_id: str,
        agent_id: str,
        search_queries: List[str],
        max_results_per_query: int = 3
    ) -> Dict[str, Any]:
        """
        Execute the document searches and aggregate results
        
        Returns aggregated search results with relevance scoring
        """
        
        try:
            # Import specialist agent for document access
            from ai_agents.specialist import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create a temporary specialist instance for search
            # This is a lightweight operation as it reuses existing assistants
            temp_agent = AgentModel(
                id=agent_id,
                workspace_id=workspace_id,
                name="RAG Search Agent",
                role="researcher",
                status="active"
            )
            
            specialist = SpecialistAgent(agent_data=temp_agent)
            
            if not specialist.has_document_access():
                logger.info("📚 No document access available for workspace")
                return {"documents_found": False, "results": []}
            
            all_results = []
            for query in search_queries:
                logger.info(f"🔍 Searching documents for: {query}")
                results = await specialist.search_workspace_documents(
                    query, 
                    max_results=max_results_per_query
                )
                
                for result in results:
                    result["search_query"] = query
                    all_results.append(result)
            
            # Deduplicate and rank results
            unique_results = self._deduplicate_and_rank_results(all_results)
            
            return {
                "documents_found": len(unique_results) > 0,
                "results": unique_results,
                "queries_used": search_queries
            }
            
        except Exception as e:
            logger.error(f"Error executing document search: {e}")
            return {"documents_found": False, "results": [], "error": str(e)}
    
    def _deduplicate_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """Deduplicate and rank search results by relevance"""
        
        # Group by document ID or content hash
        unique = {}
        for result in results:
            # Use content hash or ID as key
            key = result.get("document_id") or hash(str(result.get("content", "")))
            
            if key not in unique:
                unique[key] = result
            else:
                # Merge relevance scores if same document found multiple times
                existing = unique[key]
                existing["relevance_score"] = max(
                    existing.get("relevance_score", 0),
                    result.get("relevance_score", 0)
                )
        
        # Sort by relevance
        ranked = sorted(
            unique.values(),
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        return ranked[:10]  # Return top 10 most relevant

# Global instance
intelligent_rag_trigger = IntelligentRAGTrigger()