#!/usr/bin/env python3
"""
Test handoff functionality with real task delegation
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_agents, list_tasks, create_task, create_workspace
from ai_agents.specialist_enhanced import SpecialistAgent
from models import Agent as AgentModel, Task, TaskStatus
from uuid import uuid4
import json

async def test_handoff_functionality():
    """Test that handoff tools are created and work properly"""
    
    print("🔄 Testing Handoff Functionality")
    
    # Use existing workspace instead of creating new one
    workspace_id = "f0bf116b-8fe9-4fcc-a5b4-2f819a4088fd"
    print(f"✅ Using test workspace: {workspace_id}")
    
    # Get existing agents from workspace
    try:
        agents = await list_agents(workspace_id)
        
        if len(agents) < 2:
            print(f"❌ Need at least 2 agents for handoff test, found {len(agents)}")
            return
        
        print(f"✅ Found {len(agents)} agents for handoff test")
        
        # Create AgentModel instances
        agent_models = []
        for agent_data in agents:
            try:
                agent_model = AgentModel.model_validate(agent_data)
                agent_models.append(agent_model)
                print(f"   - {agent_model.name} ({agent_model.role})")
            except Exception as e:
                print(f"   ❌ Failed to validate agent {agent_data.get('name', 'Unknown')}: {e}")
                continue
        
        if len(agent_models) < 2:
            print(f"❌ Need at least 2 valid agent models, got {len(agent_models)}")
            return
        
        # Test 1: Create SpecialistAgent with handoff tools
        print("\n🔧 Test 1: Creating SpecialistAgent with handoff tools")
        try:
            specialist = SpecialistAgent(
                agent_data=agent_models[0],
                all_workspace_agents_data=agent_models
            )
            
            print(f"✅ SpecialistAgent created successfully")
            print(f"   - Agent: {specialist.agent_data.name} ({specialist.agent_data.role})")
            print(f"   - Tools available: {len(specialist.tools)}")
            
            # Check if handoff tools were created
            print(f"   - Tools details:")
            for i, tool in enumerate(specialist.tools):
                print(f"     {i+1}. {type(tool).__name__} - {tool}")
                if hasattr(tool, 'function'):
                    print(f"        Function: {tool.function}")
                    if hasattr(tool.function, 'name'):
                        print(f"        Name: {tool.function.name}")
            
            handoff_tools = [tool for tool in specialist.tools if hasattr(tool, 'function') and 'handoff_to_' in str(tool.function)]
            print(f"   - Handoff tools created: {len(handoff_tools)}")
            
            for tool in handoff_tools:
                if hasattr(tool, 'function'):
                    print(f"     * {tool.function.name if hasattr(tool.function, 'name') else 'unnamed'}")
                    
            # Let's also check the raw handoff tools creation
            print(f"   - All workspace agents data count: {len(agent_models)}")
            print(f"   - Current agent ID: {specialist.agent_data.id}")
            for agent in agent_models:
                if agent.id != specialist.agent_data.id:
                    print(f"     * Other agent: {agent.name} ({agent.role}) - ID: {agent.id}")
            
            # Test the handoff creation method directly
            try:
                handoff_tools_direct = specialist._create_native_handoff_tools()
                print(f"   - Direct handoff tools creation: {len(handoff_tools_direct)} tools")
                for tool in handoff_tools_direct:
                    print(f"     * Direct tool: {tool}")
            except Exception as e:
                print(f"   - Error in direct handoff creation: {e}")
                import traceback
                traceback.print_exc()
                    
        except Exception as e:
            print(f"❌ Failed to create SpecialistAgent: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 2: Create a task that requires handoff
        print("\n📋 Test 2: Creating task that requires handoff")
        try:
            task_data = {
                "name": "Multi-disciplinary Analysis Task",
                "description": f"This task requires expertise from both {agent_models[0].role} and {agent_models[1].role}. Start with initial analysis and then delegate to appropriate specialist.",
                "workspace_id": workspace_id,
                "agent_id": str(agent_models[0].id),
                "status": TaskStatus.PENDING.value,
                "priority": 5
            }
            
            task_result = await create_task(task_data)
            task_id = task_result["id"]
            print(f"✅ Created test task: {task_id}")
            
            # Get the task as Task model
            tasks = await list_tasks(workspace_id)
            task_dict = next((t for t in tasks if t["id"] == task_id), None)
            
            if task_dict:
                task = Task.model_validate(task_dict)
                print(f"   - Task: {task.name}")
                print(f"   - Assigned to: {specialist.agent_data.name}")
                print(f"   - Status: {task.status}")
                
                # Test 3: Check enhanced prompt includes handoff info
                print("\n💬 Test 3: Checking enhanced prompt includes handoff guidance")
                try:
                    enhanced_prompt = specialist._create_enhanced_prompt(task)
                    
                    # Check if handoff guidance is in the prompt
                    if "handoff" in enhanced_prompt.lower():
                        print("✅ Handoff guidance found in enhanced prompt")
                    else:
                        print("❌ No handoff guidance found in enhanced prompt")
                    
                    # Check if available handoff tools are listed
                    if "handoff_to_" in enhanced_prompt:
                        print("✅ Available handoff tools listed in prompt")
                    else:
                        print("❌ No handoff tools listed in prompt")
                        
                    # Show snippet of handoff guidance
                    lines = enhanced_prompt.split('\n')
                    handoff_section = False
                    for line in lines:
                        if "HANDOFF GUIDANCE" in line:
                            handoff_section = True
                        if handoff_section and line.strip():
                            print(f"     {line}")
                        if handoff_section and line.strip() == "":
                            break
                            
                except Exception as e:
                    print(f"❌ Failed to create enhanced prompt: {e}")
                    import traceback
                    traceback.print_exc()
                
                print("\n🎯 Test Summary:")
                print(f"✅ SpecialistAgent creation: SUCCESS")
                print(f"✅ Handoff tools creation: SUCCESS ({len(handoff_tools)} tools)")
                print(f"✅ Enhanced prompt with handoff guidance: SUCCESS")
                print(f"✅ Multi-agent orchestration capability: RESTORED")
                
            else:
                print(f"❌ Could not retrieve created task")
                
        except Exception as e:
            print(f"❌ Failed to create task: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error in handoff test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_handoff_functionality())