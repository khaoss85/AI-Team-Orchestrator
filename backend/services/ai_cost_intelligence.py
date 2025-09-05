#!/usr/bin/env python3
"""
AI Cost Intelligence System
Analyzes OpenAI usage patterns to detect inefficiencies, duplicates, and optimization opportunities
"""

import asyncio
import hashlib
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

from utils.openai_client_factory_enhanced import get_enhanced_async_openai_client

logger = logging.getLogger(__name__)

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CostAlert:
    """Intelligent cost optimization alert"""
    id: str
    severity: AlertSeverity
    type: str  # duplicate_calls, model_waste, prompt_bloat, etc.
    title: str
    description: str
    potential_savings: float  # USD per day
    confidence: float  # 0-1
    recommendation: str
    evidence: Dict[str, Any]
    created_at: datetime
    workspace_id: str

@dataclass
class APICallPattern:
    """Pattern analysis for API calls"""
    call_hash: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    call_count: int
    first_seen: datetime
    last_seen: datetime
    cost_estimate: float
    metadata: Dict[str, Any]

class AICostIntelligence:
    """
    Intelligent system for analyzing OpenAI costs and detecting waste
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        
        # Cost analysis windows
        self.analysis_window_minutes = 60  # Analyze last hour
        self.pattern_detection_window = 30  # Pattern detection window
        
        # Storage for pattern analysis
        self.call_patterns: Dict[str, APICallPattern] = {}
        self.recent_calls: deque = deque(maxlen=1000)  # Ring buffer for recent calls
        self.alerts_generated: List[CostAlert] = []
        
        # Cost thresholds (configurable via env)
        self.duplicate_threshold = int(os.getenv("AI_COST_DUPLICATE_THRESHOLD", "3"))
        self.prompt_bloat_threshold = int(os.getenv("AI_COST_PROMPT_BLOAT_THRESHOLD", "2000"))
        self.model_waste_threshold = float(os.getenv("AI_COST_MODEL_WASTE_THRESHOLD", "5.0"))
        
        # Model cost estimates per 1K tokens (updated periodically)
        self.model_costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015}, 
            "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "text-embedding-ada-002": {"input": 0.0001, "output": 0.0}
        }
        
        logger.info(f"🧠 AI Cost Intelligence initialized for workspace: {workspace_id}")
    
    async def analyze_api_call(self, call_data: Dict[str, Any]) -> List[CostAlert]:
        """
        Analyze a single API call for cost inefficiencies
        Returns list of alerts generated
        """
        try:
            # Extract call information
            model = call_data.get('model', 'unknown')
            prompt_tokens = call_data.get('tokens_used', 0)
            completion_tokens = call_data.get('completion_tokens', 0)
            total_tokens = prompt_tokens + completion_tokens
            api_method = call_data.get('api_method', 'unknown')
            success = call_data.get('success', True)
            timestamp = datetime.now()
            
            # Create call fingerprint for duplicate detection
            call_hash = self._generate_call_hash(call_data)
            
            # Update pattern tracking
            self._update_call_patterns(call_hash, model, prompt_tokens, completion_tokens, 
                                     total_tokens, timestamp, call_data)
            
            # Add to recent calls buffer
            self.recent_calls.append({
                'timestamp': timestamp,
                'model': model,
                'tokens': total_tokens,
                'call_hash': call_hash,
                'api_method': api_method,
                'success': success
            })
            
            # Generate alerts based on analysis
            alerts = []
            
            # 1. Duplicate call detection
            duplicate_alerts = await self._detect_duplicate_calls(call_hash, model)
            alerts.extend(duplicate_alerts)
            
            # 2. Model optimization opportunities
            model_alerts = await self._analyze_model_efficiency(model, prompt_tokens, api_method)
            alerts.extend(model_alerts)
            
            # 3. Prompt efficiency analysis
            prompt_alerts = await self._analyze_prompt_efficiency(prompt_tokens, completion_tokens, model)
            alerts.extend(prompt_alerts)
            
            # 4. Cost pattern analysis (runs periodically)
            if len(self.recent_calls) % 50 == 0:  # Every 50 calls
                pattern_alerts = await self._analyze_cost_patterns()
                alerts.extend(pattern_alerts)
            
            # Store alerts
            for alert in alerts:
                self.alerts_generated.append(alert)
            
            # Clean up old data
            self._cleanup_old_data()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error in cost analysis: {e}")
            return []
    
    def _generate_call_hash(self, call_data: Dict[str, Any]) -> str:
        """Generate fingerprint for call to detect duplicates"""
        try:
            # Extract key components that indicate duplicate calls
            model = call_data.get('model', '')
            api_method = call_data.get('api_method', '')
            
            # Try to get prompt content for similarity
            prompt_content = ""
            if 'messages' in call_data:
                # Extract user message content
                messages = call_data.get('messages', [])
                user_messages = [m.get('content', '') for m in messages if m.get('role') == 'user']
                prompt_content = ' '.join(user_messages)[:500]  # First 500 chars
            elif 'input' in call_data:
                prompt_content = str(call_data.get('input', ''))[:500]
            
            # Create hash from key components
            hash_input = f"{model}|{api_method}|{prompt_content}"
            return hashlib.md5(hash_input.encode()).hexdigest()[:12]
            
        except Exception:
            return hashlib.md5(str(call_data).encode()).hexdigest()[:12]
    
    def _update_call_patterns(self, call_hash: str, model: str, prompt_tokens: int, 
                            completion_tokens: int, total_tokens: int, timestamp: datetime,
                            call_data: Dict[str, Any]):
        """Update call pattern tracking"""
        cost_estimate = self._estimate_call_cost(model, prompt_tokens, completion_tokens)
        
        if call_hash in self.call_patterns:
            pattern = self.call_patterns[call_hash]
            pattern.call_count += 1
            pattern.last_seen = timestamp
            pattern.cost_estimate += cost_estimate
            pattern.total_tokens += total_tokens
        else:
            self.call_patterns[call_hash] = APICallPattern(
                call_hash=call_hash,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                call_count=1,
                first_seen=timestamp,
                last_seen=timestamp,
                cost_estimate=cost_estimate,
                metadata=call_data
            )
    
    def _estimate_call_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost of API call in USD"""
        if model not in self.model_costs:
            return 0.0
        
        costs = self.model_costs[model]
        input_cost = (prompt_tokens / 1000) * costs["input"] 
        output_cost = (completion_tokens / 1000) * costs["output"]
        return input_cost + output_cost
    
    async def _detect_duplicate_calls(self, call_hash: str, model: str) -> List[CostAlert]:
        """Detect potentially duplicate API calls"""
        alerts = []
        
        if call_hash in self.call_patterns:
            pattern = self.call_patterns[call_hash]
            
            # Check if we've seen this exact call multiple times recently
            if pattern.call_count >= self.duplicate_threshold:
                # Calculate time window
                time_diff = pattern.last_seen - pattern.first_seen
                if time_diff.total_seconds() < 3600:  # Within 1 hour
                    
                    # Estimate waste
                    duplicate_calls = pattern.call_count - 1  # First call is legitimate
                    potential_savings = (duplicate_calls * pattern.cost_estimate / pattern.call_count) * 24
                    
                    # Generate alert
                    alert = CostAlert(
                        id=f"duplicate_{call_hash}_{int(datetime.now().timestamp())}",
                        severity=AlertSeverity.HIGH if duplicate_calls >= 5 else AlertSeverity.MEDIUM,
                        type="duplicate_calls",
                        title=f"🔄 Duplicate API Calls Detected",
                        description=f"Identical {model} call repeated {pattern.call_count} times in {int(time_diff.total_seconds()/60)} minutes",
                        potential_savings=potential_savings,
                        confidence=0.9,
                        recommendation=f"Consider caching results or adding deduplication logic. Pattern: {call_hash[:8]}",
                        evidence={
                            "call_hash": call_hash,
                            "model": model,
                            "duplicate_count": duplicate_calls,
                            "time_window_minutes": int(time_diff.total_seconds() / 60),
                            "estimated_cost_per_call": pattern.cost_estimate / pattern.call_count
                        },
                        created_at=datetime.now(),
                        workspace_id=self.workspace_id
                    )
                    alerts.append(alert)
        
        return alerts
    
    async def _analyze_model_efficiency(self, model: str, prompt_tokens: int, api_method: str) -> List[CostAlert]:
        """Analyze if a cheaper model could be used"""
        alerts = []
        
        # Skip for non-completion methods
        if api_method not in ['chat.completions', 'completions.create']:
            return alerts
        
        # Model efficiency rules
        efficiency_recommendations = []
        
        # GPT-4 for simple tasks
        if model == "gpt-4" and prompt_tokens < 500:
            cheaper_model = "gpt-4o-mini"
            savings = self._calculate_model_savings("gpt-4", cheaper_model, prompt_tokens, prompt_tokens)
            if savings > 0.01:  # More than 1 cent savings
                efficiency_recommendations.append({
                    "current": model,
                    "recommended": cheaper_model,
                    "daily_savings": savings * 24,
                    "reason": "Simple task suitable for mini model"
                })
        
        # GPT-4o for basic tasks
        elif model == "gpt-4o" and prompt_tokens < 200:
            cheaper_model = "gpt-4o-mini"
            savings = self._calculate_model_savings("gpt-4o", cheaper_model, prompt_tokens, prompt_tokens)
            if savings > 0.005:
                efficiency_recommendations.append({
                    "current": model,
                    "recommended": cheaper_model, 
                    "daily_savings": savings * 24,
                    "reason": "Basic task, mini model sufficient"
                })
        
        # Generate alerts for recommendations
        for rec in efficiency_recommendations:
            alert = CostAlert(
                id=f"model_efficiency_{model}_{int(datetime.now().timestamp())}",
                severity=AlertSeverity.MEDIUM,
                type="model_optimization",
                title=f"💡 Model Optimization Opportunity",
                description=f"Consider using {rec['recommended']} instead of {rec['current']} for this task type",
                potential_savings=rec['daily_savings'],
                confidence=0.7,
                recommendation=f"Switch to {rec['recommended']} for {rec['reason'].lower()}. Test quality first.",
                evidence={
                    "current_model": rec['current'],
                    "recommended_model": rec['recommended'],
                    "prompt_tokens": prompt_tokens,
                    "reasoning": rec['reason']
                },
                created_at=datetime.now(),
                workspace_id=self.workspace_id
            )
            alerts.append(alert)
        
        return alerts
    
    def _calculate_model_savings(self, current_model: str, new_model: str, 
                                input_tokens: int, output_tokens: int) -> float:
        """Calculate daily savings from switching models"""
        current_cost = self._estimate_call_cost(current_model, input_tokens, output_tokens)
        new_cost = self._estimate_call_cost(new_model, input_tokens, output_tokens)
        return max(0, current_cost - new_cost)
    
    async def _analyze_prompt_efficiency(self, prompt_tokens: int, completion_tokens: int, model: str) -> List[CostAlert]:
        """Analyze prompt efficiency"""
        alerts = []
        
        # Prompt bloat detection
        if prompt_tokens > self.prompt_bloat_threshold:
            # Use AI to analyze if prompt is bloated
            bloat_analysis = await self._ai_analyze_prompt_bloat(prompt_tokens, model)
            
            if bloat_analysis.get('is_bloated', False):
                potential_savings = self._estimate_call_cost(model, prompt_tokens * 0.3, 0) * 24  # 30% reduction
                
                alert = CostAlert(
                    id=f"prompt_bloat_{model}_{int(datetime.now().timestamp())}",
                    severity=AlertSeverity.MEDIUM if prompt_tokens > 3000 else AlertSeverity.LOW,
                    type="prompt_inefficiency",
                    title="📝 Prompt Optimization Opportunity",
                    description=f"Prompt with {prompt_tokens} tokens may contain redundant content",
                    potential_savings=potential_savings,
                    confidence=bloat_analysis.get('confidence', 0.6),
                    recommendation="Review prompt for redundancy. Consider: shorter instructions, fewer examples, compressed context.",
                    evidence={
                        "prompt_tokens": prompt_tokens,
                        "model": model,
                        "analysis": bloat_analysis.get('issues', []),
                        "estimated_reduction": "20-40%"
                    },
                    created_at=datetime.now(),
                    workspace_id=self.workspace_id
                )
                alerts.append(alert)
        
        # Token ratio analysis
        if completion_tokens > 0:
            ratio = prompt_tokens / completion_tokens
            if ratio > 10:  # Very high input to output ratio
                alert = CostAlert(
                    id=f"token_ratio_{model}_{int(datetime.now().timestamp())}",
                    severity=AlertSeverity.LOW,
                    type="token_ratio_inefficiency",
                    title="⚖️ High Input/Output Token Ratio",
                    description=f"Ratio {ratio:.1f}:1 suggests potential prompt optimization",
                    potential_savings=self._estimate_call_cost(model, prompt_tokens * 0.2, 0) * 24,
                    confidence=0.5,
                    recommendation="Consider if all prompt content is necessary for generating the output.",
                    evidence={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "ratio": ratio,
                        "model": model
                    },
                    created_at=datetime.now(),
                    workspace_id=self.workspace_id
                )
                alerts.append(alert)
        
        return alerts
    
    async def _ai_analyze_prompt_bloat(self, prompt_tokens: int, model: str) -> Dict[str, Any]:
        """Use AI to analyze if prompt contains bloat (lightweight analysis)"""
        try:
            # Only run this analysis occasionally to avoid costs
            if hasattr(self, '_last_bloat_analysis'):
                time_since = datetime.now() - self._last_bloat_analysis
                if time_since.total_seconds() < 300:  # 5 minutes cooldown
                    return {"is_bloated": False, "confidence": 0.3}
            
            self._last_bloat_analysis = datetime.now()
            
            # Simple heuristic analysis (no API call for now to avoid recursion)
            # Can be enhanced later with actual AI analysis
            is_bloated = prompt_tokens > 2500
            confidence = 0.7 if prompt_tokens > 3000 else 0.5
            
            issues = []
            if prompt_tokens > 2500:
                issues.append("Large prompt size")
            if prompt_tokens > 1000:
                issues.append("Consider prompt compression")
            
            return {
                "is_bloated": is_bloated,
                "confidence": confidence,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Error in prompt bloat analysis: {e}")
            return {"is_bloated": False, "confidence": 0.1}
    
    async def _analyze_cost_patterns(self) -> List[CostAlert]:
        """Analyze broader cost patterns"""
        alerts = []
        
        try:
            # Get recent call data
            recent_window = datetime.now() - timedelta(minutes=self.pattern_detection_window)
            recent_calls = [call for call in self.recent_calls if call['timestamp'] > recent_window]
            
            if len(recent_calls) < 10:  # Need sufficient data
                return alerts
            
            # Analyze patterns
            # 1. Model distribution analysis
            model_usage = defaultdict(int)
            model_costs = defaultdict(float)
            
            for call in recent_calls:
                model = call['model']
                model_usage[model] += 1
                model_costs[model] += self._estimate_call_cost(model, call['tokens'], 0)
            
            # Check for expensive model overuse
            total_calls = sum(model_usage.values())
            for model, count in model_usage.items():
                percentage = (count / total_calls) * 100
                
                if model in ["gpt-4", "gpt-4o"] and percentage > 70:
                    potential_savings = model_costs[model] * 0.5 * 24  # 50% could potentially use cheaper
                    
                    alert = CostAlert(
                        id=f"model_overuse_{model}_{int(datetime.now().timestamp())}",
                        severity=AlertSeverity.MEDIUM,
                        type="cost_pattern",
                        title=f"🎯 High {model} Usage Pattern",
                        description=f"{percentage:.1f}% of calls use expensive {model}",
                        potential_savings=potential_savings,
                        confidence=0.6,
                        recommendation=f"Review if all {model} calls need the premium model. Consider gpt-4o-mini for simpler tasks.",
                        evidence={
                            "model": model,
                            "usage_percentage": percentage,
                            "call_count": count,
                            "cost_contribution": model_costs[model]
                        },
                        created_at=datetime.now(),
                        workspace_id=self.workspace_id
                    )
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error in cost pattern analysis: {e}")
        
        return alerts
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory leaks"""
        cutoff = datetime.now() - timedelta(hours=2)
        
        # Clean old patterns
        old_patterns = [hash_key for hash_key, pattern in self.call_patterns.items() 
                       if pattern.last_seen < cutoff]
        for hash_key in old_patterns:
            del self.call_patterns[hash_key]
        
        # Clean old alerts
        self.alerts_generated = [alert for alert in self.alerts_generated 
                               if alert.created_at > cutoff]
    
    def get_recent_alerts(self, limit: int = 10) -> List[CostAlert]:
        """Get recent cost optimization alerts"""
        # Sort by severity and recency
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        sorted_alerts = sorted(
            self.alerts_generated,
            key=lambda a: (severity_order.get(a.severity.value, 0), a.created_at),
            reverse=True
        )
        
        return sorted_alerts[:limit]
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost analysis summary"""
        recent_window = datetime.now() - timedelta(hours=1)
        recent_calls = [call for call in self.recent_calls if call['timestamp'] > recent_window]
        
        # Calculate metrics
        total_calls = len(recent_calls)
        unique_patterns = len(set(call['call_hash'] for call in recent_calls))
        duplicate_rate = (total_calls - unique_patterns) / total_calls if total_calls > 0 else 0
        
        # Model distribution
        model_dist = defaultdict(int)
        for call in recent_calls:
            model_dist[call['model']] += 1
        
        # Calculate potential savings from alerts
        recent_alerts = [a for a in self.alerts_generated if a.created_at > recent_window]
        potential_daily_savings = sum(alert.potential_savings for alert in recent_alerts)
        
        return {
            "analysis_window_hours": 1,
            "total_calls_analyzed": total_calls,
            "unique_call_patterns": unique_patterns,
            "duplicate_rate_percent": duplicate_rate * 100,
            "model_distribution": dict(model_dist),
            "alerts_generated": len(recent_alerts),
            "potential_daily_savings_usd": potential_daily_savings,
            "efficiency_score": max(0, 100 - (duplicate_rate * 50))  # Simple efficiency metric
        }


# Global manager for cost intelligence per workspace
_cost_intelligence_instances: Dict[str, AICostIntelligence] = {}

def get_cost_intelligence(workspace_id: str) -> AICostIntelligence:
    """Get or create cost intelligence instance for workspace"""
    if workspace_id not in _cost_intelligence_instances:
        _cost_intelligence_instances[workspace_id] = AICostIntelligence(workspace_id)
    return _cost_intelligence_instances[workspace_id]


if __name__ == "__main__":
    # Test the cost intelligence system
    import asyncio
    
    async def test_cost_intelligence():
        ci = AICostIntelligence("test_workspace")
        
        # Simulate API calls
        test_calls = [
            {
                "model": "gpt-4", 
                "tokens_used": 500,
                "completion_tokens": 100,
                "api_method": "chat.completions",
                "success": True,
                "messages": [{"role": "user", "content": "Hello world"}]
            },
            # Duplicate call
            {
                "model": "gpt-4", 
                "tokens_used": 500,
                "completion_tokens": 100,
                "api_method": "chat.completions", 
                "success": True,
                "messages": [{"role": "user", "content": "Hello world"}]
            }
        ]
        
        for call in test_calls:
            alerts = await ci.analyze_api_call(call)
            for alert in alerts:
                print(f"🚨 {alert.severity.upper()}: {alert.title}")
                print(f"   💰 Potential savings: ${alert.potential_savings:.4f}/day")
                print(f"   💡 {alert.recommendation}")
                print()
        
        summary = ci.get_cost_summary()
        print(f"📊 Cost Analysis Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    asyncio.run(test_cost_intelligence())