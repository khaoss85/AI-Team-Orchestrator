"""
🤖 AI-Driven Deliverable-Achievement Mapper
Robust mapping between deliverables/task outputs and goal achievement tracking
"""

import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AchievementResult:
    """Result of achievement analysis"""
    items_created: int = 0
    data_processed: int = 0
    deliverables_completed: int = 0
    metrics_achieved: int = 0
    confidence_score: float = 0.0
    reasoning: str = ""
    extraction_method: str = "unknown"

class DeliverableAchievementMapper:
    """
    🤖 AI-DRIVEN: Robust deliverable-to-goal achievement mapping
    Pillar 5: Goal-Driven with automatic tracking
    Pillar 11: Concrete and actionable deliverables
    """
    
    def __init__(self):
        self.extraction_methods = [
            "ai_semantic_analysis",
            "pattern_recognition", 
            "structural_analysis",
            "task_name_inference"
        ]
        
        # Enhanced pattern libraries
        self.quantity_patterns = [
            # Numbers with context
            r'(\d+)\s*(?:contacts?|leads?|prospects?)',
            r'(\d+)\s*(?:emails?|messages?|campaigns?)',
            r'(\d+)\s*(?:items?|entries?|records?)',
            r'(\d+)\s*(?:sequences?|templates?|strategies?)',
            r'(\d+)\s*(?:reports?|analyses?|documents?)',
            r'(\d+)\s*(?:tasks?|steps?|actions?)',
            
            # Achievement patterns  
            r'compiled\s+(\d+)',
            r'created\s+(\d+)',
            r'generated\s+(\d+)',
            r'processed\s+(\d+)',
            r'completed\s+(\d+)',
            
            # List patterns
            r'list\s+of\s+(\d+)',
            r'total\s+of\s+(\d+)',
            r'(\d+)\s+total',
        ]
        
        # Deliverable type patterns
        self.deliverable_patterns = {
            'items_created': [
                r'contact.*list', r'lead.*database', r'prospect.*list',
                r'icp.*contacts?', r'target.*audience', r'customer.*list',
                r'email.*list', r'subscriber.*list', r'directory'
            ],
            'deliverables_completed': [
                r'email.*sequence', r'campaign.*strategy', r'marketing.*plan',
                r'business.*strategy', r'content.*plan', r'social.*strategy',
                r'report', r'analysis', r'document', r'template', r'framework'
            ],
            'data_processed': [
                r'data.*processed', r'records.*analyzed', r'entries.*reviewed',
                r'information.*compiled', r'research.*conducted'
            ],
            'metrics_achieved': [
                r'performance.*metric', r'kpi.*achieved', r'target.*met',
                r'goal.*completed', r'milestone.*reached', r'rate.*improved'
            ]
        }
        
        logger.info("🤖 DeliverableAchievementMapper initialized with robust extraction")
    
    async def extract_achievements_robust(self, task_result: Dict[str, Any], task_name: str) -> AchievementResult:
        """
        🤖 AI-DRIVEN: Robust multi-method achievement extraction
        """
        try:
            logger.info(f"🔍 ROBUST ACHIEVEMENT EXTRACTION from: '{task_name}'")
            
            # Method 1: AI Semantic Analysis (if available)
            ai_result = await self._extract_with_ai_semantic(task_result, task_name)
            if ai_result.confidence_score >= 0.6:
                logger.info(f"✅ AI semantic analysis succeeded (confidence: {ai_result.confidence_score:.2f})")
                return ai_result
            
            # Method 2: Enhanced Pattern Recognition
            pattern_result = await self._extract_with_enhanced_patterns(task_result, task_name)
            if pattern_result.confidence_score >= 0.5:
                logger.info(f"✅ Enhanced pattern recognition succeeded (confidence: {pattern_result.confidence_score:.2f})")
                return pattern_result
            
            # Method 3: Structural Analysis
            structural_result = await self._extract_with_structural_analysis(task_result, task_name)
            if structural_result.confidence_score >= 0.4:
                logger.info(f"✅ Structural analysis succeeded (confidence: {structural_result.confidence_score:.2f})")
                return structural_result
            
            # Method 4: Task Name Inference (fallback)
            inference_result = await self._extract_with_task_inference(task_name)
            logger.info(f"✅ Using task name inference fallback (confidence: {inference_result.confidence_score:.2f})")
            return inference_result
            
        except Exception as e:
            logger.error(f"Error in robust achievement extraction: {e}")
            return AchievementResult(
                reasoning=f"Extraction failed: {str(e)}",
                extraction_method="error_fallback"
            )
    
    async def _extract_with_ai_semantic(self, task_result: Dict[str, Any], task_name: str) -> AchievementResult:
        """AI semantic analysis with improved prompting"""
        try:
            # Try to use OpenAI directly with robust error handling
            try:
                import openai
                from openai import OpenAI
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("No OpenAI API key available")
                
                client = OpenAI(api_key=api_key)
                
                # Prepare data sample
                result_text = json.dumps(task_result, default=str)[:1500]
                
                # Enhanced prompt with specific examples
                prompt = f"""Analyze this task completion to identify measurable achievements. Be precise and conservative.

TASK: {task_name}

RESULT DATA:
{result_text}

Look for these specific achievement types:

1. ITEMS_CREATED: 
   - Contact lists (count the contacts: "500 ICP contacts" = 500)
   - Lead databases, prospect lists, customer directories
   - Email templates, content pieces
   
2. DELIVERABLES_COMPLETED:
   - Email sequences, marketing campaigns, strategies
   - Reports, analyses, business plans
   - Complete documents or frameworks
   
3. DATA_PROCESSED:
   - Records processed, data points analyzed
   - Research entries compiled
   
4. METRICS_ACHIEVED:
   - Performance improvements, targets met
   - Quality scores, completion rates

EXAMPLES:
- "Compiled list of 500 ICP contacts" → items_created: 500, deliverables_completed: 1
- "Created 7-email sequence" → items_created: 7, deliverables_completed: 1  
- "Analyzed 250 customer records" → data_processed: 250, deliverables_completed: 1

IMPORTANT RULES:
- Most completed tasks should have deliverables_completed >= 1 (the task output itself)
- Items created = count of individual items (contacts, emails, records, etc.)
- Data processed = count of records/entries analyzed  
- Always count the main deliverable as deliverables_completed: 1

Extract ONLY clear, quantifiable achievements. Look for numbers!

Respond in JSON:
{{
    "items_created": <number>,
    "data_processed": <number>,
    "deliverables_completed": <number>, 
    "metrics_achieved": <number>,
    "confidence_score": <0.0-1.0>,
    "reasoning": "What specific achievements were found"
}}"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                logger.info(f"AI Achievement Extraction Prompt: {prompt}")
                logger.info(f"AI Achievement Extraction Raw Content: {content}")
                if content:
                    result_data = json.loads(content)
                    logger.info(f"AI Achievement Extraction Parsed Data: {result_data}")
                    
                    return AchievementResult(
                        items_created=int(result_data.get("items_created", 0)),
                        data_processed=int(result_data.get("data_processed", 0)),
                        deliverables_completed=int(result_data.get("deliverables_completed", 0)),
                        metrics_achieved=int(result_data.get("metrics_achieved", 0)),
                        confidence_score=float(result_data.get("confidence_score", 0.0)),
                        reasoning=result_data.get("reasoning", "AI analysis completed"),
                        extraction_method="ai_semantic_analysis"
                    )
                
            except Exception as ai_error:
                logger.debug(f"Direct OpenAI call failed: {ai_error}")
                
                # Fallback to existing AI quality validator
                try:
                    from backend.ai_quality_assurance.unified_quality_engine import AIQualityValidator
                    quality_validator = AIQualityValidator()
                    
                    if quality_validator.openai_available:
                        # Use existing validator but with our enhanced prompt
                        ai_result = await quality_validator._call_openai_api(prompt, "achievement_analysis")
                        
                        if ai_result and "raw_response" in ai_result:
                            response = ai_result["raw_response"]
                            confidence = response.get("confidence_score", 0.0)
                            
                            return AchievementResult(
                                items_created=int(response.get("items_created", 0)),
                                data_processed=int(response.get("data_processed", 0)),
                                deliverables_completed=int(response.get("deliverables_completed", 0)),
                                metrics_achieved=int(response.get("metrics_achieved", 0)),
                                confidence_score=confidence,
                                reasoning=response.get("reasoning", "AI validator analysis"),
                                extraction_method="ai_quality_validator"
                            )
                except Exception as validator_error:
                    logger.debug(f"AI quality validator failed: {validator_error}")
            
            # AI not available or failed
            return AchievementResult(
                confidence_score=0.0,
                reasoning="AI analysis not available",
                extraction_method="ai_failed"
            )
            
        except Exception as e:
            logger.debug(f"AI semantic analysis error: {e}")
            return AchievementResult(
                confidence_score=0.0,
                reasoning=f"AI error: {str(e)}",
                extraction_method="ai_error"
            )
    
    async def _extract_with_enhanced_patterns(self, task_result: Dict[str, Any], task_name: str) -> AchievementResult:
        """Enhanced pattern recognition with domain-specific intelligence"""
        try:
            # Convert all data to searchable text
            search_text = f"{task_name} {json.dumps(task_result, default=str)}".lower()
            
            achievements = AchievementResult(extraction_method="enhanced_patterns")
            total_confidence = 0.0
            matches_found = 0
            
            # Extract quantities using enhanced patterns
            all_quantities = []
            for pattern in self.quantity_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    try:
                        quantity = int(match)
                        if 1 <= quantity <= 10000:  # Reasonable range
                            all_quantities.append(quantity)
                            matches_found += 1
                    except ValueError:
                        continue
            
            # Classify achievements by content patterns
            for category, patterns in self.deliverable_patterns.items():
                category_score = 0
                for pattern in patterns:
                    if re.search(pattern, search_text, re.IGNORECASE):
                        category_score += 1
                
                if category_score > 0:
                    # Assign largest quantity to strongest category match
                    if all_quantities:
                        max_quantity = max(all_quantities)
                        if category == 'items_created' and any(p in search_text for p in ['contact', 'lead', 'prospect', 'icp']):
                            achievements.items_created = max_quantity
                            total_confidence += 0.7
                        elif category == 'deliverables_completed' and any(p in search_text for p in ['sequence', 'strategy', 'campaign', 'plan']):
                            achievements.deliverables_completed = max(1, len([q for q in all_quantities if q <= 20]))  # Reasonable for deliverables
                            total_confidence += 0.6
                        elif category == 'data_processed':
                            achievements.data_processed = max_quantity
                            total_confidence += 0.5
                        elif category == 'metrics_achieved':
                            achievements.metrics_achieved = min(max_quantity, 10)  # Cap metrics
                            total_confidence += 0.4
            
            # Ensure at least one deliverable for any task with meaningful output
            if not achievements.deliverables_completed and (achievements.items_created > 0 or achievements.data_processed > 0 or all_quantities):
                achievements.deliverables_completed = 1
                total_confidence += 0.3
                
            # Default heuristics if no specific patterns found
            if not achievements.items_created and not achievements.deliverables_completed and all_quantities:
                largest_qty = max(all_quantities)
                
                # Heuristic classification based on size and context
                if largest_qty > 50 and any(keyword in search_text for keyword in ['contact', 'lead', 'list', 'database']):
                    achievements.items_created = largest_qty
                    achievements.deliverables_completed = 1  # Always count the list as a deliverable
                    total_confidence += 0.5
                elif largest_qty <= 20 and any(keyword in search_text for keyword in ['sequence', 'strategy', 'campaign', 'email']):
                    achievements.items_created = largest_qty  # Count individual items
                    achievements.deliverables_completed = 1  # Count the sequence/strategy as one deliverable
                    total_confidence += 0.4
                else:
                    achievements.items_created = largest_qty
                    achievements.deliverables_completed = 1  # Default to one deliverable
                    total_confidence += 0.3
            
            # Calculate final confidence
            achievements.confidence_score = min(total_confidence / max(matches_found, 1), 1.0)
            achievements.reasoning = f"Found {matches_found} pattern matches, quantities: {all_quantities}"
            
            logger.debug(f"Pattern extraction: {achievements.items_created} items, {achievements.deliverables_completed} deliverables, confidence: {achievements.confidence_score:.2f}")
            
            return achievements
            
        except Exception as e:
            logger.warning(f"Enhanced pattern extraction error: {e}")
            return AchievementResult(
                confidence_score=0.0,
                reasoning=f"Pattern error: {str(e)}",
                extraction_method="pattern_error"
            )
    
    async def _extract_with_structural_analysis(self, task_result: Dict[str, Any], task_name: str) -> AchievementResult:
        """Structural analysis of result data"""
        try:
            achievements = AchievementResult(extraction_method="structural_analysis")
            
            if not task_result:
                return achievements
            
            # Analyze structure
            if isinstance(task_result, dict):
                # Count meaningful keys/values
                meaningful_keys = 0
                list_items = 0
                
                for key, value in task_result.items():
                    if isinstance(value, (list, tuple)):
                        list_length = len(value)
                        if list_length > 0:
                            list_items += list_length
                            meaningful_keys += 1
                    elif isinstance(value, str) and len(value) > 50:  # Substantial content
                        meaningful_keys += 1
                    elif isinstance(value, (int, float)) and value > 0:
                        meaningful_keys += 1
                
                # Heuristic assignment
                if list_items > 10:
                    achievements.items_created = list_items
                    achievements.confidence_score = 0.6
                elif meaningful_keys > 3:
                    achievements.deliverables_completed = 1
                    achievements.confidence_score = 0.4
                
                achievements.reasoning = f"Structural: {meaningful_keys} keys, {list_items} list items"
            
            return achievements
            
        except Exception as e:
            logger.warning(f"Structural analysis error: {e}")
            return AchievementResult(
                confidence_score=0.0,
                reasoning=f"Structural error: {str(e)}",
                extraction_method="structural_error"
            )
    
    async def _extract_with_task_inference(self, task_name: str) -> AchievementResult:
        """Inference from task name as final fallback"""
        try:
            task_lower = task_name.lower()
            achievements = AchievementResult(extraction_method="task_inference")
            
            # Extract numbers from task name
            numbers = re.findall(r'\d+', task_name)
            largest_number = max([int(n) for n in numbers], default=0)
            
            # Classify based on task type
            if any(keyword in task_lower for keyword in ['contact', 'lead', 'prospect', 'icp', 'customer']):
                achievements.items_created = largest_number if largest_number > 0 else 1
                achievements.confidence_score = 0.7 if largest_number > 0 else 0.3
                achievements.reasoning = f"Inferred contact/lead task: {largest_number or 'unspecified'} items"
                
            elif any(keyword in task_lower for keyword in ['sequence', 'strategy', 'campaign', 'plan', 'email']):
                achievements.deliverables_completed = 1
                achievements.confidence_score = 0.5
                achievements.reasoning = "Inferred deliverable creation task"
                
            elif any(keyword in task_lower for keyword in ['compile', 'list', 'create', 'generate']):
                achievements.items_created = largest_number if largest_number > 0 else 1
                achievements.confidence_score = 0.4
                achievements.reasoning = "Inferred creation task"
                
            else:
                # Generic task completion
                achievements.deliverables_completed = 1
                achievements.confidence_score = 0.2
                achievements.reasoning = "Generic task completion inference"
            
            return achievements
            
        except Exception as e:
            logger.warning(f"Task inference error: {e}")
            return AchievementResult(
                deliverables_completed=1,
                confidence_score=0.1,
                reasoning=f"Fallback: task completion assumed",
                extraction_method="fallback"
            )
    
    async def map_achievements_to_goals(self, workspace_id: str, achievements: AchievementResult) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN: Map extracted achievements to workspace goals
        """
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Get workspace goals
            goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
            goals = goals_response.data or []
            
            if not goals:
                logger.warning(f"No goals found for workspace {workspace_id}")
                return []
            
            updates = []
            
            for goal in goals:
                goal_id = goal['id']
                metric_type = goal.get('metric_type', '').lower()
                current_value = goal.get('current_value', 0)
                target_value = goal.get('target_value', 1)
                
                # Map achievements to goal metrics
                increment = 0
                
                if metric_type in ['contacts', 'leads', 'prospects', 'customers', 'items']:
                    increment = achievements.items_created
                elif metric_type in ['deliverables', 'sequences', 'campaigns', 'strategies', 'documents']:
                    increment = achievements.deliverables_completed
                elif metric_type in ['data', 'records', 'entries', 'processed']:
                    increment = achievements.data_processed
                elif metric_type in ['metrics', 'kpis', 'targets', 'goals']:
                    increment = achievements.metrics_achieved
                else:
                    # Fallback: any achievement counts toward generic goals
                    increment = max(achievements.items_created, achievements.deliverables_completed, achievements.data_processed, achievements.metrics_achieved)
                
                if increment > 0:
                    new_value = min(current_value + increment, target_value)
                    
                    if new_value > current_value:
                        updates.append({
                            'goal_id': goal_id,
                            'old_value': current_value,
                            'new_value': new_value,
                            'increment': increment,
                            'metric_type': metric_type,
                            'achievement_source': achievements.extraction_method
                        })
                        
                        # Update in database
                        supabase.table('workspace_goals').update({
                            'current_value': new_value,
                            'updated_at': 'now()'
                        }).eq('id', goal_id).execute()
                        
                        logger.info(f"✅ Goal updated: {metric_type} {current_value}→{new_value} (+{increment}) via {achievements.extraction_method}")
            
            return updates
            
        except Exception as e:
            logger.error(f"Error mapping achievements to goals: {e}")
            return []

# Global instance
deliverable_achievement_mapper = DeliverableAchievementMapper()

# Export for easy import
__all__ = ["DeliverableAchievementMapper", "deliverable_achievement_mapper", "AchievementResult"]