# utils/ai_model_optimizer.py
"""
🚨 AI Model Cost Optimizer
Automatically selects cheaper models based on task complexity and cost controls
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SIMPLE = "simple"       # Basic analysis, classification
    MEDIUM = "medium"       # Content generation, semantic matching  
    COMPLEX = "complex"     # Deep reasoning, multi-step analysis

class AIModelOptimizer:
    """Intelligently selects cost-effective models based on task requirements"""
    
    def __init__(self):
        # 🚨 COST CONTROL: Use cheaper models when enabled
        self.use_cheaper_models = os.getenv("USE_CHEAPER_MODELS", "true").lower() == "true"
        self.daily_budget = float(os.getenv("DAILY_OPENAI_BUDGET", "5.0"))
        
        # Model cost estimates (per 1K tokens)
        self.model_costs = {
            "gpt-4o": {"input": 0.005, "output": 0.015},           # Most expensive
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},   # Good balance
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}   # Cheapest
        }
        
        # Model selection by complexity
        self.model_selection = {
            # COST EMERGENCY MODE: Ultra-conservative model selection
            "emergency": {
                TaskComplexity.SIMPLE: "gpt-3.5-turbo",
                TaskComplexity.MEDIUM: "gpt-3.5-turbo", 
                TaskComplexity.COMPLEX: "gpt-4o-mini"  # Only for critical tasks
            },
            # NORMAL MODE: Balanced selection
            "normal": {
                TaskComplexity.SIMPLE: "gpt-3.5-turbo",
                TaskComplexity.MEDIUM: "gpt-4o-mini",
                TaskComplexity.COMPLEX: "gpt-4o"
            }
        }
    
    def select_model(
        self, 
        task_type: str, 
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        estimated_tokens: int = 1000
    ) -> Tuple[str, float]:
        """
        Select the most cost-effective model for a task
        
        Returns:
            Tuple[model_name, estimated_cost]
        """
        # Determine operation mode
        mode = "emergency" if self.use_cheaper_models else "normal"
        
        # Get base model recommendation
        selected_model = self.model_selection[mode][complexity]
        
        # 🚨 EMERGENCY OVERRIDES for specific high-cost functions
        if task_type in ["content_learning", "content_analysis", "insight_extraction"]:
            if self.use_cheaper_models:
                selected_model = "gpt-3.5-turbo"  # Force cheapest for content learning
                logger.warning(f"🚨 COST OVERRIDE: Using {selected_model} for {task_type} (emergency mode)")
        
        # Calculate estimated cost
        model_pricing = self.model_costs[selected_model]
        estimated_cost = (estimated_tokens / 1000) * (model_pricing["input"] + model_pricing["output"])
        
        logger.info(f"💰 Model selection: {selected_model} for {task_type} (~${estimated_cost:.4f})")
        
        return selected_model, estimated_cost
    
    def get_max_tokens_for_budget(self, model: str, remaining_budget: float) -> int:
        """Calculate max tokens we can afford with remaining budget"""
        if model not in self.model_costs:
            return 500  # Conservative default
        
        pricing = self.model_costs[model]
        cost_per_1k_tokens = pricing["input"] + pricing["output"]
        max_tokens = int((remaining_budget / cost_per_1k_tokens) * 1000)
        
        # Apply safety margin
        safe_tokens = int(max_tokens * 0.8)
        
        logger.info(f"💰 Budget check: ${remaining_budget:.2f} = ~{safe_tokens} tokens for {model}")
        return max(100, min(safe_tokens, 4000))  # Min 100, max 4000 tokens
    
    def should_skip_ai_call(self, task_type: str, estimated_cost: float) -> bool:
        """Determine if we should skip an AI call to preserve budget"""
        if task_type in ["content_learning", "insight_extraction", "content_analysis"]:
            if self.use_cheaper_models:
                logger.warning(f"🚨 SKIPPING: {task_type} call blocked in cost emergency mode")
                return True
        
        # Skip if cost exceeds 10% of daily budget
        if estimated_cost > (self.daily_budget * 0.1):
            logger.warning(f"🚨 SKIPPING: ${estimated_cost:.4f} exceeds 10% of daily budget")
            return True
        
        return False

# Global optimizer instance
ai_model_optimizer = AIModelOptimizer()

def get_cost_optimized_model(
    task_type: str,
    complexity: str = "medium", 
    estimated_tokens: int = 1000
) -> Tuple[str, Optional[int]]:
    """
    Get the most cost-effective model and token limit for a task
    
    Returns:
        Tuple[model_name, max_tokens] or Tuple[None, None] if should skip
    """
    try:
        complexity_enum = TaskComplexity(complexity.lower())
    except ValueError:
        complexity_enum = TaskComplexity.MEDIUM
    
    model, estimated_cost = ai_model_optimizer.select_model(
        task_type, complexity_enum, estimated_tokens
    )
    
    # Check if we should skip this call entirely
    if ai_model_optimizer.should_skip_ai_call(task_type, estimated_cost):
        return None, None
    
    # Get token limit based on budget
    remaining_budget = ai_model_optimizer.daily_budget - (estimated_cost * 10)  # Conservative estimate
    max_tokens = ai_model_optimizer.get_max_tokens_for_budget(model, max(remaining_budget, 1.0))
    
    return model, max_tokens

def log_model_cost_savings():
    """Log the cost savings from model optimization"""
    if ai_model_optimizer.use_cheaper_models:
        logger.info("💰 COST SAVINGS: Using cheaper models - estimated 60-70% cost reduction")
        logger.info("📊 Model strategy: GPT-3.5-turbo for basic tasks, GPT-4o-mini for complex only")
    else:
        logger.info("💰 Normal model selection active - balanced cost vs performance")