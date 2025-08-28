"""
Sub-Agent Integration - Integrates enhanced sub-agent orchestration with existing conversational system

This module provides the bridge between the conversational AI and the specialized sub-agent orchestrator,
implementing refined responsibility boundaries and eliminating overlap.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from services.enhanced_sub_agent_orchestrator import (
    enhanced_orchestrator,
    orchestrate_task,
    OrchestrationResult
)
from config.sub_agent_configurations import (
    sub_agent_orchestrator,
    AgentSpecialization,
    suggest_agents_for_task
)

logger = logging.getLogger(__name__)

class ResponsibilityMatrix:
    """
    Defines clear responsibility boundaries to eliminate agent overlap
    """
    
    # Primary responsibility mappings - each agent owns these completely
    PRIMARY_RESPONSIBILITIES = {
        "system-architect": [
            "system_architecture", "component_design", "technical_patterns",
            "scalability_planning", "integration_architecture"
        ],
        "api-contract-guardian": [
            "api_contract_design", "api_versioning", "data_transformation",
            "frontend_backend_integration", "api_consistency"
        ],
        "placeholder-police": [
            "content_verification", "implementation_validation", "quality_gates",
            "fake_content_detection", "deliverable_authenticity"
        ],
        "docs-scribe": [
            "technical_documentation", "api_documentation", "changelog_management",
            "code_commenting", "user_guides"
        ],
        "principles-guardian": [
            "security_validation", "vulnerability_assessment", "principle_compliance",
            "authentication_review", "data_protection"
        ],
        "director": [
            "multi_agent_orchestration", "workflow_coordination", "agent_selection",
            "complex_task_management", "cross_domain_integration"
        ],
        "frontend-ux-specialist": [
            "ui_component_design", "user_experience_optimization", "accessibility",
            "responsive_design", "frontend_patterns"
        ],
        "performance-optimizer": [
            "performance_analysis", "bottleneck_identification", "optimization_strategies",
            "performance_monitoring", "resource_efficiency"
        ],
        "dependency-guardian": [
            "dependency_management", "version_compatibility", "security_scanning",
            "package_lifecycle", "breaking_change_analysis"
        ]
    }
    
    # Collaboration rules - agents that should work together
    COLLABORATION_RULES = {
        "system-architect": {
            "collaborates_with": ["api-contract-guardian", "performance-optimizer"],
            "defers_to": ["principles-guardian"],  # Security has higher priority
            "supervises": ["frontend-ux-specialist"]  # Provides architectural guidance
        },
        "api-contract-guardian": {
            "collaborates_with": ["system-architect", "frontend-ux-specialist"],
            "defers_to": ["principles-guardian"],
            "validates": ["placeholder-police"]  # Ensures API implementations are real
        },
        "placeholder-police": {
            "validates": ["all"],  # Can validate any agent's output
            "critical_for": ["implementation", "content_generation", "data_creation"],
            "escalates_to": ["director"]  # Complex issues go to orchestrator
        },
        "principles-guardian": {
            "overrides": ["all"],  # Security concerns override all other considerations
            "critical_for": ["security", "auth", "validation", "compliance"],
            "collaborates_with": ["dependency-guardian"]  # Security + dependency scanning
        },
        "director": {
            "orchestrates": ["all"],
            "delegates_to": ["all"], 
            "coordinates": ["complex_multi_agent_tasks"]
        }
    }
    
    # Escalation paths - when agents need help
    ESCALATION_PATHS = {
        "conflict_resolution": "director",
        "security_concerns": "principles-guardian",
        "architecture_questions": "system-architect", 
        "api_integration_issues": "api-contract-guardian",
        "implementation_validation": "placeholder-police",
        "documentation_needs": "docs-scribe",
        "performance_problems": "performance-optimizer",
        "dependency_conflicts": "dependency-guardian",
        "ux_concerns": "frontend-ux-specialist"
    }

    @classmethod
    def get_primary_agent_for_responsibility(cls, responsibility: str) -> Optional[str]:
        """Get the primary agent responsible for a specific area"""
        for agent, responsibilities in cls.PRIMARY_RESPONSIBILITIES.items():
            if responsibility in responsibilities:
                return agent
        return None
    
    @classmethod
    def get_collaboration_partners(cls, agent_id: str) -> List[str]:
        """Get agents that should collaborate with the given agent"""
        rules = cls.COLLABORATION_RULES.get(agent_id, {})
        return rules.get("collaborates_with", [])
    
    @classmethod
    def should_escalate_to(cls, concern_type: str) -> Optional[str]:
        """Get the agent to escalate a specific concern to"""
        return cls.ESCALATION_PATHS.get(concern_type)

class ConversationalSubAgentBridge:
    """
    Bridges the conversational AI system with the sub-agent orchestrator
    """
    
    def __init__(self):
        self.responsibility_matrix = ResponsibilityMatrix()
        self.active_orchestrations: Dict[str, OrchestrationResult] = {}
    
    async def should_invoke_sub_agents(self, user_message: str, workspace_context: Dict[str, Any]) -> Tuple[bool, List[str], str]:
        """
        Determine if sub-agents should be invoked and which ones
        
        Returns:
            (should_invoke, agent_list, orchestration_pattern)
        """
        message_lower = user_message.lower()
        
        # Check for explicit sub-agent invocation patterns
        explicit_triggers = [
            "architect", "design", "implement", "security", "performance",
            "document", "api", "frontend", "backend", "complex", "system"
        ]
        
        has_explicit_trigger = any(trigger in message_lower for trigger in explicit_triggers)
        
        # Check for complex task indicators
        complexity_indicators = [
            "multiple", "system", "integration", "architecture", "comprehensive",
            "end-to-end", "full", "complete", "complex"
        ]
        
        is_complex = any(indicator in message_lower for indicator in complexity_indicators)
        
        # Check for implementation requests
        implementation_indicators = [
            "implement", "create", "build", "develop", "generate", "make"
        ]
        
        is_implementation = any(indicator in message_lower for indicator in implementation_indicators)
        
        # Decision logic
        should_invoke = has_explicit_trigger or is_complex or is_implementation
        
        if not should_invoke:
            return False, [], "none"
        
        # Suggest appropriate agents
        suggested_agents = suggest_agents_for_task(user_message)
        
        # Determine orchestration pattern
        orchestration_pattern = self._determine_orchestration_pattern(user_message, workspace_context)
        
        return True, suggested_agents, orchestration_pattern
    
    def _determine_orchestration_pattern(self, message: str, context: Dict[str, Any]) -> str:
        """Determine the most appropriate orchestration pattern"""
        message_lower = message.lower()
        
        # Security-related requests
        if any(word in message_lower for word in ["security", "auth", "permission", "vulnerability"]):
            return "security_critical_change"
        
        # Frontend/UI requests  
        if any(word in message_lower for word in ["ui", "ux", "frontend", "interface", "component"]):
            return "frontend_implementation"
        
        # Performance requests
        if any(word in message_lower for word in ["performance", "optimize", "slow", "bottleneck"]):
            return "performance_optimization"
        
        # Dependency requests
        if any(word in message_lower for word in ["dependency", "package", "update", "version"]):
            return "dependency_update"
        
        # Complex system requests
        if any(word in message_lower for word in ["system", "architecture", "complex", "integration"]):
            return "complex_implementation"
        
        return "custom"
    
    async def execute_sub_agent_orchestration(
        self,
        user_message: str,
        workspace_id: str,
        task_id: str = None,
        thinking_callback=None
    ) -> OrchestrationResult:
        """
        Execute sub-agent orchestration for a user request
        """
        
        # Check if orchestration is needed
        should_invoke, suggested_agents, pattern = await self.should_invoke_sub_agents(user_message, {})
        
        if not should_invoke:
            return OrchestrationResult(
                success=False,
                orchestration_metadata={"reason": "No sub-agent orchestration needed"}
            )
        
        if thinking_callback:
            await thinking_callback({
                "type": "thinking_step",
                "step": "sub_agent_planning",
                "title": "🎭 Planning Sub-Agent Orchestration",
                "description": f"Pattern: {pattern} | Agents: {', '.join(suggested_agents[:3])}{'...' if len(suggested_agents) > 3 else ''}",
                "status": "in_progress"
            })
        
        # Execute orchestration
        result = await orchestrate_task(
            task_description=user_message,
            workspace_id=workspace_id,
            task_id=task_id,
            orchestration_pattern=pattern,
            thinking_callback=thinking_callback
        )
        
        # Store active orchestration for reference
        if task_id:
            self.active_orchestrations[task_id] = result
        
        return result
    
    def format_orchestration_result(self, result: OrchestrationResult) -> str:
        """
        Format orchestration result for conversational response
        """
        if not result.success:
            return f"🚨 Sub-agent orchestration encountered issues: {result.orchestration_metadata.get('error', 'Unknown error')}"
        
        response_parts = []
        
        # Header
        pattern = result.orchestration_metadata.get('pattern_used', 'custom')
        agents_count = result.orchestration_metadata.get('agents_count', 0)
        execution_time = result.orchestration_metadata.get('execution_time', 0)
        
        response_parts.append(f"🎭 **Sub-Agent Orchestration Complete**")
        response_parts.append(f"Pattern: {pattern.replace('_', ' ').title()} | Agents: {agents_count} | Time: {execution_time:.1f}s")
        response_parts.append("")
        
        # Agent results summary
        successful_agents = []
        failed_agents = []
        
        for agent_id, agent_result in result.agent_results.items():
            if agent_result.get("success", False):
                successful_agents.append(agent_id)
            else:
                failed_agents.append(agent_id)
        
        if successful_agents:
            response_parts.append("✅ **Successful Agents:**")
            for agent_id in successful_agents:
                agent_config = sub_agent_orchestrator.get_agent_config(agent_id)
                agent_name = agent_config.name if agent_config else agent_id
                agent_result = result.agent_results[agent_id]
                execution_time = agent_result.get("execution_time", 0)
                response_parts.append(f"  • **{agent_name}** ({execution_time:.1f}s)")
        
        if failed_agents:
            response_parts.append("")
            response_parts.append("❌ **Failed Agents:**")
            for agent_id in failed_agents:
                agent_config = sub_agent_orchestrator.get_agent_config(agent_id)
                agent_name = agent_config.name if agent_config else agent_id
                agent_result = result.agent_results[agent_id]
                error = agent_result.get("error", "Unknown error")
                response_parts.append(f"  • **{agent_name}**: {error[:100]}...")
        
        # Key outputs
        response_parts.append("")
        response_parts.append("🎯 **Key Outputs:**")
        
        # Collect meaningful outputs from successful agents
        for agent_id in successful_agents[:3]:  # Show top 3
            agent_result = result.agent_results[agent_id].get("result", {})
            agent_config = sub_agent_orchestrator.get_agent_config(agent_id)
            agent_name = agent_config.name if agent_config else agent_id
            
            if agent_result:
                # Extract the most relevant information
                key_output = self._extract_key_output(agent_result)
                if key_output:
                    response_parts.append(f"  • **{agent_name}**: {key_output}")
        
        # Verification status
        if result.verification_chain_completed:
            response_parts.append("")
            response_parts.append("🔍 **Quality Verification**: ✅ Complete")
        
        return "\n".join(response_parts)
    
    def _extract_key_output(self, agent_result: Dict[str, Any]) -> str:
        """Extract the most relevant output from an agent result"""
        
        # Try to find meaningful summary information
        if "verification_result" in agent_result:
            return agent_result["verification_result"]
        
        if "architecture_recommendations" in agent_result:
            recs = agent_result["architecture_recommendations"]
            return f"{len(recs)} architecture recommendations provided"
        
        if "api_contracts" in agent_result:
            return f"API contracts validated: {agent_result['api_contracts'].get('rest_endpoints', 'Unknown status')}"
        
        if "documentation_generated" in agent_result:
            return "Technical documentation generated"
        
        if "orchestration_plan" in agent_result:
            return f"Orchestration plan created with {len(agent_result['orchestration_plan'])} phases"
        
        # Generic fallback
        if "analysis" in agent_result:
            return agent_result["analysis"][:100] + "..." if len(agent_result["analysis"]) > 100 else agent_result["analysis"]
        
        return "Analysis completed successfully"
    
    def get_active_orchestrations(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all active orchestrations"""
        summary = {}
        
        for task_id, result in self.active_orchestrations.items():
            summary[task_id] = {
                "success": result.success,
                "pattern": result.orchestration_metadata.get("pattern_used", "unknown"),
                "agents_count": result.orchestration_metadata.get("agents_count", 0),
                "execution_time": result.orchestration_metadata.get("execution_time", 0),
                "verification_complete": result.verification_chain_completed
            }
        
        return summary

# Global instance for integration with conversational system
sub_agent_bridge = ConversationalSubAgentBridge()

# Convenience functions for integration
async def should_invoke_sub_agents(user_message: str, workspace_context: Dict[str, Any]) -> Tuple[bool, List[str], str]:
    """Check if sub-agents should be invoked for a user message"""
    return await sub_agent_bridge.should_invoke_sub_agents(user_message, workspace_context)

async def execute_sub_agent_orchestration(
    user_message: str, 
    workspace_id: str, 
    task_id: str = None, 
    thinking_callback=None
) -> OrchestrationResult:
    """Execute sub-agent orchestration"""
    return await sub_agent_bridge.execute_sub_agent_orchestration(user_message, workspace_id, task_id, thinking_callback)

def format_orchestration_result(result: OrchestrationResult) -> str:
    """Format orchestration result for display"""
    return sub_agent_bridge.format_orchestration_result(result)