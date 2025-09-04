-- 🤖 AI Team Orchestrator - Complete Database Schema
-- Generated from production Supabase instance
-- This schema contains all tables and relationships for the AI Team Orchestrator system

-- Enable UUID extension (required)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Core System Tables
-- ============================================================================

CREATE TABLE public.workspaces (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  user_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'created'::text,
  goal text,
  budget jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT workspaces_pkey PRIMARY KEY (id)
);

CREATE TABLE public.workspace_goals (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  metric_type character varying NOT NULL,
  target_value numeric NOT NULL CHECK (target_value > 0::numeric),
  current_value numeric DEFAULT 0,
  unit text DEFAULT ''::text,
  priority integer DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
  status text DEFAULT 'active'::text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text, 'failed'::text, 'archived'::text, 'completed_pending_review'::text])),
  success_criteria jsonb DEFAULT '{}'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  description text,
  source_goal_text text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  last_validation_at timestamp with time zone,
  validation_frequency_minutes integer DEFAULT 20,
  confidence numeric DEFAULT 0.8 CHECK (confidence >= 0.0 AND confidence <= 1.0),
  semantic_context jsonb DEFAULT '{}'::jsonb,
  goal_type text DEFAULT 'deliverable'::text CHECK (goal_type = ANY (ARRAY['deliverable'::text, 'metric'::text, 'quality'::text, 'timeline'::text, 'quantity'::text])),
  is_percentage boolean DEFAULT false,
  is_minimum boolean DEFAULT true,
  asset_completion_rate numeric DEFAULT 0.0,
  quality_score numeric DEFAULT 0.0,
  asset_requirements_count integer DEFAULT 0,
  assets_completed_count integer DEFAULT 0,
  ai_validation_enabled boolean DEFAULT true,
  memory_insights jsonb DEFAULT '{}'::jsonb,
  progress_history jsonb DEFAULT '[]'::jsonb,
  last_progress_update timestamp with time zone DEFAULT now(),
  CONSTRAINT workspace_goals_pkey PRIMARY KEY (id),
  CONSTRAINT workspace_goals_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

-- ============================================================================
-- AI Agent System
-- ============================================================================

CREATE TABLE public.agents (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid,
  name text NOT NULL,
  role text NOT NULL,
  seniority text NOT NULL,
  description text,
  system_prompt text,
  status text NOT NULL DEFAULT 'created'::text,
  health jsonb DEFAULT '{"status": "unknown", "last_update": null}'::jsonb,
  llm_config jsonb,
  tools jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  can_create_tools boolean DEFAULT false,
  first_name text,
  last_name text,
  personality_traits jsonb,
  communication_style text,
  hard_skills jsonb,
  soft_skills jsonb,
  background_story text,
  daily_cost numeric DEFAULT 8.0,
  skills jsonb DEFAULT '[]'::jsonb,
  status_reason text,
  ai_handoff_history jsonb,
  ai_optimization_stats jsonb,
  CONSTRAINT agents_pkey PRIMARY KEY (id),
  CONSTRAINT agents_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.agent_handoffs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_agent_id uuid,
  target_agent_id uuid,
  description text,
  created_at timestamp with time zone DEFAULT now(),
  workspace_id uuid NOT NULL,
  CONSTRAINT agent_handoffs_pkey PRIMARY KEY (id),
  CONSTRAINT agent_handoffs_target_agent_id_fkey FOREIGN KEY (target_agent_id) REFERENCES public.agents(id),
  CONSTRAINT agent_handoffs_source_agent_id_fkey FOREIGN KEY (source_agent_id) REFERENCES public.agents(id),
  CONSTRAINT agent_handoffs_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.agent_performance_metrics (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  agent_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  avg_quality_score double precision DEFAULT 0.0,
  completed_tasks integer DEFAULT 0,
  avg_task_duration_seconds double precision DEFAULT 0.0,
  last_updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT agent_performance_metrics_pkey PRIMARY KEY (id),
  CONSTRAINT agent_performance_metrics_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT agent_performance_metrics_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id)
);

-- ============================================================================
-- Task System
-- ============================================================================

