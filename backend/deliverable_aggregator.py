# backend/deliverable_aggregator.py - ENHANCED HYBRID VERSION
# Combina AI Quality Assurance + Dynamic AI Analysis - Zero Hard-coded Dependencies

import logging
import json
import re
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from database import (
    get_workspace, list_tasks, list_agents, create_task,
    update_workspace_status
)
from models import TaskStatus, ProjectPhase
from deliverable_system.requirements_analyzer import DeliverableRequirementsAnalyzer
from deliverable_system.schema_generator import AssetSchemaGenerator
from models import ExtractedAsset, ActionableDeliverable, AssetSchema

# ENHANCED: AI Quality Assurance Integration with graceful fallback
AI_QUALITY_ASSURANCE_AVAILABLE = False
try:
    from ai_quality_assurance.enhancement_orchestrator import AssetEnhancementOrchestrator
    from ai_quality_assurance.quality_validator import AIQualityValidator
    AI_QUALITY_ASSURANCE_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ AI Quality Assurance modules imported successfully")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ AI Quality Assurance not available: {e}")
    AI_QUALITY_ASSURANCE_AVAILABLE = False

# Enhanced configuration from environment
DELIVERABLE_READINESS_THRESHOLD = int(os.getenv("DELIVERABLE_READINESS_THRESHOLD", "50"))
ENABLE_AUTO_PROJECT_COMPLETION = os.getenv("ENABLE_AUTO_PROJECT_COMPLETION", "true").lower() == "true"
MIN_COMPLETED_TASKS_FOR_DELIVERABLE = int(os.getenv("MIN_COMPLETED_TASKS_FOR_DELIVERABLE", "2"))
ENABLE_ENHANCED_DELIVERABLE_LOGIC = os.getenv("ENABLE_ENHANCED_DELIVERABLE_LOGIC", "true").lower() == "true"
ENABLE_AI_QUALITY_ASSURANCE = os.getenv("ENABLE_AI_QUALITY_ASSURANCE", "true").lower() == "true" and AI_QUALITY_ASSURANCE_AVAILABLE
ENABLE_DYNAMIC_AI_ANALYSIS = os.getenv("ENABLE_DYNAMIC_AI_ANALYSIS", "true").lower() == "true"

def is_quality_assurance_available():
    """Controllo sicuro per la disponibilità del sistema di quality assurance"""
    global AI_QUALITY_ASSURANCE_AVAILABLE
    try:
        return (AI_QUALITY_ASSURANCE_AVAILABLE and 
                ENABLE_AI_QUALITY_ASSURANCE and
                'AssetEnhancementOrchestrator' in globals() and
                'AIQualityValidator' in globals())
    except NameError:
        return False


# === DYNAMIC AI ANALYSIS SYSTEM ===

class AIDeliverableAnalyzer:
    """
    Analizzatore AI-driven per determinare dinamicamente il tipo di deliverable 
    e le strategie di aggregazione senza mappature hard-coded
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.ai_client = self._initialize_ai_client()
        logger.info(f"🤖 AI Deliverable Analyzer: {'✅ Active' if self.ai_client else '❌ Fallback mode'}")
    
    def _initialize_ai_client(self):
        """Inizializza client AI con fallback sicuro"""
        try:
            if not ENABLE_DYNAMIC_AI_ANALYSIS:
                return None
                
            import openai
            from openai import AsyncOpenAI
            if os.getenv("OPENAI_API_KEY"):
                return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except ImportError:
            logger.warning("OpenAI not available for dynamic AI analysis")
        return None
    
    async def analyze_project_deliverable_type(self, workspace_goal: str, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Analizza dinamicamente il tipo di deliverable utilizzando AI
        """
        
        cache_key = f"{hash(workspace_goal)}_{len(completed_tasks)}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # Estrai contesto dai task completati
        task_context = self._extract_task_context(completed_tasks)
        
        analysis_result = None
        
        # Tentativo AI-driven analysis
        if self.ai_client:
            try:
                analysis_result = await self._ai_analyze_deliverable_type(workspace_goal, task_context)
                logger.info(f"🤖 AI ANALYSIS: {analysis_result.get('deliverable_type')} (confidence: {analysis_result.get('confidence_score', 0):.2f})")
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}, using fallback")
        
        # Fallback a analisi rule-based dinamica
        if not analysis_result:
            analysis_result = self._fallback_analyze_deliverable_type(workspace_goal, task_context)
            logger.info(f"🔄 FALLBACK ANALYSIS: {analysis_result.get('deliverable_type')}")
        
        self.analysis_cache[cache_key] = analysis_result
        return analysis_result
    
    async def _ai_analyze_deliverable_type(self, workspace_goal: str, task_context: Dict) -> Dict[str, Any]:
        """Analisi AI per determinare tipo deliverable e strategia"""
        
        prompt = f"""Analyze this business project to determine the optimal deliverable structure and aggregation strategy.

PROJECT GOAL: {workspace_goal}

COMPLETED WORK CONTEXT:
- Total tasks completed: {task_context.get('total_tasks', 0)}
- Task types: {', '.join(task_context.get('task_types', [])[:5])}
- Key outputs: {', '.join(task_context.get('key_outputs', [])[:3])}
- Data richness: {task_context.get('data_richness_score', 0)}/10

Based on this project, determine:
1. The most appropriate deliverable format and structure
2. Key asset types that should be extracted and highlighted
3. Presentation approach that maximizes business value
4. Implementation readiness and business impact focus

Respond in this exact JSON format:
{{
    "deliverable_type": "primary_deliverable_category",
    "deliverable_description": "Clear description of what this deliverable should be",
    "key_asset_types": ["asset_type_1", "asset_type_2", "asset_type_3"],
    "presentation_format": "recommended_format_for_client_presentation",
    "business_value_focus": "primary_business_value_this_delivers",
    "implementation_priority": "immediate|short_term|strategic",
    "aggregation_strategy": "how_to_combine_and_present_the_work_done",
    "success_metrics": ["metric1", "metric2", "metric3"],
    "confidence_score": 0.85
}}"""

        response = await self.ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _fallback_analyze_deliverable_type(self, workspace_goal: str, task_context: Dict) -> Dict[str, Any]:
        """Analisi fallback rule-based dinamica"""
        
        goal_lower = workspace_goal.lower()
        task_types = task_context.get('task_types', [])
        key_outputs = task_context.get('key_outputs', [])
        
        # Analisi dinamica delle keyword nei contenuti
        all_content = f"{workspace_goal} {' '.join(task_types)} {' '.join(key_outputs)}".lower()
        
        # Pattern detection dinamico e ampliato
        business_patterns = {
            'data_focused': ['contact', 'lead', 'database', 'list', 'email', 'phone', 'crm', 'prospect'],
            'strategy_focused': ['strategy', 'plan', 'framework', 'approach', 'method', 'roadmap', 'vision'],
            'content_focused': ['content', 'social', 'marketing', 'campaign', 'creative', 'post', 'media'],
            'analysis_focused': ['analysis', 'research', 'insight', 'study', 'competitive', 'market', 'data'],
            'implementation_focused': ['implementation', 'execution', 'action', 'workflow', 'process', 'deploy'],
            'financial_focused': ['budget', 'financial', 'cost', 'revenue', 'profit', 'investment', 'funding'],
            'training_focused': ['training', 'education', 'learning', 'skill', 'development', 'course'],
            'operational_focused': ['operation', 'management', 'admin', 'system', 'infrastructure']
        }
        
        # Calcola score per ogni pattern con pesi
        pattern_scores = {}
        for pattern_type, keywords in business_patterns.items():
            score = 0
            for keyword in keywords:
                # Score base per presenza
                if keyword in all_content:
                    score += 1
                
                # Bonus per presenza nel goal (più importante)
                if keyword in goal_lower:
                    score += 2
                
                # Bonus per frequenza
                score += all_content.count(keyword) * 0.5
            
            pattern_scores[pattern_type] = score
        
        # Determina il pattern dominante
        dominant_pattern = max(pattern_scores, key=pattern_scores.get) if pattern_scores else 'analysis_focused'
        max_score = pattern_scores.get(dominant_pattern, 0)
        
        # Calcola confidence score
        total_score = sum(pattern_scores.values())
        confidence = min(max_score / max(total_score, 1) * 1.5, 1.0) if total_score > 0 else 0.5
        
        # Genera deliverable config dinamicamente
        deliverable_configs = {
            'data_focused': {
                'type': 'actionable_database_package',
                'description': 'Actionable database with contacts, leads, and implementation-ready data assets',
                'assets': ['contact_database', 'qualified_leads', 'outreach_templates', 'crm_integration_guide'],
                'format': 'structured_data_package',
                'value': 'immediate lead generation and sales pipeline development',
                'priority': 'immediate'
            },
            'strategy_focused': {
                'type': 'strategic_framework_suite',
                'description': 'Strategic framework with actionable recommendations and implementation roadmap',
                'assets': ['strategy_framework', 'action_plans', 'success_metrics', 'implementation_timeline'],
                'format': 'strategic_document_package',
                'value': 'strategic decision making and long-term business direction',
                'priority': 'strategic'
            },
            'content_focused': {
                'type': 'content_strategy_package',
                'description': 'Complete content strategy with calendar, templates, and execution guidelines',
                'assets': ['content_calendar', 'content_templates', 'social_strategy', 'brand_guidelines'],
                'format': 'creative_execution_package',
                'value': 'marketing campaign execution and brand visibility',
                'priority': 'immediate'
            },
            'analysis_focused': {
                'type': 'research_insights_report',
                'description': 'Comprehensive research report with insights, data, and strategic recommendations',
                'assets': ['research_findings', 'competitive_analysis', 'market_insights', 'trend_analysis'],
                'format': 'analytical_intelligence_report',
                'value': 'data-driven decision making and market intelligence',
                'priority': 'short_term'
            },
            'implementation_focused': {
                'type': 'implementation_blueprint',
                'description': 'Implementation-ready blueprint with workflows, processes, and execution guides',
                'assets': ['workflow_templates', 'process_guides', 'implementation_roadmap', 'training_materials'],
                'format': 'operational_execution_package',
                'value': 'operational efficiency and process optimization',
                'priority': 'immediate'
            },
            'financial_focused': {
                'type': 'financial_strategy_package',
                'description': 'Financial planning suite with budgets, forecasts, and investment strategies',
                'assets': ['financial_model', 'budget_templates', 'investment_analysis', 'cost_optimization'],
                'format': 'financial_planning_suite',
                'value': 'financial planning and resource optimization',
                'priority': 'strategic'
            },
            'training_focused': {
                'type': 'training_program_suite',
                'description': 'Complete training program with materials, schedules, and assessment tools',
                'assets': ['training_curriculum', 'learning_materials', 'assessment_tools', 'progress_tracking'],
                'format': 'educational_program_package',
                'value': 'skill development and performance improvement',
                'priority': 'short_term'
            },
            'operational_focused': {
                'type': 'operational_management_system',
                'description': 'Operational management system with processes, tools, and performance metrics',
                'assets': ['management_framework', 'operational_procedures', 'performance_metrics', 'monitoring_tools'],
                'format': 'management_system_package',
                'value': 'operational excellence and management efficiency',
                'priority': 'short_term'
            }
        }
        
        config = deliverable_configs.get(dominant_pattern, deliverable_configs['analysis_focused'])
        
        return {
            'deliverable_type': config['type'],
            'deliverable_description': config['description'],
            'key_asset_types': config['assets'],
            'presentation_format': config['format'],
            'business_value_focus': config['value'],
            'implementation_priority': config['priority'],
            'aggregation_strategy': f"Combine all work into {config['format']} highlighting {dominant_pattern.replace('_', ' ')} capabilities",
            'success_metrics': ['client_satisfaction', 'implementation_success', 'business_impact', 'roi_achievement'],
            'pattern_analysis': pattern_scores,
            'confidence_score': confidence,
            'dominant_pattern': dominant_pattern,
            'analysis_method': 'rule_based_dynamic'
        }
    
    def _extract_task_context(self, completed_tasks: List[Dict]) -> Dict[str, Any]:
        """Estrae contesto dinamicamente dai task completati"""
        
        task_types = []
        key_outputs = []
        data_richness_indicators = 0
        
        for task in completed_tasks:
            # Estrai tipo task
            task_name = task.get('name', '').lower()
            task_types.append(task_name)
            
            # Estrai output chiave
            result = task.get('result', {}) or {}
            summary = result.get('summary', '')
            if summary and len(summary) > 20:
                # Estrai prime frasi significative
                sentences = summary.split('.')[:2]
                key_outputs.extend([s.strip() for s in sentences if len(s.strip()) > 10])
            
            # Calcola data richness
            detailed_json = result.get('detailed_results_json', '')
            if detailed_json:
                try:
                    data = json.loads(detailed_json)
                    if isinstance(data, dict):
                        if len(data) > 5:
                            data_richness_indicators += 3
                        elif len(data) > 2:
                            data_richness_indicators += 2
                        else:
                            data_richness_indicators += 1
                except:
                    # Anche se non è JSON valido, ha tentato di strutturare
                    data_richness_indicators += 1
        
        return {
            'total_tasks': len(completed_tasks),
            'task_types': task_types,
            'key_outputs': key_outputs,
            'data_richness_score': min(data_richness_indicators, 10)
        }


