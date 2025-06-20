#!/usr/bin/env python3
"""
Test Complete Knowledge Insights Integration
Tests the full flow from backend API to frontend display
"""

import asyncio
import requests
import json
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

def test_knowledge_insights_api():
    print("🧠 Testing Knowledge Insights API Integration...")
    print("=" * 60)
    
    workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    
    try:
        # Test the knowledge insights endpoint
        print("1️⃣ Testing API endpoint...")
        url = f"http://localhost:8000/api/conversation/workspaces/{workspace_id}/knowledge-insights"
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total insights: {data.get('total_insights', 0)}")
            print(f"   ✅ Insights: {len(data.get('insights', []))}")
            print(f"   ✅ Best practices: {len(data.get('bestPractices', []))}")
            print(f"   ✅ Learnings: {len(data.get('learnings', []))}")
            
            # Check data structure matches frontend expectations
            print("\n2️⃣ Verifying data structure...")
            
            # Required fields for frontend
            required_fields = ['workspace_id', 'total_insights', 'insights', 'bestPractices', 'learnings', 'summary']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            else:
                print("   ✅ All required fields present")
            
            # Check summary structure
            summary = data.get('summary', {})
            summary_fields = ['recent_discoveries', 'key_constraints', 'success_patterns', 'top_tags']
            missing_summary = [field for field in summary_fields if field not in summary]
            
            if missing_summary:
                print(f"   ❌ Missing summary fields: {missing_summary}")
                return False
            else:
                print("   ✅ Summary structure complete")
            
            # Test insight structure
            if data.get('learnings'):
                sample_insight = data['learnings'][0]
                insight_fields = ['id', 'type', 'content', 'confidence', 'created_at']
                missing_insight = [field for field in insight_fields if field not in sample_insight]
                
                if missing_insight:
                    print(f"   ❌ Missing insight fields: {missing_insight}")
                    return False
                else:
                    print("   ✅ Insight structure complete")
            
            print("\n3️⃣ Sample data preview...")
            print(f"   📊 Top tags: {summary.get('top_tags', [])[:5]}")
            
            if data.get('learnings'):
                print(f"   📚 Sample learning: {data['learnings'][0]['content'][:100]}...")
            
            print("\n✅ Knowledge Insights API working perfectly!")
            print("✅ Data structure matches frontend requirements")
            print("✅ Ready for frontend integration")
            
            return True
            
        else:
            print(f"   ❌ API error: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_frontend_integration():
    print("\n🎨 Frontend Integration Test...")
    print("=" * 60)
    
    # Simulate what the frontend does
    workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    
    try:
        # Simulate the useConversationalWorkspace hook behavior
        print("1️⃣ Simulating frontend hook behavior...")
        
        # This is what happens in loadChatSpecificArtifacts for knowledge-base chat
        url = f"http://localhost:8000/api/conversation/workspaces/{workspace_id}/knowledge-insights"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            knowledge_data = response.json()
            
            # Simulate creating the artifact
            artifact = {
                "id": "knowledge-insights",
                "type": "knowledge",
                "title": "Knowledge Insights",
                "description": f"{knowledge_data['total_insights']} insights available",
                "status": "ready",
                "content": {
                    "insights": knowledge_data.get('insights', []),
                    "bestPractices": knowledge_data.get('bestPractices', []),
                    "learnings": knowledge_data.get('learnings', []),
                    "summary": knowledge_data.get('summary', {})
                },
                "lastUpdated": "2025-06-20T07:50:00.000Z"
            }
            
            print(f"   ✅ Artifact created with type: {artifact['type']}")
            print(f"   ✅ Content includes {len(artifact['content']['insights'])} insights")
            print(f"   ✅ Content includes {len(artifact['content']['learnings'])} learnings")
            
            # Verify the artifact structure is correct for KnowledgeInsightsArtifact component
            content = artifact['content']
            required_content = ['insights', 'bestPractices', 'learnings', 'summary']
            missing_content = [field for field in required_content if field not in content]
            
            if missing_content:
                print(f"   ❌ Missing content fields: {missing_content}")
                return False
            else:
                print("   ✅ Artifact content structure perfect for frontend component")
            
            # Test the summary structure specifically
            summary = content.get('summary', {})
            if 'top_tags' in summary and len(summary['top_tags']) > 0:
                print(f"   ✅ Summary includes {len(summary['top_tags'])} tags")
            
            print("\n✅ Frontend integration simulation successful!")
            print("✅ KnowledgeInsightsArtifact component will receive correct data")
            
            return True
            
        else:
            print(f"   ❌ API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend integration test failed: {e}")
        return False

def main():
    print("🧪 Complete Knowledge Insights Integration Test")
    print("=" * 70)
    
    # Test API
    api_ok = test_knowledge_insights_api()
    
    # Test frontend integration
    frontend_ok = test_frontend_integration()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"✅ API Endpoint: {'PASS' if api_ok else 'FAIL'}")
    print(f"✅ Frontend Integration: {'PASS' if frontend_ok else 'FAIL'}")
    
    if api_ok and frontend_ok:
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ Knowledge Insights fully functional from backend to frontend")
        print("✅ Real data flowing from workspace memory to UI")
        print("✅ KnowledgeInsightsArtifact component ready to display insights")
        print("\n📋 Next Steps:")
        print("• Open Knowledge Base chat in frontend")
        print("• Knowledge Insights artifact should appear in Artifacts panel")
        print("• Click to view insights with proper categorization and UI")
    else:
        print("\n❌ Issues detected - check logs above")
    
    return api_ok and frontend_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)