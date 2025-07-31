#!/usr/bin/env python3
"""
🔧 DEBUG: Tool Requirements Analysis
Test per capire perché _ai_determine_required_tools restituisce array vuoto
"""

import asyncio
import logging
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_tool_requirements():
    """Debug tool requirements analysis"""
    
    print("\n" + "="*80)
    print("🔧 DEBUG: Tool Requirements Analysis")
    print("="*80)
    
    try:
        from services.real_tool_integration_pipeline import real_tool_integration_pipeline
        from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine, PipelineStepType, PipelineContext
        
        # Test input data (same as production test)
        task_name = "Research email marketing best practices"
        task_objective = "Find current best practices for tech product launch emails"
        business_context = {
            "workspace_id": "test-workspace",
            "industry": "technology",
            "product_type": "B2B SaaS",
            "target_audience": "technical decision makers"
        }
        
        print(f"📝 Task: {task_name}")
        print(f"🎯 Objective: {task_objective}")
        print(f"🏢 Context: {json.dumps(business_context, indent=2)}")
        
        # Test 1: Direct UniversalAIPipelineEngine call
        print("\n🔍 Test 1: Direct UniversalAIPipelineEngine call...")
        
        context = PipelineContext(
            workspace_id=business_context.get("workspace_id"),
            user_context=business_context,
            cache_enabled=True,
            fallback_enabled=False  # NO FALLBACKS for debug
        )
        
        # Get available tools
        available_tools = await real_tool_integration_pipeline._get_available_tools_dynamically()
        print(f"🔧 Available tools: {len(available_tools)} tools discovered")
        
        # Prepare input exactly as in real_tool_integration_pipeline
        analysis_input = {
            "task_name": task_name,
            "task_objective": task_objective,
            "business_context": business_context,
            "available_tools": available_tools
        }
        
        # Call UniversalAIPipelineEngine directly
        result = await universal_ai_pipeline_engine.execute_pipeline_step(
            step_type=PipelineStepType.TOOL_REQUIREMENTS_ANALYSIS,
            input_data=analysis_input,
            context=context
        )
        
        print(f"✅ Pipeline result success: {result.success}")
        print(f"📊 Pipeline result data: {json.dumps(result.data, indent=2) if result.data else 'None'}")
        print(f"❌ Pipeline result error: {result.error}")
        print(f"🔄 Fallback used: {result.fallback_used}")
        
        # Test 2: _ai_determine_required_tools method
        print("\n🔍 Test 2: _ai_determine_required_tools method...")
        
        required_tools = await real_tool_integration_pipeline._ai_determine_required_tools(
            task_name=task_name,
            task_objective=task_objective,
            business_context=business_context
        )
        
        print(f"🔧 Required tools result: {required_tools}")
        print(f"📏 Required tools length: {len(required_tools)}")
        print(f"🔍 Required tools type: {type(required_tools)}")
        
        # Test 3: Check if the extraction logic is working
        if result.success and result.data:
            print("\n🔍 Test 3: Extraction logic analysis...")
            
            tool_categories = result.data.get("required_tool_categories", [])
            print(f"📊 Raw tool_categories: {tool_categories}")
            print(f"📏 Tool categories length: {len(tool_categories)}")
            
            # Manual extraction (same as in _ai_determine_required_tools)
            extracted_categories = [category.get("category", "web_research") for category in tool_categories]
            print(f"🎯 Extracted categories: {extracted_categories}")
            print(f"📏 Extracted length: {len(extracted_categories)}")
        
        # Test 4: Check fallback methods
        print("\n🔍 Test 4: Fallback method test...")
        
        fallback_result = await real_tool_integration_pipeline._fallback_tool_requirements_dynamic(
            task_name, business_context
        )
        
        print(f"🔄 Fallback result: {fallback_result}")
        print(f"📏 Fallback length: {len(fallback_result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Execute debug"""
    
    success = await debug_tool_requirements()
    
    if success:
        print("\n✅ DEBUG COMPLETED: Check logs above for analysis")
        return True
    else:
        print("\n❌ DEBUG FAILED: Check error messages above")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)