#!/bin/bash

# 🚀 Italian Lead Generation System Rollout Script
# Automatically adds lead generation components to all Italian ebook pages
# Based on the successful English rollout

set -e

echo "🇮🇹 Italian Lead Generation System Rollout Starting..."
echo ""

# Counter for processed files
processed_count=0
failed_count=0

# Find all Italian index.html files
echo "🔍 Scanning for Italian pages..."
italian_pages=$(find it/ -name "index.html" -type f | grep -v shared | sort)
total_pages=$(echo "$italian_pages" | wc -l | tr -d ' ')

echo "📊 Found $total_pages Italian pages to process"
echo ""

# Process each page
for page in $italian_pages; do
    echo "📝 Processing: $page"
    
    # Check if already has lead generation
    if grep -q "shared-lead-generation.js" "$page"; then
        echo "   ⚠️  Already has lead generation system - skipping"
        ((processed_count++))
        continue
    fi
    
    # Get the relative path depth (count slashes)
    depth=$(echo "$page" | tr -cd '/' | wc -c)
    depth=$((depth - 1))  # Subtract 1 because we start from current directory
    
    # Create relative path to parent directory
    relative_path=""
    for ((i=0; i<depth; i++)); do
        relative_path="../$relative_path"
    done
    
    echo "   🎯 Depth: $depth, Relative path: ${relative_path}"
    
    # Create backup
    cp "$page" "${page}.backup"
    
    # Add lead generation components before closing head tag
    if sed -i.tmp "
        /<\/head>/ i\\
        \\
        <!-- 🎯 Shared Lead Generation System -->\\
        <link rel=\"stylesheet\" href=\"${relative_path}shared-lead-generation.css\">\\
        <script src=\"${relative_path}shared-lead-generation.js\"></script>
    " "$page"; then
        rm "${page}.tmp"
        rm "${page}.backup"
        echo "   ✅ Successfully added lead generation system"
        ((processed_count++))
    else
        # Restore backup if failed
        mv "${page}.backup" "$page"
        echo "   ❌ Failed to process - restored backup"
        ((failed_count++))
    fi
    
    echo ""
done

echo "🏁 Italian Lead Generation Rollout Complete!"
echo ""
echo "📊 Summary:"
echo "   • Total pages found: $total_pages"
echo "   • Successfully processed: $processed_count"
echo "   • Failed: $failed_count"
echo "   • Already had system: $((total_pages - processed_count - failed_count))"
echo ""
echo "🧪 Next steps:"
echo "   • Test a few random Italian pages"
echo "   • Check browser console for any errors"
echo "   • Verify popup functionality works correctly"
echo ""
echo "🎯 Test URLs:"
echo "   • http://localhost:8888/it/filosofia-core-architettura/prefazione/"
echo "   • http://localhost:8888/it/esecuzione-qualita/quality-gate-human-loop/"
echo "   • http://localhost:8888/it/user-experience-trasparenza/prossima-frontiera-agente-stratega/"
echo ""

if [ $failed_count -eq 0 ]; then
    echo "🎉 All Italian pages successfully updated!"
else
    echo "⚠️  Some pages failed - check manually if needed"
fi