CREATE TABLE public.tasks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  agent_id uuid,
  assigned_to_role text,
  name text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'pending'::text,
  priority text NOT NULL DEFAULT 'medium'::text,
  parent_task_id uuid,
  depends_on_task_ids ARRAY,
  estimated_effort_hours double precision,
  deadline timestamp with time zone,
  context_data jsonb,
  result jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  created_by_task_id uuid,
  created_by_agent_id uuid,
  creation_type character varying,
  delegation_depth integer DEFAULT 0,
  iteration_count integer DEFAULT 0,
  max_iterations integer,
  dependency_map jsonb,
  goal_id uuid,
  metric_type text CHECK (metric_type IS NULL OR length(metric_type) >= 1 AND length(metric_type) <= 100),
  contribution_expected numeric CHECK (contribution_expected IS NULL OR contribution_expected >= 0::numeric),
  numerical_target jsonb DEFAULT '{}'::jsonb,
  is_corrective boolean DEFAULT false,
  success_criteria jsonb DEFAULT '[]'::jsonb,
  completed_at timestamp with time zone,
  target_asset_type character varying,
  produces_artifact boolean DEFAULT false,
  asset_requirement_id uuid,
  quality_validated boolean DEFAULT false,
  ai_enhanced boolean DEFAULT false,
  openai_thread_id character varying,
  real_time_thinking jsonb DEFAULT '{}'::jsonb,
  semantic_hash character varying,
  ai_context_analysis jsonb,
  ai_collaboration_mode character varying DEFAULT NULL::character varying,
  ai_complexity_level character varying DEFAULT NULL::character varying,
  CONSTRAINT tasks_pkey PRIMARY KEY (id),
  CONSTRAINT fk_tasks_asset_requirement FOREIGN KEY (asset_requirement_id) REFERENCES public.goal_asset_requirements(id),
  CONSTRAINT tasks_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id),
  CONSTRAINT tasks_created_by_agent_id_fkey FOREIGN KEY (created_by_agent_id) REFERENCES public.agents(id),
  CONSTRAINT tasks_created_by_task_id_fkey FOREIGN KEY (created_by_task_id) REFERENCES public.tasks(id),
  CONSTRAINT tasks_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.workspace_goals(id),
  CONSTRAINT tasks_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.tasks(id),
  CONSTRAINT tasks_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.task_dependencies (
  task_id uuid NOT NULL,
  depends_on_task_id uuid NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT task_dependencies_pkey PRIMARY KEY (task_id, depends_on_task_id),
  CONSTRAINT task_dependencies_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT task_dependencies_depends_on_task_id_fkey FOREIGN KEY (depends_on_task_id) REFERENCES public.tasks(id)
);

CREATE TABLE public.task_executions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL,
  agent_id uuid,
  workspace_id uuid NOT NULL,
  status text NOT NULL CHECK (status = ANY (ARRAY['started'::text, 'completed'::text, 'failed_retriable'::text, 'failed_terminal'::text])),
  started_at timestamp with time zone NOT NULL DEFAULT now(),
  completed_at timestamp with time zone,
  execution_time_seconds double precision,
  result jsonb,
  logs text,
  token_usage jsonb,
  error_message text,
  error_type text,
  retry_count integer DEFAULT 0,
  openai_trace_id text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT task_executions_pkey PRIMARY KEY (id),
  CONSTRAINT task_executions_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id),
  CONSTRAINT task_executions_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT task_executions_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id)
);

-- ============================================================================
-- Deliverables System
-- ============================================================================

