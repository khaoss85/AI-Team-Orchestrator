#!/bin/bash

WORKSPACE_ID="2d8d4059-aaee-4980-80c8-aa11269aa85d"
API_BASE="http://localhost:8000"

echo "=== Testing Unified Assets API ==="
echo "URL: ${API_BASE}/unified-assets/workspace/${WORKSPACE_ID}"
echo ""

# Test unified assets API
unified_response=$(curl -s "${API_BASE}/unified-assets/workspace/${WORKSPACE_ID}")
echo "Unified Assets Response:"
echo "$unified_response" | head -20

echo ""
echo "=== Testing Monitoring Asset Tracking API ==="
echo "URL: ${API_BASE}/monitoring/workspace/${WORKSPACE_ID}/asset-tracking"
echo ""

# Test monitoring asset tracking API  
monitoring_response=$(curl -s "${API_BASE}/monitoring/workspace/${WORKSPACE_ID}/asset-tracking")
echo "Monitoring Assets Response:"
echo "$monitoring_response" | head -20

echo ""
echo "=== Quick Analysis ==="

# Check if responses contain data
if echo "$unified_response" | grep -q '"asset_count"'; then
    asset_count=$(echo "$unified_response" | grep -o '"asset_count":[0-9]*' | cut -d: -f2)
    echo "Unified API asset_count: $asset_count"
else
    echo "Unified API: No asset_count found or API error"
fi

if echo "$monitoring_response" | grep -q '"total_assets_found"'; then
    total_found=$(echo "$monitoring_response" | grep -o '"total_assets_found":[0-9]*' | cut -d: -f2)
    echo "Monitoring API total_assets_found: $total_found"
else
    echo "Monitoring API: No total_assets_found or API error"
fi