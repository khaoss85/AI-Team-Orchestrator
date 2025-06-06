// frontend/src/types/index.ts - COMPLETE ENHANCED VERSION WITH ASSET SUPPORT

// ✅ Base types remain unchanged
export type WorkspaceStatus = 'created' | 'active' | 'paused' | 'completed' | 'error';

export type OutputType =
  | 'general'
  | 'analysis'
  | 'recommendation'
  | 'document'
  | 'final_deliverable';

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  status: WorkspaceStatus;
  goal?: string;
  budget?: {
    max_amount: number;
    currency: string;
  };
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreateData {
  name: string;
  description?: string;
  user_id: string;
  goal?: string;
  budget?: {
    max_amount: number;
    currency: string;
  };
}

// ✅ Agent types remain unchanged
export type AgentStatus = 'created' | 'initializing' | 'active' | 'paused' | 'error' | 'terminated';
export type AgentSeniority = 'junior' | 'senior' | 'expert';
export type HealthStatus = 'unknown' | 'healthy' | 'degraded' | 'unhealthy';

export enum SkillLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  EXPERT = "expert"
}

export enum PersonalityTrait {
  ANALYTICAL = "analytical",
  CREATIVE = "creative",
  DETAIL_ORIENTED = "detail-oriented",
  PROACTIVE = "proactive",
  COLLABORATIVE = "collaborative",
  DECISIVE = "decisive",
  INNOVATIVE = "innovative",
  METHODICAL = "methodical",
  ADAPTABLE = "adaptable",
  DIPLOMATIC = "diplomatic"
}

export enum CommunicationStyle {
  FORMAL = "formal",
  CASUAL = "casual",
  TECHNICAL = "technical",
  CONCISE = "concise",
  DETAILED = "detailed",
  EMPATHETIC = "empathetic",
  ASSERTIVE = "assertive"
}

export interface Skill {
  name: string;
  level: SkillLevel;
  description?: string;
}

export interface AgentHealth {
  status: HealthStatus;
  last_update?: string;
  details?: Record<string, any>;
}

export interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  role: string;
  seniority: AgentSeniority;
  description?: string;
  system_prompt?: string;
  status: AgentStatus;
  health: AgentHealth;
  llm_config?: Record<string, any>;
  tools?: Record<string, any>[];
  can_create_tools?: boolean;
  personality_traits?: PersonalityTrait[];
  communication_style?: CommunicationStyle;
  hard_skills?: Skill[];
  soft_skills?: Skill[];
  background_story?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentCreateData {
  workspace_id: string;
  name: string;
  role: string;
  seniority: AgentSeniority;
  description?: string;
  system_prompt?: string;
  model_config?: Record<string, any>;
  tools?: Record<string, any>[];
}

// ✅ Task types - Enhanced with asset context
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'canceled';

export interface Task {
  id: string;
  workspace_id: string;
  agent_id?: string;
  name: string;
  description?: string;
  status: TaskStatus;
  result?: Record<string, any>;
  created_at: string;
  updated_at: string;
  context_data?: EnhancedTaskContextData;
}

export interface TaskResultDetailsData {
  task_id: string;
  task_name: string;
  summary?: string;
  output?: string;
  status?: string;
  key_points?: string[];
  next_steps?: string[];
  detailed_results_json?: any;
  execution_time_seconds?: number;
  cost_estimated?: number;
  tokens_used?: { [key: string]: number };
  model_used?: string;
  agent_name?: string;
  agent_role?: string;
  assigned_agent_name?: string;
  assigned_agent_role?: string;
  metrics?: Record<string, any>;
  rationale?: string;
}

export interface TaskCreateData {
  workspace_id: string;
  agent_id: string;
  name: string;
  description?: string;
  status?: TaskStatus;
}

// ✅ Handoff types remain unchanged
export interface Handoff {
  id: string;
  source_agent_id: string;
  target_agent_id: string;
  description?: string;
  created_at: string;
}

