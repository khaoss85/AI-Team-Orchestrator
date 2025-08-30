#!/bin/bash

# 🔄 Lead Generation System Update Script
# Automatically copies shared files to all language directories
# Run this script after modifying shared-lead-generation.js or .css

set -e

echo "🔄 Updating Lead Generation System..."
echo ""

# Check if source files exist
if [[ ! -f "shared-lead-generation.js" ]]; then
    echo "❌ Error: shared-lead-generation.js not found in current directory"
    exit 1
fi

if [[ ! -f "shared-lead-generation.css" ]]; then
    echo "❌ Error: shared-lead-generation.css not found in current directory"
    exit 1
fi

echo "📂 Source files found:"
echo "   ✅ shared-lead-generation.js ($(wc -c < shared-lead-generation.js) bytes)"
echo "   ✅ shared-lead-generation.css ($(wc -c < shared-lead-generation.css) bytes)"
echo ""

# Copy to English directory
if [[ -d "en" ]]; then
    cp shared-lead-generation.js en/
    cp shared-lead-generation.css en/
    echo "✅ English directory updated (en/)"
else
    echo "⚠️  English directory (en/) not found"
fi

# Copy to Italian directory
if [[ -d "it" ]]; then
    cp shared-lead-generation.js it/
    cp shared-lead-generation.css it/
    echo "✅ Italian directory updated (it/)"
else
    echo "⚠️  Italian directory (it/) not found"
fi

# Future language directories
for lang_dir in es fr de; do
    if [[ -d "$lang_dir" ]]; then
        cp shared-lead-generation.js "$lang_dir/"
        cp shared-lead-generation.css "$lang_dir/"
        echo "✅ $lang_dir directory updated"
    fi
done

echo ""
echo "🎯 Lead Generation System Update Complete!"
echo ""
echo "📋 What was updated:"
echo "   • shared-lead-generation.js copied to all language directories"
echo "   • shared-lead-generation.css copied to all language directories"
echo ""
echo "💡 Next steps:"
echo "   • Test functionality on a few pages"
echo "   • Clear browser cache if needed (Cmd+Shift+R)"
echo "   • All pages now use the latest lead generation system"
echo ""
echo "🚀 Ready for production!"