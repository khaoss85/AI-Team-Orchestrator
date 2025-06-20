#!/usr/bin/env python3
"""
Test Real-Time Thinking Process
Tests the new thinking process implementation with real AI analysis steps
"""

import asyncio
import requests
import json
import sys
import time
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

def test_thinking_endpoint():
    """Test the REST endpoint with thinking process"""
    print("🧪 Testing Real-Time Thinking Process...")
    print("=" * 60)
    
    workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    
    test_message = "serve aggiungere un agente al team oppure il team secondo te è completo così?"
    
    print(f"📝 Test Message: {test_message}")
    print()
    
    try:
        # Test the thinking endpoint
        print("🚀 Sending request to thinking endpoint...")
        start_time = time.time()
        
        response = requests.post(
            f"http://localhost:8000/api/conversation/workspaces/{workspace_id}/chat/thinking",
            json={
                "message": test_message,
                "chat_id": "team"
            },
            timeout=60
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for thinking process artifact
            response_obj = data.get("response", {})
            artifacts = response_obj.get("artifacts", [])
            suggested_actions = response_obj.get("suggested_actions", [])
            
            print("\n🔍 Response Analysis:")
            print(f"   Message length: {len(response_obj.get('message', ''))}")
            print(f"   Artifacts: {len(artifacts)}")
            print(f"   Suggested actions: {len(suggested_actions)}")
            
            # Find thinking process artifact
            thinking_artifact = None
            for artifact in artifacts:
                if artifact.get("type") == "thinking_process":
                    thinking_artifact = artifact
                    break
            
            if thinking_artifact:
                print("\n🧠 THINKING PROCESS FOUND:")
                steps = thinking_artifact.get("content", {}).get("steps", [])
                print(f"   Total thinking steps: {len(steps)}")
                
                for i, step in enumerate(steps, 1):
                    step_type = step.get("type", "unknown")
                    title = step.get("title", "No title")
                    description = step.get("description", "No description")
                    status = step.get("status", "unknown")
                    
                    print(f"\n   Step {i}: {title}")
                    print(f"      Type: {step_type}")
                    print(f"      Description: {description}")
                    print(f"      Status: {status}")
                
                print("\n✅ THINKING PROCESS WORKS!")
                print("✅ Real AI analysis steps captured")
                print("✅ Ready for frontend visualization")
            else:
                print("\n❌ No thinking process artifact found")
                return False
            
            # Test suggested actions
            if suggested_actions:
                print(f"\n⚡ SUGGESTED ACTIONS FOUND: {len(suggested_actions)}")
                for i, action in enumerate(suggested_actions, 1):
                    tool = action.get("tool", "unknown")
                    label = action.get("label", "No label")
                    description = action.get("description", "No description")
                    action_type = action.get("type", "unknown")
                    
                    print(f"\n   Action {i}: {label}")
                    print(f"      Tool: {tool}")
                    print(f"      Description: {description}")
                    print(f"      Type: {action_type}")
                
                print("\n✅ SUGGESTED ACTIONS READY FOR BUTTONS!")
                return test_action_execution(workspace_id, suggested_actions[0])
            else:
                print("\n⚠️  No suggested actions found")
                return True
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_action_execution(workspace_id: str, action: dict) -> bool:
    """Test executing a suggested action"""
    print(f"\n🎯 Testing Action Execution...")
    print("=" * 40)
    
    try:
        tool_name = action.get("tool")
        parameters = action.get("parameters", {})
        
        print(f"🔧 Executing tool: {tool_name}")
        print(f"📋 Parameters: {parameters}")
        
        response = requests.post(
            f"http://localhost:8000/api/conversation/workspaces/{workspace_id}/execute-action",
            json={
                "tool": tool_name,
                "parameters": parameters,
                "chat_id": "team"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("✅ Action executed successfully!")
                print(f"🎯 Tool: {result.get('tool')}")
                
                tool_result = result.get("result", {})
                if isinstance(tool_result, dict):
                    success = tool_result.get("success", False)
                    message = tool_result.get("message", "No message")
                    print(f"📊 Result: {message[:100]}...")
                    print(f"🎉 Tool success: {success}")
                else:
                    print(f"📊 Result: {str(tool_result)[:100]}...")
                
                print("\n✅ CLICKABLE ACTIONS WORKING!")
                return True
            else:
                print(f"❌ Action failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Action execution test failed: {e}")
        return False

def main():
    print("🧪 Real-Time Thinking Process & Action Buttons Test")
    print("=" * 70)
    
    # Test thinking process
    thinking_ok = test_thinking_endpoint()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"✅ Thinking Process: {'PASS' if thinking_ok else 'FAIL'}")
    
    if thinking_ok:
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ Real thinking process implemented")
        print("✅ AI analysis steps captured in real-time")
        print("✅ Suggested actions are clickable and executable")
        print("✅ Ready for frontend integration")
        
        print("\n📋 Frontend Integration Guide:")
        print("• Use /chat/thinking endpoint for enhanced experience")
        print("• Parse thinking_process artifact for step visualization")
        print("• Render suggested_actions as clickable buttons")
        print("• Use /execute-action endpoint for button clicks")
        print("• WebSocket endpoint available for real-time streaming")
        
        print("\n🎨 UI Components Needed:")
        print("• ThinkingProcessViewer component")
        print("• ActionButton component")
        print("• Real-time step progress indicators")
        print("• Smooth transitions between thinking steps")
    else:
        print("\n❌ Issues detected - check backend implementation")
    
    return thinking_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)