CREATE TABLE public.deliverables (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  workspace_id uuid NOT NULL,
  goal_id uuid,
  task_id uuid,
  title text NOT NULL,
  description text,
  content jsonb,
  type text,
  status text NOT NULL DEFAULT 'pending'::text,
  readiness_score double precision,
  completion_percentage double precision,
  business_value_score double precision,
  quality_metrics jsonb,
  metadata jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  auto_improvements jsonb DEFAULT '[]'::jsonb,
  business_specificity_score numeric DEFAULT 0.00,
  tool_usage_score numeric DEFAULT 0.00,
  content_quality_score numeric DEFAULT 0.00,
  creation_confidence numeric DEFAULT 0.00,
  creation_reasoning text,
  learning_patterns_created integer DEFAULT 0,
  execution_time numeric DEFAULT 0.000,
  stages_completed integer DEFAULT 0,
  quality_level character varying DEFAULT 'acceptable'::character varying,
  display_content text,
  display_format character varying DEFAULT 'html'::character varying,
  display_summary text,
  display_metadata jsonb DEFAULT '{}'::jsonb,
  auto_display_generated boolean DEFAULT false,
  display_content_updated_at timestamp without time zone,
  content_transformation_status character varying DEFAULT 'pending'::character varying,
  content_transformation_error text,
  transformation_timestamp timestamp without time zone,
  transformation_method character varying DEFAULT 'ai'::character varying,
  display_quality_score double precision DEFAULT 0.0,
  user_friendliness_score double precision DEFAULT 0.0,
  readability_score double precision DEFAULT 0.0,
  ai_confidence double precision DEFAULT 0.0,
  CONSTRAINT deliverables_pkey PRIMARY KEY (id),
  CONSTRAINT deliverables_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.workspace_goals(id),
  CONSTRAINT deliverables_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT deliverables_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

-- ============================================================================
-- Asset Management System
-- ============================================================================

CREATE TABLE public.goal_asset_requirements (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  decomposition_id uuid,
  goal_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  todo_type text NOT NULL CHECK (todo_type = ANY (ARRAY['simple'::text, 'complex'::text, 'research'::text, 'implementation'::text, 'asset_requirement'::text, 'deliverable'::text])),
  internal_id text NOT NULL,
  name text NOT NULL,
  description text NOT NULL,
  priority text NOT NULL CHECK (priority = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'urgent'::text, 'critical'::text])),
  estimated_effort text CHECK (estimated_effort = ANY (ARRAY['small'::text, 'medium'::text, 'large'::text, 'xlarge'::text, '1_hour'::text, '2_hours'::text, '5_hours'::text, 'half_day'::text, 'full_day'::text, 'low'::text, 'high'::text, 'quick'::text, 'moderate'::text, 'complex'::text, 'extensive'::text])),
  user_impact text CHECK (user_impact = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
  complexity text CHECK (complexity = ANY (ARRAY['simple'::text, 'medium'::text, 'complex'::text])),
  value_proposition text,
  completion_criteria text,
  deliverable_type text CHECK (deliverable_type = ANY (ARRAY['concrete_asset'::text, 'strategic_thinking'::text])),
  supports_assets ARRAY,
  status text NOT NULL DEFAULT 'pending'::text CHECK (status = ANY (ARRAY['pending'::text, 'in_progress'::text, 'completed'::text, 'blocked'::text])),
  progress_percentage integer DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
  linked_task_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  asset_type character varying DEFAULT 'document'::character varying,
  asset_format character varying DEFAULT 'structured_data'::character varying,
  acceptance_criteria jsonb DEFAULT '{}'::jsonb,
  weight numeric DEFAULT 1.0,
  mandatory boolean DEFAULT true,
  business_value_score numeric DEFAULT 0.5,
  validation_rules jsonb DEFAULT '{}'::jsonb,
  automation_ready boolean DEFAULT false,
  ai_generated boolean DEFAULT true,
  language_agnostic boolean DEFAULT true,
  sdk_compatible boolean DEFAULT true,
  CONSTRAINT goal_asset_requirements_pkey PRIMARY KEY (id),
  CONSTRAINT goal_todos_goal_id_fkey FOREIGN KEY (goal_id) REFERENCES public.workspace_goals(id),
  CONSTRAINT goal_todos_linked_task_id_fkey FOREIGN KEY (linked_task_id) REFERENCES public.tasks(id),
  CONSTRAINT goal_todos_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.asset_artifacts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  requirement_id uuid,
  task_id uuid,
  agent_id uuid,
  artifact_name character varying NOT NULL,
  artifact_type character varying NOT NULL CHECK (artifact_type::text = ANY (ARRAY['file'::character varying::text, 'text'::character varying::text, 'json'::character varying::text, 'url'::character varying::text, 'binary'::character varying::text, 'structured_data'::character varying::text, 'openai_asset'::character varying::text])),
  content text,
  content_format character varying DEFAULT 'text'::character varying,
  file_path character varying,
  external_url character varying,
  openai_file_id character varying,
  metadata jsonb DEFAULT '{}'::jsonb,
  size_bytes integer,
  word_count integer,
  checksum character varying,
  quality_score numeric DEFAULT 0.0 CHECK (quality_score >= 0::numeric AND quality_score <= 1::numeric),
  validation_passed boolean DEFAULT false,
  validation_details jsonb DEFAULT '{}'::jsonb,
  validation_errors ARRAY,
  ai_quality_check jsonb DEFAULT '{}'::jsonb,
  status character varying DEFAULT 'draft'::character varying CHECK (status::text = ANY (ARRAY['draft'::character varying::text, 'ai_validated'::character varying::text, 'human_review'::character varying::text, 'approved'::character varying::text, 'rejected'::character varying::text, 'needs_improvement'::character varying::text])),
  version integer DEFAULT 1,
  human_review_required boolean DEFAULT false,
  business_value_score numeric DEFAULT 0.0,
  actionability_score numeric DEFAULT 0.0,
  automation_ready boolean DEFAULT false,
  ai_enhanced boolean DEFAULT false,
  enhancement_applied jsonb DEFAULT '{}'::jsonb,
  original_content_hash character varying,
  detected_language character varying DEFAULT 'auto'::character varying,
  language_agnostic boolean DEFAULT true,
  memory_context jsonb DEFAULT '{}'::jsonb,
  learning_insights jsonb DEFAULT '{}'::jsonb,
  thinking_process jsonb DEFAULT '{}'::jsonb,
  reasoning_steps ARRAY,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  approved_at timestamp with time zone,
  approved_by_user_id uuid,
  workspace_id uuid NOT NULL,
  CONSTRAINT asset_artifacts_pkey PRIMARY KEY (id),
  CONSTRAINT asset_artifacts_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id),
  CONSTRAINT asset_artifacts_requirement_id_fkey FOREIGN KEY (requirement_id) REFERENCES public.goal_asset_requirements(id),
  CONSTRAINT asset_artifacts_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT fk_asset_artifacts_agent FOREIGN KEY (agent_id) REFERENCES public.agents(id),
  CONSTRAINT fk_asset_artifacts_requirement FOREIGN KEY (requirement_id) REFERENCES public.goal_asset_requirements(id),
  CONSTRAINT fk_asset_artifacts_task FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT fk_asset_artifacts_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

