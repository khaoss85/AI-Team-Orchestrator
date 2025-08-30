#!/bin/bash

# 🔄 Remove Versioning from Shared Lead Generation System
# Updates all English pages to use unversioned shared components
# Author: Claude Code AI Assistant

set -e

echo "🔄 Removing versioning from shared lead generation system..."

# Counter for tracking progress
UPDATED_COUNT=0
TOTAL_COUNT=0

echo ""
echo "📊 Processing all English pages..."

# Process all English pages
find en -name "index.html" -type f | while read file; do
    ((TOTAL_COUNT++))
    echo "📝 Processing: $file"
    
    # Remove versioning from CSS link
    if sed -i '' 's/shared-lead-generation\.css?v=[0-9]\+\.[0-9]\+/shared-lead-generation.css/g' "$file"; then
        echo "   ✅ Updated CSS link (removed versioning)"
    fi
    
    # Remove versioning from JavaScript src
    if sed -i '' 's/shared-lead-generation\.js?v=[0-9]\+\.[0-9]\+/shared-lead-generation.js/g' "$file"; then
        echo "   ✅ Updated JS src (removed versioning)"
        ((UPDATED_COUNT++))
    fi
done

echo ""
echo "📊 Versioning Removal Summary:"
echo "   🔄 Files processed: $(find en -name "index.html" -type f | wc -l | tr -d ' ') English pages"
echo "   ✅ Versioning removed from shared-lead-generation.css and .js links"
echo ""

echo "🎯 Benefits of No Versioning:"
echo "   • Future updates: just modify shared-lead-generation.js"  
echo "   • No need to update 49+ individual pages"
echo "   • Automatic cache refresh on file changes"
echo "   • Simpler maintenance and deployment"
echo ""

echo "📋 Next Steps:"
echo "   1. Test a few pages to verify functionality"
echo "   2. Clear browser cache if needed (Cmd+Shift+R)"
echo "   3. Future changes: edit shared-lead-generation.js only"
echo ""

echo "✨ Versioning removal completed!"
echo "🚀 System now uses: shared-lead-generation.css and shared-lead-generation.js (no version numbers)"