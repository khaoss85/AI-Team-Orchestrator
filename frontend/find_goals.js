// Find workspaces with goals to debug the issue

const API_BASE = 'http://localhost:8000'

async function findWorkspacesWithGoals() {
  try {
    console.log('🔍 Searching for workspaces with goals...')
    
    // Try to find workspaces
    let response = await fetch(`${API_BASE}/workspaces`)
    let workspaces = []
    
    if (response.ok) {
      workspaces = await response.json()
      console.log('📊 Total workspaces found:', workspaces.length)
    } else {
      console.log('⚠️ Cannot fetch workspaces directly, trying monitoring endpoint')
      // Try monitoring endpoint
      response = await fetch(`${API_BASE}/monitoring/workspaces`)
      if (response.ok) {
        const data = await response.json()
        workspaces = data.workspaces || []
        console.log('📊 Total workspaces from monitoring:', workspaces.length)
      }
    }
    
    if (workspaces.length === 0) {
      console.log('❌ No workspaces found')
      return
    }
    
    console.log('📋 Checking each workspace for goals...')
    
    for (let i = 0; i < Math.min(10, workspaces.length); i++) {
      const workspace = workspaces[i]
      const workspaceId = workspace.id || workspace.workspace_id
      const workspaceName = workspace.name || workspace.title || 'Unnamed'
      
      console.log(`\n🔍 Workspace ${i+1}: ${workspaceName} (${workspaceId})`)
      
      try {
        const goalResponse = await fetch(`${API_BASE}/api/workspaces/${workspaceId}/goals`)
        if (goalResponse.ok) {
          const goals = await goalResponse.json()
          const goalCount = Array.isArray(goals) ? goals.length : (goals.goals?.length || 0)
          console.log(`  📊 Goals: ${goalCount}`)
          
          if (goalCount > 0) {
            const goalsArray = Array.isArray(goals) ? goals : (goals.goals || [])
            goalsArray.forEach((goal, idx) => {
              console.log(`    🎯 Goal ${idx+1}: ${goal.description || goal.name || goal.title || 'Unnamed'}`)
              console.log(`       Status: ${goal.status}, Progress: ${goal.current_value}/${goal.target_value}`)
              
              // Check if this is our email sequence goal
              if (goal.description?.includes('Email sequence 1') || 
                  goal.title?.includes('Email sequence 1') ||
                  goal.name?.includes('Email sequence 1')) {
                console.log('🎯 *** FOUND EMAIL SEQUENCE GOAL! ***')
                console.log('    ID:', goal.id)
                console.log('    Workspace ID:', workspaceId)
                console.log('    Full goal data:', JSON.stringify(goal, null, 2))
              }
            })
          }
        } else {
          console.log(`  ❌ Could not fetch goals: ${goalResponse.status}`)
        }
      } catch (error) {
        console.log(`  ❌ Error fetching goals: ${error.message}`)
      }
    }
    
  } catch (error) {
    console.error('❌ Error finding workspaces:', error)
  }
}

findWorkspacesWithGoals()