-- ============================================================================
-- AI Memory & Learning System
-- ============================================================================

CREATE TABLE public.workspace_insights (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  task_id uuid,
  agent_role text NOT NULL,
  insight_type text NOT NULL CHECK (insight_type = ANY (ARRAY['success_pattern'::text, 'failure_lesson'::text, 'discovery'::text, 'constraint'::text, 'optimization'::text, 'progress'::text, 'risk'::text, 'opportunity'::text, 'resource'::text])),
  content text NOT NULL CHECK (length(content) >= 5 AND length(content) <= 10000),
  relevance_tags ARRAY DEFAULT '{}'::text[],
  confidence_score numeric DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  expires_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  metadata jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT workspace_insights_pkey PRIMARY KEY (id),
  CONSTRAINT workspace_insights_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT fk_workspace_insights_workspace_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT fk_workspace_insights_task_id FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT workspace_insights_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.memory_patterns (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  pattern_id character varying NOT NULL UNIQUE,
  pattern_type character varying NOT NULL,
  semantic_features jsonb NOT NULL DEFAULT '{}'::jsonb,
  success_indicators jsonb NOT NULL DEFAULT '[]'::jsonb,
  domain_context jsonb NOT NULL DEFAULT '{}'::jsonb,
  confidence numeric NOT NULL DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
  usage_count integer DEFAULT 0 CHECK (usage_count >= 0),
  created_at timestamp with time zone DEFAULT now(),
  last_used timestamp with time zone DEFAULT now(),
  business_context text,
  content_type text,
  effectiveness_score numeric DEFAULT 0.0,
  CONSTRAINT memory_patterns_pkey PRIMARY KEY (id)
);

CREATE TABLE public.learning_patterns (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  pattern_type character varying NOT NULL,
  pattern_name character varying NOT NULL,
  pattern_description text,
  pattern_strength numeric DEFAULT 0.5 CHECK (pattern_strength >= 0.0 AND pattern_strength <= 1.0),
  pattern_data jsonb DEFAULT '{}'::jsonb,
  confidence_score numeric DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  usage_count integer DEFAULT 1,
  last_reinforced_at timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT learning_patterns_pkey PRIMARY KEY (id)
);

-- ============================================================================
-- Real-Time Thinking System (Claude/o3 Style)
-- ============================================================================

CREATE TABLE public.thinking_processes (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  process_id character varying NOT NULL UNIQUE,
  workspace_id uuid NOT NULL,
  context text NOT NULL,
  process_type character varying DEFAULT 'general'::character varying,
  final_conclusion text,
  overall_confidence numeric DEFAULT 0.5 CHECK (overall_confidence >= 0.0 AND overall_confidence <= 1.0),
  started_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  metadata jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT thinking_processes_pkey PRIMARY KEY (id)
);

CREATE TABLE public.thinking_steps (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  step_id character varying NOT NULL UNIQUE,
  process_id character varying NOT NULL,
  step_type character varying NOT NULL CHECK (step_type::text = ANY (ARRAY['analysis'::character varying::text, 'reasoning'::character varying::text, 'evaluation'::character varying::text, 'conclusion'::character varying::text, 'context_loading'::character varying::text, 'perspective'::character varying::text, 'critical_review'::character varying::text, 'synthesis'::character varying::text])),
  content text NOT NULL,
  confidence numeric DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
  step_order integer DEFAULT 1,
  timestamp timestamp with time zone DEFAULT now(),
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT thinking_steps_pkey PRIMARY KEY (id),
  CONSTRAINT thinking_steps_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.thinking_processes(process_id)
);

CREATE TABLE public.thinking_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  process_id character varying,
  event_type character varying NOT NULL CHECK (event_type::text = ANY (ARRAY['process_started'::character varying::text, 'step_added'::character varying::text, 'process_completed'::character varying::text, 'thinking_updated'::character varying::text])),
  event_data jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT thinking_events_pkey PRIMARY KEY (id)
);

