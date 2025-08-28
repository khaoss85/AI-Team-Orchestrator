// Debug script for Email sequence 1 goal artifacts panel status inconsistency

const WORKSPACE_ID = '4d6c9877-7b68-4a42-bf1f-a2e4d4dc7a91'
const GOAL_NAME = 'Email sequence 1 - Introduzione e valore'
const API_BASE = 'http://localhost:8000'

// Function to find goal by name/description
async function findGoalByName() {
  try {
    console.log('🔍 Finding goal by name:', GOAL_NAME)
    
    const response = await fetch(`${API_BASE}/api/workspaces/${WORKSPACE_ID}/goals`)
    const data = await response.json()
    
    console.log('📊 Total goals found:', Array.isArray(data) ? data.length : data.goals?.length || 0)
    console.log('📊 API response structure:', typeof data, Object.keys(data || {}))
    
    const goalsArray = Array.isArray(data) ? data : (data.goals || [])
    const goal = goalsArray.find(g => 
      g.description?.includes('Email sequence 1') || 
      g.title?.includes('Email sequence 1') ||
      g.name?.includes('Email sequence 1')
    )
    
    if (!goal) {
      console.error('❌ Goal not found!')
      return null
    }
    
    console.log('✅ Goal found:', {
      id: goal.id,
      description: goal.description,
      status: goal.status,
      progress: `${goal.current_value}/${goal.target_value}`,
      progress_percent: goal.target_value > 0 ? (goal.current_value / goal.target_value * 100) : 0
    })
    
    return goal
  } catch (error) {
    console.error('❌ Error finding goal:', error)
    return null
  }
}

// Function to check deliverables for this goal
async function checkGoalDeliverables(goalId) {
  try {
    console.log('\n🎯 Checking deliverables for goal:', goalId)
    
    const response = await fetch(`${API_BASE}/monitoring/workspace/${WORKSPACE_ID}/project/deliverables?goal_id=${goalId}`)
    const data = await response.json()
    
    console.log('📦 Deliverables API response:', data)
    console.log('📦 Deliverables count:', data.key_outputs?.length || 0)
    
    return data.key_outputs || []
  } catch (error) {
    console.error('❌ Error checking deliverables:', error)
    return []
  }
}