export interface HandoffCreateData {
  source_agent_id: string;
  target_agent_id: string;
  description?: string;
}

// ✅ Director types remain unchanged
export interface DirectorConfig {
  workspace_id: string;
  goal: string;
  budget_constraint: {
    max_amount: number;
    currency: string;
  };
  user_id: string;
  user_feedback?: string;
}

export interface DirectorTeamProposal {
  id?: string; 
  workspace_id: string;
  agents: AgentCreateData[];
  handoffs: HandoffCreateData[];
  estimated_cost: {
    total?: number;
    total_estimated_cost?: number;
    breakdown?: Record<string, number>;
    breakdown_by_agent?: Record<string, number>;
    currency?: string;
    estimated_duration_days?: number;
    notes?: string;
  };
  rationale: string;
  user_feedback?: string;
}

// ✅ Custom tools remain unchanged
export interface CustomTool {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  code: string;
  created_by: string;
  created_at: string;
  updated_at?: string;
}

export interface CustomToolCreate {
  name: string;
  description?: string;
  code: string;
  workspace_id: string;
  created_by: string;
}

// ✅ Instagram tools remain unchanged
export interface HashtagAnalysis {
  [hashtag: string]: {
    posts_count: number;
    engagement_rate: string;
    growth_rate: string;
    trending: boolean;
    popularity_score: number;
    related_tags: string[];
    best_posting_times: string[];
  };
  analysis?: {
    top_performing_hashtag: string;
    trending_hashtags: string[];
    recommendation: string;
  };
}

export interface AccountAnalysis {
  username: string;
  followers_count: number;
  following_count: number;
  posts_count: number;
  engagement_rate: string;
  post_types_distribution: {
    images: number;
    videos: number;
    carousels: number;
  };
  posting_frequency: string;
  top_hashtags: string[];
  best_performing_content: {
    type: string;
    average_likes: number;
    average_comments: number;
  };
  growth_trend: string;
  audience_demographics: {
    age_groups: {
      "18-24": number;
      "25-34": number;
      "35-44": number;
      "45+": number;
    };
    gender_split: {
      male: number;
      female: number;
    };
  };
}

export interface ContentIdea {
  title: string;
  description: string;
  content_type: string;
  theme: string;
  hashtags: string[];
  estimated_engagement: string;
  best_posting_time: string;
  visual_elements: string[];
}

// ✅ Executor types - Enhanced with asset tracking
export interface ExecutorStatus {
  is_running: boolean;
  is_paused: boolean;
  status_string: "running" | "paused" | "stopped";
}

export interface AgentActivityStat {
  completed: number;
  failed: number;
  name?: string;
}

export interface SessionStats {
  tasks_completed_successfully: number;
  tasks_failed: number;
  agent_activity: Record<string, AgentActivityStat>;
}

export interface ExecutorDetailedStats {
  executor_status: string;
  tasks_in_queue: number;
  tasks_actively_processing: number;
  max_concurrent_tasks: number;
  total_execution_log_entries: number;
  session_stats: SessionStats;
  budget_tracker_stats: {
    tracked_agents_count: number;
  };
  // 🆕 NEW: Asset tracking in executor stats
  asset_tracking?: {
    asset_tasks_processed: number;
    asset_completion_events: number;
    deliverable_triggers: number;
    asset_enhancement_events: number;
  };
}

// ✅ Human Feedback types remain unchanged
export interface FeedbackRequest {
  id: string;
  workspace_id: string;
  request_type: 'task_approval' | 'strategy_review' | 'intervention_required' | 'priority_decision' | 'resource_allocation';
  title: string;
  description: string;
  proposed_actions: ProposedAction[];
  context: Record<string, any>;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'approved' | 'rejected' | 'modified' | 'expired';
  created_at: string;
  expires_at: string;
  response?: any;
  responded_at?: string;
}

export interface ProposedAction {
  type: string;
  task_name?: string;
  description?: string;
  target_role?: string;
  priority?: string;
  impact?: string;
}

