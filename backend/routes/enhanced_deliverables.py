#!/usr/bin/env python3
"""
🎨 Enhanced Deliverables API with AI-Driven Dual-Format Architecture

This route demonstrates the complete AI-Driven transformation system:
- Fetches raw deliverables from database
- Applies AI transformation to create display_content
- Returns dual-format responses with quality metrics
- Maintains backward compatibility
"""

from fastapi import Request, APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger
import logging
import json
import asyncio
from database import supabase, get_deliverables
from services.ai_content_display_transformer import ai_content_display_transformer
from datetime import datetime

router = APIRouter(prefix="/enhanced-deliverables", tags=["enhanced-deliverables"])
logger = logging.getLogger(__name__)

@router.get("/workspace/{workspace_id}")
async def get_enhanced_workspace_deliverables(request: Request, workspace_id: str):
    """
    🎨 Get AI-enhanced deliverables with dual-format support
    
    This endpoint demonstrates the complete transformation pipeline:
    1. Fetch raw deliverables from database
    2. Apply AI content transformation 
    3. Return enhanced format with display_content
    4. Include quality metrics and transformation metadata
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"🎨 Enhanced deliverables API called for workspace {workspace_id}", endpoint="get_enhanced_workspace_deliverables", trace_id=trace_id)
    
    try:
        start_time = datetime.now()
        
        # Step 1: Fetch raw deliverables
        logger.info(f"📦 Fetching raw deliverables for workspace {workspace_id}...")
        raw_deliverables = await get_deliverables(workspace_id)
        logger.info(f"✅ Retrieved {len(raw_deliverables)} raw deliverables")
        
        if not raw_deliverables:
            return {
                "deliverables": [],
                "total_count": 0,
                "transformation_status": {"no_content": len(raw_deliverables)},
                "quality_overview": {},
                "supports_dual_format": True,
                "processing_time": 0.0
            }
        
        # Step 2: Transform deliverables with AI enhancement
        logger.info(f"🤖 Applying AI transformation to {len(raw_deliverables)} deliverables...")
        enhanced_deliverables = []
        transformation_stats = {"success": 0, "fallback": 0, "failed": 0}
        quality_scores = []
        
        # Process deliverables with AI transformation (parallel processing)
        transformation_tasks = []
        for deliverable in raw_deliverables:
            task = enhance_single_deliverable(deliverable, trace_id)
            transformation_tasks.append(task)
        
        # Execute transformations in parallel for better performance
        if transformation_tasks:
            enhanced_results = await asyncio.gather(*transformation_tasks, return_exceptions=True)
            
            for i, result in enumerate(enhanced_results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Transformation failed for deliverable {i}: {result}")
                    # Use fallback for failed transformation
                    enhanced_deliverables.append(create_fallback_enhanced_deliverable(raw_deliverables[i]))
                    transformation_stats["failed"] += 1
                else:
                    enhanced_deliverables.append(result)
                    if result.get("fallback_used", False):
                        transformation_stats["fallback"] += 1
                    else:
                        transformation_stats["success"] += 1
                        
                    # Collect quality scores
                    if result.get("display_quality_score"):
                        quality_scores.append(result["display_quality_score"])
        
        # Step 3: Calculate quality overview
        quality_overview = {}
        if quality_scores:
            quality_overview = {
                "avg_display_quality": sum(quality_scores) / len(quality_scores),
                "min_quality": min(quality_scores),
                "max_quality": max(quality_scores),
                "total_enhanced": len([d for d in enhanced_deliverables if d.get("display_content")])
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Step 4: Return enhanced response
        response = {
            "deliverables": enhanced_deliverables,
            "total_count": len(enhanced_deliverables),
            "transformation_status": transformation_stats,
            "quality_overview": quality_overview,
            "supports_dual_format": True,
            "processing_time": processing_time,
            "enhancement_metadata": {
                "ai_transformer_version": "1.0",
                "transformation_timestamp": datetime.now().isoformat(),
                "workspace_id": workspace_id,
                "total_processed": len(enhanced_deliverables)
            }
        }
        
        logger.info(f"🎉 Enhanced deliverables API completed in {processing_time:.2f}s")
        logger.info(f"📊 Transformation stats: {transformation_stats}")
        logger.info(f"🏆 Quality overview: {quality_overview}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Enhanced deliverables API failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced deliverables: {str(e)}")

async def enhance_single_deliverable(raw_deliverable: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """
    🎨 Apply AI enhancement to a single deliverable
    """
    try:
        deliverable_id = raw_deliverable.get("id", "unknown")
        content = raw_deliverable.get("content", {})
        title = raw_deliverable.get("title", "Untitled")
        
        logger.info(f"🤖 Enhancing deliverable: {title} ({deliverable_id})")
        
        # Determine business context for better transformation
        business_context = {
            "deliverable_type": raw_deliverable.get("type", "unknown"),
            "title": title,
            "workspace_context": "email_marketing"  # Could be derived from content analysis
        }
        
        # Apply AI transformation
        transformation_result = await ai_content_display_transformer.transform_to_display_format(
            content, 
            'html',  # Default to HTML for web display
            business_context
        )
        
        # Create enhanced deliverable with all dual-format fields
        enhanced = {
            # Original fields (backward compatibility)
            "id": raw_deliverable.get("id"),
            "workspace_id": raw_deliverable.get("workspace_id"),
            "goal_id": raw_deliverable.get("goal_id"),
            "task_id": raw_deliverable.get("task_id"),
            "title": title,
            "description": raw_deliverable.get("description"),
            "content": content,  # Keep original for system processing
            "type": raw_deliverable.get("type"),
            "status": raw_deliverable.get("status"),
            "created_at": raw_deliverable.get("created_at"),
            "updated_at": raw_deliverable.get("updated_at"),
            
            # Enhanced dual-format fields
            "display_content": transformation_result.transformed_content,
            "display_format": transformation_result.display_format,
            "display_summary": generate_summary(transformation_result.transformed_content)[:200] + "..." if len(generate_summary(transformation_result.transformed_content)) > 200 else generate_summary(transformation_result.transformed_content),
            "display_metadata": transformation_result.metadata,
            
            # Quality metrics
            "display_quality_score": transformation_result.transformation_confidence / 100.0,  # Convert to 0-1 scale
            "user_friendliness_score": calculate_user_friendliness_score(transformation_result),
            "readability_score": calculate_readability_score(transformation_result.transformed_content),
            "ai_confidence": transformation_result.transformation_confidence / 100.0,
            
            # Transformation tracking
            "content_transformation_status": "success" if not transformation_result.fallback_used else "fallback",
            "transformation_timestamp": datetime.now().isoformat(),
            "transformation_method": "ai" if not transformation_result.fallback_used else "fallback",
            "auto_display_generated": True,
            "fallback_used": transformation_result.fallback_used,
            "processing_time": transformation_result.processing_time,
            
            # Enhanced frontend support
            "available_formats": ["html", "markdown", "text"],
            "can_retry_transformation": transformation_result.fallback_used,
            "transformation_error": transformation_result.metadata.get("fallback_reason") if transformation_result.fallback_used else None
        }
        
        logger.info(f"✅ Enhanced deliverable {deliverable_id}: quality={enhanced['display_quality_score']:.2f}, method={enhanced['transformation_method']}")
        
        return enhanced
        
    except Exception as e:
        logger.error(f"❌ Failed to enhance deliverable {raw_deliverable.get('id')}: {e}")
        raise e

def create_fallback_enhanced_deliverable(raw_deliverable: Dict[str, Any]) -> Dict[str, Any]:
    """
    🛡️ Create fallback enhanced deliverable when AI transformation fails
    """
    content = raw_deliverable.get("content", {})
    
    # Simple content-to-HTML conversion for fallback
    if isinstance(content, dict):
        html_content = "<div class='content'>"
        for key, value in content.items():
            html_content += f"<h3>{key.replace('_', ' ').title()}</h3>"
            if isinstance(value, (list, tuple)):
                html_content += "<ul>"
                for item in value:
                    html_content += f"<li>{str(item)}</li>"
                html_content += "</ul>"
            elif isinstance(value, dict):
                html_content += "<pre>" + json.dumps(value, indent=2) + "</pre>"
            else:
                html_content += f"<p>{str(value)}</p>"
        html_content += "</div>"
    else:
        html_content = f"<div class='content'><p>{str(content)}</p></div>"
    
    return {
        **raw_deliverable,
        "display_content": html_content,
        "display_format": "html",
        "display_summary": "Content converted using fallback method",
        "display_quality_score": 0.3,  # Lower quality for fallback
        "user_friendliness_score": 0.4,
        "readability_score": 0.3,
        "ai_confidence": 0.2,
        "content_transformation_status": "fallback",
        "transformation_method": "fallback",
        "auto_display_generated": True,
        "fallback_used": True,
        "available_formats": ["html"],
        "can_retry_transformation": True,
        "transformation_error": "AI transformation unavailable"
    }

def generate_summary(content: str) -> str:
    """Generate a brief summary from content"""
    if not content or len(content) < 50:
        return content
    
    # Simple summary generation - take first sentence or 100 chars
    sentences = content.split('. ')
    if sentences and len(sentences[0]) < 150:
        return sentences[0] + ('.' if not sentences[0].endswith('.') else '')
    
    # Fallback to first 100 characters
    return content[:100].split(' ')[:-1]  # Avoid cutting words

def calculate_user_friendliness_score(transformation_result) -> float:
    """Calculate user-friendliness score based on transformation quality"""
    base_score = transformation_result.transformation_confidence / 100.0
    
    # Bonus for structured content
    if '<h' in transformation_result.transformed_content or '##' in transformation_result.transformed_content:
        base_score += 0.1
    
    # Bonus for lists
    if '<ul>' in transformation_result.transformed_content or '<ol>' in transformation_result.transformed_content:
        base_score += 0.1
        
    # Penalty for fallback
    if transformation_result.fallback_used:
        base_score *= 0.6
    
    return min(1.0, base_score)

def calculate_readability_score(content: str) -> float:
    """Simple readability score calculation"""
    if not content:
        return 0.0
    
    # Basic metrics
    word_count = len(content.split())
    sentence_count = content.count('.') + content.count('!') + content.count('?')
    
    if sentence_count == 0:
        return 0.3  # Low score for no sentences
    
    avg_words_per_sentence = word_count / sentence_count
    
    # Score based on reasonable sentence length
    if avg_words_per_sentence <= 15:
        return 0.9  # Excellent readability
    elif avg_words_per_sentence <= 25:
        return 0.7  # Good readability
    elif avg_words_per_sentence <= 35:
        return 0.5  # Fair readability
    else:
        return 0.3  # Poor readability