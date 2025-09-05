#!/usr/bin/env python3
"""
OpenAI Cost Analysis Tool - Urgent $20 Burn Investigation
Identifies excessive API usage patterns and cost drivers
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Pricing per 1K tokens (approximate as of 2025)
PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},  # $2.50/$10 per 1M tokens
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/$0.60 per 1M tokens  
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},  # Legacy pricing
    "gpt-4": {"input": 0.03, "output": 0.06},  # Most expensive
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}  # Cheapest
}

def analyze_model_usage():
    """Scan codebase for model usage patterns"""
    backend_dir = Path("/Users/pelleri/Documents/ai-team-orchestrator/backend")
    model_usage = {
        "gpt-4o": [],
        "gpt-4o-mini": [],
        "gpt-4-turbo": [],
        "gpt-4": [],
        "gpt-3.5-turbo": []
    }
    
    # Scan Python files for model references
    for py_file in backend_dir.rglob("*.py"):
        try:
            content = py_file.read_text()
            for line_num, line in enumerate(content.split('\n'), 1):
                for model in model_usage.keys():
                    # Look for model assignments
                    if f'"{model}"' in line or f"'{model}'" in line:
                        if "model" in line.lower():
                            model_usage[model].append({
                                "file": str(py_file.relative_to(backend_dir)),
                                "line": line_num,
                                "context": line.strip()[:100]
                            })
        except:
            pass
    
    return model_usage

def identify_high_frequency_services():
    """Identify services that run frequently"""
    services = {
        "auto_recovery": {
            "file": "services/goal_progress_auto_recovery.py",
            "frequency": "Every 5 minutes",
            "model": "gpt-4o-mini",
            "estimated_calls_per_day": 288  # 24 * 60 / 5
        },
        "universal_learning": {
            "file": "services/universal_learning_engine.py",
            "frequency": "Per workspace analysis",
            "model": "gpt-4o (line 239)",  # Expensive model!
            "estimated_calls_per_day": 50  # Assuming moderate usage
        },
        "director_agents": {
            "file": "ai_agents/director.py",
            "frequency": "Per team creation",
            "model": "gpt-4o (14+ instances)",
            "estimated_calls_per_day": 100  # Multiple agents per proposal
        },
        "specialist_agents": {
            "file": "ai_agents/specialist_enhanced.py",
            "frequency": "Per task execution",
            "model": "gpt-4-turbo/gpt-4o",
            "estimated_calls_per_day": 200
        }
    }
    return services

def calculate_cost_estimate():
    """Estimate daily costs based on usage patterns"""
    costs = []
    
    # Auto-recovery (runs every 5 minutes)
    auto_recovery_cost = 288 * 2000 / 1000 * PRICING["gpt-4o-mini"]["input"]  # Assuming 2K tokens per call
    costs.append(("Auto-Recovery (5-min intervals)", auto_recovery_cost))
    
    # Universal Learning Engine (using expensive gpt-4o)
    learning_cost = 50 * 5000 / 1000 * PRICING["gpt-4o"]["input"]  # 5K tokens per analysis
    costs.append(("Universal Learning Engine", learning_cost))
    
    # Director with 14 gpt-4o agents
    director_cost = 100 * 14 * 3000 / 1000 * PRICING["gpt-4o"]["input"]  # 14 agents, 3K tokens each
    costs.append(("Director Multi-Agent System", director_cost))
    
    # Specialist agents
    specialist_cost = 200 * 4000 / 1000 * PRICING["gpt-4o"]["input"]
    costs.append(("Specialist Task Execution", specialist_cost))
    
    return costs

def main():
    print("=" * 80)
    print("URGENT: OpenAI API Cost Analysis - $20 Burn Investigation")
    print("=" * 80)
    print()
    
    # Analyze model usage
    print("🔍 SCANNING FOR MODEL USAGE PATTERNS...")
    model_usage = analyze_model_usage()
    
    print("\n📊 MODEL USAGE BREAKDOWN:")
    print("-" * 40)
    for model, locations in model_usage.items():
        if locations:
            cost_factor = PRICING[model]["input"] / PRICING["gpt-3.5-turbo"]["input"]
            print(f"\n{model} (Cost: {cost_factor:.1f}x vs GPT-3.5):")
            print(f"  Found in {len(locations)} locations")
            # Show top 3 occurrences
            for loc in locations[:3]:
                print(f"  - {loc['file']}:{loc['line']}")
                print(f"    {loc['context']}")
    
    print("\n⚠️  HIGH-FREQUENCY SERVICE ANALYSIS:")
    print("-" * 40)
    services = identify_high_frequency_services()
    for service_name, details in services.items():
        print(f"\n{service_name.upper()}:")
        print(f"  File: {details['file']}")
        print(f"  Frequency: {details['frequency']}")
        print(f"  Model: {details['model']}")
        print(f"  Est. calls/day: {details['estimated_calls_per_day']}")
    
    print("\n💰 ESTIMATED DAILY COST BREAKDOWN:")
    print("-" * 40)
    costs = calculate_cost_estimate()
    total_cost = 0
    for component, cost in costs:
        print(f"{component}: ${cost:.2f}/day")
        total_cost += cost
    
    print(f"\nTOTAL ESTIMATED: ${total_cost:.2f}/day")
    print(f"Monthly projection: ${total_cost * 30:.2f}")
    
    print("\n🚨 CRITICAL FINDINGS:")
    print("-" * 40)
    print("1. Director.py uses GPT-4o for 14+ different agent roles (EXPENSIVE)")
    print("2. Universal Learning Engine uses GPT-4o instead of GPT-4o-mini")
    print("3. Auto-recovery runs every 5 minutes (288 times/day)")
    print("4. Multiple services use GPT-4/GPT-4o when GPT-4o-mini would suffice")
    print("5. No rate limiting on background services")
    
    print("\n💡 IMMEDIATE COST REDUCTION RECOMMENDATIONS:")
    print("-" * 40)
    print("1. URGENT: Switch director.py agents from gpt-4o to gpt-4o-mini")
    print("2. URGENT: Change universal_learning_engine.py line 239 to gpt-4o-mini")
    print("3. Increase auto-recovery interval from 5 min to 30 min")
    print("4. Replace all gpt-4/gpt-4o with gpt-4o-mini except where critical")
    print("5. Implement daily budget caps in quota tracker")
    print("6. Add circuit breaker for runaway API calls")
    print("7. Cache AI responses for repeated patterns")
    
    print("\n📈 POTENTIAL SAVINGS:")
    print("-" * 40)
    mini_cost = total_cost * (PRICING["gpt-4o-mini"]["input"] / PRICING["gpt-4o"]["input"])
    savings = total_cost - mini_cost
    print(f"Current daily cost: ${total_cost:.2f}")
    print(f"With GPT-4o-mini: ${mini_cost:.2f}")
    print(f"Daily savings: ${savings:.2f} ({(savings/total_cost*100):.1f}% reduction)")
    print(f"Monthly savings: ${savings * 30:.2f}")

if __name__ == "__main__":
    main()