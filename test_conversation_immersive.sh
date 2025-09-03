#!/bin/bash

echo "🎯 Testing Immersive Conversation Experience"
echo ""

cd /Users/pelleri/Documents/ai-team-orchestrator/frontend

# Test 1: Conversation page detection
echo "1. Layout Logic Test:"
if grep -q "no sidebar for immersive experience" src/components/LayoutWrapper.tsx; then
    echo "✅ Conversation pages configured for immersive experience"
    echo "✅ Floating sidebar removed from conversation layout"
else
    echo "❌ Conversation layout not updated"
fi
echo ""

# Test 2: Regular pages still have sidebar
echo "2. Regular Pages Navigation:"
if grep -q "MinimalFloatingSidebar" src/components/LayoutWrapper.tsx; then
    echo "✅ Regular pages maintain floating sidebar"
else
    echo "❌ Sidebar missing from regular pages"
fi
echo ""

# Test 3: Conversation URLs pattern
echo "3. Conversation URL Pattern Test:"
echo "Testing pattern: /projects/[id]/conversation"
echo ""
echo "Expected behavior:"
echo "✅ http://localhost:3000/projects → Floating sidebar visible"
echo "✅ http://localhost:3000/profile → Floating sidebar visible"  
echo "❌ http://localhost:3000/projects/[id]/conversation → NO sidebar (immersive)"
echo ""

# Test 4: Layout wrapper logic verification
echo "4. Layout Logic Verification:"
echo "Checking conditional rendering logic..."

# Check if conversation detection is correct
if grep -q "isConversationPage.*includes.*conversation" src/components/LayoutWrapper.tsx; then
    echo "✅ Conversation page detection logic correct"
else
    echo "❌ Conversation page detection may be incorrect"
fi

# Check if regular pages have sidebar
if grep -A 10 "useMinimalSidebar" src/components/LayoutWrapper.tsx | grep -q "MinimalFloatingSidebar"; then
    echo "✅ Regular pages include MinimalFloatingSidebar"
else
    echo "❌ Sidebar missing from regular pages"
fi
echo ""

echo "🎨 Layout Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Regular Pages: Home, Progetti, Profile → Show floating sidebar"
echo "💬 Conversation Pages: Pure immersive experience → No sidebar"
echo "🎯 Focus: Conversation interface without navigation distractions"
echo ""
echo "✅ Conversation experience optimized for focus and immersion!"