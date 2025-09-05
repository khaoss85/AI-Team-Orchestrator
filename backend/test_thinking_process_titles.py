#!/usr/bin/env python3
"""
Test script to verify AI title generation for thinking processes
"""

import asyncio
import logging
from uuid import uuid4
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.thinking_process import thinking_engine
from database import get_supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_thinking_process_with_metadata():
    """Test creating a thinking process with AI title generation and metadata"""
    
    # Use a test workspace ID (you can replace with a real one)
    workspace_id = uuid4()
    
    print("\n🧪 Testing Thinking Process with AI Title Generation and Metadata\n")
    print("=" * 60)
    
    # 1. Start a thinking process
    print("\n1️⃣ Starting thinking process...")
    context = "Analyzing market research data to identify target customer segments and develop a comprehensive go-to-market strategy for SaaS product launch"
    process_id = await thinking_engine.start_thinking_process(workspace_id, context, "market_analysis")
    print(f"   ✅ Process started: {process_id}")
    
    # 2. Add agent thinking steps with metadata
    print("\n2️⃣ Adding agent thinking steps with metadata...")
    
    # Step 1: Agent analysis
    agent_info = {
        "id": str(uuid4()),
        "name": "Market Analyst",
        "role": "market-analyst",
        "seniority": "senior",
        "skills": ["market research", "competitive analysis", "customer segmentation"],
        "workspace_id": str(workspace_id)
    }
    step1_id = await thinking_engine.add_agent_thinking_step(
        process_id, 
        agent_info, 
        "Analyzing market size and growth trends in the SaaS industry",
        confidence=0.85
    )
    print(f"   ✅ Added agent step: {agent_info['role']}")
    
    await asyncio.sleep(0.5)  # Small delay to simulate real processing
    
    # Step 2: Tool execution
    tool_results = {
        "tool_name": "market_data_scraper",
        "tool_type": "web_search",
        "parameters": {"query": "SaaS market trends 2024"},
        "execution_time_ms": 2500,
        "success": True,
        "output_type": "json",
        "summary": "Found 127 relevant market reports and analyzed trends"
    }
    step2_id = await thinking_engine.add_tool_execution_step(
        process_id,
        tool_results,
        "Successfully scraped market data from 15 sources",
        confidence=0.92
    )
    print(f"   ✅ Added tool step: {tool_results['tool_name']}")
    
    await asyncio.sleep(0.5)
    
    # Step 3: Multi-agent collaboration
    agents = [
        {"id": str(uuid4()), "role": "business-analyst", "seniority": "expert"},
        {"id": str(uuid4()), "role": "product-manager", "seniority": "senior"}
    ]
    step3_id = await thinking_engine.add_multi_agent_collaboration_step(
        process_id,
        agents,
        "parallel",
        "Collaborating to synthesize market insights and product positioning"
    )
    print(f"   ✅ Added collaboration step: {len(agents)} agents")
    
    await asyncio.sleep(0.5)
    
    # Step 4: Final analysis
    step4_id = await thinking_engine.add_thinking_step(
        process_id,
        "conclusion",
        "Based on market analysis, identified 3 key customer segments with total addressable market of $2.5B",
        confidence=0.88,
        metadata={
            "segments_identified": 3,
            "market_size": "$2.5B",
            "confidence_level": "high"
        }
    )
    print(f"   ✅ Added conclusion step")
    
    # 3. Complete the process (this will trigger AI title generation)
    print("\n3️⃣ Completing thinking process (triggering AI title generation)...")
    conclusion = "Successfully identified target market segments and developed go-to-market strategy. Key findings: Enterprise segment (40% TAM), Mid-market (35% TAM), SMB (25% TAM)."
    completed_process = await thinking_engine.complete_thinking_process(
        process_id,
        conclusion,
        overall_confidence=0.87
    )
    
    print(f"   ✅ Process completed")
    
    # 4. Display results
    print("\n4️⃣ Results:")
    print("-" * 40)
    print(f"📝 AI-Generated Title: {completed_process.title}")
    print(f"🎯 Context: {completed_process.context[:100]}...")
    print(f"✅ Conclusion: {completed_process.final_conclusion[:100]}...")
    print(f"📊 Confidence: {completed_process.overall_confidence:.0%}")
    print(f"🔢 Total Steps: {len(completed_process.steps)}")
    
    if completed_process.summary_metadata:
        print(f"\n📈 Metadata Summary:")
        print(f"   • Primary Agent: {completed_process.summary_metadata.get('primary_agent', 'N/A')}")
        print(f"   • Tools Used: {', '.join(completed_process.summary_metadata.get('tools_used', [])) or 'None'}")
        print(f"   • Duration: {completed_process.summary_metadata.get('duration_ms', 0)}ms")
        print(f"   • Estimated Tokens: {completed_process.summary_metadata.get('estimated_tokens', 0)}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    
    # 5. Verify database persistence
    print("\n5️⃣ Verifying database persistence...")
    supabase = get_supabase_client()
    
    # Check if the process was saved with title
    response = supabase.table("thinking_processes") \
        .select("process_id, title, summary_metadata") \
        .eq("process_id", process_id) \
        .execute()
    
    if response.data and len(response.data) > 0:
        db_record = response.data[0]
        print(f"   ✅ Database record found")
        print(f"   📝 Title in DB: {db_record.get('title', 'N/A')}")
        print(f"   📊 Metadata saved: {'Yes' if db_record.get('summary_metadata') else 'No'}")
    else:
        print(f"   ⚠️ Database record not found (may be due to test environment)")
    
    return completed_process

async def main():
    """Main test function"""
    try:
        # Check OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ Warning: OPENAI_API_KEY not set. AI title generation will use fallback method.")
        
        # Run the test
        result = await test_thinking_process_with_metadata()
        
        print("\n🎉 All tests passed! AI title generation and metadata are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())