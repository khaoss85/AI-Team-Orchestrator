#!/bin/bash

WORKSPACE_ID="2d8d4059-aaee-4980-80c8-aa11269aa85d"
API_BASE="http://localhost:8000"

echo "=== Testing Unified Assets API ==="
echo "URL: ${API_BASE}/unified-assets/workspace/${WORKSPACE_ID}"
echo ""

# Test unified assets API
curl -s "${API_BASE}/unified-assets/workspace/${WORKSPACE_ID}" | jq '{
  workspace_id: .workspace_id,
  asset_count: .asset_count, 
  total_versions: .total_versions,
  data_source: .data_source,
  asset_keys: (.assets | keys),
  first_asset: (.assets | to_entries | first | .value | {name, type, ready_to_use})
}'

echo ""
echo "=== Testing Monitoring Asset Tracking API ==="
echo "URL: ${API_BASE}/monitoring/workspace/${WORKSPACE_ID}/asset-tracking"
echo ""

# Test monitoring asset tracking API
curl -s "${API_BASE}/monitoring/workspace/${WORKSPACE_ID}/asset-tracking" | jq '{
  total_assets_found: .asset_summary.total_assets_found,
  completed_asset_tasks: .asset_summary.completed_asset_tasks,
  asset_keys: (.extracted_assets | keys),
  first_asset: (.extracted_assets | to_entries | first | .value | {asset_name, ready_to_use, extraction_method})
}'