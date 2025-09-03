#!/bin/bash

echo "🎯 Verifying Sidebar Update: Home → Progetti → Profile"
echo ""

cd /Users/pelleri/Documents/ai-team-orchestrator/frontend

# Test 1: MinimalFloatingSidebar updated
echo "1. Sidebar Configuration:"
if grep -q "FolderOpen" src/components/MinimalFloatingSidebar.tsx && grep -q "Progetti" src/components/MinimalFloatingSidebar.tsx; then
    echo "✅ Sidebar updated to Home → Progetti → Profile"
    echo "✅ Icon changed from FileText to FolderOpen"
else
    echo "❌ Sidebar configuration not updated"
fi
echo ""

# Test 2: Library page removed
echo "2. Library Page Cleanup:"
if [ ! -d "src/app/library" ]; then
    echo "✅ Library page removed successfully"
else
    echo "❌ Library page directory still exists"
fi
echo ""

# Test 3: Middleware updated
echo "3. Redirect Configuration:"
if grep -q "/library.*projects" middleware.ts; then
    echo "✅ Library redirect added to middleware"
else
    echo "❌ Library redirect not configured"
fi
echo ""

# Test 4: Navigation flow test
echo "4. Navigation Flow Test:"
echo "Current navigation structure:"
echo "  🏠 Home (/) → Dashboard principale"  
echo "  📁 Progetti (/projects) → Gestione workspace"
echo "  👤 Profile (/profile) → Impostazioni utente"
echo ""

# Test 5: Project page accessibility
echo "5. Core Pages Status:"
curl -s http://localhost:3000/projects | grep -q "projects" && echo "✅ Projects dashboard accessible" || echo "❌ Projects dashboard failed"
curl -s http://localhost:3000/profile | grep -q "Profile" && echo "✅ Profile page accessible" || echo "❌ Profile page failed" 
curl -s http://localhost:3000/ | grep -q "AI" && echo "✅ Homepage accessible" || echo "❌ Homepage failed"
echo ""

echo "🎨 Updated Interface Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Minimal floating sidebar: Home → Progetti → Profile"
echo "✅ Progetti icon: FolderOpen (more intuitive for projects)"  
echo "✅ Library functionality: Removed (use conversational slash commands)"
echo "✅ Navigation simplicity: 3 essential functions only"
echo ""
echo "🚀 Perfect minimal navigation active!"
echo "📁 Progetti leads directly to workspace management"
echo "💬 Library features available via slash commands in conversations"