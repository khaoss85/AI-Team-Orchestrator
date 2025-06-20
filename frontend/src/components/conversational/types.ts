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
  type: 'deliverable' | 'progress' | 'team_status' | 'configuration'
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
    description: string
    metrics: Record<string, number>
    deadline?: Date
  }
  // For fixed chats  
  systemType?: 'team' | 'configuration' | 'knowledge' | 'tools'
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