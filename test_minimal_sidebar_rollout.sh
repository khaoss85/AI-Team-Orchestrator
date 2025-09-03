#!/bin/bash

# Test script for minimal sidebar rollout
# This tests that the feature flag works correctly

echo "🧪 Testing Minimal Sidebar Rollout..."

cd /Users/pelleri/Documents/ai-team-orchestrator/frontend

# Test 1: Default state (minimal sidebar disabled)
echo ""
echo "Test 1: Default state (feature flag OFF)"
grep "NEXT_PUBLIC_ENABLE_MINIMAL_SIDEBAR=false" .env.local
if [ $? -eq 0 ]; then
    echo "✅ Feature flag correctly set to false by default"
else
    echo "❌ Feature flag not set correctly"
    exit 1
fi

# Test 2: Redirects enabled
echo ""
echo "Test 2: Legacy redirects enabled"
grep "NEXT_PUBLIC_ENABLE_LEGACY_REDIRECTS=true" .env.local
if [ $? -eq 0 ]; then
    echo "✅ Legacy redirects enabled for safe migration"
else
    echo "❌ Legacy redirects not configured"
    exit 1
fi

# Test 3: Check middleware is correctly configured
echo ""
echo "Test 3: Middleware configuration"
if [ -f "middleware.ts" ]; then
    echo "✅ Middleware file exists"
    
    # Check for redirect routes
    grep -q "/teams" middleware.ts && grep -q "/tools" middleware.ts
    if [ $? -eq 0 ]; then
        echo "✅ Redirect routes configured in middleware"
    else
        echo "❌ Redirect routes not found in middleware"
        exit 1
    fi
else
    echo "❌ Middleware file not found"
    exit 1
fi

# Test 4: Check minimal sidebar component exists
echo ""
echo "Test 4: Minimal sidebar component"
if [ -f "src/components/MinimalFloatingSidebar.tsx" ]; then
    echo "✅ MinimalFloatingSidebar component exists"
    
    # Check for accessibility features
    grep -q "aria-label" src/components/MinimalFloatingSidebar.tsx
    if [ $? -eq 0 ]; then
        echo "✅ Component has accessibility features"
    else
        echo "⚠️  Warning: Component may lack accessibility features"
    fi
else
    echo "❌ MinimalFloatingSidebar component not found"
    exit 1
fi

# Test 5: Check new pages exist
echo ""
echo "Test 5: Migration pages"
if [ -f "src/app/library/page.tsx" ] && [ -f "src/app/profile/page.tsx" ]; then
    echo "✅ Library and Profile pages created"
else
    echo "❌ Migration pages not found"
    exit 1
fi

# Test 6: Check if old routes still exist (should be removed later)
echo ""
echo "Test 6: Old route cleanup status"
if [ -f "src/app/teams/page.tsx" ]; then
    echo "⚠️  Old /teams route still exists (will be cleaned up)"
fi
if [ -f "src/app/tools/page.tsx" ]; then
    echo "⚠️  Old /tools route still exists (will be cleaned up)"
fi

echo ""
echo "🎯 Rollout Readiness Assessment:"
echo "✅ Feature flags configured for safe deployment"
echo "✅ Redirects in place to prevent broken links"
echo "✅ New components ready for activation"
echo "✅ Migration pages available"
echo ""
echo "📋 To enable minimal sidebar:"
echo "1. Change NEXT_PUBLIC_ENABLE_MINIMAL_SIDEBAR=true in .env.local"
echo "2. Test with small user group"
echo "3. Monitor for any issues"
echo "4. Clean up old components when stable"
echo ""
echo "🚀 Ready for gradual rollout!"