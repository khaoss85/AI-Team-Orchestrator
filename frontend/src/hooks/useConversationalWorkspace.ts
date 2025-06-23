import { useState, useEffect, useCallback } from 'react'
import { api } from '@/utils/api'
import { 
  ConversationMessage, 
  Chat, 
  DeliverableArtifact, 
  TeamActivity, 
  WorkspaceContext,
  AIResponse 
} from '@/components/conversational/types'

export function useConversationalWorkspace(workspaceId: string) {
  // Core state
  const [chats, setChats] = useState<Chat[]>([])
  const [activeChat, setActiveChat] = useState<Chat | null>(null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [teamActivities, setTeamActivities] = useState<TeamActivity[]>([])
  const [artifacts, setArtifacts] = useState<DeliverableArtifact[]>([])
  const [workspaceContext, setWorkspaceContext] = useState<WorkspaceContext | null>(null)
  const [thinkingSteps, setThinkingSteps] = useState<any[]>([])
  const [suggestedActions, setSuggestedActions] = useState<any[]>([])
  
  // UI state
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sendingMessage, setSendingMessage] = useState(false)
  
  // Workspace health monitoring state
  const [workspaceHealthStatus, setWorkspaceHealthStatus] = useState<any>(null)
  const [healthLoading, setHealthLoading] = useState(false)

  // Initialize workspace and fixed chats
  const initializeWorkspace = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch workspace data with detailed logging
      console.log('🔍 [ConversationalWorkspace] Fetching data for workspace:', workspaceId)
      
      // Test simple backend connection first
      try {
        const testResponse = await fetch('http://localhost:8000/')
        const testData = await testResponse.json()
        console.log('🟢 [ConversationalWorkspace] Backend connection test:', testData)
      } catch (error) {
        console.error('🔴 [ConversationalWorkspace] Backend connection failed:', error)
      }
      
      const [workspace, goals, team] = await Promise.all([
        api.workspaces.get(workspaceId).then(data => {
          console.log('✅ [ConversationalWorkspace] Workspace loaded:', data)
          return data
        }).catch(error => {
          console.error('❌ [ConversationalWorkspace] Workspace fetch failed:', error)
          console.error('❌ [ConversationalWorkspace] Error details:', error.message || error)
          // Return mock data for now
          return {
            id: workspaceId,
            name: 'Test Workspace',
            domain: 'test',
            status: 'active'
          }
        }),
        api.workspaceGoals.getAll(workspaceId).then(data => {
          console.log('✅ [ConversationalWorkspace] Goals loaded:', data)
          return data || []
        }).catch(error => {
          console.error('❌ [ConversationalWorkspace] Goals fetch failed:', error)
          return []
        }),
        api.agents.list(workspaceId).then(data => {
          console.log('✅ [ConversationalWorkspace] Team loaded:', data)
          return data || []
        }).catch(error => {
          console.error('❌ [ConversationalWorkspace] Team fetch failed:', error)
          console.error('❌ [ConversationalWorkspace] Team error details:', error.message || error)
          // Return mock team data for now
          return [
            {
              id: 'agent-1',
              name: 'Project Manager',
              role: 'project_manager',
              seniority: 'senior',
              status: 'active',
              skills: ['project_management', 'coordination']
            },
            {
              id: 'agent-2', 
              name: 'Content Specialist',
              role: 'content_specialist',
              seniority: 'expert',
              status: 'active',
              skills: ['content_creation', 'copywriting']
            }
          ]
        })
      ])

      if (!workspace) {
        throw new Error('Workspace not found')
      }

      // Set workspace context
      const contextData = {
        id: workspaceId,
        name: workspace.name || 'Untitled Workspace',
        domain: workspace.domain,
        goals: goals || [],
        team: team || [],
        configuration: workspace
      }
      
      console.log('🔧 [ConversationalWorkspace] Setting context:', contextData)
      setWorkspaceContext(contextData)

      // Initialize fixed chats
      const fixedChats: Chat[] = [
        {
          id: 'team-management',
          type: 'fixed',
          systemType: 'team',
          title: 'Team Management',
          icon: '👥',
          status: 'active'
        },
        {
          id: 'configuration',
          type: 'fixed',
          systemType: 'configuration',
          title: 'Configuration',
          icon: '⚙️',
          status: 'active'
        },
        {
          id: 'feedback-requests',
          type: 'fixed',
          systemType: 'feedback',
          title: 'Feedback Requests',
          icon: '💬',
          status: 'active'
        },
        {
          id: 'knowledge-base',
          type: 'fixed',
          systemType: 'knowledge',
          title: 'Knowledge Base',
          icon: '📚',
          status: 'active'
        },
        {
          id: 'available-tools',
          type: 'fixed',
          systemType: 'tools',
          title: 'Available Tools',
          icon: '🛠️',
          status: 'active'
        }
      ]

      // Load dynamic chats (stored objectives)
      const dynamicChats = await loadDynamicChats()

      setChats([...fixedChats, ...dynamicChats])
      
      // Set default active chat to team management
      const defaultChat = fixedChats[0]
      setActiveChat(defaultChat)
      
      // Load initial artifacts
      await loadArtifacts()
      
      // 🔧 FIX: Goal progress will be refreshed via useEffect after refreshGoalProgress is defined

    } catch (err: any) {
      console.error('Failed to initialize workspace:', err)
      setError(err.message || 'Failed to load workspace')
    } finally {
      setLoading(false)
    }
  }, [workspaceId])

  // Load dynamic chats from storage/API
  const loadDynamicChats = useCallback(async (): Promise<Chat[]> => {
    try {
      // Load goals from API to create dynamic chats (load ALL goals, not just active ones)
      console.log('🎯 [initializeWorkspace] Loading goals for workspace:', workspaceId)
      const goals = await api.workspaceGoals.getAll(workspaceId, {}).catch((error) => {
        console.error('❌ [initializeWorkspace] Failed to load goals:', error)
        return []
      })
      
      console.log('📊 [initializeWorkspace] Goals loaded:', goals)
      
      // Extract goals array from API response (API returns {success, goals, deliverable_goals, metric_goals})
      const goalsArray = Array.isArray(goals) ? goals : (goals?.goals || [])
      
      console.log('📋 [initializeWorkspace] Goals array:', goalsArray)
      
      // Create chat objects for each goal - AGNOSTIC: configurable format
      const goalChats: Chat[] = goalsArray.map((goal: any) => {
        console.log('🔧 [initializeWorkspace] Processing goal for chat:', goal)
        
        // Extract meaningful title from available fields, prioritizing user-renamed titles
        const meaningfulTitle = 
          goal.metadata?.custom_title ||  // User-renamed title has highest priority
          goal.title || 
          goal.name || 
          goal.goal_title || 
          goal.description?.substring(0, 50) || 
          goal.metric_type?.replace('_', ' ') || 
          goal.target_metric || 
          `Goal ${goal.id.substring(0, 8)}`
        
        console.log('📝 [initializeWorkspace] Goal title extracted:', meaningfulTitle)
        
        // Calculate progress based on current vs target value
        const calculatedProgress = goal.target_value > 0 
          ? (goal.current_value / goal.target_value) * 100 
          : 0
        
        return {
          id: goal.chat_id || `goal-${goal.id}`, // AGNOSTIC: Use goal.chat_id if provided
          type: 'dynamic' as const,
          title: meaningfulTitle,
          icon: goal.icon || '🎯', // AGNOSTIC: Use goal.icon if provided
          status: (goal.status === 'active' ? 'active' : goal.status === 'completed' ? 'completed' : 'inactive') as const,
          objective: {
            id: goal.id,
            description: goal.description || goal.title || goal.name || meaningfulTitle,
            targetDate: goal.target_date,
            progress: Math.min(calculatedProgress, 100) // Cap at 100%
          },
          messageCount: 0,
          lastMessageDate: goal.updated_at || goal.created_at
        }
      })
      
      console.log('🎯 [initializeWorkspace] Goal chats created:', goalChats)
      
      // Also load any manually created dynamic chats from localStorage
      const stored = localStorage.getItem(`workspace-chats-${workspaceId}`)
      const manualChats = stored ? JSON.parse(stored) : []
      
      // Merge goal chats with manual chats, avoiding duplicates
      const allChats = [...goalChats]
      manualChats.forEach((chat: Chat) => {
        if (!allChats.find(c => c.id === chat.id)) {
          allChats.push(chat)
        }
      })
      
      return allChats
    } catch (error) {
      console.error('Failed to load dynamic chats:', error)
      return []
    }
  }, [workspaceId])

  // Save dynamic chats to storage
  const saveDynamicChats = useCallback((updatedChats: Chat[]) => {
    try {
      const dynamicChats = updatedChats.filter(chat => chat.type === 'dynamic')
      localStorage.setItem(`workspace-chats-${workspaceId}`, JSON.stringify(dynamicChats))
    } catch (error) {
      console.error('Failed to save dynamic chats:', error)
    }
  }, [workspaceId])

  // Load artifacts from various sources
  const loadArtifacts = useCallback(async () => {
    try {
      console.log('📦 [loadArtifacts] Loading artifacts for workspace:', workspaceId)
      
      // Load from multiple sources
      const [assets, deliverables, progress] = await Promise.all([
        api.assetManagement.getUnifiedAssets(workspaceId).then(data => {
          console.log('📦 [loadArtifacts] Assets loaded:', data)
          return data || { assets: [] }
        }).catch(error => {
          console.error('❌ [loadArtifacts] Assets fetch failed:', error)
          return { assets: [] }
        }),
        api.monitoring.getProjectDeliverables(workspaceId).then(data => {
          console.log('📦 [loadArtifacts] Deliverables loaded:', data)
          return data?.key_outputs || []
        }).catch(error => {
          console.error('❌ [loadArtifacts] Deliverables fetch failed:', error)
          return []
        }),
        api.workspaceGoals.getAll(workspaceId).then(data => {
          console.log('📦 [loadArtifacts] Progress/Goals loaded:', data)
          return data || []
        }).catch(error => {
          console.error('❌ [loadArtifacts] Progress fetch failed:', error)
          return []
        })
      ])

      const artifacts: DeliverableArtifact[] = []

      // Skip generic assets loading - artifacts should be chat-specific only
      // Assets will be loaded only for specific chats that need them

      // Convert deliverables to artifacts
      if (deliverables.length > 0) {
        artifacts.push(...deliverables.map(deliverable => ({
          id: deliverable.id || Math.random().toString(),
          type: 'deliverable' as const,
          title: deliverable.title || 'Final Deliverable',
          description: deliverable.description,
          status: 'completed' as const,
          content: deliverable.content,
          metadata: deliverable.metadata,
          lastUpdated: deliverable.lastUpdated || new Date().toISOString()
        })))
      }

      // Team artifacts are now loaded only in chat-specific context
      // This prevents cluttering the general artifacts view

      console.log('📦 [loadArtifacts] Final artifacts:', artifacts)
      
      // Preserve existing inline artifacts (like tools_overview) when loading
      setArtifacts(prev => {
        console.log('📦 [loadArtifacts] Previous artifacts count:', prev.length)
        
        // Find inline artifacts that should be preserved
        const inlineArtifacts = prev.filter(artifact => 
          artifact.id === 'available-tools' || 
          artifact.id === 'project-description'
        )
        
        console.log('📦 [loadArtifacts] Preserving inline artifacts:', inlineArtifacts.length)
        
        // Merge new artifacts with preserved inline artifacts
        const existingIds = new Set(inlineArtifacts.map(a => a.id))
        const newArtifacts = artifacts.filter(a => !existingIds.has(a.id))
        const mergedArtifacts = [...inlineArtifacts, ...newArtifacts]
        
        console.log('📦 [loadArtifacts] Merged artifacts count:', mergedArtifacts.length)
        return mergedArtifacts
      })
    } catch (error) {
      console.error('Failed to load artifacts:', error)
    }
  }, [workspaceId, workspaceContext?.team])

  // Function to refresh goal progress in sidebar
  const refreshGoalProgress = useCallback(async () => {
    try {
      console.log('🔄 [refreshGoalProgress] Refreshing goal progress in sidebar...')
      
      // Fetch fresh goal data
      const response = await api.workspaceGoals.getAll(workspaceId, {})
      const freshGoals = response?.goals || []
      
      if (freshGoals.length === 0) {
        console.log('📋 [refreshGoalProgress] No goals found, skipping progress refresh')
        return
      }
      
      // Update chat progress for goal-based chats
      setChats(prevChats => prevChats.map(chat => {
        if (chat.type === 'dynamic' && chat.objective) {
          // Find the corresponding fresh goal data
          const freshGoal = freshGoals.find(goal => goal.id === chat.objective?.id)
          
          if (freshGoal) {
            // Calculate fresh progress
            const freshProgress = freshGoal.target_value > 0 
              ? (freshGoal.current_value / freshGoal.target_value) * 100 
              : 0
            
            console.log(`📊 [refreshGoalProgress] Updated progress for "${chat.title}": ${chat.objective.progress}% → ${Math.min(freshProgress, 100)}%`)
            
            return {
              ...chat,
              objective: {
                ...chat.objective,
                progress: Math.min(freshProgress, 100) // Cap at 100%
              },
              status: freshGoal.status === 'completed' ? 'completed' : 
                      freshGoal.status === 'active' ? 'active' : 'inactive'
            }
          }
        }
        return chat
      }))
      
    } catch (error) {
      console.error('❌ [refreshGoalProgress] Failed to refresh goal progress:', error)
    }
  }, [workspaceId])

  // Function to check workspace health status
  const checkWorkspaceHealth = useCallback(async () => {
    try {
      setHealthLoading(true)
      console.log('🏥 [checkWorkspaceHealth] Checking workspace health status...')
      
      const healthStatus = await api.monitoring.getWorkspaceHealthStatus(workspaceId)
      setWorkspaceHealthStatus(healthStatus)
      
      console.log('✅ [checkWorkspaceHealth] Health status updated:', healthStatus.status)
      return healthStatus
      
    } catch (error) {
      console.error('❌ [checkWorkspaceHealth] Failed to check workspace health:', error)
      return null
    } finally {
      setHealthLoading(false)
    }
  }, [workspaceId])

  // Function to manually unblock workspace
  const unblockWorkspace = useCallback(async (reason?: string) => {
    try {
      console.log('🔓 [unblockWorkspace] Manually unblocking workspace...')
      
      const result = await api.monitoring.unblockWorkspace(workspaceId, reason)
      
      if (result.success) {
        console.log('✅ [unblockWorkspace] Workspace unblocked successfully')
        // Refresh health status after unblocking
        await checkWorkspaceHealth()
        // Also refresh goal progress
        await refreshGoalProgress()
        return { success: true, message: result.message }
      } else {
        console.error('❌ [unblockWorkspace] Failed to unblock workspace:', result.message)
        return { success: false, message: result.message }
      }
      
    } catch (error) {
      console.error('❌ [unblockWorkspace] Error unblocking workspace:', error)
      return { success: false, message: `Failed to unblock workspace: ${error.message}` }
    }
  }, [workspaceId, checkWorkspaceHealth, refreshGoalProgress])

  // Send message to AI team using real API
  const sendMessage = useCallback(async (content: string) => {
    if (!activeChat || !workspaceContext) return

    setSendingMessage(true)
    
    // Add user message immediately with guaranteed unique ID
    const userMessage: ConversationMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'user',
      content,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])

    try {
      // Show real-time thinking activity
      setTeamActivities([
        {
          agentId: 'ai-assistant',
          agentName: 'AI Assistant',
          activity: 'Processing your request...',
          progress: 30,
          status: 'thinking',
          eta: '10s'
        }
      ])

      // Call the real conversational AI API
      const chatId = activeChat.type === 'fixed' ? activeChat.systemType || activeChat.id : activeChat.id
      const messageId = `msg-${Date.now()}`
      
      console.log('🤖 [sendMessage] Calling conversational AI API', {
        workspaceId: workspaceContext.id,
        chatId,
        content,
        messageId
      })

      const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceContext.id}/chat/thinking`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          chat_id: chatId,
          message_id: messageId,
          context: {
            chat_type: activeChat.type,
            chat_title: activeChat.title,
            workspace_context: {
              name: workspaceContext.name,
              domain: workspaceContext.domain,
              goals_count: workspaceContext.goals.length,
              team_size: workspaceContext.team.length
            }
          }
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      const apiResult = await response.json()
      console.log('✅ [sendMessage] API response received:', apiResult)

      // Extract thinking process from artifacts
      let extractedThinkingSteps: any[] = []
      let extractedSuggestedActions: any[] = []
      
      // First check if message contains inline artifacts
      // Using simple pattern that works - the issue was elsewhere
      const artifactPattern = /\*\*ARTIFACT:(\w+):(.+?)\*\*/g
      let match
      const inlineArtifacts: any[] = []
      
      while ((match = artifactPattern.exec(apiResult.response.message)) !== null) {
        const [fullMatch, artifactType, artifactData] = match
        console.log('🔍 [sendMessage] Extracting artifact:', artifactType)
        console.log('🔍 [sendMessage] Raw artifact data length:', artifactData.length)
        console.log('🔍 [sendMessage] Raw artifact data preview:', artifactData.substring(0, 100))
        try {
          const parsedData = JSON.parse(artifactData)
          console.log('📦 [sendMessage] Successfully parsed inline artifact:', artifactType)
          console.log('📦 [sendMessage] Parsed data keys:', Object.keys(parsedData))
          if (artifactType === 'tools_overview') {
            console.log('🛠️ [sendMessage] Tools count in parsed data:', parsedData.tools?.length || 0)
          }
          
          if (artifactType === 'tools_overview') {
            console.log('🎯 [sendMessage] Creating tools artifact with data:', parsedData)
            console.log('🎯 [sendMessage] Tools in parsed data:', parsedData.tools?.length || 0)
            
            // Update the available-tools artifact
            const toolsArtifact: DeliverableArtifact = {
              id: 'available-tools',
              type: 'tools',
              title: 'Available Tools',
              description: 'Tools and integrations available to the team',
              status: 'ready',
              content: parsedData,
              lastUpdated: new Date().toISOString()
            }
            
            console.log('🎯 [sendMessage] Created artifact:', toolsArtifact)
            
            setArtifacts(prev => {
              console.log('🎯 [sendMessage] Previous artifacts count:', prev.length)
              console.log('🎯 [sendMessage] Previous artifacts:', prev.map(a => ({id: a.id, type: a.type})))
              const filtered = prev.filter(a => a.id !== 'available-tools')
              const newArtifacts = [...filtered, toolsArtifact]
              console.log('🎯 [sendMessage] New artifacts count:', newArtifacts.length)
              console.log('🎯 [sendMessage] Tools artifact content tools count:', toolsArtifact.content?.tools?.length || 0)
              console.log('🎯 [sendMessage] Adding artifact with ID:', toolsArtifact.id)
              return newArtifacts
            })
          } else if (artifactType === 'project_description') {
            // Handle project description artifacts
            const projectArtifact: DeliverableArtifact = {
              id: 'project-description',
              type: 'project_description',
              title: 'Project Overview',
              description: 'AI-generated project analysis and objectives',
              status: 'ready',
              content: parsedData,
              lastUpdated: new Date().toISOString()
            }
            setArtifacts(prev => {
              const filtered = prev.filter(a => a.id !== 'project-description')
              return [...filtered, projectArtifact]
            })
          }
          
          inlineArtifacts.push({ type: artifactType, data: parsedData })
        } catch (e) {
          console.error('❌ [sendMessage] Failed to parse inline artifact:', artifactType, e)
        }
      }
      
      if (apiResult.response.artifacts && apiResult.response.artifacts.length > 0) {
        console.log('🎨 [sendMessage] AI provided artifacts:', apiResult.response.artifacts)
        
        // Find thinking process artifact
        const thinkingArtifact = apiResult.response.artifacts.find((artifact: any) => 
          artifact.type === 'thinking_process'
        )
        
        if (thinkingArtifact && thinkingArtifact.content?.steps) {
          extractedThinkingSteps = thinkingArtifact.content.steps
          console.log('🧠 [sendMessage] Found thinking steps:', extractedThinkingSteps.length)
        }
        
        // Don't call loadArtifacts() here as it overwrites inline artifacts
        // await loadArtifacts()
      }
      
      // Extract suggested actions from response
      if (apiResult.response.suggested_actions && apiResult.response.suggested_actions.length > 0) {
        extractedSuggestedActions = apiResult.response.suggested_actions
        console.log('⚡ [sendMessage] Found suggested actions:', extractedSuggestedActions.length)
      }

      // Remove inline artifact patterns from the message for cleaner display
      let cleanedMessage = apiResult.response.message
      cleanedMessage = cleanedMessage.replace(/\*\*ARTIFACT:(\w+):(.+?)\*\*/g, '')
      
      // Add AI response message with guaranteed unique ID
      const aiMessage: ConversationMessage = {
        id: apiResult.message_id || `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'team',
        content: cleanedMessage,
        timestamp: apiResult.timestamp || new Date().toISOString(),
        metadata: {
          teamMember: 'AI Assistant',
          processing_time: apiResult.processing_time_ms,
          message_type: apiResult.response.message_type,
          conversation_id: apiResult.conversation_id,
          thinking_steps: extractedThinkingSteps,
          suggested_actions: extractedSuggestedActions
        }
      }

      setMessages(prev => [...prev, aiMessage])
      
      // Store thinking steps and suggested actions for UI display
      setThinkingSteps(extractedThinkingSteps)
      setSuggestedActions(extractedSuggestedActions)

      // Handle confirmation requests
      if (apiResult.response.needs_confirmation) {
        // Could add confirmation UI here in the future
        console.log('⚠️ [sendMessage] AI requires confirmation:', apiResult.response.confirmation_id)
      }

      // Clear thinking activity
      setTeamActivities([])

    } catch (error) {
      console.error('❌ [sendMessage] Failed to send message:', error)
      
      // Add error message with guaranteed unique ID
      const errorMessage: ConversationMessage = {
        id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'system',
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
      setTeamActivities([])
    } finally {
      setSendingMessage(false)
      
      // 🔧 FIX: Refresh goal progress after any message that might affect it
      // This helps ensure sidebar reflects any goal updates from AI actions
      setTimeout(() => {
        refreshGoalProgress()
      }, 1000) // Small delay to let backend updates propagate
    }
  }, [activeChat, workspaceContext, loadArtifacts, refreshGoalProgress])

  // AI-driven dynamic chat creation
  const createDynamicChat = useCallback(async (objective: string) => {
    try {
      // 🤖 AI analyzes objective and creates appropriate chat
      const aiAnalysis = await analyzeObjectiveWithAI(objective, workspaceContext)
      
      const newChat: Chat = {
        id: `objective-${Date.now()}`,
        type: 'dynamic',
        title: aiAnalysis.suggestedTitle || generateChatTitle(objective),
        icon: aiAnalysis.suggestedIcon || '🎯',
        status: 'active',
        objective: {
          description: objective,
          metrics: aiAnalysis.extractedMetrics || {},
          deadline: aiAnalysis.suggestedDeadline || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
        },
        lastActivity: new Date().toISOString()
      }

      // Add to chats
      const updatedChats = [...chats, newChat]
      setChats(updatedChats)
      saveDynamicChats(updatedChats)
      
      // Switch to new chat
      setActiveChat(newChat)
      setMessages([]) // Clear messages for new chat
      
      // Send initial AI greeting
      setTimeout(() => {
        const greetingMessage: ConversationMessage = {
          id: `greeting-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type: 'team',
          content: `Great! I understand you want to work on: "${objective}"\n\nLet me analyze this objective and propose how our team can help you achieve it. What specific aspects would you like to focus on first?`,
          timestamp: new Date().toISOString(),
          metadata: {
            teamMember: 'AI Team',
            confidence: 0.9
          }
        }
        setMessages([greetingMessage])
      }, 500)

    } catch (error) {
      console.error('Failed to create dynamic chat:', error)
    }
  }, [chats, saveDynamicChats])

  // Archive chat
  const archiveChat = useCallback(async (chatId: string) => {
    const updatedChats = chats.map(chat => 
      chat.id === chatId 
        ? { ...chat, status: 'archived' as const }
        : chat
    )
    setChats(updatedChats)
    saveDynamicChats(updatedChats)
    
    // Switch to team management if archived chat was active
    if (activeChat?.id === chatId) {
      const teamChat = updatedChats.find(chat => chat.id === 'team-management')
      setActiveChat(teamChat || null)
      setMessages([])
    }
  }, [chats, activeChat, saveDynamicChats])

  // Reactivate a chat
  const reactivateChat = useCallback(async (chatId: string) => {
    console.log('🔄 [reactivateChat] Reactivating chat:', chatId)
    
    // Update local state
    const updatedChats = chats.map(chat => 
      chat.id === chatId ? { ...chat, status: 'active' as const } : chat
    )
    setChats(updatedChats)
    saveDynamicChats(updatedChats)
    
    // If it's a goal, try to update the database status too
    if (chatId.startsWith('goal-')) {
      try {
        const goalId = chatId.replace('goal-', '')
        const response = await fetch(`http://localhost:8000/api/workspaces/${workspaceId}/goals/${goalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'active' })
        })
        
        if (response.ok) {
          console.log('✅ [reactivateChat] Goal reactivated in database')
        } else {
          console.warn('⚠️ [reactivateChat] Failed to update goal status in database')
        }
      } catch (error) {
        console.error('❌ [reactivateChat] Error updating goal status:', error)
      }
    }
  }, [chats, workspaceId, saveDynamicChats])

  // Rename a chat
  const renameChat = useCallback(async (chatId: string, newName: string) => {
    console.log('✏️ [renameChat] Renaming chat:', chatId, 'to:', newName)
    
    // Update local state
    const updatedChats = chats.map(chat => 
      chat.id === chatId ? { ...chat, title: newName } : chat
    )
    setChats(updatedChats)
    saveDynamicChats(updatedChats)
    
    // If it's a goal, try to update the database too
    if (chatId.startsWith('goal-')) {
      try {
        const goalId = chatId.replace('goal-', '')
        const response = await fetch(`http://localhost:8000/api/workspaces/${workspaceId}/goals/${goalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            metadata: { 
              user_renamed: true, 
              custom_title: newName 
            }
          })
        })
        
        if (response.ok) {
          console.log('✅ [renameChat] Goal renamed in database')
        } else {
          console.warn('⚠️ [renameChat] Failed to update goal name in database')
        }
      } catch (error) {
        console.error('❌ [renameChat] Error updating goal name:', error)
      }
    }
  }, [chats, workspaceId, saveDynamicChats])

  // Switch active chat
  const handleSetActiveChat = useCallback(async (chat: Chat) => {
    console.log('🔄 [handleSetActiveChat] Switching to chat:', chat.id, chat.title)
    setActiveChat(chat)
    setTeamActivities([]) // Clear activities
    setThinkingSteps([]) // Clear thinking steps
    setSuggestedActions([]) // Clear suggested actions
    
    // Load chat-specific data first, then clear messages only if loading succeeds
    try {
      if (chat.type === 'fixed') {
        await loadFixedChatData(chat)
        loadChatSpecificArtifacts(chat)
      } else {
        await loadDynamicChatData(chat)
        loadChatSpecificArtifacts(chat)
      }
    } catch (error) {
      console.error('❌ [handleSetActiveChat] Failed to load chat data:', error)
      // Clear messages only if loading fails to show empty state
      setMessages([])
    }
  }, [])

  // Load artifacts specific to the selected chat
  const loadChatSpecificArtifacts = useCallback(async (chat: Chat) => {
    console.log('🎯 [loadChatSpecificArtifacts] Loading artifacts for chat:', chat.id)
    console.log('🎯 [loadChatSpecificArtifacts] workspaceContext available:', !!workspaceContext)
    console.log('🎯 [loadChatSpecificArtifacts] team length:', workspaceContext?.team?.length || 0)
    
    const chatArtifacts: DeliverableArtifact[] = []
    
    try {
      switch (chat.id) {
        case 'team-management':
          // Load team-specific artifacts with handoffs
          if (workspaceContext?.team && workspaceContext.team.length > 0) {
            console.log('👥 [loadChatSpecificArtifacts] Creating team artifact with team:', workspaceContext.team)
            
            // Also load handoffs for the team
            let handoffsData = []
            try {
              handoffsData = await api.handoffs.list(workspaceId)
              console.log('🤝 [loadChatSpecificArtifacts] Loaded handoffs:', handoffsData)
            } catch (handoffError) {
              console.warn('⚠️ [loadChatSpecificArtifacts] Could not load handoffs:', handoffError)
            }
            
            chatArtifacts.push({
              id: 'team-overview',
              type: 'team_status',
              title: 'Team Overview',
              description: `${workspaceContext.team.length} active team members, ${handoffsData.length} handoffs`,
              status: 'ready',
              content: {
                agents: workspaceContext.team,
                handoffs: handoffsData,
                team_members: workspaceContext.team.length,
                success: true
              },
              lastUpdated: new Date().toISOString()
            })
          } else {
            console.log('⚠️ [loadChatSpecificArtifacts] No team data available, trying direct API call')
            // Fallback: try loading team and handoffs directly from API
            try {
              const [teamData, handoffsData] = await Promise.all([
                api.agents.list(workspaceId),
                api.handoffs.list(workspaceId).catch(() => [])
              ])
              console.log('👥 [loadChatSpecificArtifacts] Direct API team data:', teamData)
              console.log('🤝 [loadChatSpecificArtifacts] Direct API handoffs data:', handoffsData)
              
              if (teamData && teamData.length > 0) {
                chatArtifacts.push({
                  id: 'team-overview',
                  type: 'team_status',
                  title: 'Team Overview',
                  description: `${teamData.length} active team members, ${handoffsData.length} handoffs`,
                  status: 'ready',
                  content: {
                    agents: teamData,
                    handoffs: handoffsData,
                    team_members: teamData.length,
                    success: true
                  },
                  lastUpdated: new Date().toISOString()
                })
              }
            } catch (error) {
              console.error('❌ [loadChatSpecificArtifacts] Failed to load team directly:', error)
            }
          }
          break

        case 'configuration':
          // Load configuration-specific artifacts
          if (workspaceContext?.configuration) {
            console.log('⚙️ [loadChatSpecificArtifacts] Creating config artifact with:', workspaceContext.configuration)
            chatArtifacts.push({
              id: 'workspace-config',
              type: 'configuration',
              title: 'Workspace Configuration',
              description: 'Current workspace settings and parameters',
              status: 'ready',
              content: workspaceContext.configuration,
              lastUpdated: new Date().toISOString()
            })
          } else {
            console.log('⚠️ [loadChatSpecificArtifacts] No configuration data available, trying direct API call')
            // Fallback: try loading configuration directly from API
            try {
              const configData = await api.workspaces.get(workspaceId)
              console.log('⚙️ [loadChatSpecificArtifacts] Direct API config data:', configData)
              if (configData) {
                chatArtifacts.push({
                  id: 'workspace-config',
                  type: 'configuration',
                  title: 'Workspace Configuration',
                  description: 'Current workspace settings and parameters',
                  status: 'ready',
                  content: configData,
                  lastUpdated: new Date().toISOString()
                })
              }
            } catch (error) {
              console.error('❌ [loadChatSpecificArtifacts] Failed to load config directly:', error)
            }
          }
          break

        case 'feedback-requests':
          // Load feedback-specific artifacts using same API as feedback dashboard
          try {
            const feedbackUrl = `http://localhost:8000/human-feedback/pending?workspace_id=${workspaceId}`
            const response = await fetch(feedbackUrl)
            let feedbackData: any[] = []
            
            if (response.ok) {
              feedbackData = await response.json() || []
            }
            
            // Convert to our format for compatibility
            const convertedRequests = feedbackData.map((req: any) => ({
              id: req.id,
              title: req.title,
              description: req.description,
              type: req.request_type || 'review',
              status: req.status === 'pending' ? 'pending' : 'completed',
              priority: req.priority === 'critical' ? 'urgent' : req.priority,
              createdAt: req.created_at,
              dueDate: req.expires_at,
              requestedBy: 'AI Team',
              content: req.context?.deliverable_data || req.context?.key_content,
              metadata: {
                quality_assessment: req.context?.quality_assessment,
                workspace_goal: req.context?.workspace_goal,
                why_review_needed: req.context?.why_review_needed,
                proposed_actions: req.proposed_actions
              }
            }))
            
            chatArtifacts.push({
              id: 'feedback-requests',
              type: 'feedback',
              title: 'Feedback Requests',
              description: `${convertedRequests.length} pending feedback requests`,
              status: 'ready',
              content: {
                requests: convertedRequests,
                pendingCount: convertedRequests.filter(f => f.status === 'pending').length,
                completedCount: convertedRequests.filter(f => f.status === 'completed').length
              },
              lastUpdated: new Date().toISOString()
            })
          } catch (error) {
            console.warn('Failed to load feedback requests:', error)
            // Create mock data for testing
            const mockRequests = [
              {
                id: 'mock-1',
                title: 'Email marketing campaign ready for implementation',
                description: 'Email templates, targeting strategy, and performance tracking setup',
                type: 'deliverable',
                status: 'pending',
                priority: 'high',
                createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
                dueDate: new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString(),
                requestedBy: 'AI Team',
                content: { campaign_data: 'Mock campaign content' },
                metadata: {
                  quality_assessment: { score: 43 },
                  why_review_needed: 'Ensure emails are professional, compliant, and will drive engagement'
                }
              },
              {
                id: 'mock-2',
                title: 'Business Analysis deliverable ready for use',
                description: 'Content completeness, accuracy, and business relevance',
                type: 'validation',
                status: 'pending',
                priority: 'medium',
                createdAt: new Date(Date.now() - 21 * 60 * 60 * 1000).toISOString(),
                dueDate: new Date(Date.now() + 21 * 60 * 60 * 1000).toISOString(),
                requestedBy: 'AI Team',
                content: { analysis_data: 'Mock analysis content' },
                metadata: {
                  quality_assessment: { score: 68 },
                  why_review_needed: 'Validate business insights and recommendations'
                }
              }
            ]
            
            chatArtifacts.push({
              id: 'feedback-requests',
              type: 'feedback',
              title: 'Feedback Requests',
              description: `${mockRequests.length} pending feedback requests`,
              status: 'ready',
              content: {
                requests: mockRequests,
                pendingCount: mockRequests.filter(f => f.status === 'pending').length,
                completedCount: mockRequests.filter(f => f.status === 'completed').length
              },
              lastUpdated: new Date().toISOString()
            })
          }
          break

        case 'knowledge-base':
          // Load knowledge-specific artifacts
          try {
            console.log('📚 [loadChatSpecificArtifacts] Fetching knowledge insights for workspace:', workspaceId)
            const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/knowledge-insights`)
            
            if (response.ok) {
              const knowledgeData = await response.json()
              console.log('✅ [loadChatSpecificArtifacts] Knowledge insights loaded:', knowledgeData)
              
              chatArtifacts.push({
                id: 'knowledge-insights',
                type: 'knowledge',
                title: 'Knowledge Insights',
                description: `${knowledgeData.total_insights} insights available`,
                status: 'ready',
                content: {
                  insights: knowledgeData.insights || [],
                  bestPractices: knowledgeData.bestPractices || [],
                  learnings: knowledgeData.learnings || [],
                  summary: knowledgeData.summary || {
                    recent_discoveries: [],
                    key_constraints: [],
                    success_patterns: [],
                    top_tags: []
                  }
                },
                lastUpdated: new Date().toISOString()
              })
            } else {
              console.warn('⚠️ [loadChatSpecificArtifacts] Failed to load knowledge insights:', response.status)
              // Fallback to empty knowledge base
              chatArtifacts.push({
                id: 'knowledge-insights',
                type: 'knowledge',
                title: 'Knowledge Insights',
                description: 'No insights available yet',
                status: 'ready',
                content: {
                  insights: [],
                  bestPractices: [],
                  learnings: []
                },
                lastUpdated: new Date().toISOString()
              })
            }
          } catch (error) {
            console.error('❌ [loadChatSpecificArtifacts] Error loading knowledge insights:', error)
            // Fallback to empty knowledge base
            chatArtifacts.push({
              id: 'knowledge-insights',
              type: 'knowledge',
              title: 'Knowledge Insights',
              description: 'Relevant insights and best practices',
              status: 'ready',
              content: {
                insights: [],
                bestPractices: [],
                learnings: []
              },
              lastUpdated: new Date().toISOString()
            })
          }
          break

        case 'available-tools':
          // Check if we already have a populated tools artifact from inline parsing
          const existingToolsArtifact = artifacts.find(a => 
            a.id === 'available-tools' && 
            a.content?.tools && 
            Array.isArray(a.content.tools) && 
            a.content.tools.length > 0
          )
          
          if (existingToolsArtifact) {
            console.log('🎯 [loadChatSpecificArtifacts] Found existing tools artifact with', existingToolsArtifact.content.tools.length, 'tools')
            chatArtifacts.push(existingToolsArtifact)
          } else {
            console.log('🎯 [loadChatSpecificArtifacts] Auto-requesting tools from backend')
            // Automatically request tools from backend instead of showing empty artifact
            try {
              const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/chat`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  message: 'show available tools',
                  chat_id: 'available-tools'
                })
              })
              
              if (response.ok) {
                const data = await response.json()
                const responseMessage = data.response?.message || ''
                
                // Parse inline artifacts from the response
                const artifactPattern = /\*\*ARTIFACT:(\w+):(.+?)\*\*/g
                let match
                
                while ((match = artifactPattern.exec(responseMessage)) !== null) {
                  const [, artifactType, artifactData] = match
                  if (artifactType === 'tools_overview') {
                    try {
                      const parsedData = JSON.parse(artifactData)
                      console.log('🎯 [loadChatSpecificArtifacts] Auto-loaded tools:', parsedData.tools?.length || 0)
                      
                      chatArtifacts.push({
                        id: 'available-tools',
                        type: 'tools',
                        title: 'Available Tools',
                        description: 'Tools and integrations available to the team',
                        status: 'ready',
                        content: parsedData,
                        lastUpdated: new Date().toISOString()
                      })
                      break
                    } catch (e) {
                      console.error('❌ Failed to parse auto-loaded tools:', e)
                    }
                  }
                }
              }
            } catch (error) {
              console.error('❌ Failed to auto-load tools:', error)
            }
            
            // Fallback to empty artifact if auto-loading failed
            if (chatArtifacts.length === 0 || !chatArtifacts.find(a => a.id === 'available-tools')) {
              console.log('🎯 [loadChatSpecificArtifacts] Creating empty tools artifact as fallback')
              chatArtifacts.push({
                id: 'available-tools',
                type: 'tools',
                title: 'Available Tools',
                description: 'Tools and integrations available to the team',
                status: 'ready',
                content: {
                  tools: [],
                  integrations: [],
                  capabilities: []
                },
                lastUpdated: new Date().toISOString()
              })
            }
          }
          break

        default:
          // For dynamic chats, load objective-specific artifacts with full database data
          if (chat.type === 'dynamic' && chat.objective) {
            try {
              // Load complete goal data from database including metadata
              const goalId = chat.objective.id || chat.id.replace('goal-', '')
              console.log('🎯 [loadChatSpecificArtifacts] Loading goal data for:', goalId)
              
              // First try to get the goal directly
              let fullGoalData = null
              try {
                const goalResponse = await fetch(`http://localhost:8000/workspace-goals/${goalId}`)
                if (goalResponse.ok) {
                  fullGoalData = await goalResponse.json()
                  console.log('📊 [loadChatSpecificArtifacts] Full goal data loaded:', fullGoalData)
                }
              } catch (error) {
                console.warn('⚠️ [loadChatSpecificArtifacts] Could not load individual goal:', error)
              }
              
              // Fallback: load all goals and find this one
              if (!fullGoalData) {
                const allGoals = await api.workspaceGoals.getAll(workspaceId, {})
                const goalsArray = Array.isArray(allGoals) ? allGoals : (allGoals?.goals || [])
                fullGoalData = goalsArray.find((g: any) => g.id === goalId || `goal-${g.id}` === chat.id)
                console.log('📋 [loadChatSpecificArtifacts] Goal found in array:', fullGoalData)
              }
              
              const content = {
                objective: chat.objective,
                progress: fullGoalData ? Math.min((fullGoalData.current_value / fullGoalData.target_value) * 100, 100) : 0,
                deliverables: [],
                // Include full goal metadata
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
              
              chatArtifacts.push({
                id: `objective-${chat.id}`,
                type: 'objective',
                title: chat.title,
                description: chat.objective.description,
                status: fullGoalData?.status === 'completed' ? 'completed' : 'in_progress',
                content,
                metadata: fullGoalData?.metadata || {},
                lastUpdated: fullGoalData?.updated_at || new Date().toISOString()
              })
            } catch (error) {
              console.error('❌ [loadChatSpecificArtifacts] Failed to load goal data:', error)
              // Fallback to basic artifact
              chatArtifacts.push({
                id: `objective-${chat.id}`,
                type: 'objective',
                title: chat.title,
                description: chat.objective.description,
                status: 'in_progress',
                content: {
                  objective: chat.objective,
                  progress: 0,
                  deliverables: [],
                  error: 'Could not load full goal data'
                },
                lastUpdated: new Date().toISOString()
              })
            }
          }
          break
      }

      console.log('🎯 [loadChatSpecificArtifacts] Setting chat-specific artifacts:', chatArtifacts)
      setArtifacts(chatArtifacts)

    } catch (error) {
      console.error('❌ [loadChatSpecificArtifacts] Failed to load chat artifacts:', error)
      setArtifacts([])
    }
  }, [workspaceContext, workspaceId])

  // Load data for fixed chats
  const loadFixedChatData = useCallback(async (chat: Chat) => {
    console.log('🔧 [loadFixedChatData] Loading data for chat:', chat.id, chat.title)
    
    // Force refresh artifacts when switching to team management
    if (chat.id === 'team-management') {
      console.log('👥 [loadFixedChatData] Team chat selected, refreshing artifacts...')
      await loadArtifacts()
    }
    
    try {
      // Load actual conversation history from API
      const chatId = chat.systemType || chat.id
      console.log('📞 [loadFixedChatData] Fetching conversation history for:', chatId)
      
      const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/history?chat_id=${chatId}&limit=50`)
      
      if (response.ok) {
        const conversationHistory = await response.json()
        console.log('✅ [loadFixedChatData] Conversation history loaded:', conversationHistory)
        
        // Convert API messages to UI format
        const convertedMessages: ConversationMessage[] = conversationHistory.map((msg: any) => ({
          id: msg.message_id || msg.id,
          type: msg.role === 'user' ? 'user' : 'team',
          content: msg.content,
          timestamp: msg.created_at,
          metadata: {
            teamMember: msg.role === 'user' ? 'You' : 'AI Assistant',
            thinking_steps: msg.metadata?.thinking_steps || [],
            deep_analysis: msg.metadata?.deep_analysis,
            ...(msg.metadata || {})
          }
        }))
        
        if (convertedMessages.length > 0) {
          setMessages(convertedMessages)
          return // Don't show welcome message if conversation history exists
        }
      } else {
        console.warn('⚠️ [loadFixedChatData] Failed to load conversation history:', response.status)
      }
    } catch (error) {
      console.error('❌ [loadFixedChatData] Error loading conversation history:', error)
    }
    
    // Show welcome message only if no conversation history
    const welcomeMessages: Record<string, string> = {
      'team-management': 'Hello! I can help you manage your team. You can add members, update skills, check performance, and more.',
      'configuration': 'Hi! I can help you configure your workspace settings, budgets, goals, and preferences.',
      'feedback-requests': 'Welcome to feedback management! I can help you review pending feedback requests, provide input on deliverables, and track validation status.',
      'knowledge-base': 'Welcome to your knowledge base! I can help you search for insights, best practices, and lessons learned.',
      'available-tools': 'Hello! I can show you available tools, help with integrations, and explain capabilities.'
    }

    if (welcomeMessages[chat.id]) {
      const welcomeMessage: ConversationMessage = {
        id: `welcome-${chat.id}-${Date.now()}`,
        type: 'team',
        content: welcomeMessages[chat.id],
        timestamp: new Date().toISOString(),
        metadata: {
          teamMember: 'AI Assistant'
        }
      }
      setMessages([welcomeMessage])
    }
  }, [workspaceId, loadArtifacts])

  // Load data for dynamic chats  
  const loadDynamicChatData = useCallback(async (chat: Chat) => {
    console.log('🔧 [loadDynamicChatData] Loading data for dynamic chat:', chat.id, chat.title)
    
    try {
      // First try to load from API
      const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/history?chat_id=${chat.id}&limit=50`)
      
      if (response.ok) {
        const conversationHistory = await response.json()
        console.log('✅ [loadDynamicChatData] API conversation history loaded:', conversationHistory)
        
        // Convert API messages to UI format with unique IDs and deduplication
        const convertedMessages: ConversationMessage[] = conversationHistory
          .map((msg: any, index: number) => ({
            id: msg.message_id || msg.id || `msg-${msg.created_at}-${index}`,
            type: msg.role === 'user' ? 'user' : 'team',
            content: msg.content,
            timestamp: msg.created_at,
            metadata: {
              teamMember: msg.role === 'user' ? 'You' : 'AI Assistant',
              thinking_steps: msg.metadata?.thinking_steps || [],
              deep_analysis: msg.metadata?.deep_analysis,
              ...(msg.metadata || {})
            }
          }))
          .filter((message, index, array) => {
            // Remove duplicates based on ID
            return array.findIndex(m => m.id === message.id) === index
          })
        
        console.log('✅ [loadDynamicChatData] Converted messages (deduplicated):', convertedMessages.length)
        
        if (convertedMessages.length > 0) {
          setMessages(convertedMessages)
          return
        }
      }
      
      // Fallback to localStorage for backward compatibility
      console.log('📦 [loadDynamicChatData] Falling back to localStorage')
      const stored = localStorage.getItem(`chat-messages-${chat.id}`)
      if (stored) {
        const localMessages = JSON.parse(stored)
        console.log('✅ [loadDynamicChatData] LocalStorage messages loaded:', localMessages)
        setMessages(localMessages)
      } else {
        // For goal chats, start with welcome message and auto-trigger goal analysis
        if (chat.id.startsWith('goal-')) {
          const goalWelcomeMessage: ConversationMessage = {
            id: `welcome-${chat.id}-${Date.now()}`,
            type: 'team',
            content: `🎯 **Goal Progress Analysis**\n\nLet me analyze the current progress for: **${chat.title}**\n\nI'll check task execution, deliverables, and team performance for this objective.`,
            timestamp: new Date().toISOString(),
            metadata: {
              teamMember: 'AI Assistant'
            }
          }
          
          setMessages([goalWelcomeMessage])
          
          // Auto-trigger goal progress analysis with thinking capture
          setTimeout(async () => {
            try {
              const goalId = chat.id.replace('goal-', '')
              console.log('🎯 [Auto-trigger] Starting goal analysis for:', goalId)
              
              // Clear previous thinking steps before starting new analysis
              setThinkingSteps([])
              setSuggestedActions([])
              
              // Use the thinking endpoint to capture reasoning steps
              const response = await fetch(`http://localhost:8000/api/conversation/workspaces/${workspaceId}/chat/thinking`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  message: `Show detailed progress for goal ${goalId}`,
                  chat_id: chat.id,
                  message_id: `auto-goal-analysis-${Date.now()}`
                })
              })
              
              if (response.ok) {
                const result = await response.json()
                console.log('✅ [Auto-trigger] Goal analysis response received:', result)
                
                // Extract and display thinking steps
                if (result.response.artifacts) {
                  const thinkingArtifact = result.response.artifacts.find(a => a.type === 'thinking_process')
                  if (thinkingArtifact && thinkingArtifact.content.steps) {
                    console.log('🧠 [Auto-trigger] Thinking steps found:', thinkingArtifact.content.steps.length)
                    setThinkingSteps(thinkingArtifact.content.steps)
                  }
                }
                
                // Extract suggested actions
                if (result.response.suggested_actions) {
                  console.log('⚡ [Auto-trigger] Suggested actions found:', result.response.suggested_actions.length)
                  setSuggestedActions(result.response.suggested_actions)
                }
                
                // Add the AI response message with guaranteed unique ID
                const aiMessage: ConversationMessage = {
                  id: result.message_id || `auto-analysis-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                  type: 'team',
                  content: result.response.message,
                  timestamp: result.timestamp || new Date().toISOString(),
                  metadata: {
                    teamMember: 'AI Assistant',
                    processing_time: result.processing_time_ms,
                    message_type: 'goal_analysis',
                    auto_triggered: true
                  }
                }
                
                setMessages(prev => [...prev, aiMessage])
                
              } else {
                console.error('❌ [Auto-trigger] Goal analysis failed:', response.status)
                // Fallback to regular message
                await sendMessage(`Show detailed progress for goal ${goalId} including tasks, deliverables and team performance`)
              }
            } catch (error) {
              console.error('❌ [Auto-trigger] Failed to auto-trigger goal analysis:', error)
              // Fallback to regular message
              try {
                await sendMessage(`Show detailed progress for goal ${goalId} including tasks, deliverables and team performance`)
              } catch (fallbackError) {
                console.error('❌ [Auto-trigger] Fallback also failed:', fallbackError)
              }
            }
          }, 1500)
        } else {
          setMessages([])
        }
      }
    } catch (error) {
      console.error('❌ [loadDynamicChatData] Failed to load chat messages:', error)
      setMessages([])
    }
  }, [workspaceId, sendMessage])

  // Save messages when they change (for dynamic chats)
  useEffect(() => {
    if (activeChat?.type === 'dynamic' && messages.length > 0) {
      try {
        localStorage.setItem(`chat-messages-${activeChat.id}`, JSON.stringify(messages))
      } catch (error) {
        console.error('Failed to save chat messages:', error)
      }
    }
  }, [activeChat, messages])

  // Refresh all data
  const refreshData = useCallback(async () => {
    await initializeWorkspace()
  }, [initializeWorkspace])

  // Initialize on mount
  useEffect(() => {
    initializeWorkspace()
  }, [initializeWorkspace])

  // Load initial chat data when activeChat is first set
  useEffect(() => {
    if (activeChat && !loading && messages.length === 0) {
      console.log('🔄 [useEffect] Loading initial conversation history for:', activeChat.id)
      if (activeChat.type === 'fixed') {
        loadFixedChatData(activeChat)
      } else {
        loadDynamicChatData(activeChat)
      }
    }
  }, [activeChat, loading, messages.length])

  // Reload chat-specific artifacts when workspace context is available
  useEffect(() => {
    if (workspaceContext && activeChat) {
      console.log('🔄 [useEffect] workspaceContext loaded, reloading artifacts for active chat:', activeChat.id)
      loadChatSpecificArtifacts(activeChat)
    }
  }, [workspaceContext, activeChat, loadChatSpecificArtifacts])

  // Initial goal progress refresh after workspace loads
  useEffect(() => {
    if (!loading && workspaceContext) {
      console.log('🔄 [useEffect] Workspace loaded, triggering initial goal progress refresh...')
      setTimeout(() => {
        refreshGoalProgress()
      }, 1000) // Small delay to let all data settle
    }
  }, [loading, workspaceContext, refreshGoalProgress])

  // Auto-refresh artifacts, goal progress, and health status periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (!loading && workspaceContext) {
        loadArtifacts()
        refreshGoalProgress() // 🔧 FIX: Also refresh goal progress in sidebar
        checkWorkspaceHealth() // 🆕 NEW: Check workspace health status
      }
    }, 30000) // Every 30 seconds

    return () => clearInterval(interval)
  }, [loading, workspaceContext, loadArtifacts, refreshGoalProgress, checkWorkspaceHealth])

  // Initial health check after workspace loads
  useEffect(() => {
    if (!loading && workspaceContext) {
      console.log('🏥 [useEffect] Workspace loaded, triggering initial health check...')
      setTimeout(() => {
        checkWorkspaceHealth()
      }, 2000) // Small delay to let workspace settle
    }
  }, [loading, workspaceContext, checkWorkspaceHealth])

  return {
    // State
    chats,
    activeChat,
    messages,
    teamActivities,
    artifacts,
    workspaceContext,
    thinkingSteps,
    suggestedActions,
    loading, // Initial loading only
    sendingMessage, // Separate message sending state
    error,
    
    // Health monitoring state
    workspaceHealthStatus,
    healthLoading,
    
    // Actions
    setActiveChat: handleSetActiveChat,
    sendMessage,
    createDynamicChat,
    archiveChat,
    reactivateChat,
    renameChat,
    refreshData,
    refreshGoalProgress, // 🔧 FIX: Export goal progress refresh function
    refreshMessages: () => activeChat ? loadDynamicChatData(activeChat) : Promise.resolve(),
    
    // Health monitoring actions
    checkWorkspaceHealth,
    unblockWorkspace
  }
}

// AI-driven objective analysis
async function analyzeObjectiveWithAI(objective: string, context: WorkspaceContext | null) {
  // 🤖 In production, this would call backend AI service
  // For now, simulate intelligent analysis
  
  try {
    // Simulate AI analysis delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // AI determines domain and suggests appropriate properties
    const analysis = {
      suggestedTitle: generateSmartTitle(objective),
      suggestedIcon: determineObjectiveIcon(objective),
      extractedMetrics: extractMetricsFromObjective(objective),
      suggestedDeadline: calculateReasonableDeadline(objective),
      detectedDomain: context?.domain || 'general',
      requiredCapabilities: identifyRequiredCapabilities(objective)
    }
    
    return analysis
  } catch (error) {
    console.error('AI objective analysis failed:', error)
    return {
      suggestedTitle: generateChatTitle(objective),
      suggestedIcon: '🎯',
      extractedMetrics: {},
      suggestedDeadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    }
  }
}

// Smart title generation with domain awareness
function generateSmartTitle(objective: string): string {
  const lowerObj = objective.toLowerCase()
  
  // AI-like pattern recognition for titles
  if (lowerObj.includes('content') && lowerObj.includes('linkedin')) return 'LinkedIn Content Strategy'
  if (lowerObj.includes('lead') && lowerObj.includes('generation')) return 'Lead Generation Campaign'
  if (lowerObj.includes('email') && lowerObj.includes('campaign')) return 'Email Marketing Campaign'
  if (lowerObj.includes('seo') || lowerObj.includes('search')) return 'SEO Optimization'
  if (lowerObj.includes('social') && lowerObj.includes('media')) return 'Social Media Strategy'
  if (lowerObj.includes('product') && lowerObj.includes('launch')) return 'Product Launch Plan'
  if (lowerObj.includes('analytics') || lowerObj.includes('report')) return 'Analytics & Reporting'
  
  // Fallback to simple generation
  return generateChatTitle(objective)
}

function determineObjectiveIcon(objective: string): string {
  const lowerObj = objective.toLowerCase()
  
  if (lowerObj.includes('content')) return '📝'
  if (lowerObj.includes('lead')) return '🎯'
  if (lowerObj.includes('email')) return '📧'
  if (lowerObj.includes('social')) return '📱'
  if (lowerObj.includes('seo')) return '🔍'
  if (lowerObj.includes('analytics')) return '📊'
  if (lowerObj.includes('campaign')) return '🚀'
  if (lowerObj.includes('strategy')) return '🧠'
  
  return '🎯'
}

function extractMetricsFromObjective(objective: string): Record<string, number> {
  const metrics: Record<string, number> = {}
  
  // Extract numbers and context
  const numberPattern = /(\d+)\s*([a-zA-Z]+)/g
  let match
  
  while ((match = numberPattern.exec(objective)) !== null) {
    const value = parseInt(match[1])
    const context = match[2].toLowerCase()
    
    if (context.includes('lead')) metrics.targetLeads = value
    if (context.includes('month')) metrics.timelineMonths = value
    if (context.includes('week')) metrics.timelineWeeks = value
    if (context.includes('post')) metrics.targetPosts = value
    if (context.includes('percent') || context.includes('%')) metrics.targetPercentage = value
  }
  
  return metrics
}

function calculateReasonableDeadline(objective: string): Date {
  const lowerObj = objective.toLowerCase()
  const now = new Date()
  
  // AI determines reasonable timeline based on objective complexity
  if (lowerObj.includes('quick') || lowerObj.includes('urgent')) {
    return new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000) // 1 week
  }
  if (lowerObj.includes('campaign')) {
    return new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000) // 2 months
  }
  if (lowerObj.includes('strategy') || lowerObj.includes('plan')) {
    return new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000) // 3 months
  }
  
  return new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000) // Default 1 month
}

function identifyRequiredCapabilities(objective: string): string[] {
  const capabilities: string[] = []
  const lowerObj = objective.toLowerCase()
  
  if (lowerObj.includes('content')) capabilities.push('content_creation', 'content_strategy')
  if (lowerObj.includes('lead')) capabilities.push('lead_generation', 'lead_qualification')
  if (lowerObj.includes('email')) capabilities.push('email_marketing', 'automation')
  if (lowerObj.includes('seo')) capabilities.push('seo_optimization', 'keyword_research')
  if (lowerObj.includes('social')) capabilities.push('social_media', 'community_management')
  if (lowerObj.includes('analytics')) capabilities.push('data_analysis', 'reporting')
  
  return capabilities
}

// Simple chat title generation fallback
function generateChatTitle(objective: string): string {
  const words = objective.split(' ').slice(0, 4).join(' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