export interface FeedbackResponse {
  approved: boolean;
  status: 'approved' | 'rejected';
  comment?: string;
  modifications?: any[];
  reason?: string;
}

export interface TaskAnalysisResponse {
  task_counts: Record<string, number>;
  failure_analysis: {
    total_failures: number;
    max_turns_failures: number;
    execution_errors: number;
    failure_reasons: Record<string, number>;
    average_failure_time: number;
  };
  handoff_analysis: {
    total_handoff_tasks: number;
    handoff_success_rate: number;
    recent_handoff_pattern: Array<{
      name: string;
      created_at: string;
      status: string;
      agent_id: string;
    }>;
    most_common_handoff_types: Record<string, number>;
  };
  potential_issues: {
    runaway_detected: boolean;
    excessive_handoffs: boolean;
    high_failure_rate: boolean;
    stuck_agents: string[];
    queue_overflow_risk: boolean;
  };
  recommendations: string[];
  analysis_timestamp: string;
}

export interface ActionableAsset {
  asset_name: string;  // Keep snake_case for API consistency
  asset_data: Record<string, any>;
  source_task_id: string;
  extraction_method: string;
  validation_score: number;
  actionability_score: number;
  ready_to_use: boolean;
  usage_instructions?: string;
  automation_ready?: boolean;
  file_download_url?: string;
  schema_compliant?: boolean;
}

export interface AssetRequirement {
  asset_type: string;
  asset_format: 'structured_data' | 'document' | 'spreadsheet';
  actionability_level: 'ready_to_use' | 'needs_customization' | 'template';
  business_impact: 'immediate' | 'short_term' | 'strategic';
  priority: number;
  validation_criteria: string[];
}

export interface AssetSchema {
  asset_name: string;
  schema_definition: Record<string, any>;
  validation_rules: string[];
  usage_instructions: string;
  automation_ready: boolean;
}

export interface AssetTrackingData {
  workspace_id: string;
  asset_summary: {
    total_asset_tasks: number;
    completed_asset_tasks: number;
    pending_asset_tasks: number;
    completion_rate: number;
    deliverable_ready: boolean;
  };
  asset_types_breakdown: Record<string, {
    total: number;
    completed: number;
  }>;
  completed_assets: AssetTaskInfo[];
  pending_assets: AssetTaskInfo[];
  analysis_timestamp: string;
}

export interface AssetTaskInfo {
  task_id: string;
  task_name: string;
  asset_type?: string;
  status: string;
  agent_role?: string;
  created_at?: string;
  updated_at?: string;
}

// 🆕 NEW: Asset Dashboard Types
export interface AssetViewerProps {
  asset: ActionableAsset;
  onDownload?: (asset: ActionableAsset) => void;
  onUse?: (asset: ActionableAsset) => void;
  showActions?: boolean;
}

export interface AssetDashboardData {
  requirements: {
    deliverable_category: string;
    primary_assets_needed: AssetRequirement[];
    deliverable_structure: Record<string, any>;
  };
  tracking: AssetTrackingData;
  schemas: Record<string, AssetSchema>;
  extraction_status: {
    extraction_summary: {
      total_completed_tasks: number;
      asset_production_tasks: number;
      extraction_ready_tasks: number;
      extraction_readiness_rate: number;
    };
    extraction_candidates: Array<{
      task_id: string;
      task_name: string;
      asset_type?: string;
      has_structured_output: boolean;
      extraction_ready: boolean;
    }>;
  };
}

// ✅ Enhanced Project Deliverables - Backward Compatible
export interface ProjectOutput {
  task_id: string;
  task_name: string;
  output: string;
  agent_name: string;
  agent_role: string;
  created_at: string;
  summary?: string;
  type: OutputType;
  title?: string;
  description?: string;
  key_insights?: string[];
  metrics?: Record<string, any>;
  category?: string;
  actionable_assets?: Record<string, ActionableAsset>;
  actionability_score?: number;
  automation_ready?: boolean;
  usage_guide?: Record<string, string>;
  next_steps?: string[];
  result?: Record<string, any>;
  visual_summary?: string;
  execution_time_seconds?: number;
  cost_estimated?: number;
  tokens_used?: { [key: string]: number };
  model_used?: string;
  rationale?: string;
}