// Function to check artifacts panel data structure
async function checkArtifactsPanelDataFlow(goalId) {
  try {
    console.log('\n🔍 Simulating artifacts panel data flow...')
    
    // 1. Check how loadChatSpecificArtifacts loads goal data
    console.log('Step 1: Loading full goal data')
    const goalResponse = await fetch(`${API_BASE}/workspace-goals/${goalId}`)
    let fullGoalData = goalResponse.ok ? await goalResponse.json() : null
    
    if (!fullGoalData) {
      console.warn('⚠️ Could not load individual goal, trying all goals')
      const allGoalsResponse = await fetch(`${API_BASE}/api/workspaces/${WORKSPACE_ID}/goals`)
      const allGoals = await allGoalsResponse.json()
      const goalsArray = Array.isArray(allGoals) ? allGoals : (allGoals.goals || [])
      const foundGoal = goalsArray.find(g => g.id === goalId)
      if (foundGoal) {
        console.log('✅ Found goal in all goals list')
        fullGoalData = foundGoal
      }
    }
    
    if (!fullGoalData) {
      console.error('❌ Could not load full goal data')
      return
    }
    
    console.log('📊 Full goal data:', {
      id: fullGoalData.id,
      status: fullGoalData.status,
      progress: `${fullGoalData.current_value}/${fullGoalData.target_value}`,
      metadata: fullGoalData.metadata
    })
    
    // 2. Calculate progress as artifacts panel does
    const calculatedProgress = fullGoalData.target_value > 0 
      ? (fullGoalData.current_value / fullGoalData.target_value) * 100 
      : 0
    
    console.log('📈 Calculated progress:', Math.min(calculatedProgress, 100), '%')
    
    // 3. Check deliverables
    const deliverables = await checkGoalDeliverables(goalId)
    
    // 4. Check what status ObjectiveArtifact would show
    const artifactStatus = fullGoalData?.status === 'completed' ? 'completed' : 'in_progress'
    console.log('🎯 ObjectiveArtifact status:', artifactStatus)
    
    // 5. Check what getStatusColor would return in ArtifactCard
    const getStatusColor = (status) => {
      switch (status) {
        case 'ready': return 'bg-green-100 text-green-800'
        case 'in_progress': return 'bg-yellow-100 text-yellow-800'
        case 'completed': return 'bg-blue-100 text-blue-800'
        default: return 'bg-gray-100 text-gray-800'
      }
    }
    
    console.log('🎨 ArtifactCard status color class:', getStatusColor(artifactStatus))
    
    // 6. Check content structure that would be passed to ObjectiveArtifact
    const content = {
      objective: {
        id: fullGoalData.id,
        description: fullGoalData.description || fullGoalData.name,
        progress: Math.min(calculatedProgress, 100)
      },
      progress: Math.min(calculatedProgress, 100),
      deliverables: deliverables,
      goal_data: fullGoalData,
      metadata: fullGoalData?.metadata || {},
      target_value: fullGoalData?.target_value,
      current_value: fullGoalData?.current_value,
      metric_type: fullGoalData?.metric_type,
      status: fullGoalData?.status,
      priority: fullGoalData?.priority,
      created_at: fullGoalData?.created_at,
      updated_at: fullGoalData?.updated_at
    }
    
    console.log('\n📋 ObjectiveArtifact content structure:')
    console.log('- Status passed to ObjectiveArtifact:', content.status)
    console.log('- Progress passed to ObjectiveArtifact:', content.progress, '%')
    console.log('- Deliverables count:', deliverables.length)
    
    // 7. Debug ObjectiveArtifact status logic
    console.log('\n🔍 ObjectiveArtifact status logic:')
    console.log('- objectiveData.status:', content.status)
    console.log('- getStatusColor input:', content.status)
    
    const getStatusColorObjective = (status) => {
      const statusStr = String(status || '').toLowerCase()
      switch (statusStr) {
        case 'completed': return 'bg-green-100 text-green-800'
        case 'active': return 'bg-blue-100 text-blue-800'  
        case 'paused': return 'bg-yellow-100 text-yellow-800'
        case 'cancelled': return 'bg-red-100 text-red-800'
        default: return 'bg-gray-100 text-gray-800'
      }
    }
    
    console.log('- ObjectiveArtifact status color:', getStatusColorObjective(content.status))
    
    // 8. Check artifacts panel vs ObjectiveArtifact status mismatch
    console.log('\n⚠️ STATUS INCONSISTENCY ANALYSIS:')
    console.log('- ArtifactCard shows:', artifactStatus, '(', getStatusColor(artifactStatus), ')')
    console.log('- ObjectiveArtifact shows:', content.status, '(', getStatusColorObjective(content.status), ')')
    console.log('- Progress shows:', content.progress, '%')
    
    if (artifactStatus === 'in_progress' && content.progress >= 100) {
      console.log('🚨 FOUND INCONSISTENCY: Artifact shows "in_progress" but progress is 100%!')
      console.log('- Root cause: ArtifactCard uses artifact.status which is set to "completed" ? "completed" : "in_progress"')
      console.log('- But goal.status is:', fullGoalData.status)
      console.log('- Expected: ArtifactCard should show "completed" when goal.status is "completed"')
    }
    
  } catch (error) {
    console.error('❌ Error in artifacts panel analysis:', error)
  }
}

// Main execution
async function main() {
  console.log('🐛 Debugging Email sequence 1 goal artifacts panel status inconsistency\n')
  
  const goal = await findGoalByName()
  if (!goal) {
    console.error('Cannot continue without goal data')
    return
  }
  
  const deliverables = await checkGoalDeliverables(goal.id)
  
  console.log('\n📋 SUMMARY:')
  console.log('- Goal status:', goal.status)
  console.log('- Goal progress:', goal.target_value > 0 ? (goal.current_value / goal.target_value * 100).toFixed(1) : 0, '%')
  console.log('- Deliverables found:', deliverables.length)
  
  if (deliverables.length === 0) {
    console.log('🚨 ISSUE: Progress shows 100% but no deliverables found!')
    console.log('This explains why the deliverables tab is empty.')
  }
  
  await checkArtifactsPanelDataFlow(goal.id)
}

main().catch(console.error)