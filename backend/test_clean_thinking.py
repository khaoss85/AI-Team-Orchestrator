#!/usr/bin/env python3
"""
Create multiple clean thinking processes for UX demonstration
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from services.thinking_process import RealTimeThinkingEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_clean_thinking_processes():
    """
    Create multiple clean thinking processes to showcase the enhanced UX
    """
    
    workspace_id = UUID("f79d87cc-b61f-491d-9226-4220e39e71ad")
    thinking_engine = RealTimeThinkingEngine()
    
    print("🧠 CREATING CLEAN THINKING PROCESSES FOR UX DEMONSTRATION")
    print("=" * 60)
    
    # Different thinking processes to showcase variety
    processes = [
        {
            "context": "Strategic Market Research and Competitive Analysis",
            "process_type": "analysis",
            "steps": [
                {
                    "step_type": "analysis",
                    "content": "📊 Conducting comprehensive market research across 5 key segments. Analyzing competitor positioning, pricing strategies, and market share distribution.",
                    "confidence": 0.88
                },
                {
                    "step_type": "evaluation",
                    "content": "🔍 Evaluating competitive landscape: 3 major players dominate 75% market share. Gap identified in mid-market segment with 15% annual growth rate.",
                    "confidence": 0.91
                },
                {
                    "step_type": "conclusion",
                    "content": "🎯 Strategic opportunity: Mid-market segment entry with differentiated value proposition. Projected 12-month ROI: 185%.",
                    "confidence": 0.89
                }
            ]
        },
        {
            "context": "Product Development Roadmap Planning for Q2-Q3 2025",
            "process_type": "planning",
            "steps": [
                {
                    "step_type": "analysis",
                    "content": "🗓️ Analyzing development capacity: 8 engineers available, 240 story points per sprint. Current velocity: 85% completion rate.",
                    "confidence": 0.87
                },
                {
                    "step_type": "reasoning",
                    "content": "🔧 Prioritizing features based on user impact scores: Authentication 2.0 (90), Analytics Dashboard (85), Mobile API (75).",
                    "confidence": 0.92
                },
                {
                    "step_type": "conclusion",
                    "content": "📋 Roadmap finalized: Q2 focuses on Authentication 2.0, Q3 delivers Analytics Dashboard. Timeline optimized for maximum user value.",
                    "confidence": 0.94
                }
            ]
        },
        {
            "context": "Customer Experience Optimization and Conversion Analysis",
            "process_type": "optimization",
            "steps": [
                {
                    "step_type": "analysis",
                    "content": "📈 Current conversion funnel: 45% landing → 28% trial → 12% paid. Industry benchmark: 35% trial conversion vs our 27%.",
                    "confidence": 0.86
                },
                {
                    "step_type": "reasoning",
                    "content": "🎯 Key friction points identified: Complex signup (40% drop-off), unclear pricing (25% abandon), limited trial features (35% churn).",
                    "confidence": 0.90
                },
                {
                    "step_type": "evaluation",
                    "content": "🚀 A/B testing 3 optimization approaches: Simplified signup, transparent pricing, enhanced trial. Expected 35% conversion improvement.",
                    "confidence": 0.88
                },
                {
                    "step_type": "conclusion",
                    "content": "✅ Implementation plan: Simplified signup (2 weeks), pricing transparency (1 week), trial enhancement (3 weeks). Target: 40% conversion rate.",
                    "confidence": 0.93
                }
            ]
        }
    ]
    
    created_processes = []
    
    for i, process_data in enumerate(processes, 1):
        print(f"\n🔄 Creating process {i}/{len(processes)}: {process_data['context'][:50]}...")
        
        try:
            # Create the thinking process
            process_id = await thinking_engine.start_thinking_process(
                workspace_id=workspace_id,
                context=process_data["context"],
                process_type=process_data["process_type"]
            )
            
            print(f"   ✅ Started process: {process_id}")
            
            # Add thinking steps
            for j, step_data in enumerate(process_data["steps"], 1):
                await asyncio.sleep(0.2)  # Brief delay for realism
                
                step_id = await thinking_engine.add_thinking_step(
                    process_id=process_id,
                    step_type=step_data["step_type"],
                    content=step_data["content"],
                    confidence=step_data["confidence"],
                    metadata={
                        "step_number": j,
                        "total_steps": len(process_data["steps"]),
                        "processing_time_ms": 300 + (j * 150),
                        "estimated_tokens": 120 + (j * 60)
                    }
                )
                
                print(f"      📝 Added step {j}: {step_data['step_type']}")
            
            # Complete the process
            completed_process = await thinking_engine.complete_thinking_process(
                process_id=process_id,
                conclusion=f"Successfully completed {process_data['process_type']} with actionable insights and strategic recommendations.",
                overall_confidence=0.90
            )
            
            created_processes.append({
                "id": process_id,
                "title": getattr(completed_process, 'title', 'Generated Title'),
                "steps": len(process_data["steps"]),
                "type": process_data["process_type"]
            })
            
            print(f"   🎯 Completed: {getattr(completed_process, 'title', 'Process')}")
            
        except Exception as e:
            print(f"   ❌ Failed to create process {i}: {e}")
            continue
    
    print(f"\n" + "=" * 60)
    print("✅ CLEAN THINKING PROCESSES CREATED")
    print(f"Total processes: {len(created_processes)}")
    
    for process in created_processes:
        print(f"  🧠 {process['title']} ({process['steps']} steps) - {process['type']}")
    
    print(f"\n🔗 View all processes at:")
    print(f"http://localhost:3000/projects/{workspace_id}/conversation?tab=thinking&goalId=b9ac9790-20d8-4851-8852-64847b8af6a2")
    
    return created_processes

async def main():
    """Main execution"""
    processes = await create_clean_thinking_processes()
    print(f"\n🎉 Created {len(processes)} clean thinking processes for UX evaluation!")

if __name__ == "__main__":
    asyncio.run(main())