#!/bin/bash

echo "🧪 Testing AI-Driven Knowledge Categorization System"
echo "================================================="

# Wait for backend to be ready
echo "⏱️  Waiting for backend to initialize..."
sleep 5

echo "🏥 Testing health endpoint..."
curl -X GET "http://localhost:8000/health" -H "Accept: application/json"
echo -e "\n"

echo "🧠 Testing knowledge insights endpoint..."
curl -X GET "http://localhost:8000/api/workspaces/f35639dc-12ae-4720-882d-3e35a70a79b8/knowledge-insights" \
     -H "Accept: application/json" | python3 -m json.tool

echo -e "\n✅ Test completed! Check the response for 'ai_enabled: true'"
echo "📊 Look for these indicators of success:"
echo "   - insights[], bestPractices[], learnings[] arrays populated"
echo "   - ai_enabled: true in response"
echo "   - Dynamic summary with actual content (not hardcoded tags)"
echo "   - Items should have confidence scores and reasoning fields"