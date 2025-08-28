// Debug script per investigare il goal progress vs deliverables discrepancy
// Esegui nel browser console su http://localhost:3000

async function debugGoalProgress() {
  const workspaceId = "db18803c-3718-4612-a34b-79b1167ac62f"
  const goalId = "36228534-d5db-4f12-8cda-21efe0c6373c" // Email campaign goal al 67%
  
  console.log("🔍 Debugging Goal Progress for:", goalId)
  console.log("=" + "=".repeat(80))
  
  try {
    // Get goal data
    console.log("📊 Fetching goal data...")
    const goalsResponse = await fetch(`http://localhost:8000/api/workspace-goals/${workspaceId}`)
    const goals = await goalsResponse.json()
    const goal = goals.find(g => g.id === goalId)
    
    if (!goal) {
      console.error("❌ Goal not found!")
      return
    }
    
    console.log("📊 GOAL OVERVIEW:")
    console.log(`   Title: ${goal.title || 'N/A'}`)
    console.log(`   Progress: ${goal.progress || 0}%`)
    console.log(`   Status: ${goal.status || 'unknown'}`)
    console.log(`   Current Value: ${goal.current_value || 0}`)
    console.log(`   Target Value: ${goal.target_value || 0}`)
    console.log("")
    
    // Get deliverables for this goal
    console.log("📦 Fetching deliverables...")
    const deliverablesResponse = await fetch(`http://localhost:8000/api/deliverables/workspace/${workspaceId}/goal/${goalId}`)
    const deliverables = await deliverablesResponse.json()
    
    console.log(`📦 DELIVERABLES BREAKDOWN (${deliverables.length} total):`)
    
    const deliverableStats = {}
    deliverables.forEach(deliverable => {
      const status = deliverable.status || 'unknown'
      deliverableStats[status] = (deliverableStats[status] || 0) + 1
      
      console.log(`   • ${(deliverable.title || 'No title').substring(0, 60)}`)
      console.log(`     Status: ${status} | Type: ${deliverable.type || 'N/A'}`)
      console.log(`     Task ID: ${deliverable.task_id || 'None'}`)
      console.log(`     Business Value: ${deliverable.business_value_score || 'N/A'}`)
      console.log("")
    })
    
    console.log("📊 DELIVERABLE STATUS SUMMARY:")
    Object.entries(deliverableStats).forEach(([status, count]) => {
      const percentage = deliverables.length ? (count / deliverables.length * 100) : 0
      console.log(`   ${status}: ${count} deliverables (${percentage.toFixed(1)}%)`)
    })
    console.log("")
    
    // Get all deliverables for workspace (to see what might be missing)
    console.log("🔍 Fetching ALL workspace deliverables...")
    const allDeliverablesResponse = await fetch(`http://localhost:8000/api/deliverables/workspace/${workspaceId}`)
    const allDeliverables = await allDeliverablesResponse.json()
    
    // Filter to find deliverables that might be related to this goal
    const possibleGoalDeliverables = allDeliverables.filter(d => 
      d.goal_id === goalId || 
      (d.title && (
        d.title.toLowerCase().includes('email') ||
        d.title.toLowerCase().includes('campaign') ||
        d.title.toLowerCase().includes('marketing')
      ))
    )
    
    console.log(`🔍 POSSIBLE GOAL-RELATED DELIVERABLES (${possibleGoalDeliverables.length} total):`)
    const allStats = {}
    possibleGoalDeliverables.forEach(deliverable => {
      const status = deliverable.status || 'unknown'
      allStats[status] = (allStats[status] || 0) + 1
      
      if (deliverable.goal_id !== goalId) {
        console.log(`   • ${(deliverable.title || 'No title').substring(0, 60)} [ORPHANED]`)
        console.log(`     Status: ${status} | Goal ID: ${deliverable.goal_id || 'None'}`)
      }
    })
    
    console.log("📈 ALL STATUS SUMMARY:")
    Object.entries(allStats).forEach(([status, count]) => {
      const percentage = possibleGoalDeliverables.length ? (count / possibleGoalDeliverables.length * 100) : 0
      console.log(`   ${status}: ${count} deliverables (${percentage.toFixed(1)}%)`)
    })
    console.log("")
    
    // Analysis
    const completedCount = deliverableStats.completed || 0
    const totalCount = deliverables.length
    const completedPercentage = totalCount ? (completedCount / totalCount * 100) : 0
    
    console.log("🔢 ANALYSIS:")
    console.log(`   Goal Progress: ${goal.progress || 0}%`)
    console.log(`   Deliverables Completed: ${completedCount}/${totalCount} (${completedPercentage.toFixed(1)}%)`)
    console.log(`   Showing in UI: Only 'completed' deliverables`)
    console.log("")
    
    // Show what's hidden from UI
    const hiddenDeliverables = deliverables.filter(d => d.status !== 'completed')
    if (hiddenDeliverables.length > 0) {
      console.log(`👀 HIDDEN FROM UI (${hiddenDeliverables.length} items):`)
      hiddenDeliverables.forEach(deliverable => {
        console.log(`   • ${(deliverable.title || 'No title').substring(0, 60)}`)
        console.log(`     Status: ${deliverable.status} | Why hidden: Status not 'completed'`)
      })
      console.log("")
    }
    
    console.log("🎯 RECOMMENDATIONS:")
    console.log("   1. Show ALL deliverable statuses in UI, not just 'completed'")
    console.log("   2. Add status indicators (completed/failed/pending/in_progress)")
    console.log("   3. Provide unblocking actions for failed/pending items")
    console.log("   4. Fix orphaned deliverables with goal_id = null")
    console.log("   5. Match UI progress display with actual deliverable completion")
    
  } catch (error) {
    console.error("❌ Error:", error)
  }
}

// Auto-run the debug
debugGoalProgress()