-- ============================================================================
-- Quality Assurance System
-- ============================================================================

CREATE TABLE public.quality_rules (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  asset_type character varying NOT NULL,
  rule_name character varying NOT NULL,
  rule_description text,
  ai_validation_prompt text NOT NULL,
  validation_model character varying DEFAULT 'gpt-4o-mini'::character varying,
  validation_config jsonb DEFAULT '{}'::jsonb,
  threshold_score numeric DEFAULT 0.8 CHECK (threshold_score >= 0.0 AND threshold_score <= 1.0),
  weight numeric DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 3.0),
  is_active boolean DEFAULT true,
  rule_order integer DEFAULT 1,
  failure_action character varying DEFAULT 'ai_enhance'::character varying,
  auto_learning_enabled boolean DEFAULT true,
  success_patterns jsonb DEFAULT '{}'::jsonb,
  failure_lessons jsonb DEFAULT '{}'::jsonb,
  language_agnostic boolean DEFAULT true,
  domain_agnostic boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT quality_rules_pkey PRIMARY KEY (id)
);

CREATE TABLE public.quality_validations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  artifact_id uuid,
  rule_id uuid,
  score numeric NOT NULL CHECK (score >= 0::numeric AND score <= 1::numeric),
  passed boolean NOT NULL,
  validation_output jsonb DEFAULT '{}'::jsonb,
  feedback text,
  ai_reasoning text,
  validated_at timestamp with time zone DEFAULT now(),
  validator_type character varying DEFAULT 'ai'::character varying CHECK (validator_type::text = ANY (ARRAY['ai'::character varying::text, 'human'::character varying::text, 'automated'::character varying::text, 'hybrid'::character varying::text])),
  openai_model_used character varying,
  openai_completion_id character varying,
  execution_time_ms integer,
  enhancement_suggested boolean DEFAULT false,
  enhancement_applied boolean DEFAULT false,
  enhancement_details jsonb DEFAULT '{}'::jsonb,
  actionability_assessment jsonb,
  ai_assessment jsonb,
  ai_driven boolean DEFAULT false,
  improvement_suggestions jsonb,
  business_impact text,
  quality_dimensions jsonb,
  pillar_compliance_check jsonb,
  validation_model text,
  processing_time_ms integer,
  workspace_id uuid,
  task_id uuid,
  validation_status text DEFAULT 'pending'::text,
  quality_score numeric DEFAULT 0.0,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  validation_details jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT quality_validations_pkey PRIMARY KEY (id),
  CONSTRAINT fk_quality_validations_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT fk_quality_validations_artifact FOREIGN KEY (artifact_id) REFERENCES public.asset_artifacts(id),
  CONSTRAINT fk_quality_validations_rule FOREIGN KEY (rule_id) REFERENCES public.quality_rules(id),
  CONSTRAINT quality_validations_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES public.asset_artifacts(id)
);

