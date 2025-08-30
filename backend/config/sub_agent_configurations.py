"""
Sub-Agent Configurations - Enhanced based on Goal Progress Transparency System learnings

Performance Analysis Results:
✅ HIGH PERFORMERS: system-architect, api-contract-guardian, placeholder-police, docs-scribe
✅ IMPROVED: director (unused → effective orchestrator), principles-guardian (ignored → proactive blocker)

Key Success Patterns:
- Director orchestrating 5 agents for complex fixes
- Proactive triggers based on code patterns and context
- Verification chains: implementation → verification → architecture → documentation  
- Clear responsibility separation to prevent overlap
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AgentTriggerType(Enum):
    """Types of triggers that can invoke sub-agents"""
    PROACTIVE = "proactive"  # Automatically triggered by patterns
    REACTIVE = "reactive"    # Triggered by specific requests
    ORCHESTRATED = "orchestrated"  # Triggered by director agent
    VERIFICATION = "verification"  # Triggered in verification chains

class AgentSpecialization(Enum):
    """Agent specialization areas"""
    ARCHITECTURE = "architecture"
    API_DESIGN = "api_design" 
    UX_FRONTEND = "ux_frontend"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    DEPENDENCIES = "dependencies"
    ORCHESTRATION = "orchestration"

class SubAgentConfig(BaseModel):
    """Configuration for a specialized sub-agent"""
    agent_id: str
    name: str
    description: str
    specialization: AgentSpecialization
    
    # Trigger Configuration
    proactive_triggers: List[str] = Field(default_factory=list)
    reactive_keywords: List[str] = Field(default_factory=list)
    file_pattern_triggers: List[str] = Field(default_factory=list)
    
    # Performance Settings
    priority_boost: int = 0  # Based on historical performance
    success_rate: float = 0.0  # Historical success rate
    avg_execution_time: float = 0.0  # Average execution time
    
    # Orchestration Settings
    can_orchestrate_others: bool = False
    works_well_with: List[str] = Field(default_factory=list)
    verification_chain_position: Optional[int] = None
    
    # Responsibility Boundaries
    primary_responsibilities: List[str] = Field(default_factory=list)
    secondary_responsibilities: List[str] = Field(default_factory=list)
    should_not_handle: List[str] = Field(default_factory=list)

class SubAgentOrchestrator:
    """Manages sub-agent configurations and orchestration patterns"""
    
    def __init__(self):
        self.agents = self._initialize_enhanced_agents()
        self.orchestration_patterns = self._define_orchestration_patterns()
    
    def _initialize_enhanced_agents(self) -> Dict[str, SubAgentConfig]:
        """Initialize enhanced sub-agent configurations based on performance learnings"""
        
        agents = {
            # HIGH PERFORMER: Enhanced with clearer triggers
            "system-architect": SubAgentConfig(
                agent_id="system-architect",
                name="System Architect", 
                description="Excellent architecture decisions and UX analysis. Orchestrates technical design decisions.",
                specialization=AgentSpecialization.ARCHITECTURE,
                proactive_triggers=[
                    "component creation or modification",
                    "new API endpoint design", 
                    "database schema changes",
                    "performance bottlenecks identified",
                    "scalability concerns mentioned"
                ],
                reactive_keywords=[
                    "architecture", "design", "structure", "scalability", 
                    "technical debt", "refactor", "system design"
                ],
                file_pattern_triggers=[
                    "*/components/*", "*/api/*", "*/database/*", 
                    "*/models/*", "*/services/*"
                ],
                priority_boost=20,  # High performer bonus
                success_rate=0.92,
                works_well_with=["api-contract-guardian", "performance-optimizer"],
                verification_chain_position=3,  # After implementation, before docs
                primary_responsibilities=[
                    "System architecture and design patterns",
                    "Component structure and relationships", 
                    "Technical feasibility assessment",
                    "Performance and scalability planning"
                ],
                should_not_handle=[
                    "UI/UX specific details", "Content writing", "Dependency management"
                ],
                can_orchestrate_others=True
            ),
            
            # HIGH PERFORMER: Clarified scope (maybe too broad → more focused)
            "api-contract-guardian": SubAgentConfig(
                agent_id="api-contract-guardian",
                name="API Contract Guardian",
                description="Ensures API consistency and frontend integration. Focuses on API contracts, not UI specifics.",
                specialization=AgentSpecialization.API_DESIGN,
                proactive_triggers=[
                    "API endpoint creation or modification",
                    "frontend-backend integration changes",
                    "data model updates affecting APIs",
                    "authentication/authorization changes"
                ],
                reactive_keywords=[
                    "api", "endpoint", "contract", "integration", 
                    "frontend", "backend", "rest", "graphql"
                ],
                file_pattern_triggers=[
                    "*/routes/*", "*/api/*", "*/models/*", 
                    "*/schemas/*", "*/types/*"
                ],
                priority_boost=15,
                success_rate=0.89,
                works_well_with=["system-architect", "frontend-ux-specialist"],
                verification_chain_position=2,  # After implementation
                primary_responsibilities=[
                    "API contract definition and validation",
                    "Frontend-backend integration patterns",
                    "Data flow and transformation logic",
                    "API versioning and compatibility"
                ],
                should_not_handle=[
                    "UI component design", "Performance optimization", "Business logic"
                ]
            ),
            
            # CRITICAL HIGH PERFORMER: Enhanced with better pattern detection
            "placeholder-police": SubAgentConfig(
                agent_id="placeholder-police", 
                name="Placeholder Police",
                description="CRITICAL - Prevents theoretical implementations. Verifies real vs placeholder content with semantic analysis.",
                specialization=AgentSpecialization.QUALITY,
                proactive_triggers=[
                    "any code implementation task",
                    "content generation request", 
                    "data creation or population",
                    "example or template creation",
                    "TODO or placeholder detection"
                ],
                reactive_keywords=[
                    "implement", "create", "generate", "example", 
                    "placeholder", "todo", "dummy", "mock", "fake"
                ],
                file_pattern_triggers=[
                    "*", # Monitor all files for placeholders
                ],
                priority_boost=25,  # Highest priority for critical role
                success_rate=0.95,  # Excellent at catching theoretical content
                works_well_with=["system-architect", "docs-scribe"],
                verification_chain_position=1,  # First verification step
                primary_responsibilities=[
                    "Semantic analysis of placeholder vs real content",
                    "Verification of actual implementation vs theory",
                    "Quality gates for deliverable authenticity",
                    "Prevention of generic/template responses"
                ],
                should_not_handle=[
                    "Architecture design", "Performance optimization", "Documentation writing"
                ]
            ),
            
            # HIGH PERFORMER: Enhanced with significance scoring  
            "docs-scribe": SubAgentConfig(
                agent_id="docs-scribe",
                name="Documentation Scribe",
                description="Proactive documentation with significance scoring. Creates comprehensive, contextual documentation.",
                specialization=AgentSpecialization.DOCUMENTATION,
                proactive_triggers=[
                    "significant implementation completion",
                    "API changes requiring documentation",
                    "complex business logic implementation",
                    "architectural decisions made"
                ],
                reactive_keywords=[
                    "document", "readme", "changelog", "api docs", 
                    "guide", "manual", "specification", "comments"
                ],
                file_pattern_triggers=[
                    "*/docs/*", "README.*", "CHANGELOG.*", 
                    "*.md", "*/api/openapi.*"
                ],
                priority_boost=10,
                success_rate=0.87,
                works_well_with=["system-architect", "api-contract-guardian"],
                verification_chain_position=4,  # Final step in verification chain
                primary_responsibilities=[
                    "Technical documentation creation and maintenance",
                    "API documentation and examples",
                    "Changelog and release notes",
                    "Code comments and inline documentation"
                ],
                should_not_handle=[
                    "Code implementation", "Architecture design", "Testing"
                ]
            ),
            
            # IMPROVED: From ignored → proactive security blocker
            "principles-guardian": SubAgentConfig(
                agent_id="principles-guardian",
                name="Security Principles Guardian", 
                description="Proactively blocks security violations and principle breaches. Enhanced with pattern recognition.",
                specialization=AgentSpecialization.SECURITY,
                proactive_triggers=[
                    "authentication or authorization code changes",
                    "data validation implementation",
                    "file upload or user input handling", 
                    "database query construction",
                    "external API integration"
                ],
                reactive_keywords=[
                    "security", "auth", "permission", "validation",
                    "sanitize", "sql", "xss", "csrf", "vulnerability"
                ],
                file_pattern_triggers=[
                    "*/auth/*", "*/security/*", "*/middleware/*",
                    "*/validation/*", "*/models/*"
                ],
                priority_boost=30,  # Highest priority for security
                success_rate=0.84,  # Improved from being ignored
                works_well_with=["system-architect", "api-contract-guardian"],
                verification_chain_position=1,  # Critical first check
                primary_responsibilities=[
                    "Security vulnerability detection and prevention", 
                    "Authentication and authorization validation",
                    "Data validation and sanitization oversight",
                    "Principle compliance verification"
                ],
                should_not_handle=[
                    "UI design", "Performance optimization", "Documentation"
                ]
            ),
            
            # IMPROVED: From unused → effective orchestrator
            "director": SubAgentConfig(
                agent_id="director",
                name="Multi-Agent Director",
                description="Orchestrates multiple agents for complex fixes. Enhanced orchestration patterns for 5+ agent coordination.", 
                specialization=AgentSpecialization.ORCHESTRATION,
                proactive_triggers=[
                    "complex multi-component changes",
                    "cross-cutting concern implementations",
                    "system-wide refactoring needs",
                    "integration between multiple domains"
                ],
                reactive_keywords=[
                    "orchestrate", "coordinate", "multi-agent", "complex",
                    "system-wide", "comprehensive", "end-to-end"
                ],
                file_pattern_triggers=[],  # Triggered by complexity, not file patterns
                priority_boost=5,  # Moderate priority, delegates to specialists
                success_rate=0.78,  # Improved significantly  
                works_well_with=["system-architect", "api-contract-guardian", "placeholder-police", "docs-scribe"],
                can_orchestrate_others=True,
                primary_responsibilities=[
                    "Multi-agent task orchestration and coordination",
                    "Complex workflow management", 
                    "Agent selection and sequencing",
                    "Cross-domain integration oversight"
                ],
                should_not_handle=[
                    "Direct implementation", "Detailed technical decisions"
                ]
            ),
            
            # NEW SPECIALIST: Based on "Missing Specialists" feedback - Enhanced triggers
            "frontend-ux-specialist": SubAgentConfig(
                agent_id="frontend-ux-specialist",
                name="Frontend UX Specialist",
                description="Dedicated React/Next.js UX expert for component design, user interactions, and frontend architecture.",
                specialization=AgentSpecialization.UX_FRONTEND,
                proactive_triggers=[
                    "React component creation or modification", 
                    "Next.js page or layout implementation",
                    "user interface design and styling",
                    "responsive design and mobile optimization",
                    "accessibility compliance implementation",
                    "user experience and interaction patterns",
                    "frontend state management setup"
                ],
                reactive_keywords=[
                    "ui", "ux", "frontend", "interface", "component", "react", "next.js", "nextjs",
                    "responsive", "accessibility", "user", "design", "tsx", "jsx", "css", "styling",
                    "layout", "page", "navigation", "modal", "form", "button", "hook", "state"
                ],
                file_pattern_triggers=[
                    "*/components/*", "*/ui/*", "*/styles/*", "*/pages/*", "*/app/*",
                    "*.tsx", "*.jsx", "*.css", "*.scss", "*.module.css", "tailwind.config.*"
                ],
                priority_boost=5,  # Increased for better activation
                success_rate=0.0,
                works_well_with=["api-contract-guardian", "system-architect", "placeholder-police"],
                verification_chain_position=2,
                primary_responsibilities=[
                    "React/Next.js component design and implementation",
                    "User experience optimization and interaction design", 
                    "Frontend component architecture and reusability",
                    "Accessibility compliance and responsive design implementation",
                    "UI state management and user interaction patterns"
                ],
                should_not_handle=[
                    "Backend API design", "Database architecture", "Security implementation", "Server-side logic"
                ]
            ),
            
            # NEW SPECIALIST: Performance optimization
            "performance-optimizer": SubAgentConfig(
                agent_id="performance-optimizer",
                name="Performance Optimizer",
                description="Identifies and resolves performance bottlenecks across frontend and backend systems.",
                specialization=AgentSpecialization.PERFORMANCE,
                proactive_triggers=[
                    "large data processing implementation",
                    "database query optimization needs",
                    "frontend rendering performance issues", 
                    "API response time concerns",
                    "memory or CPU intensive operations"
                ],
                reactive_keywords=[
                    "performance", "optimization", "slow", "bottleneck",
                    "memory", "cpu", "latency", "cache", "speed"
                ],
                file_pattern_triggers=[
                    "*/database/*", "*/queries/*", "*/api/*",
                    "*/components/*", "*/hooks/*"
                ],
                priority_boost=0,
                success_rate=0.0, 
                works_well_with=["system-architect", "api-contract-guardian"],
                verification_chain_position=3,
                primary_responsibilities=[
                    "Performance bottleneck identification and resolution",
                    "Database query optimization",
                    "Frontend rendering optimization",
                    "Caching strategy implementation"
                ],
                should_not_handle=[
                    "UI design", "Documentation", "Security validation"
                ]
            ),
            
            # NEW SPECIALIST: Dependency management
            "dependency-guardian": SubAgentConfig(
                agent_id="dependency-guardian",
                name="Dependency Guardian", 
                description="Manages dependencies, updates, compatibility, and version conflicts across the project.",
                specialization=AgentSpecialization.DEPENDENCIES,
                proactive_triggers=[
                    "package.json or requirements.txt changes",
                    "dependency version conflicts",
                    "security vulnerability in dependencies",
                    "breaking changes in external packages"
                ],
                reactive_keywords=[
                    "dependency", "package", "version", "update", 
                    "npm", "pip", "yarn", "conflict", "compatibility"
                ],
                file_pattern_triggers=[
                    "package.json", "requirements.txt", "Pipfile",
                    "yarn.lock", "package-lock.json"
                ],
                priority_boost=0,
                success_rate=0.0,
                works_well_with=["system-architect", "principles-guardian"],
                verification_chain_position=1,  # Early check for compatibility
                primary_responsibilities=[
                    "Dependency management and version control",
                    "Security vulnerability assessment", 
                    "Package compatibility verification",
                    "Breaking change impact analysis"
                ],
                should_not_handle=[
                    "UI implementation", "Business logic", "Performance optimization"
                ]
            )
        }
        
        return agents
    
    def _define_orchestration_patterns(self) -> Dict[str, List[str]]:
        """Define successful orchestration patterns from Goal Progress Transparency System"""
        
        return {
            "complex_implementation": [
                "director",           # Orchestrates the process
                "system-architect",   # Designs the approach  
                "placeholder-police", # Verifies real implementation
                "api-contract-guardian", # Ensures integration consistency
                "docs-scribe"        # Documents the solution
            ],
            
            "security_critical_change": [
                "principles-guardian",    # First security check
                "system-architect",      # Architecture review
                "api-contract-guardian", # API security validation  
                "placeholder-police",    # Implementation verification
                "docs-scribe"           # Security documentation
            ],
            
            "frontend_implementation": [
                "frontend-ux-specialist", # UI/UX design
                "api-contract-guardian",  # Backend integration
                "performance-optimizer",  # Frontend performance
                "placeholder-police",     # Real content verification
                "docs-scribe"            # User documentation
            ],
            
            "performance_optimization": [
                "performance-optimizer",  # Identifies bottlenecks
                "system-architect",      # Architecture improvements
                "dependency-guardian",   # Package optimization
                "placeholder-police",    # Verifies real improvements
                "docs-scribe"           # Performance documentation
            ],
            
            "dependency_update": [
                "dependency-guardian",    # Manages updates
                "principles-guardian",    # Security validation
                "system-architect",      # Impact assessment
                "performance-optimizer", # Performance impact
                "docs-scribe"           # Change documentation
            ]
        }
    
    def get_agent_config(self, agent_id: str) -> Optional[SubAgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_id)
    
    def get_agents_for_specialization(self, specialization: AgentSpecialization) -> List[SubAgentConfig]:
        """Get all agents for a specific specialization"""
        return [agent for agent in self.agents.values() if agent.specialization == specialization]
    
    def get_orchestration_pattern(self, pattern_name: str) -> List[str]:
        """Get agent sequence for a specific orchestration pattern"""
        return self.orchestration_patterns.get(pattern_name, [])
    
    def suggest_agents_for_task(self, task_description: str, file_patterns: List[str] = None) -> List[str]:
        """Suggest appropriate agents for a given task using enhanced pattern matching"""
        
        suggested_agents = []
        task_lower = task_description.lower()
        file_patterns = file_patterns or []
        
        # Score agents based on trigger matches
        agent_scores = {}
        
        for agent_id, config in self.agents.items():
            score = 0
            
            # Check reactive keywords
            for keyword in config.reactive_keywords:
                if keyword in task_lower:
                    score += 10
            
            # Check proactive triggers (semantic matching)
            for trigger in config.proactive_triggers:
                if any(word in task_lower for word in trigger.split()[:2]):  # Match first 2 words
                    score += 15
            
            # Check file pattern matches
            for pattern in config.file_pattern_triggers:
                if any(pattern in fp for fp in file_patterns):
                    score += 20
            
            # Apply performance boost
            score += config.priority_boost
            
            if score > 0:
                agent_scores[agent_id] = score
        
        # Sort by score and return top agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        suggested_agents = [agent_id for agent_id, score in sorted_agents[:5]]  # Top 5
        
        # Always include placeholder-police for implementation tasks
        if any(keyword in task_lower for keyword in ["implement", "create", "generate", "build"]):
            if "placeholder-police" not in suggested_agents:
                suggested_agents.append("placeholder-police")
        
        return suggested_agents
    
    def get_verification_chain_for_agents(self, agent_ids: List[str]) -> List[str]:
        """Order agents according to verification chain positions"""
        
        agents_with_positions = []
        agents_without_positions = []
        
        for agent_id in agent_ids:
            config = self.agents.get(agent_id)
            if config and config.verification_chain_position is not None:
                agents_with_positions.append((agent_id, config.verification_chain_position))
            else:
                agents_without_positions.append(agent_id)
        
        # Sort by chain position
        agents_with_positions.sort(key=lambda x: x[1])
        ordered_agents = [agent_id for agent_id, pos in agents_with_positions]
        
        # Add agents without specific positions at the end
        ordered_agents.extend(agents_without_positions)
        
        return ordered_agents


# Global instance
sub_agent_orchestrator = SubAgentOrchestrator()

# Convenience functions for external use
def get_agent_config(agent_id: str) -> Optional[SubAgentConfig]:
    """Get configuration for a specific agent"""
    return sub_agent_orchestrator.get_agent_config(agent_id)

def suggest_agents_for_task(task_description: str, file_patterns: List[str] = None) -> List[str]:
    """Suggest appropriate agents for a given task"""
    return sub_agent_orchestrator.suggest_agents_for_task(task_description, file_patterns)

def get_orchestration_pattern(pattern_name: str) -> List[str]:
    """Get predefined orchestration pattern"""
    return sub_agent_orchestrator.get_orchestration_pattern(pattern_name)

def get_verification_chain_for_agents(agent_ids: List[str]) -> List[str]:
    """Order agents according to verification chain"""
    return sub_agent_orchestrator.get_verification_chain_for_agents(agent_ids)