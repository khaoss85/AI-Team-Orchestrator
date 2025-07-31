#!/usr/bin/env python3
"""
🧠 AI-DRIVEN TASK EXECUTION CLASSIFIER

Sistema AI per classificare automaticamente i task e determinare
il tipo di execution richiesto (planning vs data collection vs generation).

Principi:
- AI-driven: Usa OpenAI per classificazione semantica
- Domain-agnostic: Funziona per qualsiasi business domain  
- Holistic: Integrato con tutto il sistema di orchestrazione
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from pydantic import BaseModel
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskExecutionType(Enum):
    """Tipi di execution classificati dall'AI"""
    PLANNING = "planning"              # Strategia, metodologia, strutture
    DATA_COLLECTION = "data_collection" # Web scraping, ricerca, liste
    CONTENT_GENERATION = "content_generation" # Creazione asset, copywriting
    ANALYSIS = "analysis"              # Analisi dati, insights, report
    VALIDATION = "validation"          # QA, testing, verifica

class TaskExecutionClassification(BaseModel):
    """Risultato della classificazione AI"""
    task_id: str
    execution_type: TaskExecutionType
    requires_tools: bool
    tools_needed: List[str]
    content_type_expected: str
    output_specificity: str  # "methodology" | "specific_data" | "mixed"
    expected_data_format: Optional[str]  # "CSV", "JSON", "structured_list", etc.
    ai_reasoning: str
    confidence_score: float

class AITaskExecutionClassifier:
    """
    🧠 Classificatore AI per determinare il tipo di execution necessario
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI()
        
    async def classify_task_execution(
        self, 
        task_name: str, 
        task_description: str, 
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> TaskExecutionClassification:
        """
        🎯 Classifica un task per determinare il tipo di execution
        """
        
        logger.info(f"🧠 AI classifying task execution: {task_name}")
        
        # Costruisci prompt AI-driven
        classification_prompt = self._build_classification_prompt(
            task_name, task_description, workspace_context
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": classification_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent classification
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Valida e costruisci classificazione
            classification = TaskExecutionClassification(
                task_id=f"task_{datetime.now().isoformat()}",
                execution_type=TaskExecutionType(result["execution_type"]),
                requires_tools=result["requires_tools"],
                tools_needed=result["tools_needed"],
                content_type_expected=result["content_type_expected"],
                output_specificity=result.get("output_specificity", "methodology"),
                expected_data_format=result.get("expected_data_format"),
                ai_reasoning=result["ai_reasoning"],
                confidence_score=result["confidence_score"]
            )
            
            logger.info(f"✅ Task classified as: {classification.execution_type.value}")
            logger.info(f"🔧 Tools needed: {classification.tools_needed}")
            
            return classification
            
        except Exception as e:
            logger.error(f"❌ AI classification failed: {e}")
            # Fallback classification
            return self._create_fallback_classification(task_name, task_description)
    
    def _get_system_prompt(self) -> str:
        """Sistema prompt per classificazione AI"""
        return """You are an AI task execution classifier. Your job is to analyze tasks and determine:

1. EXECUTION TYPE:
   - "planning": Strategy, methodology, frameworks, templates
   - "data_collection": Web scraping, research, finding lists/contacts 
   - "content_generation": Creating copy, articles, designs, code
   - "analysis": Analyzing data, generating insights, reports
   - "validation": Quality assurance, testing, verification

2. TOOL REQUIREMENTS:
   - Does this task need web scraping/search tools?
   - What specific tools are needed?

3. OUTPUT SPECIFICITY - CRITICAL:
   - "methodology": Task wants HOW to do something (strategies, guides)
   - "specific_data": Task wants ACTUAL data (real names, emails, phone numbers)
   - "mixed": Task wants both methodology and specific data

4. DATA FORMAT DETECTION:
   - Look for format clues: "CSV", "JSON", "list format", "table", etc.
   - If format specified, expect specific_data not methodology

