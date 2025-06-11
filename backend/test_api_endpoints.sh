#!/bin/bash
# Test script for unified asset management API endpoints
# Uses the discovered workspace with real deliverable data

WORKSPACE_ID="2d8d4059-aaee-4980-80c8-aa11269aa85d"
BASE_URL="http://localhost:8000"

echo "🧪 TESTING UNIFIED ASSET MANAGEMENT API ENDPOINTS"
echo "=================================================="
echo "Workspace ID: $WORKSPACE_ID"
echo "Base URL: $BASE_URL"
echo ""

echo "🔧 Testing API endpoints (make sure backend is running on port 8000)..."
echo ""

# Test 1: Project deliverables endpoint
echo "📋 1. Testing Project Deliverables endpoint:"
echo "   URL: $BASE_URL/projects/$WORKSPACE_ID/deliverables"
echo "   Command: curl -s $BASE_URL/projects/$WORKSPACE_ID/deliverables | jq ."
echo ""

# Test 2: Project insights endpoint  
echo "📊 2. Testing Project Insights endpoint:"
echo "   URL: $BASE_URL/projects/$WORKSPACE_ID/insights"
echo "   Command: curl -s $BASE_URL/projects/$WORKSPACE_ID/insights | jq ."
echo ""

# Test 3: Asset management endpoint
echo "🎯 3. Testing Asset Management endpoint:"
echo "   URL: $BASE_URL/assets/workspace/$WORKSPACE_ID"
echo "   Command: curl -s $BASE_URL/assets/workspace/$WORKSPACE_ID | jq ."
echo ""

echo "🌐 FRONTEND URLS TO TEST:"
echo "   Deliverables: http://localhost:3000/projects/$WORKSPACE_ID/deliverables"
echo "   Assets: http://localhost:3000/projects/$WORKSPACE_ID/assets"
echo "   Overview: http://localhost:3000/projects/$WORKSPACE_ID"
echo ""

echo "📋 TO START TESTING:"
echo "1. Start the backend: cd backend && python main.py"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Test API endpoints with the curl commands above"
echo "4. Test frontend by opening the URLs in your browser"
echo ""

echo "🎯 SPECIFIC TEST SCENARIOS:"
echo "   ✅ Check that deliverables are returned with rich content"
echo "   ✅ Verify assets show actionability scores and usage guidance"
echo "   ✅ Confirm visual summaries are generated for structured data"
echo "   ✅ Test that markup processing works for tables/cards/metrics"
echo "   ✅ Verify the unified asset viewer displays properly"