export interface ProjectOutputExtended extends ProjectOutput {
  // Additional frontend-specific fields
  icon?: string;
  priority?: number;
  completeness?: number;
  isFinalDeliverable?: boolean;
  execution_time_seconds?: number;
  cost_estimated?: number;
  tokens_used?: { [key: string]: number };
  model_used?: string;
  rationale?: string;
  visual_summary?: string;
  content?: {
    summary: string;
    keyPoints: string[];
    details: string;
    keyInsights: string[];
    metrics: Record<string, any>;
    recommendations: string[];
    nextSteps: string[];
    actionableAssets?: Record<string, ActionableAsset>;
    usageGuide?: Record<string, string>;
  };
}

export interface ProjectDeliverables {
  workspace_id: string;
  summary: string;
  key_outputs: ProjectOutput[];
  insight_cards?: ProjectDeliverableCard[];
  final_recommendations: string[];
  next_steps: string[];
  completion_status: 'in_progress' | 'awaiting_review' | 'completed';
  total_tasks: number;
  completed_tasks: number;
  generated_at: string;
}

export interface ProjectDeliverablesExtended extends ProjectDeliverables {
  key_outputs: ProjectOutputExtended[];
  asset_summary?: {
    total_assets: number;
    ready_to_use_assets: number;
    automation_ready_assets: number;
    average_actionability_score: number;
  };
  actionable_assets_catalog?: Record<string, ActionableAsset>;
}

export interface DeliverableFeedback {
  feedback_type: 'approve' | 'request_changes' | 'general_feedback';
  message: string;
  specific_tasks?: string[];
  priority: 'low' | 'medium' | 'high';
}

export interface ProjectDeliverableCard {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  key_insights: string[];
  metrics?: Record<string, any>;
  created_by: string;
  created_at: string;
  completeness_score: number;
}

export interface AssetDisplayData {
  asset: ActionableAsset;
  task_info: AssetTaskInfo;
  schema?: AssetSchema;
}

export interface AssetManagementState {
  // Raw API data
  tracking: AssetTrackingData | null;
  requirements: {
    workspace_id: string;
    deliverable_category: string;
    primary_assets_needed: AssetRequirement[];
    deliverable_structure: Record<string, any>;
    generated_at: string;
  } | null;
  schemas: Record<string, AssetSchema>;
  extractionStatus: {
    extraction_summary: {
      total_completed_tasks: number;
      asset_production_tasks: number;
      extraction_ready_tasks: number;
      extraction_readiness_rate: number;
    };
    extraction_candidates: Array<{
      task_id: string;
      task_name: string;
      asset_type?: string;
      has_structured_output: boolean;
      extraction_ready: boolean;
      completed_at: string;
    }>;
    next_steps: string[];
  } | null;

  // Deliverables data
  deliverables: ProjectDeliverablesExtended | null;
  finalDeliverables: ProjectOutputExtended[];
  
  // Processed deliverable assets
  deliverableAssets: Record<string, ActionableAsset>;
  processedAssets: AssetDisplayData[];
  
  // States
  loading: boolean;
  error: string | null;
}

export interface AssetCompletionStats {
  totalAssets: number;
  completedAssets: number;
  pendingAssets: number;
  completionRate: number;
  isDeliverableReady: boolean;
}

export interface AssetProgress {
  completed: number;
  total: number;
  percentage: number;
}

export interface UseAssetManagementReturn {
  // Direct access to structured data
  tracking: AssetTrackingData | null;
  requirements: AssetManagementState['requirements'];
  schemas: Record<string, AssetSchema>;
  extractionStatus: AssetManagementState['extractionStatus'];