-- ============================================================================
-- Conversational AI System
-- ============================================================================

CREATE TABLE public.conversations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  chat_id text NOT NULL,
  schema_version text NOT NULL DEFAULT 'v2025-06-A'::text,
  title text,
  description text,
  active_messages ARRAY DEFAULT '{}'::jsonb[],
  archived_summaries ARRAY DEFAULT '{}'::jsonb[],
  context_snapshot jsonb DEFAULT '{}'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  conversational_features jsonb DEFAULT '{"context_aware": true, "tool_integration": true, "progressive_summarization": true}'::jsonb,
  last_summarization timestamp with time zone,
  CONSTRAINT conversations_pkey PRIMARY KEY (id),
  CONSTRAINT conversations_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.conversation_messages (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL,
  message_id text NOT NULL,
  role text NOT NULL CHECK (role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text])),
  content text NOT NULL,
  content_type text DEFAULT 'text'::text CHECK (content_type = ANY (ARRAY['text'::text, 'json'::text, 'markdown'::text, 'html'::text])),
  tools_used jsonb DEFAULT '[]'::jsonb,
  actions_performed jsonb DEFAULT '[]'::jsonb,
  artifacts_generated jsonb DEFAULT '[]'::jsonb,
  context_snapshot jsonb DEFAULT '{}'::jsonb,
  workspace_state_hash text,
  metadata jsonb DEFAULT '{}'::jsonb,
  estimated_tokens integer DEFAULT 0,
  processing_time_ms integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  conversation_identifier text,
  CONSTRAINT conversation_messages_pkey PRIMARY KEY (id),
  CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id)
);

-- ============================================================================
-- System Monitoring & Performance
-- ============================================================================

CREATE TABLE public.component_health (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  component_name text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'unknown'::text CHECK (status = ANY (ARRAY['healthy'::text, 'degraded'::text, 'unhealthy'::text, 'stopped'::text, 'unknown'::text])),
  health_score numeric DEFAULT 0.0 CHECK (health_score >= 0.0 AND health_score <= 1.0),
  last_heartbeat timestamp with time zone,
  heartbeat_interval_seconds integer DEFAULT 30,
  consecutive_failures integer DEFAULT 0,
  last_error text,
  last_success_at timestamp with time zone,
  avg_response_time_ms numeric DEFAULT 0.0,
  error_rate numeric DEFAULT 0.0,
  throughput_per_minute numeric DEFAULT 0.0,
  component_version text,
  configuration jsonb DEFAULT '{}'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  dependencies ARRAY DEFAULT '{}'::text[],
  dependent_components ARRAY DEFAULT '{}'::text[],
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  component_type text NOT NULL DEFAULT 'CORE'::text,
  CONSTRAINT component_health_pkey PRIMARY KEY (id)
);

CREATE TABLE public.ai_decision_log (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  decision_type character varying NOT NULL,
  source_agent_id uuid,
  target_agent_id uuid,
  task_id uuid,
  decision_data jsonb NOT NULL,
  execution_time_ms integer,
  success boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ai_decision_log_pkey PRIMARY KEY (id),
  CONSTRAINT ai_decision_log_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id),
  CONSTRAINT ai_decision_log_target_agent_id_fkey FOREIGN KEY (target_agent_id) REFERENCES public.agents(id),
  CONSTRAINT ai_decision_log_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT ai_decision_log_source_agent_id_fkey FOREIGN KEY (source_agent_id) REFERENCES public.agents(id)
);

-- ============================================================================
-- Human Feedback & Confirmation System
-- ============================================================================