class DynamicAssetExtractor:
    """
    Estrattore dinamico di asset che si adatta al tipo di progetto
    """
    
    def __init__(self):
        self.ai_analyzer = AIDeliverableAnalyzer()
    
    async def extract_assets_dynamically(
        self, 
        completed_tasks: List[Dict], 
        deliverable_analysis: Dict[str, Any],
        existing_schemas: Optional[Dict[str, AssetSchema]] = None
    ) -> Dict[str, Any]:
        """
        Estrae asset dinamicamente basandosi sull'analisi del deliverable
        """
        
        extracted_assets = {}
        target_asset_types = deliverable_analysis.get('key_asset_types', [])
        
        logger.info(f"🔍 DYNAMIC EXTRACTION: Targeting {len(target_asset_types)} asset types")
        
        for task in completed_tasks:
            try:
                # Determina se questo task ha prodotto asset azionabili
                asset_data = await self._extract_asset_from_task(task, target_asset_types, deliverable_analysis)
                
                if asset_data:
                    asset_id = f"asset_{task.get('id', '')}"
                    
                    # Se abbiamo schema esistenti, prova validazione
                    if existing_schemas and asset_data.get('asset_type') in existing_schemas:
                        schema = existing_schemas[asset_data['asset_type']]
                        asset_data = await self._enhance_with_schema_validation(asset_data, schema)
                    
                    extracted_assets[asset_id] = asset_data
                    logger.info(f"✅ EXTRACTED: {asset_data.get('asset_type', 'generic')} from task {task.get('id', '')}")
                    
            except Exception as e:
                logger.warning(f"Error extracting from task {task.get('id', '')}: {e}")
                continue
        
        logger.info(f"🔍 EXTRACTION COMPLETE: {len(extracted_assets)} assets extracted")
        return extracted_assets
    
    async def _extract_asset_from_task(self, task: Dict, target_asset_types: List[str], deliverable_analysis: Dict) -> Optional[Dict[str, Any]]:
        """Estrae asset da un singolo task con AI enhancement"""
        
        result = task.get('result', {}) or {}
        detailed_json = result.get('detailed_results_json', '')
        summary = result.get('summary', '')
        
        # Prova estrazione da JSON strutturato
        if detailed_json:
            try:
                data = json.loads(detailed_json)
                if isinstance(data, dict) and len(data) >= 2:  # Soglia più permissiva
                    asset_type = await self._determine_asset_type_ai(data, target_asset_types, task.get('name', ''), deliverable_analysis)
                    
                    return {
                        'asset_type': asset_type,
                        'asset_data': data,
                        'source_task_id': task.get('id', ''),
                        'extraction_method': 'structured_json',
                        'quality_score': self._calculate_quality_score(data),
                        'actionability_score': self._calculate_actionability_score(data),
                        'ready_to_use': self._is_ready_to_use(data),
                        'task_context': {
                            'task_name': task.get('name', ''),
                            'task_summary': summary[:200] if summary else '',
                            'creation_context': task.get('context_data', {})
                        },
                        'enhancement_potential': self._assess_enhancement_potential(data)
                    }
            except json.JSONDecodeError:
                pass
        
        # Fallback: estrazione da summary se contiene dati strutturati
        if summary and len(summary) > 50:  # Soglia più permissiva
            structured_data = self._extract_structured_data_from_text(summary)
            if structured_data:
                asset_type = await self._determine_asset_type_ai(structured_data, target_asset_types, task.get('name', ''), deliverable_analysis)
                
                return {
                    'asset_type': asset_type,
                    'asset_data': structured_data,
                    'source_task_id': task.get('id', ''),
                    'extraction_method': 'text_extraction',
                    'quality_score': 0.5,  # Lower score for text extraction
                    'actionability_score': 0.4,
                    'ready_to_use': False,
                    'task_context': {
                        'task_name': task.get('name', ''),
                        'task_summary': summary[:200]
                    },
                    'enhancement_potential': 0.8  # High potential for text-extracted data
                }
        
        return None
    
    async def _determine_asset_type_ai(self, data: Dict, target_types: List[str], task_name: str, deliverable_analysis: Dict) -> str:
        """Determina il tipo di asset usando AI con context awareness"""
        
        # Se abbiamo AI disponibile, usala con context del deliverable
        if self.ai_analyzer.ai_client:
            try:
                data_sample = json.dumps(data, default=str)[:500]
                business_focus = deliverable_analysis.get('business_value_focus', '')
                deliverable_type = deliverable_analysis.get('deliverable_type', '')
                
                prompt = f"""Analyze this data to determine the most appropriate asset type for a {deliverable_type} focused on {business_focus}.

TASK NAME: {task_name}
SUGGESTED ASSET TYPES: {', '.join(target_types)}
DELIVERABLE CONTEXT: {deliverable_type} - {business_focus}
DATA SAMPLE: {data_sample}

Based on the data structure, content, and business context, determine the most specific and actionable asset type.
Choose from the suggested types if they fit, or propose a better alternative that aligns with the deliverable focus.

Respond with just the asset type name (e.g., "contact_database", "content_calendar", "strategic_framework").
Make it specific to the business context and actionable for immediate use."""

                response = await self.ai_analyzer.ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=50
                )
                
                ai_type = response.choices[0].message.content.strip().lower().replace(' ', '_')
                if ai_type and len(ai_type) < 50:  # Sanity check
                    return ai_type
                    
            except Exception as e:
                logger.debug(f"AI asset type determination failed: {e}")
        
        # Fallback rule-based migliorato
        return self._determine_asset_type_fallback(data, target_types, task_name, deliverable_analysis)
    
    def _determine_asset_type_fallback(self, data: Dict, target_types: List[str], task_name: str, deliverable_analysis: Dict) -> str:
        """Fallback rule-based avanzato per determinare asset type"""
        
        data_str = json.dumps(data, default=str).lower()
        task_name_lower = task_name.lower()
        business_focus = deliverable_analysis.get('business_value_focus', '').lower()
        
        # Pattern dinamici espansi e context-aware
        content_patterns = {
            'contact_database': ['email', 'phone', 'company', 'name', 'contact', 'lead', 'prospect'],
            'content_calendar': ['post', 'caption', 'hashtag', 'content', 'social', 'schedule', 'publish'],
            'strategy_framework': ['strategy', 'plan', 'framework', 'approach', 'objective', 'goal'],
            'competitive_analysis': ['competitor', 'analysis', 'comparison', 'market', 'rival'],
            'financial_model': ['budget', 'cost', 'revenue', 'financial', 'profit', 'investment'],
            'training_program': ['training', 'course', 'education', 'skill', 'learning', 'development'],
            'workflow_template': ['step', 'process', 'workflow', 'procedure', 'guideline', 'protocol'],
            'research_report': ['research', 'study', 'finding', 'insight', 'data', 'analysis'],
            'implementation_guide': ['implementation', 'deploy', 'execute', 'action', 'instruction'],
            'performance_metrics': ['metric', 'kpi', 'measurement', 'tracking', 'performance']
        }
        
        # Calcola score per ogni pattern con context awareness
        pattern_scores = {}
        for pattern_name, keywords in content_patterns.items():
            score = 0
            
            for keyword in keywords:
                # Score base per presenza nei dati
                if keyword in data_str:
                    score += 2
                
                # Score per presenza nel task name
                if keyword in task_name_lower:
                    score += 3
                
                # Score per allineamento con business focus
                if keyword in business_focus:
                    score += 4
                
                # Score per target types
                if any(keyword in target_type for target_type in target_types):
                    score += 5
            
            pattern_scores[pattern_name] = score
        
        # Trova il pattern dominante
        if pattern_scores:
            best_match = max(pattern_scores, key=pattern_scores.get)
            if pattern_scores[best_match] > 2:  # Soglia minima
                return best_match
        
        # Fallback basato su business focus
        focus_mapping = {
            'lead generation': 'contact_database',
            'content': 'content_calendar',
            'strategy': 'strategy_framework',
            'analysis': 'research_report',
            'training': 'training_program',
            'financial': 'financial_model',
            'implementation': 'implementation_guide'
        }
        
        for focus_keyword, asset_type in focus_mapping.items():
            if focus_keyword in business_focus:
                return asset_type
        
        # Default generico ma specifico
        return "business_asset"
    
    def _extract_structured_data_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Estrae dati strutturati da testo con AI enhancement"""
        
        structured_data = {}
        
        # Pattern extraction migliorati
        patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'urls': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'phones': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'percentages': r'\b\d+(?:\.\d+)?%',
            'money_values': r'[$€£¥]\s?\d+(?:,\d{3})*(?:\.\d{2})?',
            'dates': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'numbers': r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                structured_data[key] = matches
        
        # Estrai liste strutturate
        list_patterns = [
            r'(?:^|\n)\s*[\-\*\•]\s*(.+)',  # Bullet points
            r'(?:^|\n)\s*\d+[\.\)]\s*(.+)',  # Numbered lists
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches and len(matches) >= 2:
                structured_data['extracted_list_items'] = matches
                break
        
        # Estrai key-value pairs
        kv_pattern = r'([A-Za-z\s]+):\s*([^\n]+)'
        kv_matches = re.findall(kv_pattern, text)
        if kv_matches:
            structured_data['key_value_pairs'] = {k.strip(): v.strip() for k, v in kv_matches}
        
        # Se abbiamo estratto dati, aggiungi metadati
        if structured_data:
            structured_data['original_text_sample'] = text[:300]
            structured_data['extraction_confidence'] = len(structured_data) / 10  # Normalized confidence
            return structured_data
        
        return None
    
    def _calculate_quality_score(self, data: Dict) -> float:
        """Calcola quality score dinamicamente e intelligentemente"""
        
        score = 0.3  # Base score più permissivo
        
        # Bonus per completezza strutturale
        field_count = len(data)
        if field_count >= 7:
            score += 0.3
        elif field_count >= 4:
            score += 0.2
        elif field_count >= 2:
            score += 0.1
        
        # Bonus per dati strutturati complessi
        complex_structures = sum(1 for v in data.values() if isinstance(v, (list, dict)))
        score += min(complex_structures * 0.1, 0.2)
        
        # Bonus per presenza di dati azionabili
        data_str = json.dumps(data, default=str).lower()
        actionable_indicators = ['@', 'http', 'phone', '$', '%', 'date', 'contact', 'email']
        actionable_count = sum(1 for indicator in actionable_indicators if indicator in data_str)
        score += min(actionable_count * 0.05, 0.15)
        
        # Penalità per placeholder e content generico
        placeholder_indicators = ['placeholder', 'example', 'todo', 'tbd', 'lorem', 'ipsum', 'xxx']
        placeholder_penalty = sum(0.1 for indicator in placeholder_indicators if indicator in data_str)
        score -= min(placeholder_penalty, 0.4)
        
        # Bonus per lunghezza e dettaglio del contenuto
        total_content_length = sum(len(str(v)) for v in data.values())
        if total_content_length > 500:
            score += 0.15
        elif total_content_length > 200:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_actionability_score(self, data: Dict) -> float:
        """Calcola actionability score intelligentemente"""
        
        score = 0.3  # Base score
        
        data_str = json.dumps(data, default=str).lower()
        
        # Score per presenza di dati immediatamente utilizzabili
        immediate_use_indicators = [
            ('@', 0.2),  # Email addresses
            ('http', 0.15),  # URLs
            ('phone', 0.15),  # Phone numbers
            ('$', 0.1),  # Money values
            ('%', 0.1),  # Percentages
            ('date', 0.1),  # Dates
            ('step', 0.1),  # Process steps
            ('action', 0.1)  # Action items
        ]
        
        for indicator, bonus in immediate_use_indicators:
            if indicator in data_str:
                score += bonus
        
        # Bonus per struttura organizzata
        if isinstance(data, dict):
            organized_structures = ['list', 'items', 'steps', 'contacts', 'tasks', 'goals']
            organized_count = sum(1 for key in data.keys() if any(struct in str(key).lower() for struct in organized_structures))
            score += min(organized_count * 0.1, 0.2)
        
        # Bonus per completezza implementativa
        implementation_indicators = ['instruction', 'guide', 'how', 'implement', 'deploy', 'use']
        impl_count = sum(1 for indicator in implementation_indicators if indicator in data_str)
        score += min(impl_count * 0.05, 0.15)
        
        return max(0.0, min(1.0, score))
    
    def _is_ready_to_use(self, data: Dict) -> bool:
        """Determina se l'asset è ready to use con soglie intelligenti"""
        
        quality = self._calculate_quality_score(data)
        actionability = self._calculate_actionability_score(data)
        
        # Soglie dinamiche più permissive
        return quality >= 0.6 and actionability >= 0.5
    
    def _assess_enhancement_potential(self, data: Dict) -> float:
        """Valuta il potenziale di enhancement dell'asset"""
        
        base_potential = 0.5
        
        # Maggiore potenziale se ha struttura ma manca contenuto specifico
        if len(data) >= 3:
            base_potential += 0.2
        
        # Potenziale per asset con placeholder o contenuto generico
        data_str = json.dumps(data, default=str).lower()
        if any(placeholder in data_str for placeholder in ['placeholder', 'example', 'todo']):
            base_potential += 0.3
        
        return min(1.0, base_potential)
    
    async def _enhance_with_schema_validation(self, asset_data: Dict, schema: AssetSchema) -> Dict:
        """Migliora asset data con validazione schema se disponibile"""
        
        try:
            from deliverable_system.schema_generator import AssetSchemaGenerator
            schema_generator = AssetSchemaGenerator()
            
            # Valida contro schema
            validation_result = schema_generator.validate_asset_against_schema(
                asset_data['asset_data'], schema
            )
            
            # Aggiorna score basato su validazione
            if validation_result.get('valid', False):
                asset_data['quality_score'] = max(asset_data['quality_score'], 0.7)
                asset_data['schema_validated'] = True
            
            asset_data['schema_validation'] = validation_result
            
        except Exception as e:
            logger.debug(f"Schema validation failed: {e}")
        
        return asset_data


