#!/bin/bash

# 🎯 Lead Generation System Rollout Script
# Adds shared lead generation components to all English ebook pages
# Author: Claude Code AI Assistant

set -e  # Exit on any error

echo "🚀 Starting Lead Generation System Rollout..."
echo "📊 Found $(find en -name "index.html" -type f | wc -l | tr -d ' ') English pages to update"

# Counter for tracking progress
UPDATED_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

# Function to calculate relative path to shared components
calculate_relative_path() {
    local file_path="$1"
    local depth=$(echo "$file_path" | tr '/' '\n' | wc -l | tr -d ' ')
    
    # For en/index.html (depth 2), relative path is "./"
    # For en/category/index.html (depth 3), relative path is "../"  
    # For en/category/subcategory/index.html (depth 4), relative path is "../../"
    
    local relative_path=""
    for ((i=2; i<depth; i++)); do
        relative_path="../$relative_path"
    done
    
    # If still empty, it's the root en/ directory
    if [[ -z "$relative_path" ]]; then
        relative_path="./"
    fi
    
    echo "$relative_path"
}

# Function to add shared components to a single file
add_shared_components() {
    local file="$1"
    local relative_path=$(calculate_relative_path "$file")
    
    echo "📝 Processing: $file (relative path: ${relative_path})"
    
    # Check if file already has shared components
    if grep -q "shared-lead-generation.css" "$file"; then
        echo "   ⚠️  Already has shared components, skipping..."
        ((SKIPPED_COUNT++))
        return 0
    fi
    
    # Create backup
    cp "$file" "$file.backup"
    
    # Add CSS link in <head> section (before closing </head>)
    if ! sed -i '' "/<\/head>/i\\
    <!-- Shared Lead Generation System -->\\
    <link rel=\"stylesheet\" href=\"${relative_path}shared-lead-generation.css?v=1.4\">
" "$file"; then
        echo "   ❌ Failed to add CSS link"
        mv "$file.backup" "$file"  # Restore backup
        ((FAILED_COUNT++))
        return 1
    fi
    
    # Add JavaScript before closing </body>
    if ! sed -i '' "/<\/body>/i\\
    <!-- Shared Lead Generation System -->\\
    <script src=\"${relative_path}shared-lead-generation.js?v=1.4\"></script>
" "$file"; then
        echo "   ❌ Failed to add JavaScript"
        mv "$file.backup" "$file"  # Restore backup  
        ((FAILED_COUNT++))
        return 1
    fi
    
    # Remove backup if successful
    rm "$file.backup"
    ((UPDATED_COUNT++))
    echo "   ✅ Successfully updated"
    return 0
}

# Process all English index.html files
echo ""
echo "🔄 Processing files..."
echo ""

find en -name "index.html" -type f | sort | while read file; do
    add_shared_components "$file"
done

# Update counters (need to use files since subshell can't modify parent variables)
UPDATED_COUNT=$(find en -name "index.html" -type f -exec grep -l "shared-lead-generation.css" {} \; | wc -l | tr -d ' ')
TOTAL_COUNT=$(find en -name "index.html" -type f | wc -l | tr -d ' ')

echo ""
echo "📊 Rollout Summary:"
echo "   ✅ Successfully updated: $UPDATED_COUNT files"
echo "   ⚠️  Skipped (already had components): $((TOTAL_COUNT - UPDATED_COUNT)) files"
echo "   📁 Total files processed: $TOTAL_COUNT files"
echo ""

if [[ $UPDATED_COUNT -gt 0 ]]; then
    echo "🎯 Lead Generation System successfully deployed to $UPDATED_COUNT English pages!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Test a few pages to verify functionality"
    echo "   2. Monitor browser console for any JavaScript errors"
    echo "   3. Check popup functionality with different triggers"
    echo "   4. Commit changes to git when satisfied"
    echo ""
    echo "🧪 Quick Test Commands:"
    echo "   open http://localhost:8888/en/core-philosophy-architecture/15-pillars-ai-system/"
    echo "   open http://localhost:8888/en/execution-quality/quality-gates-human-loop/"
    echo "   open http://localhost:8888/en/memory-system-scaling/semantic-caching/"
else
    echo "ℹ️  All files already had lead generation components - no updates needed."
fi

echo "✨ Rollout completed!"