#!/usr/bin/env python3
"""
Create a distinctive thinking process specifically to test the new collapsed UI format
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from services.thinking_process import RealTimeThinkingEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_ui_demo_thinking_process():
    """
    Create a thinking process specifically designed to test the new UI:
    - Concise AI-generated title
    - Essential metadata (agent, tools, tokens, duration)
    - Collapsed by default with expand/collapse functionality
    """
    
    workspace_id = UUID("f79d87cc-b61f-491d-9226-4220e39e71ad")
    thinking_engine = RealTimeThinkingEngine()
    
    print("🧠 CREATING UI DEMO THINKING PROCESS")
    print("=" * 50)
    print("Testing the new collapsed/expanded UI format")
    
    try:
        # Create thinking process with descriptive context for AI title generation
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context="🎨 UI/UX Design Analysis - ChatGPT/Claude Minimal Interface Implementation",
            process_type="ui_design_analysis"
        )
        
        print(f"✅ Started UI demo process: {process_id}")
        
        # Add distinctive thinking steps that showcase the new format
        steps = [
            {
                "step_type": "analysis",
                "content": "🔍 **INTERFACE ANALYSIS** - Analyzing the thinking process UI transformation from verbose display to minimal ChatGPT/Claude style. Current implementation shows excessive detail by default, reducing scannability.",
                "confidence": 0.88,
                "metadata": {
                    "step_number": 1,
                    "total_steps": 4,
                    "processing_time_ms": 420,
                    "estimated_tokens": 150,
                    "ui_analysis": "excessive_detail",
                    "design_pattern": "chatgpt_claude_minimal"
                }
            },
            {
                "step_type": "design_planning",
                "content": "🎯 **DESIGN STRATEGY** - Planning collapsed-first approach: Show only AI-generated title initially, with small metadata below (agent, execution time, tokens, tools). Full detailed reasoning hidden until user expands. This matches user expectation: 'io pensavo ad avere solo titolo visibile fatto carino, poi espansione anche dettaglio sotto'.",
                "confidence": 0.94,
                "metadata": {
                    "step_number": 2,
                    "total_steps": 4,
                    "processing_time_ms": 580,
                    "estimated_tokens": 220,
                    "design_decision": "collapsed_first",
                    "user_feedback": "title_only_initially"
                }
            },
            {
                "step_type": "implementation",
                "content": "⚡ **IMPLEMENTATION DETAILS** - Implementing expand/collapse state management with clean visual hierarchy. Title prominent with good typography, metadata in subtle gray text, chevron icons for expansion. Clean borders and hover states following minimal design principles.",
                "confidence": 0.91,
                "metadata": {
                    "step_number": 3,
                    "total_steps": 4,
                    "processing_time_ms": 720,
                    "estimated_tokens": 280,
                    "ui_elements": ["title", "metadata", "chevron", "hover_states"],
                    "visual_hierarchy": "minimal_clean"
                }
            },
            {
                "step_type": "conclusion",
                "content": "✨ **SUCCESS VALIDATION** - New UI format achieves the desired user experience: clean title-first presentation, essential metadata visibility, and detailed content on-demand. Users can quickly scan thinking process titles and expand only relevant processes for deep analysis. Matches ChatGPT/Claude professional minimal aesthetic.",
                "confidence": 0.96,
                "metadata": {
                    "step_number": 4,
                    "total_steps": 4,
                    "processing_time_ms": 630,
                    "estimated_tokens": 320,
                    "validation_criteria": ["scannability", "on_demand_detail", "professional_aesthetic"],
                    "user_satisfaction": "achieved"
                }
            }
        ]
        
        # Add each thinking step with realistic timing
        for i, step_data in enumerate(steps, 1):
            await asyncio.sleep(0.4)  # Simulate thinking time
            
            step_id = await thinking_engine.add_thinking_step(
                process_id=process_id,
                step_type=step_data["step_type"],
                content=step_data["content"],
                confidence=step_data["confidence"],
                metadata=step_data["metadata"]
            )
            
            print(f"  ✅ Added step {i}: {step_data['step_type']}")
        
        # Complete the process with conclusive summary
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion="UI/UX transformation successfully implemented. New thinking process interface provides optimal user experience with title-first presentation, essential metadata visibility, and on-demand detailed content expansion. Design follows ChatGPT/Claude minimal principles.",
            overall_confidence=0.93
        )
        
        print(f"🎯 Completed UI demo process")
        print(f"   • AI-generated title will appear in frontend")
        print(f"   • Essential metadata: Agent (UI Designer), Duration (~2.4s), Tokens (~970), Tools (design_analysis)")
        print(f"   • Steps: {len(steps)} (collapsed by default)")
        
        print(f"\n🔗 VIEW THE NEW COLLAPSED FORMAT:")
        print(f"http://localhost:3000/projects/{workspace_id}/conversation?tab=thinking&goalId=b9ac9790-20d8-4851-8852-64847b8af6a2")
        
        return process_id
        
    except Exception as e:
        print(f"❌ Failed to create UI demo process: {e}")
        logger.error(f"UI demo creation failed: {e}", exc_info=True)
        return None

async def main():
    """Main execution"""
    print("🎨 AI TEAM ORCHESTRATOR - UI DEMO THINKING PROCESS")
    print("=" * 60)
    print("Creating thinking process to demonstrate new collapsed UI format:")
    print("• Title-only initial display")
    print("• Essential metadata below title")
    print("• Detailed content hidden until expansion")
    print("• ChatGPT/Claude minimal aesthetic")
    print("=" * 60)
    
    process_id = await create_ui_demo_thinking_process()
    
    if process_id:
        print(f"\n✅ UI DEMO CREATION SUCCESS!")
        print(f"🎯 Process ID: {process_id}")
        print("📱 You should now see ONLY the title initially with small metadata below")
        print("🔍 Click to expand and see full detailed reasoning steps")
        print("🎨 Clean, minimal interface matching ChatGPT/Claude style")
    else:
        print(f"\n❌ UI DEMO CREATION FAILED")
        print("Check the backend logs for details")

if __name__ == "__main__":
    asyncio.run(main())