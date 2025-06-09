"""
JSON Cleaning Utilities
Handles malformed JSON from AI responses and cleans them for proper parsing
"""

import json
import re
import logging

logger = logging.getLogger(__name__)

def clean_and_parse_json(json_string: str) -> dict:
    """
    Clean and parse potentially malformed JSON string
    
    Args:
        json_string: Raw JSON string that might have formatting issues
        
    Returns:
        Parsed dictionary or None if parsing fails
    """
    if not json_string:
        return None
    
    try:
        # Try normal parsing first
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.warning(f"Initial JSON parse failed: {e}")
        
        # Try cleaning the JSON
        cleaned_json = clean_json_string(json_string)
        
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e2:
            logger.error(f"JSON parse failed even after cleaning: {e2}")
            logger.error(f"Problematic JSON around position {e2.pos if hasattr(e2, 'pos') else 'unknown'}")
            return None

def clean_json_string(json_string: str) -> str:
    """
    Clean common JSON formatting issues
    
    Args:
        json_string: Raw JSON string
        
    Returns:
        Cleaned JSON string
    """
    # Remove any leading/trailing whitespace
    cleaned = json_string.strip()
    
    # Fix unescaped quotes in string values
    # This regex finds quoted strings and escapes internal quotes
    def escape_quotes_in_strings(match):
        content = match.group(1)
        # Escape any unescaped quotes within the string
        content = content.replace('"', '\\"')
        # But don't double-escape already escaped quotes
        content = content.replace('\\\\"', '\\"')
        return f'"{content}"'
    
    # Pattern to match string values (content between quotes)
    # This is a simplified approach - for production, consider a proper JSON parser
    cleaned = re.sub(r'"([^"]*(?:\\"[^"]*)*)"', escape_quotes_in_strings, cleaned)
    
    # Fix trailing commas before closing brackets/braces
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    
    # Fix missing commas between objects/arrays (common AI mistake)
    cleaned = re.sub(r'}\s*{', '}, {', cleaned)
    cleaned = re.sub(r']\s*\[', '], [', cleaned)
    cleaned = re.sub(r'}\s*\[', '}, [', cleaned)
    cleaned = re.sub(r']\s*{', '], {', cleaned)
    
    # Fix missing quotes around unquoted keys
    cleaned = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
    
    return cleaned

def safe_json_extract(text: str, fallback_format: str = "object") -> dict:
    """
    Safely extract JSON from text that might contain other content
    
    Args:
        text: Text that might contain JSON
        fallback_format: What to assume if no JSON found ("object" or "array")
        
    Returns:
        Extracted JSON as dictionary
    """
    # Try to find JSON-like structures in the text
    json_patterns = [
        r'\{.*\}',  # Object
        r'\[.*\]',  # Array
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            result = clean_and_parse_json(match)
            if result is not None:
                return result
    
    # If no JSON found, return minimal structure
    if fallback_format == "array":
        return {"items": []}
    else:
        return {"content": text[:200] + "..." if len(text) > 200 else text}

def validate_structured_content(data: dict) -> bool:
    """
    Validate that structured content has expected format
    
    Args:
        data: Dictionary to validate
        
    Returns:
        True if valid structured content format
    """
    if not isinstance(data, dict):
        return False
    
    # Check for common structured content patterns
    valid_patterns = [
        # Calendar/schedule pattern
        lambda d: 'calendar' in d and isinstance(d['calendar'], list),
        # Posts pattern  
        lambda d: 'posts' in d and isinstance(d['posts'], list),
        # Generic array pattern
        lambda d: any(isinstance(v, list) and len(v) > 0 for v in d.values()),
        # Analysis pattern
        lambda d: any(k in d for k in ['executive_summary', 'key_insights', 'actionable_insights']),
    ]
    
    return any(pattern(data) for pattern in valid_patterns)