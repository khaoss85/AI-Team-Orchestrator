#!/usr/bin/env python3
"""
API Endpoint Test - Test conversational AI API endpoints
Tests the HTTP endpoints that the frontend will actually use
"""

import requests
import json
import time
from typing import Dict, Any

class ConversationalAPITest:
    """Test conversational AI API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_workspace_id = "f0469d4e-fa6b-47f4-a7bd-be5d59e24157"  # Existing workspace
        
    def run_api_tests(self):
        """Run all API endpoint tests"""
        print("🌐 Testing Conversational AI API Endpoints")
        print("="*60)
        
        # Check if server is running
        if not self.check_server():
            print("❌ Server not running at", self.base_url)
            print("💡 Start the server with: python main.py")
            return False
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Conversation Chat", self.test_chat_endpoint),
            ("Conversation History", self.test_history_endpoint),
            ("Conversation Context", self.test_context_endpoint),
            ("Version History", self.test_version_endpoints),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = test_func()
                status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
                print(f"   {status}")
                if not result.get("success", False):
                    print(f"   Details: {result.get('error', 'Unknown error')}")
                results.append((test_name, result.get("success", False)))
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                results.append((test_name, False))
        
        # Summary
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        print(f"\n" + "="*60)
        print(f"📊 API TEST SUMMARY")
        print(f"   Total Endpoints: {total}")
        print(f"   ✅ Working: {passed}")
        print(f"   ❌ Failed: {total - passed}")
        print(f"   📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All API endpoints are working!")
            print("🚀 Conversational AI is ready for frontend integration")
        else:
            print(f"\n⚠️ {total - passed} endpoints need attention")
        
        return passed == total
    
    def check_server(self) -> bool:
        """Check if the server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_health_check(self) -> Dict[str, Any]:
        """Test basic health check"""
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_chat_endpoint(self) -> Dict[str, Any]:
        """Test conversation chat endpoint"""
        try:
            chat_data = {
                "message": "What's the current project status?",
                "chat_id": "api-test",
                "message_id": f"test-{int(time.time())}",
                "context": {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/conversation/workspaces/{self.test_workspace_id}/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_has_message": "response" in data and "message" in data["response"],
                    "processing_time": data.get("processing_time_ms", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_history_endpoint(self) -> Dict[str, Any]:
        """Test conversation history endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/conversation/workspaces/{self.test_workspace_id}/history",
                params={"chat_id": "api-test", "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "messages_returned": len(data) if isinstance(data, list) else 0
                }
            else:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_context_endpoint(self) -> Dict[str, Any]:
        """Test conversation context endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/conversation/workspaces/{self.test_workspace_id}/context",
                params={"chat_id": "api-test"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "has_workspace_summary": "workspace_summary" in data,
                    "has_team_summary": "team_summary" in data
                }
            else:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_version_endpoints(self) -> Dict[str, Any]:
        """Test versioning endpoints"""
        try:
            response = requests.get(f"{self.base_url}/api/conversation/versioning/history")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "version_history_available": isinstance(data, list)
                }
            else:
                return {
                    "success": False,
                    "error": f"Status code: {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Run API tests"""
    tester = ConversationalAPITest()
    success = tester.run_api_tests()
    
    if success:
        print("\n💡 Next Steps:")
        print("   1. Test the conversational UI in the frontend")
        print("   2. Try real conversations in different workspaces")
        print("   3. Test confirmation workflows")
        print("   4. Verify context awareness across chats")
    else:
        print("\n💡 Troubleshooting:")
        print("   1. Ensure server is running: python main.py")
        print("   2. Check database tables are created")
        print("   3. Verify environment variables are set")
        print("   4. Check server logs for detailed errors")

if __name__ == "__main__":
    main()