"""
Ambiguity Resolver - Intelligent clarification system for conversational AI
Universal system that handles unclear requests across any domain
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
from enum import Enum

from openai import OpenAI

from ..database import get_supabase_client

logger = logging.getLogger(__name__)

class AmbiguityType(Enum):
    """Types of ambiguity that can occur in user requests"""
    MISSING_PARAMETERS = "missing_parameters"
    UNCLEAR_INTENT = "unclear_intent"
    MULTIPLE_INTERPRETATIONS = "multiple_interpretations"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    VAGUE_REFERENCE = "vague_reference"
    INCOMPLETE_SPECIFICATION = "incomplete_specification"

class ClarificationStrategy(Enum):
    """Strategies for resolving ambiguity"""
    ASK_SPECIFIC_QUESTION = "ask_specific_question"
    PROVIDE_OPTIONS = "provide_options"
    SUGGEST_DEFAULT = "suggest_default"
    REQUEST_CONTEXT = "request_context"
    CLARIFY_SCOPE = "clarify_scope"

class AmbiguityResolver:
    """
    Universal ambiguity resolution system that works across any domain.
    Intelligently identifies unclear requests and guides users to specificity.
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.supabase = get_supabase_client()
        self.openai_client = OpenAI()
        
        # Tool parameter requirements
        self.tool_requirements = self._define_tool_requirements()
        
        # Common ambiguity patterns
        self.ambiguity_patterns = self._define_ambiguity_patterns()
        
        # Domain-specific clarification templates
        self.clarification_templates = self._define_clarification_templates()
    
    async def analyze_request(self, user_message: str, intent: str = None, 
                            extracted_params: Dict[str, Any] = None,
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user request for ambiguity and determine if clarification is needed.
        
        Args:
            user_message: Original user message
            intent: Detected intent/action
            extracted_params: Parameters extracted from message
            context: Current workspace context
            
        Returns:
            Analysis result with clarification needs or ready-to-execute signal
        """
        try:
            analysis = {
                "needs_clarification": False,
                "ambiguity_type": None,
                "missing_parameters": [],
                "suggestions": [],
                "clarification_question": None,
                "confidence_score": 1.0,
                "ready_to_execute": False
            }
            
            # 1. Check for missing required parameters
            missing_params = await self._check_missing_parameters(intent, extracted_params or {})
            if missing_params:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": AmbiguityType.MISSING_PARAMETERS.value,
                    "missing_parameters": missing_params,
                    "clarification_question": await self._generate_parameter_question(intent, missing_params),
                    "suggestions": await self._suggest_parameter_values(intent, missing_params, context or {})
                })
                return analysis
            
            # 2. Check for unclear intent
            intent_clarity = await self._analyze_intent_clarity(user_message, intent)
            if not intent_clarity["is_clear"]:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": AmbiguityType.UNCLEAR_INTENT.value,
                    "clarification_question": intent_clarity["question"],
                    "suggestions": intent_clarity["possible_intents"]
                })
                return analysis
            
            # 3. Check for vague references
            vague_refs = await self._detect_vague_references(user_message, context or {})
            if vague_refs:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": AmbiguityType.VAGUE_REFERENCE.value,
                    "clarification_question": await self._generate_reference_question(vague_refs),
                    "suggestions": await self._suggest_specific_references(vague_refs, context or {})
                })
                return analysis
            
            # 4. Check for multiple valid interpretations
            interpretations = await self._find_multiple_interpretations(user_message, intent, extracted_params or {})
            if len(interpretations) > 1:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": AmbiguityType.MULTIPLE_INTERPRETATIONS.value,
                    "clarification_question": "I found multiple ways to interpret your request. Which did you mean?",
                    "suggestions": [{"option": interp["description"], "action": interp["action"]} for interp in interpretations]
                })
                return analysis
            
            # 5. Check for incomplete specifications
            completeness = await self._check_specification_completeness(user_message, intent, extracted_params or {})
            if not completeness["is_complete"]:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": AmbiguityType.INCOMPLETE_SPECIFICATION.value,
                    "clarification_question": completeness["question"],
                    "suggestions": completeness["suggestions"]
                })
                return analysis
            
            # 6. AI-driven ambiguity detection
            ai_analysis = await self._ai_ambiguity_analysis(user_message, intent, extracted_params or {})
            if ai_analysis["has_ambiguity"]:
                analysis.update({
                    "needs_clarification": True,
                    "ambiguity_type": ai_analysis["type"],
                    "clarification_question": ai_analysis["question"],
                    "suggestions": ai_analysis["suggestions"]
                })
                return analysis
            
            # Request is clear and ready to execute
            analysis.update({
                "ready_to_execute": True,
                "confidence_score": 0.95
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
            return {
                "needs_clarification": True,
                "ambiguity_type": AmbiguityType.INSUFFICIENT_CONTEXT.value,
                "clarification_question": "I'm having trouble understanding your request. Could you please provide more details?",
                "error": str(e)
            }
    
    def _define_tool_requirements(self) -> Dict[str, Dict[str, Any]]:
        """
        Define parameter requirements for each tool/action.
        Universal definitions that work across any domain.
        """
        return {
            "modify_budget": {
                "required": ["operation", "amount"],
                "optional": ["reason"],
                "types": {
                    "operation": ["increase", "decrease", "set"],
                    "amount": "number",
                    "reason": "string"
                },
                "validation": {
                    "amount": lambda x: x > 0,
                    "operation": lambda x: x in ["increase", "decrease", "set"]
                }
            },
            
            "create_agent": {
                "required": ["role", "seniority"],
                "optional": ["name", "skills", "description"],
                "types": {
                    "role": "string",
                    "seniority": ["junior", "senior", "expert"],
                    "name": "string",
                    "skills": "list",
                    "description": "string"
                }
            },
            
            "create_deliverable": {
                "required": ["title", "description"],
                "optional": ["type", "priority", "deadline", "assigned_to"],
                "types": {
                    "title": "string",
                    "description": "string",
                    "type": ["document", "design", "code", "analysis", "report"],
                    "priority": ["low", "medium", "high", "critical"],
                    "deadline": "date",
                    "assigned_to": "string"
                }
            },
            
            "create_task": {
                "required": ["title", "description"],
                "optional": ["assigned_to", "priority", "estimated_hours", "type"],
                "types": {
                    "title": "string",
                    "description": "string",
                    "assigned_to": "string",
                    "priority": ["low", "medium", "high", "critical"],
                    "estimated_hours": "number",
                    "type": "string"
                }
            },
            
            "upload_knowledge": {
                "required": ["agent_name", "document_title", "content"],
                "optional": ["document_type", "tags"],
                "types": {
                    "agent_name": "string",
                    "document_title": "string",
                    "content": "string",
                    "document_type": ["text", "pdf", "url", "file"],
                    "tags": "list"
                }
            },
            
            "analyze_team_performance": {
                "required": [],
                "optional": ["time_period", "focus_area"],
                "types": {
                    "time_period": ["last_7_days", "last_30_days", "last_quarter"],
                    "focus_area": ["overall", "productivity", "quality", "collaboration"]
                }
            }
        }
    
    def _define_ambiguity_patterns(self) -> List[Dict[str, Any]]:
        """Define patterns that indicate ambiguity in user messages"""
        return [
            {
                "pattern": r"\b(increase|add|more)\b.*budget",
                "type": AmbiguityType.MISSING_PARAMETERS.value,
                "missing": ["amount"],
                "question": "By how much would you like to increase the budget?"
            },
            {
                "pattern": r"\b(add|create|new)\b.*agent",
                "type": AmbiguityType.MISSING_PARAMETERS.value,
                "missing": ["role", "seniority"],
                "question": "What role and seniority level should the new agent have?"
            },
            {
                "pattern": r"\b(that|this|it|they)\b",
                "type": AmbiguityType.VAGUE_REFERENCE.value,
                "question": "Could you be more specific about what you're referring to?"
            },
            {
                "pattern": r"\b(some|few|several|many)\b",
                "type": AmbiguityType.INCOMPLETE_SPECIFICATION.value,
                "question": "Could you specify the exact number or amount?"
            },
            {
                "pattern": r"\b(soon|later|eventually|sometime)\b",
                "type": AmbiguityType.INCOMPLETE_SPECIFICATION.value,
                "question": "When exactly would you like this to happen?"
            }
        ]
    
    def _define_clarification_templates(self) -> Dict[str, Dict[str, str]]:
        """Define templates for generating clarification questions"""
        return {
            "missing_amount": {
                "question": "What amount would you like to {action}?",
                "suggestions": "Here are some common amounts based on your project:"
            },
            "missing_assignee": {
                "question": "Who should be assigned to this {item_type}?",
                "suggestions": "Here are your available team members:"
            },
            "missing_deadline": {
                "question": "When do you need this {item_type} completed?",
                "suggestions": "Common timeframes for similar work:"
            },
            "unclear_scope": {
                "question": "Could you clarify the scope of this {action}?",
                "suggestions": "Here are some options to consider:"
            },
            "vague_reference": {
                "question": "Which specific {item_type} are you referring to?",
                "suggestions": "Here are the available options:"
            }
        }
    
    async def _check_missing_parameters(self, intent: str, extracted_params: Dict[str, Any]) -> List[str]:
        """Check for missing required parameters for the intended action"""
        if not intent or intent not in self.tool_requirements:
            return []
        
        requirements = self.tool_requirements[intent]
        required_params = requirements.get("required", [])
        
        missing = []
        for param in required_params:
            if param not in extracted_params or extracted_params[param] is None:
                missing.append(param)
        
        return missing
    
    async def _analyze_intent_clarity(self, user_message: str, intent: str) -> Dict[str, Any]:
        """Analyze if the user's intent is clear"""
        if not intent:
            # Use AI to suggest possible intents
            possible_intents = await self._suggest_possible_intents(user_message)
            return {
                "is_clear": False,
                "question": "What would you like me to help you with?",
                "possible_intents": possible_intents
            }
        
        # Check if multiple actions could match
        ambiguous_phrases = [
            ("modify", ["modify_budget", "modify_agent", "modify_task"]),
            ("create", ["create_agent", "create_task", "create_deliverable"]),
            ("delete", ["delete_agent", "delete_task", "delete_deliverable"]),
            ("analyze", ["analyze_team_performance", "analyze_project_status"])
        ]
        
        for phrase, possible_actions in ambiguous_phrases:
            if phrase in user_message.lower() and intent in possible_actions:
                # Check if there are other equally valid interpretations
                other_matches = [action for action in possible_actions if action != intent]
                if other_matches:
                    return {
                        "is_clear": False,
                        "question": f"I see you want to {phrase} something. Could you be more specific?",
                        "possible_intents": [{"action": action, "description": self._get_action_description(action)} for action in possible_actions]
                    }
        
        return {"is_clear": True}
    
    async def _detect_vague_references(self, user_message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect vague references in the message"""
        vague_references = []
        
        # Common vague terms
        vague_patterns = [
            (r"\b(that|this|it)\s+(agent|task|deliverable|project)", "item"),
            (r"\bthe\s+(agent|task|deliverable)", "item"),
            (r"\b(him|her|them)\b", "person"),
            (r"\b(last|first|recent)\s+(one|item)", "item")
        ]
        
        for pattern, ref_type in vague_patterns:
            matches = re.finditer(pattern, user_message, re.IGNORECASE)
            for match in matches:
                vague_references.append({
                    "text": match.group(),
                    "type": ref_type,
                    "position": match.span()
                })
        
        return vague_references
    
    async def _find_multiple_interpretations(self, user_message: str, intent: str, 
                                          extracted_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find multiple valid interpretations of the request"""
        interpretations = []
        
        # Check for ambiguous action words
        if "add" in user_message.lower():
            potential_actions = []
            if "agent" in user_message.lower():
                potential_actions.append({"action": "create_agent", "description": "Create a new team member"})
            if "task" in user_message.lower():
                potential_actions.append({"action": "create_task", "description": "Create a new task"})
            if "budget" in user_message.lower():
                potential_actions.append({"action": "modify_budget", "description": "Increase the budget"})
            
            if len(potential_actions) > 1:
                interpretations = potential_actions
        
        # Check for context-dependent interpretations
        if "improve" in user_message.lower():
            interpretations = [
                {"action": "analyze_team_performance", "description": "Analyze current performance for improvement insights"},
                {"action": "suggest_team_member", "description": "Add team members to improve capabilities"},
                {"action": "create_task", "description": "Create improvement tasks"}
            ]
        
        return interpretations
    
    async def _check_specification_completeness(self, user_message: str, intent: str, 
                                              extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the specification is complete enough to execute"""
        if not intent or intent not in self.tool_requirements:
            return {"is_complete": True}
        
        requirements = self.tool_requirements[intent]
        
        # Check for incomplete specifications based on intent
        if intent == "modify_budget":
            amount = extracted_params.get("amount")
            if amount is None or amount <= 0:
                return {
                    "is_complete": False,
                    "question": "What specific amount would you like to change the budget by?",
                    "suggestions": ["€1000", "€2500", "€5000", "10% increase", "20% increase"]
                }
        
        elif intent == "create_agent":
            role = extracted_params.get("role")
            if not role or len(role.strip()) < 3:
                return {
                    "is_complete": False,
                    "question": "What specific role should the new agent have?",
                    "suggestions": await self._suggest_agent_roles()
                }
        
        elif intent == "create_task":
            title = extracted_params.get("title")
            description = extracted_params.get("description")
            if not title or not description or len(description.strip()) < 10:
                return {
                    "is_complete": False,
                    "question": "Could you provide more details about what this task should accomplish?",
                    "suggestions": ["Include specific deliverables", "Add acceptance criteria", "Specify timeline requirements"]
                }
        
        return {"is_complete": True}
    
    async def _ai_ambiguity_analysis(self, user_message: str, intent: str, 
                                   extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to detect subtle ambiguities"""
        try:
            analysis_prompt = f"""
            Analyze this user request for ambiguity:
            
            MESSAGE: "{user_message}"
            DETECTED INTENT: {intent}
            EXTRACTED PARAMETERS: {extracted_params}
            
            Check for:
            1. Unclear pronouns or references
            2. Missing critical details
            3. Ambiguous quantities or timeframes
            4. Conflicting instructions
            5. Assumptions that need clarification
            
            Respond with JSON:
            {{
                "has_ambiguity": boolean,
                "type": "ambiguity_type",
                "question": "clarification question",
                "suggestions": ["suggestion1", "suggestion2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing text for ambiguity and helping users clarify their requests."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to parse JSON response
            import json
            try:
                result = json.loads(ai_response)
                return result
            except json.JSONDecodeError:
                return {"has_ambiguity": False}
                
        except Exception as e:
            logger.error(f"AI ambiguity analysis failed: {e}")
            return {"has_ambiguity": False}
    
    async def _generate_parameter_question(self, intent: str, missing_params: List[str]) -> str:
        """Generate specific question for missing parameters"""
        if not missing_params:
            return ""
        
        param_questions = {
            "amount": "What amount would you like to specify?",
            "operation": "Would you like to increase, decrease, or set a new value?",
            "role": "What role should this team member have?",
            "seniority": "What seniority level? (junior, senior, or expert)",
            "title": "What should be the title?",
            "description": "Could you provide more details about this?",
            "assigned_to": "Who should be assigned to this?",
            "priority": "What priority level? (low, medium, high, or critical)",
            "deadline": "When should this be completed?",
            "agent_name": "Which team member are you referring to?"
        }
        
        if len(missing_params) == 1:
            param = missing_params[0]
            return param_questions.get(param, f"Could you specify the {param}?")
        
        questions = []
        for param in missing_params[:3]:  # Limit to 3 questions
            questions.append(param_questions.get(param, f"the {param}"))
        
        return f"I need a few more details: {', '.join(questions[:-1])} and {questions[-1]}?"
    
    async def _suggest_parameter_values(self, intent: str, missing_params: List[str], 
                                      context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest possible values for missing parameters"""
        suggestions = []
        
        for param in missing_params:
            if param == "amount" and "budget" in intent:
                current_budget = context.get("budget", {}).get("max_budget", 10000)
                suggestions.extend([
                    {"param": "amount", "value": "1000", "description": "€1,000"},
                    {"param": "amount", "value": "2500", "description": "€2,500"},
                    {"param": "amount", "value": str(int(current_budget * 0.2)), "description": f"20% of current budget (€{int(current_budget * 0.2)})"}
                ])
            
            elif param == "role":
                suggestions.extend([
                    {"param": "role", "value": "developer", "description": "Software Developer"},
                    {"param": "role", "value": "designer", "description": "UI/UX Designer"},
                    {"param": "role", "value": "analyst", "description": "Business Analyst"},
                    {"param": "role", "value": "manager", "description": "Project Manager"}
                ])
            
            elif param == "seniority":
                suggestions.extend([
                    {"param": "seniority", "value": "junior", "description": "Junior (€6/day)"},
                    {"param": "seniority", "value": "senior", "description": "Senior (€10/day)"},
                    {"param": "seniority", "value": "expert", "description": "Expert (€18/day)"}
                ])
            
            elif param == "assigned_to":
                team = context.get("agents", [])
                for agent in team[:5]:  # Limit to 5 suggestions
                    suggestions.append({
                        "param": "assigned_to",
                        "value": agent.get("name", "Unknown"),
                        "description": f"{agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown role')})"
                    })
        
        return suggestions
    
    async def _suggest_possible_intents(self, user_message: str) -> List[Dict[str, str]]:
        """Suggest possible intents based on message content"""
        suggestions = []
        
        message_lower = user_message.lower()
        
        # Budget-related
        if any(word in message_lower for word in ["budget", "money", "cost", "expense"]):
            suggestions.append({"intent": "modify_budget", "description": "Modify project budget"})
            suggestions.append({"intent": "analyze_project_status", "description": "Check budget status"})
        
        # Team-related
        if any(word in message_lower for word in ["team", "agent", "member", "person"]):
            suggestions.append({"intent": "create_agent", "description": "Add new team member"})
            suggestions.append({"intent": "analyze_team_performance", "description": "Analyze team performance"})
        
        # Task-related
        if any(word in message_lower for word in ["task", "work", "todo", "assignment"]):
            suggestions.append({"intent": "create_task", "description": "Create new task"})
        
        # Deliverable-related
        if any(word in message_lower for word in ["deliverable", "output", "result", "document"]):
            suggestions.append({"intent": "create_deliverable", "description": "Create new deliverable"})
        
        # Analysis-related
        if any(word in message_lower for word in ["status", "progress", "how", "report"]):
            suggestions.append({"intent": "analyze_project_status", "description": "Get project status"})
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    async def _suggest_agent_roles(self) -> List[str]:
        """Suggest common agent roles"""
        return [
            "Software Developer",
            "UI/UX Designer", 
            "Business Analyst",
            "Project Manager",
            "Quality Assurance",
            "Content Creator",
            "Marketing Specialist",
            "Data Analyst"
        ]
    
    async def _generate_reference_question(self, vague_refs: List[Dict[str, Any]]) -> str:
        """Generate question to clarify vague references"""
        if not vague_refs:
            return ""
        
        ref_types = set(ref["type"] for ref in vague_refs)
        
        if "item" in ref_types:
            return "Which specific item are you referring to? Could you provide the name or more details?"
        
        if "person" in ref_types:
            return "Which team member are you referring to? Could you provide their name or role?"
        
        return "Could you be more specific about what you're referring to?"
    
    async def _suggest_specific_references(self, vague_refs: List[Dict[str, Any]], 
                                         context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest specific references to replace vague ones"""
        suggestions = []
        
        # Get available items from context
        agents = context.get("agents", [])
        tasks = context.get("recent_tasks", [])
        deliverables = context.get("deliverables", [])
        
        for ref in vague_refs:
            if ref["type"] == "item":
                # Suggest agents
                for agent in agents[:3]:
                    suggestions.append({
                        "type": "agent",
                        "value": agent.get("name", "Unknown"),
                        "description": f"Team member: {agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown role')})"
                    })
                
                # Suggest recent tasks
                for task in tasks[:3]:
                    suggestions.append({
                        "type": "task", 
                        "value": task.get("title", "Unknown"),
                        "description": f"Task: {task.get('title', 'Unknown')}"
                    })
            
            elif ref["type"] == "person":
                # Suggest team members
                for agent in agents:
                    suggestions.append({
                        "type": "agent",
                        "value": agent.get("name", "Unknown"),
                        "description": f"{agent.get('name', 'Unknown')} - {agent.get('role', 'Unknown role')}"
                    })
        
        return suggestions[:6]  # Limit suggestions
    
    def _get_action_description(self, action: str) -> str:
        """Get human-readable description for action"""
        descriptions = {
            "modify_budget": "Change project budget amount",
            "create_agent": "Add new team member",
            "create_task": "Create new task or assignment", 
            "create_deliverable": "Create project deliverable",
            "analyze_project_status": "Get project status report",
            "analyze_team_performance": "Analyze team performance",
            "upload_knowledge": "Add knowledge to team member"
        }
        
        return descriptions.get(action, action.replace("_", " ").title())