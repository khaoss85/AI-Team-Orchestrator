"""
Utility Routes
Provides various utility endpoints for data processing and cleaning
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging
from utils.json_cleaner import clean_and_parse_json, safe_json_extract, validate_structured_content

logger = logging.getLogger(__name__)
router = APIRouter()

class JsonCleaningRequest(BaseModel):
    json_string: str

class JsonCleaningResponse(BaseModel):
    parsed_json: Optional[Dict[str, Any]]
    success: bool
    original_error: Optional[str] = None
    cleaning_applied: bool = False

@router.post("/utils/clean-json", response_model=JsonCleaningResponse)
async def clean_json_endpoint(request: JsonCleaningRequest):
    """
    Clean and parse potentially malformed JSON string
    """
    try:
        # Try normal parsing first
        import json
        try:
            parsed = json.loads(request.json_string)
            return JsonCleaningResponse(
                parsed_json=parsed,
                success=True,
                cleaning_applied=False
            )
        except json.JSONDecodeError as original_error:
            # Apply cleaning
            cleaned_result = clean_and_parse_json(request.json_string)
            
            if cleaned_result is not None:
                return JsonCleaningResponse(
                    parsed_json=cleaned_result,
                    success=True,
                    original_error=str(original_error),
                    cleaning_applied=True
                )
            else:
                # Fallback to safe extraction
                fallback_result = safe_json_extract(request.json_string)
                return JsonCleaningResponse(
                    parsed_json=fallback_result,
                    success=True,
                    original_error=str(original_error),
                    cleaning_applied=True
                )
                
    except Exception as e:
        logger.error(f"JSON cleaning failed: {e}")
        return JsonCleaningResponse(
            parsed_json=None,
            success=False,
            original_error=str(e),
            cleaning_applied=False
        )

class ContentValidationRequest(BaseModel):
    content: Dict[str, Any]

class ContentValidationResponse(BaseModel):
    is_valid: bool
    content_type: str
    suggested_renderer: str
    issues: list[str] = []

@router.post("/utils/validate-content", response_model=ContentValidationResponse)
async def validate_content_endpoint(request: ContentValidationRequest):
    """
    Validate and analyze structured content to suggest best rendering approach
    """
    try:
        content = request.content
        is_valid = validate_structured_content(content)
        issues = []
        
        # Detect content type and suggest renderer
        content_type = "generic"
        suggested_renderer = "structured"
        
        if 'calendar' in content and isinstance(content['calendar'], list):
            content_type = "calendar"
            suggested_renderer = "array"
        elif 'posts' in content and isinstance(content['posts'], list):
            content_type = "social_content"
            suggested_renderer = "array"
        elif any(isinstance(v, list) and len(v) > 0 for v in content.values()):
            content_type = "array_based"
            suggested_renderer = "array"
        elif 'rendered_html' in content:
            content_type = "pre_rendered"
            suggested_renderer = "html"
        elif any(k in content for k in ['executive_summary', 'key_insights']):
            content_type = "analysis"
            suggested_renderer = "structured"
        
        # Check for common issues
        if not content:
            issues.append("Content is empty")
        elif not isinstance(content, dict):
            issues.append("Content is not a dictionary")
        
        # Check for array fields with no items
        empty_arrays = [k for k, v in content.items() if isinstance(v, list) and len(v) == 0]
        if empty_arrays:
            issues.append(f"Empty arrays found: {', '.join(empty_arrays)}")
        
        return ContentValidationResponse(
            is_valid=is_valid,
            content_type=content_type,
            suggested_renderer=suggested_renderer,
            issues=issues
        )
        
    except Exception as e:
        logger.error(f"Content validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Content validation failed: {str(e)}")