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