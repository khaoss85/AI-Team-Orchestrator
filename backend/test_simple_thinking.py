#!/usr/bin/env python3
"""
Simple test script to inject thinking process that works with current database schema
"""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4, UUID

from services.thinking_process import RealTimeThinkingEngine, ThinkingStep

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inject_working_thinking_process():
    """
    Inject a working thinking process using current database schema
    """
    
    workspace_id = UUID("f79d87cc-b61f-491d-9226-4220e39e71ad")
    
    # Initialize thinking engine
    thinking_engine = RealTimeThinkingEngine()
    
    print(f"🧠 Injecting test thinking process for workspace {workspace_id}")
    
    try:
        # Start a new thinking process
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context="Marketing Strategy Analysis for Email Campaign Optimization",
            process_type="strategic_analysis"
        )
        
        print(f"✅ Started thinking process: {process_id}")
        
        # Add simple thinking steps that work with current schema
        steps = [
            {
                "step_type": "analysis",
                "content": "📊 Analyzing current email marketing performance metrics: 23% open rate, 4.2% CTR, 1.8% conversion rate. Industry benchmarks show potential for 35% open rate improvement.",
                "confidence": 0.85,
                "metadata": {
                    "step_number": 1,
                    "processing_time_ms": 420,
                    "tokens_generated": 150
                }
            },
            {
                "step_type": "reasoning",
                "content": "🎯 Key insight: Segmentation strategy is underperforming. Current broad targeting dilutes message relevance. Need persona-specific email sequences to increase engagement.",
                "confidence": 0.92,
                "metadata": {
                    "step_number": 2,
                    "processing_time_ms": 570,
                    "tokens_generated": 230
                }
            },
            {
                "step_type": "evaluation",
                "content": "🔍 Evaluating three optimization approaches:\n1. Advanced segmentation (high impact, medium effort)\n2. Personalization engine (very high impact, high effort)\n3. Send time optimization (medium impact, low effort)\n\nRecommendation: Start with #1 and #3 for quick wins.",
                "confidence": 0.88,
                "metadata": {
                    "step_number": 3,
                    "processing_time_ms": 720,
                    "tokens_generated": 310
                }
            },
            {
                "step_type": "conclusion",
                "content": "💡 Final recommendation: Focus on data-driven personalization through enhanced segmentation. This approach balances high impact with manageable implementation complexity, providing clear ROI measurement opportunities.",
                "confidence": 0.94,
                "metadata": {
                    "step_number": 4,
                    "processing_time_ms": 620,
                    "tokens_generated": 400
                }
            }
        ]
        
        # Add each thinking step
        for i, step_data in enumerate(steps, 1):
            await asyncio.sleep(0.3)  # Simulate thinking time
            
            try:
                step_id = await thinking_engine.add_thinking_step(
                    process_id=process_id,
                    step_type=step_data["step_type"],
                    content=step_data["content"],
                    confidence=step_data["confidence"],
                    metadata=step_data["metadata"]
                )
                
                print(f"  ✅ Added step {i}/{len(steps)}: {step_data['step_type']} -> {step_id}")
                
            except Exception as step_error:
                print(f"  ❌ Failed to add step {i}: {step_error}")
                # Continue with other steps even if one fails
                continue
        
        # Complete the thinking process (using correct method signature)
        try:
            completed_process = await thinking_engine.complete_thinking_process(
                process_id=process_id,
                conclusion="Strategic email marketing optimization plan developed with focus on behavioral segmentation and personalization. Implementation roadmap provides clear 40-50% engagement improvement path with measurable ROI.",
                overall_confidence=0.91
            )
            
            print(f"🎯 Completed thinking process successfully")
            print(f"   • Title: {getattr(completed_process, 'title', 'Not available yet')}")
            print(f"   • Steps: {len(completed_process.steps) if completed_process.steps else 0}")
            
        except Exception as complete_error:
            print(f"⚠️ Could not complete process: {complete_error}")
            # Process is still created and steps added, just not completed
        
        print(f"\n✨ Test thinking process injected!")
        print(f"📍 View at: http://localhost:3000/projects/{workspace_id}/conversation?goalId=b9ac9790-20d8-4851-8852-64847b8af6a2&tab=thinking")
        
        return process_id
        
    except Exception as e:
        print(f"❌ Failed to inject thinking process: {e}")
        logger.error(f"Injection failed: {e}", exc_info=True)
        return None

async def main():
    """Main execution"""
    print("🧠 AI TEAM ORCHESTRATOR - SIMPLE THINKING PROCESS INJECTION")
    print("=" * 60)
    print("Creating thinking process with current schema compatibility")
    print("=" * 60)
    
    process_id = await inject_working_thinking_process()
    
    if process_id:
        print(f"\n" + "=" * 60)
        print("✅ INJECTION COMPLETE")
        print(f"Process ID: {process_id}")
        print("🔍 Go to the thinking tab to see the new format!")
    else:
        print(f"\n" + "=" * 60)
        print("❌ INJECTION FAILED")
        print("Check the backend logs for details")

if __name__ == "__main__":
    asyncio.run(main())