#!/usr/bin/env python3
"""
Integration test to verify frontend thinking integration is working correctly.
This script will help debug why the frontend isn't displaying the thinking steps.
"""

import requests
import json

def test_thinking_api():
    """Test the backend thinking API directly"""
    
    workspace_id = "f5c4f1e0-a887-4431-b43e-aea6d62f2d4a"
    api_base = "http://localhost:8000"
    
    print("🧪 Testing Backend Thinking API Integration")
    print("=" * 50)
    
    # Test the API endpoint the frontend is calling
    thinking_url = f"{api_base}/api/thinking/workspace/{workspace_id}?limit=50"
    print(f"📡 Testing: {thinking_url}")
    
    try:
        response = requests.get(thinking_url)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response received successfully")
            print(f"📋 Total processes: {len(data.get('processes', []))}")
            
            # Analyze the processes for debugging
            processes = data.get('processes', [])
            for i, process in enumerate(processes[:3]):  # Show first 3
                print(f"\n🔍 Process {i+1}:")
                print(f"   ID: {process.get('process_id', 'N/A')}")
                print(f"   Context: {process.get('context', 'N/A')[:100]}...")
                print(f"   Steps: {len(process.get('steps', []))}")
                
                # Check if this matches our target deliverable
                context = (process.get('context', '') or '').lower()
                if any(keyword in context for keyword in ['piano editoriale', 'instagram', 'post su instagram']):
                    print(f"   🎯 MATCHES target deliverable!")
                    print(f"   📝 Full context: {process.get('context', 'N/A')}")
                    
                    # Show steps for matching process
                    steps = process.get('steps', [])
                    for j, step in enumerate(steps[:2]):  # Show first 2 steps
                        print(f"      Step {j+1}: {step.get('content', 'N/A')[:80]}...")
                        print(f"      Type: {step.get('step_type', 'N/A')}")
                        print(f"      Timestamp: {step.get('timestamp', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_frontend_simulation():
    """Simulate what the frontend should be doing"""
    
    print(f"\n🎭 Frontend Integration Simulation")
    print("=" * 50)
    
    # These are the values from the user's interface
    test_params = {
        'goalId': '22f28697-e628-48a1-977d-4cf69496f486',
        'workspaceId': 'f5c4f1e0-a887-4431-b43e-aea6d62f2d4a',
        'deliverableTitle': 'Piano editoriale mensile per post su Instagram'
    }
    
    print(f"🔧 Simulating useGoalThinking with:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    
    # Simulate the filtering logic from useGoalThinking
    workspace_id = test_params['workspaceId']
    goal_id = test_params['goalId']
    deliverable_title = test_params['deliverableTitle']
    
    api_base = "http://localhost:8000"
    thinking_url = f"{api_base}/api/thinking/workspace/{workspace_id}?limit=50"
    
    try:
        response = requests.get(thinking_url)
        if response.status_code == 200:
            data = response.json()
            all_processes = data.get('processes', [])
            
            print(f"📊 Total processes fetched: {len(all_processes)}")
            
            # Apply the filtering logic from useGoalThinking
            goal_related_processes = []
            
            for process in all_processes:
                context = (process.get('context', '') or '').lower()
                goal_id_lower = goal_id.lower()
                
                matches = {
                    'directGoalId': goal_id_lower in context,
                    'deliverableTitleMatch': False,
                    'taskMetadata': False
                }
                
                # Check deliverable title match
                if deliverable_title:
                    title_lower = deliverable_title.lower()
                    if title_lower in context:
                        matches['deliverableTitleMatch'] = True
                    else:
                        # Check for multiple key words
                        title_words = [word for word in title_lower.split() if len(word) > 3]
                        matching_words = [word for word in title_words if word in context]
                        if len(matching_words) >= 2:
                            matches['deliverableTitleMatch'] = True
                
                # Check for Instagram-related content
                if not deliverable_title and any(keyword in context for keyword in ['piano editoriale', 'instagram', 'post su instagram']):
                    matches['deliverableTitleMatch'] = True
                
                # Check metadata
                steps = process.get('steps', [])
                for step in steps:
                    step_metadata = step.get('metadata', {})
                    if any(goal_id_lower in str(value).lower() for value in step_metadata.values()):
                        matches['taskMetadata'] = True
                        break
                
                is_match = matches['directGoalId'] or matches['deliverableTitleMatch'] or matches['taskMetadata']
                
                if is_match:
                    goal_related_processes.append(process)
                    print(f"✅ Found matching process: {process.get('process_id', 'N/A')}")
                    print(f"   Context: {context[:100]}...")
                    print(f"   Matches: {matches}")
            
            print(f"\n🎯 Goal-related processes found: {len(goal_related_processes)}")
            
            # Transform to thinking steps
            transformed_steps = []
            for process in goal_related_processes:
                for step in process.get('steps', []):
                    transformed_steps.append({
                        'id': step.get('step_id', 'unknown'),
                        'session_id': process.get('process_id', 'unknown'),
                        'step_type': step.get('step_type', 'goal_thinking'),
                        'thinking_content': step.get('content', ''),
                        'created_at': step.get('timestamp', '')
                    })
            
            print(f"📝 Transformed thinking steps: {len(transformed_steps)}")
            
            if transformed_steps:
                print("\n🧠 Sample thinking steps:")
                for i, step in enumerate(transformed_steps[:3]):
                    print(f"   Step {i+1}: {step['thinking_content'][:100]}...")
                    print(f"      Type: {step['step_type']}")
                    print(f"      Created: {step['created_at']}")
                
                return transformed_steps
            else:
                print("❌ No thinking steps found after transformation")
                return []
                
        else:
            print(f"❌ API Error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    print("🚀 Frontend-Backend Thinking Integration Test")
    print("=" * 60)
    
    # Test backend API
    api_success = test_thinking_api()
    
    if api_success:
        # Test frontend simulation
        thinking_steps = test_frontend_simulation()
        
        if thinking_steps:
            print(f"\n✅ SUCCESS: Integration should work!")
            print(f"📊 Found {len(thinking_steps)} thinking steps")
            print("\n💡 Next steps:")
            print("1. Check browser console for frontend debugging logs")
            print("2. Verify the useGoalThinking hook is being called")
            print("3. Check if the filtering logic matches our simulation")
        else:
            print(f"\n❌ ISSUE: No thinking steps found with current filtering")
            print("\n🔧 Potential fixes:")
            print("1. Check if the goal ID is correctly extracted in the frontend")
            print("2. Verify the deliverable title matches the context")
            print("3. Consider broadening the matching criteria")
    else:
        print(f"\n❌ BACKEND API ISSUE: Fix the API endpoint first")

if __name__ == "__main__":
    main()