#!/usr/bin/env python3
"""
🤖 AI-DRIVEN Task Classification System

Semantic task type classification using AI to understand task intent and purpose.
Ensures proper task categorization for optimal agent assignment and content generation.

Respects the 14 Pillars:
- PILLAR 1: AI-Driven (no hardcoded rules)
- PILLAR 2: Domain Agnostic (works for any business domain)
- PILLAR 14: Real Tool Integration (uses actual AI capabilities)
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from models import TaskType

logger = logging.getLogger(__name__)

class AITaskClassifier:
    """🤖 **AI-Driven Task Classification Engine**
    
    Uses semantic AI analysis to classify tasks based on their true intent and purpose,
    replacing hardcoded keyword matching with intelligent understanding.
    """
    
    def __init__(self):
        self.classification_cache = {}  # Cache for performance
        
    async def classify_task(self, task_data: Dict[str, Any], goal_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        🎯 **CORE METHOD**: Classify a task using AI semantic analysis
        
        Args:
            task_data: Task information (name, description, etc.)
            goal_context: Optional goal context for better classification
            
        Returns:
            {
                "task_type": TaskType,
                "confidence": float,
                "reasoning": str,
                "agent_requirements": {...},
                "content_specifications": {...}
            }
        """
        try:
            task_name = task_data.get("name", "")
            task_description = task_data.get("description", "")
            goal_info = goal_context.get("description", "") if goal_context else ""
            
            # Check cache first
            cache_key = f"{task_name}:{task_description}:{goal_info}"
            if cache_key in self.classification_cache:
                logger.info(f"🔄 Using cached classification for task: {task_name}")
                return self.classification_cache[cache_key]
            
            logger.info(f"🔍 Classifying task: '{task_name}'")
            
            # Use AI to analyze and classify the task
            classification_result = await self._ai_classify_task(task_data, goal_context)
            
            # Cache the result
            self.classification_cache[cache_key] = classification_result
            
            return classification_result
            
        except Exception as e:
            logger.error(f"❌ Error classifying task: {e}")
            return self._fallback_classification(task_data)
    
    async def _ai_classify_task(self, task_data: Dict[str, Any], goal_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """🤖 AI-driven task classification using semantic analysis"""
        from services.ai_provider_abstraction import ai_provider_manager
        
        # 🤖 Task Classifier Agent Configuration
        TASK_CLASSIFIER_AGENT_CONFIG = {
            "name": "Task Classifier Agent",
            "role": "AI-driven task classification specialist",
            "capabilities": ["semantic_analysis", "task_categorization", "intent_recognition"]
        }
        
        try:
            task_name = task_data.get("name", "")
            task_description = task_data.get("description", "")
            goal_info = goal_context.get("description", "") if goal_context else ""
            goal_intent = goal_context.get("goal_intent_classification", "HYBRID") if goal_context else "HYBRID"
            
            classification_prompt = f"""Analyze this task and classify its TYPE based on semantic understanding of its purpose and deliverable.

TASK NAME: "{task_name}"
TASK DESCRIPTION: "{task_description}"
GOAL CONTEXT: "{goal_info}"
GOAL INTENT: {goal_intent}

**TASK TYPE DEFINITIONS:**
- CONTENT_CREATION: Writing actual content (emails with subject/body, documents, scripts, copy, articles, social posts)
- DATA_GATHERING: Collecting real information (contact lists, research data, market analysis, competitor info)
- STRATEGY_PLANNING: Strategic thinking (analysis, planning, roadmaps, decision frameworks)
- IMPLEMENTATION: Technical work (building, setup, coding, configuration, integration)
- QUALITY_ASSURANCE: Review and validation (testing, proofreading, fact-checking, approval)
- COORDINATION: Team/project management (communication, scheduling, handoffs, meetings)
- HYBRID: Tasks requiring multiple types

**CRITICAL EXAMPLES:**
- "Write Email 1: Welcome sequence" → CONTENT_CREATION (creates actual email content)
- "Create contact list for prospects" → DATA_GATHERING (collects real contact information)
- "Research best practices for email marketing" → DATA_GATHERING (collects information)
- "Develop content strategy framework" → STRATEGY_PLANNING (creates strategic approach)
- "Review and approve email content" → QUALITY_ASSURANCE (validates existing content)

**IMPORTANT**: Focus on the PRIMARY DELIVERABLE the task will create, not just keywords.

Return as JSON:
{{
  "task_type": "CONTENT_CREATION|DATA_GATHERING|STRATEGY_PLANNING|IMPLEMENTATION|QUALITY_ASSURANCE|COORDINATION|HYBRID",
  "confidence": 0.95,
  "reasoning": "Detailed explanation of why this classification was chosen",
  "primary_deliverable": "What the task will actually produce",
  "agent_requirements": {{
    "skills_needed": ["specific skills required"],
    "seniority_level": "junior|senior|expert",
    "domain_knowledge": "required domain expertise"
  }},
  "content_specifications": {{
    "output_format": "email|document|list|analysis|code|etc",
    "includes_actual_content": true,
    "content_count": 1,
    "quality_criteria": "specific quality requirements"
  }}
}}"""

            response_content = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=TASK_CLASSIFIER_AGENT_CONFIG,
                prompt=classification_prompt,
            )
            
            # Parse AI response
            if isinstance(response_content, str):
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    classification_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in AI response")
            elif isinstance(response_content, dict):
                classification_data = response_content
            else:
                raise TypeError(f"Unexpected response type from AI provider: {type(response_content)}")
            
            # Convert string task_type to enum
            task_type_str = classification_data.get("task_type", "HYBRID")
            try:
                task_type = TaskType(task_type_str.lower())
            except ValueError:
                logger.warning(f"⚠️ Unknown task type from AI: {task_type_str}, defaulting to HYBRID")
                task_type = TaskType.HYBRID
            
            result = {
                "task_type": task_type,
                "confidence": classification_data.get("confidence", 0.8),
                "reasoning": classification_data.get("reasoning", "AI classification"),
                "primary_deliverable": classification_data.get("primary_deliverable", "Unknown deliverable"),
                "agent_requirements": classification_data.get("agent_requirements", {}),
                "content_specifications": classification_data.get("content_specifications", {}),
                "classification_method": "ai",
                "classified_at": datetime.now().isoformat()
            }
            
            logger.info(f"🤖 AI task classification successful: {task_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI task classification failed: {e}")
            return self._fallback_classification(task_data)
    
    def _fallback_classification(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """🛡️ Fallback classification using pattern recognition"""
        task_name = task_data.get("name", "").lower()
        task_description = task_data.get("description", "").lower()
        combined_text = f"{task_name} {task_description}"
        
        # Pattern-based classification (fallback only)
        task_type = TaskType.HYBRID
        confidence = 0.6
        reasoning = "Fallback pattern-based classification"
        
        # Content creation patterns
        if any(pattern in combined_text for pattern in [
            "write", "create email", "draft", "compose", "content", "script", "copy", "post"
        ]):
            task_type = TaskType.CONTENT_CREATION
            reasoning = "Contains content creation keywords"
            
        # Data gathering patterns  
        elif any(pattern in combined_text for pattern in [
            "research", "find", "collect", "gather", "list", "contact", "data", "search"
        ]):
            task_type = TaskType.DATA_GATHERING
            reasoning = "Contains data gathering keywords"
            
        # Strategy planning patterns
        elif any(pattern in combined_text for pattern in [
            "plan", "strategy", "analyze", "framework", "roadmap", "approach"
        ]):
            task_type = TaskType.STRATEGY_PLANNING
            reasoning = "Contains strategy planning keywords"
            
        # Implementation patterns
        elif any(pattern in combined_text for pattern in [
            "build", "setup", "implement", "configure", "integrate", "develop"
        ]):
            task_type = TaskType.IMPLEMENTATION
            reasoning = "Contains implementation keywords"
            
        # Quality assurance patterns
        elif any(pattern in combined_text for pattern in [
            "review", "test", "validate", "check", "approve", "verify"
        ]):
            task_type = TaskType.QUALITY_ASSURANCE  
            reasoning = "Contains quality assurance keywords"
            
        # Coordination patterns
        elif any(pattern in combined_text for pattern in [
            "coordinate", "schedule", "meeting", "communicate", "handoff"
        ]):
            task_type = TaskType.COORDINATION
            reasoning = "Contains coordination keywords"
        
        return {
            "task_type": task_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "primary_deliverable": "Pattern-based inference",
            "agent_requirements": {
                "skills_needed": ["general"],
                "seniority_level": "senior",
                "domain_knowledge": "universal"
            },
            "content_specifications": {
                "output_format": "unknown",
                "includes_actual_content": task_type == TaskType.CONTENT_CREATION,
                "content_count": 1,
                "quality_criteria": "standard"
            },
            "classification_method": "fallback",
            "classified_at": datetime.now().isoformat()
        }
    
    async def classify_batch_tasks(self, tasks_data: List[Dict[str, Any]], goal_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        🚀 **BATCH PROCESSING**: Classify multiple tasks in parallel
        
        Returns list of classification results in the same order as input tasks.
        """
        try:
            logger.info(f"🔄 Batch classifying {len(tasks_data)} tasks")
            
            # Process tasks in parallel for performance
            classification_tasks = [
                self.classify_task(task_data, goal_context) 
                for task_data in tasks_data
            ]
            
            results = await asyncio.gather(*classification_tasks, return_exceptions=True)
            
            # Handle any exceptions in individual classifications
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Error classifying task {i}: {result}")
                    final_results.append(self._fallback_classification(tasks_data[i]))
                else:
                    final_results.append(result)
            
            logger.info(f"✅ Batch classification completed: {len(final_results)} tasks processed")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Error in batch task classification: {e}")
            return [self._fallback_classification(task_data) for task_data in tasks_data]

# Factory function for easy usage
def create_ai_task_classifier() -> AITaskClassifier:
    """Create a new AITaskClassifier instance"""
    return AITaskClassifier()

# Convenience function for single task classification
async def classify_task_ai(task_data: Dict[str, Any], goal_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    🎯 Convenience function: Classify a single task using AI
    
    Args:
        task_data: Task information (name, description, etc.)
        goal_context: Optional goal context for better classification
        
    Returns:
        Classification result with task_type, confidence, reasoning, etc.
    """
    classifier = create_ai_task_classifier()
    return await classifier.classify_task(task_data, goal_context)