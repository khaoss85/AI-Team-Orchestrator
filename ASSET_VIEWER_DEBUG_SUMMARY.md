# SmartAssetViewer Debug Summary

## Issue Identified
The SmartAssetViewer was showing "No data available for this asset" because of a data structure mismatch between backend and frontend.

## Root Cause
- **Backend Structure**: The unified assets API returns assets with a `content` field containing the actual data
- **Frontend Expectation**: The SmartAssetViewer expected an `asset_data` field containing the actual data
- **Missing Mapping**: No conversion between the two structures

## Backend Structure (unified_assets.py)
```json
{
  "assets": {
    "asset_key": {
      "id": "asset_key",
      "name": "Asset Name",
      "type": "asset_type",
      "content": {
        "structured_content": {...},
        "rendered_html": "...",
        "has_ai_enhancement": true
      }
    }
  }
}
```

## Frontend Expectation (ActionableAsset type)
```json
{
  "asset_name": "...",
  "name": "...",
  "asset_data": {...}
}
```

## Fix Applied

### 1. SmartAssetViewer.tsx Updates
- Added compatibility layer: `const assetData = asset.asset_data || asset.content || {};`
- Updated all references to use the compatible `assetData` variable
- Added debug logging to track the data flow
- Updated the raw data tab to show both structures

### 2. Parent Component Updates (page.tsx)
- Added conversion in `handleViewAssetDetails` to transform unified assets to ActionableAsset format
- Properly maps `content` -> `asset_data` during asset selection
- Added debug logging to track the conversion

## Key Changes
1. **SmartAssetViewer.tsx**: Lines 64-72, 75, 84, 91, 98, 114-117, 154-155, 184-191, 201, 318
2. **page.tsx**: Lines 110-132 (handleViewAssetDetails function)

## Testing
After these changes, the SmartAssetViewer should:
1. Properly handle both `asset_data` and `content` structures
2. Display asset content instead of "No data available"
3. Show debug information in console for troubleshooting
4. Work with the unified assets API response format

## Expected Result
The popup should now show actual asset content with proper rendering of:
- Pre-rendered HTML content
- Structured data
- Array-based content via GenericArrayViewer
- Fallback content display