  // Deliverables
  deliverables: ProjectDeliverablesExtended | null;
  finalDeliverables: ProjectOutputExtended[];
  
  // Direct access to processed assets
  assets: ActionableAsset[];
  assetDisplayData: AssetDisplayData[];
  deliverableAssets: Record<string, ActionableAsset>;
  
  // States
  loading: boolean;
  error: string | null;
  
  // Actions
  refresh: () => Promise<void>;
  triggerAssetAnalysis: () => Promise<boolean>;
  checkDeliverableReadiness: () => Promise<boolean>;
  
  // Computed values and helpers
  getAssetProgress: () => AssetProgress;
  getAssetsByType: (assetType: string) => AssetDisplayData[];
  isDeliverableReady: () => boolean;
  getRequiredAssetTypes: () => string[];
  getCompletedAssetTypes: () => string[];
  getMissingAssetTypes: () => string[];
  getAssetTypeProgress: (assetType: string) => AssetProgress;
  canExtractAssets: () => boolean;
  getExtractionCandidates: () => Array<{
    task_id: string;
    task_name: string;
    asset_type?: string;
    has_structured_output: boolean;
    extraction_ready: boolean;
    completed_at: string;
  }>;
  hasAssetSchemas: () => boolean;
  getSchemaForAssetType: (assetType: string) => AssetSchema | null;
  isAssetTask: (task: any) => boolean;
  getAssetTypeFromTask: (task: any) => string | null;
  getAssetCompletionStats: () => AssetCompletionStats;
}

export interface EnhancedTaskContextData {
  // Asset-oriented fields
  asset_production?: boolean;
  asset_oriented_task?: boolean;
  asset_type?: string;
  detected_asset_type?: string;
  project_phase?: 'ANALYSIS' | 'IMPLEMENTATION' | 'FINALIZATION';
  is_final_deliverable?: boolean;
  deliverable_aggregation?: boolean;
  triggers_project_completion?: boolean;
  
  [key: string]: any;
}

export interface AssetViewerProps {
  asset: ActionableAsset;
  onDownload?: () => void;
  onUse?: () => void;
  onViewDetails?: () => void;
  showActions?: boolean;
}

export interface AssetDashboardProps {
  workspaceId: string;
}

export interface EnhancedProjectResult {
  id: string;
  title: string;
  description: string;
  date: string;
  type: string;
  icon: string;
  creator: string;
  isFinalDeliverable: boolean;
  completeness: number;
  priority: number;
  content: {
    summary: string;
    keyPoints: string[];
    details: string;
    keyInsights: string[];
    metrics: Record<string, any>;
    recommendations: string[];
    nextSteps: string[];
    actionableAssets?: Record<string, ActionableAsset>;
    usageGuide?: Record<string, string>;
  };
}
export interface AgentProposal {
  id: string;
  agentName: string;
  agentRole: string;
  title: string;
  type: 'analysis' | 'deliverable' | 'system' | 'optimization';
  status: 'ready_for_review' | 'implementing' | 'approved' | 'rejected' | 'completed';
  confidence: number;
  timestamp: string;
  taskId: string;
  preview: {
    type: 'chart' | 'calendar' | 'flowchart' | 'document' | 'dataset';
    data: string;
    thumbnail?: string;
  };
  output: {
    summary: string;
    actionable: string;
    impact: string;
    technicalDetails?: any;
  };
  nextSteps: Array<{
    action: string;
    urgency: 'high' | 'medium' | 'low';
    effort: 'low' | 'medium' | 'high';
    automated?: boolean;
  }>;
  metadata: {
    createdAt: string;
    updatedAt: string;
    sourceTaskId: string;
    estimatedValue?: number;
    riskLevel?: 'low' | 'medium' | 'high';
  };
}

export interface OrchestrationStats {
  total: number;
  pending: number;
  implementing: number;
  completed: number;
  avgConfidence: number;
  totalEstimatedValue: number;
}
