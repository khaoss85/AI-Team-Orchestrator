// types.ts - Core types for conversational interface
export interface ConversationMessage {
  id: string
  type: 'user' | 'team' | 'system'
  content: string
  timestamp: string
  metadata?: {
    teamMember?: string
    workingOn?: string[]
    attachments?: DeliverableReference[]
    confidence?: number
  }
}

export interface TeamActivity {
  agentId: string
  agentName: string
  activity: string
  progress: number
  eta?: string
  status: 'thinking' | 'working' | 'completed' | 'waiting'
}

export interface DeliverableArtifact {
  id: string
  type: 'deliverable' | 'progress' | 'team_status' | 'configuration' | 'feedback' | 'knowledge' | 'tools' | 'project_description'
  title: string
  description?: string
  status: 'ready' | 'in_progress' | 'completed'
  content?: any
  metadata?: Record<string, any>
  lastUpdated: string
}

export interface Chat {
  id: string
  type: 'fixed' | 'dynamic'
  title: string
  icon?: string
  status: 'active' | 'archived' | 'completed'
  lastActivity?: string
  unreadCount?: number
  // For dynamic chats
  objective?: {
    id?: string
    description: string
    targetDate?: string
    progress?: number
  }
  messageCount?: number
  lastMessageDate?: string
  // For fixed chats  
  systemType?: 'team' | 'configuration' | 'knowledge' | 'tools' | 'feedback'
  // 🎯 ENHANCED: Business value tracking
  businessValueWarning?: boolean
  // 🔒 COMPLETION GUARANTEE: Goals with guaranteed completion
  completionGuarantee?: boolean
}

export interface WorkspaceContext {
  id: string
  name: string
  domain?: string
  goals: Record<string, any>[]
  team: any[]
  configuration: Record<string, any>
}

export interface ChatContext {
  chatId: string
  chatType: 'fixed' | 'dynamic'
  capabilities: string[]
  conversationHistory: ConversationMessage[]
  relevantArtifacts: DeliverableArtifact[]
}

export interface AIResponse {
  message: string
  confidence: number
  suggestedActions?: string[]
  artifactsUpdated?: string[]
  teamActivities?: TeamActivity[]
}

export interface DeliverableReference {
  id: string
  title: string
  type: string
  preview?: string
}

// AI-Driven Theme Types for Macro-Deliverable Grouping
export interface MacroTheme {
  theme_id: string
  name: string
  description: string
  icon: string
  business_value: string
  confidence_score: number
  goals: string[] // Goal IDs in this theme
  deliverables: any[] // Deliverables in this theme
  statistics: {
    total_goals: number
    total_deliverables: number
    average_progress: number
    completed_deliverables: number
  }
  reasoning: string
}

export interface ThemeExtractionResult {
  workspace_id: string
  macro_deliverables: MacroTheme[]
  view_type: 'themed_groups' | 'simple_goals'
  ungrouped_goals: string[]
  extraction_summary: {
    total_goals: number
    total_themes: number
    goals_grouped: number
    goals_ungrouped: number
    grouping_efficiency: number
  }
  timestamp: string
}