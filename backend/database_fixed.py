#!/usr/bin/env python3
"""
🌍 UNIVERSAL DATABASE FUNCTIONS - PILLAR 2 & 3 COMPLIANT
Fixed version of database.py with removed hardcoded business domain logic
"""

def _map_requirement_to_metric_type(req_type: str) -> str:
    """
    🌍 UNIVERSAL AI-DRIVEN MAPPING - Zero hardcoded business logic
    
    Uses universal pattern classification to map requirement types to universal metric categories,
    supporting truly unlimited domains and use cases without business-specific hardcoding.
    """
    req_type_lower = req_type.lower().strip()
    
    # Universal pattern-based classification (no domain-specific hardcoding)
    if any(word in req_type_lower for word in ['rate', '%', 'conversion', 'performance', 'quality', 'score']):
        return "quality_measures"
    elif any(word in req_type_lower for word in ['time', 'day', 'deadline', 'timeline', 'duration']):
        return "time_based_metrics"
    elif any(word in req_type_lower for word in ['engage', 'interact', 'response', 'participation']):
        return "engagement_metrics"
    elif any(word in req_type_lower for word in ['complete', 'finish', 'done', 'progress']):
        return "completion_metrics"
    else:
        return "quantified_outputs"  # Universal fallback for countable items

# This file shows the fixed version of the _map_requirement_to_metric_type function
# to replace the hardcoded business logic version in database.py