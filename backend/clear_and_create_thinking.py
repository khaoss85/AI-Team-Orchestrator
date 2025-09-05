#!/usr/bin/env python3
"""
Clear all thinking processes and create one distinctive new one
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from database import get_supabase_client
from services.thinking_process import RealTimeThinkingEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_all_thinking_processes():
    """Clear all thinking processes from the workspace"""
    supabase = get_supabase_client()
    workspace_id = "f79d87cc-b61f-491d-9226-4220e39e71ad"
    
    print("🧹 CLEARING ALL EXISTING THINKING PROCESSES")
    
    try:
        # Delete all thinking steps first (foreign key dependency)
        steps_result = supabase.table("thinking_steps").delete().neq("id", "impossible-id").execute()
        print(f"   🗑️ Deleted {len(steps_result.data) if steps_result.data else 0} thinking steps")
        
        # Delete all thinking processes
        processes_result = supabase.table("thinking_processes").delete().neq("id", "impossible-id").execute()
        print(f"   🗑️ Deleted {len(processes_result.data) if processes_result.data else 0} thinking processes")
        
        print("✅ Database cleared successfully")
        
    except Exception as e:
        print(f"⚠️ Error clearing database: {e}")

async def create_distinctive_thinking_process():
    """Create one very distinctive thinking process"""
    
    workspace_id = UUID("f79d87cc-b61f-491d-9226-4220e39e71ad")
    thinking_engine = RealTimeThinkingEngine()
    
    print("\n🧠 CREATING NEW DISTINCTIVE THINKING PROCESS")
    print("=" * 50)
    
    try:
        # Create a very distinctive thinking process
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context="🚀 AI-DRIVEN UX ENHANCEMENT DEMONSTRATION - New Thinking Process Format Testing",
            process_type="demonstration"
        )
        
        print(f"✅ Started distinctive process: {process_id}")
        
        # Add very distinctive steps
        distinctive_steps = [
            {
                "step_type": "analysis",
                "content": "🎯 **NEW UX FORMAT TEST** - Analyzing the enhanced thinking process visualization with concise titles and metadata display. This demonstrates the ChatGPT/Claude-style minimal interface.",
                "confidence": 0.95
            },
            {
                "step_type": "evaluation", 
                "content": "✨ **ENHANCED METADATA** - Evaluating the new format: Agent info, processing time, token count, and duration are now visible at a glance. UI clutter reduced by 80%.",
                "confidence": 0.92
            },
            {
                "step_type": "conclusion",
                "content": "🎉 **SUCCESS DEMONSTRATION** - The new thinking process UX successfully delivers: concise AI-generated titles, essential metadata visibility, minimal design, and improved user experience!",
                "confidence": 0.97
            }
        ]
        
        # Add each step with metadata
        for i, step_data in enumerate(distinctive_steps, 1):
            step_id = await thinking_engine.add_thinking_step(
                process_id=process_id,
                step_type=step_data["step_type"],
                content=step_data["content"],
                confidence=step_data["confidence"],
                metadata={
                    "step_number": i,
                    "total_steps": len(distinctive_steps),
                    "processing_time_ms": 250 + (i * 100),
                    "estimated_tokens": 80 + (i * 40),
                    "demo_flag": True,
                    "new_format": "enhanced_ux"
                }
            )
            
            print(f"   📝 Added distinctive step {i}: {step_data['step_type']}")
            await asyncio.sleep(0.3)
        
        # Complete the process
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion="🎯 UX Enhancement demonstration completed successfully! The new thinking process format provides better user experience with concise titles and essential metadata visibility.",
            overall_confidence=0.95
        )
        
        print(f"🎯 Completed distinctive process")
        print(f"   • Title: {getattr(completed_process, 'title', 'Generated Title')}")
        print(f"   • Steps: {len(distinctive_steps)}")
        
        print(f"\n🔗 VIEW THE NEW FORMAT:")
        print(f"http://localhost:3000/projects/{workspace_id}/conversation?tab=thinking&goalId=b9ac9790-20d8-4851-8852-64847b8af6a2")
        
        return process_id
        
    except Exception as e:
        print(f"❌ Failed to create distinctive process: {e}")
        return None

async def main():
    """Main execution"""
    print("🔄 THINKING PROCESS UX DEMONSTRATION SETUP")
    print("=" * 50)
    
    # Clear existing processes
    await clear_all_thinking_processes()
    
    # Create new distinctive process
    process_id = await create_distinctive_thinking_process()
    
    if process_id:
        print(f"\n✅ SUCCESS!")
        print(f"🎯 Created distinctive thinking process: {process_id}")
        print(f"🔍 Now you should see ONLY the new enhanced format!")
    else:
        print(f"\n❌ FAILED!")

if __name__ == "__main__":
    asyncio.run(main())