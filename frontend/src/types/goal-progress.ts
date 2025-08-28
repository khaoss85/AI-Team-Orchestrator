// TypeScript interfaces for Goal Progress Transparency API

export interface GoalProgressDetail {
  goal: {
    id: string
    title: string
    status: string
    progress: number
    current_value?: number
    target_value?: number
  }
  progress_analysis: {
    reported_progress: number
    goal_based_progress: number
    api_calculated_progress: number
    progress_discrepancy: number
    calculation_method: string
    goal_metrics: {
      current_value: number
      target_value: number
    }
    api_metrics: {
      total_deliverables: number
      completed_deliverables: number
    }
  }
  deliverable_breakdown: {
    completed: DeliverableItem[]
    failed: DeliverableItem[]
    pending: DeliverableItem[]
    in_progress: DeliverableItem[]
    unknown: DeliverableItem[]
  }
  deliverable_stats: {
    completed: number
    failed: number
    pending: number
    in_progress: number
    unknown: number
    total: number
  }
  visibility_analysis: {
    shown_in_ui: number
    hidden_from_ui: number
    transparency_gap: string
  }
  unblocking: {
    actionable_items: number
    retry_available: number
    total_blocked_progress: number
    missing_deliverables: number
    recommended_actions: string[]
  }
  recommendations: string[]
}

export interface DeliverableItem {
  id: string
  title: string
  status: 'completed' | 'failed' | 'pending' | 'in_progress' | 'unknown'
  type?: string
  task_id?: string
  business_value_score?: number
  created_at?: string
  updated_at?: string
  quality_level?: string
  can_retry: boolean
  retry_reason?: string
  unblock_actions: string[]
  
  // 🚀 AI-DRIVEN DUAL-FORMAT SUPPORT
  // Execution content (structured data for processing)
  execution_content?: Record<string, any>
  execution_format?: string
  
  // Display content (user-friendly format for presentation)
  display_content?: string
  display_format?: 'html' | 'markdown' | 'text'
  display_summary?: string
  display_preview?: string
  
  // Quality and transformation metadata
  display_quality_score?: number
  user_friendliness_score?: number
  readability_score?: number
  content_transformation_status?: 'pending' | 'success' | 'failed'
  transformation_error?: string
  
  // User actions for dual-format
  can_retry_transformation?: boolean
  available_formats?: string[]
  
  // Legacy support (deprecated)
  content?: string | Record<string, any>
}

export interface UnblockRequest {
  action: 'retry_failed' | 'resume_pending' | 'escalate_all' | 'retry_specific'
  deliverable_ids?: string[]
}

export interface UnblockResponse {
  action_taken: string
  workspace_id: string
  goal_id: string
  items_processed: {
    id: string
    title: string
    action: string
  }[]
  items_skipped: any[]
  errors: any[]
  success: boolean
  message: string
}

export type DeliverableStatus = 'completed' | 'failed' | 'pending' | 'in_progress' | 'unknown'

// Status display configurations
export const DELIVERABLE_STATUS_CONFIG: Record<DeliverableStatus, {
  label: string
  icon: string
  color: string
  bgColor: string
  description: string
}> = {
  completed: {
    label: 'Completed',
    icon: '✅',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    description: 'Successfully completed and delivered'
  },
  failed: {
    label: 'Failed',
    icon: '❌',
    color: 'text-red-800',
    bgColor: 'bg-red-100',
    description: 'Task execution failed - can be retried'
  },
  pending: {
    label: 'Pending',
    icon: '⏳',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    description: 'Task waiting to be processed - can be resumed'
  },
  in_progress: {
    label: 'In Progress',
    icon: '🔄',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    description: 'Currently being processed'
  },
  unknown: {
    label: 'Unknown',
    icon: '❓',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    description: 'Status cannot be determined'
  }
}

// Unblock action configurations
export const UNBLOCK_ACTION_CONFIG = {
  retry_task: {
    label: 'Retry Task',
    icon: '🔄',
    color: 'bg-blue-500 hover:bg-blue-600',
    description: 'Retry the failed task'
  },
  resume_task: {
    label: 'Resume Task', 
    icon: '▶️',
    color: 'bg-green-500 hover:bg-green-600',
    description: 'Resume the pending task'
  },
  check_progress: {
    label: 'Check Progress',
    icon: '🔍',
    color: 'bg-yellow-500 hover:bg-yellow-600',
    description: 'Check current progress status'
  },
  skip_and_continue: {
    label: 'Skip & Continue',
    icon: '⏭️',
    color: 'bg-gray-500 hover:bg-gray-600', 
    description: 'Skip this task and continue'
  },
  escalate_to_human: {
    label: 'Escalate to Human',
    icon: '🚨',
    color: 'bg-red-500 hover:bg-red-600',
    description: 'Escalate to human reviewer'
  },
  check_dependencies: {
    label: 'Check Dependencies',
    icon: '🔗',
    color: 'bg-purple-500 hover:bg-purple-600',
    description: 'Check task dependencies'
  },
  escalate_if_stuck: {
    label: 'Escalate if Stuck',
    icon: '⚠️',
    color: 'bg-orange-500 hover:bg-orange-600',
    description: 'Escalate if task appears stuck'
  }
}

