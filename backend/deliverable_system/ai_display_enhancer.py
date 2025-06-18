#!/usr/bin/env python3
"""
🤖 AI-DRIVEN DISPLAY ENHANCER
Integra il markup processor nell'ecosystem per generare display instructions
"""

import json
import logging
from typing import Dict, Any, Optional

from .markup_processor import DeliverableMarkupProcessor

logger = logging.getLogger(__name__)

class AIDisplayEnhancer:
    """
    🌍 UNIVERSAL DISPLAY ENHANCER
    Integra AI-driven display generation nel flusso dei deliverable
    Rispetta tutti i pilastri architetturali
    """
    
    def __init__(self):
        self.markup_processor = DeliverableMarkupProcessor()
    
    async def enhance_deliverable_with_display_format(self, deliverable_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Enhances deliverable with AI-generated display instructions
        """
        
        try:
            # Extract content to be enhanced
            content_to_enhance = None
            
            if "detailed_results_json" in deliverable_data:
                try:
                    content_to_enhance = json.loads(deliverable_data["detailed_results_json"])
                except json.JSONDecodeError:
                    content_to_enhance = deliverable_data["detailed_results_json"]
            elif "summary" in deliverable_data:
                content_to_enhance = deliverable_data["summary"]
            else:
                content_to_enhance = deliverable_data
            
            # Generate AI-driven display instructions
            enhanced_content = await self.markup_processor.process_deliverable_content(content_to_enhance)
            
            # Integrate display instructions back into deliverable
            enhanced_deliverable = deliverable_data.copy()
            
            if "_display_format" in enhanced_content:
                # Add display instructions to detailed_results_json
                if "detailed_results_json" in enhanced_deliverable:
                    try:
                        existing_data = json.loads(enhanced_deliverable["detailed_results_json"])
                        existing_data["_display_format"] = enhanced_content["_display_format"]
                        enhanced_deliverable["detailed_results_json"] = json.dumps(existing_data)
                    except json.JSONDecodeError:
                        # Create new structured data with display format
                        new_data = {
                            "content": enhanced_deliverable["detailed_results_json"],
                            "_display_format": enhanced_content["_display_format"]
                        }
                        enhanced_deliverable["detailed_results_json"] = json.dumps(new_data)
                else:
                    # Create detailed_results_json with display format
                    new_data = {
                        "content": content_to_enhance,
                        "_display_format": enhanced_content["_display_format"]
                    }
                    enhanced_deliverable["detailed_results_json"] = json.dumps(new_data)
                
                # Add metadata about enhancement
                if "metadata" not in enhanced_deliverable:
                    enhanced_deliverable["metadata"] = {}
                
                enhanced_deliverable["metadata"]["display_enhanced"] = True
                enhanced_deliverable["metadata"]["display_method"] = enhanced_content.get("processing_method", "unknown")
                
                logger.info(f"✅ Enhanced deliverable with {enhanced_content['_display_format']['type']} display format")
            
            return enhanced_deliverable
            
        except Exception as e:
            logger.error(f"Failed to enhance deliverable with display format: {e}")
            return deliverable_data  # Return original if enhancement fails
    
    async def enhance_task_output_with_display_format(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Enhances task output with AI-generated display instructions for human feedback
        """
        
        try:
            # Find the main output content
            main_content = None
            
            if "detailed_results_json" in task_result:
                main_content = task_result["detailed_results_json"]
            elif "summary" in task_result:
                main_content = task_result["summary"]
            elif "output" in task_result:
                main_content = task_result["output"]
            else:
                main_content = task_result
            
            # Generate display instructions
            if main_content:
                enhanced_content = await self.markup_processor.process_deliverable_content(main_content)
                
                # Add to task result
                enhanced_task = task_result.copy()
                enhanced_task["_display_enhanced"] = enhanced_content
                
                logger.info(f"✅ Enhanced task output with display format")
                return enhanced_task
            
            return task_result
            
        except Exception as e:
            logger.error(f"Failed to enhance task output: {e}")
            return task_result

# Global instance
ai_display_enhancer = AIDisplayEnhancer()