CLASSIFICATION RULES:
- "Lista contatti" + "formato CSV" = specific_data + CSV format
- "Research how to find contacts" = methodology
- "Generate contact list with names, emails" = specific_data
- "Strategy for contact generation" = methodology

Respond in JSON format:
{
  "execution_type": "data_collection|planning|content_generation|analysis|validation",
  "requires_tools": true/false,
  "tools_needed": ["WebSearchTool", "FileSearchTool", etc],
  "content_type_expected": "list of contacts|strategy document|email copy|etc",
  "output_specificity": "methodology|specific_data|mixed",
  "expected_data_format": "CSV|JSON|structured_list|null",
  "ai_reasoning": "why you classified it this way including specificity reasoning",
  "confidence_score": 0.0-1.0
}"""

    def _build_classification_prompt(
        self, 
        task_name: str, 
        task_description: str, 
        workspace_context: Optional[Dict[str, Any]]
    ) -> str:
        """Costruisce prompt specifico per il task"""
        
        prompt = f"""Classify this task for execution:

TASK NAME: {task_name}
TASK DESCRIPTION: {task_description}
"""
        
        if workspace_context:
            prompt += f"\nWORKSPACE CONTEXT: {json.dumps(workspace_context, indent=2)}"
        
        prompt += """

CLASSIFICATION RULES:
- If task mentions "research", "find", "collect", "scrape", "list of" -> likely DATA_COLLECTION
- If task mentions "create", "write", "generate", "design" -> likely CONTENT_GENERATION  
- If task mentions "analyze", "report", "insights", "metrics" -> likely ANALYSIS
- If task mentions "strategy", "plan", "methodology", "structure" -> likely PLANNING
- If task mentions "validate", "check", "verify", "test" -> likely VALIDATION

TOOL REQUIREMENTS:
- DATA_COLLECTION tasks almost always need WebSearchTool
- CONTENT_GENERATION might need research first
- ANALYSIS needs data input
- PLANNING usually doesn't need external tools
- VALIDATION needs access to what's being validated

Classify this task now."""

        return prompt
    
    def _create_fallback_classification(
        self, 
        task_name: str, 
        task_description: str
    ) -> TaskExecutionClassification:
        """Fallback classification quando AI non disponibile"""
        
        # Simple heuristic-based classification
        task_text = f"{task_name} {task_description}".lower()
        
        if any(keyword in task_text for keyword in ["research", "find", "collect", "list", "contacts"]):
            execution_type = TaskExecutionType.DATA_COLLECTION
            requires_tools = True
            tools_needed = ["WebSearchTool"]
        elif any(keyword in task_text for keyword in ["create", "write", "generate", "design"]):
            execution_type = TaskExecutionType.CONTENT_GENERATION
            requires_tools = False
            tools_needed = []
        else:
            execution_type = TaskExecutionType.PLANNING
            requires_tools = False
            tools_needed = []
        
        # Detect output specificity in fallback
        output_specificity = "methodology"
        expected_format = None
        
        if any(fmt in task_text for fmt in ["csv", "json", "formato", "list format"]):
            output_specificity = "specific_data"
            if "csv" in task_text:
                expected_format = "CSV"
            elif "json" in task_text:
                expected_format = "JSON"
        
        return TaskExecutionClassification(
            task_id=f"fallback_{datetime.now().isoformat()}",
            execution_type=execution_type,
            requires_tools=requires_tools,
            tools_needed=tools_needed,
            content_type_expected="unknown",
            output_specificity=output_specificity,
            expected_data_format=expected_format,
            ai_reasoning="Fallback classification due to AI unavailability",
            confidence_score=0.6
        )

# Singleton instance
ai_task_execution_classifier = AITaskExecutionClassifier()

async def classify_task_for_execution(
    task_name: str, 
    task_description: str, 
    workspace_context: Optional[Dict[str, Any]] = None
) -> TaskExecutionClassification:
    """
    🎯 Function helper per classificare task
    """
    return await ai_task_execution_classifier.classify_task_execution(
        task_name, task_description, workspace_context
    )