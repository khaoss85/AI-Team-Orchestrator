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
        workspace_context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None
    ) -> TaskExecutionClassification:
        """
        🎯 Classifica un task per determinare il tipo di execution
        """
        
        logger.info(f"🧠 AI classifying task execution: {task_name}")
        
        # 🔧 HOLISTIC: Get available tools first to inform classification
        if available_tools is None:
            available_tools = await self._detect_available_tools(workspace_context)
        
        # Costruisci prompt AI-driven con tool context
        classification_prompt = self._build_classification_prompt(
            task_name, task_description, workspace_context, available_tools
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

    async def _detect_available_tools(self, workspace_context: Optional[Dict[str, Any]]) -> List[str]:
        """🔧 Detect available tools in workspace to inform classification with fallback awareness"""
        available_tools = []
        tool_capabilities = {}
        
        try:
            # Check MCP tools availability with graceful fallback awareness
            from services.mcp_tool_discovery import get_mcp_tools_for_agent
            workspace_id = workspace_context.get("workspace_id") if workspace_context else None
            
            if workspace_id:
                # Get available tools (including fallback tools)
                discovered_tools = await get_mcp_tools_for_agent(
                    agent_name="classifier_agent",
                    domain="data_analysis",  # Generic domain for classification
                    workspace_id=workspace_id
                )
                
                # 🔧 CRITICAL: Analyze tool types to understand capabilities
                mcp_tools_available = False
                fallback_only = False
                
                for tool in discovered_tools:
                    tool_name = tool.get("name", "unknown")
                    tool_type = tool.get("tool_type", "mcp")
                    is_fallback = tool.get("fallback_tool", False)
                    
                    available_tools.append(tool_name)
                    tool_capabilities[tool_name] = {
                        "type": tool_type,
                        "is_fallback": is_fallback,
                        "capabilities": tool.get("capabilities", [])
                    }
                    
                    if tool_type == "mcp" and not is_fallback:
                        mcp_tools_available = True
                    elif is_fallback:
                        fallback_only = True
                
                # 🧠 INTELLIGENT CLASSIFICATION: Store tool context for smart classification
                if workspace_context:
                    workspace_context["tool_analysis"] = {
                        "mcp_available": mcp_tools_available,
                        "fallback_only": fallback_only,
                        "tool_capabilities": tool_capabilities,
                        "real_data_tools_count": sum(1 for tool in discovered_tools 
                                                  if not tool.get("fallback_tool", False) 
                                                  and "web_search" in tool.get("capabilities", [])),
                        "content_generation_mode": fallback_only and not mcp_tools_available
                    }
                
                logger.info(f"🔧 Tool analysis: MCP={mcp_tools_available}, Fallback={fallback_only}, Real data tools={workspace_context.get('tool_analysis', {}).get('real_data_tools_count', 0)}")
            
            # Always include basic SDK tools in the list (they might be fallback or real)
            if "WebSearchTool" not in available_tools:
                available_tools.append("WebSearchTool")
            if "FileSearchTool" not in available_tools:
                available_tools.append("FileSearchTool")
            
        except Exception as e:
            logger.warning(f"Failed to detect available tools: {e}")
            # Ultimate fallback
            available_tools = ["WebSearchTool", "FileSearchTool"]
            if workspace_context:
                workspace_context["tool_analysis"] = {
                    "mcp_available": False,
                    "fallback_only": True,
                    "content_generation_mode": True,
                    "real_data_tools_count": 0,
                    "error": str(e)
                }
        
        logger.info(f"🔧 Detected {len(available_tools)} available tools: {available_tools}")
        return available_tools

    def _build_classification_prompt(
        self, 
        task_name: str, 
        task_description: str, 
        workspace_context: Optional[Dict[str, Any]],
        available_tools: List[str] = None
    ) -> str:
        """Costruisce prompt specifico per il task"""
        
        available_tools_str = ", ".join(available_tools) if available_tools else "None detected"
        
        # 🧠 CRITICAL: Include tool analysis for intelligent fallback-aware classification
        tool_analysis = workspace_context.get("tool_analysis", {}) if workspace_context else {}
        content_generation_mode = tool_analysis.get("content_generation_mode", False)
        real_data_tools_count = tool_analysis.get("real_data_tools_count", 0)
        
        prompt = f"""Classify this task for execution considering available tools and their capabilities:

TASK NAME: {task_name}
TASK DESCRIPTION: {task_description}

AVAILABLE TOOLS: {available_tools_str}
REAL DATA COLLECTION TOOLS: {real_data_tools_count} tools capable of collecting authentic data
CONTENT GENERATION MODE: {"ACTIVE - Use this for tasks requiring specific data" if content_generation_mode else "INACTIVE - Real data tools available"}
"""
        
        if workspace_context:
            # Include filtered context (remove tool_capabilities to avoid JSON issues)
            filtered_context = {k: v for k, v in workspace_context.items() if k != "tool_analysis"}
            if filtered_context:
                prompt += f"\nWORKSPACE CONTEXT: {json.dumps(filtered_context, indent=2)}"
            
            if tool_analysis:
                prompt += f"\nTOOL CAPABILITY ANALYSIS: MCP available={tool_analysis.get('mcp_available', False)}, Fallback only={tool_analysis.get('fallback_only', True)}"
        
        prompt += f"""

🔧 TOOL-AWARE CLASSIFICATION RULES WITH GRACEFUL FALLBACK:

CRITICAL: Consider both available tools AND their capabilities when classifying!

1. DATA_COLLECTION Classification (STRICT REQUIREMENTS):
   - Only classify as DATA_COLLECTION if REAL DATA COLLECTION TOOLS > 0
   - WebSearchTool must be a real search tool, not a fallback simulation
   - Task asks for specific, authentic data (emails, phone numbers, real company info)
   
2. CONTENT_GENERATION Classification (SMART FALLBACK):
   - Use when CONTENT GENERATION MODE = ACTIVE 
   - Use when task asks for specific data but only fallback tools available
   - Can create realistic examples, templates, structured formats without real data
   - Better to deliver well-structured templates than failed data collection
   
3. GRACEFUL FALLBACK INTELLIGENCE:
   - If REAL DATA TOOLS = 0 but task asks for "contact list"
     → CONTENT_GENERATION with "realistic contact template in CSV format"
   - If CONTENT GENERATION MODE = ACTIVE and task asks for "research"
     → CONTENT_GENERATION with "research methodology and structured findings template"
   - If fallback tools only, focus on methodology and structured formats
   
4. KEYWORD PATTERNS (UPDATED FOR FALLBACK):
   - "research", "find", "collect", "list of" + REAL DATA TOOLS > 0 → DATA_COLLECTION
   - "research", "find", "collect", "list of" + REAL DATA TOOLS = 0 → CONTENT_GENERATION
   - "create", "write", "generate", "design" → CONTENT_GENERATION (always)
   - "analyze", "report", "insights" → ANALYSIS (can work with generated content)
   - "strategy", "plan", "methodology" → PLANNING (doesn't need real data)

🎯 GRACEFUL INTELLIGENCE: Deliver business value even with limited tools!
When real data tools aren't available, create high-quality structured content that provides immediate business utility.

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
    workspace_context: Optional[Dict[str, Any]] = None,
    available_tools: Optional[List[str]] = None
) -> TaskExecutionClassification:
    """
    🎯 Function helper per classificare task
    """
    return await ai_task_execution_classifier.classify_task_execution(
        task_name, task_description, workspace_context, available_tools
    )