CREATE TABLE public.human_feedback_requests (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid,
  request_type text NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  proposed_actions jsonb NOT NULL,
  context jsonb,
  priority text NOT NULL DEFAULT 'medium'::text,
  status text NOT NULL DEFAULT 'pending'::text,
  timeout_hours integer DEFAULT 24,
  created_at timestamp with time zone DEFAULT now(),
  expires_at timestamp with time zone NOT NULL,
  response jsonb,
  responded_at timestamp with time zone,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT human_feedback_requests_pkey PRIMARY KEY (id),
  CONSTRAINT human_feedback_requests_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.pending_confirmations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  action_id uuid NOT NULL UNIQUE,
  conversation_id uuid NOT NULL,
  message_id uuid NOT NULL,
  action_type text NOT NULL,
  action_description text NOT NULL,
  parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
  risk_level text NOT NULL DEFAULT 'medium'::text CHECK (risk_level = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
  status text NOT NULL DEFAULT 'pending'::text CHECK (status = ANY (ARRAY['pending'::text, 'confirmed'::text, 'cancelled'::text, 'expired'::text])),
  confirmed_by uuid,
  confirmed_at timestamp with time zone,
  expires_at timestamp with time zone NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  action_id_text text,
  conversation_identifier text,
  CONSTRAINT pending_confirmations_pkey PRIMARY KEY (id),
  CONSTRAINT pending_confirmations_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id),
  CONSTRAINT pending_confirmations_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.conversation_messages(id)
);

-- ============================================================================
-- Additional Support Tables
-- ============================================================================

CREATE TABLE public.team_proposals (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid,
  proposal_data jsonb NOT NULL,
  status text NOT NULL DEFAULT 'pending'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT team_proposals_pkey PRIMARY KEY (id),
  CONSTRAINT team_proposals_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id)
);

CREATE TABLE public.execution_logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid,
  agent_id uuid,
  task_id uuid,
  type text NOT NULL,
  content jsonb,
  created_at timestamp with time zone DEFAULT now(),
  message text,
  CONSTRAINT execution_logs_pkey PRIMARY KEY (id),
  CONSTRAINT execution_logs_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id),
  CONSTRAINT execution_logs_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id),
  CONSTRAINT execution_logs_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id)
);

CREATE TABLE public.logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  workspace_id uuid,
  type character varying NOT NULL DEFAULT 'info'::character varying,
  message text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT logs_pkey PRIMARY KEY (id)
);

-- ============================================================================
-- Performance Indexes
-- ============================================================================

-- Core workspace and goal indexes
CREATE INDEX IF NOT EXISTS idx_workspace_goals_workspace_id ON workspace_goals(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_status ON workspace_goals(status);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_semantic_context ON workspace_goals USING GIN(semantic_context);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_goal_type ON workspace_goals(goal_type);

-- Task system indexes
CREATE INDEX IF NOT EXISTS idx_tasks_workspace_id ON tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);

-- Deliverable indexes
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON deliverables(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_goal_id ON deliverables(goal_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);

-- Asset and artifact indexes
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_workspace_id ON asset_artifacts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_task_id ON asset_artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_status ON asset_artifacts(status);

-- Memory and insights indexes
CREATE INDEX IF NOT EXISTS idx_workspace_insights_workspace_id ON workspace_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_insight_type ON workspace_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_memory_patterns_pattern_type ON memory_patterns(pattern_type);

-- Agent performance indexes
CREATE INDEX IF NOT EXISTS idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agent_performance_workspace_id ON agent_performance_metrics(workspace_id);

-- Thinking processes indexes
CREATE INDEX IF NOT EXISTS idx_thinking_processes_workspace_id ON thinking_processes(workspace_id);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_process_id ON thinking_steps(process_id);

-- Quality system indexes
CREATE INDEX IF NOT EXISTS idx_quality_validations_workspace_id ON quality_validations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_quality_validations_artifact_id ON quality_validations(artifact_id);

-- Conversation indexes
CREATE INDEX IF NOT EXISTS idx_conversations_workspace_id ON conversations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);

-- ============================================================================
-- Schema Setup Complete
-- ============================================================================

-- This schema provides the complete foundation for the AI Team Orchestrator
-- Features included:
-- - Multi-workspace management with advanced goal decomposition
-- - AI agent orchestration with handoffs and performance tracking  
-- - Intelligent task system with dependencies and semantic analysis
-- - Professional deliverable generation with dual-format content
-- - Asset management with quality validation and AI enhancement
-- - Real-time thinking processes (Claude/o3 style)
-- - Comprehensive memory and learning system
-- - Quality assurance with AI-driven validation
-- - Conversational AI interface with tool integration
-- - System monitoring and performance tracking
-- - Human-in-the-loop feedback and confirmation system