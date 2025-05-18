// Tipi per workspace/progetti
export type WorkspaceStatus = 'created' | 'active' | 'paused' | 'completed' | 'error';

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

// Tipi per agenti
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

// Tipi per task
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
}

export interface TaskCreateData {
  workspace_id: string;
  agent_id: string;
  name: string;
  description?: string;
  status?: TaskStatus;
}

// Tipi per handoff
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

// Tipi per il director
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

// Tipi per tool personalizzati
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

// Tipi per l'analisi Instagram
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

export interface ExecutorStatus {
  is_running: boolean;
  is_paused: boolean;
  status_string: "running" | "paused" | "stopped";
}

export interface AgentActivityStat {
  completed: number;
  failed: number;
  name?: string; // Il nome potrebbe essere aggiunto in futuro
}

export interface SessionStats {
  tasks_completed_successfully: number;
  tasks_failed: number;
  agent_activity: Record<string, AgentActivityStat>; // agent_id come chiave
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
}

// Human Feedback Types
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

export interface ProjectOutput {
  task_id: string;
  task_name: string;
  output: string;
  agent_name: string;
  agent_role: string;
  created_at: string;
  summary?: string;
  type: 'general' | 'analysis' | 'recommendation' | 'document';
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