// --- AI-DRIVEN DUAL-FORMAT ARCHITECTURE TYPES ---

export interface ContentTransformationRequest {
  asset_id: string
  execution_content: Record<string, any>
  content_type: string
  target_format?: 'html' | 'markdown' | 'text'
  transformation_context?: Record<string, any>
  user_preferences?: Record<string, any>
  quality_requirements?: Record<string, string>
}

export interface ContentTransformationResponse {
  success: boolean
  asset_id: string
  display_content?: string
  display_format: string
  display_summary?: string
  display_metadata: Record<string, any>
  
  // Quality metrics
  display_quality_score: number
  user_friendliness_score: number
  readability_score: number
  
  // Transformation details
  transformation_method: string
  transformation_timestamp: string
  ai_confidence: number
  
  // Error handling
  error_message?: string
  fallback_used: boolean
  retry_suggestions: string[]
}

export interface EnhancedDeliverableResponse {
  id: string
  title: string
  type: string
  status: string
  created_at: string
  updated_at: string
  
  // Execution content (for system processing)
  execution_content: Record<string, any>
  execution_format: string
  
  // Display content (for user presentation)
  display_content?: string
  display_format: string
  display_summary?: string
  display_preview?: string
  
  // Quality and transformation metadata
  display_quality_score: number
  user_friendliness_score: number
  content_transformation_status: string
  transformation_error?: string
  
  // Business metadata
  business_value_score: number
  category: string
  quality_score: number
  
  // User actions
  can_retry_transformation: boolean
  available_formats: string[]
  
  // Backward compatibility
  content?: string | Record<string, any>
}

export interface DeliverableListResponse {
  deliverables: EnhancedDeliverableResponse[]
  total_count: number
  transformation_status: Record<string, number>
  quality_overview: Record<string, number>
  
  // Pagination and filtering
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
  
  // System capabilities
  supports_dual_format: boolean
  available_transformations: string[]
}

export interface ContentTransformationError {
  error_code: string
  error_message: string
  asset_id: string
  retry_count: number
  max_retries: number
  last_attempt: string
  suggested_actions: string[]
  fallback_content?: string
  technical_details: Record<string, any>
}

export interface TransformationBatchRequest {
  asset_ids: string[]
  target_format?: string
  priority?: 'low' | 'normal' | 'high'
  transformation_context?: Record<string, any>
}

export interface TransformationBatchResponse {
  batch_id: string
  total_assets: number
  successful_transformations: number
  failed_transformations: number
  pending_transformations: number
  
  results: ContentTransformationResponse[]
  
  started_at: string
  completed_at?: string
  estimated_completion?: string
}

// --- MIGRATION AND COMPATIBILITY TYPES ---

export interface ContentMigrationPlan {
  migration_id: string
  total_assets: number
  assets_to_migrate: string[]
  
  migration_strategy: 'incremental' | 'bulk' | 'on_demand'
  batch_size: number
  priority_order: 'newest_first' | 'oldest_first' | 'high_quality_first'
  
  min_quality_threshold: number
  skip_failed_assets: boolean
  create_backups: boolean
  
  estimated_duration_hours: number
  scheduled_start?: string
}

export interface MigrationStatus {
  migration_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  progress_percentage: number
  
  processed_count: number
  successful_count: number
  failed_count: number
  skipped_count: number
  
  started_at?: string
  completed_at?: string
  estimated_remaining_minutes?: number
  
  recent_errors: string[]
  retry_queue: string[]
}

// Display format configurations
export const DISPLAY_FORMAT_CONFIG = {
  html: {
    label: 'HTML',
    icon: '🌐',
    color: 'text-blue-600',
    description: 'Rich HTML format with styling'
  },
  markdown: {
    label: 'Markdown',
    icon: '📝',
    color: 'text-green-600',
    description: 'Markdown format for documentation'
  },
  text: {
    label: 'Plain Text',
    icon: '📄',
    color: 'text-gray-600',
    description: 'Simple text format'
  }
}

// Transformation status configurations
export const TRANSFORMATION_STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    icon: '⏳',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    description: 'Transformation queued'
  },
  success: {
    label: 'Success',
    icon: '✅',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    description: 'Successfully transformed'
  },
  failed: {
    label: 'Failed',
    icon: '❌',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    description: 'Transformation failed'
  }
}