class IntelligentDeliverablePackager:
    """
    Packager intelligente che crea deliverable personalizzati usando AI
    """
    
    def __init__(self):
        self.ai_analyzer = AIDeliverableAnalyzer()
    
    async def create_intelligent_deliverable(
        self,
        workspace_id: str,
        workspace_goal: str,
        deliverable_analysis: Dict[str, Any],
        extracted_assets: Dict[str, Any],
        completed_tasks: List[Dict],
        quality_analysis: Optional[Dict] = None
    ) -> ActionableDeliverable:
        """
        Crea deliverable intelligente usando analisi AI e quality assurance
        """
        
        # Genera executive summary con AI awareness
        executive_summary = await self._generate_intelligent_executive_summary(
            workspace_goal, deliverable_analysis, extracted_assets, completed_tasks, quality_analysis
        )
        
        # Organizza asset intelligentemente
        organized_assets = await self._organize_assets_intelligently(extracted_assets, deliverable_analysis)
        
        # Genera usage guide dinamico e dettagliato
        usage_guide = await self._generate_intelligent_usage_guide(organized_assets, deliverable_analysis)
        
        # Genera next steps con AI guidance
        next_steps = await self._generate_intelligent_next_steps(deliverable_analysis, organized_assets, quality_analysis)
        
        # Calcola metriche avanzate
        business_metrics = self._calculate_advanced_business_metrics(extracted_assets, completed_tasks, deliverable_analysis)
        
        # Prepara asset data per ActionableDeliverable
        actionable_assets_dict = {}
        for asset_id, asset_info in organized_assets.items():
            actionable_assets_dict[asset_id] = ExtractedAsset(
                asset_name=asset_info.get('asset_type', 'business_asset'),
                asset_data=asset_info.get('asset_data', {}),
                source_task_id=asset_info.get('source_task_id', ''),
                extraction_method=asset_info.get('extraction_method', 'intelligent'),
                validation_score=asset_info.get('quality_score', 0.5),
                actionability_score=asset_info.get('actionability_score', 0.5),
                ready_to_use=asset_info.get('ready_to_use', False)
            )
        
        deliverable = ActionableDeliverable(
            workspace_id=workspace_id,
            deliverable_id=f"intelligent_{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            meta={
                'project_goal': workspace_goal,
                'deliverable_type': deliverable_analysis.get('deliverable_type', 'intelligent_package'),
                'ai_analysis_confidence': deliverable_analysis.get('confidence_score', 0.8),
                'total_assets': len(extracted_assets),
                'ready_to_use_assets': sum(1 for asset in extracted_assets.values() if asset.get('ready_to_use', False)),
                'generation_method': 'ai_intelligent_hybrid',
                'business_value_focus': deliverable_analysis.get('business_value_focus', ''),
                'implementation_priority': deliverable_analysis.get('implementation_priority', 'short_term'),
                'quality_enhanced': quality_analysis is not None,
                'system_version': '3.0_intelligent_hybrid'
            },
            executive_summary=executive_summary,
            actionable_assets=actionable_assets_dict,
            usage_guide=usage_guide,
            next_steps=next_steps,
            automation_ready=self._calculate_automation_readiness(organized_assets),
            actionability_score=self._calculate_overall_actionability_score(organized_assets)
        )
        
        logger.info(f"🤖 INTELLIGENT DELIVERABLE: Created {deliverable_analysis.get('deliverable_type')} "
                   f"with {len(extracted_assets)} assets (AI confidence: {deliverable_analysis.get('confidence_score', 0):.2f})")
        
        return deliverable
    
    async def _generate_intelligent_executive_summary(
        self,
        workspace_goal: str,
        deliverable_analysis: Dict[str, Any],
        extracted_assets: Dict[str, Any],
        completed_tasks: List[Dict],
        quality_analysis: Optional[Dict] = None
    ) -> str:
        """Genera executive summary intelligente con AI"""
        
        if self.ai_analyzer.ai_client:
            try:
                # Prepara context per AI
                assets_summary = []
                for asset_id, asset in extracted_assets.items():
                    quality_score = asset.get('quality_score', 0)
                    actionability = asset.get('actionability_score', 0)
                    ready_status = "✅ Ready" if asset.get('ready_to_use', False) else "🔧 Needs work"
                    assets_summary.append(f"- {asset.get('asset_type', 'Unknown')}: {ready_status} (Q:{quality_score:.1f}, A:{actionability:.1f})")
                
                quality_info = ""
                if quality_analysis:
                    quality_stats = quality_analysis.get('quality_analysis', {})
                    quality_info = f"""
QUALITY ASSURANCE RESULTS:
- Average Quality Score: {quality_stats.get('average_quality_score', 0):.1f}/1.0
- Ready-to-use Assets: {quality_stats.get('ready_to_use_assets', 0)}/{quality_stats.get('total_assets_analyzed', 0)}
- Enhancement Tasks: {quality_stats.get('enhancement_tasks_created', 0)} created"""
                
                prompt = f"""Write a compelling executive summary for this business deliverable that showcases the intelligent analysis and results.

PROJECT GOAL: {workspace_goal}
DELIVERABLE TYPE: {deliverable_analysis.get('deliverable_type', '')}
AI ANALYSIS CONFIDENCE: {deliverable_analysis.get('confidence_score', 0):.1f}/1.0
BUSINESS VALUE FOCUS: {deliverable_analysis.get('business_value_focus', '')}

PROJECT COMPLETION METRICS:
- Tasks completed: {len(completed_tasks)}
- Assets extracted: {len(extracted_assets)}
- Implementation priority: {deliverable_analysis.get('implementation_priority', '')}

INTELLIGENT ASSET ANALYSIS:
{chr(10).join(assets_summary)}
{quality_info}

Write a professional 2-3 paragraph executive summary that:
1. Clearly states what was accomplished with intelligent analysis
2. Highlights the AI-driven approach and quality assurance
3. Emphasizes immediate business value and implementation readiness
4. Shows confidence in the intelligent system's analysis
5. Uses professional language suitable for C-level presentation

Focus on outcomes, business impact, and the intelligent approach used."""

                response = await self.ai_analyzer.ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=700
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"AI executive summary generation failed: {e}")
        
        # Fallback summary intelligente
        return self._generate_intelligent_fallback_summary(workspace_goal, deliverable_analysis, extracted_assets, quality_analysis)
    
    def _generate_intelligent_fallback_summary(
        self,
        workspace_goal: str,
        deliverable_analysis: Dict[str, Any],
        extracted_assets: Dict[str, Any],
        quality_analysis: Optional[Dict] = None
    ) -> str:
        """Genera executive summary fallback intelligente"""
        
        total_assets = len(extracted_assets)
        ready_assets = sum(1 for asset in extracted_assets.values() if asset.get('ready_to_use', False))
        deliverable_type = deliverable_analysis.get('deliverable_type', 'intelligent business deliverable')
        confidence = deliverable_analysis.get('confidence_score', 0.8)
        business_focus = deliverable_analysis.get('business_value_focus', 'strategic business value')
        
        quality_section = ""
        if quality_analysis:
            quality_stats = quality_analysis.get('quality_analysis', {})
            avg_quality = quality_stats.get('average_quality_score', 0)
            enhancement_tasks = quality_stats.get('enhancement_tasks_created', 0)
            quality_section = f" Our intelligent quality assurance system analyzed all assets with an average quality score of {avg_quality:.1f}/1.0 and created {enhancement_tasks} enhancement tasks to optimize deliverable value."
        
        return f"""**Intelligent Project Delivery Summary**

**Objective Achieved:** {workspace_goal}

This project has been completed using our intelligent, AI-driven delivery system with {confidence:.0%} confidence in the analysis and approach. The system has produced a comprehensive {deliverable_type} containing {total_assets} strategically analyzed business assets. {ready_assets} assets have been identified as immediately ready for implementation, enabling rapid deployment and time-to-value acceleration.

**Intelligent Analysis Results:** Our AI system identified the optimal focus on {business_focus}, structuring all deliverables for maximum business impact. Each asset has been intelligently categorized, quality-assessed, and prepared with specific implementation guidance.{quality_section}

**Business Impact & Implementation:** These intelligently curated deliverables enable immediate implementation of {workspace_goal.lower()}, with clear pathways to measurable business outcomes. The intelligent system has optimized asset organization and presentation for maximum usability, ensuring long-term value creation and successful business deployment."""
    
    async def _organize_assets_intelligently(self, extracted_assets: Dict[str, Any], deliverable_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Organizza asset usando logica intelligente"""
        
        organized = {}
        implementation_priority = deliverable_analysis.get('implementation_priority', 'short_term')
        
        # Organizza per priorità e qualità
        for asset_id, asset in extracted_assets.items():
            quality_score = asset.get('quality_score', 0)
            actionability_score = asset.get('actionability_score', 0)
            ready_to_use = asset.get('ready_to_use', False)
            
            # Calcola priority score intelligente
            priority_score = (quality_score * 0.4) + (actionability_score * 0.4) + (0.2 if ready_to_use else 0)
            
            # Aggiungi priority boost basato su implementation_priority
            if implementation_priority == 'immediate' and ready_to_use:
                priority_score += 0.2
            elif implementation_priority == 'strategic' and quality_score > 0.7:
                priority_score += 0.15
            
            asset['priority_score'] = priority_score
            asset['implementation_tier'] = self._determine_implementation_tier(asset, implementation_priority)
            
            organized[asset_id] = asset
        
        # Ordina per priority score
        organized = dict(sorted(organized.items(), key=lambda x: x[1].get('priority_score', 0), reverse=True))
        
        return organized
    
    def _determine_implementation_tier(self, asset: Dict, implementation_priority: str) -> str:
        """Determina tier di implementazione intelligente"""
        
        quality = asset.get('quality_score', 0)
        actionability = asset.get('actionability_score', 0)
        ready = asset.get('ready_to_use', False)
        
        if ready and quality >= 0.7 and actionability >= 0.6:
            return 'tier_1_immediate'
        elif quality >= 0.6 and actionability >= 0.5:
            return 'tier_2_short_term'
        elif quality >= 0.4:
            return 'tier_3_development'
        else:
            return 'tier_4_reference'
    
    async def _generate_intelligent_usage_guide(self, organized_assets: Dict[str, Any], deliverable_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Genera usage guide intelligente e dettagliato"""
        
        usage_guide = {}
        business_focus = deliverable_analysis.get('business_value_focus', '')
        
        for asset_id, asset in organized_assets.items():
            asset_type = asset.get('asset_type', 'business_asset')
            tier = asset.get('implementation_tier', 'tier_2_short_term')
            quality_score = asset.get('quality_score', 0)
            actionability_score = asset.get('actionability_score', 0)
            
            # Generate tier-specific guidance
            tier_guidance = {
                'tier_1_immediate': f"🚀 **IMMEDIATE DEPLOYMENT READY**: This {asset_type} is optimized and ready for immediate business implementation.",
                'tier_2_short_term': f"📋 **SHORT-TERM IMPLEMENTATION**: This {asset_type} requires minimal customization before deployment.",
                'tier_3_development': f"🔧 **DEVELOPMENT PHASE**: This {asset_type} needs enhancement but provides a solid foundation.",
                'tier_4_reference': f"📚 **REFERENCE MATERIAL**: Use this {asset_type} as supporting information and insights."
            }
            
            base_guidance = tier_guidance.get(tier, f"📋 Review and adapt this {asset_type}")
            
            # Add quality and actionability context
            quality_context = f" Quality Score: {quality_score:.1f}/1.0, Actionability: {actionability_score:.1f}/1.0."
            
            # Add business context
            business_context = f" Aligned with {business_focus} strategy for maximum business impact."
            
            # Add specific implementation guidance based on asset type
            implementation_guidance = self._get_asset_specific_guidance(asset_type, tier, business_focus)
            
            usage_guide[asset_id] = base_guidance + quality_context + business_context + implementation_guidance
        
        return usage_guide
    
    def _get_asset_specific_guidance(self, asset_type: str, tier: str, business_focus: str) -> str:
        """Ottieni guidance specifico per tipo di asset"""
        
        guidance_map = {
            'contact_database': " Import into CRM, segment by qualification scores, and begin targeted outreach campaigns.",
            'content_calendar': " Load into content management system, schedule posts, and track engagement metrics.",
            'strategy_framework': " Review with leadership team, customize for organizational context, and begin implementation planning.",
            'financial_model': " Validate assumptions, customize for business model, and use for budget planning and investor presentations.",
            'training_program': " Deploy following structured timeline, track participant progress, and measure skill improvement.",
            'research_report': " Review findings with stakeholders, extract actionable insights, and integrate into strategic planning.",
            'implementation_guide': " Follow step-by-step procedures, assign responsible teams, and establish progress checkpoints.",
            'workflow_template': " Customize for organizational processes, train team members, and implement monitoring systems."
        }
        
        specific = guidance_map.get(asset_type, " Follow best practices for your industry and organizational context.")
        
        # Add tier-specific enhancements
        if tier == 'tier_1_immediate':
            specific += " Begin implementation within 24-48 hours for optimal results."
        elif tier == 'tier_2_short_term':
            specific += " Plan implementation within 1-2 weeks after customization."
        
        return specific
    
    async def _generate_intelligent_next_steps(
        self, 
        deliverable_analysis: Dict[str, Any], 
        organized_assets: Dict[str, Any],
        quality_analysis: Optional[Dict] = None
    ) -> List[str]:
        """Genera next steps intelligenti e personalizzati"""
        
        next_steps = []
        
        # Analizza tier distribution
        tier_counts = {}
        for asset in organized_assets.values():
            tier = asset.get('implementation_tier', 'tier_2_short_term')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Steps basati su tier 1 (immediate)
        tier_1_count = tier_counts.get('tier_1_immediate', 0)
        if tier_1_count > 0:
            next_steps.append(f"🚀 IMMEDIATE (Week 1): Deploy {tier_1_count} ready-to-use assets for instant business value")
        
        # Steps basati su tier 2 (short-term)
        tier_2_count = tier_counts.get('tier_2_short_term', 0)
        if tier_2_count > 0:
            next_steps.append(f"📋 SHORT-TERM (Week 2-3): Customize and deploy {tier_2_count} high-quality assets")
        
        # Steps basati su tier 3 (development)
        tier_3_count = tier_counts.get('tier_3_development', 0)
        if tier_3_count > 0:
            next_steps.append(f"🔧 DEVELOPMENT (Month 1): Enhance {tier_3_count} foundational assets for extended value")
        
        # Quality-based steps
        if quality_analysis:
            quality_stats = quality_analysis.get('quality_analysis', {})
            enhancement_tasks = quality_stats.get('enhancement_tasks_created', 0)
            if enhancement_tasks > 0:
                next_steps.append(f"🔍 QUALITY ENHANCEMENT: Monitor and complete {enhancement_tasks} AI-identified improvement tasks")
        
        # Implementation priority specific steps
        implementation_priority = deliverable_analysis.get('implementation_priority', 'short_term')
        if implementation_priority == 'immediate':
            next_steps.insert(0, "⚡ URGENT: Begin immediate implementation to capitalize on time-sensitive opportunities")
        elif implementation_priority == 'strategic':
            next_steps.append("🎯 STRATEGIC: Integrate deliverables into long-term strategic planning and execution roadmap")
        
        # Generic ongoing steps
        next_steps.extend([
            "📊 MONITORING (Ongoing): Track implementation progress and measure business impact using provided success metrics",
            "🔄 OPTIMIZATION (Month 1+): Iterate and improve based on performance data and business feedback",
            "📈 SCALING (Quarter 1+): Scale successful implementations and expand to additional business areas"
        ])
        
        return next_steps
    
    def _calculate_advanced_business_metrics(
        self, 
        extracted_assets: Dict[str, Any], 
        completed_tasks: List[Dict],
        deliverable_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcola metriche business avanzate e intelligenti"""
        
        total_assets = len(extracted_assets)
        ready_assets = sum(1 for asset in extracted_assets.values() if asset.get('ready_to_use', False))
        
        # Calcola score medi con pesatura intelligente
        quality_scores = [asset.get('quality_score', 0) for asset in extracted_assets.values()]
        actionability_scores = [asset.get('actionability_score', 0) for asset in extracted_assets.values()]
        
        weighted_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        weighted_actionability = sum(actionability_scores) / len(actionability_scores) if actionability_scores else 0
        
        # Analizza tier distribution
        tier_distribution = {}
        for asset in extracted_assets.values():
            tier = asset.get('implementation_tier', 'tier_2_short_term')
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Calcola business value score
        business_value_score = (
            (weighted_quality * 0.3) +
            (weighted_actionability * 0.3) +
            (ready_assets / total_assets * 0.4) if total_assets > 0 else 0
        )
        
        # Determina time to value
        immediate_ratio = tier_distribution.get('tier_1_immediate', 0) / total_assets if total_assets > 0 else 0
        if immediate_ratio >= 0.5:
            time_to_value = "Immediate (1-3 days)"
        elif immediate_ratio >= 0.3:
            time_to_value = "Very Fast (1 week)"
        elif ready_assets >= total_assets * 0.6:
            time_to_value = "Fast (1-2 weeks)"
        else:
            time_to_value = "Standard (2-4 weeks)"
        
        return {
            'total_assets_delivered': total_assets,
            'immediately_actionable': ready_assets,
            'weighted_quality_score': round(weighted_quality, 2),
            'weighted_actionability_score': round(weighted_actionability, 2),
            'business_value_score': round(business_value_score, 2),
            'implementation_readiness': f"{ready_assets}/{total_assets} assets ready",
            'time_to_value': time_to_value,
            'tier_distribution': tier_distribution,
            'ai_analysis_confidence': deliverable_analysis.get('confidence_score', 0.8),
            'business_value_category': self._categorize_business_value(business_value_score),
            'implementation_complexity': self._assess_implementation_complexity(tier_distribution),
            'total_tasks_completed': len(completed_tasks),
            'intelligence_level': 'AI-Enhanced' if deliverable_analysis.get('confidence_score', 0) > 0.7 else 'Standard'
        }
    
    def _categorize_business_value(self, score: float) -> str:
        """Categorizza business value intelligentemente"""
        if score >= 0.8:
            return "Exceptional"
        elif score >= 0.7:
            return "High"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Moderate"
        else:
            return "Developing"
    
    def _assess_implementation_complexity(self, tier_distribution: Dict[str, int]) -> str:
        """Valuta complessità di implementazione"""
        immediate = tier_distribution.get('tier_1_immediate', 0)
        total = sum(tier_distribution.values())
        
        if total == 0:
            return "Unknown"
        
        immediate_ratio = immediate / total
        
        if immediate_ratio >= 0.7:
            return "Low - Most assets ready for immediate use"
        elif immediate_ratio >= 0.4:
            return "Moderate - Mix of ready and customizable assets"
        else:
            return "High - Requires significant customization effort"
    
    def _calculate_automation_readiness(self, organized_assets: Dict[str, Any]) -> bool:
        """Calcola automation readiness intelligente"""
        
        if not organized_assets:
            return False
        
        automation_scores = []
        for asset in organized_assets.values():
            score = 0
            
            # Score basato su qualità e actionability
            if asset.get('quality_score', 0) >= 0.7:
                score += 0.4
            if asset.get('actionability_score', 0) >= 0.6:
                score += 0.3
            if asset.get('ready_to_use', False):
                score += 0.3
            
            automation_scores.append(score)
        
        avg_automation_score = sum(automation_scores) / len(automation_scores)
        return avg_automation_score >= 0.6
    
    def _calculate_overall_actionability_score(self, organized_assets: Dict[str, Any]) -> int:
        """Calcola actionability score complessivo intelligente (0-100)"""
        
        if not organized_assets:
            return 0
        
        # Media pesata degli score individuali
        total_score = 0
        total_weight = 0
        
        for asset in organized_assets.values():
            actionability = asset.get('actionability_score', 0)
            quality = asset.get('quality_score', 0)
            ready = asset.get('ready_to_use', False)
            
            # Peso basato su priority score
            weight = asset.get('priority_score', 0.5)
            
            # Score combinato
            combined_score = (actionability * 0.5) + (quality * 0.3) + (0.2 if ready else 0)
            
            total_score += combined_score * weight
            total_weight += weight
        
        base_score = total_score / total_weight if total_weight > 0 else 0
        
        # Bonus per diversità di asset
        diversity_bonus = min(len(organized_assets) * 0.02, 0.15)
        
        # Bonus per tier 1 assets
        tier_1_count = sum(1 for asset in organized_assets.values() 
                          if asset.get('implementation_tier') == 'tier_1_immediate')
        tier_1_bonus = min(tier_1_count * 0.05, 0.15)
        
        final_score = (base_score + diversity_bonus + tier_1_bonus) * 100
        return min(100, int(final_score))


# === ENHANCED DELIVERABLE AGGREGATOR WITH INTELLIGENCE ===

class IntelligentDeliverableAggregator:
    """
    Aggregatore intelligente che combina il meglio di AI Quality Assurance + Dynamic AI Analysis
    """
    
    def __init__(self):
        # Core components
        self.ai_analyzer = AIDeliverableAnalyzer()
        self.asset_extractor = DynamicAssetExtractor()
        self.packager = IntelligentDeliverablePackager()
        
        # Quality Assurance components se disponibili
        self.enhancement_orchestrator = None
        self.quality_validator = None
        
        if is_quality_assurance_available():
            try:
                self.enhancement_orchestrator = AssetEnhancementOrchestrator()
                self.quality_validator = AIQualityValidator()
                logger.info("✅ Intelligent Deliverable Aggregator with full AI Quality Assurance")
            except Exception as e:
                logger.error(f"Failed to initialize AI Quality Assurance: {e}")
        else:
            logger.info("🔄 Intelligent Deliverable Aggregator without AI Quality Assurance")
        
        # Schema system components se disponibili
        try:
            self.requirements_analyzer = DeliverableRequirementsAnalyzer()
            self.schema_generator = AssetSchemaGenerator()
            logger.info("✅ Schema system available")
        except Exception as e:
            logger.warning(f"Schema system not available: {e}")
            self.requirements_analyzer = None
            self.schema_generator = None
        
        # Configurazioni
        self.readiness_threshold = DELIVERABLE_READINESS_THRESHOLD / 100.0
        self.min_completed_tasks = MIN_COMPLETED_TASKS_FOR_DELIVERABLE
        
        logger.info("🤖 Intelligent Deliverable Aggregator initialized successfully")
    
    async def check_and_create_final_deliverable(self, workspace_id: str) -> Optional[str]:
        """
        Controlla e crea deliverable finale usando approccio intelligente ibrido
        """
        
        try:
            logger.info(f"🤖 INTELLIGENT DELIVERABLE: Starting analysis for workspace {workspace_id}")
            
            # Fase 1: Controlli preliminari
            if not await self._is_ready_for_deliverable(workspace_id):
                logger.debug(f"🤖 NOT READY: Workspace {workspace_id}")
                return None
            
            if await self._deliverable_exists(workspace_id):
                logger.info(f"🤖 EXISTS: Final deliverable already exists for {workspace_id}")
                return None
            
            # Fase 2: Raccolta dati del progetto
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if not workspace or len(completed_tasks) < self.min_completed_tasks:
                logger.info(f"🤖 INSUFFICIENT DATA: {len(completed_tasks)} completed tasks")
                return None
            
            workspace_goal = workspace.get("goal", "")
            
            # Fase 3: Analisi AI dinamica del tipo di deliverable
            deliverable_analysis = await self.ai_analyzer.analyze_project_deliverable_type(
                workspace_goal, completed_tasks
            )
            
            logger.info(f"🤖 AI ANALYSIS: {deliverable_analysis.get('deliverable_type')} "
                       f"(confidence: {deliverable_analysis.get('confidence_score', 0):.2f})")
            
            # Fase 4: Analisi requirements e schema se disponibili
            asset_schemas = {}
            if self.requirements_analyzer and self.schema_generator:
                try:
                    requirements = await self.requirements_analyzer.analyze_deliverable_requirements(workspace_id)
                    asset_schemas = await self.schema_generator.generate_asset_schemas(requirements)
                    logger.info(f"🤖 SCHEMA SYSTEM: Generated {len(asset_schemas)} schemas")
                except Exception as e:
                    logger.warning(f"Schema generation failed: {e}")
            
            # Fase 5: Estrazione intelligente degli asset
            extracted_assets = await self.asset_extractor.extract_assets_dynamically(
                completed_tasks, deliverable_analysis, asset_schemas
            )
            
            if not extracted_assets:
                logger.warning(f"🤖 NO ASSETS: No actionable assets extracted from {len(completed_tasks)} tasks")
                # Continua comunque con deliverable vuoto ma informativo
            
            # Fase 6: Creazione deliverable intelligente
            intelligent_deliverable = await self.packager.create_intelligent_deliverable(
                workspace_id, workspace_goal, deliverable_analysis, extracted_assets, completed_tasks
            )
            
            # Fase 7: Quality Enhancement se disponibile
            quality_enhanced_deliverable = None
            if self.enhancement_orchestrator and ENABLE_AI_QUALITY_ASSURANCE:
                try:
                    logger.info(f"🤖 QUALITY ENHANCEMENT: Starting AI quality analysis")
                    enhanced_data = await self.enhancement_orchestrator.analyze_and_enhance_deliverable_assets(
                        workspace_id, intelligent_deliverable.model_dump()
                    )
                    quality_enhanced_deliverable = enhanced_data
                    logger.info(f"🤖 QUALITY ENHANCEMENT: Completed successfully")
                except Exception as e:
                    logger.error(f"Quality enhancement failed: {e}, continuing with standard deliverable")
            
            # Fase 8: Creazione task deliverable nel database
            deliverable_task_id = await self._create_intelligent_deliverable_task(
                workspace_id, workspace, intelligent_deliverable, deliverable_analysis, quality_enhanced_deliverable
            )
            
            if deliverable_task_id:
                logger.critical(f"🤖 SUCCESS: Intelligent deliverable created: {deliverable_task_id}")
                
                # Trigger auto-completion se abilitato
                if ENABLE_AUTO_PROJECT_COMPLETION:
                    asyncio.create_task(self._trigger_intelligent_completion_sequence(workspace_id, deliverable_task_id))
                
                return deliverable_task_id
            else:
                logger.error(f"🤖 FAILED: Could not create deliverable task")
                return None
                
        except Exception as e:
            logger.error(f"🤖 ERROR: Exception in intelligent deliverable creation for {workspace_id}: {e}", exc_info=True)
            return None
    
    async def _is_ready_for_deliverable(self, workspace_id: str) -> bool:
        """Controlla readiness con criteri intelligenti"""
        
        try:
            tasks = await list_tasks(workspace_id)
            
            if not tasks:
                return False
            
            completed = [t for t in tasks if t.get("status") == "completed"]
            in_progress = [t for t in tasks if t.get("status") == "in_progress"]
            pending = [t for t in tasks if t.get("status") == "pending"]
            failed = [t for t in tasks if t.get("status") == "failed"]
            
            total_tasks = len(tasks)
            completed_count = len(completed)
            
            # Criteri intelligenti multi-path
            completion_rate = completed_count / total_tasks if total_tasks > 0 else 0
            
            # Path 1: Alta completion rate
            high_completion = completion_rate >= self.readiness_threshold and completed_count >= self.min_completed_tasks
            
            # Path 2: Sufficiente progresso con buona distribuzione
            good_progress = completed_count >= 4 and completion_rate >= 0.6 and len(pending) <= 5
            
            # Path 3: Progetti lunghi con sostanziale completamento
            substantial_work = completed_count >= 8 and completion_rate >= 0.5
            
            # Path 4: Analisi qualitativa dei task completati
            quality_threshold = await self._qualitative_readiness_check(completed, workspace_id)
            
            # Path 5: Time-based per progetti running
            time_based = await self._time_based_readiness_check(workspace_id, completed_count)
            
            is_ready = any([high_completion, good_progress, substantial_work, quality_threshold, time_based])
            
            logger.info(f"🤖 READINESS: {completed_count}/{total_tasks} completed ({completion_rate:.2f}), "
                       f"Paths: [HiComp:{high_completion}, GoodProg:{good_progress}, Subst:{substantial_work}, "
                       f"Qual:{quality_threshold}, Time:{time_based}] = {is_ready}")
            
            return is_ready
            
        except Exception as e:
            logger.error(f"Error in intelligent readiness check: {e}")
            return False
    
    async def _qualitative_readiness_check(self, completed_tasks: List[Dict], workspace_id: str) -> bool:
        """Analisi qualitativa della readiness"""
        
        if len(completed_tasks) < 3:
            return False
        
        # Analizza la sostanza dei task completati
        substantial_tasks = 0
        for task in completed_tasks:
            result = task.get('result', {}) or {}
            summary = result.get('summary', '')
            detailed_json = result.get('detailed_results_json', '')
            
            # Task è sostanziale se ha buon contenuto
            if (len(summary) > 100 or 
                (detailed_json and len(detailed_json) > 200)):
                substantial_tasks += 1
        
        # Se almeno 60% dei task sono sostanziali
        substantial_ratio = substantial_tasks / len(completed_tasks)
        return substantial_ratio >= 0.6 and substantial_tasks >= 3
    
    async def _time_based_readiness_check(self, workspace_id: str, completed_count: int) -> bool:
        """Controllo readiness basato su tempo con logica intelligente"""
        
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace or not workspace.get("created_at"):
                return False
            
            created_at = datetime.fromisoformat(workspace["created_at"].replace('Z', '+00:00'))
            project_age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600
            
            # Logica intelligente time-based
            if project_age_hours > 6 and completed_count >= 4:  # Progetto lungo con buon progress
                return True
            elif project_age_hours > 12 and completed_count >= 3:  # Progetto molto lungo
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _deliverable_exists(self, workspace_id: str) -> bool:
        """Controlla esistenza deliverable con detection intelligente"""
        
        try:
            tasks = await list_tasks(workspace_id)
            
            for task in tasks:
                context_data = task.get("context_data", {}) or {}
                task_name = (task.get("name", "") or "").upper()
                
                # Check per marker espliciti di deliverable
                if isinstance(context_data, dict):
                    deliverable_markers = [
                        "is_final_deliverable",
                        "deliverable_aggregation", 
                        "triggers_project_completion",
                        "intelligent_deliverable",
                        "quality_enhanced_deliverable",
                        "dynamic_deliverable"
                    ]
                    
                    if any(context_data.get(marker) for marker in deliverable_markers):
                        logger.info(f"🤖 EXISTING DELIVERABLE: Found by context marker: {task['id']}")
                        return True
                
                # Check per pattern specifici nel nome (escludendo planning)
                deliverable_patterns = [
                    "🎯 FINAL DELIVERABLE:",
                    "🎯 INTELLIGENT DELIVERABLE:",
                    "🎯 DYNAMIC DELIVERABLE:",
                    "🎯 QUALITY-ASSURED FINAL DELIVERABLE",
                    "🎯 FINAL ASSET-READY DELIVERABLE"
                ]
                
                # Escludi pattern di planning
                planning_exclusions = [
                    "PLANNING",
                    "SETUP", 
                    "CREATE FINAL DELIVERABLES",
                    "CRITICAL: CREATE"
                ]
                
                # Se contiene pattern di exclusion, skip
                if any(exclusion in task_name for exclusion in planning_exclusions):
                    continue
                
                # Se contiene pattern di deliverable, è un deliverable
                if any(pattern in task_name for pattern in deliverable_patterns):
                    logger.info(f"🤖 EXISTING DELIVERABLE: Found by name pattern: {task['id']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existing deliverable: {e}")
            return True  # Safe default
    
    async def _create_intelligent_deliverable_task(
        self,
        workspace_id: str,
        workspace: Dict,
        intelligent_deliverable: ActionableDeliverable,
        deliverable_analysis: Dict[str, Any],
        quality_enhanced_data: Optional[Dict] = None
    ) -> Optional[str]:
        """Crea task deliverable intelligente nel database"""
        
        try:
            # Trova agente ottimale con AI guidance
            agents = await list_agents(workspace_id)
            deliverable_agent = await self._find_optimal_deliverable_agent(
                agents, deliverable_analysis, intelligent_deliverable
            )
            
            if not deliverable_agent:
                logger.error(f"No suitable agent for intelligent deliverable in workspace {workspace_id}")
                return None
            
            # Crea descrizione intelligente
            description = await self._create_intelligent_task_description(
                workspace.get("goal", ""), intelligent_deliverable, deliverable_analysis, quality_enhanced_data
            )
            
            # Nome task intelligente
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            deliverable_type = deliverable_analysis.get('deliverable_type', 'intelligent_package')
            confidence = deliverable_analysis.get('confidence_score', 0.8)
            ai_indicator = "🤖 AI" if confidence > 0.7 else "🔄"
            
            task_name = f"🎯 {ai_indicator} INTELLIGENT DELIVERABLE: {deliverable_type} (C:{confidence:.1f}) ({timestamp})"
            
            # Context data ricco e intelligente
            context_data = {
                "is_final_deliverable": True,
                "deliverable_aggregation": True,
                "intelligent_deliverable": True,
                "deliverable_type": deliverable_type,
                "project_phase": "FINALIZATION",
                "ai_analysis_confidence": confidence,
                "ai_enhanced": True,
                "quality_enhanced": quality_enhanced_data is not None,
                "total_assets": len(intelligent_deliverable.actionable_assets),
                "actionability_score": intelligent_deliverable.actionability_score,
                "automation_ready": intelligent_deliverable.automation_ready,
                "workspace_goal": workspace.get("goal", ""),
                "creation_timestamp": datetime.now().isoformat(),
                "triggers_project_completion": True,
                "system_version": "intelligent_hybrid_v3.0",
                "ai_analyzer_used": self.ai_analyzer.ai_client is not None,
                "quality_assurance_available": self.enhancement_orchestrator is not None,
                "business_value_focus": deliverable_analysis.get('business_value_focus', ''),
                "implementation_priority": deliverable_analysis.get('implementation_priority', ''),
                "precomputed_deliverable": intelligent_deliverable.model_dump(),
                "quality_enhanced_data": quality_enhanced_data
            }
            
            # Crea task con priorità appropriata
            task_priority = self._determine_intelligent_task_priority(deliverable_analysis, intelligent_deliverable)
            
            deliverable_task = await create_task(
                workspace_id=workspace_id,
                agent_id=deliverable_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority=task_priority,
                creation_type="intelligent_ai_deliverable",
                context_data=context_data
            )
            
            if deliverable_task and deliverable_task.get("id"):
                logger.critical(f"🤖 INTELLIGENT DELIVERABLE TASK: {deliverable_task['id']} "
                               f"assigned to {deliverable_agent['name']} (Priority: {task_priority})")
                return deliverable_task["id"]
            else:
                logger.error(f"Failed to create intelligent deliverable task in database")
                return None
                
        except Exception as e:
            logger.error(f"Error creating intelligent deliverable task: {e}", exc_info=True)
            return None
    
    async def _find_optimal_deliverable_agent(
        self, 
        agents: List[Dict], 
        deliverable_analysis: Dict[str, Any],
        intelligent_deliverable: ActionableDeliverable
    ) -> Optional[Dict]:
        """Trova agente ottimale con AI guidance"""
        
        if not agents:
            return None
        
        active_agents = [a for a in agents if a.get("status") == "active"]
        if not active_agents:
            return None
        
        # Analisi intelligente delle requirements
        deliverable_type = deliverable_analysis.get('deliverable_type', '')
        business_focus = deliverable_analysis.get('business_value_focus', '')
        implementation_priority = deliverable_analysis.get('implementation_priority', '')
        actionability_score = intelligent_deliverable.actionability_score
        
        # Scoring intelligente e context-aware
        scored_agents = []
        
        for agent in active_agents:
            role = (agent.get("role", "") or "").lower()
            name = (agent.get("name", "") or "").lower()
            seniority = agent.get("seniority", "junior")
            
            score = 0
            
            # Base score per ruoli manageriali (ottimi per deliverable)
            if any(keyword in role for keyword in ['manager', 'coordinator', 'director', 'lead']):
                score += 20
            
            # Score per allineamento con deliverable type
            type_keywords = deliverable_type.lower().replace('_', ' ').split()
            for keyword in type_keywords:
                if keyword in role or keyword in name:
                    score += 12
            
            # Score per business focus alignment
            focus_keywords = business_focus.lower().split()
            for keyword in focus_keywords:
                if keyword in role or keyword in name:
                    score += 10
            
            # Score per implementation priority
            if implementation_priority == 'immediate' and 'senior' in seniority.lower():
                score += 8
            elif implementation_priority == 'strategic' and any(kw in role for kw in ['strategy', 'manager', 'director']):
                score += 10
            
            # Score per seniority (importante per deliverable quality)
            seniority_scores = {"expert": 15, "senior": 12, "junior": 6}
            score += seniority_scores.get(seniority, 0)
            
            # Bonus per high actionability deliverable
            if actionability_score >= 80 and any(kw in role for kw in ['manager', 'coordinator']):
                score += 8
            
            # Penalty per mismatch totale
            if score < 10:
                score = max(score, 5)  # Minimum viable score
            
            if score > 0:
                scored_agents.append((agent, score, role))
        
        if scored_agents:
            # Ordina per score e prendi il migliore
            scored_agents.sort(key=lambda x: x[1], reverse=True)
            best_agent, best_score, best_role = scored_agents[0]
            
            logger.info(f"🤖 OPTIMAL AGENT: {best_agent['name']} ({best_role}) "
                       f"selected for {deliverable_type} (score: {best_score})")
            return best_agent
        
        # Fallback: primo agente attivo
        fallback = active_agents[0]
        logger.warning(f"🤖 FALLBACK AGENT: {fallback['name']} selected")
        return fallback
    
    def _determine_intelligent_task_priority(
        self, 
        deliverable_analysis: Dict[str, Any],
        intelligent_deliverable: ActionableDeliverable
    ) -> str:
        """Determina priorità task intelligentemente"""
        
        implementation_priority = deliverable_analysis.get('implementation_priority', 'short_term')
        actionability_score = intelligent_deliverable.actionability_score
        confidence = deliverable_analysis.get('confidence_score', 0.8)
        
        # Logic intelligente per priority
        if implementation_priority == 'immediate' or actionability_score >= 85:
            return "high"
        elif implementation_priority == 'strategic' and confidence >= 0.8:
            return "high"
        elif actionability_score >= 70:
            return "medium"
        else:
            return "medium"  # Default sicuro
    
    async def _create_intelligent_task_description(
        self,
        goal: str,
        intelligent_deliverable: ActionableDeliverable,
        deliverable_analysis: Dict[str, Any],
        quality_enhanced_data: Optional[Dict] = None
    ) -> str:
        """Crea descrizione task intelligente e completa"""
        
        # Estrai dati chiave
        deliverable_type = deliverable_analysis.get('deliverable_type', 'intelligent_package')
        confidence = deliverable_analysis.get('confidence_score', 0.8)
        business_focus = deliverable_analysis.get('business_value_focus', '')
        total_assets = len(intelligent_deliverable.actionable_assets)
        actionability_score = intelligent_deliverable.actionability_score
        automation_ready = intelligent_deliverable.automation_ready
        
        # Quality enhancement info
        quality_info = ""
        if quality_enhanced_data:
            quality_stats = quality_enhanced_data.get('meta', {}).get('quality_analysis', {})
            if quality_stats:
                avg_quality = quality_stats.get('average_quality_score', 0)
                enhancement_tasks = quality_stats.get('enhancement_tasks_created', 0)
                quality_info = f"""
📊 **AI QUALITY ENHANCEMENT RESULTS:**
- Average Asset Quality: {avg_quality:.1f}/1.0
- Enhancement Tasks Created: {enhancement_tasks}
- Quality-Assured Processing: ✅ Active"""
        
        description = f"""🤖 **INTELLIGENT AI-DRIVEN DELIVERABLE CREATION**

**PROJECT OBJECTIVE:** {goal}

**🧠 AI ANALYSIS SUMMARY:**
- Deliverable Type: {deliverable_type.replace('_', ' ').title()}
- AI Confidence Level: {confidence:.1f}/1.0 ({self._get_confidence_description(confidence)})
- Business Value Focus: {business_focus}
- Implementation Strategy: {deliverable_analysis.get('implementation_priority', '').title()}

**📦 INTELLIGENT DELIVERABLE PACKAGE:**
- Total Analyzed Assets: {total_assets}
- Overall Actionability Score: {actionability_score}/100
- Automation Ready: {'✅ Yes' if automation_ready else '❌ No'}
- System Intelligence Level: {'🤖 AI-Enhanced' if confidence > 0.7 else '🔄 Standard'}
{quality_info}

**🎯 YOUR INTELLIGENT MISSION:**
You are receiving a pre-computed, AI-analyzed deliverable package that has been intelligently structured for maximum business impact. Your task is to present this analysis in a professional, client-ready format that showcases the intelligent approach used.

**✅ REQUIRED OUTPUT FORMAT:**
Your detailed_results_json must contain:
```json
{{
  "deliverable_type": "{deliverable_type}",
  "executive_summary": "Professional summary highlighting the intelligent AI-driven approach and business value",
  "ai_analysis_confidence": {confidence},
  "business_value_focus": "{business_focus}",
  "intelligent_asset_summary": {{
    "total_assets": {total_assets},
    "actionability_score": {actionability_score},
    "automation_ready": {str(automation_ready).lower()},
    "implementation_tiers": "Breakdown of assets by implementation readiness"
  }},
  "intelligent_recommendations": {{
    "immediate_actions": ["AI-identified immediate steps"],
    "strategic_initiatives": ["Long-term value maximization steps"],
    "success_metrics": ["Intelligent KPIs for measuring deliverable success"]
  }},
  "ai_system_insights": {{
    "analysis_method": "Dynamic AI analysis with {self._get_confidence_description(confidence)} confidence",
    "quality_assurance": "{'AI Quality Enhancement Applied' if quality_enhanced_data else 'Standard Processing'}",
    "automation_potential": "Assessment of automation opportunities"
  }}
}}
```

**🚨 CRITICAL SUCCESS FACTORS:**
- Leverage the AI's intelligent analysis and present it professionally
- Highlight the sophisticated approach used in asset analysis and organization
- Emphasize business value and implementation readiness
- Show confidence in the intelligent system's recommendations
- Create a deliverable worthy of the advanced AI analysis performed

**🤖 INTELLIGENCE AMPLIFICATION:**
This deliverable represents the culmination of advanced AI analysis including:
{self._format_intelligence_features(confidence, quality_enhanced_data)}

**📋 FINAL DELIVERABLE STANDARDS:**
✅ Professional presentation of AI-driven insights and recommendations
✅ Clear categorization of assets by intelligence-assessed implementation readiness  
✅ Specific, actionable guidance based on intelligent analysis
✅ Confidence in AI recommendations while maintaining professional oversight
✅ Ready for C-level presentation and immediate business deployment

The intelligent system has performed sophisticated analysis - trust the recommendations while adding your professional presentation expertise."""
        
        return description.strip()
    
    def _get_confidence_description(self, confidence: float) -> str:
        """Ottieni descrizione textuale della confidence"""
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.8:
            return "High" 
        elif confidence >= 0.7:
            return "Good"
        elif confidence >= 0.6:
            return "Moderate"
        else:
            return "Standard"
    
    def _format_intelligence_features(self, confidence: float, quality_enhanced_data: Optional[Dict]) -> str:
        """Formatta features di intelligence per descrizione"""
        
        features = []
        
        if confidence > 0.7:
            features.append("- 🤖 Dynamic AI deliverable type analysis and optimization")
        
        if self.ai_analyzer.ai_client:
            features.append("- 🧠 GPT-4o-mini powered content analysis and asset categorization")
        
        if quality_enhanced_data:
            features.append("- 🔍 AI Quality Assurance with automated enhancement task generation")
        
        if self.requirements_analyzer:
            features.append("- 📋 Dynamic requirements analysis and schema generation")
        
        features.append("- 📊 Intelligent asset scoring and implementation tier classification")
        features.append("- 🎯 Business value optimization and actionability enhancement")
        
        return "\n".join(features)
    
    async def _trigger_intelligent_completion_sequence(self, workspace_id: str, deliverable_task_id: str):
        """Trigger sequenza di completamento intelligente"""
        
        try:
            logger.info(f"🤖 INTELLIGENT COMPLETION: Starting for workspace {workspace_id}")
            
            # Monitoring intelligente con timeout adattivo
            max_wait_minutes = 45
            check_interval_seconds = 90  # Check meno frequenti ma più intelligenti
            
            for attempt in range(max_wait_minutes // 2):
                await asyncio.sleep(check_interval_seconds)
                
                tasks = await list_tasks(workspace_id)
                deliverable_task = next((t for t in tasks if t.get("id") == deliverable_task_id), None)
                
                if not deliverable_task:
                    logger.warning(f"🤖 COMPLETION: Deliverable task {deliverable_task_id} not found")
                    break
                
                status = deliverable_task.get("status")
                
                if status == "completed":
                    # Verifica qualità del completamento
                    if await self._verify_intelligent_completion(deliverable_task):
                        logger.info(f"🤖 COMPLETION: High-quality completion verified")
                        await update_workspace_status(workspace_id, "completed")
                        logger.critical(f"🤖 PROJECT COMPLETED: Workspace {workspace_id} marked as completed with intelligent verification")
                        break
                    else:
                        logger.warning(f"🤖 COMPLETION: Task completed but quality verification failed")
                        break
                        
                elif status == "failed":
                    logger.error(f"🤖 COMPLETION: Deliverable task failed")
                    break
                elif status in ["pending", "in_progress"]:
                    logger.debug(f"🤖 COMPLETION: Task {deliverable_task_id} still {status} (attempt {attempt + 1})")
                    continue
            
        except Exception as e:
            logger.error(f"Error in intelligent completion sequence: {e}")
    
    async def _verify_intelligent_completion(self, deliverable_task: Dict) -> bool:
        """Verifica intelligente della qualità del completamento"""
        
        try:
            result = deliverable_task.get("result", {})
            if not result:
                return False
            
            detailed_json = result.get("detailed_results_json", "")
            if not detailed_json:
                return False
            
            # Prova parsing JSON
            try:
                data = json.loads(detailed_json)
                if not isinstance(data, dict):
                    return False
                
                # Verifica campi intelligenti chiave
                required_fields = ["deliverable_type", "executive_summary"]
                if not all(field in data for field in required_fields):
                    return False
                
                # Verifica qualità contenuto
                executive_summary = data.get("executive_summary", "")
                if len(executive_summary) < 100:  # Minimum substantial content
                    return False
                
                logger.info(f"✅ Intelligent completion verification passed")
                return True
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in deliverable task completion")
                return False
            
        except Exception as e:
            logger.error(f"Error in intelligent completion verification: {e}")
            return False


# === GLOBAL INSTANCE CON SELEZIONE INTELLIGENTE ===

# Usa IntelligentDeliverableAggregator come istanza principale
deliverable_aggregator = IntelligentDeliverableAggregator()

# === HELPER FUNCTIONS ===

async def check_and_create_final_deliverable(workspace_id: str) -> Optional[str]:
    """Helper function principale che usa il sistema intelligente"""
    try:
        return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)
    except Exception as e:
        logger.error(f"Error in intelligent deliverable creation: {e}", exc_info=True)
        return None

async def create_intelligent_deliverable(workspace_id: str) -> Optional[str]:
    """Helper per forzare creazione deliverable intelligente"""
    try:
        return await deliverable_aggregator.check_and_create_final_deliverable(workspace_id)
    except Exception as e:
        logger.error(f"Error in forced intelligent deliverable creation: {e}")
        return None

def get_deliverable_system_status() -> Dict[str, Any]:
    """Ottieni stato completo del sistema deliverable intelligente"""
    
    return {
        "system_version": "3.0_intelligent_hybrid_ai_driven",
        "approach": "Intelligent AI-driven with Quality Assurance integration",
        "ai_components": {
            "dynamic_ai_analysis": deliverable_aggregator.ai_analyzer.ai_client is not None,
            "quality_assurance_available": deliverable_aggregator.enhancement_orchestrator is not None,
            "schema_system_available": deliverable_aggregator.requirements_analyzer is not None,
            "intelligent_packaging": True
        },
        "configuration": {
            "readiness_threshold": DELIVERABLE_READINESS_THRESHOLD,
            "auto_completion": ENABLE_AUTO_PROJECT_COMPLETION,
            "min_completed_tasks": MIN_COMPLETED_TASKS_FOR_DELIVERABLE,
            "enhanced_logic": ENABLE_ENHANCED_DELIVERABLE_LOGIC,
            "ai_quality_assurance": ENABLE_AI_QUALITY_ASSURANCE,
            "dynamic_ai_analysis": ENABLE_DYNAMIC_AI_ANALYSIS
        },
        "components": {
            "intelligent_aggregator": True,
            "dynamic_ai_analyzer": True,
            "intelligent_asset_extractor": True,
            "intelligent_packager": True,
            "quality_validator": deliverable_aggregator.quality_validator is not None,
            "enhancement_orchestrator": deliverable_aggregator.enhancement_orchestrator is not None,
            "requirements_analyzer": deliverable_aggregator.requirements_analyzer is not None,
            "schema_generator": deliverable_aggregator.schema_generator is not None
        },
        "intelligence_features": {
            "ai_powered_deliverable_analysis": deliverable_aggregator.ai_analyzer.ai_client is not None,
            "dynamic_asset_type_detection": True,
            "intelligent_agent_selection": True,
            "quality_enhancement_integration": deliverable_aggregator.enhancement_orchestrator is not None,
            "schema_based_validation": deliverable_aggregator.schema_generator is not None,
            "multi_tier_implementation_planning": True,
            "business_value_optimization": True
        }
    }

async def verify_intelligent_deliverable_completion(workspace_id: str, deliverable_task_id: str) -> bool:
    """Verifica completion con criteri intelligenti"""
    try:
        tasks = await list_tasks(workspace_id)
        deliverable_task = next((t for t in tasks if t.get("id") == deliverable_task_id), None)
        
        if not deliverable_task:
            logger.error(f"Deliverable task {deliverable_task_id} not found")
            return False
        
        if deliverable_task.get("status") != "completed":
            logger.warning(f"Deliverable task {deliverable_task_id} not completed yet")
            return False
        
        # Verifica intelligente dei risultati
        result = deliverable_task.get("result", {})
        if not result or not result.get("detailed_results_json"):
            logger.error(f"Deliverable task {deliverable_task_id} has no valid results")
            return False
        
        try:
            data = json.loads(result["detailed_results_json"])
            
            # Verifica campi intelligenti essenziali
            essential_fields = ["deliverable_type", "executive_summary"]
            if not all(field in data for field in essential_fields):
                logger.error(f"Deliverable task {deliverable_task_id} missing essential fields")
                return False
            
            # Verifica qualità contenuto
            executive_summary = data.get("executive_summary", "")
            if len(executive_summary) < 150:
                logger.error(f"Deliverable task {deliverable_task_id} has insufficient content quality")
                return False
            
            logger.info(f"✅ Intelligent deliverable task {deliverable_task_id} completed successfully")
            return True
            
        except json.JSONDecodeError:
            logger.error(f"Deliverable task {deliverable_task_id} has invalid JSON results")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying intelligent deliverable completion: {e}")
        return False

async def monitor_intelligent_deliverable_completion(workspace_id: str, deliverable_task_id: str):
    """Monitor intelligent deliverable con retry e fallback"""
    try:
        max_wait_minutes = 60  # Tempo maggiore per deliverable intelligenti
        check_interval_seconds = 120
        
        for attempt in range(max_wait_minutes // 2):
            await asyncio.sleep(check_interval_seconds)
            
            tasks = await list_tasks(workspace_id)
            deliverable_task = next((t for t in tasks if t.get("id") == deliverable_task_id), None)
            
            if not deliverable_task:
                logger.error(f"Intelligent deliverable task {deliverable_task_id} disappeared during monitoring")
                break
            
            status = deliverable_task.get("status")
            
            if status == "completed":
                if await verify_intelligent_deliverable_completion(workspace_id, deliverable_task_id):
                    logger.info(f"✅ Intelligent deliverable monitoring: Task {deliverable_task_id} completed successfully")
                    return
                else:
                    logger.error(f"❌ Intelligent deliverable monitoring: Task {deliverable_task_id} completed but failed quality verification")
                    break
            elif status == "failed":
                logger.error(f"❌ Intelligent deliverable monitoring: Task {deliverable_task_id} failed")
                break
            elif status in ["pending", "in_progress"]:
                logger.debug(f"🤖 Intelligent deliverable monitoring: Task {deliverable_task_id} still {status}")
                continue
        
        logger.warning(f"⚠️ Intelligent deliverable monitoring timeout for task {deliverable_task_id}")
        
    except Exception as e:
        logger.error(f"Error in monitor_intelligent_deliverable_completion: {e}")


# === MONITORING E METRICS AVANZATI ===

class IntelligentQualityMetricsCollector:
    """Collector avanzato per metriche di qualità intelligenti"""
    
    def __init__(self):
        self.quality_metrics = []
        self.deliverable_stats = {
            "total_deliverables_created": 0,
            "intelligent_deliverables": 0,
            "quality_enhanced_deliverables": 0,
            "ai_analyzed_deliverables": 0,
            "failed_deliverables": 0,
            "average_ai_confidence": 0.0,
            "average_actionability_score": 0.0
        }
        self.ai_analysis_metrics = []
    
    def record_intelligent_deliverable_creation(
        self, 
        workspace_id: str, 
        deliverable_type: str,
        ai_confidence: float,
        actionability_score: int,
        quality_enhanced: bool,
        success: bool
    ):
        """Registra creazione deliverable intelligente"""
        
        self.deliverable_stats["total_deliverables_created"] += 1
        
        if success:
            self.deliverable_stats["intelligent_deliverables"] += 1
            
            if quality_enhanced:
                self.deliverable_stats["quality_enhanced_deliverables"] += 1
            
            if ai_confidence > 0.6:
                self.deliverable_stats["ai_analyzed_deliverables"] += 1
        else:
            self.deliverable_stats["failed_deliverables"] += 1
        
        # Aggiorna medie
        total_successful = self.deliverable_stats["intelligent_deliverables"]
        if total_successful > 0:
            current_avg_confidence = self.deliverable_stats["average_ai_confidence"]
            current_avg_actionability = self.deliverable_stats["average_actionability_score"]
            
            self.deliverable_stats["average_ai_confidence"] = (
                (current_avg_confidence * (total_successful - 1) + ai_confidence) / total_successful
            )
            self.deliverable_stats["average_actionability_score"] = (
                (current_avg_actionability * (total_successful - 1) + actionability_score) / total_successful
            )
    
    def record_ai_analysis_metrics(
        self,
        workspace_id: str,
        analysis_type: str,
        confidence_score: float,
        processing_time: float,
        assets_analyzed: int
    ):
        """Registra metriche di analisi AI"""
        
        self.ai_analysis_metrics.append({
            "timestamp": datetime.now().isoformat(),
            "workspace_id": workspace_id,
            "analysis_type": analysis_type,
            "confidence_score": confidence_score,
            "processing_time_seconds": processing_time,
            "assets_analyzed": assets_analyzed
        })
    
    def get_intelligent_deliverable_trends(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Ottieni trend per deliverable intelligenti"""
        
        metrics = self.ai_analysis_metrics
        if workspace_id:
            metrics = [m for m in metrics if m["workspace_id"] == workspace_id]
        
        if not metrics:
            return {"message": "No intelligent deliverable metrics available"}
        
        avg_confidence = sum(m["confidence_score"] for m in metrics) / len(metrics)
        avg_processing_time = sum(m["processing_time_seconds"] for m in metrics) / len(metrics)
        
        return {
            "total_intelligent_analyses": len(metrics),
            "average_ai_confidence": round(avg_confidence, 3),
            "average_processing_time": round(avg_processing_time, 2),
            "confidence_trend": "improving" if len(metrics) > 1 and metrics[-1]["confidence_score"] > metrics[0]["confidence_score"] else "stable",
            "latest_analysis": metrics[-1] if metrics else None,
            "deliverable_success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calcola success rate dei deliverable"""
        total = self.deliverable_stats["total_deliverables_created"]
        failed = self.deliverable_stats["failed_deliverables"]
        
        if total == 0:
            return 0.0
        
        return round((total - failed) / total, 3)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche complete del sistema"""
        
        stats = dict(self.deliverable_stats)
        
        # Calcola percentuali
        total = stats["total_deliverables_created"]
        if total > 0:
            stats["intelligence_rate"] = round(stats["intelligent_deliverables"] / total, 3)
            stats["quality_enhancement_rate"] = round(stats["quality_enhanced_deliverables"] / total, 3)
            stats["ai_analysis_rate"] = round(stats["ai_analyzed_deliverables"] / total, 3)
            stats["success_rate"] = self._calculate_success_rate()
        else:
            stats.update({
                "intelligence_rate": 0.0,
                "quality_enhancement_rate": 0.0,
                "ai_analysis_rate": 0.0,
                "success_rate": 0.0
            })
        
        return stats
    
    def reset_metrics(self):
        """Reset di tutte le metriche"""
        self.quality_metrics.clear()
        self.ai_analysis_metrics.clear()
        self.deliverable_stats = {
            "total_deliverables_created": 0,
            "intelligent_deliverables": 0,
            "quality_enhanced_deliverables": 0,
            "ai_analyzed_deliverables": 0,
            "failed_deliverables": 0,
            "average_ai_confidence": 0.0,
            "average_actionability_score": 0.0
        }

# Istanza globale del collector
intelligent_metrics_collector = IntelligentQualityMetricsCollector()


# === SYSTEM HEALTH E DIAGNOSTICS ===

async def run_intelligent_system_diagnostics() -> Dict[str, Any]:
    """Esegui diagnostici completi del sistema intelligente"""
    
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "system_health": "unknown",
        "components": {},
        "ai_services": {},
        "recommendations": []
    }
    
    try:
        # Test AI Analyzer
        ai_analyzer_status = "healthy"
        try:
            test_analyzer = AIDeliverableAnalyzer()
            if test_analyzer.ai_client:
                diagnostics["ai_services"]["openai_available"] = True
                diagnostics["ai_services"]["dynamic_analysis"] = "available"
            else:
                diagnostics["ai_services"]["openai_available"] = False
                diagnostics["ai_services"]["dynamic_analysis"] = "fallback_mode"
                diagnostics["recommendations"].append("Consider enabling OpenAI API for enhanced AI analysis")
        except Exception as e:
            ai_analyzer_status = "degraded"
            diagnostics["ai_services"]["dynamic_analysis"] = f"error: {str(e)}"
        
        diagnostics["components"]["ai_analyzer"] = ai_analyzer_status
        
        # Test Quality Assurance
        quality_status = "not_available"
        if is_quality_assurance_available():
            try:
                test_orchestrator = AssetEnhancementOrchestrator()
                quality_status = "healthy"
                diagnostics["ai_services"]["quality_assurance"] = "available"
            except Exception as e:
                quality_status = "degraded"
                diagnostics["ai_services"]["quality_assurance"] = f"error: {str(e)}"
        else:
            diagnostics["ai_services"]["quality_assurance"] = "not_available"
            diagnostics["recommendations"].append("Enable AI Quality Assurance for enhanced deliverable quality")
        
        diagnostics["components"]["quality_assurance"] = quality_status
        
        # Test Database Connectivity
        db_status = "unknown"
        try:
            # Test basic database operations
            test_workspaces = await list_tasks("test")  # This will test DB connectivity
            db_status = "healthy"
        except Exception as e:
            db_status = "error"
            diagnostics["recommendations"].append(f"Database connectivity issue: {str(e)}")
        
        diagnostics["components"]["database"] = db_status
        
        # Test Schema System
        schema_status = "not_available"
        try:
            if deliverable_aggregator.requirements_analyzer and deliverable_aggregator.schema_generator:
                schema_status = "healthy"
                diagnostics["ai_services"]["schema_system"] = "available"
            else:
                diagnostics["ai_services"]["schema_system"] = "not_available"
        except Exception as e:
            schema_status = "degraded"
            diagnostics["ai_services"]["schema_system"] = f"error: {str(e)}"
        
        diagnostics["components"]["schema_system"] = schema_status
        
        # Overall system health
        component_statuses = [
            diagnostics["components"]["ai_analyzer"],
            diagnostics["components"]["database"]
        ]
        
        if all(status == "healthy" for status in component_statuses):
            diagnostics["system_health"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            diagnostics["system_health"] = "degraded"
        else:
            diagnostics["system_health"] = "functional"
        
        # Performance metrics
        diagnostics["performance"] = intelligent_metrics_collector.get_comprehensive_stats()
        
        # Configuration status
        diagnostics["configuration_status"] = {
            "ai_quality_assurance_enabled": ENABLE_AI_QUALITY_ASSURANCE,
            "dynamic_ai_analysis_enabled": ENABLE_DYNAMIC_AI_ANALYSIS,
            "auto_completion_enabled": ENABLE_AUTO_PROJECT_COMPLETION,
            "readiness_threshold": DELIVERABLE_READINESS_THRESHOLD
        }
        
    except Exception as e:
        diagnostics["system_health"] = "error"
        diagnostics["error"] = str(e)
        diagnostics["recommendations"].append("System diagnostics failed - manual investigation required")
    
    return diagnostics

def reset_intelligent_system_stats():
    """Reset completo delle statistiche del sistema intelligente"""
    
    # Reset metrics collector
    intelligent_metrics_collector.reset_metrics()
    
    # Reset orchestrator stats se disponibili
    if hasattr(deliverable_aggregator, 'enhancement_orchestrator') and deliverable_aggregator.enhancement_orchestrator:
        try:
            deliverable_aggregator.enhancement_orchestrator.reset_stats()
        except:
            pass
    
    # Reset quality validator stats se disponibili
    if hasattr(deliverable_aggregator, 'quality_validator') and deliverable_aggregator.quality_validator:
        try:
            deliverable_aggregator.quality_validator.reset_stats()
        except:
            pass
    
    # Reset AI analyzer cache
    if hasattr(deliverable_aggregator, 'ai_analyzer'):
        deliverable_aggregator.ai_analyzer.analysis_cache.clear()
    
    logger.info("🔄 Intelligent system stats reset completed")


# === CONFIGURATION HELPERS ===

def update_intelligent_system_config(**kwargs):
    """Aggiorna configurazione sistema intelligente runtime"""
    
    global ENABLE_AI_QUALITY_ASSURANCE, ENABLE_DYNAMIC_AI_ANALYSIS
    global DELIVERABLE_READINESS_THRESHOLD, MIN_COMPLETED_TASKS_FOR_DELIVERABLE
    
    updated = []
    
    if 'enable_ai_quality' in kwargs:
        ENABLE_AI_QUALITY_ASSURANCE = bool(kwargs['enable_ai_quality'])
        updated.append(f"AI Quality Assurance: {ENABLE_AI_QUALITY_ASSURANCE}")
    
    if 'enable_dynamic_ai' in kwargs:
        ENABLE_DYNAMIC_AI_ANALYSIS = bool(kwargs['enable_dynamic_ai'])
        updated.append(f"Dynamic AI Analysis: {ENABLE_DYNAMIC_AI_ANALYSIS}")
    
    if 'readiness_threshold' in kwargs:
        DELIVERABLE_READINESS_THRESHOLD = int(kwargs['readiness_threshold'])
        deliverable_aggregator.readiness_threshold = DELIVERABLE_READINESS_THRESHOLD / 100.0
        updated.append(f"Readiness Threshold: {DELIVERABLE_READINESS_THRESHOLD}%")
    
    if 'min_completed_tasks' in kwargs:
        MIN_COMPLETED_TASKS_FOR_DELIVERABLE = int(kwargs['min_completed_tasks'])
        deliverable_aggregator.min_completed_tasks = MIN_COMPLETED_TASKS_FOR_DELIVERABLE
        updated.append(f"Min Completed Tasks: {MIN_COMPLETED_TASKS_FOR_DELIVERABLE}")
    
    if updated:
        logger.info(f"🔧 Intelligent system configuration updated: {', '.join(updated)}")
    
    return {"updated": updated, "current_config": get_deliverable_system_status()["configuration"]}


# === ADVANCED HELPER FUNCTIONS ===

async def force_create_intelligent_deliverable_with_analysis(workspace_id: str, analysis_override: Optional[Dict] = None) -> Optional[str]:
    """Force creation con analisi specifica (per testing/admin)"""
    try:
        logger.info(f"🤖 FORCE CREATE: Starting intelligent deliverable for {workspace_id}")
        
        # Bypass readiness check
        workspace = await get_workspace(workspace_id)
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        if not workspace:
            logger.error(f"Workspace {workspace_id} not found")
            return None
        
        workspace_goal = workspace.get("goal", "")
        
        # Use provided analysis or generate new one
        if analysis_override:
            deliverable_analysis = analysis_override
            logger.info(f"🤖 FORCE CREATE: Using provided analysis override")
        else:
            deliverable_analysis = await deliverable_aggregator.ai_analyzer.analyze_project_deliverable_type(
                workspace_goal, completed_tasks
            )
            logger.info(f"🤖 FORCE CREATE: Generated new analysis")
        
        # Continue with normal flow
        extracted_assets = await deliverable_aggregator.asset_extractor.extract_assets_dynamically(
            completed_tasks, deliverable_analysis
        )
        
        intelligent_deliverable = await deliverable_aggregator.packager.create_intelligent_deliverable(
            workspace_id, workspace_goal, deliverable_analysis, extracted_assets, completed_tasks
        )
        
        deliverable_task_id = await deliverable_aggregator._create_intelligent_deliverable_task(
            workspace_id, workspace, intelligent_deliverable, deliverable_analysis
        )
        
        if deliverable_task_id:
            logger.critical(f"🤖 FORCE CREATE SUCCESS: {deliverable_task_id}")
        
        return deliverable_task_id
        
    except Exception as e:
        logger.error(f"Error in force create intelligent deliverable: {e}", exc_info=True)
        return None

async def analyze_workspace_deliverable_potential(workspace_id: str) -> Dict[str, Any]:
    """Analizza potenziale di deliverable per workspace"""
    try:
        workspace = await get_workspace(workspace_id)
        tasks = await list_tasks(workspace_id)
        
        if not workspace:
            return {"error": "Workspace not found"}
        
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        # Analisi AI se disponibile
        analysis = {}
        if deliverable_aggregator.ai_analyzer.ai_client and completed_tasks:
            try:
                analysis = await deliverable_aggregator.ai_analyzer.analyze_project_deliverable_type(
                    workspace.get("goal", ""), completed_tasks
                )
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
        
        # Analisi readiness
        readiness_result = await deliverable_aggregator._is_ready_for_deliverable(workspace_id)
        
        # Analisi asset potential
        asset_potential = {}
        if completed_tasks:
            try:
                test_extraction = await deliverable_aggregator.asset_extractor.extract_assets_dynamically(
                    completed_tasks, analysis or {}
                )
                asset_potential = {
                    "extractable_assets": len(test_extraction),
                    "ready_to_use": sum(1 for asset in test_extraction.values() if asset.get('ready_to_use', False)),
                    "average_quality": sum(asset.get('quality_score', 0) for asset in test_extraction.values()) / len(test_extraction) if test_extraction else 0
                }
            except Exception as e:
                logger.warning(f"Asset potential analysis failed: {e}")
        
        return {
            "workspace_id": workspace_id,
            "workspace_goal": workspace.get("goal", ""),
            "task_summary": {
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "completion_rate": len(completed_tasks) / len(tasks) if tasks else 0
            },
            "readiness_assessment": {
                "is_ready": readiness_result,
                "readiness_threshold": deliverable_aggregator.readiness_threshold,
                "min_tasks_met": len(completed_tasks) >= deliverable_aggregator.min_completed_tasks
            },
            "ai_analysis": analysis,
            "asset_potential": asset_potential,
            "recommendations": deliverable_aggregator._generate_recommendations(readiness_result, len(completed_tasks), analysis)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing workspace deliverable potential: {e}")
        return {"error": str(e)}

def _generate_recommendations(self, is_ready: bool, completed_count: int, analysis: Dict) -> List[str]:
    """Genera raccomandazioni per migliorare il deliverable potential"""
    recommendations = []
    
    if not is_ready:
        if completed_count < self.min_completed_tasks:
            recommendations.append(f"Complete at least {self.min_completed_tasks - completed_count} more tasks")
        
        if completed_count > 0:
            recommendations.append("Focus on completing high-quality tasks with substantial outputs")
        
        recommendations.append("Ensure tasks produce detailed results with structured data")
    
    if analysis:
        confidence = analysis.get('confidence_score', 0)
        if confidence < 0.7:
            recommendations.append("Add more specific, domain-focused tasks to improve AI analysis confidence")
    
    if is_ready:
        recommendations.append("✅ Ready for deliverable creation - consider running the intelligent deliverable process")
    
    return recommendations

# Aggiungi il metodo alla classe
IntelligentDeliverableAggregator._generate_recommendations = _generate_recommendations


# === LOGGING E INITIALIZATION ===

logger.info("=" * 80)
logger.info("🤖 INTELLIGENT DELIVERABLE AGGREGATOR SYSTEM INITIALIZED")
logger.info("=" * 80)
logger.info(f"Version: 3.0 Intelligent Hybrid (AI-Driven + Quality Assurance)")
logger.info(f"Aggregator: {type(deliverable_aggregator).__name__}")
logger.info(f"AI Analysis: {'✅ GPT-4o-mini Active' if deliverable_aggregator.ai_analyzer.ai_client else '🔄 Fallback Mode'}")
logger.info(f"Quality Assurance: {'✅ Active' if is_quality_assurance_available() else '❌ Inactive'}")
logger.info(f"Schema System: {'✅ Active' if deliverable_aggregator.requirements_analyzer else '❌ Inactive'}")
logger.info(f"Configuration: Threshold={DELIVERABLE_READINESS_THRESHOLD}%, MinTasks={MIN_COMPLETED_TASKS_FOR_DELIVERABLE}")
logger.info(f"Intelligence Features: Dynamic Analysis, Smart Asset Extraction, Intelligent Packaging")
logger.info("=" * 80)

# Log startup diagnostics
startup_diagnostics = {
    "ai_client_available": deliverable_aggregator.ai_analyzer.ai_client is not None,
    "quality_orchestrator_available": deliverable_aggregator.enhancement_orchestrator is not None,
    "schema_system_available": deliverable_aggregator.requirements_analyzer is not None,
    "configuration_valid": all([
        DELIVERABLE_READINESS_THRESHOLD > 0,
        MIN_COMPLETED_TASKS_FOR_DELIVERABLE > 0,
        isinstance(ENABLE_AUTO_PROJECT_COMPLETION, bool)
    ])
}

logger.info(f"🔧 Startup Diagnostics: {startup_diagnostics}")

if not startup_diagnostics["ai_client_available"]:
    logger.warning("⚠️ OpenAI API not available - system will use fallback analysis methods")

if not startup_diagnostics["quality_orchestrator_available"]:
    logger.warning("⚠️ Quality Assurance not available - deliverables will not have automated quality enhancement")

logger.info("🚀 System ready for intelligent deliverable creation")
logger.info("=" * 80)