// Type definitions for OpenAI Usage API data

export interface ModelCost {
  model: string;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost: number;
  request_count: number;
  error_count: number;
}

export interface HourlyUsage {
  hour: number;
  cost: number;
  tokens: number;
  requests: number;
}

export interface DailyUsage {
  date: string;
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  hourly_breakdown?: HourlyUsage[];
}

export interface UsageData {
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  model_breakdown: ModelCost[];
  daily_breakdown?: DailyUsage[];
  period_start: string;
  period_end: string;
}

export interface BudgetStatus {
  monthly_budget: number;
  current_spend: number;
  // Support both field names from backend (budget_used_percentage is frontend, budget_used_percent is backend)
  budget_used_percentage?: number;
  budget_used_percent?: number;
  // Support both projected field names
  projected_monthly_spend?: number;
  projected_monthly?: number;
  days_remaining: number;
  daily_average: number;
  is_over_budget?: boolean;
  budget_alert_level?: 'normal' | 'warning' | 'critical' | string;
  recommendations?: string[];
  // Additional fields from backend
  recommended_daily_limit?: number;
  projected_overage?: number;
  status?: string;
}

export interface CostIntelligence {
  alerts: CostAlert[];
  total_alerts: number;
  potential_monthly_savings: number;
}

export interface CostAlert {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  title: string;
  description: string;
  recommendation: string;
  potential_savings: number;
  confidence: number;
  created_at: string;
}

export interface ModelComparison {
  models: ModelCostComparison[];
  recommended_model: string;
  estimated_savings: number;
}

export interface ModelCostComparison {
  model: string;
  daily_cost: number;
  projected_monthly: number;
  cost_per_1k_tokens: number;
  efficiency_score: number;
  pros: string[];
  cons: string[];
}

export interface UsageDashboard {
  current_month: UsageData;
  today: UsageData;
  budget: BudgetStatus;
  model_comparison: ModelComparison;
  cost_intelligence: CostIntelligence;
  last_updated: string;
}